#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Final curation: remove clear off-topic false positives, add back in-scope drops."""
import json, re, sys

with open("D:/proj/edge_agent/data/_arxiv_collect.json","r",encoding="utf-8") as f:
    raw = json.load(f)["kept"]
with open("D:/proj/edge_agent/data/_arxiv_collect_filtered.json","r",encoding="utf-8") as f:
    cur = json.load(f)["kept"]

# current kept ids
cur_ids = {p["id"] for p in cur}
raw_by_id = {p["id"]: p for p in raw}

# IDs to remove (clear off-topic false positives)
REMOVE = {
    "2606.28217v1","2606.28186v1","2606.28252v1","2606.27974v1","2606.27069v1",
    "2606.26426v1","2606.26403v1","2606.26382v1","2606.26277v1","2606.26003v1",
    "2606.25964v1","2606.25699v1","2606.25673v1","2606.25436v1","2606.25386v1",
    "2606.25342v1","2606.25313v1","2606.25256v1","2606.25215v1","2606.24808v1",
    "2606.24781v1","2606.24748v2","2606.24983v1","2606.24589v1","2606.24585v1",
    "2606.24453v1","2606.24259v1","2606.24046v1","2606.23957v1","2606.24941v1",
    "2606.23891v1","2606.23626v1","2606.23286v1","2606.23277v1","2606.23125v1",
    "2606.23050v1","2606.22939v1","2606.22837v1","2606.22776v1","2606.22682v1",
    "2606.22333v1","2606.22218v1","2606.21970v1","2606.21963v1","2606.21900v1",
    "2606.27147v1",  # safe autoregressive image generation (image gen)
    "2606.26595v1",  # LLM detecting emerging topics in service feedback
    "2606.26451v1",  # music singing evaluation
    "2606.26627v1",  # privacy in LLM agents survey (not efficiency)
    "2606.27069v2",  # judicial discretion legal (v2 was the real id)
    "2606.27180v1",  # RL reward shaping (training theory)
    "2606.26050v1",  # natural ungrokking pretraining theory
    "2606.24994v1",  # trajectory optimization for RLVR (training)
    "2606.22110v1",  # TraceView visualization tool (not inference)
    "2606.24173v2" if False else "2606.24173v1",  # placeholder no-op
}
# remove placeholder no-op
REMOVE.discard("2606.24173v2")
REMOVE.discard("2606.24173v1")

# IDs to add back from raw (in-scope but were dropped)
ADD_BACK = {
    "2606.28070v1",  # JD Oxygen industrial LLM/VLM serving system
    "2606.23546v1",  # Energy Consumption of Transformer Fine-Tuning (roofline)
    "2606.23112v1",  # Self-Evolution Multi-Turn Tool-Calling Agents
    "2606.25553v1",  # Latency-Aware Service Placement for Edge
    "2606.22588v1",  # Non-Uniform L2 Cache Latency NVIDIA SM (GPU hardware/serving)
    "2606.22635v1",  # Neuromorphic Silicon Suite (edge hardware)
    "2606.25277v1",  # Integrated HW-SW Design Low-Data Spatial Defect Detection (edge)
}

final = [p for p in cur if p["id"] not in REMOVE]
for aid in ADD_BACK:
    if aid in raw_by_id and aid not in {p["id"] for p in final}:
        final.append(raw_by_id[aid])

final.sort(key=lambda p: p["published"], reverse=True)

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
    if any(k in t for k in ["agent memory","tool use","tool-use","llm agent","agent framework","function calling","tool-calling","tool calling"]): d.append("agent/tool")
    if any(k in t for k in ["serving","vllm","tensorrt","inference engine","throughput","batching","continuous batching","pagedattention"]): d.append("serving")
    if "attention" in t and any(k in t for k in ["efficient","linear","sparse","flash","sliding","grouped","value-only","value space"]): d.append("efficient-attn")
    if any(k in t for k in ["lora","low-rank","low rank","adapter","peft","parameter-efficient"]): d.append("peft/low-rank")
    if any(k in t for k in ["mixture of experts"," moe ","expert pruning","intra-expert"]): d.append("moe")
    if "offload" in t or "edge-cloud" in t or "cloud-edge" in t or "edge cloud" in t: d.append("edge-cloud")
    if "energy" in t or "low-power" in t or "low power" in t: d.append("energy/low-power")
    if "fpga" in t or "asic" in t or "memrist" in t or "nems" in t or "neuromorphic" in t or "p-bit" in t: d.append("edge-hw")
    if not d: d.append("general-edge")
    seen=set();out=[]
    for x in d:
        if x not in seen: seen.add(x);out.append(x)
    return ",".join(out[:3])
def one_liner(p):
    s=re.sub(r"\s+"," ",p["summary"]).strip()
    if len(s)>110: s=s[:107]+"..."
    return s

with open("D:/proj/edge_agent/data/_arxiv_final.json","w",encoding="utf-8") as f:
    json.dump(final,f,ensure_ascii=False,indent=2)

print(f"# TOTAL: {len(final)}")
for p in final:
    ds=date_str(p["published"]); ti=p["title"][:80]; url=f"https://arxiv.org/abs/{p['id']}"
    print(f"{p['id']} | {ds} | {ti} | {url} | {guess_dirs(p)} | {one_liner(p)}")
