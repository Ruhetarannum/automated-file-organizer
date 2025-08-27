import pytest
import sys
import os


def run_all_tests():
    tests_dir = "tests"

    if not os.path.exists(tests_dir):
        print(f"❌ Tests directory not found: {tests_dir}")
        sys.exit(1)

    print(f"\n🚀 Running all tests in: {tests_dir}\n")
    # Run pytest with verbose output
    exit_code = pytest.main(["-v", tests_dir])

    if exit_code == 0:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Check output above.")
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_tests())
