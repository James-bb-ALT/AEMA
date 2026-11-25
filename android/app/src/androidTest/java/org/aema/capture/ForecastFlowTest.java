package org.aema.capture;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class ForecastFlowTest {
    private Context context() { return InstrumentationRegistry.getInstrumentation().getTargetContext(); }
    private JSONObject fixture() throws Exception {
        try (InputStream source = InstrumentationRegistry.getInstrumentation().getContext().getAssets().open("forecast-native-cases.json")) {
            return new JSONObject(ForecastStore.read(source, ForecastModel.MAX_BYTES));
        }
    }
    @Test public void nativeEngineMatchesSixOutputsAcrossSixteenHeldoutCases() throws Exception {
        JSONObject fixture = fixture();
        ForecastModel model = new ForecastModel(fixture.getJSONObject("model").toString());
        JSONArray cases = fixture.getJSONArray("cases");
        double maximum = 0;
        long started = System.nanoTime();
        for (int i = 0; i < cases.length(); i++) {
            JSONObject row = cases.getJSONObject(i);
            double[] actual = model.engine.predict(ForecastModel.vector(row.getJSONArray("features")));
            double[] expected = ForecastModel.vector(row.getJSONArray("expected"));
            assertArrayEquals(expected, actual, 0.001);
            for (int j = 0; j < actual.length; j++) maximum = Math.max(maximum, Math.abs(actual[j] - expected[j]));
            JSONObject report = ForecastRunner.evaluate(model, row, true);
            assertTrue(report.getBoolean("synthetic"));
            assertEquals(4, report.getJSONArray("components").length());
            assertEquals(2, report.getJSONArray("uids").length());
            assertEquals(6 * 3600 * 1000L, report.getLong("end_ms") - report.getLong("origin_ms"));
        }
        assertEquals(16, cases.length());
        double[] input = ForecastModel.vector(cases.getJSONObject(0).getJSONArray("features"));
        for (int i = 0; i < 20; i++) model.engine.predict(input);
        double[] timings = new double[1000]; double checksum = 0;
        for (int i = 0; i < timings.length; i++) {
            long begin = System.nanoTime();
            double[] values = model.engine.predict(input);
            timings[i] = (System.nanoTime() - begin) / 1e6;
            checksum += values[0];
        }
        assertTrue(checksum > 0);
        java.util.Arrays.sort(timings);
        ModelStore.writeJson(new File(context().getFilesDir(), "forecast-validation.json"), new JSONObject()
            .put("synthetic", true).put("cases", cases.length()).put("max_abs_error_mah", maximum)
            .put("wall_ms", (System.nanoTime() - started) / 1e6).put("app_version", BuildConfig.VERSION_NAME)
            .put("engine", "native_ridge").put("warm_repetitions", timings.length)
            .put("warm_6_output_p50_ms", timings[500]).put("warm_6_output_p95_ms", timings[950])
            .put("timing_scope", "emulator_warm_one_fixed_feature_vector_excludes_preparation"));
    }
    @Test public void malformedAndSyntheticImportsPreserveExistingModel() throws Exception {
        File dir = new File(context().getCacheDir(), "forecast-store-test");
        ForecastStore store = new ForecastStore(dir);
        JSONObject data = fixture().getJSONObject("model");
        assertTrue(data.getBoolean("synthetic"));
        assertThrows(IllegalArgumentException.class, () -> store.install(new ByteArrayInputStream(data.toString().getBytes(StandardCharsets.UTF_8))));
        // Deliberate fixture-only provenance override exercises the import path, never publishes a personal model.
        data.put("synthetic", false);
        try {
            store.install(new ByteArrayInputStream(data.toString().getBytes(StandardCharsets.UTF_8)));
            byte[] before = Files.readAllBytes(store.file().toPath());
            assertThrows(Exception.class, () -> store.install(new ByteArrayInputStream("{}".getBytes(StandardCharsets.UTF_8))));
            assertArrayEquals(before, Files.readAllBytes(store.file().toPath()));
            assertThrows(Exception.class, () -> store.install(new ByteArrayInputStream(new byte[ForecastModel.MAX_BYTES + 1])));
            assertArrayEquals(before, Files.readAllBytes(store.file().toPath()));
        } finally { store.file().delete(); }
    }
    @Test public void demonstrationScreenRunsWithoutLlmAndDoesNotInstallPersonalModel() throws Exception {
        Context context = context();
        ForecastStore personal = new ForecastStore(context.getFilesDir());
        byte[] before = personal.file().exists() ? Files.readAllBytes(personal.file().toPath()) : null;
        Activity activity = InstrumentationRegistry.getInstrumentation().startActivitySync(
            new Intent(context, ForecastActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        File report = new File(context.getFilesDir(), "forecast-demo-result.json");
        long previous = report.isFile() ? report.lastModified() : 0;
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Button demo = find(activity.getWindow().getDecorView(), "Executar demonstração sintética");
            assertNotNull(demo); demo.performClick();
        });
        long end = android.os.SystemClock.elapsedRealtime() + 15000;
        while ((!report.isFile() || report.lastModified() == previous) && android.os.SystemClock.elapsedRealtime() < end)
            android.os.SystemClock.sleep(100);
        assertTrue(report.isFile());
        assertTrue("Demonstration did not produce a fresh report", report.lastModified() > previous);
        JSONObject saved = new JSONObject(new String(Files.readAllBytes(report.toPath()), StandardCharsets.UTF_8));
        assertEquals("demonstration", saved.getString("status"));
        assertTrue(saved.getBoolean("synthetic"));
        if (before == null) assertFalse(personal.file().exists());
        else assertArrayEquals(before, Files.readAllBytes(personal.file().toPath()));
        InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);
    }
    private Button find(View view, String text) {
        if (view instanceof Button && text.contentEquals(((Button) view).getText())) return (Button) view;
        if (view instanceof ViewGroup) for (int i = 0; i < ((ViewGroup) view).getChildCount(); i++) {
            Button result = find(((ViewGroup) view).getChildAt(i), text); if (result != null) return result;
        }
        return null;
    }
}
