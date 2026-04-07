import pytest
import shutil
from pathlib import Path
from pyregex.infrastructure.persistence.pattern_repository import PatternRepository
from pyregex.infrastructure.persistence.config_repository import ConfigRepository

@pytest.fixture
def temp_dir(tmp_path):
    """Provides a temporary directory for file-based tests."""
    return tmp_path

@pytest.fixture
def temp_repo(temp_dir):
    """Provides a PatternRepository pointing to a temporary directory."""
    repo = PatternRepository(private_dir=temp_dir, global_dir=temp_dir)
    return repo

@pytest.fixture
def temp_config_repo(temp_dir):
    """Provides a ConfigRepository pointing to a temporary directory."""
    repo = ConfigRepository(config_dir=temp_dir)
    return repo
