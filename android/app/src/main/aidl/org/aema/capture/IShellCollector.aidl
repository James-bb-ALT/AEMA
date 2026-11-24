package org.aema.capture;
import android.os.ParcelFileDescriptor;
interface IShellCollector {
    String execute(int command, in ParcelFileDescriptor output) = 0;
    void destroy() = 16777114;
}
