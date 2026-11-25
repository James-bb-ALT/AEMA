package org.aema.capture;

import android.content.Context;
import android.os.SystemClock;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.InputStream;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;

/** Shared by automatic collection and the forecast screen. Personal and demo results never mix. */
final class ForecastRunner {
    static synchronized JSONObject personal(Context context) throws Exception {
        JSONObject report;
        JSONObject modelForArchive = null;
        try {
            ForecastModel model = new ForecastStore(context.getFilesDir()).load();
            modelForArchive = model.data;
            if (model.synthetic) throw new IllegalArgumentException("Synthetic model cannot forecast personal usage");
            synchronized (Python.class) { if (!Python.isStarted()) Python.start(new AndroidPlatform(context)); }
            long started = SystemClock.elapsedRealtime();
            JSONObject input = new JSONObject(Python.getInstance().getModule("aema.forecast")
                .callAttr("prepare_forecast", new File(context.getFilesDir(), "captures").getAbsolutePath(),
                    model.data.toString(), System.currentTimeMillis()).toString());
            long preparation = SystemClock.elapsedRealtime() - started;
            report = "ready".equals(input.optString("status")) ? evaluate(model, input, false) : input;
            if (input.has("history_sha256")) report.put("history_sha256", input.getJSONArray("history_sha256"));
            if (input.has("history_span_hours")) report.put("history_span_hours", input.getDouble("history_span_hours"));
            report.put("preparation_ms", preparation).put("model_sha256", model.sha);
        } catch (Exception error) {
            report = new JSONObject().put("status", "abstained").put("reason",
                "MODEL_REQUIRED".equals(error.getMessage()) ? "MODEL_REQUIRED" : "MODEL_OR_HISTORY_INVALID");
        }
        report.put("synthetic", false).put("generated_at_utc", Instant.now().toString())
            .put("app_version", BuildConfig.VERSION_NAME).put("schema_version", "aema_forecast_result/1.0");
        if ("predicted".equals(report.optString("status"))) archive(context, report, modelForArchive);
        ModelStore.writeJson(new File(context.getFilesDir(), "forecast-result.json"), report);
        AnalysisDebug.event(context, "forecast", report.getString("status"), new JSONObject()
            .put("reason", report.optString("reason")).put("prediction_ms", report.optDouble("prediction_ms", 0))
            .put("preparation_ms", report.optLong("preparation_ms", 0)).put("engine", "native_ridge"));
        return report;
    }
    private static void archive(Context context, JSONObject report, JSONObject model) throws Exception {
        File root = new File(context.getFilesDir(), "forecasts");
        if (!root.isDirectory() && !root.mkdirs()) throw new IllegalStateException("Forecast storage unavailable");
        String name = "forecast_" + System.currentTimeMillis() + "_" + java.util.UUID.randomUUID() + ".zip";
        File pending = new File(root, ".pending-" + name), saved = new File(root, name);
        try {
            try (java.util.zip.ZipOutputStream zip = new java.util.zip.ZipOutputStream(new java.io.FileOutputStream(pending))) {
                for (String entry : new String[]{"forecast.json", "model.json"}) {
                    zip.putNextEntry(new java.util.zip.ZipEntry(entry));
                    zip.write((entry.equals("forecast.json") ? report : model).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    zip.closeEntry();
                }
            }
            java.nio.file.Files.move(pending.toPath(), saved.toPath(), java.nio.file.StandardCopyOption.ATOMIC_MOVE);
        } finally { if (pending.exists()) pending.delete(); }
        try { FolderExport.copy(context, saved); }
        catch (Exception error) { AnalysisDebug.event(context, "forecast_export", "COPY_FAILED_PRIVATE_ARCHIVE_KEPT", null); }
    }
    static JSONObject demo(Context context) throws Exception {
        JSONObject fixture;
        try (InputStream source = context.getAssets().open("forecast-demo.json")) {
            fixture = new JSONObject(ForecastStore.read(source, ForecastModel.MAX_BYTES));
        }
        ForecastModel model = new ForecastModel(fixture.getJSONObject("model").toString());
        if (!model.synthetic) throw new IllegalArgumentException("Demonstration must be marked synthetic");
        JSONObject report = evaluate(model, fixture.getJSONObject("input"), true);
        report.put("app_version", BuildConfig.VERSION_NAME).put("schema_version", "aema_forecast_result/1.0")
            .put("generated_at_utc", Instant.now().toString()).put("model_sha256", model.sha);
        ModelStore.writeJson(new File(context.getFilesDir(), "forecast-demo-result.json"), report);
        AnalysisDebug.event(context, "forecast_demo", "OK", new JSONObject()
            .put("prediction_ms", report.getDouble("prediction_ms")).put("synthetic", true));
        return report;
    }
    static JSONObject evaluate(ForecastModel model, JSONObject input, boolean demo) throws Exception {
        if (demo != model.synthetic) throw new IllegalArgumentException("Provenance mismatch");
        double[] features = ForecastModel.vector(input.getJSONArray("features"));
        long start = System.nanoTime();
        double[] prediction = model.engine.predict(features);
        double elapsed = (System.nanoTime() - start) / 1e6;
        long origin = input.getLong("origin_ms");
        ArrayList<JSONObject> components = new ArrayList<>(), uids = new ArrayList<>();
        JSONArray targets = model.data.getJSONArray("targets"), shared = input.optJSONArray("shared_uids");
        double sum = 0;
        for (int i = 0; i < targets.length(); i++) {
            JSONObject target = targets.getJSONObject(i);
            JSONObject row = new JSONObject().put("id", target.getString("id")).put("estimated_mah", prediction[i]);
            if (i < 4) { components.add(row); sum += prediction[i]; }
            else {
                int uid = Integer.parseInt(target.getString("id").substring(4));
                boolean isShared = false;
                if (shared != null) for (int j = 0; j < shared.length(); j++) if (shared.getInt(j) == uid) isShared = true;
                uids.add(row.put("shared_uid", isShared));
            }
        }
        Comparator<JSONObject> descending = Comparator.comparingDouble((JSONObject r) -> -r.optDouble("estimated_mah"))
            .thenComparing(r -> r.optString("id"));
        components.sort(descending); uids.sort(descending);
        JSONArray suggestions = new JSONArray();
        if (!components.isEmpty() && components.get(0).optDouble("estimated_mah") > 0) {
            String id = components.get(0).getString("id");
            String text = id.equals("component:screen") ? "Revise brilho e tempo de tela; mudanças podem afetar visibilidade."
                : id.equals("component:cpu") ? "Revise as atividades previstas que usam CPU antes de alterar configurações."
                : "Revise o uso da conexão prevista; mudanças podem afetar sincronização e conectividade.";
            suggestions.put(new JSONObject().put("evidence_id", id).put("text", text));
        }
        if (!uids.isEmpty() && uids.get(0).optDouble("estimated_mah") > 0)
            suggestions.put(new JSONObject().put("evidence_id", uids.get(0).getString("id"))
                .put("text", "Revise o uso do UID previsto antes de restringir apps. UIDs compartilhados não permitem dividir o consumo por pacote; restrições podem atrasar notificações."));
        return new JSONObject().put("status", demo ? "demonstration" : "predicted").put("synthetic", demo)
            .put("origin_ms", origin).put("end_ms", origin + 6 * 3600 * 1000L)
            .put("components", new JSONArray(components)).put("uids", new JSONArray(uids))
            .put("modeled_component_sum_mah", sum).put("suggestions", suggestions)
            .put("prediction_ms", elapsed).put("engine", "native_ridge")
            .put("scientific_validation", false).put("ranking_scope", "modeled_targets_only")
            .put("target_semantics", "future_BatteryStats_estimate_not_physical_ground_truth");
    }
}
