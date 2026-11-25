package org.aema.capture;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Locale;

/** Experimental native forecast, with explicit separation between personal data and simulation. */
public final class ForecastActivity extends Activity {
    private TextView status, result;
    private boolean busy;
    private String shown, exporting;
    private final ArrayList<Button> controls = new ArrayList<>();
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (saved != null) { shown = saved.getString("shown"); exporting = saved.getString("exporting"); }
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.rgb(244, 246, 243));
        LinearLayout body = new LinearLayout(this); body.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(24); body.setPadding(pad, pad, pad, pad);
        body.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(pad, pad + insets.getSystemWindowInsetTop(), pad, pad + insets.getSystemWindowInsetBottom());
            return insets;
        });
        scroll.addView(body);
        text(body, "Previsão leve · 6 horas", 27);
        text(body, "Ridge experimental, sem modelo de linguagem. Prevê estimativas de componentes e UIDs modelados, offline.", 16);
        status = text(body, "Importe um modelo treinado para esta instalação ou execute a demonstração.", 16);
        button(body, "Importar modelo pessoal JSON", () -> startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT)
            .setType("*/*").addCategory(Intent.CATEGORY_OPENABLE), 60));
        button(body, "Prever com histórico do telefone", () -> work(false));
        button(body, "Executar demonstração sintética", () -> work(true));
        result = text(body, "Nenhuma previsão exibida.", 16); result.setTextIsSelectable(true);
        button(body, "Exportar relatório exibido", () -> {
            if (shown == null) { status.setText("Execute uma previsão ou demonstração primeiro."); return; }
            exporting = shown;
            startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json")
                .addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE, "aema-previsao.json"), 61);
        });
        text(body, "A demonstração não usa seu histórico e não instala um modelo pessoal. O treino pessoal acontece no computador, " +
            "com transferência local. A previsão automática é atualizada após cada coleta quando há modelo e histórico válido.", 14);
        text(body, "Limites: apenas tela, CPU, Wi-Fi, rede móvel e UIDs escolhidos no treinamento. O ranking considera somente esses alvos. " +
            "Componentes e UIDs se sobrepõem: não some os dois grupos. Não há garantia de precisão, economia ou atualização automática dos pesos.", 14);
        text(body, "O histórico exige oito janelas válidas de seis horas nos últimos 14 dias. Cada janela deve ter mesmo boot/reset e campos completos nos dois extremos. " +
            "Uma previsão nova exige captura feita há até 30 minutos. O treino precisa de mais dados.", 14);
        button(body, "Voltar à coleta", this::finish);
        setContentView(scroll);
        if (shown != null) { try { show(new JSONObject(shown)); } catch (Exception ignored) {} }
        else {
            try {
                java.io.File file = new java.io.File(getFilesDir(), "forecast-result.json");
                if (file.isFile() && file.length() < 128 * 1024) {
                    try (InputStream in = new java.io.FileInputStream(file)) { show(new JSONObject(ForecastStore.read(in, 128 * 1024))); }
                }
            } catch (Exception ignored) {}
        }
    }
    private void work(boolean demo) {
        if (busy) return;
        setBusy(true); status.setText(demo ? "Executando demonstração local…" : "Verificando modelo e histórico…");
        new Thread(() -> {
            try {
                JSONObject report = demo ? ForecastRunner.demo(this) : ForecastRunner.personal(this);
                runOnUiThread(() -> { if (!isDestroyed()) { show(report); setBusy(false); } });
            } catch (Exception error) {
                runOnUiThread(() -> { if (!isDestroyed()) { status.setText("Falha ao executar ou salvar. Veja Debug na tela de leitura."); setBusy(false); } });
            }
        }, "aema-forecast").start();
    }
    private void show(JSONObject report) {
        try {
            shown = report.toString();
            if ("abstained".equals(report.optString("status"))) {
                status.setText("Sem previsão: " + reason(report.optString("reason")));
                result.setText("Nenhum valor novo foi previsto. Faça uma coleta recente e confira o modelo/histórico.");
                return;
            }
            boolean demo = report.getBoolean("synthetic");
            status.setText(demo ? "Demonstração sintética concluída — não é uma previsão do seu telefone."
                : "Previsão experimental salva. Confira a data de origem antes de usar.");
            StringBuilder value = new StringBuilder(demo ? "DADOS SINTÉTICOS\n" : "ESTIMATIVAS EXPERIMENTAIS\n");
            value.append("Período UTC: ").append(Instant.ofEpochMilli(report.getLong("origin_ms")))
                .append(" a ").append(Instant.ofEpochMilli(report.getLong("end_ms"))).append('\n');
            if (!demo && System.currentTimeMillis() >= report.getLong("end_ms")) value.append("PERÍODO ENCERRADO — faça nova coleta.\n");
            value.append("\nComponentes modelados (ordem prevista):\n");
            appendRows(value, report.getJSONArray("components"));
            value.append("\nUIDs modelados (não representam todos os apps):\n");
            appendRows(value, report.getJSONArray("uids"));
            value.append("\nSoma apenas dos quatro componentes: ")
                .append(number(report.getDouble("modeled_component_sum_mah"))).append(" mAh estimados. Não é o total completo da bateria.\n");
            JSONArray suggestions = report.getJSONArray("suggestions");
            for (int i = 0; i < suggestions.length(); i++) value.append('\n').append(suggestions.getJSONObject(i).getString("text")).append('\n');
            value.append("\nInferência Ridge: ").append(number(report.getDouble("prediction_ms"))).append(" ms. " +
                "Este tempo não inclui coleta ou preparação de histórico. Não há alteração automática de configurações.");
            result.setText(value);
        } catch (Exception error) { status.setText("Relatório incompatível."); }
    }
    private void appendRows(StringBuilder value, JSONArray rows) throws Exception {
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.getJSONObject(i);
            String label = row.getString("id").replace("component:screen", "Tela").replace("component:cpu", "CPU")
                .replace("component:wifi", "Wi-Fi").replace("component:mobile_radio", "Rede móvel").replace("uid:", "UID ");
            value.append(label).append(": ").append(number(row.getDouble("estimated_mah"))).append(" mAh estimados");
            if (row.optBoolean("shared_uid")) value.append(" (compartilhado; sem divisão por pacote)");
            value.append('\n');
        }
    }
    private static String reason(String code) {
        return switch (code) {
            case "MODEL_REQUIRED" -> "importe um modelo pessoal JSON treinado no computador.";
            case "NEED_VALID_HISTORY" -> "faltam oito janelas válidas de seis horas nos últimos 14 dias.";
            case "DEVICE_MISMATCH" -> "o modelo pertence a outra instalação ou versão de sistema.";
            case "CAPTURE_STALE_OR_CLOCK_CHANGED" -> "a captura não é recente ou houve mudança de relógio.";
            default -> "histórico/modelo inválido, reset/boot alterado, carga nos extremos ou campos indisponíveis.";
        };
    }
    private String number(double v) { return String.format(Locale.getDefault(), "%.4g", v); }
    private void setBusy(boolean value) { busy = value; for (Button b : controls) b.setEnabled(!value); }
    private TextView text(LinearLayout body, String value, int size) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size);
        view.setTextColor(Color.rgb(24, 44, 36)); view.setPadding(0, dp(12), 0, dp(8)); body.addView(view); return view;
    }
    private void button(LinearLayout body, String value, Runnable action) {
        Button button = new Button(this); button.setText(value); button.setAllCaps(false); button.setMinHeight(dp(52));
        button.setOnClickListener(view -> { if (!busy) action.run(); }); controls.add(button); body.addView(button);
    }
    private int dp(int value) { return (int)(value * getResources().getDisplayMetrics().density); }
    @Override protected void onActivityResult(int request, int code, Intent data) {
        super.onActivityResult(request, code, data);
        if (code != RESULT_OK || data == null || data.getData() == null) return;
        if (request == 60) {
            if (busy) return;
            setBusy(true); status.setText("Validando modelo pessoal…");
            new Thread(() -> {
                try (InputStream source = getContentResolver().openInputStream(data.getData())) {
                    new ForecastStore(getFilesDir()).install(source);
                    JSONObject report = ForecastRunner.personal(this);
                    runOnUiThread(() -> { if (!isDestroyed()) { show(report); setBusy(false); } });
                } catch (Exception error) {
                    AnalysisDebug.event(this, "forecast_import", "REJECTED", null);
                    runOnUiThread(() -> { if (!isDestroyed()) {
                        status.setText("Modelo recusado: confira contrato, tamanho (até 256 KiB) e origem não sintética. O anterior foi preservado.");
                        setBusy(false);
                    } });
                }
            }, "aema-forecast-import").start();
        } else if (request == 61 && exporting != null) {
            try (OutputStream out = getContentResolver().openOutputStream(data.getData(), "wt")) {
                if (out == null) throw new IllegalStateException();
                out.write(exporting.getBytes(StandardCharsets.UTF_8)); status.setText("Relatório exportado.");
            } catch (Exception error) { status.setText("Não foi possível exportar o relatório."); }
        }
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        state.putString("shown", shown); state.putString("exporting", exporting); super.onSaveInstanceState(state);
    }
}
