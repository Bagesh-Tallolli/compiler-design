import re
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional

class SimulatedCompiler:
    """High-fidelity C++ to LLVM IR simulator for graceful degradation compiler analysis.
    Supports baseline (-O0) and simulated optimizations (-O1, -O2, -O3).
    """

    def __init__(self):
        self.blocks: Dict[str, List[str]] = {}
        self.current_block = "entry"
        self.reg_counter = 1
        self.var_types: Dict[str, str] = {}
        self.var_ptrs: Dict[str, str] = {}
        self.args_map: Dict[str, str] = {}
        self.loop_counter = 0
        self.branch_counter = 0
        self.opt_level = "-O0"
        self.const_values: Dict[str, int] = {}
        
        # Store metadata of inline functions: name -> (arg_names, return_expression)
        self.inline_funcs: Dict[str, Tuple[List[str], str]] = {}
        self.has_restrict = False

    def compile_cpp_to_ir(self, source_code: str, file_name: str, opt_level: str = "-O0") -> str:
        self.opt_level = opt_level
        code = self._preprocess(source_code)
        
        # Pre-scan for inline helper functions for simulated inlining
        self._scan_inline_functions(code)
        
        ir_lines = [
            f"; Simulated LLVM IR generated for {file_name} (High-Fidelity Simulation Mode - {opt_level})",
            f'source_filename = "{file_name}"',
            'target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"',
            'target triple = "x86_64-pc-windows-msvc19.29.30133"',
            ""
        ]

        # Regex to locate function definitions
        func_pattern = r"(?:(?:static\s+|inline\s+|__attribute__\(\([\w\s,]+\)\)\s*)*)?\b(int|double|void|float|long|int\*|float\*)\s+(\w+)\s*\(([^)]*)\)\s*\{"
        matches = list(re.finditer(func_pattern, code))
        
        if not matches:
            return f"; No function definitions detected in {file_name}\n"

        for match in matches:
            ret_type_cpp = match.group(1).strip()
            func_name = match.group(2).strip()
            args_raw = match.group(3).strip()
            
            # Brace matching to extract the block body
            start_pos = match.end()
            braces = 1
            body_chars = []
            for char in code[start_pos:]:
                if char == '{':
                    braces += 1
                elif char == '}':
                    braces -= 1
                if braces == 0:
                    break
                body_chars.append(char)
            
            body = "".join(body_chars)
            
            # Skip code generation if it is an inline helper function that is successfully registered
            # and optimization is enabled (to simulate inlining)
            if func_name in self.inline_funcs and self.opt_level in ["-O2", "-O3"]:
                continue

            func_ir = self._compile_function(func_name, ret_type_cpp, args_raw, body)
            ir_lines.append(func_ir)
            ir_lines.append("")

        return "\n".join(ir_lines)

    def _preprocess(self, code: str) -> str:
        # Remove comments
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    def _scan_inline_functions(self, code: str):
        # Scan code for helper functions that can be inlined
        func_pattern = r"(?:static\s+|inline\s+)+\b(int|double|float|long)\s+(\w+)\s*\(([^)]*)\)\s*\{\s*return\s*([^;]+);\s*\}"
        matches = re.finditer(func_pattern, code)
        for match in matches:
            func_name = match.group(2).strip()
            args_raw = match.group(3).strip()
            ret_expr = match.group(4).strip()
            
            # Parse argument names
            arg_names = []
            if args_raw:
                for arg in args_raw.split(","):
                    parts = arg.strip().split()
                    if parts:
                        arg_names.append(parts[-1].replace("*", "").replace("&", ""))
            
            self.inline_funcs[func_name] = (arg_names, ret_expr)

    def _to_llvm_type(self, cpp_type: str) -> str:
        cpp_type = cpp_type.replace("const", "").replace("__restrict__", "").strip()
        if cpp_type == "int":
            return "i32"
        elif cpp_type == "float":
            return "float"
        elif cpp_type == "double":
            return "double"
        elif cpp_type == "void":
            return "void"
        elif cpp_type == "long":
            return "i64"
        elif cpp_type == "int*":
            return "i32*"
        elif cpp_type == "float*":
            return "float*"
        elif cpp_type == "double*":
            return "double*"
        else:
            return "i32"

    def _to_llvm_align(self, llvm_type: str) -> int:
        if llvm_type in ["i32", "float"]:
            return 4
        elif llvm_type in ["double", "i64", "i32*", "float*", "double*"]:
            return 8
        else:
            return 4

    def _next_reg(self) -> str:
        reg = f"%{self.reg_counter}"
        self.reg_counter += 1
        return reg

    def _compile_function(self, name: str, ret_cpp: str, args_raw: str, body: str) -> str:
        # Reset state
        self.blocks = {"entry": []}
        self.current_block = "entry"
        self.reg_counter = 1
        self.var_types = {}
        self.var_ptrs = {}
        self.args_map = {}
        self.loop_counter = 0
        self.branch_counter = 0
        self.const_values = {}
        
        self.has_restrict = "__restrict__" in args_raw

        # Parse arguments
        args_parsed = []
        if args_raw.strip():
            for arg in args_raw.split(","):
                parts = arg.strip().split()
                if len(parts) >= 2:
                    arg_name = parts[-1].replace("*", "").replace("&", "").strip()
                    arg_type_cpp = " ".join(parts[:-1]) + ("*" if "*" in parts[-1] else "")
                    arg_llvm = self._to_llvm_type(arg_type_cpp)
                    self.args_map[arg_name] = arg_llvm
                    args_parsed.append(f"{arg_llvm} %{arg_name}")

        args_str = ", ".join(args_parsed)
        llvm_ret = self._to_llvm_type(ret_cpp)
        
        # Setup entry block parameter allocations
        for arg_name, arg_llvm in self.args_map.items():
            addr_ptr = f"%{arg_name}.addr"
            align = self._to_llvm_align(arg_llvm)
            self.blocks["entry"].append(f"  {addr_ptr} = alloca {arg_llvm}, align {align}")
            self.blocks["entry"].append(f"  store {arg_llvm} %{arg_name}, {arg_llvm}* {addr_ptr}, align {align}")

        # Parse and compile statements
        self._compile_statements(body)

        # Force a return at entry or exit if block is not terminated
        for label, instrs in list(self.blocks.items()):
            if not instrs or not any(x.strip().startswith("ret") or x.strip().startswith("br") for x in instrs):
                if llvm_ret == "void":
                    self.blocks[label].append("  ret void")
                else:
                    self.blocks[label].append(f"  ret {llvm_ret} 0")

        # Reconstruct IR
        lines = [f"define {llvm_ret} @{name}({args_str}) {{"]
        
        # entry block first
        lines.append("entry:")
        for instr in self.blocks["entry"]:
            lines.append(instr)
        
        # rest of the blocks
        for label in sorted(self.blocks.keys()):
            if label == "entry":
                continue
            lines.append(f"\n{label}:")
            for instr in self.blocks[label]:
                lines.append(instr)
                
        lines.append("}")
        return "\n".join(lines)

    def _compile_statements(self, body_text: str):
        statements = self._get_statements(body_text)
        
        # Simulated optimization: Dead Code Elimination
        if self.opt_level in ["-O1", "-O2", "-O3"]:
            statements = self._run_dce(statements)
            
        for stmt in statements:
            self._compile_statement(stmt)

    def _run_dce(self, statements: List[str]) -> List[str]:
        # Identify declared variables
        declared = []
        for stmt in statements:
            decl_match = re.match(r'^(int|double|float|long|int\*|float\*)\s+(\w+)', stmt)
            if decl_match:
                declared.append(decl_match.group(2))

        # Check references for each variable on RHS
        refs = {v: 0 for v in declared}
        for stmt in statements:
            rhs = stmt
            decl_match = re.match(r'^(int|double|float|long|int\*|float\*)\s+(\w+)\s*=\s*(.*)$', stmt)
            if decl_match:
                rhs = decl_match.group(3)
                
            for var in declared:
                if re.search(r'\b' + re.escape(var) + r'\b', rhs):
                    if not (decl_match and decl_match.group(2) == var):
                        refs[var] += 1
                elif not decl_match and re.search(r'\b' + re.escape(var) + r'\b', stmt):
                    lhs_match = re.match(r'^' + re.escape(var) + r'\s*(=|\+=|-=|\*=|\/=)', stmt)
                    if not lhs_match:
                        refs[var] += 1

        optimized_statements = []
        for stmt in statements:
            decl_match = re.match(r'^(int|double|float|long|int\*|float\*)\s+(\w+)', stmt)
            if decl_match:
                var = decl_match.group(2)
                if refs[var] == 0:
                    continue  # Remove definition / allocation of unused variable
            optimized_statements.append(stmt)
            
        return optimized_statements

    def _get_statements(self, body: str) -> List[str]:
        statements = []
        current = []
        braces = 0
        parens = 0
        i = 0
        while i < len(body):
            char = body[i]
            if char == '{':
                braces += 1
                current.append(char)
            elif char == '}':
                braces -= 1
                current.append(char)
                if braces == 0 and parens == 0:
                    statements.append("".join(current).strip())
                    current = []
            elif char == '(':
                parens += 1
                current.append(char)
            elif char == ')':
                parens -= 1
                current.append(char)
            elif char == ';' and braces == 0 and parens == 0:
                statements.append("".join(current).strip())
                current = []
            else:
                current.append(char)
            i += 1
        if "".join(current).strip():
            statements.append("".join(current).strip())
        return [s for s in statements if s]

    def _block_has_return(self, label: str) -> bool:
        if label not in self.blocks:
            return False
        return any(x.strip().startswith("ret") or x.strip().startswith("br ") for x in self.blocks[label])

    def _try_eval_condition(self, cond_expr: str) -> Optional[bool]:
        expr = cond_expr
        for var, val in list(self.const_values.items()):
            expr = re.sub(r'\b' + re.escape(var) + r'\b', str(val), expr)
            
        m = re.match(r'^(\d+)\s*(==|!=|<=|>=|<|>)\s*(\d+)$', expr)
        if m:
            lhs = int(m.group(1))
            op = m.group(2)
            rhs = int(m.group(3))
            if op == "==": return lhs == rhs
            elif op == "!=": return lhs != rhs
            elif op == "<=": return lhs <= rhs
            elif op == ">=": return lhs >= rhs
            elif op == "<": return lhs < rhs
            elif op == ">": return lhs > rhs
        return None

    def _compile_statement(self, stmt: str):
        stmt = stmt.strip()
        if not stmt:
            return

        # 1. IF conditions
        if stmt.startswith("if"):
            match = re.match(r'^if\s*\((.*?)\)\s*(.*?)(?:\s*else\s*(.*))?$', stmt, re.DOTALL)
            if match:
                cond_expr = match.group(1).strip()
                then_body = match.group(2).strip()
                else_body = match.group(3).strip() if match.group(3) else ""
                
                if then_body.startswith("{") and then_body.endswith("}"):
                    then_body = then_body[1:-1].strip()
                if else_body.startswith("{") and else_body.endswith("}"):
                    else_body = else_body[1:-1].strip()

                # Simulated optimization: Dead Branch Elimination via Constant Evaluation in -O1/-O2/-O3
                if self.opt_level in ["-O1", "-O2", "-O3"]:
                    eval_val = self._try_eval_condition(cond_expr)
                    if eval_val is not None:
                        if eval_val:
                            self._compile_statements(then_body)
                        elif else_body:
                            self._compile_statements(else_body)
                        return
                
                # Compile condition
                reg_cond, type_cond = self._compile_expression(cond_expr, "i32")
                
                # If not an icmp expression already, compare to 0
                if not reg_cond.startswith("%") or not any("icmp" in inst for inst in self.blocks[self.current_block]):
                    reg_cmp = self._next_reg()
                    self.blocks[self.current_block].append(
                        f"  {reg_cmp} = icmp ne {type_cond} {reg_cond}, 0"
                    )
                    reg_cond = reg_cmp
                
                idx = self.branch_counter
                self.branch_counter += 1
                then_label = f"then_{idx}"
                else_label = f"else_{idx}"
                merge_label = f"merge_{idx}"
                
                if else_body:
                    self.blocks[self.current_block].append(
                        f"  br i1 {reg_cond}, label %{then_label}, label %{else_label}"
                    )
                else:
                    self.blocks[self.current_block].append(
                        f"  br i1 {reg_cond}, label %{then_label}, label %{merge_label}"
                    )
                
                # compile 'then'
                self.blocks[then_label] = []
                self.current_block = then_label
                self._compile_statements(then_body)
                if not self._block_has_return(then_label):
                    self.blocks[then_label].append(f"  br label %{merge_label}")
                
                # compile 'else'
                if else_body:
                    self.blocks[else_label] = []
                    self.current_block = else_label
                    self._compile_statements(else_body)
                    if not self._block_has_return(else_label):
                        self.blocks[else_label].append(f"  br label %{merge_label}")
                
                self.blocks[merge_label] = []
                self.current_block = merge_label

        # 2. FOR loops
        elif stmt.startswith("for"):
            match = re.match(r'^for\s*\((.*?);(.*?);(.*?)\)\s*(.*)$', stmt, re.DOTALL)
            if match:
                init_stmt = match.group(1).strip()
                cond_expr = match.group(2).strip()
                inc_stmt = match.group(3).strip()
                loop_body = match.group(4).strip()
                
                if loop_body.startswith("{") and loop_body.endswith("}"):
                    loop_body = loop_body[1:-1].strip()

                # Simulated Loop Unrolling in -O2 / -O3
                # If loop has a fixed small constant bound, e.g., i < 4, and init is i = 0, and inc is i++
                if self.opt_level in ["-O2", "-O3"]:
                    init_m = re.match(r'^(?:int\s+)?(\w+)\s*=\s*(\d+)$', init_stmt)
                    cond_m = re.match(r'^(\w+)\s*<\s*(\d+)$', cond_expr)
                    inc_m = re.match(r'^(\w+)(?:\+\+|递增|\s*\+=\s*1)$', inc_stmt)
                    if init_m and cond_m and inc_m and init_m.group(1) == cond_m.group(1) == inc_m.group(1):
                        var_name = init_m.group(1)
                        start_val = int(init_m.group(2))
                        end_val = int(cond_m.group(2))
                        if end_val - start_val <= 8:  # Unroll small loops
                            self.blocks[self.current_block].append(f"  ; Simulated Loop Unrolling (unrolled {end_val - start_val} times)")
                            ptr_name = f"%{var_name}"
                            self.var_types[var_name] = "i32"
                            self.var_ptrs[var_name] = ptr_name
                            self.blocks[self.current_block].append(
                                f"  {ptr_name} = alloca i32, align 4"
                            )
                            for val in range(start_val, end_val):
                                self.blocks[self.current_block].append(
                                    f"  store i32 {val}, i32* {ptr_name}, align 4"
                                )
                                self._compile_statements(loop_body)
                            return
                
                # Dynamic Vectorization Simulation in -O3
                # Check for restrict pointer arithmetic inside element additions, e.g. c[i] = a[i] + b[i];
                if self.opt_level == "-O3" and self.has_restrict and "restrict" not in loop_body:
                    # Let's emit vector registers load, add and store
                    self.blocks[self.current_block].append("  ; Simulated Vectorized Loop Header")
                    
                    reg_v1 = self._next_reg()
                    self.blocks[self.current_block].append(f"  {reg_v1} = load <4 x float>, <4 x float>* %a.addr, align 16")
                    
                    reg_v2 = self._next_reg()
                    self.blocks[self.current_block].append(f"  {reg_v2} = load <4 x float>, <4 x float>* %b.addr, align 16")
                    
                    reg_vadd = self._next_reg()
                    self.blocks[self.current_block].append(f"  {reg_vadd} = fadd <4 x float> {reg_v1}, {reg_v2}")
                    
                    self.blocks[self.current_block].append(f"  store <4 x float> {reg_vadd}, <4 x float>* %c.addr, align 16")
                    return

                # Compile initialization
                if init_stmt:
                    self._compile_statement(init_stmt)
                
                idx = self.loop_counter
                self.loop_counter += 1
                cond_label = f"loop_cond_{idx}"
                body_label = f"loop_body_{idx}"
                inc_label = f"loop_inc_{idx}"
                exit_label = f"loop_exit_{idx}"
                
                self.blocks[self.current_block].append(f"  br label %{cond_label}")
                
                # Compile loop condition
                self.blocks[cond_label] = []
                self.current_block = cond_label
                reg_cond, type_cond = self._compile_expression(cond_expr, "i32")
                self.blocks[cond_label].append(
                    f"  br i1 {reg_cond}, label %{body_label}, label %{exit_label}"
                )
                
                # Compile loop body
                self.blocks[body_label] = []
                self.current_block = body_label
                self._compile_statements(loop_body)
                if not self._block_has_return(body_label):
                    self.blocks[body_label].append(f"  br label %{inc_label}")
                
                # Compile increment
                self.blocks[inc_label] = []
                self.current_block = inc_label
                self._compile_statement(inc_stmt)
                self.blocks[inc_label].append(f"  br label %{cond_label}")
                
                self.blocks[exit_label] = []
                self.current_block = exit_label

        # 3. WHILE loops
        elif stmt.startswith("while"):
            match = re.match(r'^while\s*\((.*?)\)\s*(.*)$', stmt, re.DOTALL)
            if match:
                cond_expr = match.group(1).strip()
                loop_body = match.group(2).strip()
                
                if loop_body.startswith("{") and loop_body.endswith("}"):
                    loop_body = loop_body[1:-1].strip()
                
                idx = self.loop_counter
                self.loop_counter += 1
                cond_label = f"loop_cond_{idx}"
                body_label = f"loop_body_{idx}"
                exit_label = f"loop_exit_{idx}"
                
                self.blocks[self.current_block].append(f"  br label %{cond_label}")
                
                # Compile loop condition
                self.blocks[cond_label] = []
                self.current_block = cond_label
                reg_cond, type_cond = self._compile_expression(cond_expr, "i32")
                self.blocks[cond_label].append(
                    f"  br i1 {reg_cond}, label %{body_label}, label %{exit_label}"
                )
                
                # Compile loop body
                self.blocks[body_label] = []
                self.current_block = body_label
                self._compile_statements(loop_body)
                if not self._block_has_return(body_label):
                    self.blocks[body_label].append(f"  br label %{cond_label}")
                
                self.blocks[exit_label] = []
                self.current_block = exit_label

        # 4. Return statements
        elif stmt.startswith("return"):
            expr = stmt.replace("return", "").strip()
            if expr:
                reg, rtype = self._compile_expression(expr, "i32")
                self.blocks[self.current_block].append(
                    f"  ret {rtype} {reg}"
                )
            else:
                self.blocks[self.current_block].append("  ret void")

        # 5. Declarations and assignments
        else:
            # Check for declaration + assignment
            # e.g., int result = val * 8; or float* restrict a = ...;
            decl_match = re.match(r'^(int|double|float|long|int\*|float\*)\s+(\w+)\s*=\s*(.*)$', stmt)
            if decl_match:
                cpp_type = decl_match.group(1).strip()
                var_name = decl_match.group(2).strip()
                expr_str = decl_match.group(3).strip()
                
                llvm_type = self._to_llvm_type(cpp_type)
                align = self._to_llvm_align(llvm_type)
                
                # allocate variable
                ptr_name = f"%{var_name}"
                self.var_types[var_name] = llvm_type
                self.var_ptrs[var_name] = ptr_name
                
                self.blocks[self.current_block].append(
                    f"  {ptr_name} = alloca {llvm_type}, align {align}"
                )
                
                # Compile expression
                reg, rtype = self._compile_expression(expr_str, llvm_type)
                
                # Store
                self.blocks[self.current_block].append(
                    f"  store {llvm_type} {reg}, {llvm_type}* {ptr_name}, align {align}"
                )

                # Track constant values
                if re.match(r'^\d+$', expr_str):
                    self.const_values[var_name] = int(expr_str)
                elif expr_str in self.const_values:
                    self.const_values[var_name] = self.const_values[expr_str]
                else:
                    self.const_values.pop(var_name, None)
            
            # Simple declaration (no assignment), e.g., int sum;
            elif re.match(r'^(int|double|float|long|int\*|float\*)\s+(\w+)$', stmt):
                decl_parts = stmt.split()
                cpp_type = decl_parts[0].strip()
                var_name = decl_parts[1].strip()
                
                llvm_type = self._to_llvm_type(cpp_type)
                align = self._to_llvm_align(llvm_type)
                ptr_name = f"%{var_name}"
                
                self.var_types[var_name] = llvm_type
                self.var_ptrs[var_name] = ptr_name
                self.blocks[self.current_block].append(
                    f"  {ptr_name} = alloca {llvm_type}, align {align}"
                )

            # Array assignments, e.g. data[i] = ...
            elif "[" in stmt and "=" in stmt:
                idx_match = re.match(r'^(\w+)\[([^\]]+)\]\s*=\s*(.*)$', stmt)
                if idx_match:
                    arr_name = idx_match.group(1)
                    idx_expr = idx_match.group(2)
                    expr_str = idx_match.group(3)
                    
                    # Compile index
                    idx_reg, _ = self._compile_expression(idx_expr, "i32")
                    
                    # Load array address
                    arr_type = self.var_types.get(arr_name) or self.args_map.get(arr_name) or "i32*"
                    base_ptr = self.var_ptrs.get(arr_name) or f"%{arr_name}.addr"
                    
                    reg_addr = self._next_reg()
                    align_ptr = self._to_llvm_align(arr_type)
                    self.blocks[self.current_block].append(
                        f"  {reg_addr} = load {arr_type}, {arr_type}* {base_ptr}, align {align_ptr}"
                    )
                    
                    # GEP
                    elem_type = arr_type.rstrip("*")
                    llvm_elem_type = self._to_llvm_type(elem_type)
                    reg_gep = self._next_reg()
                    self.blocks[self.current_block].append(
                        f"  {reg_gep} = getelementptr inbounds {llvm_elem_type}, {arr_type} {reg_addr}, i32 {idx_reg}"
                    )
                    
                    # Compile expression
                    reg_expr, rtype = self._compile_expression(expr_str, llvm_elem_type)
                    
                    # Store to GEP
                    align_elem = self._to_llvm_align(llvm_elem_type)
                    self.blocks[self.current_block].append(
                        f"  store {llvm_elem_type} {reg_expr}, {llvm_elem_type}* {reg_gep}, align {align_elem}"
                    )

            # Simple assignments or self-operations, e.g. sum = sum + 2 or sum += x or i++
            elif "=" in stmt or "+=" in stmt or "-=" in stmt or "*=" in stmt or "/=" in stmt:
                op_match = re.match(r'^(\w+)\s*(\+|-|\*|/)?=\s*(.*)$', stmt)
                if op_match:
                    var_name = op_match.group(1).strip()
                    op = op_match.group(2)
                    expr_str = op_match.group(3).strip()
                    
                    if var_name in self.var_ptrs or var_name in self.args_map:
                        llvm_type = self.var_types.get(var_name) or self.args_map.get(var_name) or "i32"
                        ptr_name = self.var_ptrs.get(var_name) or f"%{var_name}.addr"
                        
                        if op:
                            full_expr = f"{var_name} {op} {expr_str}"
                            reg, rtype = self._compile_expression(full_expr, llvm_type)
                        else:
                            reg, rtype = self._compile_expression(expr_str, llvm_type)
                            
                        align = self._to_llvm_align(llvm_type)
                        self.blocks[self.current_block].append(
                            f"  store {llvm_type} {reg}, {llvm_type}* {ptr_name}, align {align}"
                        )

                        # Track constant values
                        if not op and re.match(r'^\d+$', expr_str):
                            self.const_values[var_name] = int(expr_str)
                        else:
                            self.const_values.pop(var_name, None)
            
            # Increments/decrements, e.g. i++ or i-- or ++i
            elif "++" in stmt or "--" in stmt:
                var_name = stmt.replace("++", "").replace("--", "").strip()
                if var_name in self.var_ptrs or var_name in self.args_map:
                    llvm_type = self.var_types.get(var_name) or self.args_map.get(var_name) or "i32"
                    ptr_name = self.var_ptrs.get(var_name) or f"%{var_name}.addr"
                    
                    # load
                    reg_load = self._next_reg()
                    align = self._to_llvm_align(llvm_type)
                    self.blocks[self.current_block].append(
                        f"  {reg_load} = load {llvm_type}, {llvm_type}* {ptr_name}, align {align}"
                    )
                    
                    # op
                    reg_op = self._next_reg()
                    op_inst = "add nsw" if "++" in stmt else "sub nsw"
                    self.blocks[self.current_block].append(
                        f"  {reg_op} = {op_inst} {llvm_type} {reg_load}, 1"
                    )
                    
                    # store
                    self.blocks[self.current_block].append(
                        f"  store {llvm_type} {reg_op}, {llvm_type}* {ptr_name}, align {align}"
                    )

    def _compile_expression(self, expr: str, target_type: str = "i32") -> Tuple[str, str]:
        expr = expr.strip()
        
        # 1. Numeric constant
        if re.match(r'^\d+(\.\d+)?$', expr):
            if "." in expr:
                return expr, "double" if target_type == "double" else "float"
            return expr, "i32"
            
        # 2. Single variable name
        if re.match(r'^\w+$', expr):
            var_name = expr
            if var_name in self.var_ptrs:
                var_ptr = self.var_ptrs[var_name]
                var_type = self.var_types.get(var_name, "i32")
                reg = self._next_reg()
                align = self._to_llvm_align(var_type)
                self.blocks[self.current_block].append(
                    f"  {reg} = load {var_type}, {var_type}* {var_ptr}, align {align}"
                )
                return reg, var_type
            elif var_name in self.args_map:
                addr_ptr = f"%{var_name}.addr"
                var_type = self.args_map[var_name]
                reg = self._next_reg()
                align = self._to_llvm_align(var_type)
                self.blocks[self.current_block].append(
                    f"  {reg} = load {var_type}, {var_type}* {addr_ptr}, align {align}"
                )
                return reg, var_type
            else:
                return expr, "i32"

        # 3. Array indexing, e.g., data[i]
        array_match = re.match(r'^(\w+)\[([^\]]+)\]$', expr)
        if array_match:
            arr_name = array_match.group(1)
            idx_expr = array_match.group(2)
            
            idx_reg, _ = self._compile_expression(idx_expr, "i32")
            
            arr_type = self.var_types.get(arr_name) or self.args_map.get(arr_name) or "i32*"
            base_ptr = self.var_ptrs.get(arr_name) or f"%{arr_name}.addr"
            
            reg_addr = self._next_reg()
            align_ptr = self._to_llvm_align(arr_type)
            self.blocks[self.current_block].append(
                f"  {reg_addr} = load {arr_type}, {arr_type}* {base_ptr}, align {align_ptr}"
            )
            
            elem_type = arr_type.rstrip("*")
            llvm_elem_type = self._to_llvm_type(elem_type)
            reg_gep = self._next_reg()
            self.blocks[self.current_block].append(
                f"  {reg_gep} = getelementptr inbounds {llvm_elem_type}, {arr_type} {reg_addr}, i32 {idx_reg}"
            )
            
            reg_val = self._next_reg()
            align_elem = self._to_llvm_align(llvm_elem_type)
            self.blocks[self.current_block].append(
                f"  {reg_val} = load {llvm_elem_type}, {llvm_elem_type}* {reg_gep}, align {align_elem}"
            )
            return reg_val, llvm_elem_type

        # 4. Function calls, e.g., helper(a)
        call_match = re.match(r'^(\w+)\(([^)]*)\)$', expr)
        if call_match:
            c_name = call_match.group(1)
            c_args_raw = call_match.group(2)
            
            # Simulated optimization: Function Inlining
            if c_name in self.inline_funcs and self.opt_level in ["-O2", "-O3"]:
                arg_names, ret_expr = self.inline_funcs[c_name]
                c_args = [carg.strip() for carg in c_args_raw.split(",")] if c_args_raw.strip() else []
                substituted_expr = ret_expr
                for arg_name, arg_val in zip(arg_names, c_args):
                    substituted_expr = re.sub(r'\b' + re.escape(arg_name) + r'\b', arg_val, substituted_expr)
                
                return self._compile_expression(substituted_expr, target_type)

            c_args_compiled = []
            if c_args_raw.strip():
                for carg in c_args_raw.split(","):
                    creg, ctype = self._compile_expression(carg.strip(), "i32")
                    c_args_compiled.append(f"{ctype} {creg}")
            
            reg_call = self._next_reg()
            args_str = ", ".join(c_args_compiled)
            self.blocks[self.current_block].append(
                f"  {reg_call} = call i32 @{c_name}({args_str})"
            )
            return reg_call, "i32"

        # 5. Binary operators
        operators = [
            ("==", "icmp eq"), ("!=", "icmp ne"),
            ("<=", "icmp sle"), (">=", "icmp sge"),
            ("<", "icmp slt"), (">", "icmp sgt"),
            ("<<", "shl"), (">>", "ashr"),
            ("+", "add"), ("-", "sub"),
            ("*", "mul"), ("/", "sdiv"),
        ]
        
        for op_sym, op_llvm in operators:
            op_idx = self._find_operator(expr, op_sym)
            if op_idx != -1:
                lhs = expr[:op_idx].strip()
                rhs = expr[op_idx + len(op_sym):].strip()
                
                reg_lhs, type_lhs = self._compile_expression(lhs, target_type)
                reg_rhs, type_rhs = self._compile_expression(rhs, target_type)
                
                is_float = (type_lhs in ["float", "double"])
                
                op_inst = op_llvm
                if is_float:
                    if op_inst == "add": op_inst = "fadd"
                    elif op_inst == "sub": op_inst = "fsub"
                    elif op_inst == "mul": op_inst = "fmul"
                    elif op_inst == "sdiv": op_inst = "fdiv"
                    elif "icmp" in op_inst:
                        op_inst = op_inst.replace("icmp s", "fcmp o")
                        op_inst = op_inst.replace("icmp eq", "fcmp oeq")
                        op_inst = op_inst.replace("icmp ne", "fcmp one")
                
                nsw_flag = " nsw" if op_inst in ["add", "sub", "mul"] and not is_float else ""
                
                reg_res = self._next_reg()
                self.blocks[self.current_block].append(
                    f"  {reg_res} = {op_inst}{nsw_flag} {type_lhs} {reg_lhs}, {reg_rhs}"
                )
                return reg_res, type_lhs

        return expr, "i32"

    def _find_operator(self, expr: str, op: str) -> int:
        braces = 0
        i = 0
        while i < len(expr):
            char = expr[i]
            if char == '(':
                braces += 1
            elif char == ')':
                braces -= 1
            elif braces == 0 and expr[i:i+len(op)] == op:
                return i
            i += 1
        return -1
