package org.aema.capture;

import android.app.ActivityManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.JSONObject;
import java.io.File;
import java.util.concurrent.atomic.AtomicBoolean;

/** One foreground-screen request; cancellation never waits for native work on the UI. */
public final class AnalysisController {
    public interface Listener { void status(String text); void completed(JSONObject report); void failed(String message); }
    private final Context context;
    private final Listener listener;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final AtomicBoolean cancelled = new AtomicBoolean();
    private boolean bound, finished;
    private ILlmService remote;
    private String prepared;
    private JSONObject modelInfo;
    private final Runnable timeout = () -> fail("TIMEOUT", "A leitura excedeu dois minutos. Tente novamente com mais memória disponível.");
    private final ServiceConnection connection = new ServiceConnection() {
        @Override public void onServiceConnected(ComponentName name, IBinder binder) {
            if (finished) return;
            remote = ILlmService.Stub.asInterface(binder);
            try {
                JSONObject input = new JSONObject(prepared);
                listener.status("Modelo lendo a captura… Você pode cancelar.");
                remote.analyze(input.getString("prompt"), input.getString("grammar"), new ILlmCallback.Stub() {
                    @Override public void completed(String response) {
                        new Thread(() -> validate(response), "aema-llm-validate").start();
                    }
                    @Override public void failed(String code) { main.post(() -> fail(code, describe(code))); }
                });
            } catch (Exception error) { fail("START_FAILED", "Não foi possível iniciar a leitura local."); }
        }
        @Override public void onServiceDisconnected(ComponentName name) {
            fail("WORKER_EXITED", "O Android encerrou o processo do modelo. Pode ter faltado memória.");
        }
        @Override public void onNullBinding(ComponentName name) { fail("BIND_FAILED", "O processo do modelo não iniciou."); }
        @Override public void onBindingDied(ComponentName name) { onServiceDisconnected(name); }
    };
    public AnalysisController(Context context, Listener listener) {
        this.context = context.getApplicationContext(); this.listener = listener;
    }
    public void start(File capture) {
        main.postDelayed(timeout, 120000);
        new Thread(() -> {
            try {
                ActivityManager.MemoryInfo memory = new ActivityManager.MemoryInfo();
                context.getSystemService(ActivityManager.class).getMemoryInfo(memory);
                if (memory.lowMemory || memory.availMem < 768L * 1024 * 1024)
                    throw new IllegalStateException("LOW_MEMORY");
                main.post(() -> { if (!finished) listener.status("Conferindo modelo e integridade da captura…"); });
                modelInfo = new ModelStore(context).verify(cancelled::get);
                if (cancelled.get()) return;
                synchronized (Python.class) {
                    if (!Python.isStarted()) Python.start(new AndroidPlatform(context));
                }
                prepared = Python.getInstance().getModule("aema.llm")
                    .callAttr("prepare_analysis", capture.getAbsolutePath()).toString();
                if (cancelled.get()) return;
                JSONObject input = new JSONObject(prepared);
                AnalysisDebug.event(context, "prepare", "OK", new JSONObject()
                    .put("capture_sha256", input.getString("capture_sha256"))
                    .put("model_sha256", modelInfo.getString("sha256"))
                    .put("facts", input.getJSONArray("facts").length()));
                main.post(() -> {
                    if (finished) return;
                    bound = context.bindService(new Intent(context, LlmService.class), connection, Context.BIND_AUTO_CREATE);
                    if (!bound) fail("BIND_FAILED", "O processo do modelo não iniciou.");
                });
            } catch (Exception | OutOfMemoryError error) {
                String code = "LOW_MEMORY".equals(error.getMessage()) ? "LOW_MEMORY" : "PREPARE_FAILED";
                main.post(() -> fail(code, describe(code)));
            }
        }, "aema-llm-prepare").start();
    }
    private void validate(String response) {
        try {
            if (cancelled.get()) return;
            JSONObject nativeReport = new JSONObject(response);
            String text = nativeReport.getString("text");
            nativeReport.remove("text");
            AnalysisDebug.event(context, "generation", "FINISHED", nativeReport);
            JSONObject result = new JSONObject(Python.getInstance().getModule("aema.llm")
                .callAttr("validate_reading", prepared, text).toString());
            result.put("model", modelInfo).put("runtime", nativeReport);
            main.post(() -> {
                if (finished) return;
                try {
                    ModelStore.writeJson(new File(context.getFilesDir(), "analysis-result.json"), result);
                    AnalysisDebug.event(context, "inference", "OK", nativeReport);
                    finish(); listener.completed(result);
                } catch (Exception error) { fail("SAVE_FAILED", "A leitura terminou, mas não foi possível salvar o relatório."); }
            });
        } catch (Exception error) {
            main.post(() -> fail("UNGROUNDED_OUTPUT", "O modelo não produziu uma leitura verificável. Nenhuma recomendação nova foi publicada."));
        }
    }
    public void cancel() {
        if (!finished) {
            AnalysisDebug.event(context, "inference", "CANCELLED", null);
            finish();
        }
    }
    private void finish() {
        if (finished) return;
        finished = true; cancelled.set(true); main.removeCallbacks(timeout);
        if (remote != null) try { remote.cancel(); } catch (Exception ignored) {}
        if (bound) {
            context.unbindService(connection); bound = false;
            context.stopService(new Intent(context, LlmService.class));
        }
    }
    private void fail(String code, String text) {
        if (finished) return;
        AnalysisDebug.event(context, "inference", code, null);
        finish(); listener.failed(text + " Veja os detalhes em Debug.");
    }
    static String describe(String code) {
        return switch (code) {
            case "LOW_MEMORY", "OUT_OF_MEMORY" -> "Memória disponível insuficiente. Feche outros aplicativos e tente novamente.";
            case "PREPARE_FAILED" -> "Confira o modelo e faça uma coleta completa com parsing válido antes de analisar.";
            case "MODEL_REQUIRES_QWEN3" -> "Este leitor requer um modelo Qwen3 GGUF. Importe um arquivo compatível.";
            case "CANCELLED_OR_TIMEOUT" -> "O modelo atingiu o limite de tempo ou a leitura foi cancelada.";
            case "RUNTIME_UNAVAILABLE" -> "A biblioteca de IA não está disponível para este aparelho.";
            case "MODEL_LOAD_FAILED" -> "O modelo não carregou. Confira o arquivo e a memória disponível.";
            default -> "A leitura local não terminou (" + code + ").";
        };
    }
}
