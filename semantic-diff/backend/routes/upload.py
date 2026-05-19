from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import os
from ..compiler.llvm_compiler import LLVMCompiler
from ..ir_normalizer.normalizer import IRNormalizer
from ..diff_engine.ir_diff import IRDiffEngine
from ..cfg_engine.cfg_builder import CFGBuilder
from ..cfg_engine.cfg_diff import CFGDiffEngine
from ..diff_engine.function_mapper import FunctionMapper
from ..dfg_engine.dfg_builder import DFGBuilder
from ..dfg_engine.dfg_diff import DFGDiffEngine

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated_ir"
NORMALIZED_DIR = BASE_DIR / "normalized_ir"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".c", ".cpp"}

compiler = LLVMCompiler()
diff_engine = IRDiffEngine()
cfg_builder = CFGBuilder()
cfg_diff_engine = CFGDiffEngine()
function_mapper = FunctionMapper()
dfg_builder = DFGBuilder()
dfg_diff_engine = DFGDiffEngine()

@router.post("/upload")
async def upload(old_file: UploadFile = File(...), new_file: UploadFile = File(...)):
    # Validate file extensions
    old_ext = Path(old_file.filename).suffix.lower()
    new_ext = Path(new_file.filename).suffix.lower()

    if old_ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Invalid old file type: {old_ext}")
    if new_ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Invalid new file type: {new_ext}")

    if not compiler.available():
        raise HTTPException(status_code=500, detail="clang not found on server PATH")

    # save uploads
    old_id = uuid.uuid4().hex
    new_id = uuid.uuid4().hex
    old_src_path = UPLOAD_DIR / f"old_{old_id}{old_ext}"
    new_src_path = UPLOAD_DIR / f"new_{new_id}{new_ext}"

    with old_src_path.open("wb") as f:
        f.write(await old_file.read())
    with new_src_path.open("wb") as f:
        f.write(await new_file.read())

    # compile to IR
    old_ll = GENERATED_DIR / f"old_{old_id}.ll"
    new_ll = GENERATED_DIR / f"new_{new_id}.ll"

    ok_old, err_old = compiler.compile_to_ir(str(old_src_path), str(old_ll))
    if not ok_old:
        return JSONResponse(status_code=400, content={"success": False, "error": f"Old file compile failed: {err_old}"})

    ok_new, err_new = compiler.compile_to_ir(str(new_src_path), str(new_ll))
    if not ok_new:
        return JSONResponse(status_code=400, content={"success": False, "error": f"New file compile failed: {err_new}"})

    # read raw IR contents
    old_ir = old_ll.read_text(encoding="utf-8")
    new_ir = new_ll.read_text(encoding="utf-8")

    # normalize IR
    normalizer_old = IRNormalizer()
    normalized_old_ir, stats_old = normalizer_old.normalize(old_ir)

    normalizer_new = IRNormalizer()
    normalized_new_ir, stats_new = normalizer_new.normalize(new_ir)

    # save normalized IR
    old_norm_ll = NORMALIZED_DIR / f"normalized_old_{old_id}.ll"
    new_norm_ll = NORMALIZED_DIR / f"normalized_new_{new_id}.ll"
    old_norm_ll.write_text(normalized_old_ir, encoding="utf-8")
    new_norm_ll.write_text(normalized_new_ir, encoding="utf-8")

    # aggregate diagnostics
    diagnostics = {
        "old": stats_old,
        "new": stats_new,
    }

    # compute semantic diff
    diff_summary = diff_engine.diff(normalized_old_ir, normalized_new_ir)

    # extract and compare CFGs
    old_functions = function_mapper.extract_functions(normalized_old_ir)
    new_functions = function_mapper.extract_functions(normalized_new_ir)

    cfg_diffs = []
    for func_name in set(old_functions.keys()) & set(new_functions.keys()):
        old_func = old_functions[func_name]
        new_func = new_functions[func_name]

        old_cfg = cfg_builder.build_from_function_ir(old_func.raw_text, func_name)
        new_cfg = cfg_builder.build_from_function_ir(new_func.raw_text, func_name)

        cfg_diff = cfg_diff_engine.diff(old_cfg, new_cfg)
        cfg_diffs.append(cfg_diff.to_dict())

    dfg_diffs = []
    for func_name in set(old_functions.keys()) & set(new_functions.keys()):
        old_func = old_functions[func_name]
        new_func = new_functions[func_name]

        old_dfg = dfg_builder.build_from_function_ir(old_func.raw_text, func_name)
        new_dfg = dfg_builder.build_from_function_ir(new_func.raw_text, func_name)

        dfg_diff = dfg_diff_engine.diff(old_dfg, new_dfg, old_func.raw_text, new_func.raw_text)
        dfg_diffs.append(dfg_diff.to_dict())

    return {
        "success": True,
        "old_ir": old_ir,
        "new_ir": new_ir,
        "normalized_old_ir": normalized_old_ir,
        "normalized_new_ir": normalized_new_ir,
        "old_file": old_ll.name,
        "new_file": new_ll.name,
        "normalized_old_file": old_norm_ll.name,
        "normalized_new_file": new_norm_ll.name,
        "diagnostics": diagnostics,
        "diff": diff_summary.to_dict(),
        "cfg_analysis": cfg_diffs,
        "dfg_analysis": dfg_diffs,
    }
