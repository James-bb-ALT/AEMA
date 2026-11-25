package org.aema.capture;

import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

/** Single atomic JSON model: invalid/interrupted imports preserve the installed model. */
final class ForecastStore {
    final File root;
    ForecastStore(File root) { this.root = root; }
    File file() { return new File(root, "forecast-model.json"); }
    ForecastModel load() throws Exception {
        if (!file().isFile() || file().length() > ForecastModel.MAX_BYTES)
            throw new IllegalStateException("MODEL_REQUIRED");
        return new ForecastModel(new String(Files.readAllBytes(file().toPath()), StandardCharsets.UTF_8));
    }
    void install(InputStream source) throws Exception {
        if (source == null) throw new IllegalArgumentException("Missing model input");
        String text = read(source, ForecastModel.MAX_BYTES);
        ForecastModel model = new ForecastModel(text);
        if (model.synthetic) throw new IllegalArgumentException("Synthetic model is only allowed in demonstration");
        if (!root.isDirectory() && !root.mkdirs()) throw new IllegalStateException("Storage unavailable");
        ModelStore.writeJson(file(), model.data);
    }
    static String read(InputStream source, int limit) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192]; int n;
        while ((n = source.read(buffer)) != -1) {
            if (out.size() + n > limit) throw new IllegalArgumentException("Input exceeds limit");
            out.write(buffer, 0, n);
        }
        return out.toString("UTF-8");
    }
}
