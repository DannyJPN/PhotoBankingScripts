# IMPLEMENTATION_STATUS.md — givephotobankreadymediafiles

## What is implemented

### Core pipeline
- `givephotobankreadymediafiles.py` — main entry point, GUI media viewer with metadata editing
- `preparemediafile.py` — single-file CLI metadata preparation
- `generatealternatives.py` — generate BW/negative/sharpen/misty/blurred variants

### AI metadata generation (`givephotobankreadymediafileslib/`)
- `metadata_generator.py` — title, description, keyword generation via AI providers
- `ai_coordinator.py` — orchestrates single and batch AI requests
- `batch_manager.py` — OpenAI Batch API lifecycle (collect → send → poll → import)
- `batch_state.py`, `batch_lock.py` — batch persistence and concurrency control
- `batch_prompts.py` — prompt templates for batch metadata generation
- `categories_manager.py` — per-bank category assignment
- `alternative_generator.py` — alternative edit type processing

### GUI components (`givephotobankreadymediafileslib/`)
- `media_viewer.py`, `media_viewer_refactored.py` — main viewer window
- `media_display.py`, `viewer_state.py` — display helpers and state management
- `editorial_dialog.py` — editorial metadata input dialog
- `batch_description_dialog.py` — batch job description dialog
- `tag_entry.py`, `ui_components.py` — reusable UI widgets
- `media_processor.py`, `media_helper.py` — file I/O helpers for GUI
- `metadata_validator.py` — validates metadata before write
- `mediainfo_loader.py` — loads EXIF/media info

### AI provider layer (`shared/`)
- `ai_provider.py` — abstract base: `Message`, `AIResponse`, `BatchJob`, `ContentBlock`
- `cloud_ai.py`, `local_ai.py`, `neural_network.py` — provider base classes
- `openai_provider.py` — OpenAI API (GPT-4o, GPT-4.1, GPT-5, o-series), batch support
- `anthropic_provider.py` — Anthropic API (Claude 3.x, Claude 4.x), batch support
- `ollama_provider.py` — local Ollama server (LLaVA, Llama 3.2-vision, Qwen2.5-VL, etc.)
- `ai_factory.py` — provider registry and `create_from_model_key()` convenience API
- `ai_module.py` — high-level wrapper used by metadata_generator
- `prompt_manager.py` — prompt template management

### Utilities (`shared/`)
- `config.py` — loads `config_template.json` and user config overlay
- `config_template.json` — canonical model/provider registry with pricing
- `exif_handler.py`, `exif_downloader.py` — EXIF read/write via ExifTool
- `file_operations.py` — centralised CRUD (copy, move, delete, ensure_dir)
- `hash_utils.py` — perceptual and cryptographic hash helpers
- `csv_sanitizer.py` — CSV encoding/header normalisation
- `logging_config.py`, `utils.py` — shared logging and misc helpers

### Constants
- `givephotobankreadymediafileslib/constants.py` — all default paths, column names, batch
  limits, status values, Ollama model lists, photobank category counts

### Tests
- Unit tests for all major modules under `tests/unit/`
- Integration tests: `tests/integration/test_metadata_generator_pipeline__scenarios.py`
- Performance tests: `tests/performance/`
- Security tests: `tests/security/`

---

## Pending / known limitations

- No Google AI (Gemini) or Mistral provider implementations (stubs registered in factory but classes not present)
- `uploadtophotobanks/` integration is planned but not connected
- Batch polling uses fixed interval; adaptive back-off not implemented
- Ollama vision model list in `ollama_provider.py` is a static set; no auto-discovery from running server at init time
- `config_template.json` prices are indicative; no live price-fetch mechanism

---

## Recent changes

- AI provider model lists updated to reflect current Claude 4.x, GPT-5/4.1, and Ollama vision models
- Fixed pricing errors across OpenAI and Anthropic entries in `config_template.json`
- Removed duplicate JSON keys (`claude-3-7-sonnet-20250219`, `claude-3-5-haiku-20241022`) that caused silent data loss
- Added `claude-opus-4-7` as current flagship Anthropic model
- Corrected Ollama `vision_models` set: added `qwen2.5-vl`, `minicpm-v`, `moondream2`, `llama4:scout/maverick`
- Fixed `supports_images` flag in config_template.json for o3/o3-pro/o4-mini (all three support vision)
- `copy_file()` in `shared/file_operations.py` rewritten to atomic temp+fsync+rename pattern — prevents zero-filled/truncated files on interrupted writes (issue #156)
