from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 10)
MAX_SETUPTOOLS_MAJOR = 81

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GOMOKU_AI_ROOT = ROOT / "gomoku_ai"
if GOMOKU_AI_ROOT.is_dir() and str(GOMOKU_AI_ROOT) not in sys.path:
    sys.path.insert(0, str(GOMOKU_AI_ROOT))


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def ok(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "OK", detail)


def warn(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "WARN", detail)


def fail(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "FAIL", detail)


def run_command(command: list[str], cwd: Path | None = None, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def package_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_python_version() -> CheckResult:
    current = sys.version_info[:3]
    detail = f"{platform.python_implementation()} {platform.python_version()} at {sys.executable}"
    if current < MIN_PYTHON:
        return fail("Python version", f"{detail}; required >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}")
    return ok("Python version", detail)


def check_virtual_environment() -> CheckResult:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        return ok("Virtual environment", f"active at {sys.prefix}")
    return warn("Virtual environment", "not active; recommended to use Workshop root .venv")


def check_pip() -> CheckResult:
    result = run_command([sys.executable, "-m", "pip", "--version"])
    if result.returncode != 0:
        return fail("pip", result.stderr.strip() or "python -m pip failed")
    return ok("pip", result.stdout.strip())


def check_pip_dependencies() -> CheckResult:
    result = run_command([sys.executable, "-m", "pip", "check"], timeout=60)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        return fail("pip dependency consistency", output or "pip check failed")
    return ok("pip dependency consistency", output or "No broken requirements found")


def check_distribution_versions() -> list[CheckResult]:
    required = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("websockets", "websockets"),
        ("pydantic", "pydantic"),
        ("PyYAML", "yaml"),
        ("numpy", "numpy"),
        ("pybind11", "pybind11"),
        ("torch", "torch"),
        ("tqdm", "tqdm"),
        ("tensorboard", "tensorboard"),
    ]
    results: list[CheckResult] = []
    for distribution, module_name in required:
        version = package_version(distribution)
        if version is None:
            results.append(fail(f"Package {distribution}", "not installed"))
            continue
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - diagnostic script
            results.append(fail(f"Package {distribution}", f"{version}; import failed: {exc}"))
        else:
            results.append(ok(f"Package {distribution}", version))
    return results


def check_setuptools_version() -> CheckResult:
    version = package_version("setuptools")
    if version is None:
        return fail("setuptools", "not installed")
    major = _parse_major(version)
    if major is not None and major >= MAX_SETUPTOOLS_MAJOR:
        return fail("setuptools", f"{version}; project expects setuptools<{MAX_SETUPTOOLS_MAJOR}")
    return ok("setuptools", f"{version}; satisfies <{MAX_SETUPTOOLS_MAJOR}")


def _parse_major(version: str) -> int | None:
    head = version.split(".", 1)[0]
    try:
        return int(head)
    except ValueError:
        return None


def check_torch() -> CheckResult:
    try:
        import torch
    except Exception as exc:
        return fail("PyTorch", f"import failed: {exc}")

    detail = f"torch {torch.__version__}; cuda_available={torch.cuda.is_available()}"
    if torch.cuda.is_available():
        try:
            detail += f"; device={torch.cuda.get_device_name(0)}"
        except Exception:
            pass
    return ok("PyTorch", detail)


def check_local_inference_imports() -> CheckResult:
    try:
        importlib.import_module("local_inference_service.app")
        importlib.import_module("local_inference_service.core.local_move_service")
    except Exception as exc:
        return fail("Local Inference Service imports", str(exc))
    return ok("Local Inference Service imports", "app and core modules import successfully")


def check_local_inference_request() -> CheckResult:
    try:
        from fastapi.testclient import TestClient
        from local_inference_service.app import app
    except Exception as exc:
        return fail("Local Inference Service request", f"import failed: {exc}")

    board = [[0 for _ in range(15)] for _ in range(15)]
    try:
        with TestClient(app) as client:
            response = client.post(
                "/bot_move",
                json={"board": board, "current_player": 1, "engine_name": "center_first"},
            )
    except Exception as exc:
        return fail("Local Inference Service request", str(exc))

    if response.status_code != 200:
        return fail("Local Inference Service request", f"HTTP {response.status_code}: {response.text}")

    payload = response.json()
    expected = {"row": 7, "col": 7, "x": 7, "y": 7}
    for key, value in expected.items():
        if payload.get(key) != value:
            return fail("Local Inference Service request", f"unexpected response: {payload}")
    return ok("Local Inference Service request", json.dumps(payload, ensure_ascii=False))


def check_dynamic_python_engine() -> CheckResult:
    try:
        from fastapi.testclient import TestClient
        from local_inference_service.app import app
    except Exception as exc:
        return fail("Dynamic Python MoveEngine", f"import failed: {exc}")

    code = "\n".join(
        [
            "import json",
            "import sys",
            "for line in sys.stdin:",
            "    json.loads(line)",
            "    print(json.dumps({'x': 3, 'y': 4, 'debug': {'verify': True}}), flush=True)",
        ]
    )

    with tempfile.TemporaryDirectory() as tmp:
        engine_path = Path(tmp) / "verify_engine.py"
        engine_path.write_text(code, encoding="utf-8")
        board = [[0 for _ in range(15)] for _ in range(15)]
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/bot_move",
                    json={
                        "board": board,
                        "current_player": 1,
                        "engine_kind": "python_script",
                        "engine_path": str(engine_path),
                    },
                )
        except Exception as exc:
            return fail("Dynamic Python MoveEngine", str(exc))

    if response.status_code != 200:
        return fail("Dynamic Python MoveEngine", f"HTTP {response.status_code}: {response.text}")
    payload = response.json()
    if payload.get("row") == 4 and payload.get("col") == 3:
        return ok("Dynamic Python MoveEngine", "stdin/stdout JSON Lines path works")
    return fail("Dynamic Python MoveEngine", f"unexpected response: {payload}")


