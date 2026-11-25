"""Bounded, local LoRA smoke experiment on synthetic evidence-selection labels.

Not a battery forecaster; does not modify the model installed in the Android app.
Run only in the isolated environment documented beside this script.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import platform
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("DO_NOT_TRACK", "1")

import psutil
import torch
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

MODEL = "Qwen/Qwen3-0.6B"
SYSTEM = "You select evidence-grounded battery observations. Follow the JSON contract exactly."


def prompt_text(prompt):
    # Match the app's explicit non-thinking ChatML prefix.
    return f"<|im_start|>system\n{SYSTEM}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n"


def encode(tokenizer, case):
    prefix = tokenizer(prompt_text(case["prepared"]["prompt"]), add_special_tokens=False)[
        "input_ids"
    ]
    target = tokenizer(case["target"] + "<|im_end|>", add_special_tokens=False)["input_ids"]
    assert len(prefix) + len(target) <= 768, "No silent truncation of training examples"
    return dict(
        input_ids=torch.tensor([prefix + target], device="cuda"),
        labels=torch.tensor([[-100] * len(prefix) + target], device="cuda"),
    )


@torch.no_grad()
def heldout_loss(model, encoded):
    model.eval()
    losses = [float(model(**row).loss) for row in encoded]
    return sum(losses) / len(losses)


@torch.no_grad()
def generations(model, tokenizer, cases):
    model.eval()
    result = []
    for case in cases:
        inputs = tokenizer(
            prompt_text(case["prepared"]["prompt"]), add_special_tokens=False, return_tensors="pt"
        ).to("cuda")
        output = model.generate(
            **inputs, do_sample=False, max_new_tokens=64, pad_token_id=tokenizer.eos_token_id
        )
        text = tokenizer.decode(output[0, inputs.input_ids.shape[1] :], skip_special_tokens=True)
        try:
            exact = json.loads(text) == json.loads(case["target"])
        except ValueError:
            exact = False
        result.append(dict(id=case["id"], exact_rule_match=exact, response=text))
    return result


def digest_parameters(model):
    digest = hashlib.sha256()
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            digest.update(name.encode())
            digest.update(parameter.detach().float().cpu().numpy().tobytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    assert len(args.revision) == 40
    assert torch.cuda.is_available(), "This protocol measures CUDA, not CPU training"
    torch.cuda.set_per_process_memory_fraction(0.60)
    torch.set_num_threads(4)
    set_seed(20261124)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    partitions = {
        split: [r for r in cases if r["split"] == split]
        for split in ("train", "validation", "test")
    }
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL, revision=args.revision, trust_remote_code=False
    )
    base = AutoModelForCausalLM.from_pretrained(
        MODEL,
        revision=args.revision,
        trust_remote_code=False,
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
    ).to("cuda")
    base.config.use_cache = False
    load_seconds = time.perf_counter() - started
    encoded = {
        split: [encode(tokenizer, row) for row in rows] for split, rows in partitions.items()
    }
    torch.cuda.reset_peak_memory_stats()
    baseline_loss = heldout_loss(base, encoded["test"])
    # Generation subset fixed by IDs before training. No grammar in this research arm.
    generation_cases = partitions["test"][:8]
    baseline_generations = generations(base, tokenizer, generation_cases)
    model = get_peft_model(
        base,
        LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"],
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    before = digest_parameters(model)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=2e-4)
    model.train()
    training = []
    rss_peak = psutil.Process().memory_info().rss
    training_started = time.perf_counter()
    # Exactly60 optimizer steps, microbatch1, accumulation2. No test-driven tuning.
    for step in range(60):
        optimizer.zero_grad(set_to_none=True)
        loss_value = 0.0
        for micro in range(2):
            row = encoded["train"][(step * 2 + micro) % len(encoded["train"])]
            loss = model(**row).loss
            assert torch.isfinite(loss), "nonfinite training loss"
            loss_value += float(loss.detach()) / 2
            (loss / 2).backward()
        norm = torch.nn.utils.clip_grad_norm_(
            (p for p in model.parameters() if p.requires_grad), 1.0
        )
        assert torch.isfinite(norm), "nonfinite gradients"
        optimizer.step()
        training.append(loss_value)
        rss_peak = max(rss_peak, psutil.Process().memory_info().rss)
        if step % 10 == 0:
            print(json.dumps(dict(step=step, loss=loss_value)), flush=True)
    torch.cuda.synchronize()
    training_seconds = time.perf_counter() - training_started
    after = digest_parameters(model)
    assert before != after, "adapter did not change"
    peak_allocated = torch.cuda.max_memory_allocated()
    peak_reserved = torch.cuda.max_memory_reserved()
    validation_loss = heldout_loss(model, encoded["validation"])
    adapted_loss = heldout_loss(model, encoded["test"])
    adapted_generations = generations(model, tokenizer, generation_cases)
    adapter = args.output / "adapter"
    model.save_pretrained(adapter, safe_serialization=True)
    files = {
        p.name: dict(size_bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in adapter.iterdir()
        if p.is_file()
    }
    # Reload into the same frozen base and verify one held-out forward loss.
    reference = float(model(**encoded["test"][0]).loss.detach())
    del model, base
    gc.collect()
    torch.cuda.empty_cache()
    clean_base = AutoModelForCausalLM.from_pretrained(
        MODEL,
        revision=args.revision,
        trust_remote_code=False,
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
    ).to("cuda")
    clean_base.config.use_cache = False
    reloaded = PeftModel.from_pretrained(clean_base, adapter).eval()
    restored = float(reloaded(**encoded["test"][0]).loss.detach())
    reload_abs_loss_error = abs(reference - restored)
    assert reload_abs_loss_error < 1e-5, (
        f"adapter reload parity failed: {reference} vs {restored} "
        f"(absolute error {reload_abs_loss_error})"
    )
    result = dict(
        synthetic=True,
        experiment="LoRA resource/learning smoke test, not personal battery forecasting",
        model=MODEL,
        revision=args.revision,
        python=platform.python_version(),
        versions={
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "peft", "psutil")
        },
        hardware=dict(
            gpu=torch.cuda.get_device_name(),
            gpu_total_bytes=torch.cuda.get_device_properties(0).total_memory,
            host_ram_bytes=psutil.virtual_memory().total,
        ),
        protocol=dict(
            steps=60,
            microbatch=1,
            accumulation=2,
            max_sequence_tokens=768,
            dtype="bfloat16",
            lora_rank=8,
            target_modules=["q_proj", "v_proj"],
            learning_rate=2e-4,
            seed=20261124,
            gpu_allocator_fraction=0.60,
            generation_grammar=False,
        ),
        partitions={name: len(rows) for name, rows in partitions.items()},
        cases_sha256=hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        trainable_parameters=trainable,
        total_parameters=total,
        model_load_seconds=load_seconds,
        training_seconds=training_seconds,
        peak_torch_allocated_bytes=peak_allocated,
        peak_torch_reserved_bytes=peak_reserved,
        sampled_training_host_peak_rss_bytes=rss_peak,
        losses=dict(
            first_training=training[0],
            last_training=training[-1],
            base_test=baseline_loss,
            adapted_test=adapted_loss,
            adapted_validation=validation_loss,
        ),
        baseline_generations=baseline_generations,
        adapted_generations=adapted_generations,
        training_losses=training,
        adapter_files=files,
        checks=dict(
            finite_loss_and_gradient="pass",
            adapter_parameters_changed=before != after,
            reload_abs_loss_error=reload_abs_loss_error,
        ),
        deployment="not_exported_or_installed; GGUF conversion/quantization and Android adapter parity untested",
    )
    (args.output / "lora-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "complete": True,
                "training_seconds": training_seconds,
                "losses": result["losses"],
                "peak_allocated_bytes": peak_allocated,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
