"""
Batch mode orchestration for givephotobankreadymediafiles.
"""
from __future__ import annotations

import os
import json
import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional

from PIL import Image

from shared.config import get_config
from shared.ai_module import Message, ContentBlock, create_from_model_key
from shared.file_operations import load_csv, save_csv_with_backup, read_json, write_json, read_binary

from givephotobankreadymediafileslib.constants import (
    COL_FILE, COL_PATH, COL_TITLE, COL_DESCRIPTION, COL_KEYWORDS, COL_PREP_DATE,
    COL_STATUS_SUFFIX, COL_EDITORIAL, COL_ORIGINAL, COL_CATEGORY_SUFFIX,
    MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH,
    STATUS_UNPROCESSED, STATUS_PREPARED, STATUS_REJECTED, STATUS_ERROR, STATUS_BACKUP,
    DEFAULT_BATCH_DESCRIPTION_MIN_LENGTH,
    DEFAULT_BATCH_POLL_INTERVAL,
    DEFAULT_ALTERNATIVE_BATCH_SIZE, DEFAULT_ALTERNATIVE_EFFECTS,
    EFFECT_NAME_MAPPING, ORIGINAL_NO, CSV_ALLOWED_EXTENSIONS,
    DEFAULT_DAILY_BATCH_LIMIT, BATCH_COST_LOG, BATCH_IMAGE_MAX_BASE64_BYTES,
    DEFAULT_BATCH_VISION_SIZE
)
from givephotobankreadymediafileslib.media_processor import find_unprocessed_records
from givephotobankreadymediafileslib.mediainfo_loader import load_media_records
from givephotobankreadymediafileslib.media_helper import is_image_file
from givephotobankreadymediafileslib.batch_state import BatchRegistry, BatchState
from givephotobankreadymediafileslib.batch_prompts import build_batch_prompt, build_alternative_prompt
from givephotobankreadymediafileslib.batch_description_dialog import collect_batch_description

from tqdm import tqdm
from givephotobankreadymediafileslib.alternative_generator import (
    AlternativeGenerator, get_alternative_output_dirs
)


def _get_default_model_key() -> str:
    config = get_config()
    provider, model = config.get_default_ai_model()
    return f"{provider}/{model}"


def _create_batch_provider(model_key: str):
    config = get_config()
    provider, model = model_key.split('/', 1)
    model_config = config.get_ai_model_config(provider, model)
    if not model_config:
        raise RuntimeError("No valid AI model configuration found for batch mode.")

    kwargs = {}
    api_key = model_config.get("api_key")
    endpoint = model_config.get("endpoint")
    if api_key:
        kwargs["api_key"] = api_key
    if endpoint:
        kwargs["base_url"] = endpoint

    provider_instance = create_from_model_key(model_key, **kwargs)
    if not provider_instance.supports_batch():
        raise RuntimeError(f"Model does not support batch processing: {model_key}")
    if not provider_instance.supports_images():
        raise RuntimeError(f"Model does not support images: {model_key}")
    return provider_instance


def _image_to_content_block(file_path: str) -> Optional[ContentBlock]:
    if not is_image_file(file_path):
        return None

    try:
        image_bytes = read_binary(file_path)
        with Image.open(BytesIO(image_bytes)) as image:
            image = image.convert("RGB")
            sizes = [4000, 3000, 2000]
            for max_dim in sizes:
                resized = image
                if max(image.size) > max_dim:
                    scale = max_dim / max(image.size)
                    new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
                    resized = image.resize(new_size, Image.Resampling.LANCZOS)

                buffer = BytesIO()
                resized.save(buffer, format="JPEG", quality=90)
                data = buffer.getvalue()
                base64_len = int(len(data) * 4 / 3)
                if base64_len <= BATCH_IMAGE_MAX_BASE64_BYTES:
                    return ContentBlock.image_base64(data, mime_type="image/jpeg")

            logging.warning("Image too large for batch mode after resize: %s", file_path)
            return None
    except Exception as e:
        logging.error("Failed to preprocess image %s: %s", file_path, e)
        return None


def _get_resized_dimensions(file_path: str) -> Optional[tuple]:
    if not os.path.exists(file_path):
        return None
    try:
        image_bytes = read_binary(file_path)
        with Image.open(BytesIO(image_bytes)) as image:
            image = image.convert("RGB")
            sizes = [4000, 3000, 2000]
            for max_dim in sizes:
                resized = image
                if max(image.size) > max_dim:
                    scale = max_dim / max(image.size)
                    new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
                    resized = image.resize(new_size, Image.Resampling.LANCZOS)

                buffer = BytesIO()
                resized.save(buffer, format="JPEG", quality=90)
                data = buffer.getvalue()
                base64_len = int(len(data) * 4 / 3)
                if base64_len <= BATCH_IMAGE_MAX_BASE64_BYTES:
                    return resized.size
    except Exception:
        return None
    return None


