package org.aema.capture;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class ScheduleReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (!Scheduler.state(context).getBoolean("enabled", false)) return;
        if (Scheduler.ACTION.equals(intent.getAction())) {
            long due = intent.getLongExtra("scheduled_at_ms", System.currentTimeMillis());
            Scheduler.arm(context, IntervalPlan.next(
                Scheduler.state(context).getLong("anchor", due), System.currentTimeMillis()));
            try {
                context.startForegroundService(new Intent(context, CaptureService.class)
                    .putExtra("scheduled_at_ms", due));
            } catch (RuntimeException error) {
                Scheduler.state(context).edit().putString("last_error",
                    "Android bloqueou a coleta: " + error.getMessage()).apply();
            }
        } else {
            Scheduler.rearm(context);
        }
    }
}
