import unittest
import os


def run_all_tests():
    tests_dir = "tests"
    loader = unittest.TestLoader()

    # Discover all test files in 'tests' folder
    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_file_path = os.path.join(root, file)
                module_name = os.path.splitext(test_file_path.replace(os.sep, "."))[0]

                print(f"\nRunning tests in: {test_file_path}")

                try:
                    tests = loader.loadTestsFromName(module_name)
                    runner = unittest.TextTestRunner(verbosity=2)
                    result = runner.run(tests)

                    if not result.wasSuccessful():
                        print(f"\n❌ Errors or failures in {test_file_path}")
                    else:
                        print(f"✅ All tests passed in {test_file_path}")
                except Exception as e:
                    print(f"\n⚠ Could not run tests in {test_file_path}")
                    print(f"Error: {e}")


if __name__ == "__main__":
    run_all_tests()
