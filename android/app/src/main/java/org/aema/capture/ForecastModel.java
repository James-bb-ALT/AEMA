package org.aema.capture;

import org.json.JSONArray;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HashSet;

/** Strict interoperable model contract; source claims do not constitute scientific validation. */
final class ForecastModel {
    static final int MAX_BYTES = 256 * 1024;
    static final String CONTRACT = "valid_lag1_lag4_mean8_calendar_age_utc_v1";
    final JSONObject data;
    final RidgeEngine engine;
    final boolean synthetic;
    final String sha;
    ForecastModel(String text) throws Exception {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        if (bytes.length > MAX_BYTES) throw new IllegalArgumentException("Model exceeds 256 KiB");
        data = new JSONObject(text);
        if (!"aema_ridge_6h/1.0".equals(data.getString("schema_version")) ||
                !CONTRACT.equals(data.getString("feature_contract")) || !(data.get("horizon_hours") instanceof Number) ||
                data.getDouble("horizon_hours") != 6 ||
                !(data.get("synthetic") instanceof Boolean) ||
                !data.getString("device_key").matches("[a-f0-9]{64}"))
            throw new IllegalArgumentException("Unsupported forecast contract");
        synthetic = data.getBoolean("synthetic");
        JSONArray targets = data.getJSONArray("targets");
        if (targets.length() < 5 || targets.length() > 16) throw new IllegalArgumentException("Invalid targets");
        String[] components = {"screen", "cpu", "wifi", "mobile_radio"};
        HashSet<String> ids = new HashSet<>();
        for (int i = 0; i < targets.length(); i++) {
            JSONObject target = targets.getJSONObject(i);
            String id = target.getString("id"), axis = target.getString("axis");
            if (!ids.add(id)) throw new IllegalArgumentException("Duplicate target");
            if (i < 4) {
                if (!"component".equals(axis) || !id.equals("component:" + components[i]))
                    throw new IllegalArgumentException("Invalid component order");
            } else if (!"uid".equals(axis) || !id.matches("uid:[1-9][0-9]{0,9}") ||
                    Long.parseLong(id.substring(4)) > Integer.MAX_VALUE)
                throw new IllegalArgumentException("Invalid UID target");
        }
        double[] mean = vector(data.getJSONArray("x_mean")), scale = vector(data.getJSONArray("x_scale"));
        JSONArray rows = data.getJSONArray("weights");
        if (rows.length() > 100) throw new IllegalArgumentException("Too many weights");
        double[][] weights = new double[rows.length()][];
        for (int i = 0; i < rows.length(); i++) weights[i] = vector(rows.getJSONArray(i));
        engine = new RidgeEngine(mean, scale, weights);
        if (engine.targets != targets.length()) throw new IllegalArgumentException("Target/weight mismatch");
        sha = ModelStore.hex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    static double[] vector(JSONArray source) throws Exception {
        if (source.length() > 100) throw new IllegalArgumentException("Oversized vector");
        double[] result = new double[source.length()];
        for (int i = 0; i < result.length; i++) {
            if (!(source.get(i) instanceof Number)) throw new IllegalArgumentException("Numeric values required");
            result[i] = source.getDouble(i);
            if (!Double.isFinite(result[i])) throw new IllegalArgumentException("Nonfinite number");
        }
        return result;
    }
}
