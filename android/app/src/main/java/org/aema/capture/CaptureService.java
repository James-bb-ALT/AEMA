package org.aema.capture;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.ComponentName;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import android.os.PowerManager;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.JSONArray;
import org.json.JSONObject;
import rikka.shizuku.Shizuku;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.Instant;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public final class CaptureService extends Service {
    private static final String CHANNEL = "captures";
    private boolean running;
    private PowerManager.WakeLock wakeLock;

    @Override public void onCreate() {
        super.onCreate();
        getSystemService(NotificationManager.class).createNotificationChannel(
            new NotificationChannel(CHANNEL, "Coletas AEMA", NotificationManager.IMPORTANCE_LOW));
    }
    private Notification notification(String text) {
        PendingIntent open = PendingIntent.getActivity(this, 0, new Intent(this, MainActivity.class),
            PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this, CHANNEL).setContentTitle("AEMA · coleta local")
            .setContentText(text).setSmallIcon(R.drawable.ic_aema).setContentIntent(open)
            .setOngoing(true).build();
    }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        startForeground(1, notification("Salvando BatteryStats no telefone…"));
        if (running) return START_NOT_STICKY;
        running = true;
        Scheduler.state(this).edit().putBoolean("running", true).apply();
        long scheduled = intent == null ? System.currentTimeMillis()
            : intent.getLongExtra("scheduled_at_ms", System.currentTimeMillis());
        wakeLock = getSystemService(PowerManager.class).newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK, "AEMA:Capture");
        wakeLock.acquire(20 * 60 * 1000L);
        new Thread(() -> collect(scheduled), "aema-capture").start();
        return START_NOT_STICKY;
    }
    private void collect(long scheduled) {
        File staging = new File(getFilesDir(), "staging/" + UUID.randomUUID());
        JSONObject metadata = new JSONObject();
        JSONArray commands = new JSONArray();
        Shizuku.UserServiceArgs args = new Shizuku.UserServiceArgs(
            new ComponentName(this, ShellCollector.class)).daemon(false)
            .processNameSuffix("collector").version(BuildConfig.VERSION_CODE);
        final IShellCollector[] remote = new IShellCollector[1];
        CountDownLatch connected = new CountDownLatch(1);
        ServiceConnection connection = new ServiceConnection() {
            @Override public void onServiceConnected(ComponentName name, IBinder binder) {
                remote[0] = IShellCollector.Stub.asInterface(binder);
                connected.countDown();
            }
            @Override public void onServiceDisconnected(ComponentName name) { remote[0] = null; }
        };
        boolean bound = false;
        String warning = "";
        try {
            if (!staging.mkdirs()) throw new IllegalStateException("Armazenamento indisponível");
            metadata.put("schema_version", "1.0");
            metadata.put("session_id", UUID.randomUUID().toString());
            metadata.put("started_at_utc", Instant.now().toString());
            metadata.put("started_elapsed_realtime_ms", android.os.SystemClock.elapsedRealtime());
            metadata.put("scheduled_at_utc", Instant.ofEpochMilli(scheduled).toString());
            metadata.put("delay_ms", Math.max(0, System.currentTimeMillis() - scheduled));
            metadata.put("transport", "shizuku_user_service");
            metadata.put("commands", commands);
            metadata.put("battery_state_file", "battery_state.txt");
            try {
                CountDownLatch received = new CountDownLatch(1);
                Shizuku.OnBinderReceivedListener listener = received::countDown;
                Shizuku.addBinderReceivedListenerSticky(listener);
                try {
                    if (!received.await(20, TimeUnit.SECONDS) || !Shizuku.pingBinder())
                        throw new IllegalStateException("Inicie o Shizuku e autorize o AEMA.");
                } finally { Shizuku.removeBinderReceivedListener(listener); }
                if (Shizuku.checkSelfPermission() != PackageManager.PERMISSION_GRANTED)
                    throw new IllegalStateException("Permissão do Shizuku não concedida.");
                Shizuku.bindUserService(args, connection);
                bound = true;
                if (!connected.await(30, TimeUnit.SECONDS) || remote[0] == null)
                    throw new IllegalStateException("Shizuku não conectou ao coletor.");
                String[] names = {"model.txt", "build.txt", "sdk.txt", "stats.csv", "stats.txt",
                    "packageUID.txt", "battery_state.txt"};
                for (int command = 0; command < names.length; command++) {
                    File output = new File(staging, names[command]);
                    JSONObject status;
                    try (ParcelFileDescriptor fd = ParcelFileDescriptor.open(output,
                            ParcelFileDescriptor.MODE_CREATE | ParcelFileDescriptor.MODE_TRUNCATE |
                            ParcelFileDescriptor.MODE_READ_WRITE)) {
                        if (remote[0] == null) throw new IllegalStateException("Shizuku desconectado");
                        status = new JSONObject(remote[0].execute(command, fd));
                    }
                    commands.put(status);
                    if (status.getInt("exit_code") != 0 || output.length() == 0)
                        throw new IllegalStateException("Comando falhou: " + names[command]);
                }
                String id = Scheduler.state(this).getString("device_id", null);
                if (id == null) {
                    id = UUID.randomUUID().toString();
                    Scheduler.state(this).edit().putString("device_id", id).apply();
                }
                JSONObject device = new JSONObject();
                device.put("serial", id);
                device.put("serial_kind", "installation_uuid_not_hardware_serial");
                device.put("model", read(new File(staging, "model.txt")));
                device.put("build_fingerprint", read(new File(staging, "build.txt")));
                device.put("sdk", read(new File(staging, "sdk.txt")));
                metadata.put("device", device);
                metadata.put("status", "complete");
            } catch (Exception error) {
                metadata.put("status", "failed");
                metadata.put("collection_error", error.toString());
                warning = "Coleta incompleta. Verifique Shizuku e abra o ZIP de diagnóstico.";
            }
            metadata.put("ended_at_utc", Instant.now().toString());
            metadata.put("ended_elapsed_realtime_ms", android.os.SystemClock.elapsedRealtime());
            synchronized (Python.class) {
                if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
            }
            String archive = Python.getInstance().getModule("aema.mobile")
                .callAttr("publish_capture", staging.getAbsolutePath(),
                    new File(getFilesDir(), "captures").getAbsolutePath(), metadata.toString())
                .toString();
            // Record the durable private archive before accessing an external provider.
            Scheduler.state(this).edit().putString("last_file", new File(archive).getName())
                .putLong("last_at", System.currentTimeMillis()).putString("last_error", warning).apply();
            // Raw data remains on this device. SAF copying happens only to a chosen folder.
            try { FolderExport.copy(this, new File(archive)); }
            catch (Exception error) { warning = "ZIP salvo no app; selecione a pasta novamente para copiar."; }
            JSONObject published = new JSONObject(readManifest(archive));
            if (warning.isEmpty() && !"complete".equals(published.optString("parse_status")))
                warning = "Brutos salvos. Parsing incompatível; veja o manifesto no ZIP.";
            Scheduler.state(this).edit().putString("last_error", warning).apply();
            AnalysisDebug.event(this, "capture", warning.isEmpty() ? "OK" : "WARNING",
                new JSONObject().put("command_count", commands.length())
                    .put("collection_status", metadata.optString("status"))
                    .put("parse_status", published.optString("parse_status")));
        } catch (Exception error) {
            warning = "Falha ao salvar: " + error.getMessage();
            Scheduler.state(this).edit().putString("last_error", warning).apply();
            AnalysisDebug.event(this, "capture", "SAVE_FAILED", null);
        } finally {
            if (bound) try { Shizuku.unbindUserService(args, connection, true); }
                catch (RuntimeException ignored) {}
            if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
            stopForeground(STOP_FOREGROUND_REMOVE);
            if (!warning.isEmpty()) getSystemService(NotificationManager.class).notify(2,
                new Notification.Builder(this, CHANNEL).setContentTitle("AEMA · atenção à coleta")
                    .setContentText(warning).setStyle(new Notification.BigTextStyle().bigText(warning))
                    .setSmallIcon(R.drawable.ic_aema).setAutoCancel(true).build());
            running = false;
            Scheduler.state(this).edit().putBoolean("running", false).apply();
            stopSelf();
        }
    }
    static String read(File path) throws Exception {
        return new String(Files.readAllBytes(path.toPath()), StandardCharsets.UTF_8).trim();
    }
    static String readManifest(String path) throws Exception {
        try (java.util.zip.ZipFile archive = new java.util.zip.ZipFile(path);
             var stream = archive.getInputStream(archive.getEntry("capture_manifest.json"))) {
            ByteArrayOutputStreamCompat text = new ByteArrayOutputStreamCompat();
            byte[] buffer = new byte[8192]; int count;
            while ((count = stream.read(buffer)) != -1) text.write(buffer, 0, count);
            return text.toString("UTF-8");
        }
    }
    private static final class ByteArrayOutputStreamCompat extends java.io.ByteArrayOutputStream {}
    @Override public IBinder onBind(Intent intent) { return null; }
    @Override public void onTimeout(int startId, int fgsType) {
        Scheduler.state(this).edit().putString("last_error", "Android encerrou a coleta por tempo limite.").apply();
        stopSelf();
    }
}
