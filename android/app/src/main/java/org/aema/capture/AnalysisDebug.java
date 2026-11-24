package org.aema.capture;

import android.app.ActivityManager;
import android.content.Context;
import android.os.Build;
import android.os.Debug;
import android.os.SystemClock;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.time.Instant;

/** Bounded local diagnostics. No raw captures, package names or prompts. */
public final class AnalysisDebug {
    private AnalysisDebug() {}
    static File file(Context context) { return new File(context.getFilesDir(), "analysis-debug.json"); }
    static synchronized void event(Context context, String stage, String code, JSONObject metrics) {
        try {
            JSONObject log = read(context);
            JSONArray previous = log.optJSONArray("events");
            JSONArray events = new JSONArray();
            if (previous != null) for (int i = Math.max(0, previous.length() - 39); i < previous.length(); i++)
                events.put(previous.getJSONObject(i));
            events.put(new JSONObject().put("at_utc", Instant.now().toString())
                .put("elapsed_realtime_ms", SystemClock.elapsedRealtime())
                .put("stage", stage).put("code", code)
                .put("main_pss_kib", Debug.getPss()).put("metrics", metrics == null ? new JSONObject() : metrics));
            ModelStore.writeJson(file(context), new JSONObject().put("events", events));
        } catch (Exception ignored) { /* A full disk must not crash analysis. */ }
    }
    private static JSONObject read(Context context) throws Exception {
        File source = file(context);
        return source.isFile() && source.length() < 256 * 1024
            ? new JSONObject(new String(Files.readAllBytes(source.toPath()), StandardCharsets.UTF_8)) : new JSONObject();
    }
    public static synchronized JSONObject report(Context context) throws Exception {
        JSONObject report = read(context);
        ActivityManager.MemoryInfo memory = new ActivityManager.MemoryInfo();
        context.getSystemService(ActivityManager.class).getMemoryInfo(memory);
        report.put("schema_version", "1.0").put("app_version", BuildConfig.VERSION_NAME)
            .put("sdk", Build.VERSION.SDK_INT).put("abi", Build.SUPPORTED_ABIS[0])
            .put("ram_total_bytes", memory.totalMem).put("ram_available_bytes", memory.availMem)
            .put("low_memory", memory.lowMemory).put("runtime", "llama.cpp")
            .put("runtime_revision", "0ce7f213b0749fa4dee4e87d8ae7bf63e621c1ad")
            .put("pss_note", "instantaneous samples, not peak memory")
            .put("forecast_status", "not_trained");
        ModelStore store = new ModelStore(context);
        if (store.ready()) report.put("model", store.info());
        var state = Scheduler.state(context);
        report.put("collection", new JSONObject().put("enabled", state.getBoolean("enabled", false))
            .put("running", state.getBoolean("running", false))
            .put("next_at_ms", state.getLong("next_at", 0)).put("last_at_ms", state.getLong("last_at", 0)));
        return report;
    }
    public static synchronized void clear(Context context) throws Exception {
        ModelStore.writeJson(file(context), new JSONObject().put("events", new JSONArray()));
    }
}
