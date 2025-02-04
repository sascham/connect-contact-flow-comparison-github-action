import os
import sys
import warnings

import pytest


@pytest.fixture(autouse=True)
def ignore_datetime_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, message="datetime.datetime.utcnow()")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="botocore.auth")

# Add the src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
