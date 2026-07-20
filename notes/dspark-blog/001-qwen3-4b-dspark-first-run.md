# DeepSpec Qwen3-4B DSpark 首次运行实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前机器的 WSL2 Ubuntu 22.04 CPU 环境中调用 DeepSpec 官方 Qwen3 DSpark evaluator 完成一次 Qwen3-4B 真实生成，并保存可复现的实验记录和关键代码解读。

**Architecture:** 使用一个最小本地 runner 绕过 DeepSpec 面向 CUDA/NCCL 多卡评测的 `BaseEvaluator.__init__`，但继续调用官方 `Qwen3DSparkEvaluator.build_models()`、`generate_one_sample()` 和底层 proposal/verification 实现。runner 只增加 CLI、CPU 设备选择、进程峰值 RSS 监控和 JSON 序列化；实验结论以实际日志为准，不修改 DSpark 算法代码。

**Tech Stack:** Python 3、PyTorch 2.9.1、Transformers 5.10.2、DeepSpec、Hugging Face Hub、WSL2 Ubuntu 22.04、PowerShell、pytest、psutil

---

## 文件结构

- Create: `scripts/local/inspect_environment.ps1` — 采集 Windows、WSL、CPU、GPU、内存、磁盘和 Git 基线。
- Create: `experiments/first_run_qwen3_4b.py` — 调用官方 evaluator 执行一条 prompt 并输出 JSON。
- Create: `experiments/requirements-local.txt` — 本地 runner 额外依赖。
- Create: `tests/experiments/test_first_run_qwen3_4b.py` — 验证纯指标汇总和参数构造，不下载模型。
- Create: `results/first-run-qwen3-4b/environment.json` — 环境快照。
- Create: `results/first-run-qwen3-4b/run.json` — 成功运行的结构化结果。
- Create: `results/first-run-qwen3-4b/run.log` — 成功运行的完整控制台日志。
- Create: `specs/001-qwen3-4b-dspark-first-run-record.md` — 实际命令、错误、修复、结果和代码解读。
- Modify: `.gitignore` — 忽略本地虚拟环境、Python 缓存和临时下载文件。

### Task 1: 固定本地实验目录与环境快照

**Files:**
- Create: `scripts/local/inspect_environment.ps1`
- Create: `results/first-run-qwen3-4b/environment.json`
- Modify: `.gitignore`

- [ ] **Step 1: 在 `.gitignore` 中加入本地实验忽略项**

追加：

```gitignore
.venv/
.pytest_cache/
**/__pycache__/
results/first-run-qwen3-4b/*.tmp
```

- [ ] **Step 2: 创建环境采集脚本**

创建 `scripts/local/inspect_environment.ps1`：

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$resultDir = Join-Path $repoRoot 'results\first-run-qwen3-4b'
New-Item -ItemType Directory -Force -Path $resultDir | Out-Null

$computer = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$os = Get-CimInstance Win32_OperatingSystem
$gpus = Get-CimInstance Win32_VideoController | ForEach-Object {
    [ordered]@{
        name = $_.Name
        driver_version = $_.DriverVersion
        adapter_ram_bytes = $_.AdapterRAM
    }
}
$drive = Get-PSDrive -Name ((Split-Path $repoRoot -Qualifier).TrimEnd(':'))
$wslStatus = (& wsl.exe --status 2>&1 | Out-String).Trim()
$wslVersion = (& wsl.exe -d Ubuntu-22.04 -- bash -lc 'uname -a; python3 --version 2>&1 || true' 2>&1 | Out-String).Trim()

$payload = [ordered]@{
    captured_at = (Get-Date).ToString('o')
    repository = $repoRoot.Path
    git_commit = (& git -C $repoRoot rev-parse HEAD).Trim()
    git_branch = (& git -C $repoRoot branch --show-current).Trim()
    windows = [ordered]@{
        caption = $os.Caption
        version = $os.Version
        architecture = $os.OSArchitecture
    }
    cpu = [ordered]@{
        name = $cpu.Name
        cores = $cpu.NumberOfCores
        logical_processors = $cpu.NumberOfLogicalProcessors
    }
    memory = [ordered]@{
        total_bytes = [int64]$computer.TotalPhysicalMemory
        free_bytes = [int64]$os.FreePhysicalMemory * 1KB
    }
    disk = [ordered]@{
        drive = $drive.Name
        free_bytes = [int64]$drive.Free
        used_bytes = [int64]$drive.Used
    }
    gpus = @($gpus)
    wsl_status = $wslStatus
    wsl_probe = $wslVersion
}

