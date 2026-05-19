import shutil
import subprocess
from pathlib import Path
from typing import Tuple

class LLVMCompiler:
    def __init__(self, clang_path: str | None = None):
        self.clang = clang_path or shutil.which("clang")

    def available(self) -> bool:
        return bool(self.clang)

    def compile_to_ir(self, source_path: str, output_path: str, extra_args: list[str] | None = None) -> Tuple[bool, str]:
        """Compile a C/C++ source file to LLVM IR (.ll).

        Returns (success, stderr_or_empty). On success, writes output_path.
        """
        if not self.available():
            return False, "clang not found on PATH"

        args = [self.clang, "-S", "-emit-llvm", source_path, "-o", output_path]
        if extra_args:
            args[1:1] = extra_args

        try:
            proc = subprocess.run(args, capture_output=True, text=True, check=False)
        except Exception as e:
            return False, str(e)

        if proc.returncode != 0:
            return False, proc.stderr or proc.stdout or f"clang exited {proc.returncode}"

        # verify file exists
        if not Path(output_path).exists():
            return False, "clang did not produce output file"

        return True, ""
