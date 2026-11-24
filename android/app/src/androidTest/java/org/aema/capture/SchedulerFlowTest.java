package org.aema.capture;

import android.content.Context;
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

/** Optional device test: requires Shizuku to be running and authorized beforehand. */
@RunWith(AndroidJUnit4.class)
public class SchedulerFlowTest {
    @Test public void exactAlarmCollectsInBackgroundAndKeepsSixHourCadence() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();
        assumeTrue("Authorize Shizuku first", Shizuku.pingBinder() &&
            Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED);
        assumeTrue("Allow exact alarms first", Scheduler.permitted(context));
        // An idle emulator may report no UID estimates at all. Generate a small,
        // muted audio workload before requiring a fully parseable UID section.
        android.media.MediaPlayer player = android.media.MediaPlayer.create(context,
            android.provider.Settings.System.DEFAULT_NOTIFICATION_URI);
        assertNotNull("A notification sound is needed for the emulator workload", player);
        try { player.setVolume(0, 0); player.start(); SystemClock.sleep(1500); }
        finally { player.release(); }
        long before = System.currentTimeMillis();
        Scheduler.enable(context);
        Scheduler.arm(context, before + 5000);
        instrumentation.getUiAutomation().executeShellCommand("input keyevent HOME").close();
        long deadline = SystemClock.elapsedRealtime() + 180_000;
        while ((Scheduler.state(context).getLong("last_at", 0) < before ||
                Scheduler.state(context).getBoolean("running", false)) &&
                SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(250);
        assertTrue("No archive from alarm", Scheduler.state(context).getLong("last_at", 0) >= before);
        String name = Scheduler.state(context).getString("last_file", "");
        File archive = new File(context.getFilesDir(), "captures/" + name);
        assertTrue(archive.isFile());
        JSONObject manifest = new JSONObject(CaptureService.readManifest(archive.getAbsolutePath()));
        assertEquals("complete", manifest.getString("status"));
        assertEquals("complete", manifest.getString("parse_status"));
        assertEquals("shizuku_user_service", manifest.getString("transport"));
        assertTrue(Scheduler.state(context).getLong("next_at", 0) > before + 5 * 60 * 60 * 1000L);
        Scheduler.disable(context);
        assertFalse(Scheduler.state(context).getBoolean("enabled", true));
        assertEquals(0, Scheduler.state(context).getLong("next_at", -1));
        assertTrue("Pausing must retain existing data", archive.isFile());
    }
}
