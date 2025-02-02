import pytest
import subprocess

@pytest.fixture(scope='session', autouse=True)
def setup_environment():
    # Example setup step: Ensure LocalStack is running
    try:
        result = subprocess.run(['python', 'setup.py', 'install'], check=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    except subprocess.CalledProcessError as error:
        print(f"Error occurred: {error}")
        print(f"Output: {error.output}")
        print(f"Error Output: {error.stderr}")
        if "subprocess-exited-with-error" in error.stderr:
            print("A subprocess exited with an error. This is likely not a problem with pip.")
            if "PyYAML" in error.stderr:
                print("The error occurred while installing the PyYAML package. Please check the build dependencies.")
        raise
    except Exception as error:
        print(f"An unexpected error occurred: {error}")
        raise
    # Add other setup steps as needed
    yield
    # Teardown steps if necessary
