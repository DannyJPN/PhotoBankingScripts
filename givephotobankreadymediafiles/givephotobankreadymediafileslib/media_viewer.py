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
        
    def setup_ui(self):
        """Setup the main UI layout."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for media display
        self.setup_media_panel(main_paned)
        
        # Right panel for metadata interface
        self.setup_terminal_panel(main_paned)
        
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
        
    def setup_terminal_panel(self, parent):
        """Setup the right panel with metadata interface."""
        control_frame = ttk.Frame(parent)
        parent.add(control_frame, weight=1)
        
        # File path display
        path_frame = ttk.LabelFrame(control_frame, text="Current File")
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_path_label = ttk.Label(path_frame, text="No file loaded", 
                                       wraplength=300, justify=tk.LEFT)
        self.file_path_label.pack(padx=10, pady=10, anchor=tk.W)
        
        # AI Model Selection - at the top after Current File
        self.setup_ai_model_panel(control_frame)
        
        # Title input with generate button
        title_frame = ttk.LabelFrame(control_frame, text="Title")
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(title_frame, text="Enter title:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Title entry and button frame
        title_input_frame = ttk.Frame(title_frame)
        title_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Title with character limit (shortest limit across photobanks is ~100 chars)
        self.title_entry = ttk.Entry(title_input_frame, width=60)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.title_entry.bind('<KeyRelease>', self.on_title_change)
        
        # Title character counter
        self.title_char_label = ttk.Label(title_input_frame, text="0/100")
        self.title_char_label.pack(side=tk.RIGHT, padx=(5, 5))
        self.title_entry.bind('<Return>', self.handle_title_input)
        
        self.title_generate_button = ttk.Button(title_input_frame, text="Generate", 
                                               command=self.generate_title)
        self.title_generate_button.pack(side=tk.RIGHT)
        
        # Description input with generate button
        desc_frame = ttk.LabelFrame(control_frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(desc_frame, text="Enter description:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Description input and button frame
        desc_input_frame = ttk.Frame(desc_frame)
        desc_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Description with character limit (shortest limit ~200 chars)
        self.desc_text = tk.Text(desc_input_frame, height=2, wrap=tk.WORD, font=('Arial', 9), width=50)
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.desc_text.bind('<KeyRelease>', self.on_description_change)
        
        # Description controls frame
        desc_controls_frame = ttk.Frame(desc_input_frame)
        desc_controls_frame.pack(side=tk.RIGHT, anchor=tk.N)
        
        # Description character counter
        self.desc_char_label = ttk.Label(desc_controls_frame, text="0/200")
        self.desc_char_label.pack(pady=(0, 2))
        
        self.desc_generate_button = ttk.Button(desc_controls_frame, text="Generate", 
                                              command=self.generate_description)
        self.desc_generate_button.pack()
        
        # Keywords input with generate button
        keywords_frame = ttk.LabelFrame(control_frame, text="Keywords")
        keywords_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(keywords_frame, text="Enter keywords:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Keywords as tags with drag & drop
        keywords_input_frame = ttk.Frame(keywords_frame)
        keywords_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Keywords tags container with scrolling
        keywords_container = ttk.Frame(keywords_input_frame)
        keywords_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Entry for adding keywords
        self.keyword_entry = ttk.Entry(keywords_container)
        self.keyword_entry.pack(fill=tk.X, pady=(0, 5))
        self.keyword_entry.bind('<KeyPress>', self.validate_keyword_input)
        self.keyword_entry.bind('<KeyRelease>', self.on_keyword_entry_change)
        self.keyword_entry.bind('<Return>', self.process_keyword_entry)
        
        # Scrollable tags area
        self.tags_canvas = tk.Canvas(keywords_container, height=60, bg='white', highlightthickness=1)
        tags_scrollbar = ttk.Scrollbar(keywords_container, orient=tk.HORIZONTAL, command=self.tags_canvas.xview)
        self.tags_frame = ttk.Frame(self.tags_canvas)
        
        self.tags_canvas.configure(xscrollcommand=tags_scrollbar.set)
        self.tags_canvas.create_window((0, 0), window=self.tags_frame, anchor="nw")
        
        self.tags_canvas.pack(fill=tk.BOTH, expand=True)
        tags_scrollbar.pack(fill=tk.X)
        
        # Bind canvas resizing
        self.tags_frame.bind('<Configure>', self.on_tags_frame_configure)
        
        # Keywords controls frame
        keywords_controls_frame = ttk.Frame(keywords_input_frame)
        keywords_controls_frame.pack(side=tk.RIGHT, anchor=tk.N)
        
        # Keywords counter
        self.keywords_count_label = ttk.Label(keywords_controls_frame, text="0/50")
        self.keywords_count_label.pack(pady=(0, 5))
        
        self.keywords_generate_button = ttk.Button(keywords_controls_frame, text="Generate", width=8,
                                                  command=self.generate_keywords)
        self.keywords_generate_button.pack()
        
        # Initialize keywords storage
        self.keywords_list = []
        self.tag_widgets = []
        
        # Editorial checkbox
        editorial_frame = ttk.LabelFrame(control_frame, text="Editorial Mode")
        editorial_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.editorial_var = tk.BooleanVar()
        self.editorial_checkbox = ttk.Checkbutton(editorial_frame, text="Enable editorial mode (news, documentary, etc.)",
                                                 variable=self.editorial_var)
        self.editorial_checkbox.pack(anchor=tk.W, padx=10, pady=10)
        
        # Categories selection
        self.setup_categories_panel(control_frame)
        
        # Action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.generate_all_button = ttk.Button(action_frame, text="Generate All", 
                                            command=self.generate_all_metadata)
        self.generate_all_button.pack(side=tk.LEFT, padx=2)
        
        self.save_button = ttk.Button(action_frame, text="Save & Continue", 
                                    command=self.save_metadata)
        self.save_button.pack(side=tk.LEFT, padx=2)
        
    def setup_ai_model_panel(self, parent):
        """Setup AI model selection panel - simple dropdown only."""
        model_frame = ttk.LabelFrame(parent, text="AI Model Selection")
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model selection dropdown - compact layout
        selection_frame = ttk.Frame(model_frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(selection_frame, text="Model:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_combo = ttk.Combobox(selection_frame, state="readonly", width=30)
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Load AI models after GUI is ready
        self.root.after(500, self.load_ai_models)
            
    def setup_categories_panel(self, parent):
        """Setup categories selection panel with all photobanks."""
        categories_frame = ttk.LabelFrame(parent, text="Categories")
        categories_frame.pack(fill=tk.X, padx=5, pady=5)
        
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
        self.refresh_tags()
        
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
    
    def on_tags_frame_configure(self, event):
        """Update canvas scroll region when tags frame size changes."""
        self.tags_canvas.configure(scrollregion=self.tags_canvas.bbox("all"))
    
    def validate_keyword_input(self, event):
        """Validate input to only allow alfanumeric, dash, space, comma, semicolon."""
        # Allow these keys: alphanumeric, dash, space, comma, semicolon, backspace, delete, arrows
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-,; ')
        
        # Allow control keys
        control_keys = {'BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Return', 'Tab'}
        
        if event.keysym in control_keys:
            return  # Allow control keys
        
        if event.char and event.char not in allowed_chars:
            return 'break'  # Block the character
    
    def on_keyword_entry_change(self, event):
        """Handle real-time processing of keyword entry."""
        text = self.keyword_entry.get()
        # Check for separators: comma, semicolon
        separators = [',', ';']
        for sep in separators:
            if sep in text:
                self.process_keyword_entry()
                break
    
    def process_keyword_entry(self, event=None):
        """Process keywords from entry field and create tags."""
        text = self.keyword_entry.get().strip()
        if not text:
            return
            
        # Split by various separators
        keywords = []
        for sep in [',', ';']:
            if sep in text:
                keywords = [kw.strip() for kw in text.split(sep) if kw.strip()]
                break
        
        if not keywords:
            keywords = [text]
        
        # Add valid keywords
        for keyword in keywords:
            if len(keyword) > 2 and keyword not in self.keywords_list and len(self.keywords_list) < 50:
                self.keywords_list.append(keyword)
        
        # Clear entry
        self.keyword_entry.delete(0, tk.END)
        
        # Refresh tags display
        self.refresh_tags()
    
    def create_tag_widget(self, parent, keyword, index):
        """Create a draggable tag widget for a keyword."""
        tag_frame = ttk.Frame(parent, style='Tag.TFrame')
        
        # Configure tag style
        tag_frame.configure(relief='raised', borderwidth=1)
        
        # Keyword label
        keyword_label = ttk.Label(tag_frame, text=keyword)
        keyword_label.pack(side=tk.LEFT, padx=(3, 1), pady=2)
        
        # Remove button (X)
        remove_btn = ttk.Button(tag_frame, text="×", width=2, 
                               command=lambda: self.remove_tag(index))
        remove_btn.pack(side=tk.RIGHT, padx=(1, 3), pady=2)
        
        # Bind drag events to both frame and label
        for widget in [tag_frame, keyword_label]:
            widget.bind('<Button-1>', lambda e, idx=index: self.start_tag_drag(e, idx))
            widget.bind('<B1-Motion>', self.drag_tag)
            widget.bind('<ButtonRelease-1>', self.drop_tag)
        
        return tag_frame
    
    def refresh_tags(self):
        """Refresh the display of keyword tags."""
        # Clear existing widgets
        for widget in self.tag_widgets:
            widget.destroy()
        self.tag_widgets.clear()
        
        # Create new tag widgets
        row, col = 0, 0
        max_cols = 4  # Tags per row
        
        for i, keyword in enumerate(self.keywords_list):
            tag_widget = self.create_tag_widget(self.tags_frame, keyword, i)
            tag_widget.grid(row=row, column=col, padx=2, pady=2, sticky='w')
            self.tag_widgets.append(tag_widget)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Update counter
        self.update_keywords_counter()
        
        # Update canvas scroll region
        self.tags_frame.update_idletasks()
        self.tags_canvas.configure(scrollregion=self.tags_canvas.bbox("all"))
    
    def start_tag_drag(self, event, index):
        """Start dragging a tag."""
        self.drag_data = {'index': index, 'item': self.keywords_list[index]}
    
    def drag_tag(self, event):
        """Handle tag dragging (visual feedback could be added)."""
        pass
    
    def drop_tag(self, event):
        """Handle tag drop for reordering."""
        if self.drag_data.get('index') is not None:
            # Find drop target by checking widget positions
            source_index = self.drag_data['index']
            
            # Get mouse position relative to tags frame
            x = self.tags_canvas.canvasx(event.x)
            y = self.tags_canvas.canvasy(event.y)
            
            # Find closest tag position
            target_index = self.find_drop_target(x, y)
            
            if target_index is not None and target_index != source_index:
                # Move keyword in list
                keyword = self.keywords_list.pop(source_index)
                self.keywords_list.insert(target_index, keyword)
                
                # Refresh display
                self.refresh_tags()
        
        # Clear drag data
        self.drag_data = {}
    
    def find_drop_target(self, x, y):
        """Find the target index for dropping based on mouse position."""
        max_cols = 4
        tag_width = 80  # Approximate tag width
        tag_height = 25  # Approximate tag height
        
        col = max(0, int(x // tag_width))
        row = max(0, int(y // tag_height))
        
        target_index = row * max_cols + col
        return min(target_index, len(self.keywords_list) - 1) if self.keywords_list else 0
    
    def remove_tag(self, index):
        """Remove a keyword tag."""
        if 0 <= index < len(self.keywords_list):
            self.keywords_list.pop(index)
            self.refresh_tags()
    
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
        """Generate title using AI."""
        selected_model = self.model_combo.get()
        messagebox.showinfo("Info", f"Title generation with {selected_model} will be implemented later")
    
    def generate_description(self):
        """Generate description using AI."""
        selected_model = self.model_combo.get()
        messagebox.showinfo("Info", f"Description generation with {selected_model} will be implemented later")
    
    def generate_keywords(self):
        """Generate keywords using AI."""
        selected_model = self.model_combo.get()
        messagebox.showinfo("Info", f"Keywords generation with {selected_model} will be implemented later")
    
    def generate_categories(self):
        """Generate categories using AI."""
        selected_model = self.model_combo.get()
        messagebox.showinfo("Info", f"Categories generation with {selected_model} will be implemented later")
    
    def generate_all_metadata(self):
        """Generate all metadata using AI."""
        selected_model = self.model_combo.get()
        messagebox.showinfo("Info", f"Full metadata generation with {selected_model} will be implemented later")


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