def _split_ready_batches(ready_batches: List[tuple], registry: BatchRegistry,
                         batch_type: str, batch_size_limit: int) -> List[tuple]:
    pending = []
    remaining = []
    for batch_id, info in ready_batches:
        if info.get("batch_type") != batch_type:
            remaining.append((batch_id, info))
            continue
        pending.append((batch_id, info))

    pending.sort(key=lambda item: (str(item[1].get("created_at", "")), item[0]))
    if not pending or batch_size_limit <= 0:
        return ready_batches

    for batch_id, info in pending:
        batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))
        items = batch_state.list_by_status("description_saved")
        if len(items) <= batch_size_limit:
            continue

        chunks = [items[i:i + batch_size_limit] for i in range(0, len(items), batch_size_limit)]
        for chunk in chunks:
            new_batch_id = registry.create_batch(batch_type, batch_size_limit)
            new_state = BatchState(new_batch_id, registry.get_batch_dir(new_batch_id))
            for entry in chunk:
                new_state.add_file(
                    entry["file_path"],
                    _build_custom_id(entry["file_path"], new_batch_id),
                    user_description=entry.get("user_description", ""),
                    editorial=bool(entry.get("editorial")),
                    editorial_data=entry.get("editorial_data"),
                    entry_type=entry.get("entry_type", "original"),
                    extra={
                        "edit_tag": entry.get("edit_tag"),
                        "original_file_path": entry.get("original_file_path"),
                        "original_title": entry.get("original_title", ""),
                        "original_description": entry.get("original_description", ""),
                        "original_keywords": entry.get("original_keywords", [])
                    }
                )
                new_state.update_file(entry["file_path"], status="description_saved")
                registry.update_file_batch(entry["file_path"], new_batch_id)
                registry.increment_batch_file_count(new_batch_id)
            registry.set_batch_status(new_batch_id, "ready")

        registry.set_batch_status(batch_id, STATUS_ERROR, error="size_limit_split")

    return list(registry.get_active_batches(status="ready").items())


def _estimate_prompt_tokens(text: str) -> int:
    try:
        import tiktoken  # type: ignore
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, math.ceil(len(text) / 4))


def _estimate_vision_tokens(width: int, height: int) -> int:
    if width <= 0 or height <= 0:
        return 0

    # Resize to fit within 2048x2048 while preserving aspect ratio
    scale = min(2048 / width, 2048 / height, 1.0)
    resized_w = int(width * scale)
    resized_h = int(height * scale)

    # Scale so shortest side is 768px
    shortest = min(resized_w, resized_h)
    if shortest == 0:
        return 0
    scale_to_768 = 768 / shortest
    final_w = int(resized_w * scale_to_768)
    final_h = int(resized_h * scale_to_768)

    tiles_wide = math.ceil(final_w / 512)
    tiles_high = math.ceil(final_h / 512)
    return 85 + (tiles_wide * tiles_high * 170)


def _estimate_batch_cost(provider, items: List[dict]) -> dict:
    prompt_tokens = 0
    vision_tokens = 0
    completion_tokens = 150 * len(items)

    for item in items:
        if item.get("entry_type") == "alternative":
            original_title = _sanitize_text(str(item.get("original_title", "")))
            original_description = _sanitize_text(str(item.get("original_description", "")))
            original_keywords = [_sanitize_text(str(k)) for k in _parse_keywords(item.get("original_keywords", []))]
            prompt = build_alternative_prompt(
                item.get("edit_tag", ""),
                original_title,
                original_description,
                original_keywords,
                bool(item.get("editorial"))
            )
            prompt_tokens += _estimate_prompt_tokens(prompt)
        else:
            user_description = _sanitize_text(str(item.get("user_description", "")))
            prompt = build_batch_prompt(user_description, item.get("editorial_data"))
            prompt_tokens += _estimate_prompt_tokens(prompt)
            dimensions = _get_resized_dimensions(item.get("file_path", ""))
            if dimensions:
                vision_tokens += _estimate_vision_tokens(dimensions[0], dimensions[1])

    total_prompt = prompt_tokens + vision_tokens
    cost = None
    if hasattr(provider, "_calculate_cost"):
        cost = provider._calculate_cost({
            "prompt_tokens": total_prompt,
            "completion_tokens": completion_tokens
        })

    return {
        "estimated_prompt_tokens": prompt_tokens,
        "estimated_vision_tokens": vision_tokens,
        "estimated_completion_tokens": completion_tokens,
        "estimated_input_tokens": total_prompt,
        "estimated_output_tokens": completion_tokens,
        "estimated_cost": cost
    }


def _sanitize_text(value: str) -> str:
    text = value.replace("{", "(").replace("}", ")")
    text = text.replace("\n", " ").replace("\r", " ")
    return " ".join(text.split())


