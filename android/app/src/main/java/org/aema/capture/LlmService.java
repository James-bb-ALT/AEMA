package org.aema.capture;

import android.app.Service;
import android.content.Intent;
import android.os.Debug;
import android.os.IBinder;
import org.json.JSONObject;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicBoolean;

/** Bound only while the analysis screen is visible; no privileges, tools or network. */
public final class LlmService extends Service {
    private final AtomicBoolean running = new AtomicBoolean();
    private final ILlmService.Stub binder = new ILlmService.Stub() {
        @Override public void analyze(String prompt, String grammar, ILlmCallback callback) {
            if (!running.compareAndSet(false, true)) {
                try { callback.failed("BUSY"); } catch (Exception ignored) {}
                return;
            }
            try { LlmNative.reset(); }
            catch (LinkageError error) {
                running.set(false);
                try { callback.failed("RUNTIME_UNAVAILABLE"); } catch (Exception ignored) {}
                return;
            }
            new Thread(() -> {
                try {
                    File model = new File(getFilesDir(), "llm/model.gguf");
                    String result = new String(LlmNative.generate(model.getAbsolutePath(),
                        prompt, grammar, 128, 90000), StandardCharsets.UTF_8);
                    JSONObject report = new JSONObject(result);
                    report.put("worker_pss_after_kib", Debug.getPss());
                    report.put("backend", "cpu");
                    report.put("threads", 4);
                    callback.completed(report.toString());
                } catch (Exception | LinkageError | OutOfMemoryError error) {
                    try { callback.failed(error instanceof OutOfMemoryError ? "OUT_OF_MEMORY"
                        : safeCode(error.getMessage())); } catch (Exception ignored) {}
                } finally { running.set(false); }
            }, "aema-llm-worker").start();
        }
        @Override public void cancel() { try { LlmNative.cancel(); } catch (LinkageError ignored) {} }
    };
    private static String safeCode(String code) {
        return code != null && code.matches("[A-Z_]{3,64}") ? code : "INFERENCE_FAILED";
    }
    @Override public IBinder onBind(Intent intent) { return binder; }
    @Override public void onDestroy() {
        // The dedicated process also bounds stuck native loads and frees all model memory.
        android.os.Process.killProcess(android.os.Process.myPid());
        super.onDestroy();
    }
}
