package org.aema.capture;
import org.junit.Test;
import static org.junit.Assert.*;
public class IntervalPlanTest {
    @Test public void firstSlotIsSixHoursAfterStart() {
        assertEquals(1000 + 21_600_000L, IntervalPlan.next(1000, 1000));
    }
    @Test public void lateRunPreservesCadenceAndSkipsLostSlots() {
        long anchor = 1000;
        assertEquals(anchor + 4 * IntervalPlan.INTERVAL_MS,
            IntervalPlan.next(anchor, anchor + 3 * IntervalPlan.INTERVAL_MS + 500));
    }
    @Test public void backwardClockKeepsOriginalAnchor() {
        assertEquals(1000, IntervalPlan.next(1000, 1));
    }
}