def _classify_send_error(error: Exception) -> str:
    try:
        import openai  # type: ignore
        if isinstance(error, openai.RateLimitError):
            return "rate_limit"
        if isinstance(error, openai.AuthenticationError):
            return "auth"
        if isinstance(error, openai.APIConnectionError):
            return "network"
        if isinstance(error, openai.APIError):
            return "unknown"
    except Exception:
        pass
    message = str(error).lower()
    if "rate limit" in message or "429" in message:
        return "rate_limit"
    if "auth" in message or "api key" in message or "unauthorized" in message:
        return "auth"
    if "size" in message or "too large" in message or "max file" in message:
        return "size"
    if "timeout" in message or "connection" in message or "network" in message:
        return "network"
    return "unknown"


def _get_openai_daily_count(provider, date_key: str) -> Optional[int]:
    try:
        client = getattr(provider, "_get_client", None)
        if client is None:
            return None
        client = client()
        if not hasattr(client, "batches"):
            return None
        list_fn = getattr(client.batches, "list", None)
        if not callable(list_fn):
            return None
        response = list_fn(limit=200)
        items = getattr(response, "data", None) or getattr(response, "items", None) or []
        count = 0
        for item in items:
            created_at = getattr(item, "created_at", None)
            if created_at is None:
                continue
            created = datetime.utcfromtimestamp(created_at).strftime("%Y-%m-%d")
            if created == date_key:
                count += 1
        return count
    except Exception:
        return None


def _build_messages(file_path: str, user_description: str,
                    editorial_data: Optional[Dict[str, str]]) -> Optional[List[Message]]:
    if not os.path.exists(file_path):
        logging.error("File missing for batch message build: %s", file_path)
        return None
    content_block = _image_to_content_block(file_path)
    if not content_block:
        return None
    prompt = build_batch_prompt(_sanitize_text(user_description), editorial_data)
    return [Message.user([ContentBlock.text(prompt), content_block])]


def _find_record_for_path(records: List[Dict[str, str]], file_path: str) -> Optional[Dict[str, str]]:
    normalized = os.path.abspath(file_path).replace("\\", "/")
    for record in records:
        record_path = record.get(COL_PATH, "")
        if record_path:
            if os.path.abspath(record_path).replace("\\", "/") == normalized:
                return record
    return None


def _normalize_path(file_path: str) -> str:
    return os.path.abspath(file_path).replace("\\", "/")


def _build_custom_id(file_path: str, batch_id: str) -> str:
    stem = os.path.splitext(os.path.basename(file_path))[0]
    return f"{stem}_{batch_id}"


