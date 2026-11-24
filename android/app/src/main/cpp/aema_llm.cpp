#include <jni.h>
#include <algorithm>
#include <llama.h>
#include <atomic>
#include <chrono>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/resource.h>

namespace {
using Clock = std::chrono::steady_clock;
std::atomic<bool> cancelled{false};
struct Deadline { Clock::time_point end; };
bool abort_run(void *data) {
    return cancelled.load() || Clock::now() > static_cast<Deadline *>(data)->end;
}
bool progress(float, void *data) { return !abort_run(data); }
long milliseconds(Clock::time_point start) {
    return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - start).count();
}
std::string utf8(JNIEnv *env, jstring value) {
    const char *bytes = env->GetStringUTFChars(value, nullptr);
    if (!bytes) throw std::runtime_error("INVALID_ARGUMENT");
    std::string result(bytes);
    env->ReleaseStringUTFChars(value, bytes);
    return result;
}
std::string quote(const std::string &value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c == '\n') out << "\\n";
        else if (c == '\r') out << "\\r";
        else if (c == '\t') out << "\\t";
        else if (c >= 32) out << c;
    }
    out << '"';
    return out.str();
}
void quiet_log(enum ggml_log_level, const char *, void *) {}
}

extern "C" JNIEXPORT void JNICALL
Java_org_aema_capture_LlmNative_reset(JNIEnv *, jclass) { cancelled.store(false); }
extern "C" JNIEXPORT void JNICALL
Java_org_aema_capture_LlmNative_cancel(JNIEnv *, jclass) { cancelled.store(true); }

