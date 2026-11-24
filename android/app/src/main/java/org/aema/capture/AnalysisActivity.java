package org.aema.capture;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

/** Local model management, grounded reading, cancellation and explicit debug export. */
public final class AnalysisActivity extends Activity {
    private TextView status, model, result;
    private Button analyze, install, importModel, cancel;
    private AnalysisController controller;
    private final AtomicBoolean importingCancelled = new AtomicBoolean();
    private volatile boolean importing;
    private String exportPayload;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (saved != null) exportPayload = saved.getString("export");
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(244, 246, 243));
        LinearLayout body = new LinearLayout(this); body.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(24); body.setPadding(pad, pad, pad, pad);
        body.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(pad, pad + insets.getSystemWindowInsetTop(), pad, pad + insets.getSystemWindowInsetBottom());
            return insets;
        });
        scroll.addView(body);
        text(body, "Leitura local por IA", 28, true);
        text(body, "Componentes e aplicativos, sem internet. O modelo destaca fatos da captura e sugestões para revisão.", 16, false);
        model = text(body, "", 14, false);
        status = text(body, "Pronto para ler uma captura.", 17, true);
        install = button(body, "Preparar modelo incluído", this::installBundled);
        importModel = button(body, "Importar Qwen3 GGUF", () -> startActivityForResult(
            new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE), 40));
        analyze = button(body, "Ler captura mais recente", this::analyze);
        cancel = button(body, "Cancelar", this::cancelWork);
        cancel.setEnabled(false);
        text(body, "Última leitura", 20, true);
        result = text(body, "Nenhuma leitura salva.", 15, false); result.setTextIsSelectable(true);
        button(body, "Exportar última leitura", () -> {
            try {
                File file = new File(getFilesDir(), "analysis-result.json");
                if (!file.isFile()) { status.setText("Faça uma leitura antes de exportar."); return; }
                export(new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8), "aema-leitura.json");
            } catch (Exception error) { status.setText("Não foi possível abrir o relatório salvo."); }
        });
        text(body, "Debug", 20, true);
        text(body, "Tempos, tokens, memória, hashes e falhas ficam neste telefone. O debug não inclui brutos, nomes de pacotes ou prompts.", 14, false);
        button(body, "Ver debug", () -> {
            try {
                TextView debug = new TextView(this); debug.setText(AnalysisDebug.report(this).toString(2));
                debug.setTextIsSelectable(true); debug.setPadding(pad, pad, pad, pad);
                ScrollView panel = new ScrollView(this); panel.addView(debug);
                new AlertDialog.Builder(this).setTitle("Debug local").setView(panel)
                    .setPositiveButton("Fechar", null).show();
            } catch (Exception error) { status.setText("Debug indisponível."); }
        });
        button(body, "Exportar debug JSON", () -> {
            try { export(AnalysisDebug.report(this).toString(2), "aema-debug.json"); }
            catch (Exception error) { status.setText("Não foi possível preparar o debug."); }
        });
        button(body, "Limpar histórico de debug", () -> {
            try { AnalysisDebug.clear(this); status.setText("Histórico de debug limpo. Capturas e leituras mantidas."); }
            catch (Exception error) { status.setText("Não foi possível limpar o debug."); }
        });
        text(body, "Limites desta versão", 19, true);
        text(body, "A leitura usa estimativas acumuladas do Android. Ainda não prevê as próximas 6 horas nem aprende automaticamente. " +
            "Componentes e aplicativos são visões sobrepostas: não some seus valores. Nenhuma configuração é alterada pela IA.", 14, false);
        text(body, "Qwen3 · llama.cpp em CPU · máximo de 128 tokens por leitura · versão " + BuildConfig.VERSION_NAME, 12, false);
        button(body, "Licenças do modelo e runtime", () -> {
            try {
                StringBuilder licenses = new StringBuilder();
                for (String name : new String[]{"llama.cpp-MIT.txt", "Qwen-Apache-2.0.txt"}) {
                    try (java.io.InputStream source = getAssets().open("licenses/" + name)) {
                        java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
                        byte[] buffer = new byte[4096]; int n;
                        while ((n = source.read(buffer)) != -1) bytes.write(buffer, 0, n);
                        licenses.append(name).append("\n\n").append(bytes.toString("UTF-8")).append("\n\n");
                    }
                }
                TextView content = new TextView(this); content.setText(licenses); content.setTextIsSelectable(true);
                ScrollView panel = new ScrollView(this); panel.addView(content);
                new AlertDialog.Builder(this).setTitle("Licenças").setView(panel).setPositiveButton("Fechar", null).show();
            } catch (Exception error) { status.setText("Consulte THIRD_PARTY_NOTICES no repositório AEMA."); }
        });
        button(body, "Voltar à coleta", this::finish);
        setContentView(scroll); refreshModel(); loadSaved();
    }
    private void refreshModel() {
        ModelStore store = new ModelStore(this);
        try {
            if (store.ready()) {
                JSONObject info = store.info();
                model.setText(info.getString("name") + " · " + info.getLong("size_bytes") / (1024 * 1024) + " MiB\nSHA-256: " + info.getString("sha256"));
            } else model.setText(store.bundled() ? "Modelo incluído no APK. Prepare-o uma vez para usar offline."
                : "Importe um Qwen3 GGUF v3 de até 1 GiB. O app não baixa modelos pela internet.");
        } catch (Exception error) { model.setText("Modelo incompleto. Prepare ou importe novamente."); }
        install.setVisibility(store.bundled() ? android.view.View.VISIBLE : android.view.View.GONE);
    }
    private void installBundled() { importSource(null); }
    private void importSource(android.net.Uri uri) {
        if (importing || controller != null) return;
        importing = true; importingCancelled.set(false); setBusy(true);
        status.setText("Copiando e verificando o modelo…");
        new Thread(() -> {
            try {
                ModelStore store = new ModelStore(this);
                java.util.function.LongConsumer progress = bytes -> runOnUiThread(() -> {
                    if (!importingCancelled.get()) status.setText("Preparando modelo: " + bytes / (1024 * 1024) + " MiB…");
                });
                if (uri == null) store.installBundled(importingCancelled::get, progress);
                else store.importUri(uri, importingCancelled::get, progress);
                AnalysisDebug.event(this, "model_import", "OK", store.info());
                runOnUiThread(() -> { if (!isDestroyed()) { refreshModel(); status.setText("Modelo pronto para leitura offline."); } });
            } catch (Exception | OutOfMemoryError error) {
                AnalysisDebug.event(this, "model_import", importingCancelled.get() ? "CANCELLED" : "IMPORT_FAILED", null);
                runOnUiThread(() -> { if (!isDestroyed()) status.setText(importingCancelled.get()
                    ? "Importação cancelada." : "Não foi possível importar. Verifique formato, tamanho e espaço livre."); });
            } finally { importing = false; runOnUiThread(() -> { if (!isDestroyed()) setBusy(false); }); }
        }, "aema-model-import").start();
    }
    private void analyze() {
        if (controller != null || importing) return;
        if (!new ModelStore(this).ready()) { status.setText("Prepare ou importe o modelo primeiro."); return; }
        File[] files = new File(getFilesDir(), "captures").listFiles((dir, name) -> name.endsWith(".zip"));
        if (files == null || files.length == 0) { status.setText("Volte à coleta e toque em Coletar agora."); return; }
        File latest = Arrays.stream(files).max(Comparator.comparingLong(File::lastModified)).orElseThrow();
        status.setText("Preparando leitura…"); setBusy(true);
        controller = new AnalysisController(this, new AnalysisController.Listener() {
            @Override public void status(String text) { status.setText(text); }
            @Override public void completed(JSONObject report) {
                controller = null; setBusy(false); status.setText("Leitura concluída e salva neste telefone."); show(report);
            }
            @Override public void failed(String message) { controller = null; setBusy(false); status.setText(message); }
        });
        controller.start(latest);
    }
    private void show(JSONObject report) {
        try {
            StringBuilder text = new StringBuilder("Captura: ").append(report.optString("captured_at_utc", "—"))
                .append("\nLeitura de snapshot acumulado · sem previsão futura\n");
            JSONArray focus = report.getJSONArray("focus");
            if (focus.length() == 0) text.append("\nO modelo se absteve de selecionar pontos de atenção.\n");
            for (int i = 0; i < focus.length(); i++) {
                JSONObject fact = focus.getJSONObject(i);
                text.append("\n").append(fact.getString("label")).append(": ")
                    .append(String.format(Locale.getDefault(), "%.6g", fact.getDouble("value_mah")))
                    .append(" mAh atribuídos pelo Android");
                if (fact.optBoolean("shared_uid")) text.append(" (UID compartilhado; sem divisão por pacote)");
                text.append('\n');
            }
            JSONArray suggestions = report.getJSONArray("suggestions");
            for (int i = 0; i < suggestions.length(); i++) text.append("\n• ").append(suggestions.getJSONObject(i).getString("text")).append('\n');
            if (report.optInt("rejected_negative_estimates") > 0)
                text.append("\nEstimativas negativas foram excluídas desta leitura.\n");
            text.append("\nEstes valores não medem economia garantida. A leitura salva continua identificada pela data e pelo hash da captura.");
            result.setText(text);
        } catch (Exception error) { result.setText("Relatório salvo incompatível."); }
    }
    private void loadSaved() {
        try {
            File file = new File(getFilesDir(), "analysis-result.json");
            if (file.isFile() && file.length() < 256 * 1024)
                show(new JSONObject(new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8)));
        } catch (Exception ignored) {}
    }
    private void setBusy(boolean busy) {
        analyze.setEnabled(!busy); importModel.setEnabled(!busy); install.setEnabled(!busy); cancel.setEnabled(busy);
        if (busy) getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }
    private void cancelWork() {
        importingCancelled.set(true);
        if (controller != null) { controller.cancel(); controller = null; }
        if (!importing) setBusy(false);
        status.setText("Operação cancelada. A última leitura salva foi mantida.");
    }
    private void export(String text, String name) {
        exportPayload = text;
        startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json")
            .addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE, name), 41);
    }
    @Override protected void onActivityResult(int request, int code, Intent data) {
        super.onActivityResult(request, code, data);
        if (code != RESULT_OK || data == null || data.getData() == null) return;
        if (request == 40) importSource(data.getData());
        if (request == 41 && exportPayload != null) {
            String payload = exportPayload; exportPayload = null;
            android.net.Uri destination = data.getData();
            new Thread(() -> {
                try (OutputStream output = getContentResolver().openOutputStream(destination, "wt")) {
                    if (output == null) throw new IllegalStateException();
                    output.write(payload.getBytes(StandardCharsets.UTF_8));
                    runOnUiThread(() -> status.setText("Relatório exportado para o local escolhido."));
                } catch (Exception error) { runOnUiThread(() -> status.setText("Falha ao exportar. Escolha outro local.")); }
            }, "aema-debug-export").start();
        }
    }
    @Override protected void onSaveInstanceState(Bundle saved) { saved.putString("export", exportPayload); super.onSaveInstanceState(saved); }
    @Override protected void onStop() { cancelWork(); super.onStop(); }
    private TextView text(LinearLayout parent, String value, int size, boolean bold) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size);
        view.setTextColor(Color.rgb(24, 44, 36)); view.setPadding(0, dp(12), 0, dp(8));
        if (bold) view.setTypeface(null, android.graphics.Typeface.BOLD);
        parent.addView(view); return view;
    }
    private Button button(LinearLayout parent, String label, Runnable action) {
        Button button = new Button(this); button.setText(label); button.setAllCaps(false);
        button.setMinHeight(dp(52)); button.setOnClickListener(v -> action.run());
        parent.addView(button, new LinearLayout.LayoutParams(-1, -2)); return button;
    }
    private int dp(int value) { return (int)(value * getResources().getDisplayMetrics().density); }
}
