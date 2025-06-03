from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def test_files():
    return Path(__file__).parent / 'files'