extern "C" JNIEXPORT jbyteArray JNICALL
Java_org_aema_capture_LlmNative_generate(JNIEnv *env, jclass, jstring model_path,
        jstring user_prompt, jstring grammar_text, jint maximum_tokens, jint timeout_ms) {
    try {
        if (maximum_tokens < 1 || maximum_tokens > 128 || timeout_ms < 1 || timeout_ms > 120000)
            throw std::runtime_error("INVALID_ARGUMENT");
        auto started = Clock::now();
        Deadline deadline{started + std::chrono::milliseconds(timeout_ms)};
        auto path = utf8(env, model_path);
        auto input = utf8(env, user_prompt);
        auto grammar = utf8(env, grammar_text);
        if (input.size() > 12000 || grammar.size() > 4096)
            throw std::runtime_error("INPUT_TOO_LARGE");
        llama_log_set(quiet_log, nullptr); // Never send private prompts to logcat.
        llama_backend_init();
        auto params = llama_model_default_params();
        params.n_gpu_layers = 0;
        params.progress_callback = progress;
        params.progress_callback_user_data = &deadline;
        std::unique_ptr<llama_model, decltype(&llama_model_free)> model(
            llama_model_load_from_file(path.c_str(), params), llama_model_free);
        if (!model) throw std::runtime_error(abort_run(&deadline) ? "CANCELLED_OR_TIMEOUT" : "MODEL_LOAD_FAILED");
        char architecture[64] = {};
        llama_model_meta_val_str(model.get(), "general.architecture", architecture, sizeof(architecture));
        if (std::string(architecture) != "qwen3") throw std::runtime_error("MODEL_REQUIRES_QWEN3");
        const auto *vocab = llama_model_get_vocab(model.get());
        auto config = llama_context_default_params();
        config.n_ctx = 2048;
        config.n_batch = 256;
        config.n_ubatch = 128;
        config.n_threads = 4;
        config.n_threads_batch = 4;
        config.offload_kqv = false;
        config.abort_callback = abort_run;
        config.abort_callback_data = &deadline;
        std::unique_ptr<llama_context, decltype(&llama_free)> context(
            llama_init_from_model(model.get(), config), llama_free);
        if (!context) throw std::runtime_error("CONTEXT_INIT_FAILED");
        long load_ms = milliseconds(started);
        // Explicit Qwen3 non-thinking ChatML. Other architectures are rejected above.
        std::string prompt = "<|im_start|>system\nYou select evidence-grounded battery observations. "
            "Follow the JSON contract exactly.<|im_end|>\n<|im_start|>user\n" + input +
            "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n";
        std::vector<llama_token> tokens(2048);
        int count = llama_tokenize(vocab, prompt.data(), static_cast<int>(prompt.size()),
            tokens.data(), static_cast<int>(tokens.size()), true, true);
        if (count <= 0 || count + maximum_tokens > 2048) throw std::runtime_error("CONTEXT_TOO_LONG");
        auto prefill_start = Clock::now();
        for (int offset = 0; offset < count; offset += 256) {
            if (abort_run(&deadline)) throw std::runtime_error("CANCELLED_OR_TIMEOUT");
            auto batch = llama_batch_get_one(tokens.data() + offset, std::min(256, count - offset));
            if (llama_decode(context.get(), batch) != 0)
                throw std::runtime_error(abort_run(&deadline) ? "CANCELLED_OR_TIMEOUT" : "PREFILL_FAILED");
        }
        long prefill_ms = milliseconds(prefill_start);
        std::unique_ptr<llama_sampler, decltype(&llama_sampler_free)> sampler(
            llama_sampler_chain_init(llama_sampler_chain_default_params()), llama_sampler_free);
        auto *constraint = llama_sampler_init_grammar(vocab, grammar.c_str(), "root");
        if (!constraint) throw std::runtime_error("GRAMMAR_INVALID");
        llama_sampler_chain_add(sampler.get(), constraint);
        llama_sampler_chain_add(sampler.get(), llama_sampler_init_greedy());
        auto decode_start = Clock::now();
        std::string output, stop = "token_limit";
        int generated = 0;
        for (; generated < maximum_tokens; ) {
            if (abort_run(&deadline)) throw std::runtime_error("CANCELLED_OR_TIMEOUT");
            llama_token token = llama_sampler_sample(sampler.get(), context.get(), -1);
            if (llama_vocab_is_eog(vocab, token)) { stop = "eog"; break; }
            std::vector<char> piece(256);
            int size = llama_token_to_piece(vocab, token, piece.data(), piece.size(), 0, false);
            if (size < 0) {
                piece.resize(-size);
                size = llama_token_to_piece(vocab, token, piece.data(), piece.size(), 0, false);
            }
            if (size < 0) throw std::runtime_error("TOKEN_DECODE_FAILED");
            output.append(piece.data(), size);
            ++generated;
            if (!output.empty() && output.back() == '}') { stop = "structured_complete"; break; }
            auto batch = llama_batch_get_one(&token, 1);
            if (llama_decode(context.get(), batch) != 0)
                throw std::runtime_error(abort_run(&deadline) ? "CANCELLED_OR_TIMEOUT" : "DECODE_FAILED");
        }
        std::ostringstream result;
        struct rusage usage{};
        getrusage(RUSAGE_SELF, &usage);
        result << "{\"text\":" << quote(output) << ",\"prompt_tokens\":" << count
            << ",\"output_tokens\":" << generated << ",\"load_ms\":" << load_ms
            << ",\"prefill_ms\":" << prefill_ms << ",\"decode_ms\":" << milliseconds(decode_start)
            << ",\"elapsed_ms\":" << milliseconds(started)
            << ",\"worker_peak_rss_kib\":" << usage.ru_maxrss << ",\"stop_reason\":" << quote(stop) << "}";
        auto data = result.str();
        auto bytes = env->NewByteArray(static_cast<jsize>(data.size()));
        if (bytes) env->SetByteArrayRegion(bytes, 0, data.size(), reinterpret_cast<const jbyte *>(data.data()));
        return bytes;
    } catch (const std::exception &error) {
        env->ThrowNew(env->FindClass("java/lang/IllegalStateException"), error.what());
        return nullptr;
    }
}
