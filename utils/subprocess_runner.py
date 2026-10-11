from __future__ import annotations

import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from importlib.util import find_spec
from io import StringIO

from utils.paths import merged_env


@dataclass(slots=True)
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int

    @property
    def text(self) -> str:
        return (self.stdout or self.stderr).strip()


class SubprocessRunner:
    def is_available(self, executable: str) -> bool:
        if shutil.which(executable, path=merged_env().get("PATH")) is not None:
            return True
        if executable == "pymobiledevice3":
            return find_spec("pymobiledevice3") is not None
        return False

    def run(self, command: list[str], timeout: int = 30) -> CommandResult:
        if command and command[0] == "pymobiledevice3" and shutil.which(command[0], path=merged_env().get("PATH")) is None:
            return self._run_embedded_pymobiledevice3(command)

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=merged_env(),
            )
            return CommandResult(
                ok=completed.returncode == 0,
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
            )
        except FileNotFoundError:
            return CommandResult(False, "", f"命令未找到：{command[0]}", 127)
        except subprocess.TimeoutExpired as exc:
            return CommandResult(False, exc.stdout or "", f"命令执行超时：{' '.join(command)}", 124)
        except Exception as exc:
            return CommandResult(False, "", f"命令执行失败：{exc}", 1)

    def _run_embedded_pymobiledevice3(self, command: list[str]) -> CommandResult:
        stdout = StringIO()
        stderr = StringIO()
        old_argv = sys.argv[:]
        old_path = sys.path[:]
        try:
            from pymobiledevice3.__main__ import main as pymobiledevice3_main

            sys.argv = command[:]
            with redirect_stdout(stdout), redirect_stderr(stderr):
                try:
                    pymobiledevice3_main()
                    returncode = 0
                except SystemExit as exc:
                    returncode = int(exc.code or 0) if isinstance(exc.code, int) else 1
            return CommandResult(
                ok=returncode == 0,
                stdout=stdout.getvalue(),
                stderr=stderr.getvalue(),
                returncode=returncode,
            )
        except Exception as exc:
            return CommandResult(False, stdout.getvalue(), stderr.getvalue() + f"\n内置 pymobiledevice3 执行失败：{exc}", 1)
        finally:
            sys.argv = old_argv
            sys.path = old_path
