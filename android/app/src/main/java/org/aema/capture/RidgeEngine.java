package org.aema.capture;

/** Bounded dense Ridge inference. No Python, JNI, model framework or network dependency. */
public final class RidgeEngine {
    private final double[] mean, scale;
    private final double[][] weights;
    public final int targets;
    public RidgeEngine(double[] mean, double[] scale, double[][] weights) {
        if (mean == null || scale == null || weights == null || weights.length != mean.length + 1 ||
                mean.length != scale.length || weights.length == 0 || weights[0] == null)
            throw new IllegalArgumentException("Invalid model dimensions");
        targets = weights[0].length;
        if (targets < 5 || targets > 16 || mean.length != 3 * targets + 5)
            throw new IllegalArgumentException("Unsupported forecast dimensions");
        this.mean = mean.clone(); this.scale = scale.clone();
        this.weights = new double[weights.length][targets];
        for (int i = 0; i < mean.length; i++)
            if (!Double.isFinite(mean[i]) || !Double.isFinite(scale[i]) || scale[i] <= 0)
                throw new IllegalArgumentException("Invalid normalization");
        for (int i = 0; i < weights.length; i++) {
            if (weights[i] == null || weights[i].length != targets)
                throw new IllegalArgumentException("Invalid weight row");
            for (int j = 0; j < targets; j++) {
                if (!Double.isFinite(weights[i][j])) throw new IllegalArgumentException("Nonfinite weight");
                this.weights[i][j] = weights[i][j];
            }
        }
    }
    public double[] predict(double[] features) {
        if (features == null || features.length != mean.length) throw new IllegalArgumentException("Invalid input dimensions");
        double[] result = weights[0].clone();
        for (int i = 0; i < features.length; i++) {
            if (!Double.isFinite(features[i])) throw new IllegalArgumentException("Nonfinite feature");
            double normalized = (features[i] - mean[i]) / scale[i];
            for (int j = 0; j < targets; j++) result[j] += normalized * weights[i + 1][j];
        }
        for (int j = 0; j < targets; j++) {
            if (!Double.isFinite(result[j])) throw new IllegalArgumentException("Prediction overflow");
            result[j] = Math.max(0, result[j]);
        }
        return result;
    }
}