$outputPath = Join-Path $resultDir 'environment.json'
$payload | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $outputPath
Write-Host $outputPath
```

- [ ] **Step 3: 执行环境采集脚本**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local/inspect_environment.ps1
```

Expected: 输出 `results\first-run-qwen3-4b\environment.json` 的绝对路径，命令退出码为 0。

- [ ] **Step 4: 检查快照不包含凭据**

Run:

```powershell
rg -n -i "token|password|secret|authorization|hf_" results/first-run-qwen3-4b/environment.json
```

Expected: 无匹配，`rg` 退出码为 1。

- [ ] **Step 5: 确认 WSL 能访问仓库路径**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'test -d /mnt/d/proj/dspark-blog/deepspec && echo READY'
```

Expected: `READY`。

- [ ] **Step 6: 创建 WSL 虚拟环境并安装官方依赖和测试工具**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip setuptools wheel && .venv/bin/python -m pip install -r requirements.txt "psutil>=5.9,<8" "pytest>=8,<10"'
```

Expected: 退出码 0；若官方固定版本没有适配当前 Python 的 wheel，保留完整错误，安装该 wheel 支持的 Python 版本后删除并重建 `.venv`，不修改 DeepSpec 固定的依赖版本。

- [ ] **Step 7: 验证 WSL Python 可以导入 DeepSpec**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -c "import torch, transformers; from deepspec.eval.dspark import Qwen3DSparkEvaluator; print(torch.__version__, transformers.__version__, torch.cuda.is_available(), Qwen3DSparkEvaluator.__name__)"'
```

Expected: 打印 `2.9.1 5.10.2 False Qwen3DSparkEvaluator`。

- [ ] **Step 8: 提交环境脚本与快照**

先检查 `.agent/config.yml`；该文件不存在时按 `auto_commit: true` 处理。

```powershell
git add .gitignore scripts/local/inspect_environment.ps1 results/first-run-qwen3-4b/environment.json
git commit -m "chore: capture DeepSpec experiment environment"
```

Expected: commit 成功，工作树干净。

### Task 2: 为最小 runner 定义可测试的指标接口

**Files:**
- Create: `experiments/first_run_qwen3_4b.py`
- Create: `experiments/requirements-local.txt`
- Create: `tests/experiments/test_first_run_qwen3_4b.py`

- [ ] **Step 1: 创建本地附加依赖文件**

创建 `experiments/requirements-local.txt`：

```text
psutil>=5.9,<8
pytest>=8,<10
```

- [ ] **Step 2: 写指标汇总的失败测试**

创建 `tests/experiments/test_first_run_qwen3_4b.py`：

```python
from types import SimpleNamespace

from experiments.first_run_qwen3_4b import build_args, summarize_response


def test_build_args_uses_official_qwen3_4b_pair():
    args = build_args(
        target_model="Qwen/Qwen3-4B",
        draft_model="deepseek-ai/dspark_qwen3_4b_block7",
        max_new_tokens=32,
        temperature=0.0,
    )

    assert args.target_name_or_path == "Qwen/Qwen3-4B"
    assert args.draft_name_or_path == "deepseek-ai/dspark_qwen3_4b_block7"
    assert args.max_new_tokens == 32
    assert args.temperature == 0.0
    assert args.confidence_threshold == 0.0
    assert args.tasks == []


