#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fourth-pass filter: title-based strong signal OR very specific abstract phrase."""
import json, re, sys

with open("D:/proj/edge_agent/data/_arxiv_collect.json","r",encoding="utf-8") as f:
    data = json.load(f)
kept = data["kept"]

# Strong, specific phrases. Matching in TITLE => contribution is about edge/inference-efficiency.
TITLE_STRONG = [
    "on-device","on device","edge device","edge ai","edge inference","edge computing",
    "edge llm","edge cloud","edge server","edge tpu","edge offload","edge-cloud","cloud-edge",
    "mobile","smartphone","iot","embedded","microcontroller","npu","mcu",
    "resource-constrain","resource constrain","low-resource","low resource",
    "memory-constrain","memory constrain","energy-efficient","energy efficient",
    "low-power","low power","power-efficient","battery",
    "quantiz","int8","int4","low-bit","fixed-point","weight-only","mixed-precision",
    "pruning","prune","sparsif","sparsity","structured spars","weight sharing",
    "distill","knowledge distill","model compression","compact","lightweight",
    "kv cache","key-value cache","kv-cache","paged attention","pagedattention","radix",
    "speculative","draft model","early exit","early exiting","cascade",
    "efficient inference","efficient transformer","efficient attention",
    "linear attention","flash attention","flashattention","grouped-query","grouped query",
    " gqa","multi-query","sliding window","window attention","sparse attention",
    "efficient ","accelerat","speedup","speed up","low-latency","low latency",
    "high-throughput","high throughput","inference accele","hardware accele",
    "systolic","fpga","asic","tensor core","gpu kernel","cuda",
    "small language model","small model"," slm","lora","low-rank adapt","low rank adapt",
    "adapter","peft","parameter-efficient","parameter efficient",
    "mixture of experts","moe","expert routing","conditional computation",
    "serving","inference engine","vllm","tensorrt","tensor rt","llama.cpp","llamacpp",
    "onnx runtime","onnxruntime","tflite","wasm","webgpu","model serving",
    "continuous batching","batching","dynamic batching","request scheduling",
    "inference latency","serving system","disaggregated inference",
    "federated","edge collaboration","offload","offloading","hybrid inference",
    "agent memory","memory augmented","tool use","tool-use","tool calling",
    "function calling","llm agent","agent framework","edge agent","agent inference",
]

# Very specific abstract phrases (rare enough to not false-positive broadly).
ABS_SPECIFIC = [
    "on-device","on device","edge device","edge ai","edge inference","edge computing",
    "edge llm","edge cloud","edge tpu","edge offload","edge-cloud","cloud-edge",
    "mobile device","smartphone","mobile llm","mobile inference","mobilebert","mobilellm","edgebert",
    "iot device","embedded device","embedded system","microcontroller"," mcu "," npu ",
    "resource-constrain","resource constrain","resource-limited","low-resource deployment",
    "memory-constrain","memory constrain","memory footprint","compute-bound","memory-bound",
    "energy-efficient inference","energy efficient inference","low-power","low power","battery",
    "int8","int4","int2","low-bit","weight-only quantiz","mixed-precision quantiz","quantiz",
    "structured spars","weight pruning","model pruning","knowledge distill","model compression",
    "compact model","lightweight model",
    "kv cache","key-value cache","kv-cache","pagedattention","paged attention","radixattention",
    "speculative decoding","speculative execution","draft model","self-speculative","early exit",
    "efficient inference","efficient transformer","efficient attention","linear attention",
    "flash attention","flashattention","grouped-query","grouped query"," gqa ","multi-query",
    "sliding window attention","sparse attention","approximate attention",
    "inference accele","hardware accele","tensor core","gpu kernel","cuda kernel","fpga","asic",
    "small language model"," slm ","lightweight language model","lora","low-rank adapt","low rank adapt",
    "parameter-efficient","parameter efficient","peft","mixture of experts"," moe ","expert routing",
    "conditional computation",
    "vllm","tensorrt","tensor rt","llama.cpp","llamacpp","onnx runtime","onnxruntime","tflite",
    " webgpu","model serving","continuous batching","dynamic batching","pagedattention",
    "disaggregated inference","serving system","inference engine","inference latency",
    "federated learning","edge collaboration","edge-cloud collaboration","cloud-edge",
    "offload inference","offloading inference","hybrid inference",
    "agent memory","tool use","tool-use","tool calling","function calling","llm agent",
    "agent framework","edge agent","agent inference",
    "deploy on edge","deploy on mobile","on mobile device","on edge device",
    "reduce latency","reduce memory","memory-efficient","memory efficient","compute-efficient",
    "inference throughput","inference speedup","faster inference","accelerate inference",
    "edge deployment","mobile deployment","on-device deployment",
]

