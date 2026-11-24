package org.aema.capture;

/** CPU-only JNI. Loaded exclusively in the :llm process. */
public final class LlmNative {
    static { System.loadLibrary("aema_llm"); }
    private LlmNative() {}
    public static native void reset();
    public static native void cancel();
    public static native byte[] generate(String model, String prompt, String grammar,
        int maximumTokens, int timeoutMs);
}
