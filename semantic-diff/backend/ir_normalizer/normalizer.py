import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
from pathlib import Path


@dataclass
class NormalizationStats:
    metadata_removed: int = 0
    variables_canonicalized: int = 0
    blocks_normalized: int = 0
    comments_removed: int = 0


class IRNormalizer:
    """Reusable LLVM IR normalization pipeline."""

    def __init__(self):
        self.var_mapping: Dict[str, str] = {}
        self.block_mapping: Dict[str, str] = {}
        self.var_counter = 0
        self.block_counter = 0
        self.stats = NormalizationStats()

    def normalize(self, ir_content: str) -> Tuple[str, NormalizationStats]:
        """Normalize LLVM IR and return normalized IR + statistics."""
        self.var_mapping.clear()
        self.block_mapping.clear()
        self.var_counter = 0
        self.block_counter = 0
        self.stats = NormalizationStats()

        # Step 1: Strip metadata and declarations
        ir = self._strip_metadata_and_declarations(ir_content)

        # Step 2: Canonicalize variables
        ir = self._canonicalize_variables(ir)

        # Step 3: Normalize basic blocks
        ir = self._normalize_blocks(ir)

        # Step 4: Normalize formatting
        ir = self._normalize_formatting(ir)

        return ir, self.stats

    def _strip_metadata_and_declarations(self, ir: str) -> str:
        """Remove metadata, comments, source info, target specs."""
        lines = ir.split('\n')
        result = []

        for line in lines:
            # Skip empty lines initially (will normalize later)
            if not line.strip():
                continue

            # Skip comments
            if line.strip().startswith(';'):
                self.stats.comments_removed += 1
                continue

            # Skip source_filename, target triple, target datalayout
            if any(x in line for x in ['source_filename', 'target triple', 'target datalayout']):
                self.stats.metadata_removed += 1
                continue

            # Remove inline metadata (!dbg, !llvm.loop, !tbaa, !prof, etc.)
            original_line = line
            line = re.sub(r'(![\w\.]+(\s*=\s*)?[\w\{\}\,\s]*)', '', line)
            line = re.sub(r'(![\w\.]+)', '', line)

            if line != original_line:
                self.stats.metadata_removed += (len(original_line.split('!')) - 1)

            # Clean up extra spaces
            line = re.sub(r'\s+', ' ', line).strip()

            if line:
                result.append(line)

        return '\n'.join(result)

    def _canonicalize_variables(self, ir: str) -> str:
        """Convert %1, %x, %tmp etc. to v1, v2, v3..."""
        lines = ir.split('\n')
        result = []

        for line in lines:
            # Find all variable references (starting with %)
            variables = set(re.findall(r'%[\w\.]+', line))

            for var in sorted(variables):  # Sort for determinism
                if var not in self.var_mapping:
                    self.var_mapping[var] = f'v{self.var_counter}'
                    self.var_counter += 1
                    self.stats.variables_canonicalized += 1

                line = line.replace(var, self.var_mapping[var])

            result.append(line)

        return '\n'.join(result)

    def _normalize_blocks(self, ir: str) -> str:
        """Normalize basic block labels to block_0, block_1, etc."""
        lines = ir.split('\n')
        result = []

        for line in lines:
            # Match block labels (pattern: label_name:)
            match = re.match(r'^(\w+):(.*)$', line)
            if match:
                label = match.group(1)
                rest = match.group(2)

                if label not in self.block_mapping:
                    self.block_mapping[label] = f'block_{self.block_counter}'
                    self.block_counter += 1
                    self.stats.blocks_normalized += 1

                line = f'{self.block_mapping[label]}:{rest}'

            # Replace block references in jumps (br i1 %cond, label %ifthen, label %ifend)
            for old_block, new_block in self.block_mapping.items():
                line = re.sub(
                    rf'\blabel\s+%{re.escape(old_block)}\b',
                    f'label %{new_block}',
                    line
                )
                line = re.sub(
                    rf'%{re.escape(old_block)}\b',
                    f'%{new_block}',
                    line
                )

            result.append(line)

        return '\n'.join(result)

    def _normalize_formatting(self, ir: str) -> str:
        """Normalize whitespace and formatting for stable serialization."""
        lines = ir.split('\n')
        result = []

        for line in lines:
            # Normalize whitespace: multiple spaces -> single space
            line = re.sub(r'\s+', ' ', line)

            # Normalize spacing around operators
            line = re.sub(r'\s*=\s*', ' = ', line)
            line = re.sub(r'\s+,\s+', ', ', line)
            line = re.sub(r',(\S)', r', \1', line)

            # Remove trailing spaces
            line = line.rstrip()

            # Skip empty lines, but preserve block structure
            if line or (result and result[-1].endswith(':')):
                result.append(line)

        # Remove consecutive blank lines
        cleaned = []
        prev_blank = False
        for line in result:
            if not line.strip():
                if not prev_blank:
                    cleaned.append(line)
                prev_blank = True
            else:
                cleaned.append(line)
                prev_blank = False

        return '\n'.join(cleaned)

    @staticmethod
    def from_file(file_path: str) -> Tuple[str, Dict]:
        """Load and normalize from file."""
        content = Path(file_path).read_text(encoding='utf-8')
        normalizer = IRNormalizer()
        normalized, stats = normalizer.normalize(content)
        return normalized, {
            'metadata_removed': stats.metadata_removed,
            'variables_canonicalized': stats.variables_canonicalized,
            'blocks_normalized': stats.blocks_normalized,
            'comments_removed': stats.comments_removed,
        }
