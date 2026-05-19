import subprocess
import sys
from pathlib import Path

def test_cli_compare():
    # Paths to test case files (adjust if needed)
    old_file = Path(__file__).parents[1] / 'testcases' / 'tc2_dce_old.cpp'
    new_file = Path(__file__).parents[1] / 'testcases' / 'tc2_dce_new.cpp'
    output_report = Path('test_report.txt')

    # Run the CLI compare command
    result = subprocess.run([
        sys.executable,
        '-m', 'src.cli',
        'compare',
        str(old_file),
        str(new_file),
        '-o', str(output_report)
    ], capture_output=True, text=True)

    # Ensure the process exited without error
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    # Verify report was created
    assert output_report.exists(), "Report file was not generated"
    # Simple sanity check on content
    content = output_report.read_text(encoding='utf-8')
    assert "Overall Risk" in content, "Report does not contain expected sections"
    # Clean up
    output_report.unlink()

if __name__ == '__main__':
    test_cli_compare()
    print('Test passed')
