package org.aema.capture;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.provider.Settings;
import android.provider.DocumentsContract;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import rikka.shizuku.Shizuku;
import java.io.File;
import java.text.DateFormat;
import java.util.Date;

/** Local collection controls. No network permission, account or remote storage. */
public final class MainActivity extends Activity {
    private TextView status;
    private TextView details;
    private Button toggle;
    private final Handler handler = new Handler();
    private final Runnable refresh = new Runnable() {
        @Override public void run() { update(); handler.postDelayed(this, 2000); }
    };
    private final Shizuku.OnRequestPermissionResultListener permission = (request, result) -> {
        update();
        message(result == PackageManager.PERMISSION_GRANTED
            ? "Shizuku autorizado." : "Autorize o AEMA no Shizuku para coletar.");
    };

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        Shizuku.addRequestPermissionResultListener(permission);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(244, 246, 243));
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(24);
        body.setPadding(pad, pad, pad, pad);
        // Respect system bars with edge-to-edge enforcement on Android 15+.
        body.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(pad, pad + insets.getSystemWindowInsetTop(), pad,
                pad + insets.getSystemWindowInsetBottom());
            return insets;
        });
        scroll.addView(body);
        text(body, "AEMA", 36, true);
        text(body, "BatteryStats no seu telefone", 18, false);
        text(body, "Um novo ZIP a cada 6 horas. Coleta e parsing locais, sem envio pela internet.", 16, false);
        status = text(body, "", 20, true);
        details = text(body, "", 14, false);
        button(body, "1. Autorizar Shizuku", () -> {
            if (!Shizuku.pingBinder()) {
                new AlertDialog.Builder(this).setTitle("Inicie o Shizuku")
                    .setMessage("Instale e inicie o Shizuku. Depois volte ao AEMA e autorize o acesso. " +
                        "Sem root, o Shizuku precisa ser reiniciado após reiniciar o telefone.")
                    .setPositiveButton("Abrir Shizuku", (dialog, which) -> {
                        Intent launch = getPackageManager().getLaunchIntentForPackage("moe.shizuku.privileged.api");
                        if (launch != null) startActivity(launch);
                        else message("Instale o Shizuku pelo site shizuku.rikka.app.");
                    }).setNegativeButton("Fechar", null).show();
            } else if (Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED) {
                message("Shizuku já autorizado.");
            } else Shizuku.requestPermission(1);
        });
        button(body, "2. Escolher pasta para os ZIPs", () -> {
            Intent select = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
            startActivityForResult(select, 20);
        });
        button(body, "3. Permitir alarmes e notificações", () -> {
            if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED)
                requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 30);
            if (!Scheduler.permitted(this)) startActivity(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
                Uri.parse("package:" + getPackageName())));
            else message("Alarmes exatos autorizados.");
        });
        toggle = button(body, "", () -> {
            if (Scheduler.state(this).getBoolean("enabled", false)) {
                Scheduler.disable(this);
                message("Coleta automática pausada. Os arquivos foram mantidos.");
            } else {
                if (!ready()) return;
                Scheduler.enable(this);
                startForegroundService(new Intent(this, CaptureService.class));
                message("Primeira coleta iniciada. Próximas a cada 6 horas.");
            }
            update();
        });
        toggle.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(23, 107, 83)));
        toggle.setTextColor(Color.WHITE);
        button(body, "Coletar agora", () -> {
            if (ready()) {
                startForegroundService(new Intent(this, CaptureService.class));
                message("Coleta iniciada. Aguarde o novo ZIP.");
            }
        });
        button(body, "Copiar todos os ZIPs para a pasta", () -> copyAll());
        text(body, "Sobre os dados", 19, true);
        text(body, "Os ZIPs contêm pacotes, UIDs e outros dados privados. Escolha uma pasta local, " +
            "como Documentos/AEMA. Provedores de nuvem podem sincronizar a pasta escolhida. " +
            "Uma cópia fica protegida no app até a desinstalação; os ZIPs já exportados permanecem na pasta.", 14, false);
        text(body, "São snapshots acumulados do Android, sem reset dos contadores. O intervalo de coleta " +
            "não transforma os valores em consumo exclusivo de 6 horas. Formatos incompatíveis ficam " +
            "registrados no manifesto e os brutos são preservados. Telefone desligado, Shizuku parado, " +
            "forçar parada e restrições do fabricante podem interromper ou atrasar a coleta.", 14, false);
        text(body, "Versão " + BuildConfig.VERSION_NAME + " · Android 8+ · ARM64 / x86_64", 12, false);
        setContentView(scroll);
    }
    private boolean ready() {
        if (!Shizuku.pingBinder() || Shizuku.checkSelfPermission() != PackageManager.PERMISSION_GRANTED) {
            message("Inicie e autorize o Shizuku primeiro."); return false;
        }
        if (!Scheduler.permitted(this)) { message("Autorize os alarmes exatos primeiro."); return false; }
        if (Scheduler.state(this).getString("folder", null) == null) {
            message("Escolha uma pasta local para os ZIPs primeiro."); return false;
        }
        return true;
    }
    private void copyAll() {
        if (Scheduler.state(this).getString("folder", null) == null) {
            message("Escolha uma pasta primeiro."); return;
        }
        new Thread(() -> {
            try { FolderExport.all(this); runOnUiThread(() -> message("ZIPs copiados para a pasta escolhida.")); }
            catch (Exception error) { runOnUiThread(() -> message("Falha ao copiar. Escolha a pasta novamente.")); }
        }, "aema-export").start();
    }
    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == 20 && result == RESULT_OK && data != null && data.getData() != null) {
            Uri tree = data.getData();
            try {
                getContentResolver().takePersistableUriPermission(tree,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                Scheduler.state(this).edit().putString("folder", tree.toString()).apply();
                copyAll();
            } catch (SecurityException error) { message("A pasta não concedeu acesso persistente."); }
        }
    }
    private void update() {
        if (status == null) return;
        var state = Scheduler.state(this);
        boolean enabled = state.getBoolean("enabled", false);
        boolean shizuku = Shizuku.pingBinder();
        status.setText(enabled ? "Coleta automática ativada" : "Coleta automática pausada");
        toggle.setText(enabled ? "Pausar coleta automática" : "Ativar coleta a cada 6 horas");
        File[] archives = new File(getFilesDir(), "captures").listFiles((dir, name) -> name.endsWith(".zip"));
        String folder = state.getString("folder", null);
        String error = state.getString("last_error", "");
        details.setText("Shizuku: " + (shizuku ? "disponível" : "não iniciado") +
            "\nPróxima: " + date(state.getLong("next_at", 0)) +
            "\nÚltima: " + date(state.getLong("last_at", 0)) +
            "\nArquivos no app: " + (archives == null ? 0 : archives.length) +
            "\nPasta: " + folderLabel(folder) +
            (error.isEmpty() ? "" : "\nAtenção: " + error));
    }
    private String date(long value) {
        return value == 0 ? "—" : DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT).format(new Date(value));
    }
    private String folderLabel(String folder) {
        if (folder == null) return "a escolher";
        try {
            String id = DocumentsContract.getTreeDocumentId(Uri.parse(folder));
            if (id.contains(":")) {
                String path = id.substring(id.indexOf(':') + 1);
                return (id.startsWith("primary:") ? "Armazenamento interno" : "Armazenamento") +
                    (path.isEmpty() ? "" : " / " + path);
            }
        } catch (IllegalArgumentException ignored) {}
        return "Pasta selecionada";
    }
    private TextView text(LinearLayout parent, String value, int size, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value); view.setTextSize(size); view.setTextColor(Color.rgb(24, 44, 36));
        if (bold) view.setTypeface(null, android.graphics.Typeface.BOLD);
        view.setPadding(0, dp(12), 0, dp(8)); parent.addView(view); return view;
    }
    private Button button(LinearLayout parent, String label, Runnable action) {
        Button button = new Button(this); button.setText(label); button.setAllCaps(false);
        button.setMinHeight(dp(52)); button.setOnClickListener(view -> {
            try { action.run(); } catch (RuntimeException error) { message(error.getMessage()); }
        });
        parent.addView(button, new LinearLayout.LayoutParams(-1, -2)); return button;
    }
    private int dp(int value) { return (int)(value * getResources().getDisplayMetrics().density); }
    private void message(String value) { Toast.makeText(this, value, Toast.LENGTH_LONG).show(); }
    @Override protected void onResume() {
        super.onResume(); Scheduler.rearm(this); handler.post(refresh);
    }
    @Override protected void onPause() { handler.removeCallbacks(refresh); super.onPause(); }
    @Override protected void onDestroy() {
        Shizuku.removeRequestPermissionResultListener(permission); super.onDestroy();
    }
}