def test_summarize_response_reports_acceptance_metrics():
    response = SimpleNamespace(
        num_input_tokens=9,
        num_output_tokens=8,
        verify_count=2,
        proposal_lengths=[7, 7],
        accepted_draft_lengths=[4, 2],
        acceptance_lengths=[5, 3],
    )

    result = summarize_response(response)

    assert result == {
        "num_input_tokens": 9,
        "num_output_tokens": 8,
        "verify_count": 2,
        "proposal_lengths": [7, 7],
        "accepted_draft_lengths": [4, 2],
        "acceptance_lengths": [5, 3],
        "average_proposal_length": 7.0,
        "average_accepted_draft_length": 3.0,
        "average_acceptance_length": 4.0,
    }


def test_summarize_response_handles_zero_verifications():
    response = SimpleNamespace(
        num_input_tokens=9,
        num_output_tokens=1,
        verify_count=0,
        proposal_lengths=[],
        accepted_draft_lengths=[],
        acceptance_lengths=[],
    )

    result = summarize_response(response)

    assert result["average_proposal_length"] == 0.0
    assert result["average_accepted_draft_length"] == 0.0
    assert result["average_acceptance_length"] == 0.0
```

- [ ] **Step 3: 创建只有接口的 runner 并验证测试失败**

创建 `experiments/first_run_qwen3_4b.py`：

```python
from __future__ import annotations

from types import SimpleNamespace


def build_args(
    *,
    target_model: str,
    draft_model: str,
    max_new_tokens: int,
    temperature: float,
) -> SimpleNamespace:
    raise NotImplementedError


def summarize_response(response: SimpleNamespace) -> dict[str, object]:
    raise NotImplementedError
```

Run:

```bash
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m pytest tests/experiments/test_first_run_qwen3_4b.py -v'
```

Expected: 3 tests fail with `NotImplementedError`.

- [ ] **Step 4: 实现最小参数和指标汇总函数**

将 runner 更新为：

```python
from __future__ import annotations

from types import SimpleNamespace


def build_args(
    *,
    target_model: str,
    draft_model: str,
    max_new_tokens: int,
    temperature: float,
) -> SimpleNamespace:
    return SimpleNamespace(
        target_name_or_path=target_model,
        draft_name_or_path=draft_model,
        max_new_tokens=int(max_new_tokens),
        temperature=float(temperature),
        confidence_threshold=0.0,
        tensorboard_dir=None,
        step=None,
        seed=980406,
        tasks=[],
    )


