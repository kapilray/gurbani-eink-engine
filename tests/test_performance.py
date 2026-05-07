"""
Build Performance Tests.

Ensures that the build process remains efficient and doesn't regress 
significantly in speed.
"""
import sys, os, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_SCRIPT = os.path.join(ROOT, 'scripts', 'build.py')
PYTHON = sys.executable

def test_build_performance():
    """
    Japji Sahib should build in under 10 seconds on a typical machine.
    This catches accidental O(n^2) regexes or slow network calls.
    """
    start_time = time.time()
    
    # Run the build script
    result = subprocess.run(
        [PYTHON, BUILD_SCRIPT],
        capture_output=True,
        text=True,
        cwd=ROOT
    )
    
    duration = time.time() - start_time
    
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    assert duration < 10.0, f"Build took too long: {duration:.2f}s (limit: 10s)"

if __name__ == "__main__":
    try:
        test_build_performance()
        print("PASS: Performance baseline met.")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
