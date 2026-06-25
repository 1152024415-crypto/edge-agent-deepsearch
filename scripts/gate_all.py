#!/usr/bin/env python3
"""跑全部 4 道 gate。任一失败则整体失败（exit 1）。

用法: python scripts/gate_all.py
runtime 搜集产出 + 更新 index 后、push 前必须跑此脚本。
"""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
gates = ["gate_frontmatter.py", "gate_dedup.py", "gate_window.py", "gate_vendors.py"]
failed = []
for g in gates:
    print(f"\n=== {g} ===")
    r = subprocess.run([sys.executable, str(here / g)])
    if r.returncode != 0:
        failed.append(g)

if failed:
    print(f"\n[GATE ALL] FAILED: {failed}")
    sys.exit(1)
print("\n[GATE ALL] all 4 gates passed")
sys.exit(0)
