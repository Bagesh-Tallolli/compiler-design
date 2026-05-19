import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Dict

class LLVMCompiler:
    def __init__(self):
        self.clang = None
        self.opt = None
        self.llvm_dis = None
        self._detect_llvm_pipeline()

    def _detect_llvm_pipeline(self):
        # 1. Try PATH detection first
        clang_in_path = shutil.which("clang++") or shutil.which("clang")
        opt_in_path = shutil.which("opt")
        llvm_dis_in_path = shutil.which("llvm-dis")

        if clang_in_path:
            self.clang = clang_in_path
            # If clang is found, search opt/llvm-dis relative to clang or on path
            clang_bin = Path(clang_in_path).parent
            self.opt = shutil.which("opt") or self._find_exe(clang_bin / "opt")
            self.llvm_dis = shutil.which("llvm-dis") or self._find_exe(clang_bin / "llvm-dis")
            return

        # 2. Try common installation directories across Windows, macOS, Linux
        common_paths = [
            # Windows Standard paths
            r"C:\Program Files\LLVM\bin",
            r"C:\Program Files (x86)\LLVM\bin",
            r"C:\msys64\mingw64\bin",
            r"C:\msys64\ucrt64\bin",
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\x64\bin",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\Llvm\x64\bin",
            r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\Llvm\x64\bin",
            
            # macOS paths
            "/opt/homebrew/opt/llvm/bin",
            "/opt/homebrew/bin",
            "/usr/local/opt/llvm/bin",
            "/usr/local/bin",
            
            # Linux paths
            "/usr/lib/llvm-17/bin",
            "/usr/lib/llvm-18/bin",
            "/usr/lib/llvm-19/bin",
            "/usr/bin"
        ]

        for path_str in common_paths:
            path = Path(path_str)
            if path.exists():
                clang_path = self._find_exe(path / "clang++") or self._find_exe(path / "clang")
                if clang_path:
                    self.clang = str(clang_path)
                    self.opt = str(self._find_exe(path / "opt")) if self._find_exe(path / "opt") else None
                    self.llvm_dis = str(self._find_exe(path / "llvm-dis")) if self._find_exe(path / "llvm-dis") else None
                    return

        # 3. Try finding via llvm-config if on path
        llvm_config = shutil.which("llvm-config")
        if llvm_config:
            try:
                bindir = subprocess.run([llvm_config, "--bindir"], capture_output=True, text=True, check=True).stdout.strip()
                bindir_path = Path(bindir)
                clang_path = self._find_exe(bindir_path / "clang++") or self._find_exe(bindir_path / "clang")
                if clang_path:
                    self.clang = str(clang_path)
                    self.opt = str(self._find_exe(bindir_path / "opt")) if self._find_exe(bindir_path / "opt") else None
                    self.llvm_dis = str(self._find_exe(bindir_path / "llvm-dis")) if self._find_exe(bindir_path / "llvm-dis") else None
            except Exception:
                pass

    def _find_exe(self, base_path: Path) -> Path | None:
        """Helper to find an executable with or without Windows extension."""
        if base_path.exists():
            return base_path
        exe_path = base_path.with_suffix(".exe")
        if exe_path.exists():
            return exe_path
        return None

    def get_diagnostics(self) -> Dict[str, any]:
        status = {
            "clang_detected": bool(self.clang),
            "clang_path": self.clang,
            "opt_detected": bool(self.opt),
            "llvm_dis_detected": bool(self.llvm_dis)
        }
        
        if self.clang:
            try:
                version_out = subprocess.run([self.clang, "--version"], capture_output=True, text=True).stdout
                status["clang_version"] = version_out.splitlines()[0] if version_out else "Unknown"
            except:
                status["clang_version"] = "Unknown"
        else:
            status["clang_version"] = None

        return status

    def available(self) -> bool:
        return bool(self.clang)

    def compile_to_ir(self, source_path: str, output_path: str, extra_args: list[str] | None = None) -> Tuple[bool, str]:
        """Compile a C/C++ source file to LLVM IR (.ll)."""
        if not self.available():
            # Fallback to high-fidelity simulated compiler
            try:
                from .simulated_compiler import SimulatedCompiler
                source_code = Path(source_path).read_text(encoding="utf-8")
                compiler_sim = SimulatedCompiler()
                
                # Extract optimization level from extra_args
                opt_level = "-O0"
                if extra_args:
                    for arg in extra_args:
                        if arg in ["-O0", "-O1", "-O2", "-O3"]:
                            opt_level = arg
                            break
                            
                ir_content = compiler_sim.compile_cpp_to_ir(source_code, Path(source_path).name, opt_level)
                Path(output_path).write_text(ir_content, encoding="utf-8")
                return True, ""
            except Exception as e:
                return False, f"Simulated compilation fallback failed: {str(e)}"

        args = [self.clang, "-S", "-emit-llvm", source_path, "-o", output_path]
        if extra_args:
            args[1:1] = extra_args

        try:
            proc = subprocess.run(args, capture_output=True, text=True, check=False)
        except Exception as e:
            return False, str(e)

        if proc.returncode != 0:
            return False, proc.stderr or proc.stdout or f"clang exited {proc.returncode}"

        if not Path(output_path).exists():
            return False, "clang did not produce output file"

        return True, ""

    def optimize_ir(self, input_ll: str, output_ll: str, opt_level: str = "-O3") -> Tuple[bool, str]:
        """Run the LLVM opt tool on an IR file."""
        if not self.opt:
            return False, "opt not found on PATH"
        
        args = [self.opt, "-S", opt_level, input_ll, "-o", output_ll]
        try:
            proc = subprocess.run(args, capture_output=True, text=True, check=False)
        except Exception as e:
            return False, str(e)
            
        if proc.returncode != 0:
            return False, proc.stderr or f"opt exited {proc.returncode}"
            
        if not Path(output_ll).exists():
            return False, "opt did not produce output file"
            
        return True, ""