def _parse_keywords(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [kw.strip() for kw in value.split(",") if kw.strip()]
    return []


def _get_default_effects() -> List[str]:
    effects = []
    for item in DEFAULT_ALTERNATIVE_EFFECTS.split(","):
        item = item.strip()
        if not item:
            continue
        effects.append(EFFECT_NAME_MAPPING.get(item.lower(), item))
    return effects


def _find_or_create_alternative_batch(registry: BatchRegistry, edit_tag: str) -> str:
    batch_type = f"alternatives{edit_tag}"
    for batch_id, info in registry.get_active_batches(status="collecting").items():
        if info.get("batch_type") == batch_type:
            return batch_id
    return registry.create_batch(batch_type, DEFAULT_ALTERNATIVE_BATCH_SIZE)


def _update_record_with_metadata(record: Dict[str, str], metadata: Dict[str, object]) -> None:
    record[COL_TITLE] = str(metadata.get("title", ""))[:MAX_TITLE_LENGTH]
    record[COL_DESCRIPTION] = str(metadata.get("description", ""))[:MAX_DESCRIPTION_LENGTH]

    keywords = metadata.get("keywords", [])
    if isinstance(keywords, list):
        record[COL_KEYWORDS] = ", ".join([str(k) for k in keywords])
    else:
        record[COL_KEYWORDS] = str(keywords)

    if COL_EDITORIAL in record:
        record[COL_EDITORIAL] = "ano" if metadata.get("editorial") else "ne"

    record[COL_PREP_DATE] = datetime.now().strftime('%d.%m.%Y')

    categories = metadata.get("categories", {})
    if isinstance(categories, dict):
        for photobank, selected in categories.items():
            if not selected:
                continue
            column_name = f"{photobank}{COL_CATEGORY_SUFFIX}"
            if column_name in record:
                if isinstance(selected, list):
                    record[column_name] = ", ".join(selected)
                else:
                    record[column_name] = str(selected)

    for key, value in record.items():
        if key.endswith(COL_STATUS_SUFFIX) and value == STATUS_UNPROCESSED:
            record[key] = STATUS_PREPARED


def _reject_record(record: Dict[str, str]) -> None:
    record[COL_PREP_DATE] = datetime.now().strftime('%d.%m.%Y')
    for key, value in record.items():
        if key.endswith(COL_STATUS_SUFFIX) and value == STATUS_UNPROCESSED:
            record[key] = STATUS_REJECTED


def _save_metadata_to_csv(media_csv: str, file_path: str,
                          metadata: Dict[str, object],
                          editorial_fallback: bool) -> bool:
    records = load_csv(media_csv)
    record = _find_record_for_path(records, file_path)
    if not record:
        return False

    if "editorial" not in metadata:
        metadata["editorial"] = bool(editorial_fallback)

    _update_record_with_metadata(record, metadata)
    save_csv_with_backup(records, media_csv)
    return True


def _process_batch_results(batch_state: BatchState, results: List[Dict[str, object]],
                           media_csv: str) -> List[str]:
    failed_custom_ids: List[str] = []
    for result in tqdm(results, desc="Saving metadata to CSV", unit="file"):
        custom_id = result.get("custom_id")
        payload = result.get("payload")
        error = result.get("error")

        if not custom_id:
            continue

        if error or payload is None:
            batch_state.update_file_by_custom_id(custom_id, status="batch_failed", error=error or "No payload")
            failed_custom_ids.append(custom_id)
            continue

        try:
            metadata = json.loads(payload)
        except Exception as e:
            batch_state.update_file_by_custom_id(custom_id, status="batch_failed", error=str(e))
            failed_custom_ids.append(custom_id)
            continue

        file_entry = next((item for item in batch_state.all_files() if item["custom_id"] == custom_id), None)
        if not file_entry:
            continue

        if not os.path.exists(file_entry["file_path"]):
            batch_state.update_file_by_custom_id(custom_id, status="batch_failed", error="file_not_found")
            failed_custom_ids.append(custom_id)
            continue

        saved = _save_metadata_to_csv(media_csv, file_entry["file_path"], metadata, bool(file_entry.get("editorial")))
        if not saved:
            batch_state.update_file_by_custom_id(custom_id, status="batch_failed", error="Record not found")
            failed_custom_ids.append(custom_id)
            continue

        batch_state.update_file_by_custom_id(custom_id, status="saved_to_csv", result=metadata)

    return failed_custom_ids


def _generate_alternatives_for_file(registry: BatchRegistry, media_csv: str,
                                    original_path: str, original_metadata: Dict[str, object]) -> None:
    normalized = _normalize_path(original_path)
    if registry.data.get("alternatives_generated", {}).get(normalized):
        return

    records = load_csv(media_csv)
    original_record = _find_record_for_path(records, original_path)
    if not original_record:
        logging.warning("Original record not found for alternatives: %s", original_path)
        return

    effects = _get_default_effects()
    generator = AlternativeGenerator(enabled_alternatives=effects)
    target_dir, edited_dir = get_alternative_output_dirs(original_path)
    alternative_files = generator.generate_all_versions(original_path, target_dir, edited_dir)

    original_keywords = _parse_keywords(original_metadata.get("keywords", []))
    editorial_flag = bool(original_metadata.get("editorial"))

    for alt_info in alternative_files:
        if alt_info.get("type") != "edit":
            continue

        edit_tag = alt_info.get("edit")
        alt_path = alt_info.get("path")
        if not alt_path:
            continue

        ext = os.path.splitext(alt_path)[1].lower()
        if ext not in CSV_ALLOWED_EXTENSIONS:
            continue

        alt_filename = os.path.basename(alt_path)
        existing_record = _find_record_for_path(records, alt_path)
        if existing_record is None:
            alt_record = original_record.copy()
        else:
            alt_record = existing_record

        alt_record[COL_FILE] = alt_filename
        alt_record[COL_PATH] = alt_path
        alt_record[COL_ORIGINAL] = ORIGINAL_NO

        if edit_tag == "_sharpen":
            alt_record[COL_TITLE] = str(original_metadata.get("title", ""))[:MAX_TITLE_LENGTH]
            alt_record[COL_DESCRIPTION] = str(original_metadata.get("description", ""))[:MAX_DESCRIPTION_LENGTH]
            alt_record[COL_KEYWORDS] = ", ".join(original_keywords)
            alt_record[COL_PREP_DATE] = datetime.now().strftime('%d.%m.%Y')
            for key in alt_record.keys():
                if key.endswith(COL_STATUS_SUFFIX):
                    alt_record[key] = STATUS_BACKUP
        else:
            alt_record[COL_TITLE] = ""
            alt_record[COL_DESCRIPTION] = ""
            alt_record[COL_KEYWORDS] = ""
            alt_record[COL_PREP_DATE] = ""
            for key, value in alt_record.items():
                if key.endswith(COL_STATUS_SUFFIX):
                    alt_record[key] = STATUS_UNPROCESSED

            batch_id = _find_or_create_alternative_batch(registry, edit_tag)
            batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))
            custom_id = _build_custom_id(alt_path, batch_id)
            batch_state.add_file(
                alt_path,
                custom_id,
                user_description="",
                editorial=editorial_flag,
                editorial_data=None,
                entry_type="alternative",
                extra={
                    "edit_tag": edit_tag,
                    "original_file_path": original_path,
                    "original_title": original_metadata.get("title", ""),
                    "original_description": original_metadata.get("description", ""),
                    "original_keywords": original_keywords
                }
            )
            batch_state.update_file(alt_path, status="description_saved")
            registry.register_file(alt_path, batch_id)
            registry.increment_batch_file_count(batch_id)

            batch_info = registry.get_active_batches().get(batch_id, {})
            if batch_info.get("file_count", 0) >= DEFAULT_ALTERNATIVE_BATCH_SIZE:
                registry.set_batch_status(batch_id, "ready")

        if existing_record is None:
            records.append(alt_record)

    save_csv_with_backup(records, media_csv)
    registry.data["alternatives_generated"][normalized] = datetime.utcnow().isoformat()
    registry.save()


