package org.aema.capture;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import rikka.shizuku.Shizuku;
import java.io.File;
import static org.junit.Assert.*;
import static org.junit.Assume.*;

@RunWith(AndroidJUnit4.class)
public class CaptureFailureTest {
    @Test public void stoppedShizukuCreatesDiagnosticArchiveWithoutClaimingSuccessfulParsing() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();
        assumeFalse("Stop Shizuku for this test", Shizuku.pingBinder());
        Scheduler.disable(context);
        context.startActivity(new Intent(context, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        SystemClock.sleep(1000);
        long before = System.currentTimeMillis();
        context.startForegroundService(new Intent(context, CaptureService.class));
        long deadline = SystemClock.elapsedRealtime() + 180_000;
        while ((Scheduler.state(context).getLong("last_at", 0) < before ||
                Scheduler.state(context).getBoolean("running", false)) &&
                SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(250);
        assertTrue("Failure archive not published", Scheduler.state(context).getLong("last_at", 0) >= before);
        File archive = new File(context.getFilesDir(), "captures/" +
            Scheduler.state(context).getString("last_file", ""));
        JSONObject manifest = new JSONObject(CaptureService.readManifest(archive.getAbsolutePath()));
        assertEquals("failed", manifest.getString("status"));
        assertEquals("not_attempted", manifest.getString("parse_status"));
        assertTrue(manifest.has("collection_error"));
        assertFalse(manifest.getBoolean("scientific_validation"));
        String[] requested = context.getPackageManager().getPackageInfo(context.getPackageName(),
            PackageManager.GET_PERMISSIONS).requestedPermissions;
        assertFalse(java.util.Arrays.asList(requested).contains("android.permission.INTERNET"));
    }
}
