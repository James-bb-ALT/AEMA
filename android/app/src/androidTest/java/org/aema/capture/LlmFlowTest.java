package org.aema.capture;

import android.content.Context;
import android.content.Intent;
import android.content.ComponentName;
import android.content.ServiceConnection;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.JSONObject;
import org.junit.Assume;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.zip.ZipOutputStream;
import java.util.zip.ZipEntry;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class LlmFlowTest {
    private static final String DEVICE_MODEL = "/data/local/tmp/aema-qwen.gguf";
    private Context context() { return InstrumentationRegistry.getInstrumentation().getTargetContext(); }
    private String shell(String command) throws Exception {
        try (InputStream stream = new ParcelFileDescriptor.AutoCloseInputStream(
                InstrumentationRegistry.getInstrumentation().getUiAutomation().executeShellCommand(command))) {
            java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
            byte[] buffer = new byte[8192]; int count;
            while ((count = stream.read(buffer)) != -1) bytes.write(buffer, 0, count);
            return bytes.toString("UTF-8");
        }
    }
    private void ensureModel() throws Exception {
        ModelStore store = new ModelStore(context());
        if (store.ready() && ModelStore.DEFAULT_SHA.equals(store.info().getString("sha256"))) return;
        boolean available = shell("stat -c %s " + DEVICE_MODEL).trim().equals("639446688");
        if (InstrumentationRegistry.getArguments().getString("requireModel", "false").equals("true"))
            assertTrue("Required official model is missing: " + DEVICE_MODEL, available);
        Assume.assumeTrue("Push official model to " + DEVICE_MODEL + " for native inference test", available);
        try (InputStream source = new ParcelFileDescriptor.AutoCloseInputStream(
                InstrumentationRegistry.getInstrumentation().getUiAutomation().executeShellCommand("cat " + DEVICE_MODEL))) {
            store.install(source, "Qwen3-0.6B-Q8_0 oficial", ModelStore.DEFAULT_SHA, () -> false, bytes -> {});
        }
    }
    private File fixtureCapture() throws Exception {
        Context context = context();
        File fixtures = new File(context.getCacheDir(), "llm-fixtures"); fixtures.mkdirs();
        for (String name : new String[]{"checkin_v9.csv", "battery_report.txt", "packages.txt"}) {
            try (InputStream source = InstrumentationRegistry.getInstrumentation().getContext().getAssets().open(name);
                 FileOutputStream out = new FileOutputStream(new File(fixtures, name))) {
                byte[] buffer = new byte[4096]; int n;
                while ((n = source.read(buffer)) != -1) out.write(buffer, 0, n);
            }
        }
        synchronized (Python.class) { if (!Python.isStarted()) Python.start(new AndroidPlatform(context)); }
        String output = Python.getInstance().getModule("aema.demo").callAttr("run_demo",
            fixtures.getAbsolutePath(), new File(context.getCacheDir(), "llm-datasets").getAbsolutePath())
            .callAttr("__getitem__", "output_directory").toString();
        File capture = new File(context.getCacheDir(), "llm-fixture.zip");
        try (ZipOutputStream zip = new ZipOutputStream(new FileOutputStream(capture))) {
            JSONObject metadata = new JSONObject().put("schema_version", "1.0").put("status", "complete")
                .put("parse_status", "complete").put("parsed_directory", "parsed/data")
                .put("ended_at_utc", "2026-01-01T00:00:00Z");
            zip.putNextEntry(new ZipEntry("capture_manifest.json"));
            zip.write(metadata.toString().getBytes(StandardCharsets.UTF_8)); zip.closeEntry();
            for (File artifact : new File(output).listFiles()) {
                zip.putNextEntry(new ZipEntry("parsed/data/" + artifact.getName()));
                zip.write(Files.readAllBytes(artifact.toPath())); zip.closeEntry();
            }
            String[] raw = {"stats.csv", "stats.txt", "packageUID.txt"};
            String[] names = {"checkin_v9.csv", "battery_report.txt", "packages.txt"};
            for (int i = 0; i < raw.length; i++) {
                zip.putNextEntry(new ZipEntry(raw[i]));
                zip.write(Files.readAllBytes(new File(fixtures, names[i]).toPath())); zip.closeEntry();
            }
        }
        return capture;
    }
    @Test public void realModelRunsInSeparateProcessAndProducesGroundedSavedReading() throws Exception {
        ensureModel();
        File capture = fixtureCapture();
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<JSONObject> result = new AtomicReference<>();
        AtomicReference<String> failure = new AtomicReference<>();
        AtomicReference<AnalysisController> controller = new AtomicReference<>();
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            AnalysisController reader = new AnalysisController(context(), new AnalysisController.Listener() {
                @Override public void status(String ignored) {}
                @Override public void completed(JSONObject report) { result.set(report); done.countDown(); }
                @Override public void failed(String message) { failure.set(message); done.countDown(); }
            });
            controller.set(reader); reader.start(capture);
        });
        try {
            assertTrue("LLM controller timed out", done.await(130, TimeUnit.SECONDS));
            assertNull(failure.get(), failure.get());
            JSONObject report = result.get();
            assertNotNull(report);
            assertEquals("not_trained", report.getString("forecast_status"));
            assertEquals("llm_snapshot_reading", report.getString("mode"));
            assertTrue(report.getJSONObject("runtime").getInt("output_tokens") > 0);
            assertTrue(report.getJSONObject("runtime").getLong("worker_peak_rss_kib") > 0);
            assertEquals(ModelStore.DEFAULT_SHA, report.getJSONObject("model").getString("sha256"));
            assertTrue(new File(context().getFilesDir(), "analysis-result.json").isFile());
            JSONObject debug = AnalysisDebug.report(context());
            assertFalse(debug.toString().contains("com.example"));
            assertFalse(debug.toString().contains("prompt\""));
            assertTrue(debug.toString().contains("output_tokens"));
            assertEquals(-1, context().checkSelfPermission(android.Manifest.permission.INTERNET));
        } finally { InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> controller.get().cancel()); }
    }
    @Test public void cancellationReleasesBoundNativeWorker() throws Exception {
        ensureModel();
        CountDownLatch started = new CountDownLatch(1);
        AtomicReference<ILlmService> remote = new AtomicReference<>();
        ServiceConnection connection = new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName name, IBinder binder) {
                remote.set(ILlmService.Stub.asInterface(binder)); started.countDown();
            }
            @Override public void onServiceDisconnected(ComponentName name) {}
        };
        assertTrue(context().bindService(new Intent(context(), LlmService.class), connection, Context.BIND_AUTO_CREATE));
        try {
            assertTrue(started.await(15, TimeUnit.SECONDS));
            CountDownLatch completed = new CountDownLatch(1);
            AtomicReference<String> outcome = new AtomicReference<>();
            remote.get().analyze("Read the facts.", "root ::= \"{}\"", new ILlmCallback.Stub() {
                @Override public void completed(String value) { outcome.set("COMPLETED"); completed.countDown(); }
                @Override public void failed(String value) { outcome.set(value); completed.countDown(); }
            });
            remote.get().cancel();
            assertTrue("CPU callback must observe cancellation", completed.await(15, TimeUnit.SECONDS));
            assertEquals("CANCELLED_OR_TIMEOUT", outcome.get());
        } finally { context().unbindService(connection); context().stopService(new Intent(context(), LlmService.class)); }
    }
    @Test public void invalidAndCancelledImportsPreserveInstalledModel() throws Exception {
        ensureModel();
        ModelStore store = new ModelStore(context());
        byte[] invalid = new byte[1024 * 1024];
        assertThrows(IllegalArgumentException.class, () -> store.install(
            new java.io.ByteArrayInputStream(invalid), "invalid", null, () -> false, bytes -> {}));
        assertEquals(ModelStore.DEFAULT_SHA, store.info().getString("sha256"));
        assertThrows(java.util.concurrent.CancellationException.class, () -> store.install(
            new java.io.ByteArrayInputStream(invalid), "cancelled", null, () -> true, bytes -> {}));
        assertEquals(ModelStore.DEFAULT_SHA, store.verify(() -> false).getString("sha256"));
        assertFalse(new File(store.directory(), "model.pending").exists());
    }
}
