package org.aema.capture;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

public final class Scheduler {
    static final String ACTION = "org.aema.capture.CAPTURE";
    private Scheduler() {}
    static SharedPreferences state(Context context) {
        return context.getSharedPreferences("capture", Context.MODE_PRIVATE);
    }
    static boolean permitted(Context context) {
        return Build.VERSION.SDK_INT < 31 || context.getSystemService(AlarmManager.class)
            .canScheduleExactAlarms();
    }
    static PendingIntent pending(Context context, long scheduled) {
        Intent intent = new Intent(context, ScheduleReceiver.class).setAction(ACTION);
        intent.putExtra("scheduled_at_ms", scheduled);
        return PendingIntent.getBroadcast(context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }
    static void enable(Context context) {
        if (!permitted(context)) throw new IllegalStateException("Autorize alarmes exatos primeiro.");
        long anchor = System.currentTimeMillis();
        state(context).edit().putBoolean("enabled", true).putLong("anchor", anchor).apply();
        arm(context, IntervalPlan.next(anchor, anchor));
    }
    static void arm(Context context, long when) {
        if (!permitted(context)) {
            state(context).edit().putString("last_error", "Alarme sem autorização. Abra o app.")
                .putLong("next_at", 0).apply();
            return;
        }
        context.getSystemService(AlarmManager.class).setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP, when, pending(context, when));
        state(context).edit().putLong("next_at", when).apply();
    }
    static void rearm(Context context) {
        SharedPreferences state = state(context);
        if (!state.getBoolean("enabled", false)) return;
        long now = System.currentTimeMillis();
        long previous = state.getLong("next_at", 0);
        // After reboot/update, an overdue slot is retried later via an alarm, never at BOOT.
        long next = previous > 0 && previous <= now ? now + 120_000
            : IntervalPlan.next(state.getLong("anchor", now), now);
        arm(context, next);
    }
    static void disable(Context context) {
        context.getSystemService(AlarmManager.class).cancel(pending(context, 0));
        state(context).edit().putBoolean("enabled", false).putLong("next_at", 0).apply();
    }
}
