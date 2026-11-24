package org.aema.capture;
import org.aema.capture.ILlmCallback;
interface ILlmService {
    void analyze(String prompt, String grammar, ILlmCallback callback);
    void cancel();
}
