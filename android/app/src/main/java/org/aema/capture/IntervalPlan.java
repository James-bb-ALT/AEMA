package org.aema.capture;

/** Fixed cadence from the original anchor, skipping missed slots without replaying dumps. */
public final class IntervalPlan {
    public static final long INTERVAL_MS = 6 * 60 * 60 * 1000L;
    private IntervalPlan() {}
    public static long next(long anchor, long now) {
        if (now < anchor) return anchor;
        return anchor + (Math.floorDiv(now - anchor, INTERVAL_MS) + 1) * INTERVAL_MS;
    }
}
