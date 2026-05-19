import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class BasicBlock:
    """Represents a normalized basic block."""
    label: str
    instructions: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.label)


@dataclass
class Function:
    """Represents an extracted function from normalized LLVM IR."""
    name: str
    return_type: str
    arguments: List[str] = field(default_factory=list)
    blocks: List[BasicBlock] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    function_calls: List[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self):
        return {
            "name": self.name,
            "return_type": self.return_type,
            "arguments": self.arguments,
            "block_count": len(self.blocks),
            "instruction_count": len(self.instructions),
            "function_calls": self.function_calls,
        }


class FunctionMapper:
    """Extracts functions from normalized LLVM IR."""

    def extract_functions(self, ir_content: str) -> Dict[str, Function]:
        """Parse LLVM IR and extract all functions.
        
        Returns dict: {function_name -> Function}
        """
        functions: Dict[str, Function] = {}
        lines = ir_content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Match function definition: define <return_type> @<name>(<args>)
            match = re.match(r'define\s+(\S+)\s+@([\w\.]+)\s*\((.*?)\)', line)
            if match:
                return_type = match.group(1)
                func_name = match.group(2)
                args_str = match.group(3)

                # Parse arguments
                args = self._parse_arguments(args_str)

                # Extract function body (until closing brace)
                body_lines = []
                brace_count = 0
                in_body = False

                # Check if '{' is in the define line itself
                if '{' in line:
                    in_body = True
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')

                i += 1
                while i < len(lines):
                    body_line = lines[i]
                    if '{' in body_line:
                        in_body = True
                        brace_count += body_line.count('{')
                    if '}' in body_line:
                        brace_count -= body_line.count('}')
                    if in_body:
                        body_lines.append(body_line)
                    if in_body and brace_count == 0:
                        i += 1
                        break
                    i += 1

                # Parse function body
                blocks = self._extract_blocks('\n'.join(body_lines))
                instructions = self._extract_instructions('\n'.join(body_lines))
                calls = self._extract_function_calls('\n'.join(body_lines))

                func = Function(
                    name=func_name,
                    return_type=return_type,
                    arguments=args,
                    blocks=blocks,
                    instructions=instructions,
                    function_calls=calls,
                    raw_text='\n'.join(body_lines),
                )
                functions[func_name] = func
            else:
                i += 1

        return functions

    def _parse_arguments(self, args_str: str) -> List[str]:
        """Parse function arguments (e.g., 'i32 %a, i32 %b')."""
        if not args_str.strip():
            return []
        
        args = []
        # Split by comma, but respect parentheses
        parts = re.split(r',\s*', args_str)
        for part in parts:
            part = part.strip()
            if part:
                # Extract type + name (e.g., "i32 %a" -> "i32")
                match = re.match(r'(\S+)', part)
                if match:
                    args.append(match.group(1))
        return args

    def _extract_blocks(self, func_body: str) -> List[BasicBlock]:
        """Extract basic blocks from function body."""
        blocks = []
        current_block = None
        lines = func_body.split('\n')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('{') or stripped.startswith('}'):
                continue

            # Block label (ends with :)
            if stripped.endswith(':') and not stripped.startswith('!'):
                if current_block:
                    blocks.append(current_block)
                label = stripped[:-1]
                current_block = BasicBlock(label=label)
            elif not stripped.startswith('!'):
                if current_block is None:
                    current_block = BasicBlock(label="entry")
                current_block.instructions.append(stripped)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _extract_instructions(self, func_body: str) -> List[str]:
        """Extract all instructions from function body."""
        instructions = []
        lines = func_body.split('\n')

        for line in lines:
            stripped = line.strip()
            # Skip labels, braces, and metadata
            if stripped and not stripped.endswith(':') and not stripped.startswith('{') and not stripped.startswith('}') and not stripped.startswith('!'):
                instructions.append(stripped)

        return instructions

    def _extract_function_calls(self, func_body: str) -> List[str]:
        """Extract called functions from function body."""
        calls = set()
        # Match patterns like: call i32 @function_name(...)
        matches = re.findall(r'call\s+\S+\s+@([\w\.]+)\s*\(', func_body)
        calls.update(matches)
        return sorted(list(calls))
