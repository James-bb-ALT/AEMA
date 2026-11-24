package org.aema.capture;

import android.content.Context;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.UUID;
import static org.junit.Assert.*;

/** Executes actual Android Python/numpy/pandas binaries, not JVM substitutes. */
@RunWith(AndroidJUnit4.class)
public class OfflinePipelineTest {
    @Test public void sameFixturesProduceSameCanonicalDatasetOnAndroid() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();
        File fixtures = new File(context.getCacheDir(), "fixtures-" + UUID.randomUUID());
        assertTrue(fixtures.mkdirs());
        for (String name : new String[]{"checkin_v9.csv", "battery_report.txt", "packages.txt", "battery_report_aosp15.txt"}) {
            try (InputStream source = instrumentation.getContext().getAssets().open(name);
                 FileOutputStream sink = new FileOutputStream(new File(fixtures, name))) {
                byte[] buffer = new byte[4096]; int count;
                while ((count = source.read(buffer)) != -1) sink.write(buffer, 0, count);
            }
        }
        if (!Python.isStarted()) Python.start(new AndroidPlatform(context));
        String result = Python.getInstance().getModule("json").callAttr("dumps",
            Python.getInstance().getModule("aema.demo").callAttr("run_demo",
                fixtures.getAbsolutePath(), new File(context.getCacheDir(), "demo").getAbsolutePath())).toString();
        JSONObject report = new JSONObject(result);
        assertEquals(88, report.getInt("canonical_records"));
        assertEquals(3, report.getInt("package_uid_relations"));
        assertFalse(report.getBoolean("scientific_validation"));
        assertEquals(2, Python.getInstance().getModule("aema.parsers.battery_report")
            .callAttr("BatteryReportParser", new File(fixtures, "battery_report_aosp15.txt").getAbsolutePath())
            .callAttr("parse_result").get("records").asList().size());
        // All host algorithms are packaged in the APK, including study auditing and privacy.
        for (String module : new String[]{"aema.collector", "aema.session", "aema.study",
                "aema.validation", "aema.privacy", "aema.mobile", "aema.presentation"})
            assertNotNull(Python.getInstance().getModule(module));
    }
}