def _queue_alternatives_from_batch(batch_state: BatchState, registry: BatchRegistry, media_csv: str) -> None:
    for item in batch_state.all_files():
        if item.get("entry_type") and item.get("entry_type") != "original":
            continue
        if item.get("status") != "saved_to_csv":
            continue
        original_path = item.get("file_path")
        if not original_path:
            continue
        original_metadata = item.get("result") or {}
        _generate_alternatives_for_file(registry, media_csv, original_path, original_metadata)


def _finalize_alternative_batches(registry: BatchRegistry) -> None:
    for batch_id, info in registry.get_active_batches(status="collecting").items():
        batch_type = info.get("batch_type", "")
        if not batch_type.startswith("alternatives"):
            continue
        if int(info.get("file_count", 0)) > 0:
            registry.set_batch_status(batch_id, "ready")


def _log_batch_cost(batch_id: str, provider, batch_job) -> None:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for response in batch_job.results or []:
        usage = response.usage or {}
        totals["prompt_tokens"] += int(usage.get("prompt_tokens", 0))
        totals["completion_tokens"] += int(usage.get("completion_tokens", 0))
        totals["total_tokens"] += int(usage.get("total_tokens", 0))

    cost = None
    if hasattr(provider, "_calculate_cost"):
        try:
            cost = provider._calculate_cost(totals)
        except Exception:
            cost = None

    log_data = read_json(BATCH_COST_LOG, default={})
    existing = log_data.get(batch_id, {})
    existing.update({
        "model": getattr(provider, "model_name", "unknown"),
        "prompt_tokens": totals["prompt_tokens"],
        "completion_tokens": totals["completion_tokens"],
        "total_tokens": totals["total_tokens"],
        "actual_cost": cost,
        "logged_at": datetime.utcnow().isoformat()
    })
    log_data[batch_id] = existing
    write_json(BATCH_COST_LOG, log_data)


def _sync_retry_failed_items(provider, batch_state: BatchState, failed_custom_ids: List[str],
                             media_csv: str, registry: Optional[BatchRegistry] = None) -> None:
    for custom_id in failed_custom_ids:
        entry = next((item for item in batch_state.all_files() if item["custom_id"] == custom_id), None)
        if not entry:
            continue
        attempts = int(entry.get("sync_attempts", 0))
        if attempts >= 3:
            batch_state.update_file_by_custom_id(custom_id, status=STATUS_ERROR, error="sync_retry_exhausted")
            continue

        for attempt in range(attempts + 1, 4):
            try:
                if entry.get("entry_type") == "alternative":
                    original_title = _sanitize_text(str(entry.get("original_title", "")))
                    original_description = _sanitize_text(str(entry.get("original_description", "")))
                    original_keywords = [_sanitize_text(str(k)) for k in _parse_keywords(entry.get("original_keywords", []))]
                    prompt = build_alternative_prompt(
                        entry.get("edit_tag", ""),
                        original_title,
                        original_description,
                        original_keywords,
                        bool(entry.get("editorial"))
                    )
                    messages = [Message.user_text(prompt)]
                else:
                    messages = _build_messages(entry["file_path"], entry.get("user_description", ""),
                                               entry.get("editorial_data"))
                if not messages:
                    if os.path.exists(entry.get("file_path", "")) and is_image_file(entry.get("file_path", "")):
                        batch_state.update_file_by_custom_id(
                            custom_id,
                            status="skipped_large",
                            error="image_too_large"
                        )
                        if registry:
                            registry.unregister_file(entry.get("file_path", ""))
                    else:
                        batch_state.update_file_by_custom_id(custom_id, status=STATUS_ERROR, error="sync_missing_file")
                    break

                response = provider.generate_text(messages)
                metadata = json.loads(response.content)
                saved = _save_metadata_to_csv(media_csv, entry["file_path"], metadata, bool(entry.get("editorial")))
                if not saved:
                    batch_state.update_file_by_custom_id(custom_id, status=STATUS_ERROR, error="Record not found")
                    break

                batch_state.update_file_by_custom_id(custom_id, status="saved_to_csv", result=metadata,
                                                     sync_attempts=attempt)
                break
            except Exception as e:
                batch_state.update_file_by_custom_id(custom_id, sync_attempts=attempt, error=str(e))
                if attempt >= 3:
                    batch_state.update_file_by_custom_id(custom_id, status=STATUS_ERROR, error="sync_retry_exhausted")


