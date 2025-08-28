"""
Media viewer with metadata generation interface for photobank ready media files.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox, Text, Listbox, SINGLE
from PIL import Image, ImageTk
import pygame
from typing import Optional, Callable, List, Dict, Any
import threading
import time

from givephotobankreadymediafileslib.constants import (
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, MAX_TITLE_LENGTH, 
    MAX_DESCRIPTION_LENGTH, MAX_KEYWORDS_COUNT
)
from givephotobankreadymediafileslib.media_helper import is_video_file, is_image_file
from shared.config import get_config


class MetadataViewer:
    def __init__(self, root: tk.Tk, media_file_path: str):
        self.root = root
        self.root.title("Photobank Metadata Generator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Initialize configuration
        self.config = get_config()
        
        # Initialize pygame for video playback (defer for performance)
        self.pygame_initialized = False
        
        # Current media info
        self.media_file_path = media_file_path
        self.current_image: Optional[ImageTk.PhotoImage] = None
        self.original_image_size: Optional[tuple] = None
        self.video_surface = None
        self.video_playing = False
        self.video_paused = False
        
        # AI model selection
        self.available_ai_models = self.config.get_available_ai_models()
        default_provider, default_model = self.config.get_default_ai_model()
        self.selected_ai_model = f"{default_provider}/{default_model}"
        
        # Metadata fields
        self.metadata = {
            'title': '',
            'description': '',
            'keywords': [],
            'categories': {},
            'editorial': False
        }
        
        # Available photobank categories (will be loaded from CSV)
        self.photobank_categories = {
            'Shutterstock': [],
            'Adobe': [],
            'Alamy': [],
            'Dreamstime': []
        }
        
        self.setup_ui()
        self.load_media_file(media_file_path)
        
        # Bind resize event for responsive image display
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def setup_ui(self):
        """Setup the user interface with media viewer and metadata fields."""
        # Main container with two panes
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left pane - Media viewer
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)
        self.setup_media_viewer(left_frame)
        
        # Right pane - Metadata fields
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        self.setup_metadata_panel(right_frame)

    def setup_media_viewer(self, parent):
        """Setup the media viewing area."""
        # Media display frame
        self.media_frame = ttk.Frame(parent)
        self.media_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for image/video display
        self.canvas = tk.Canvas(self.media_frame, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Video control frame
        self.video_controls = ttk.Frame(parent)
        self.video_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Video controls (initially hidden)
        self.play_button = ttk.Button(self.video_controls, text="Play", command=self.toggle_video)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.video_progress = ttk.Progressbar(self.video_controls, mode='determinate')
        self.video_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # File info label
        self.file_info_label = ttk.Label(parent, text="", background='lightgray')
        self.file_info_label.pack(fill=tk.X, padx=5, pady=2)

    def setup_metadata_panel(self, parent):
        """Setup the metadata editing panel."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Metadata fields
        self.setup_ai_model_section(scrollable_frame)
        self.setup_title_section(scrollable_frame)
        self.setup_description_section(scrollable_frame)
        self.setup_keywords_section(scrollable_frame)
        self.setup_categories_section(scrollable_frame)
        self.setup_editorial_section(scrollable_frame)
        self.setup_action_buttons(scrollable_frame)

    def setup_ai_model_section(self, parent):
        """Setup AI model selection section."""
        ai_frame = ttk.LabelFrame(parent, text="AI Model Selection", padding=10)
        ai_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model selection
        model_label = ttk.Label(ai_frame, text="AI Model:")
        model_label.pack(anchor=tk.W)
        
        self.ai_model_var = tk.StringVar(value=self.selected_ai_model)
        
        # Create list of display names for dropdown
        model_options = []
        self.model_mapping = {}
        
        for model_info in self.available_ai_models:
            display_name = model_info["display_name"]
            model_key = model_info["key"]
            model_options.append(display_name)
            self.model_mapping[display_name] = model_key
        
        if not model_options:
            model_options = ["No AI models available (check API keys)"]
            self.model_mapping[model_options[0]] = ""
        
        self.ai_model_combo = ttk.Combobox(
            ai_frame, 
            textvariable=self.ai_model_var, 
            values=model_options,
            state="readonly",
            width=50
        )
        self.ai_model_combo.pack(fill=tk.X, pady=(0, 5))
        
        # Set current selection
        if self.selected_ai_model in self.model_mapping.values():
            for display_name, key in self.model_mapping.items():
                if key == self.selected_ai_model:
                    self.ai_model_var.set(display_name)
                    break
        
        # Bind selection change
        self.ai_model_combo.bind('<<ComboboxSelected>>', self.on_ai_model_changed)
        
        # Model info display
        self.model_info_label = ttk.Label(ai_frame, text="", foreground="gray")
        self.model_info_label.pack(anchor=tk.W)
        
        # Update model info
        self.update_model_info()

    def setup_title_section(self, parent):
        """Setup title input section."""
        title_frame = ttk.LabelFrame(parent, text="Název", padding=10)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(title_frame, textvariable=self.title_var)
        self.title_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Character counter
        self.title_counter = ttk.Label(title_frame, text=f"0/{MAX_TITLE_LENGTH}")
        self.title_counter.pack(anchor=tk.E)
        
        self.title_var.trace('w', self.update_title_counter)
        
        # Generate button
        ttk.Button(title_frame, text="Generovat název", 
                  command=self.generate_title).pack(fill=tk.X, pady=(5, 0))

    def setup_description_section(self, parent):
        """Setup description input section."""
        desc_frame = ttk.LabelFrame(parent, text="Popis", padding=10)
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.description_text = Text(desc_frame, height=4, wrap=tk.WORD)
        self.description_text.pack(fill=tk.X, pady=(0, 5))
        
        # Character counter
        self.desc_counter = ttk.Label(desc_frame, text=f"0/{MAX_DESCRIPTION_LENGTH}")
        self.desc_counter.pack(anchor=tk.E)
        
        self.description_text.bind('<KeyRelease>', self.update_description_counter)
        
        # Generate button
        ttk.Button(desc_frame, text="Generovat popis", 
                  command=self.generate_description).pack(fill=tk.X, pady=(5, 0))

    def setup_keywords_section(self, parent):
        """Setup keywords input section."""
        keywords_frame = ttk.LabelFrame(parent, text="Klíčová slova", padding=10)
        keywords_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Keywords listbox with scrollbar
        keywords_list_frame = ttk.Frame(keywords_frame)
        keywords_list_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.keywords_listbox = Listbox(keywords_list_frame, height=6, selectmode=SINGLE)
        keywords_scrollbar = ttk.Scrollbar(keywords_list_frame, orient="vertical", 
                                         command=self.keywords_listbox.yview)
        self.keywords_listbox.configure(yscrollcommand=keywords_scrollbar.set)
        
        self.keywords_listbox.pack(side="left", fill="both", expand=True)
        keywords_scrollbar.pack(side="right", fill="y")
        
        # Keyword input and buttons
        keyword_input_frame = ttk.Frame(keywords_frame)
        keyword_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(keyword_input_frame, textvariable=self.keyword_var)
        self.keyword_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(keyword_input_frame, text="Přidat", 
                  command=self.add_keyword).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(keyword_input_frame, text="Odstranit", 
                  command=self.remove_keyword).pack(side=tk.LEFT)
        
        # Keyword counter
        self.keywords_counter = ttk.Label(keywords_frame, text=f"0/{MAX_KEYWORDS_COUNT}")
        self.keywords_counter.pack(anchor=tk.E)
        
        # Generate button
        ttk.Button(keywords_frame, text="Generovat klíčová slova", 
                  command=self.generate_keywords).pack(fill=tk.X, pady=(5, 0))
        
        # Bind Enter key to add keyword
        self.keyword_entry.bind('<Return>', lambda e: self.add_keyword())

    def setup_categories_section(self, parent):
        """Setup photobank categories section."""
        categories_frame = ttk.LabelFrame(parent, text="Kategorie pro fotobanky", padding=10)
        categories_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.category_vars = {}
        self.category_combos = {}
        
        for photobank in self.photobank_categories.keys():
            bank_frame = ttk.Frame(categories_frame)
            bank_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(bank_frame, text=f"{photobank}:", width=12).pack(side=tk.LEFT)
            
            self.category_vars[photobank] = tk.StringVar()
            combo = ttk.Combobox(bank_frame, textvariable=self.category_vars[photobank], 
                                values=self.photobank_categories[photobank], state="readonly")
            combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.category_combos[photobank] = combo
        
        # Generate button
        ttk.Button(categories_frame, text="Generovat kategorie", 
                  command=self.generate_categories).pack(fill=tk.X, pady=(10, 0))

    def setup_editorial_section(self, parent):
        """Setup editorial checkbox section."""
        editorial_frame = ttk.LabelFrame(parent, text="Speciální označení", padding=10)
        editorial_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.editorial_var = tk.BooleanVar()
        ttk.Checkbutton(editorial_frame, text="Editorial", 
                       variable=self.editorial_var).pack(anchor=tk.W)

    def setup_action_buttons(self, parent):
        """Setup save/cancel buttons."""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=5, pady=20)
        
        ttk.Button(buttons_frame, text="Uložit metadata", 
                  command=self.save_metadata).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Zrušit", 
                  command=self.cancel).pack(side=tk.LEFT)

    def load_media_file(self, file_path: str):
        """Load and display media file."""
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return
        
        self.media_file_path = file_path
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Update file info
        self.file_info_label.config(text=f"{file_name} ({file_size:,} bytes)")
        
        if is_image_file(file_path):
            self.load_image(file_path)
            self.video_controls.pack_forget()
        elif is_video_file(file_path):
            self.initialize_pygame_if_needed()  # Only init when actually needed
            self.load_video_preview(file_path)
            self.video_controls.pack(fill=tk.X, padx=5, pady=5)
        else:
            logging.warning(f"Unsupported file type: {file_path}")

    def load_image(self, image_path: str):
        """Load and display image."""
        try:
            image = Image.open(image_path)
            self.original_image_size = image.size
            self.resize_and_display_image(image)
        except Exception as e:
            logging.error(f"Error loading image {image_path}: {e}")
            messagebox.showerror("Error", f"Cannot load image: {e}")

    def load_video_preview(self, video_path: str):
        """Load video and show first frame."""
        # For now, just show a placeholder for video
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            self.canvas.create_text(canvas_width//2, canvas_height//2, 
                                  text=f"VIDEO\n{os.path.basename(video_path)}", 
                                  fill="white", font=("Arial", 16))

    def resize_and_display_image(self, image: Image.Image):
        """Resize and display image to fit canvas."""
        if not self.original_image_size:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet
            self.root.after(100, lambda: self.resize_and_display_image(image))
            return
        
        # Calculate aspect ratio preserving resize
        img_width, img_height = self.original_image_size
        aspect_ratio = img_width / img_height
        
        # Calculate new size
        if canvas_width / canvas_height > aspect_ratio:
            # Canvas is wider than image aspect ratio
            new_height = canvas_height
            new_width = int(new_height * aspect_ratio)
        else:
            # Canvas is taller than image aspect ratio
            new_width = canvas_width
            new_height = int(new_width / aspect_ratio)
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.current_image = ImageTk.PhotoImage(resized_image)
        
        # Clear and display
        self.canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_image)

    def on_window_resize(self, event):
        """Handle window resize to update image display."""
        if (hasattr(self, 'original_image_size') and self.original_image_size and 
            is_image_file(self.media_file_path)):
            # Reload image with new size after a short delay
            self.root.after(100, lambda: self.load_image(self.media_file_path))

    def update_title_counter(self, *args):
        """Update title character counter."""
        current_length = len(self.title_var.get())
        self.title_counter.config(text=f"{current_length}/{MAX_TITLE_LENGTH}")
        
        if current_length > MAX_TITLE_LENGTH:
            self.title_counter.config(foreground="red")
        else:
            self.title_counter.config(foreground="black")

    def update_description_counter(self, event=None):
        """Update description character counter."""
        current_text = self.description_text.get("1.0", tk.END).strip()
        current_length = len(current_text)
        self.desc_counter.config(text=f"{current_length}/{MAX_DESCRIPTION_LENGTH}")
        
        if current_length > MAX_DESCRIPTION_LENGTH:
            self.desc_counter.config(foreground="red")
        else:
            self.desc_counter.config(foreground="black")

    def add_keyword(self):
        """Add keyword to the list."""
        keyword = self.keyword_var.get().strip()
        if not keyword:
            return
        
        if keyword not in self.metadata['keywords']:
            if len(self.metadata['keywords']) >= MAX_KEYWORDS_COUNT:
                messagebox.showwarning("Warning", f"Maximum {MAX_KEYWORDS_COUNT} keywords allowed")
                return
            
            self.metadata['keywords'].append(keyword)
            self.keywords_listbox.insert(tk.END, keyword)
            self.update_keywords_counter()
        
        self.keyword_var.set("")

    def remove_keyword(self):
        """Remove selected keyword."""
        selection = self.keywords_listbox.curselection()
        if selection:
            index = selection[0]
            keyword = self.keywords_listbox.get(index)
            self.keywords_listbox.delete(index)
            self.metadata['keywords'].remove(keyword)
            self.update_keywords_counter()

    def update_keywords_counter(self):
        """Update keywords counter."""
        current_count = len(self.metadata['keywords'])
        self.keywords_counter.config(text=f"{current_count}/{MAX_KEYWORDS_COUNT}")

    def toggle_video(self):
        """Toggle video playback (placeholder)."""
        self.initialize_pygame_if_needed()  # Only init when needed
        if self.video_playing:
            self.play_button.config(text="Play")
            self.video_playing = False
        else:
            self.play_button.config(text="Pause")
            self.video_playing = True

    def on_ai_model_changed(self, event=None):
        """Handle AI model selection change."""
        display_name = self.ai_model_var.get()
        if display_name in self.model_mapping:
            self.selected_ai_model = self.model_mapping[display_name]
            logging.info(f"AI model changed to: {self.selected_ai_model}")
            self.update_model_info()
    
    def update_model_info(self):
        """Update model information display."""
        if not self.selected_ai_model or "/" not in self.selected_ai_model:
            self.model_info_label.config(text="No model selected")
            return
        
        provider, model = self.selected_ai_model.split("/", 1)
        model_config = self.config.get_ai_model_config(provider, model)
        
        if model_config:
            info_text = f"Max tokens: {model_config['max_tokens']}, "
            info_text += f"Images: {'Yes' if model_config['supports_images'] else 'No'}, "
            info_text += f"Cost: ${model_config['cost_per_1k_tokens']:.4f}/1K tokens"
            if model_config.get('notes'):
                info_text += f" ({model_config['notes']})"
            self.model_info_label.config(text=info_text)
        else:
            self.model_info_label.config(text="Model configuration not available")
    
    def get_current_ai_config(self):
        """Get current AI model configuration."""
        if not self.selected_ai_model or "/" not in self.selected_ai_model:
            return None
        
        provider, model = self.selected_ai_model.split("/", 1)
        return self.config.get_ai_model_config(provider, model)
    
    def initialize_pygame_if_needed(self):
        """Initialize pygame only when needed for better performance."""
        if not self.pygame_initialized:
            pygame.init()
            pygame.mixer.init()
            self.pygame_initialized = True

    # Placeholder methods for AI generation (to be implemented)
    def generate_title(self):
        """Generate title using AI (placeholder)."""
        ai_config = self.get_current_ai_config()
        if ai_config:
            model_name = ai_config['model_name']
            messagebox.showinfo("Info", f"AI generování titulku pomocí {model_name} bude implementováno později")
        else:
            messagebox.showwarning("Warning", "Není vybrán žádný AI model nebo chybí API klíč")

    def generate_description(self):
        """Generate description using AI (placeholder)."""
        ai_config = self.get_current_ai_config()
        if ai_config:
            model_name = ai_config['model_name']
            messagebox.showinfo("Info", f"AI generování popisu pomocí {model_name} bude implementováno později")
        else:
            messagebox.showwarning("Warning", "Není vybrán žádný AI model nebo chybí API klíč")

    def generate_keywords(self):
        """Generate keywords using AI (placeholder)."""
        ai_config = self.get_current_ai_config()
        if ai_config:
            model_name = ai_config['model_name']
            messagebox.showinfo("Info", f"AI generování klíčových slov pomocí {model_name} bude implementováno později")
        else:
            messagebox.showwarning("Warning", "Není vybrán žádný AI model nebo chybí API klíč")

    def generate_categories(self):
        """Generate categories using AI (placeholder)."""
        ai_config = self.get_current_ai_config()
        if ai_config:
            model_name = ai_config['model_name']
            messagebox.showinfo("Info", f"AI generování kategorií pomocí {model_name} bude implementováno později")
        else:
            messagebox.showwarning("Warning", "Není vybrán žádný AI model nebo chybí API klíč")

    def save_metadata(self):
        """Save metadata and close window."""
        # Collect all metadata
        self.metadata['title'] = self.title_var.get()
        self.metadata['description'] = self.description_text.get("1.0", tk.END).strip()
        self.metadata['editorial'] = self.editorial_var.get()
        
        # Collect categories
        for photobank, var in self.category_vars.items():
            self.metadata['categories'][photobank] = var.get()
        
        logging.info(f"Saved metadata for {self.media_file_path}")
        logging.debug(f"Metadata: {self.metadata}")
        
        messagebox.showinfo("Success", "Metadata byla úspěšně uložena")
        self.root.destroy()

    def cancel(self):
        """Cancel and close window."""
        self.root.destroy()

    def on_window_close(self):
        """Handle window close event."""
        self.cancel()