"""
Batch mode description dialog for collecting free-form user descriptions.
"""
from __future__ import annotations

import os
import logging
import subprocess
import tkinter as tk
from io import BytesIO
from tkinter import ttk, messagebox
from typing import Optional, Dict

from PIL import Image, ImageTk

from shared.file_operations import read_binary
from givephotobankreadymediafileslib.editorial_dialog import (
    extract_editorial_metadata_from_exif,
    get_editorial_metadata
)
from givephotobankreadymediafileslib.media_helper import is_video_file


class BatchDescriptionDialog:
    """Collects user description and optional editorial metadata."""

    def __init__(self, parent: tk.Tk, file_path: str, min_length: int, progress_text: str = ""):
        self.parent = parent
        self.file_path = file_path
        self.min_length = min_length
        self.progress_text = progress_text
        self.result: Optional[Dict[str, object]] = None
        self._image = None
        self._build_ui()

    def _build_ui(self) -> None:
        title_suffix = f" - {self.progress_text}" if self.progress_text else ""
        self.parent.title(f"[BATCH MODE] Description Collection{title_suffix}")
        self.parent.geometry("1200x800")
        self.parent.minsize(1000, 700)

        main_frame = ttk.Frame(self.parent, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text=self.file_path, wraplength=1000).pack(anchor=tk.W)
        if self.progress_text:
            ttk.Label(top_frame, text=self.progress_text).pack(anchor=tk.W)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Media preview
        preview_frame = ttk.Frame(content_frame)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.preview_label = ttk.Label(preview_frame, text="Loading preview...")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # Description input
        form_frame = ttk.Frame(content_frame)
        form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(10, 0))

        ttk.Label(form_frame, text="User description (min length required)").pack(anchor=tk.W)
        self.desc_text = tk.Text(form_frame, height=18, width=50, wrap=tk.WORD)
        self.desc_text.pack(fill=tk.BOTH, expand=True)
        self.desc_text.bind("<KeyRelease>", self._update_counter)

        self.counter_label = ttk.Label(form_frame, text=f"0 / {self.min_length} characters")
        self.counter_label.pack(anchor=tk.W, pady=(4, 8))

        self.editorial_var = tk.BooleanVar(value=False)
        self.editorial_check = ttk.Checkbutton(
            form_frame,
            text="Editorial mode (requires city/country/date)",
            variable=self.editorial_var
        )
        self.editorial_check.pack(anchor=tk.W, pady=(2, 8))

        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.pack(fill=tk.X, pady=(8, 0))

        self.save_button = ttk.Button(buttons_frame, text="Save", command=self._on_save)
        self.save_button.pack(side=tk.LEFT, padx=(0, 6))
        self.save_button.state(["disabled"])
        ttk.Button(buttons_frame, text="Reject", command=self._on_reject).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(buttons_frame, text="Skip", command=self._on_skip).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(buttons_frame, text="Show in Explorer", command=self._on_open_explorer).pack(side=tk.RIGHT)

        self.parent.protocol("WM_DELETE_WINDOW", self._on_cancel)

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(8, 0))
        self.status_label = ttk.Label(status_frame, text=self.progress_text or "")
        self.status_label.pack(anchor=tk.W)

        self._load_preview()

    def _load_preview(self) -> None:
        if not os.path.exists(self.file_path):
            self.preview_label.configure(text="File not found")
            return

        if is_video_file(self.file_path):
            self.preview_label.configure(text="Video preview not available in batch mode.")
            return

        try:
            image_bytes = read_binary(self.file_path)
            with Image.open(BytesIO(image_bytes)) as image:
                preview = image.copy()
            max_w = 700
            max_h = 700
            preview.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            self._image = ImageTk.PhotoImage(preview)
            self.preview_label.configure(image=self._image, text="")
        except Exception as e:
            logging.error("Failed to load preview: %s", e)
            self.preview_label.configure(text=f"Preview error: {e}")

    def _update_counter(self, event=None) -> None:
        length = len(self._get_description())
        self.counter_label.configure(text=f"{length} / {self.min_length} characters")
        if length >= self.min_length:
            self.save_button.state(["!disabled"])
        else:
            self.save_button.state(["disabled"])

    def _get_description(self) -> str:
        return self.desc_text.get("1.0", tk.END).strip()

    def _on_save(self) -> None:
        description = self._get_description()
        if len(description) < self.min_length:
            messagebox.showwarning(
                "Description too short",
                f"Please enter at least {self.min_length} characters."
            )
            return

        editorial_data = None
        if self.editorial_var.get():
            extracted, missing = extract_editorial_metadata_from_exif(self.file_path)
            editorial_data = get_editorial_metadata(self.parent, missing, extracted)
            if editorial_data is None:
                return

        self.result = {
            "action": "save",
            "description": description,
            "editorial": bool(self.editorial_var.get()),
            "editorial_data": editorial_data
        }
        self.parent.destroy()

    def _on_reject(self) -> None:
        confirm = messagebox.askyesno("Reject File", "Reject this file?")
        if not confirm:
            return
        self.result = {"action": "reject"}
        self.parent.destroy()

    def _on_skip(self) -> None:
        self.result = {"action": "skip"}
        self.parent.destroy()

    def _on_cancel(self) -> None:
        self.result = {"action": "skip"}
        self.parent.destroy()

    def _on_open_explorer(self) -> None:
        if not os.path.exists(self.file_path):
            messagebox.showwarning("Missing file", "File not found on disk.")
            return
        try:
            if os.name == "nt":
                subprocess.run(["explorer", "/select,", os.path.normpath(self.file_path)])
            else:
                directory = os.path.dirname(self.file_path)
                subprocess.run(["xdg-open", directory])
        except Exception as e:
            logging.error("Failed to open explorer: %s", e)
            messagebox.showerror("Error", f"Failed to open file location:\n{e}")


def collect_batch_description(file_path: str, min_length: int, progress_text: str = "") -> Dict[str, object]:
    """Show the dialog and return user result dict."""
    root = tk.Tk()
    dialog = BatchDescriptionDialog(root, file_path, min_length, progress_text=progress_text)
    root.mainloop()
    return dialog.result or {"action": "skip"}
