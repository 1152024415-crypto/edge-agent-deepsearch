"""公共工具：读 frontmatter / index / vendors，统一错误收集与退出。

所有 gate 脚本 import 本模块复用。退出码：0=通过，1=有错误。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_ERRORS = []


def err(msg):
    _ERRORS.append(msg)


def read_frontmatter(md_path):
    """提取 markdown 文件 --- 之间 YAML frontmatter，返回 dict；无则 None。"""
    import yaml
    text = Path(md_path).read_text(encoding="utf-8-sig")
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", text, re.S)
    if not m:
        return None
    return yaml.safe_load(m.group(1))


def read_index():
    p = ROOT / "data" / "index.json"
    return json.loads(p.read_text(encoding="utf-8"))


def list_papers():
    d = ROOT / "content" / "papers"
    if not d.exists():
        return []
    return sorted(d.glob("*.md"))


def list_posts():
    """Backward-compatible alias while older gate scripts are migrated."""
    return list_papers()


def read_vendors():
    import yaml
    p = ROOT / "data" / "vendors.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def vendor_names(vendors_yaml):
    names = [v["name"] for v in vendors_yaml.get("device_vendors", [])]
    names += [v["name"] for v in vendors_yaml.get("model_vendors", [])]
    return set(names)


def finish():
    if _ERRORS:
        print(f"[FAIL] {len(_ERRORS)} error(s):")
        for e in _ERRORS:
            print(f"  - {e}")
        sys.exit(1)
    print("[OK] gate passed")
    sys.exit(0)