def check_gomoku_ai_imports() -> CheckResult:
    try:
        importlib.import_module("gomoku_ai")
        importlib.import_module("bots")
        importlib.import_module("gomoku_ai.env")
    except Exception as exc:
        return fail("gomoku_ai imports", str(exc))
    return ok("gomoku_ai imports", "gomoku_ai, bots, and env import successfully")


def check_cpp_backend() -> CheckResult:
    try:
        from gomoku_ai.cpp_backend import BACKEND_AVAILABLE, score_classic_candidates
    except Exception as exc:
        return fail("gomoku_ai C++ backend import", str(exc))

    if not BACKEND_AVAILABLE:
        return fail(
            "gomoku_ai C++ backend",
            "not built; run pip install -r requirements.txt after installing a C++ compiler",
        )

    try:
        import numpy as np

        board = np.zeros((15, 15), dtype=np.int8)
        result = score_classic_candidates(board, [112], 1)
    except Exception as exc:
        return fail("gomoku_ai C++ backend smoke", str(exc))

    return ok("gomoku_ai C++ backend", f"available; scored {len(result)} candidate(s)")


def check_direction_delta_table() -> CheckResult:
    path = ROOT / "gomoku_ai" / "cpp" / "precompute" / "direction_delta_table.bin"
    if path.is_file():
        return ok("C++ precompute table", str(path))
    return fail("C++ precompute table", f"missing: {path}")


def check_cpp_compiler() -> CheckResult:
    system = platform.system().lower()
    if system == "windows":
        return check_windows_cpp_compiler()
    if shutil.which("c++") or shutil.which("g++") or shutil.which("clang++"):
        compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
        return ok("C++ compiler", f"found {compiler}")
    return fail("C++ compiler", "no c++, g++, or clang++ found on PATH")


def check_windows_cpp_compiler() -> CheckResult:
    cl_path = shutil.which("cl.exe")
    if cl_path:
        return ok("C++ compiler", f"MSVC cl.exe found on PATH: {cl_path}")

    vswhere = find_vswhere()
    if vswhere is not None:
        result = run_command(
            [
                str(vswhere),
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            timeout=20,
        )
        install_path = result.stdout.strip()
        if result.returncode == 0 and install_path:
            dev_cmd = Path(install_path) / "Common7" / "Tools" / "VsDevCmd.bat"
            if dev_cmd.is_file():
                return ok("C++ compiler", f"MSVC Build Tools found; use {dev_cmd} if pip cannot find cl.exe")
            return warn("C++ compiler", f"Visual Studio C++ tools found at {install_path}, but VsDevCmd.bat was not found")

    return fail(
        "C++ compiler",
        "MSVC cl.exe not found. Install Visual Studio 2022 Build Tools with Desktop development with C++.",
    )


def find_vswhere() -> Path | None:
    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Microsoft Visual Studio"
        / "Installer"
        / "vswhere.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        / "Microsoft Visual Studio"
        / "Installer"
        / "vswhere.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    path_hit = shutil.which("vswhere.exe")
    return Path(path_hit) if path_hit else None


def run_checks(include_compiler: bool) -> list[CheckResult]:
    checks: list[Callable[[], CheckResult]] = [
        check_python_version,
        check_virtual_environment,
        check_pip,
        check_setuptools_version,
        check_torch,
        check_local_inference_imports,
        check_local_inference_request,
        check_dynamic_python_engine,
        check_gomoku_ai_imports,
        check_direction_delta_table,
        check_cpp_backend,
        check_pip_dependencies,
    ]
    if include_compiler:
        checks.insert(5, check_cpp_compiler)

    results: list[CheckResult] = []
    for check in checks:
        try:
            results.append(check())
        except Exception as exc:  # pragma: no cover - defensive diagnostic script
            results.append(fail(check.__name__, f"unexpected error: {exc}"))

    results[5:5] = check_distribution_versions()
    return results


def print_results(results: list[CheckResult]) -> None:
    width = max(len(result.name) for result in results)
    for result in results:
        print(f"[{result.status:<4}] {result.name:<{width}}  {result.detail}")

    failed = sum(1 for result in results if result.status == "FAIL")
    warned = sum(1 for result in results if result.status == "WARN")
    print()
    if failed:
        print(f"Environment verification failed: {failed} failure(s), {warned} warning(s).")
    elif warned:
        print(f"Environment verification passed with {warned} warning(s).")
    else:
        print("Environment verification passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Workshop runtime environment.")
    parser.add_argument(
        "--skip-compiler",
        action="store_true",
        help="Skip C++ compiler discovery. The built gomoku_ai C++ backend is still checked.",
    )
    args = parser.parse_args()

    results = run_checks(include_compiler=not args.skip_compiler)
    print_results(results)
    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
