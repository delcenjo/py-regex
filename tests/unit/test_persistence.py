import pytest
from pyregex.infrastructure.persistence.pattern_repository import SavedPattern

def test_pattern_repository_save_load(temp_repo):
    """Verify that a pattern can be saved and then retrieved."""
    pattern = SavedPattern(name="test_email", pattern=r"[\w.-]+@[\w.-]+\.\w+")
    temp_repo.save(pattern)
    
    loaded = temp_repo.get("test_email")
    assert loaded is not None
    assert loaded.name == "test_email"
    assert loaded.pattern == r"[\w.-]+@[\w.-]+\.\w+"

def test_pattern_repository_favorite(temp_repo):
    """Verify favoriting behavior."""
    pattern = SavedPattern(name="fav_test", pattern="foo")
    temp_repo.save(pattern)
    
    assert temp_repo.toggle_favorite("fav_test") is True
    assert temp_repo.get("fav_test").is_favorite is True
    
    assert temp_repo.toggle_favorite("fav_test") is False
    assert temp_repo.get("fav_test").is_favorite is False

def test_pattern_repository_delete(temp_repo):
    """Verify deletion."""
    pattern = SavedPattern(name="to_delete", pattern="bar")
    temp_repo.save(pattern)
    assert temp_repo.get("to_delete") is not None
    
    assert temp_repo.delete("to_delete") is True
    assert temp_repo.get("to_delete") is None
