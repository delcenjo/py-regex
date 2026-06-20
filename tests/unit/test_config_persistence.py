import pytest
from pyregex.infrastructure.config.models import AppConfig

def test_config_repository_save_load(temp_config_repo):
    """Verify that config can be saved and loaded."""
    config = AppConfig(region="EU", theme="light")
    temp_config_repo.save(config)
    
    loaded = temp_config_repo.load()
    assert loaded.region == "EU"
    assert loaded.theme == "light"

def test_config_repository_default(temp_config_repo):
    """Verify default config when file doesn't exist."""
    assert temp_config_repo.exists() is False
    config = temp_config_repo.load()
    assert config.region == "US" # Default
