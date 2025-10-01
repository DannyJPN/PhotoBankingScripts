"""
Graphical media viewer with responsive layout for categorizing files.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import pygame
from typing import Optional, Callable, List, Dict
import threading
import time

from givephotobankreadymediafileslib.media_helper import is_video_file
from givephotobankreadymediafileslib.tag_entry import TagEntry
from givephotobankreadymediafileslib.editorial_dialog import (
    get_editorial_metadata, extract_editorial_metadata_from_exif
)


class MediaViewer:
    def __init__(self, root: tk.Tk, target_folder: str, categories: Dict[str, List[str]] = None):
        self.root = root
        self.root.title("AI Media Metadata Generator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Store categories
        self.categories = categories or {}
        
        # Initialize pygame for video playback
        pygame.init()
        pygame.mixer.init()
        
        # Current media info
        self.current_file_path: Optional[str] = None
        self.current_record: Optional[dict] = None
        self.current_image: Optional[ImageTk.PhotoImage] = None
        self.original_image_size: Optional[tuple] = None
        self.video_surface = None
        self.video_playing = False
        self.video_paused = False
        self.completion_callback: Optional[Callable] = None
        
        # AI generation state - separate threads for each type
        self.ai_threads = {
            'title': None,
            'description': None, 
            'keywords': None,
            'categories': None,
            'all': None
        }
        self.ai_cancelled = {
            'title': False,
            'description': False,
            'keywords': False, 
            'categories': False
        }
        self.generation_lock = threading.Lock()
        
        # Configure styles for tags
        self.setup_styles()
        
        self.setup_ui()
        
        # Bind resize event for responsive image display
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Handle window close event (equivalent to Ctrl+C)
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def setup_styles(self):
        """Setup custom styles for UI components."""
        style = ttk.Style()
        
        # Configure tag frame style
        style.configure('Tag.TFrame',
                       background='lightblue',
                       relief='raised',
                       borderwidth=1)
        
        # Configure reject button style (red text)
        style.configure('Reject.TButton', foreground='red')
        
    def setup_ui(self):
        """Setup the main UI layout."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for media display
        self.setup_media_panel(main_paned)
        
        # Right panel for metadata interface
        self.setup_metadata_panel(main_paned)
        
    def setup_media_panel(self, parent):
        """Setup the left panel for media display."""
        media_frame = ttk.Frame(parent)
        parent.add(media_frame, weight=2)
        
        # Media display area
        self.media_label = ttk.Label(media_frame, text="No media loaded", 
                                   anchor=tk.CENTER, background='black', foreground='white')
        self.media_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Video controls frame
        controls_frame = ttk.Frame(media_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.play_button = ttk.Button(controls_frame, text="Play", command=self.toggle_video)
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(controls_frame, text="Stop", command=self.stop_video)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Video progress bar
        self.video_progress = ttk.Scale(controls_frame, orient=tk.HORIZONTAL, 
                                      from_=0, to=100, command=self.seek_video)
        self.video_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Time labels
        self.time_label = ttk.Label(controls_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.RIGHT, padx=2)
        
        # Initially hide video controls
        controls_frame.pack_forget()
        self.controls_frame = controls_frame
        
    def setup_metadata_panel(self, parent):
        """Setup the right panel with metadata interface - horizontal layout with vertical keywords."""
        control_frame = ttk.Frame(parent)
        parent.add(control_frame, weight=1)
        
        # Create horizontal paned window for left fields + right keywords listbox
        metadata_paned = ttk.PanedWindow(control_frame, orient=tk.HORIZONTAL)
        metadata_paned.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        # Left side - metadata fields (wider)
        left_frame = ttk.Frame(metadata_paned)
        metadata_paned.add(left_frame, weight=3)
        
        # Right side - keywords listbox (narrower)
        right_frame = ttk.Frame(metadata_paned) 
        metadata_paned.add(right_frame, weight=2)
        
        # File path display (in left frame)
        path_frame = ttk.LabelFrame(left_frame, text="Current File")
        path_frame.pack(fill=tk.X, padx=5, pady=(5, 2))
        
        self.file_path_label = ttk.Label(path_frame, text="No file loaded", 
                                       wraplength=250, justify=tk.LEFT)
        self.file_path_label.pack(padx=10, pady=5, anchor=tk.W)
        
        # AI Model Selection (in left frame)
        self.setup_ai_model_panel(left_frame)
        
        # Title input (in left frame, narrower)
        title_frame = ttk.LabelFrame(left_frame, text="Title")
        title_frame.pack(fill=tk.X, padx=5, pady=(2, 2))
        
        ttk.Label(title_frame, text="Enter title:").pack(anchor=tk.W, padx=10, pady=(5, 3))
        
        # Title entry (smaller width)
        self.title_entry = ttk.Entry(title_frame, width=30)
        self.title_entry.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.title_entry.bind('<KeyRelease>', self.on_title_change)
        self.title_entry.bind('<Return>', self.handle_title_input)
        
        # Title controls
        title_controls_frame = ttk.Frame(title_frame)
        title_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.title_char_label = ttk.Label(title_controls_frame, text="0/100")
        self.title_char_label.pack(side=tk.LEFT)
        
        self.title_generate_button = ttk.Button(title_controls_frame, text="Generate", 
                                               command=self.generate_title)
        self.title_generate_button.pack(side=tk.RIGHT)
        
        # Description input (in left frame, taller)
        desc_frame = ttk.LabelFrame(left_frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=5, pady=(2, 2))
        
        ttk.Label(desc_frame, text="Enter description:").pack(anchor=tk.W, padx=10, pady=(5, 3))
        
        # Description text (taller for 200+ chars)
        self.desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD, font=('Arial', 9), width=30)
        self.desc_text.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.desc_text.bind('<KeyRelease>', self.on_description_change)
        
        # Description controls
        desc_controls_frame = ttk.Frame(desc_frame)
        desc_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.desc_char_label = ttk.Label(desc_controls_frame, text="0/200")
        self.desc_char_label.pack(side=tk.LEFT)
        
        self.desc_generate_button = ttk.Button(desc_controls_frame, text="Generate", 
                                              command=self.generate_description)
        self.desc_generate_button.pack(side=tk.RIGHT)
        
        # Keywords - vertical listbox (in right frame, fixed height, ends above categories)
        keywords_frame = ttk.LabelFrame(right_frame, text="Keywords (Tags)")
        keywords_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))
        
        # TagEntry widget - narrower width, expands to fill available height
        self.keywords_tag_entry = TagEntry(keywords_frame, width=25,
                                          max_tags=50, on_change=self.on_keywords_change)
        self.keywords_tag_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 5))
        
        # Keywords controls at bottom
        keywords_controls_frame = ttk.Frame(keywords_frame)
        keywords_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.keywords_count_label = ttk.Label(keywords_controls_frame, text="0/50")
        self.keywords_count_label.pack(side=tk.LEFT)
        
        self.keywords_generate_button = ttk.Button(keywords_controls_frame, text="Generate",
                                                  command=self.generate_keywords)
        self.keywords_generate_button.pack(side=tk.RIGHT)
        
        # Initialize keywords storage for compatibility
        self.keywords_list = []
        
        # Editorial checkbox (in left frame)
        editorial_frame = ttk.LabelFrame(left_frame, text="Editorial Mode")
        editorial_frame.pack(fill=tk.X, padx=5, pady=(2, 0))
        
        self.editorial_var = tk.BooleanVar()
        self.editorial_checkbox = ttk.Checkbutton(editorial_frame, text="Editorial mode",
                                                 variable=self.editorial_var)
        self.editorial_checkbox.pack(anchor=tk.W, padx=10, pady=5)
        
        # Categories selection spanning full width (below horizontal paned window)
        self.setup_categories_panel(control_frame)
        
        # Action buttons (span full width at bottom)
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=10, side=tk.BOTTOM)
        
        self.generate_all_button = ttk.Button(action_frame, text="Generate All", 
                                            command=self.generate_all_metadata)
        self.generate_all_button.pack(side=tk.LEFT, padx=2)
        
        self.save_button = ttk.Button(action_frame, text="Save & Continue", 
                                    command=self.save_metadata)
        self.save_button.pack(side=tk.LEFT, padx=2)
        
        self.reject_button = ttk.Button(action_frame, text="Reject",
                                      command=self.reject_metadata,
                                      style='Reject.TButton')
        self.reject_button.pack(side=tk.LEFT, padx=2)

        self.explorer_button = ttk.Button(action_frame, text="Open in Explorer",
                                        command=self.open_in_explorer)
        self.explorer_button.pack(side=tk.LEFT, padx=2)
        
    def setup_ai_model_panel(self, parent):
        """Setup AI model selection panel - simple dropdown only."""
        model_frame = ttk.LabelFrame(parent, text="AI Model Selection")
        model_frame.pack(fill=tk.X, padx=5, pady=(2, 2))
        
        # Model selection dropdown - compact layout
        selection_frame = ttk.Frame(model_frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Model:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_combo = ttk.Combobox(selection_frame, state="readonly", width=30)
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Load AI models after GUI is ready
        self.root.after(500, self.load_ai_models)
            
    def setup_categories_panel(self, parent):
        """Setup categories selection panel with all photobanks."""
        categories_frame = ttk.LabelFrame(parent, text="Categories")
        categories_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Categories selection with generate button
        categories_input_frame = ttk.Frame(categories_frame)
        categories_input_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(categories_input_frame, text="Select categories:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.categories_generate_button = ttk.Button(categories_input_frame, text="Generate", 
                                                    command=self.generate_categories)
        self.categories_generate_button.pack(side=tk.RIGHT)
        
        # Direct frame for categories (no scrolling needed)
        self.categories_container = ttk.Frame(categories_frame)
        self.categories_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Populate categories from passed data
        self.populate_categories_ui()
            
    def load_media(self, file_path: str, record: dict, completion_callback: Optional[Callable] = None):
        """Load and display media file with metadata interface."""
        self.current_file_path = file_path
        self.current_record = record
        self.completion_callback = completion_callback
        
        # Clear previous media
        self.clear_media()
        
        # Update file path display
        self.file_path_label.configure(text=file_path)
        
        # Load existing metadata from record if available
        title = record.get('Název', '')
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, title)
        self.on_title_change()  # Update character counter
        
        description = record.get('Popis', '')
        self.desc_text.delete('1.0', tk.END)
        self.desc_text.insert('1.0', description)
        self.on_description_change()  # Update character counter
        
        # Load keywords into tags
        keywords = record.get('Klíčová slova', '')
        self.keywords_list.clear()
        if keywords:
            for keyword in keywords.split(','):
                keyword = keyword.strip()
                if keyword:
                    self.keywords_list.append(keyword)
        self.refresh_keywords_display()
        
        # Load editorial mode
        editorial = record.get('Editorial', False)
        if isinstance(editorial, str):
            editorial = editorial.lower() in ('true', '1', 'yes', 'ano')
        self.editorial_var.set(bool(editorial))
        
        # Load existing categories from record
        self.load_existing_categories(record)
        
        # Load media file
        if is_video_file(file_path):
            self.load_video(file_path)
        else:
            self.load_image(file_path)
            
        # Focus on first control
        self.title_entry.focus()
        
    def load_image(self, file_path: str):
        """Load and display an image file with responsive sizing."""
        try:
            # Hide video controls
            self.controls_frame.pack_forget()
            
            # Load original image
            image = Image.open(file_path)
            self.original_image_size = image.size
            
            # Resize for current display area
            self.resize_image()
            
        except Exception as e:
            logging.error(f"Error loading image: {e}")
            self.media_label.configure(image="", text=f"Error loading image:\n{str(e)}")
            
    def resize_image(self):
        """Resize current image to fit display area responsively."""
        if not self.current_file_path or not self.original_image_size:
            return
            
        try:
            # Get current display area size
            self.media_label.update_idletasks()
            display_width = max(self.media_label.winfo_width() - 20, 300)
            display_height = max(self.media_label.winfo_height() - 20, 200)
            
            # Load image again
            image = Image.open(self.current_file_path)
            
            # Calculate scaling to fit area while maintaining aspect ratio
            # Never scale above 100% of original size
            scale_x = min(display_width / image.width, 1.0)
            scale_y = min(display_height / image.height, 1.0) 
            scale = min(scale_x, scale_y)
            
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(image)
            
            # Display image
            self.media_label.configure(image=self.current_image, text="")
            
        except Exception as e:
            logging.error(f"Error resizing image: {e}")
            
    def on_window_resize(self, event):
        """Handle window resize events."""
        # Only resize image if it's the main window being resized
        if event.widget == self.root and self.current_file_path and not is_video_file(self.current_file_path):
            # Delay resize to avoid too many calls
            self.root.after(100, self.resize_image)
            
    def load_video(self, file_path: str):
        """Load and prepare video for playback."""
        try:
            # Show video controls
            self.controls_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # For now, show video info and thumbnail
            self.media_label.configure(image="", text=f"Video file:\n{os.path.basename(file_path)}\n\nUse controls below to play")
            
            
        except Exception as e:
            logging.error(f"Error loading video: {e}")
            self.media_label.configure(image="", text=f"Error loading video:\n{str(e)}")
            
    def clear_media(self):
        """Clear current media display."""
        self.current_image = None
        self.media_label.configure(image="", text="No media loaded")
        self.stop_video()
        
    def toggle_video(self):
        """Toggle video play/pause."""
        if self.video_playing:
            self.pause_video()
        else:
            self.play_video()
            
    def play_video(self):
        """Start video playback."""
        if self.current_file_path and is_video_file(self.current_file_path):
            self.video_playing = True
            self.video_paused = False
            self.play_button.configure(text="Pause")
            
    def pause_video(self):
        """Pause video playback."""
        self.video_playing = False
        self.video_paused = True
        self.play_button.configure(text="Play")
        
    def stop_video(self):
        """Stop video playback."""
        self.video_playing = False
        self.video_paused = False
        self.play_button.configure(text="Play")
        self.video_progress.set(0)
        
    def seek_video(self, value):
        """Seek to position in video."""
        if self.current_file_path and is_video_file(self.current_file_path):
            logging.info(f"Seeking to {float(value):.1f}%")
        
    def load_ai_models(self):
        """Load available AI models from configuration - lazy loading."""
        try:
            # Load config only when needed
            from shared.config import get_config
            config = get_config()
            
            available_models = config.get_available_ai_models()
            
            if not available_models:
                logging.warning("No AI models available - check API keys in environment or config")
                self.model_combo.configure(values=["No models available"])
                self.model_combo.set("No models available")
                return
            
            # Populate combo box
            model_names = [model["display_name"] for model in available_models]
            self.model_combo.configure(values=model_names)
            
            # Set default model
            default_provider, default_model = config.get_default_ai_model()
            default_key = f"{default_provider}/{default_model}"
            
            for i, model in enumerate(available_models):
                if model["key"] == default_key:
                    self.model_combo.current(i)
                    break
            else:
                # Default not found, select first
                if available_models:
                    self.model_combo.current(0)
            
            # Bind selection change
            self.model_combo.bind('<<ComboboxSelected>>', self.on_model_selected)
            
            # Load initial model details
            self.on_model_selected()
            
        except Exception as e:
            logging.error(f"Error loading AI models: {e}")
            self.model_combo.configure(values=["Error loading models"])
            self.model_combo.set("Error loading models")
    
    def on_model_selected(self, event=None):
        """Handle model selection change."""
        selection = self.model_combo.get()
        logging.info(f"AI model selected: {selection}")
        # Model details can be displayed here if needed
    
    def populate_categories_ui(self):
        """Populate categories UI with dropdown lists for each photobank based on their actual needs."""
        self.category_combos = {}
        
        if not self.categories:
            ttk.Label(self.categories_container, 
                     text="No categories available").pack(pady=10)
            return
        
        # Define number of categories per photobank based on verified 2025 research
        categories_count = {
            'shutterstock': 2,  # Up to 2 categories (verified from Shutterstock docs)
            'adobestock': 1,    # 1 category (Adobe Sensei suggests one category)  
            'dreamstime': 3,    # Up to 3 categories (verified from Dreamstime blog)
            'alamy': 2,         # Primary + optional Secondary category (verified from Alamy help)
            # All other photobanks have NO categories
            'depositphotos': 0,
            'bigstockphoto': 0,
            '123rf': 0,
            'canstockphoto': 0,
            'pond5': 0,
            'gettyimages': 0
        }
        
        # Create UI for each photobank's categories in compact horizontal layout
        photobanks_with_categories = [(photobank, categories) for photobank, categories in self.categories.items() 
                                    if categories_count.get(photobank.lower().replace(' ', '').replace('_', ''), 0) > 0]
        
        if not photobanks_with_categories:
            ttk.Label(self.categories_container, text="No categories available").pack(pady=10)
            return
        
        # Horizontal layout: all photobanks in one row
        row_frame = ttk.Frame(self.categories_container)
        row_frame.pack(fill=tk.X, pady=5)
        
        for i, (photobank, categories) in enumerate(photobanks_with_categories):
            photobank_key = photobank.lower().replace(' ', '').replace('_', '')
            max_categories = categories_count.get(photobank_key, 0)
            
            # Create compact frame for this photobank
            bank_frame = ttk.Frame(row_frame)
            bank_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
            
            # Photobank label
            bank_label = ttk.Label(bank_frame, text=photobank)
            bank_label.pack(anchor=tk.W)
            
            # Create dropdowns for this photobank
            self.category_combos[photobank] = []
            for j in range(max_categories):
                combo = ttk.Combobox(bank_frame, values=[''] + categories, 
                                   state="readonly", width=12)
                combo.pack(fill=tk.X, pady=1)
                combo.set('')  # Default to empty
                
                self.category_combos[photobank].append(combo)

    def load_existing_categories(self, record: dict):
        """Load existing categories from CSV record into UI dropdowns."""
        if not hasattr(self, 'category_combos') or not self.category_combos:
            return
        
        # Category field mappings for CSV columns
        category_mappings = {
            'shutterstock': ['Kategorie_ShutterStock', 'Kategorie_ShutterStock_2'],
            'adobestock': ['Kategorie_AdobeStock'],
            'dreamstime': ['Kategorie_Dreamstime_1', 'Kategorie_Dreamstime_2', 'Kategorie_Dreamstime_3'],
            'alamy': ['Kategorie_Alamy_1', 'Kategorie_Alamy_2']
        }
        
        # Load categories for each photobank
        for photobank, combos in self.category_combos.items():
            photobank_key = photobank.lower().replace(' ', '').replace('_', '')
            
            if photobank_key in category_mappings:
                category_fields = category_mappings[photobank_key]
                
                # Set values for each dropdown
                for i, combo in enumerate(combos):
                    if i < len(category_fields):
                        field_name = category_fields[i]
                        category_value = record.get(field_name, '').strip()
                        
                        if category_value:
                            # Find the category in combo values and select it
                            values = combo['values']
                            if category_value in values:
                                combo.set(category_value)
                                logging.info(f"Loaded category for {photobank} [{i+1}]: {category_value}")
    
    def on_title_change(self, event=None):
        """Update title character counter."""
        current_length = len(self.title_entry.get())
        self.title_char_label.configure(text=f"{current_length}/100")
        if current_length > 100:
            self.title_char_label.configure(foreground='red')
        else:
            self.title_char_label.configure(foreground='black')
    
    def on_description_change(self, event=None):
        """Update description character counter."""
        current_text = self.desc_text.get('1.0', tk.END)
        current_length = len(current_text.strip())
        self.desc_char_label.configure(text=f"{current_length}/200")
        if current_length > 200:
            self.desc_char_label.configure(foreground='red')
        else:
            self.desc_char_label.configure(foreground='black')
    
    def on_keywords_change(self):
        """Handle keywords change from TagEntry widget."""
        # Update keywords list for compatibility with existing code
        self.keywords_list = self.keywords_tag_entry.get_tags()
        self.update_keywords_counter()
    
    def refresh_keywords_display(self):
        """Refresh the keywords display after loading from file."""
        # Set tags in the new TagEntry widget
        self.keywords_tag_entry.set_tags(self.keywords_list)
        
        # Update counter
        self.update_keywords_counter()
    
    def update_keywords_counter(self):
        """Update keywords counter."""
        current_count = len(self.keywords_list)
        self.keywords_count_label.configure(text=f"{current_count}/50")
        if current_count >= 50:
            self.keywords_count_label.configure(foreground='red')
        else:
            self.keywords_count_label.configure(foreground='black')

    def handle_title_input(self, event):
        """Handle title input Enter key."""
        # Move focus to description
        self.desc_text.focus()
    
    def generate_title(self):
        """Generate title using AI in background thread."""
        if not self.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return
            
        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return
        
        # Check if title generation is already running
        if self.ai_threads['title'] and self.ai_threads['title'].is_alive():
            # Cancel current generation
            self.ai_cancelled['title'] = True
            self.title_generate_button.configure(text="Generate", state="normal")
            return
            
        # Start generation in background thread
        self.ai_cancelled['title'] = False
        self.ai_threads['title'] = threading.Thread(
            target=self._generate_title_worker,
            args=(selected_model,),
            daemon=True
        )
        
        # Update UI for loading state
        self.title_generate_button.configure(text="Cancel")
        
        self.ai_threads['title'].start()
    
    def _generate_title_worker(self, selected_model: str):
        """Worker thread for title generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator
            
            config = get_config()
            available_models = config.get_available_ai_models()
            
            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break
            
            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")
            
            # Check for cancellation
            if self.ai_cancelled['title']:
                return
            
            # Create generator and generate title
            generator = create_metadata_generator(model_key)
            existing_title = self.title_entry.get().strip()
            title = generator.generate_title(self.current_file_path, 
                                           existing_title if existing_title else None)
            
            # Check for cancellation before updating UI
            if self.ai_cancelled['title']:
                return
            
            # Update UI in main thread
            self.root.after(0, self._update_title_result, title, None)
            
        except Exception as e:
            logging.error(f"Title generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_title_result, None, str(e))
    
    def _update_title_result(self, title: Optional[str], error: Optional[str]):
        """Update UI with title generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate title: {error}")
            elif title and not self.ai_cancelled['title']:
                self.title_entry.delete(0, tk.END)

                self.title_entry.insert(0, title)
                self.on_title_change()
        finally:
            # Reset button
            self.title_generate_button.configure(text="Generate", state="normal")
    
    def generate_description(self):
        """Generate description using AI in background thread."""
        if not self.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return
            
        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return
        
        # Check if description generation is already running
        if self.ai_threads['description'] and self.ai_threads['description'].is_alive():
            # Cancel current generation
            self.ai_cancelled['description'] = True
            self.desc_generate_button.configure(text="Generate", state="normal")
            return
            
        # Start generation in background thread
        self.ai_cancelled['description'] = False
        self.ai_threads['description'] = threading.Thread(
            target=self._generate_description_worker,
            args=(selected_model,),
            daemon=True
        )
        
        # Update UI for loading state
        self.desc_generate_button.configure(text="Cancel")
        
        self.ai_threads['description'].start()
    
    def _generate_description_worker(self, selected_model: str):
        """Worker thread for description generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator
            
            config = get_config()
            available_models = config.get_available_ai_models()
            
            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break
            
            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")
            
            # Check for cancellation
            if self.ai_cancelled['description']:
                return
            
            # Handle editorial metadata if needed
            editorial_data = None
            if self.editorial_var.get():
                # Extract editorial metadata from EXIF
                extracted_data, missing_fields = extract_editorial_metadata_from_exif(self.current_file_path)
                
                # Check if we need user input for missing fields
                if any(missing_fields.values()):
                    # Show dialog synchronously and wait for result
                    editorial_data = self._show_editorial_dialog_sync(missing_fields, extracted_data)
                    if editorial_data is None:
                        # User cancelled - stop generation
                        return
                    # Merge with extracted data
                    editorial_data = {**extracted_data, **editorial_data}
                else:
                    editorial_data = extracted_data
            
            # Create generator and generate description
            generator = create_metadata_generator(model_key)
            existing_title = self.title_entry.get().strip()
            existing_desc = self.desc_text.get('1.0', tk.END).strip()
            
            description = generator.generate_description(
                self.current_file_path, 
                existing_title if existing_title else None,
                existing_desc if existing_desc else None,
                editorial_data
            )
            
            # Check for cancellation before updating UI
            if self.ai_cancelled['description']:
                return
            
            # Update UI in main thread
            self.root.after(0, self._update_description_result, description, None)
            
        except Exception as e:
            logging.error(f"Description generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_description_result, None, str(e))
    
    def _update_description_result(self, description: Optional[str], error: Optional[str]):
        """Update UI with description generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate description: {error}")
            elif description and not self.ai_cancelled['description']:
                self.desc_text.delete('1.0', tk.END)
                self.desc_text.insert('1.0', description)
                self.on_description_change()
        finally:
            # Reset button
            self.desc_generate_button.configure(text="Generate", state="normal")
    
    def generate_keywords(self):
        """Generate keywords using AI in background thread."""
        if not self.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return
            
        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return
        
        # Check if keywords generation is already running
        if self.ai_threads['keywords'] and self.ai_threads['keywords'].is_alive():
            # Cancel current generation
            self.ai_cancelled['keywords'] = True
            self.keywords_generate_button.configure(text="Generate", state="normal")
            return
            
        # Start generation in background thread
        self.ai_cancelled['keywords'] = False
        self.ai_threads['keywords'] = threading.Thread(
            target=self._generate_keywords_worker,
            args=(selected_model,),
            daemon=True
        )
        
        # Update UI for loading state
        self.keywords_generate_button.configure(text="Cancel")
        
        self.ai_threads['keywords'].start()
    
    def _generate_keywords_worker(self, selected_model: str):
        """Worker thread for keywords generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator
            
            config = get_config()
            available_models = config.get_available_ai_models()
            
            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break
            
            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")
            
            # Check for cancellation
            if self.ai_cancelled['keywords']:
                return
            
            # Create generator and generate keywords
            generator = create_metadata_generator(model_key)
            existing_title = self.title_entry.get().strip()
            existing_desc = self.desc_text.get('1.0', tk.END).strip()
            
            # Ask for keyword count
            keyword_count = min(50, 50 - len(self.keywords_list))  # Don't exceed 50 total
            
            keywords = generator.generate_keywords(
                self.current_file_path,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None,
                keyword_count,
                self.editorial_var.get()  # Pass editorial flag
            )
            
            # Check for cancellation before updating UI
            if self.ai_cancelled['keywords']:
                return
            
            # Update UI in main thread
            self.root.after(0, self._update_keywords_result, keywords, None)
            
        except Exception as e:
            logging.error(f"Keywords generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_keywords_result, None, str(e))
    
    def _update_keywords_result(self, keywords: Optional[List[str]], error: Optional[str]):
        """Update UI with keywords generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate keywords: {error}")
            elif keywords and not self.ai_cancelled['keywords']:
                # Add keywords to existing list (avoiding duplicates)
                for keyword in keywords:
                    if keyword not in self.keywords_list and len(self.keywords_list) < 50:
                        self.keywords_list.append(keyword)
                
                # Update UI
                self.refresh_keywords_display()
        finally:
            # Reset button
            self.keywords_generate_button.configure(text="Generate", state="normal")
    
    def generate_categories(self):
        """Generate categories using AI in background thread."""
        if not self.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return
            
        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return
            
        if not hasattr(self, 'category_combos') or not self.category_combos:
            messagebox.showinfo("No Categories", "No category dropdowns available to populate")
            return
        
        # Check if categories generation is already running
        if self.ai_threads['categories'] and self.ai_threads['categories'].is_alive():
            # Cancel current generation
            self.ai_cancelled['categories'] = True
            self.categories_generate_button.configure(text="Generate", state="normal")
            return
            
        # Start generation in background thread
        self.ai_cancelled['categories'] = False
        self.ai_threads['categories'] = threading.Thread(
            target=self._generate_categories_worker,
            args=(selected_model,),
            daemon=True
        )
        
        # Update UI for loading state
        self.categories_generate_button.configure(text="Cancel")
        
        self.ai_threads['categories'].start()
    
    def _generate_categories_worker(self, selected_model: str):
        """Worker thread for categories generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator
            
            config = get_config()
            available_models = config.get_available_ai_models()
            
            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break
            
            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")
            
            # Check for cancellation
            if self.ai_cancelled['categories']:
                return
            
            # Create generator and set categories
            generator = create_metadata_generator(model_key)
            generator.set_photobank_categories(self.categories)
            
            existing_title = self.title_entry.get().strip()
            existing_desc = self.desc_text.get('1.0', tk.END).strip()
            
            # Generate categories for all photobanks
            generated_categories = generator.generate_categories(
                self.current_file_path,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None
            )
            
            # Check for cancellation before updating UI
            if self.ai_cancelled['categories']:
                return
            
            # Update UI in main thread
            self.root.after(0, self._update_categories_result, generated_categories, None)
            
        except Exception as e:
            logging.error(f"Categories generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_categories_result, None, str(e))
    
    def _update_categories_result(self, generated_categories: Optional[Dict], error: Optional[str]):
        """Update UI with categories generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate categories: {error}")
            elif generated_categories and not self.ai_cancelled['categories']:
                # Update UI dropdowns with generated categories
                for photobank, categories in generated_categories.items():
                    if photobank in self.category_combos:
                        combos = self.category_combos[photobank]
                        
                        # Set categories in dropdowns
                        for i, category in enumerate(categories):
                            if i < len(combos):
                                if category in combos[i]['values']:
                                    combos[i].set(category)
                                    logging.info(f"Set category for {photobank} [{i+1}]: {category}")
        finally:
            # Reset button
            self.categories_generate_button.configure(text="Generate", state="normal")
    
    def generate_all_metadata(self):
        """Generate all metadata serially with proper dependencies."""
        if not self.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return
            
        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return
        
        # Check if Generate All is already active - if so, cancel
        if hasattr(self, '_generate_all_active') and self._generate_all_active:
            self._cancel_all_generation()
            return
            
        # Start serial generation in background thread
        self._generate_all_active = True
        self.generate_all_button.configure(text="Cancel", state="normal")
        
        # Start generation in background thread to avoid blocking UI
        self.ai_threads['all'] = threading.Thread(
            target=self._generate_all_worker,
            args=(selected_model,),
            daemon=True
        )
        self.ai_threads['all'].start()
        
    def _generate_all_worker(self, selected_model: str):
        """Worker thread that runs all generations serially with join()."""
        try:
            # Reset all cancellation flags
            for gen_type in ['title', 'description', 'keywords', 'categories']:
                self.ai_cancelled[gen_type] = False
            
            # Generate title and wait for completion
            self._start_and_wait_for_generation('title', selected_model)
            if not self._generate_all_active or self.ai_cancelled['title']:
                return
            
            # Generate description and wait for completion
            self._start_and_wait_for_generation('description', selected_model)
            if not self._generate_all_active or self.ai_cancelled['description']:
                return
                
            # Generate keywords and wait for completion
            self._start_and_wait_for_generation('keywords', selected_model)
            if not self._generate_all_active or self.ai_cancelled['keywords']:
                return
                
            # Generate categories and wait for completion
            self._start_and_wait_for_generation('categories', selected_model)
            if not self._generate_all_active or self.ai_cancelled['categories']:
                return
            
            # All completed successfully
            self.root.after(0, self._complete_all_generation)
            
        except Exception as e:
            logging.error(f"Generate All failed: {e}")
            self.root.after(0, self._complete_all_generation)
    
    def _start_and_wait_for_generation(self, gen_type: str, selected_model: str):
        """Start a generation and wait for it to complete."""
        # Update UI in main thread - change button to Cancel
        if gen_type == 'title':
            self.root.after(0, lambda: self.title_generate_button.configure(text="Cancel"))
        elif gen_type == 'description':
            self.root.after(0, lambda: self.desc_generate_button.configure(text="Cancel"))
        elif gen_type == 'keywords':
            self.root.after(0, lambda: self.keywords_generate_button.configure(text="Cancel"))
        elif gen_type == 'categories':
            self.root.after(0, lambda: self.categories_generate_button.configure(text="Cancel"))
        
        # Start the worker thread directly
        if gen_type == 'title':
            self.ai_threads['title'] = threading.Thread(
                target=self._generate_title_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['title'].start()
            self.ai_threads['title'].join()
        elif gen_type == 'description':
            self.ai_threads['description'] = threading.Thread(
                target=self._generate_description_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['description'].start()
            self.ai_threads['description'].join()
        elif gen_type == 'keywords':
            self.ai_threads['keywords'] = threading.Thread(
                target=self._generate_keywords_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['keywords'].start()
            self.ai_threads['keywords'].join()
        elif gen_type == 'categories':
            self.ai_threads['categories'] = threading.Thread(
                target=self._generate_categories_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['categories'].start()
            self.ai_threads['categories'].join()
    
    def _any_thread_running(self):
        """Check if any AI generation thread is currently running."""
        for thread_type, thread in self.ai_threads.items():
            if thread and thread.is_alive():
                return True
        return False
        
    def _cancel_all_generation(self):
        """Cancel all running generations and reset all buttons."""
        # Set cancellation flags for all types
        for gen_type in ['title', 'description', 'keywords', 'categories']:
            self.ai_cancelled[gen_type] = True
        
        # Reset all individual buttons to Generate state
        self.title_generate_button.configure(text="Generate", state="normal")
        self.desc_generate_button.configure(text="Generate", state="normal")
        self.keywords_generate_button.configure(text="Generate", state="normal")
        self.categories_generate_button.configure(text="Generate", state="normal")
        
        # Reset Generate All state and button
        self._generate_all_active = False
        self.generate_all_button.configure(text="Generate All", state="normal")
        
        logging.info("All generations cancelled")
    
    def _complete_all_generation(self):
        """Complete the generate all process."""
        self._generate_all_active = False
        self.generate_all_button.configure(text="Generate All", state="normal")
        logging.info("All metadata generation completed")



    def save_metadata(self):
        """Save metadata and close window."""
        if not hasattr(self, 'current_record'):
            messagebox.showwarning("No File", "No file is currently loaded.")
            return
        
        # Collect metadata
        title = self.title_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        
        # Collect keywords from tags list
        keywords = ', '.join(self.keywords_list)
        
        if not title:
            messagebox.showwarning("Missing Data", "Please enter a title.")
            return
        
        # Collect selected categories from dropdowns
        selected_categories = {}
        if hasattr(self, 'category_combos'):
            for photobank, combos in self.category_combos.items():
                selected_categories[photobank] = []
                for combo in combos:
                    value = combo.get().strip()
                    if value:  # Only add non-empty selections
                        selected_categories[photobank].append(value)
        
        # Update record with metadata
        metadata = {
            'title': title,
            'description': description,
            'keywords': keywords,
            'editorial': self.editorial_var.get(),
            'categories': selected_categories
        }
        
        # Call completion callback with metadata
        if self.completion_callback:
            self.completion_callback(metadata)
            
        self.root.destroy()
    
    def reject_metadata(self):
        """Reject this file and set status to rejected for all photobanks."""
        if not hasattr(self, 'current_record'):
            messagebox.showwarning("No File", "No file is currently loaded.")
            return
        
        # Ask for confirmation
        response = messagebox.askyesno(
            "Reject File", 
            f"Are you sure you want to reject this file?\n\n{self.current_file_path}\n\nThis will set status to 'zamítnuto' for all photobanks.",
            icon='warning'
        )
        
        if not response:
            return
        
        # Create rejection metadata (minimal data needed)
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'editorial': False,
            'categories': {},
            'rejected': True  # Special flag to indicate rejection
        }
        
        # Call completion callback with rejection metadata
        if self.completion_callback:
            self.completion_callback(metadata)
            
        self.root.destroy()
        
    def _show_editorial_dialog(self, missing_fields: Dict[str, bool], extracted_data: Dict[str, str], selected_model: str):
        """Show editorial metadata dialog and continue description generation."""
        try:
            # Show dialog and get result
            editorial_data = get_editorial_metadata(self.root, missing_fields, extracted_data)
            
            if editorial_data is None:
                # User cancelled - reset button and return
                self.desc_generate_button.configure(text="Generate", state="normal")
                return
            
            # Continue description generation with complete editorial data
            complete_data = {**extracted_data, **editorial_data}
            
            # Start new thread for generation with complete data
            self.ai_threads['description'] = threading.Thread(
                target=self._generate_description_with_editorial,
                args=(selected_model, complete_data),
                daemon=True
            )
            self.ai_threads['description'].start()
            
        except Exception as e:
            logging.error(f"Editorial dialog failed: {e}")
            self.root.after(0, self._update_description_result, None, str(e))
    
    def _generate_description_with_editorial(self, selected_model: str, editorial_data: Dict[str, str]):
        """Continue description generation with complete editorial data."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator
            
            config = get_config()
            available_models = config.get_available_ai_models()
            
            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break
            
            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")
            
            # Check for cancellation
            if self.ai_cancelled['description']:
                return
            
            # Create generator and generate description with editorial data
            generator = create_metadata_generator(model_key)
            existing_title = self.title_entry.get().strip()
            existing_desc = self.desc_text.get('1.0', tk.END).strip()
            
            description = generator.generate_description(
                self.current_file_path,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None,
                editorial_data
            )
            
            # Check for cancellation before updating UI
            if self.ai_cancelled['description']:
                return
            
            # Update UI in main thread
            self.root.after(0, self._update_description_result, description, None)
            
        except Exception as e:
            logging.error(f"Description generation with editorial failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_description_result, None, str(e))

    def _show_editorial_dialog_sync(self, missing_fields: Dict[str, bool], extracted_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Show editorial dialog synchronously from worker thread."""
        # Create result container and event for synchronization
        result_container = {'result': None}
        dialog_completed = threading.Event()
        
        def show_dialog_in_main_thread():
            """Show dialog in main thread and store result."""
            try:
                result_container['result'] = get_editorial_metadata(self.root, missing_fields, extracted_data)
            except Exception as e:
                logging.error(f"Editorial dialog error: {e}")
                result_container['result'] = None
            finally:
                dialog_completed.set()
        
        # Schedule dialog to show in main thread
        self.root.after(0, show_dialog_in_main_thread)
        
        # Wait for dialog completion (blocks worker thread)
        dialog_completed.wait()
        
        return result_container['result']

    def open_in_explorer(self):
        """Open the current file location in Windows Explorer."""
        if not self.current_file_path:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                # Use Windows Explorer to show file and select it
                # Don't use check=True as Explorer sometimes returns non-zero exit codes even on success
                result = subprocess.run(['explorer', '/select,', self.current_file_path])
                logging.info(f"Opened file location in Explorer: {self.current_file_path} (exit code: {result.returncode})")
            else:
                # For other systems, just open the directory
                directory = os.path.dirname(self.current_file_path)
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(['open', directory])
                else:  # Linux and others
                    subprocess.run(['xdg-open', directory])
                logging.info(f"Opened directory: {directory}")

        except Exception as e:
            logging.error(f"Failed to open file location: {e}")
            messagebox.showerror("Error", f"Failed to open file location:\n{str(e)}")

    def on_window_close(self):
        """Handle window close event - equivalent to Ctrl+C."""
        logging.info("Window closed by user - terminating script")
        self.root.destroy()

        # Exit the entire script (equivalent to Ctrl+C)
        import sys
        sys.exit(0)


def show_media_viewer(file_path: str, record: dict, completion_callback: Optional[Callable] = None, 
                     categories: Dict[str, List[str]] = None):
    """Show the media viewer for a specific file and record."""
    root = tk.Tk()
    viewer = MediaViewer(root, "", categories)  # Pass categories to viewer
    viewer.load_media(file_path, record, completion_callback)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()
    

if __name__ == "__main__":
    # Test the viewer
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        show_media_viewer(test_file)
    else:
        print("Usage: python media_viewer.py <media_file>")