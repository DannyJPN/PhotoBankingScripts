"""
Test-specific constants for GivePhotoBankReadyMediaFiles module.

This module provides test-only values as required by CLAUDE.md global rules.
"""

from typing import Dict, List

# Test directories - safe paths for testing
TEST_MEDIA_CSV: str = "F:/Dropbox/Scripts/Python/Fotobanking/givephotobankreadymediafiles/tests/data/test_media.csv"
TEST_CATEGORIES_CSV: str = "F:/Dropbox/Scripts/Python/Fotobanking/givephotobankreadymediafiles/tests/data/test_categories.csv"
TEST_TRAINING_DATA_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/givephotobankreadymediafiles/tests/data/training"
TEST_LOG_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/givephotobankreadymediafiles/tests/logs"
TEST_MODELS_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/givephotobankreadymediafiles/tests/data/models"

# Test-only configuration
TEST_LOG_LEVEL: str = "DEBUG"
TEST_INTERVAL: int = 1  # Fast interval for testing
TEST_MAX_COUNT: int = 5  # Process only few files in tests

# Test AI models
TEST_AI_MODELS: Dict[str, str] = {
    "local_llm": "test/local_model",
    "online_llm": "test/gpt-3.5-turbo",
    "neural_network": "test_title_model.pt"
}

# Test media files
TEST_MEDIA_FILES: Dict[str, str] = {
    "test_image.jpg": "F:/test/images/test_image.jpg",
    "test_video.mp4": "F:/test/videos/test_video.mp4"
}

# Test categories
TEST_CATEGORIES: List[str] = [
    "Test_Nature",
    "Test_People", 
    "Test_Technology"
]

# Mock API keys for testing (not real)
TEST_OPENAI_API_KEY: str = "test_openai_key_not_real"
TEST_ANTHROPIC_API_KEY: str = "test_anthropic_key_not_real"
TEST_GOOGLE_API_KEY: str = "test_google_key_not_real"