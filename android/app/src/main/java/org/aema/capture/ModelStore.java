package org.aema.capture;

import android.content.Context;
import android.net.Uri;
import android.os.StatFs;
import android.util.AtomicFile;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.concurrent.CancellationException;
import java.util.function.BooleanSupplier;
import java.util.function.LongConsumer;

/** Atomic model replacement; an interrupted import preserves the previous model. */
public final class ModelStore {
    public static final long MAX_BYTES = 1024L * 1024 * 1024;
    public static final String DEFAULT_SHA = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031";
    private final Context context;
    public ModelStore(Context context) { this.context = context.getApplicationContext(); }
    public File directory() { return new File(context.getFilesDir(), "llm"); }
    public File model() { return new File(directory(), "model.gguf"); }
    public File metadata() { return new File(directory(), "model.json"); }
    public boolean ready() { return model().isFile() && metadata().isFile(); }
    public boolean bundled() {
        try (InputStream ignored = context.getAssets().open("models/qwen3.gguf")) { return true; }
        catch (Exception error) { return false; }
    }
    public JSONObject info() throws Exception {
        return new JSONObject(new String(Files.readAllBytes(metadata().toPath()), StandardCharsets.UTF_8));
    }
    public void installBundled(BooleanSupplier cancelled, LongConsumer progress) throws Exception {
        try (InputStream source = context.getAssets().open("models/qwen3.gguf")) {
            install(source, "Qwen3-0.6B-Q8_0 oficial", DEFAULT_SHA, cancelled, progress);
        }
    }
    public void importUri(Uri uri, BooleanSupplier cancelled, LongConsumer progress) throws Exception {
        try (InputStream source = context.getContentResolver().openInputStream(uri)) {
            if (source == null) throw new IllegalStateException("Não foi possível abrir o modelo.");
            install(source, "Qwen3 GGUF importado", null, cancelled, progress);
        }
    }
    public void install(InputStream source, String label, String expectedSha,
            BooleanSupplier cancelled, LongConsumer progress) throws Exception {
        synchronized (ModelStore.class) {
        if (!directory().isDirectory() && !directory().mkdirs()) throw new IllegalStateException("Sem acesso ao armazenamento.");
        File temporary = new File(directory(), "model.pending");
        long available = new StatFs(directory().getAbsolutePath()).getAvailableBytes();
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        long size = 0;
        byte[] header = new byte[8];
        try {
            try (FileOutputStream target = new FileOutputStream(temporary)) {
                byte[] buffer = new byte[1024 * 1024]; int count;
                while ((count = source.read(buffer)) != -1) {
                    if (cancelled.getAsBoolean()) throw new CancellationException();
                    if (count == 0) continue;
                    for (int i = 0; i < count && size + i < header.length; i++) header[(int)size + i] = buffer[i];
                    size += count;
                    if (size > MAX_BYTES || size > available - 64 * 1024 * 1024)
                        throw new IllegalStateException("Modelo maior que 1 GiB ou espaço insuficiente.");
                    target.write(buffer, 0, count); digest.update(buffer, 0, count);
                    progress.accept(size);
                }
                target.getFD().sync();
            }
            if (cancelled.getAsBoolean()) throw new CancellationException();
            validateHeader(header, size);
            String sha = hex(digest.digest());
            if (expectedSha != null && !expectedSha.equals(sha))
                throw new IllegalStateException("O hash do modelo incluído não confere.");
            JSONObject info = new JSONObject().put("name", label).put("sha256", sha)
                .put("size_bytes", size).put("gguf_version", 3).put("expected_architecture", "qwen3")
                .put("source", expectedSha == null ? "local_import" : "Qwen/Qwen3-0.6B-GGUF@23749fefcc72300e3a2ad315e1317431b06b590a");
            // Model file is replaced before metadata; inference verifies its digest each time.
            Files.move(temporary.toPath(), model().toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            writeJson(metadata(), info);
        } finally { if (temporary.exists()) temporary.delete(); }
        }
    }
    public static void validateHeader(byte[] header, long size) {
        if (size < 1024 * 1024 || size > MAX_BYTES || header.length < 8 ||
                header[0] != 'G' || header[1] != 'G' || header[2] != 'U' || header[3] != 'F' ||
                ByteBuffer.wrap(header, 4, 4).order(ByteOrder.LITTLE_ENDIAN).getInt() != 3)
            throw new IllegalArgumentException("Selecione um modelo Qwen3 GGUF v3 válido, de até 1 GiB.");
    }
    public JSONObject verify(BooleanSupplier cancelled) throws Exception {
        JSONObject saved = info();
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream source = Files.newInputStream(model().toPath())) {
            byte[] buffer = new byte[1024 * 1024]; int n;
            while ((n = source.read(buffer)) != -1) {
                if (cancelled.getAsBoolean()) throw new CancellationException();
                digest.update(buffer, 0, n);
            }
        }
        if (model().length() != saved.getLong("size_bytes") || !hex(digest.digest()).equals(saved.getString("sha256")))
            throw new IllegalStateException("Modelo alterado ou incompleto. Importe novamente.");
        return saved;
    }
    static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes) result.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        return result.toString();
    }
    static void writeJson(File file, JSONObject data) throws Exception {
        AtomicFile atomic = new AtomicFile(file);
        FileOutputStream stream = atomic.startWrite();
        try { stream.write(data.toString(2).getBytes(StandardCharsets.UTF_8)); atomic.finishWrite(stream); }
        catch (Exception error) { atomic.failWrite(stream); throw error; }
    }
}