def _collect_descriptions(registry: BatchRegistry, batch_size: int, media_csv: str,
                          model_key: str) -> None:
    records = load_media_records(media_csv)
    unprocessed = find_unprocessed_records(records)
    active_files = set(registry.data.get("file_registry", {}).keys())

    collecting_batches = registry.get_active_batches(status="collecting")
    total_limit = max(1, int(batch_size))
    originals_limit = DEFAULT_BATCH_VISION_SIZE
    if collecting_batches:
        batch_id = next(iter(collecting_batches.keys()))
    else:
        batch_id = registry.create_batch("originals", originals_limit)

    batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))
    provider = _create_batch_provider(model_key)

    candidates = []
    for record in unprocessed:
        file_path = record.get(COL_PATH, "")
        normalized = _normalize_path(file_path) if file_path else ""
        if not file_path or normalized in active_files:
            continue
        candidates.append(record)

    candidates = candidates[:total_limit]
    total = len(candidates)
    for index, record in enumerate(tqdm(candidates, desc="Collecting descriptions", unit="file"), start=1):
        file_path = record.get(COL_PATH, "")
        normalized = _normalize_path(file_path) if file_path else ""

        estimate = _estimate_batch_cost(provider, batch_state.list_by_status("description_saved"))
        cost = estimate.get("estimated_cost")
        cost_text = f"${cost:.2f}" if isinstance(cost, (int, float)) else "N/A"
        progress_text = f"Progress: {index}/{total} | Est: {cost_text}"
        response = collect_batch_description(file_path, DEFAULT_BATCH_DESCRIPTION_MIN_LENGTH, progress_text=progress_text)
        action = response.get("action")

        if action == "skip":
            continue
        if action == "reject":
            record_map = load_csv(media_csv)
            target_record = _find_record_for_path(record_map, file_path)
            if target_record:
                _reject_record(target_record)
                save_csv_with_backup(record_map, media_csv)
            continue
        if action != "save":
            continue

        custom_id = _build_custom_id(file_path, batch_id)
        batch_state.add_file(
            file_path,
            custom_id,
            user_description=response.get("description", ""),
            editorial=bool(response.get("editorial")),
            editorial_data=response.get("editorial_data")
        )
        batch_state.update_file(file_path, status="description_saved")
        registry.register_file(file_path, batch_id)
        active_files.add(normalized)
        registry.increment_batch_file_count(batch_id)

        batch_info = registry.get_active_batches().get(batch_id, {})
        if batch_info.get("file_count", 0) >= originals_limit:
            registry.set_batch_status(batch_id, "ready")
            batch_id = registry.create_batch("originals", originals_limit)
            batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))


