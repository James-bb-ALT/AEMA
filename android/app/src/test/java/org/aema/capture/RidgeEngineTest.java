package org.aema.capture;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.Arrays;

public class RidgeEngineTest {
    private double[] scale() { double[] v = new double[20]; Arrays.fill(v, 2); return v; }
    @Test public void normalizesAddsInterceptClampsAndCopiesParameters() {
        double[] mean = new double[20], scale = scale();
        double[][] weights = new double[21][5];
        weights[0][0] = 5; weights[1][0] = 3; weights[0][1] = -2;
        RidgeEngine engine = new RidgeEngine(mean, scale, weights);
        weights[0][0] = 999; scale[0] = 999;
        double[] x = new double[20]; x[0] = 4;
        assertArrayEquals(new double[]{11, 0, 0, 0, 0}, engine.predict(x), 1e-12);
    }
    @Test public void rejectsBadShapesAndNonfiniteInputs() {
        assertThrows(IllegalArgumentException.class, () -> new RidgeEngine(new double[2], new double[2], new double[3][5]));
        assertThrows(IllegalArgumentException.class, () -> new RidgeEngine(new double[20], new double[20], new double[21][5]));
        double[][] weights = new double[21][5]; weights[0][0] = Double.NaN;
        assertThrows(IllegalArgumentException.class, () -> new RidgeEngine(new double[20], scale(), weights));
        RidgeEngine engine = new RidgeEngine(new double[20], scale(), new double[21][5]);
        assertThrows(IllegalArgumentException.class, () -> engine.predict(new double[19]));
        double[] x = new double[20]; x[0] = Double.POSITIVE_INFINITY;
        assertThrows(IllegalArgumentException.class, () -> engine.predict(x));
    }
    @Test public void overflowCannotPublishInfinity() {
        double[][] weights = new double[21][5]; weights[1][0] = Double.MAX_VALUE;
        RidgeEngine engine = new RidgeEngine(new double[20], scale(), weights);
        double[] x = new double[20]; x[0] = 10;
        assertThrows(IllegalArgumentException.class, () -> engine.predict(x));
    }
}
