package org.aema.capture;
oneway interface ILlmCallback {
    void completed(String response);
    void failed(String code);
}