def _send_ready_batches(registry: BatchRegistry, media_csv: str, model_key: str) -> None:
    provider = _create_batch_provider(model_key)
    ready_batches = list(registry.get_active_batches(status="ready").items())
    ready_batches.sort(key=lambda item: (
        1 if str(item[1].get("batch_type", "")).startswith("alternatives") else 0,
        str(item[1].get("created_at", "")),
        item[0]
    ))
    ready_batches = _split_ready_batches(ready_batches, registry, "originals", DEFAULT_BATCH_VISION_SIZE)
    ready_batches = list(registry.get_active_batches(status="ready").items())
    ready_batches.sort(key=lambda item: (
        1 if str(item[1].get("batch_type", "")).startswith("alternatives") else 0,
        str(item[1].get("created_at", "")),
        item[0]
    ))
    date_key = datetime.utcnow().strftime("%Y-%m-%d")
    daily_count = _get_openai_daily_count(provider, date_key)
    if daily_count is None:
        daily_count = registry.get_daily_count(date_key)

    if daily_count >= DEFAULT_DAILY_BATCH_LIMIT:
        logging.warning("Daily batch limit reached (%s). Skipping send phase.", DEFAULT_DAILY_BATCH_LIMIT)
        return

    for batch_id, info in tqdm(ready_batches, desc="Sending batches", unit="batch"):
        if daily_count + 1 > DEFAULT_DAILY_BATCH_LIMIT:
            logging.warning("Daily batch limit reached while sending. Remaining batches deferred.")
            break

        batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))
        items = batch_state.list_by_status("description_saved")

        messages_list = []
        custom_ids = []
        send_items = []
        for item in items:
            if not os.path.exists(item.get("file_path", "")):
                batch_state.update_file(item["file_path"], status=STATUS_ERROR, error="file_not_found")
                continue
            if item.get("entry_type") == "alternative":
                original_title = _sanitize_text(str(item.get("original_title", "")))
                original_description = _sanitize_text(str(item.get("original_description", "")))
                original_keywords = [_sanitize_text(str(k)) for k in _parse_keywords(item.get("original_keywords", []))]
                prompt = build_alternative_prompt(
                    item.get("edit_tag", ""),
                    original_title,
                    original_description,
                    original_keywords,
                    bool(item.get("editorial"))
                )
                messages = [Message.user_text(prompt)]
            else:
                content_block = _image_to_content_block(item["file_path"])
                if not content_block:
                    batch_state.update_file(item["file_path"], status="skipped_large", error="image_too_large")
                    registry.unregister_file(item["file_path"])
                    continue
                prompt = build_batch_prompt(_sanitize_text(item.get("user_description", "")),
                                            item.get("editorial_data"))
                messages = [Message.user([ContentBlock.text(prompt), content_block])]
            if not messages:
                batch_state.update_file(item["file_path"], status=STATUS_ERROR, error="Unsupported file type")
                continue
            messages_list.append(messages)
            custom_ids.append(item["custom_id"])
            send_items.append(item)

        if not messages_list:
            registry.set_batch_status(batch_id, STATUS_ERROR, error="empty_batch")
            continue

        estimate = _estimate_batch_cost(provider, send_items)
        cost_log = read_json(BATCH_COST_LOG, default={})
        existing = cost_log.get(batch_id, {})
        existing.update({
            "model": getattr(provider, "model_name", "unknown"),
            "estimated_prompt_tokens": estimate["estimated_prompt_tokens"],
            "estimated_vision_tokens": estimate["estimated_vision_tokens"],
            "estimated_completion_tokens": estimate["estimated_completion_tokens"],
            "estimated_input_tokens": estimate["estimated_input_tokens"],
            "estimated_output_tokens": estimate["estimated_output_tokens"],
            "estimated_cost": estimate["estimated_cost"],
            "estimated_at": datetime.utcnow().isoformat()
        })
        cost_log[batch_id] = existing
        write_json(BATCH_COST_LOG, cost_log)
        if estimate["estimated_cost"] is not None:
            logging.info("Estimated batch cost for %s: $%.6f", batch_id, estimate["estimated_cost"])

        attempt = 0
        while True:
            try:
                batch_job = provider.create_batch_job(messages_list, custom_ids)
                registry.set_batch_status(batch_id, "sent", openai_batch_id=batch_job.job_id)
                for item in items:
                    batch_state.update_file(item["file_path"], status="batch_sent")
                daily_count += 1
                registry.increment_daily_count(date_key, 1)
                break
            except Exception as e:
                attempt += 1
                error_type = _classify_send_error(e)
                logging.error("Failed to send batch %s: %s", batch_id, e)

                if error_type == "network" and attempt < 3:
                    backoff = min(2 ** attempt, 10)
                    logging.warning("Retrying batch send in %s seconds...", backoff)
                    import time
                    time.sleep(backoff)
                    continue

                if error_type == "rate_limit":
                    logging.warning("Rate limit reached. Deferring remaining batches.")
                    return

                if error_type == "auth":
                    registry.set_batch_status(batch_id, STATUS_ERROR, error="authentication_failed")
                    return

                if error_type == "size" and len(items) > 1:
                    logging.warning("Splitting batch %s due to size limit.", batch_id)
                    mid = len(items) // 2
                    split_groups = [items[:mid], items[mid:]]
                    batch_type = info.get("batch_type", "originals")
                    for group in split_groups:
                        new_batch_id = registry.create_batch(batch_type, info.get("batch_size_limit", len(group)))
                        new_state = BatchState(new_batch_id, registry.get_batch_dir(new_batch_id))
                        for entry in group:
                            new_state.add_file(
                                entry["file_path"],
                                _build_custom_id(entry["file_path"], new_batch_id),
                                user_description=entry.get("user_description", ""),
                                editorial=bool(entry.get("editorial")),
                                editorial_data=entry.get("editorial_data"),
                                entry_type=entry.get("entry_type", "original"),
                                extra={
                                    "edit_tag": entry.get("edit_tag"),
                                    "original_file_path": entry.get("original_file_path"),
                                    "original_title": entry.get("original_title", ""),
                                    "original_description": entry.get("original_description", ""),
                                    "original_keywords": entry.get("original_keywords", [])
                                }
                            )
                            new_state.update_file(entry["file_path"], status="description_saved")
                            registry.update_file_batch(entry["file_path"], new_batch_id)
                            registry.increment_batch_file_count(new_batch_id)
                        registry.set_batch_status(new_batch_id, "ready")

                    registry.set_batch_status(batch_id, STATUS_ERROR, error="size_limit_split")
                    break

                registry.set_batch_status(batch_id, STATUS_ERROR, error=str(e))
                break


