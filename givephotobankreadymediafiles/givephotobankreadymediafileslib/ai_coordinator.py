"""
AI generation coordination logic.

This module handles:
- AI model management and selection
- Thread coordination for AI generation tasks
- Generation workflow orchestration (title, description, keywords, categories)
- Cancellation and completion handling
"""

import logging
import threading
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field


@dataclass
class AIThreadState:
    """
    State for AI generation threads.

    :param thread: Active thread or None
    :param cancelled: Whether generation was cancelled
    """

    thread: Optional[threading.Thread] = None
    cancelled: bool = False


@dataclass
class AIModelInfo:
    """
    Information about an AI model.

    :param key: Model key in format "provider/model_name"
    :param display_name: Human-readable display name
    :param provider: AI provider name
    :param model_name: Model name within provider
    """

    key: str
    display_name: str
    provider: str
    model_name: str


def load_available_models() -> List[AIModelInfo]:
    """
    Load available AI models from configuration.

    :return: List of available AI models
    :raises: Exception if config loading fails
    """
    try:
        from shared.config import get_config

        config = get_config()
        available_models = config.get_available_ai_models()

        if not available_models:
            logging.warning("No AI models available - check API keys in environment or config")
            return []

        # Convert to AIModelInfo dataclasses
        return [
            AIModelInfo(
                key=model["key"],
                display_name=model["display_name"],
                provider=model["key"].split("/")[0],
                model_name=model["key"].split("/")[1]
            )
            for model in available_models
        ]

    except Exception as e:
        logging.error(f"Error loading AI models: {e}")
        raise


def get_default_model() -> tuple[str, str]:
    """
    Get default AI model provider and name.

    :return: Tuple of (provider, model_name)
    :raises: Exception if config loading fails
    """
    try:
        from shared.config import get_config

        config = get_config()
        return config.get_default_ai_model()

    except Exception as e:
        logging.error(f"Error getting default model: {e}")
        raise


def find_model_by_display_name(display_name: str, available_models: List[AIModelInfo]) -> Optional[str]:
    """
    Find model key by display name.

    :param display_name: Display name to search for
    :param available_models: List of available models
    :return: Model key or None if not found
    """
    for model in available_models:
        if model.display_name == display_name:
            return model.key
    return None


def create_metadata_generator(model_key: str):
    """
    Create a metadata generator for the given model.

    :param model_key: Model key in format "provider/model_name"
    :return: Metadata generator instance
    :raises: Exception if generator creation fails
    """
    try:
        from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator

        return create_metadata_generator(model_key)

    except Exception as e:
        logging.error(f"Error creating metadata generator: {e}")
        raise


def generate_title_sync(
    file_path: str,
    model_key: str,
    existing_title: Optional[str] = None
) -> str:
    """
    Generate title synchronously using AI.

    :param file_path: Path to media file
    :param model_key: Model key in format "provider/model_name"
    :param existing_title: Existing title to refine (optional)
    :return: Generated title
    :raises: Exception if generation fails
    """
    generator = create_metadata_generator(model_key)
    return generator.generate_title(file_path, existing_title)


def generate_description_sync(
    file_path: str,
    model_key: str,
    existing_title: Optional[str] = None,
    existing_description: Optional[str] = None,
    editorial_data: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate description synchronously using AI.

    :param file_path: Path to media file
    :param model_key: Model key in format "provider/model_name"
    :param existing_title: Existing title for context (optional)
    :param existing_description: Existing description to refine (optional)
    :param editorial_data: Editorial metadata if applicable (optional)
    :return: Generated description
    :raises: Exception if generation fails
    """
    generator = create_metadata_generator(model_key)
    return generator.generate_description(
        file_path,
        existing_title,
        existing_description,
        editorial_data
    )


def generate_keywords_sync(
    file_path: str,
    model_key: str,
    keyword_count: int,
    existing_title: Optional[str] = None,
    existing_description: Optional[str] = None,
    is_editorial: bool = False
) -> List[str]:
    """
    Generate keywords synchronously using AI.

    :param file_path: Path to media file
    :param model_key: Model key in format "provider/model_name"
    :param keyword_count: Number of keywords to generate
    :param existing_title: Existing title for context (optional)
    :param existing_description: Existing description for context (optional)
    :param is_editorial: Whether this is editorial content
    :return: List of generated keywords
    :raises: Exception if generation fails
    """
    generator = create_metadata_generator(model_key)
    return generator.generate_keywords(
        file_path,
        existing_title,
        existing_description,
        keyword_count,
        is_editorial
    )


def generate_categories_sync(
    file_path: str,
    model_key: str,
    photobank_categories: Dict[str, List[str]],
    existing_title: Optional[str] = None,
    existing_description: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Generate categories synchronously using AI.

    :param file_path: Path to media file
    :param model_key: Model key in format "provider/model_name"
    :param photobank_categories: Available categories per photobank
    :param existing_title: Existing title for context (optional)
    :param existing_description: Existing description for context (optional)
    :return: Dict of photobank -> list of selected categories
    :raises: Exception if generation fails
    """
    generator = create_metadata_generator(model_key)
    generator.set_photobank_categories(photobank_categories)
    return generator.generate_categories(
        file_path,
        existing_title,
        existing_description
    )


def start_generation_thread(
    target_function: Callable,
    args: tuple,
    daemon: bool = True
) -> threading.Thread:
    """
    Start a new generation thread.

    :param target_function: Function to run in thread
    :param args: Arguments to pass to function
    :param daemon: Whether thread should be daemon
    :return: Started thread
    """
    thread = threading.Thread(target=target_function, args=args, daemon=daemon)
    thread.start()
    return thread


def is_thread_running(thread: Optional[threading.Thread]) -> bool:
    """
    Check if a thread is currently running.

    :param thread: Thread to check
    :return: True if thread is alive, False otherwise
    """
    return thread is not None and thread.is_alive()


def wait_for_thread(thread: Optional[threading.Thread]) -> None:
    """
    Wait for a thread to complete.

    :param thread: Thread to wait for
    """
    if thread and thread.is_alive():
        thread.join()