def _average(values: list[int]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def summarize_response(response: SimpleNamespace) -> dict[str, object]:
    proposal_lengths = [int(value) for value in response.proposal_lengths]
    accepted_draft_lengths = [
        int(value) for value in response.accepted_draft_lengths
    ]
    acceptance_lengths = [int(value) for value in response.acceptance_lengths]
    return {
        "num_input_tokens": int(response.num_input_tokens),
        "num_output_tokens": int(response.num_output_tokens),
        "verify_count": int(response.verify_count),
        "proposal_lengths": proposal_lengths,
        "accepted_draft_lengths": accepted_draft_lengths,
        "acceptance_lengths": acceptance_lengths,
        "average_proposal_length": _average(proposal_lengths),
        "average_accepted_draft_length": _average(accepted_draft_lengths),
        "average_acceptance_length": _average(acceptance_lengths),
    }
```

- [ ] **Step 5: 运行测试确认通过**

Run:

```bash
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m pytest tests/experiments/test_first_run_qwen3_4b.py -v'
```

Expected: `3 passed`。

- [ ] **Step 6: 提交可测试接口**

先检查 `.agent/config.yml`；该文件不存在时按 `auto_commit: true` 处理。

```bash
git add experiments/requirements-local.txt experiments/first_run_qwen3_4b.py tests/experiments/test_first_run_qwen3_4b.py
git commit -m "test: define DeepSpec first-run metrics"
```

Expected: commit 成功。

### Task 3: 实现调用官方 evaluator 的 CPU runner

**Files:**
- Modify: `experiments/first_run_qwen3_4b.py`
- Modify: `tests/experiments/test_first_run_qwen3_4b.py`

- [ ] **Step 1: 增加默认 CLI 参数测试**

在测试文件追加：

```python
from experiments.first_run_qwen3_4b import parse_args


def test_parse_args_defaults_to_first_run_models():
    args = parse_args([])

    assert args.target_model == "Qwen/Qwen3-4B"
    assert args.draft_model == "deepseek-ai/dspark_qwen3_4b_block7"
    assert args.prompt == "Explain speculative decoding in one short paragraph."
    assert args.max_new_tokens == 32
    assert args.device == "cpu"
```

- [ ] **Step 2: 运行测试验证 CLI 尚不存在**

Run:

```bash
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m pytest tests/experiments/test_first_run_qwen3_4b.py::test_parse_args_defaults_to_first_run_models -v'
```

Expected: collection fails because `parse_args` cannot be imported。

- [ ] **Step 3: 将 runner 扩展为完整最小执行脚本**

保留 Task 2 的三个函数，并在同一文件加入以下代码：

```python
import argparse
import json
import os
import threading
import time
from pathlib import Path

import psutil
import torch

from deepspec.data.parser import encode_chat_messages
from deepspec.eval.base_evaluator import resolve_stop_token_ids
from deepspec.eval.dspark import Qwen3DSparkEvaluator
from deepspec.utils import seed_all


DEFAULT_TARGET = "Qwen/Qwen3-4B"
DEFAULT_DRAFT = "deepseek-ai/dspark_qwen3_4b_block7"
DEFAULT_PROMPT = "Explain speculative decoding in one short paragraph."


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-model", default=DEFAULT_TARGET)
    parser.add_argument("--draft-model", default=DEFAULT_DRAFT)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


class PeakRSSMonitor:
    def __init__(self) -> None:
        self.process = psutil.Process(os.getpid())
        self.peak_rss_bytes = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self._stop.wait(0.1):
            self.peak_rss_bytes = max(
                self.peak_rss_bytes,
                int(self.process.memory_info().rss),
            )

    def __enter__(self) -> "PeakRSSMonitor":
        self.peak_rss_bytes = int(self.process.memory_info().rss)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.peak_rss_bytes = max(
            self.peak_rss_bytes,
            int(self.process.memory_info().rss),
        )
        self._stop.set()
        self._thread.join()


def build_local_evaluator(args: SimpleNamespace, device: torch.device):
    evaluator = Qwen3DSparkEvaluator.__new__(Qwen3DSparkEvaluator)
    evaluator.args = args
    evaluator.device = device
    evaluator.global_rank = 0
    evaluator.world_size = 1
    evaluator.tasks = []
    evaluator.target_model, evaluator.draft_model, evaluator.tokenizer = (
        evaluator.build_models()
    )
    evaluator.confidence_head_recorder = None
    evaluator.metrics_rows = []
    return evaluator


def run(args: argparse.Namespace) -> dict[str, object]:
    experiment_args = build_args(
        target_model=args.target_model,
        draft_model=args.draft_model,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
    )
    device = torch.device(args.device)
    seed_all(int(experiment_args.seed))

    started_at = time.time()
    with PeakRSSMonitor() as memory:
        load_started = time.perf_counter()
        evaluator = build_local_evaluator(experiment_args, device)
        load_seconds = time.perf_counter() - load_started

        messages = [{"role": "user", "content": args.prompt}]
        input_ids = encode_chat_messages(
            evaluator.tokenizer,
            messages,
            add_generation_prompt=True,
            enable_thinking=False,
        ).to(device)
        stop_token_ids = resolve_stop_token_ids(
            evaluator.target_model,
            evaluator.tokenizer,
        )

        generation_started = time.perf_counter()
        response = evaluator.generate_one_sample(
            input_ids=input_ids,
            stop_token_ids=stop_token_ids,
        )
        generation_seconds = time.perf_counter() - generation_started

        generated_ids = response.output_ids[0, response.num_input_tokens :]
        generated_text = evaluator.tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        )

    result = {
        "status": "success",
        "started_at_unix": started_at,
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
        "target_model": args.target_model,
        "draft_model": args.draft_model,
        "device": str(device),
        "torch_version": torch.__version__,
        "prompt": args.prompt,
        "generated_text": generated_text,
        "max_new_tokens": int(args.max_new_tokens),
        "temperature": float(args.temperature),
        "model_load_seconds": load_seconds,
        "generation_seconds": generation_seconds,
        "peak_rss_bytes": int(memory.peak_rss_bytes),
        "metrics": summarize_response(response),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def main() -> None:
    args = parse_args()
    result = run(args)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行全部轻量测试**

Run:

```bash
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m pytest tests/experiments/test_first_run_qwen3_4b.py -v'
```

Expected: `4 passed`，且不下载模型。

- [ ] **Step 5: 检查 runner 可以显示帮助**

Run:

```bash
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m experiments.first_run_qwen3_4b --help'
```

Expected: 输出 target、draft、prompt、max-new-tokens、temperature、device 和 output 参数。

- [ ] **Step 6: 提交 CPU runner**

先检查 `.agent/config.yml`；该文件不存在时按 `auto_commit: true` 处理。

```bash
git add experiments/first_run_qwen3_4b.py tests/experiments/test_first_run_qwen3_4b.py
git commit -m "feat: add local DeepSpec DSpark runner"
```

Expected: commit 成功。

### Task 4: 在 WSL2 中建立 DeepSpec CPU 环境

**Files:**
- Create: `.venv/` — Git 忽略的 WSL Python 虚拟环境。
- Create: `results/first-run-qwen3-4b/pip-freeze.txt`

- [ ] **Step 1: 确认 WSL 能访问仓库路径**

Run from PowerShell:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'test -d /mnt/d/proj/dspark-blog/deepspec && echo READY'
```

Expected: `READY`。

- [ ] **Step 2: 创建虚拟环境并升级安装工具**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip setuptools wheel'
```

Expected: 退出码 0，`.venv/bin/python` 存在。

- [ ] **Step 3: 安装官方依赖和本地实验依赖**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m pip install -r requirements.txt -r experiments/requirements-local.txt'
```

Expected: 退出码 0；若 `torch==2.9.1` 或 `triton==3.5.1` 没有适配当前 Python 的 wheel，保留完整错误到 record spec，并先升级 Ubuntu 的 Python 到官方 wheel 支持版本，再重建 `.venv`，不修改 DeepSpec 的依赖版本。

- [ ] **Step 4: 验证 CPU PyTorch 与 DeepSpec 导入**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -c "import torch, transformers; from deepspec.eval.dspark import Qwen3DSparkEvaluator; print(torch.__version__); print(transformers.__version__); print(torch.cuda.is_available()); print(Qwen3DSparkEvaluator.__name__)"'
```

Expected: 打印 `2.9.1`、`5.10.2`、`False` 和 `Qwen3DSparkEvaluator`。

- [ ] **Step 5: 保存最终依赖版本**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m pip freeze > results/first-run-qwen3-4b/pip-freeze.txt'
```

Expected: 文件包含 `torch==2.9.1` 和 `transformers==5.10.2`。

- [ ] **Step 6: 提交依赖快照**

先检查 `.agent/config.yml`；该文件不存在时按 `auto_commit: true` 处理。

```powershell
git add results/first-run-qwen3-4b/pip-freeze.txt
git commit -m "chore: record DeepSpec runtime dependencies"
```

Expected: commit 成功。

### Task 5: 执行 Qwen3-4B DSpark 真实生成

**Files:**
- Create: `results/first-run-qwen3-4b/run.json`
- Create: `results/first-run-qwen3-4b/run.log`

- [ ] **Step 1: 检查磁盘与可用内存**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'df -h /mnt/d; free -h'
```

Expected: D 盘至少 20 GB 可用，WSL 可用内存至少 12 GB；不满足时停止模型下载并在 record spec 记录资源阻塞。

- [ ] **Step 2: 运行 8-token 预检并保存日志**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && set -o pipefail && .venv/bin/python -m experiments.first_run_qwen3_4b --max-new-tokens 8 --device cpu --output results/first-run-qwen3-4b/run.tmp 2>&1 | tee results/first-run-qwen3-4b/preflight.log'
```

Expected: 两个模型下载并加载；若生成成功，`run.tmp` 的 `status` 为 `success`。若失败，保留 `preflight.log`，根据原始异常只处理依赖缺失、内存不足或不支持的 CPU bf16 运算，不改 DSpark 算法代码。

- [ ] **Step 3: 执行正式 32-token 生成**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && set -o pipefail && .venv/bin/python -m experiments.first_run_qwen3_4b --max-new-tokens 32 --device cpu --output results/first-run-qwen3-4b/run.json 2>&1 | tee results/first-run-qwen3-4b/run.log'
```

Expected: 退出码 0；`run.json` 包含 `status: success`、非空 `generated_text`、正数 `generation_seconds`、正数 `peak_rss_bytes`，以及 `proposal_lengths`、`accepted_draft_lengths` 和 `acceptance_lengths`。

- [ ] **Step 4: 对结构化结果执行验收脚本**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python - <<"PY"
import json
from pathlib import Path

result = json.loads(Path("results/first-run-qwen3-4b/run.json").read_text())
assert result["status"] == "success"
assert result["target_model"] == "Qwen/Qwen3-4B"
assert result["draft_model"] == "deepseek-ai/dspark_qwen3_4b_block7"
assert result["device"] == "cpu"
assert result["generated_text"].strip()
assert result["generation_seconds"] > 0
assert result["peak_rss_bytes"] > 0
assert len(result["metrics"]["proposal_lengths"]) == result["metrics"]["verify_count"]
assert len(result["metrics"]["accepted_draft_lengths"]) == result["metrics"]["verify_count"]
print("PASS")
PY'
```

Expected: `PASS`。

- [ ] **Step 5: 检查日志与结果不包含凭据**

Run:

```powershell
rg -n -i "authorization:|password|secret|hf_[a-zA-Z0-9]{20,}" results/first-run-qwen3-4b/run.json results/first-run-qwen3-4b/run.log
```

Expected: 无匹配，`rg` 退出码为 1。

- [ ] **Step 6: 提交成功运行产物**

先检查 `.agent/config.yml`；该文件不存在时按 `auto_commit: true` 处理。

```powershell
git add results/first-run-qwen3-4b/run.json results/first-run-qwen3-4b/run.log
git commit -m "exp: record Qwen3-4B DSpark first run"
```

Expected: commit 成功。

### Task 6: 写入实验记录与关键代码解读

**Files:**
- Create: `specs/001-qwen3-4b-dspark-first-run-record.md`

- [ ] **Step 1: 从实际产物提取不可手填的结果字段**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python - <<"PY"
import json
from pathlib import Path

env = json.loads(Path("results/first-run-qwen3-4b/environment.json").read_text(encoding="utf-8-sig"))
run = json.loads(Path("results/first-run-qwen3-4b/run.json").read_text())
print(json.dumps({
    "git_commit": run["git_commit"],
    "device": run["device"],
    "load_seconds": run["model_load_seconds"],
    "generation_seconds": run["generation_seconds"],
    "peak_rss_bytes": run["peak_rss_bytes"],
    "metrics": run["metrics"],
    "generated_text": run["generated_text"],
}, ensure_ascii=False, indent=2))
PY'
```

Expected: 输出与 `run.json` 一致的实验摘要；写 record spec 时直接使用这些实际值。

- [ ] **Step 2: 创建最终实验记录**

创建 `specs/001-qwen3-4b-dspark-first-run-record.md`，必须包含以下已填充章节，不使用空白字段：

```markdown
# DeepSpec Qwen3-4B DSpark 首次运行记录

## 1. 实验结论

写明成功或失败状态，以及是否满足设计 spec 的六项成功条件。

## 2. 固定版本与环境

写入 DeepSpec commit、分支、操作系统、WSL、CPU、内存、PyTorch、Transformers 和实际 device。

## 3. 模型与运行参数

写入 target、draft、prompt、temperature、max_new_tokens 和 confidence_threshold。

## 4. 执行时间线

按发生顺序写每条实际命令、退出状态、错误原文摘要、原因判断和最小修复。没有发生错误时明确写“本次没有发生需要修复的运行错误”。

## 5. 最终输出与指标

原样写入生成文本，并列出模型加载耗时、生成耗时、峰值 RSS、verify_count、每轮 proposal length、accepted draft length、acceptance length 及三项平均值。

## 6. 关键代码调用链

按以下真实调用顺序解读：

1. `experiments/first_run_qwen3_4b.py::build_local_evaluator`
2. `deepspec/eval/dspark/evaluator.py::Qwen3DSparkEvaluator.build_models`
3. `deepspec/eval/base_evaluator.py::generate_decoding_sample`
4. `deepspec/eval/dspark/evaluator.py::Qwen3DSparkEvaluator._propose`
5. `deepspec/eval/dspark/draft_ops.py::forward_dspark_draft_block`
6. `deepspec/eval/dspark/draft_ops.py::build_dspark_proposal`
7. `deepspec/modeling/dspark/markov_head.py` 中本次调用的 Markov 采样方法
8. `deepspec/eval/base_evaluator.py::verify_draft_tokens`
9. `deepspec/eval/dspark/evaluator.py::Qwen3DSparkEvaluator._update`

每个节点说明输入、输出、在一次 decode step 中的职责，以及它与上一个节点传递的关键张量或 token。

## 7. 本机限制与观察边界

明确写明 CPU 结果不能代表 CUDA/SGLang 生产性能，当前实验没有验证训练、STS 或负载感知调度，并列出官方接口没有暴露的指标。

## 8. 下一阶段

只给出与后续 llama.cpp 调研衔接的一个建议，不在本阶段执行。
```

- [ ] **Step 3: 检查记录没有占位内容或泄露凭据**

Run:

```powershell
rg -n "T[B]D|T[O]DO|待[补]|待[定]|<填写|hf_[a-zA-Z0-9]{20,}" specs/001-qwen3-4b-dspark-first-run-record.md
```

Expected: 无匹配，`rg` 退出码为 1。

- [ ] **Step 4: 核对记录中的路径与符号存在**

Run:

```powershell
rg -n "class Qwen3DSparkEvaluator|def build_models|def _propose|def _update" deepspec/eval/dspark/evaluator.py
rg -n "def generate_decoding_sample|def verify_draft_tokens" deepspec/eval/base_evaluator.py
rg -n "def forward_dspark_draft_block|def build_dspark_proposal" deepspec/eval/dspark/draft_ops.py
rg -n "class|def" deepspec/modeling/dspark/markov_head.py
```

Expected: record spec 引用的所有核心入口均有匹配。

- [ ] **Step 5: 提交实验记录**

先检查 `.agent/config.yml`；该文件不存在时按 `auto_commit: true` 处理。

```powershell
git add specs/001-qwen3-4b-dspark-first-run-record.md
git commit -m "docs: record DeepSpec Qwen3-4B first run"
```

Expected: commit 成功。

### Task 7: 完整验收

**Files:**
- Verify: `specs/001-qwen3-4b-dspark-first-run-design.md`
- Verify: `specs/001-qwen3-4b-dspark-first-run-record.md`
- Verify: `results/first-run-qwen3-4b/environment.json`
- Verify: `results/first-run-qwen3-4b/run.json`
- Verify: `results/first-run-qwen3-4b/run.log`

- [ ] **Step 1: 运行轻量测试**

Run:

```powershell
wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/d/proj/dspark-blog/deepspec && .venv/bin/python -m pytest tests/experiments/test_first_run_qwen3_4b.py -v'
```

Expected: `4 passed`。

- [ ] **Step 2: 运行 Git 和文档检查**

Run:

```powershell
git diff --check
git status --short --branch
rg -n "T[B]D|T[O]DO|待[补]|待[定]|hf_[a-zA-Z0-9]{20,}" specs results/first-run-qwen3-4b
```

Expected: `git diff --check` 无输出；Git 工作树干净；敏感信息与占位扫描无匹配。

- [ ] **Step 3: 确认提交历史完整**

Run:

```powershell
git log --oneline --decorate -8
```

Expected: 包含设计 spec、实施计划、环境快照、runner 测试、runner 实现、依赖快照、运行结果和实验记录的独立提交。

- [ ] **Step 4: 不创建额外验收提交**

该任务只做只读验证。检查 `.agent/config.yml`；无论 `auto_commit` 设置如何，本任务没有文件变化，因此不执行 `git commit`。