EXCLUDE_STRONG = [
    "medical triage","clinical recall","patient triage",
    "cryptograph","post-quantum crypt","blockchain",
    "face recognition","face hallucination","talking head","deepfake",
    "hyperparameter optimization","neural architecture search","automl",
    "text-to-video","video generation","world model",
    "gui agent","ui automation","mobile gui","screen interaction",
    "image inpainting","image editing","object removal","image restoration",
    "image super-resolution","image denois","image deblur",
    "video inpaint","video editing",
]

def text(p): return (p["title"]+" "+p["summary"]).lower()
def title(p): return p["title"].lower()
def has_any(t,kws): return any(k in t for k in kws)

def keep(p):
    t = text(p); ti = title(p)
    for k in EXCLUDE_STRONG:
        if k in t: return False,"exclude:"+k
    # title strong => in scope
    if has_any(ti, TITLE_STRONG): return True,"title"
    # abstract very specific phrase
    if has_any(t, ABS_SPECIFIC): return True,"abs-spec"
    return False,"no-anchor"

kept2=[]; dropped2=[]
for p in kept:
    ok,reason=keep(p)
    (kept2 if ok else dropped2).append((p,reason))
kept2.sort(key=lambda x:x[0]["published"],reverse=True)

def date_str(d): return d[:10] if d else ""
def guess_dirs(p):
    t=(p["title"]+" "+p["summary"]).lower(); d=[]
    if "quantiz" in t or "int8" in t or "int4" in t or "low-bit" in t: d.append("quantization")
    if "kv cache" in t or "key-value cache" in t or "key value cache" in t or "kv-cache" in t: d.append("kv-cache")
    if "speculative" in t: d.append("spec-decoding")
    if "pruning" in t or "prune" in t or "spars" in t: d.append("pruning/sparse")
    if "distill" in t: d.append("distillation")
    if "small language model" in t or " slm" in t or "lightweight" in t: d.append("small-model")
    if any(k in t for k in ["on-device","on device","edge device","mobile","npu","embedded","microcontroller","smartphone","iot"]): d.append("on-device/edge")
    if "federated" in t: d.append("federated")
    if any(k in t for k in ["agent memory","tool use","tool-use","llm agent","agent framework","function calling"]): d.append("agent/tool")
    if any(k in t for k in ["serving","vllm","tensorrt","inference engine","throughput","batching","continuous batching","pagedattention"]): d.append("serving")
    if "attention" in t and any(k in t for k in ["efficient","linear","sparse","flash","sliding","grouped"]): d.append("efficient-attn")
    if any(k in t for k in ["lora","low-rank","low rank","adapter","peft","parameter-efficient"]): d.append("peft/low-rank")
    if any(k in t for k in ["mixture of experts"," moe "]): d.append("moe")
    if "offload" in t or "edge-cloud" in t or "cloud-edge" in t: d.append("edge-cloud")
    if not d: d.append("general-edge")
    seen=set();out=[]
    for x in d:
        if x not in seen: seen.add(x);out.append(x)
    return ",".join(out[:3])
def one_liner(p):
    s=re.sub(r"\s+"," ",p["summary"]).strip()
    if len(s)>110: s=s[:107]+"..."
    return s

with open("D:/proj/edge_agent/data/_arxiv_collect_filtered.json","w",encoding="utf-8") as f:
    json.dump({"kept":[p for p,_ in kept2],"dropped":[{"id":p["id"],"title":p["title"],"published":p["published"],"reason":r} for p,r in dropped2]},f,ensure_ascii=False,indent=2)

print(f"# TOTAL: {len(kept2)}")
for p,_ in kept2:
    ds=date_str(p["published"]); ti=p["title"][:80]; url=f"https://arxiv.org/abs/{p['id']}"
    print(f"{p['id']} | {ds} | {ti} | {url} | {guess_dirs(p)} | {one_liner(p)}")

sys.stderr.write(f"kept={len(kept2)} dropped={len(dropped2)}\n")
sys.stderr.write("\n--- DROPPED titles (sanity) ---\n")
for p,r in dropped2:
    sys.stderr.write(f"{p['id']} | {p['title'][:75]} | {r}\n")
