package org.aema.capture;

import android.os.ParcelFileDescriptor;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.concurrent.TimeUnit;

/** Shizuku UserService. Only fixed, read-only commands are accepted over Binder. */
public final class ShellCollector extends IShellCollector.Stub {
    static final String[][] COMMANDS = {
        {"/system/bin/getprop", "ro.product.model"},
        {"/system/bin/getprop", "ro.build.fingerprint"},
        {"/system/bin/getprop", "ro.build.version.sdk"},
        {"/system/bin/dumpsys", "batterystats", "--checkin"},
        {"/system/bin/dumpsys", "batterystats"},
        {"/system/bin/pm", "list", "packages", "-U"},
        {"/system/bin/dumpsys", "battery"}
    };

    public ShellCollector() {}

    @Override public synchronized String execute(int command, ParcelFileDescriptor output) {
        JSONObject result = new JSONObject();
        Process process = null;
        try (var sink = new ParcelFileDescriptor.AutoCloseOutputStream(output)) {
            if (command < 0 || command >= COMMANDS.length)
                throw new IllegalArgumentException("Unknown read-only command");
            result.put("argv", new JSONArray(COMMANDS[command]));
            result.put("started_at_utc", Instant.now().toString());
            result.put("started_elapsed_realtime_ms", android.os.SystemClock.elapsedRealtime());
            process = new ProcessBuilder(COMMANDS[command]).start();
            final Process running = process;
            ByteArrayOutputStream errors = new ByteArrayOutputStream();
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            final Throwable[] failure = new Throwable[1];
            Thread stdout = new Thread(() -> {
                try (InputStream stream = running.getInputStream()) {
                    byte[] buffer = new byte[65536];
                    int read;
                    while ((read = stream.read(buffer)) != -1) {
                        sink.write(buffer, 0, read);
                        digest.update(buffer, 0, read);
                    }
                } catch (Throwable error) { failure[0] = error; }
            });
            Thread stderr = new Thread(() -> {
                try (InputStream stream = running.getErrorStream()) {
                    byte[] buffer = new byte[4096];
                    int read;
                    while ((read = stream.read(buffer)) != -1) {
                        if (errors.size() < 16384)
                            errors.write(buffer, 0, Math.min(read, 16384 - errors.size()));
                    }
                } catch (Exception ignored) { /* Process status remains authoritative. */ }
            });
            stdout.start();
            stderr.start();
            if (!process.waitFor(120, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                throw new IllegalStateException("Command timed out after 120 seconds");
            }
            stdout.join(5000);
            stderr.join(5000);
            if (stdout.isAlive() || stderr.isAlive() || failure[0] != null)
                throw new IllegalStateException("Could not finish reading command output");
            sink.flush();
            result.put("exit_code", process.exitValue());
            result.put("stdout_sha256", hex(digest.digest()));
            result.put("stderr", errors.toString("UTF-8"));
        } catch (Exception error) {
            try { result.put("exit_code", -1); result.put("error", error.toString()); }
            catch (Exception ignored) {}
        } finally {
            if (process != null) process.destroy();
            try { result.put("ended_at_utc", Instant.now().toString()); }
            catch (Exception ignored) {}
            try { result.put("ended_elapsed_realtime_ms", android.os.SystemClock.elapsedRealtime()); }
            catch (Exception ignored) {}
        }
        return result.toString();
    }

    private static String hex(byte[] bytes) {
        StringBuilder value = new StringBuilder();
        for (byte b : bytes) value.append(String.format(java.util.Locale.ROOT, "%02X", b & 255));
        return value.toString();
    }

    @Override public void destroy() { System.exit(0); }
}