def _retrieve_completed_batches(registry: BatchRegistry, media_csv: str,
                                model_key: str) -> None:
    provider = _create_batch_provider(model_key)
    sent_batches = list(registry.get_active_batches(status="sent").items())
    sent_batches.sort(key=lambda item: (
        1 if str(item[1].get("batch_type", "")).startswith("alternatives") else 0,
        str(item[1].get("created_at", "")),
        item[0]
    ))

    def _retrieve_group(group: List[tuple]) -> None:
        batch_jobs = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_map = {}
            for batch_id, info in group:
                openai_batch_id = info.get("openai_batch_id")
                if not openai_batch_id:
                    continue
                future_map[executor.submit(provider.get_batch_job, openai_batch_id)] = (batch_id, openai_batch_id)

            for future in tqdm(as_completed(future_map), desc="Retrieving batches", unit="batch", total=len(future_map)):
                batch_id, _ = future_map[future]
                try:
                    batch_jobs[batch_id] = future.result()
                except Exception as e:
                    logging.error("Failed to retrieve batch %s: %s", batch_id, e)

        for batch_id, batch_job in batch_jobs.items():
            status = batch_job.status

            if status != "completed":
                if status in ["failed", "expired", "cancelled"]:
                    registry.set_batch_status(batch_id, STATUS_ERROR, error=status)
                continue

            _log_batch_cost(batch_id, provider, batch_job)

            results = []
            for response in batch_job.results or []:
                custom_id = response.metadata.get("custom_id") if response.metadata else None
                results.append({
                    "custom_id": custom_id,
                    "payload": response.content,
                    "error": None
                })

            batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))
            failed_custom_ids = _process_batch_results(batch_state, results, media_csv)

            result_ids = {item.get("custom_id") for item in results if item.get("custom_id")}
            missing = []
            for item in batch_state.all_files():
                if item.get("status") == "batch_sent" and item.get("custom_id") not in result_ids:
                    batch_state.update_file(item["file_path"], status="batch_failed", error="missing_result")
                    missing.append(item.get("custom_id"))

            failed_custom_ids.extend([cid for cid in missing if cid])
            if failed_custom_ids:
                _sync_retry_failed_items(provider, batch_state, failed_custom_ids, media_csv, registry=registry)
                _queue_alternatives_from_batch(batch_state, registry, media_csv)
                _finalize_alternative_batches(registry)
                registry.complete_batch(batch_id)

    originals = [item for item in sent_batches if not str(item[1].get("batch_type", "")).startswith("alternatives")]
    alternatives = [item for item in sent_batches if str(item[1].get("batch_type", "")).startswith("alternatives")]
    _retrieve_group(originals)
    _retrieve_group(alternatives)


def run_batch_mode(media_csv: str, batch_size: int, wait_timeout: int,
                   poll_interval: int = DEFAULT_BATCH_POLL_INTERVAL) -> None:
    """
    Run batch mode orchestration.

    Args:
        media_csv: Path to PhotoMedia.csv
        batch_size: Files per batch
        wait_timeout: Optional wait after sending (seconds)
        poll_interval: Poll interval for batch status
    """
    registry = BatchRegistry()
    registry.cleanup_completed()

    model_key = _get_default_model_key()
    logging.info("=== BATCH MODE STARTED ===")
    logging.info("Batch mode using model: %s", model_key)
    active = registry.get_active_batches()
    if active:
        status_counts = {}
        for info in active.values():
            status = info.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        logging.info("Active batches by status: %s", status_counts)
    else:
        logging.info("No active batches. Starting fresh collection.")

    _retrieve_completed_batches(registry, media_csv, model_key)
    _send_ready_batches(registry, media_csv, model_key)
    _collect_descriptions(registry, batch_size, media_csv, model_key)

    import time
    if wait_timeout == 0:
        while True:
            _retrieve_completed_batches(registry, media_csv, model_key)
            if not registry.get_active_batches(status="sent"):
                break
            time.sleep(poll_interval)
    elif wait_timeout > 0:
        start = time.time()
        while time.time() - start < wait_timeout:
            _retrieve_completed_batches(registry, media_csv, model_key)
            time.sleep(poll_interval)
        logging.info("Batch wait timeout reached (%s seconds).", wait_timeout)


def check_batch_statuses() -> List[str]:
    """
    Return human-readable batch status lines.
    """
    registry = BatchRegistry()
    model_key = _get_default_model_key()
    provider = None
    lines = []

    for batch_id, info in registry.get_active_batches().items():
        status = info.get("status", "unknown")
        openai_batch_id = info.get("openai_batch_id")
        detail = ""
        if openai_batch_id:
            if provider is None:
                try:
                    provider = _create_batch_provider(model_key)
                except Exception as e:
                    detail = f" (provider error: {e})"
            if provider:
                try:
                    batch_job = provider.get_batch_job(openai_batch_id)
                    status = batch_job.status
                except Exception as e:
                    detail = f" (status error: {e})"
        lines.append(f"{batch_id}: {status}{detail}")

    if not lines:
        lines.append("No active batches.")

    return lines
