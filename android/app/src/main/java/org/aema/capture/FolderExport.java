package org.aema.capture;

import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;

/** SAF mirror. A private original is kept if a provider fails or a grant is revoked. */
final class FolderExport {
    private FolderExport() {}
    static void copy(Context context, File archive) throws IOException {
        String value = Scheduler.state(context).getString("folder", null);
        if (value == null) return;
        Uri tree = Uri.parse(value);
        String rootId = DocumentsContract.getTreeDocumentId(tree);
        Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, rootId);
        try (Cursor cursor = context.getContentResolver().query(children, new String[]{
                DocumentsContract.Document.COLUMN_DISPLAY_NAME}, null, null, null)) {
            if (cursor == null) throw new IOException("Pasta indisponível");
            while (cursor.moveToNext()) {
                if (archive.getName().equals(cursor.getString(0))) return;
            }
        }
        Uri parent = DocumentsContract.buildDocumentUriUsingTree(tree, rootId);
        Uri destination = DocumentsContract.createDocument(context.getContentResolver(), parent,
            "application/zip", ".pending-" + archive.getName());
        if (destination == null) throw new IOException("Não foi possível criar o ZIP na pasta");
        try {
            try (FileInputStream source = new FileInputStream(archive);
                    OutputStream sink = context.getContentResolver().openOutputStream(destination, "w")) {
                if (sink == null) throw new IOException("Pasta sem acesso de escrita");
                byte[] buffer = new byte[65536];
                int count;
                while ((count = source.read(buffer)) != -1) sink.write(buffer, 0, count);
            }
            if (DocumentsContract.renameDocument(context.getContentResolver(), destination,
                    archive.getName()) == null) throw new IOException("Não foi possível finalizar o ZIP");
        } catch (Exception error) {
            try { DocumentsContract.deleteDocument(context.getContentResolver(), destination); }
            catch (Exception ignored) {}
            throw new IOException("ZIP preservado no app; falha ao copiar para a pasta", error);
        }
    }
    static void all(Context context) throws IOException {
        for (String directoryName : new String[]{"captures", "forecasts"}) {
        File[] files = new File(context.getFilesDir(), directoryName).listFiles(
            (directory, name) -> name.endsWith(".zip"));
        if (files != null) for (File file : files) copy(context, file);
        }
    }
}
