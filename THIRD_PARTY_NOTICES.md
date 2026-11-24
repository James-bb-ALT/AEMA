# Third-party notices for AEMA 2.0.0

## llama.cpp

The CPU inference library is built from ggml-org/llama.cpp, revision
`0ce7f213b0749fa4dee4e87d8ae7bf63e621c1ad`.

- Source: https://github.com/ggml-org/llama.cpp/tree/0ce7f213b0749fa4dee4e87d8ae7bf63e621c1ad
- Pinned source archive SHA-256: `89dbcaad6b45afefcc040ffdd2b54cdd0b628ce141fb3322300353db994a1fec`.
- License: MIT. The upstream copyright and permission notice is reproduced in
  [`llama.cpp-MIT.txt`](android/app/src/main/assets/licenses/llama.cpp-MIT.txt) and packaged in the APK.
- AEMA adds a separate JNI bridge. It does not modify the pinned upstream source.

## Optional bundled Qwen3 model

The self-contained APK includes the official Qwen3-0.6B Q8_0 GGUF from the Qwen team.
The smaller APK contains the runtime and requires importing compatible Qwen3 GGUF weights.

- Source: https://huggingface.co/Qwen/Qwen3-0.6B-GGUF
- Repository revision: `23749fefcc72300e3a2ad315e1317431b06b590a`.
- File: `Qwen3-0.6B-Q8_0.gguf`, 639,446,688 bytes.
- SHA-256: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
- License: Apache License 2.0. The producer's supplied license is reproduced in
  [`Qwen-Apache-2.0.txt`](android/app/src/main/assets/licenses/Qwen-Apache-2.0.txt) and packaged in the APK.
- The bundled weights are not fine-tuned by AEMA and are not represented as a validated battery predictor.
- No endorsement by either upstream project is implied.

The source repository does not track model weights. Build-time network retrieval of
the pinned native source does not grant the Android app network permission. No model
download or external inference service runs inside AEMA.

Existing dependencies retain their own licenses and versions. This file documents
the inference components added in 2.0.0; it does not replace upstream notices.
