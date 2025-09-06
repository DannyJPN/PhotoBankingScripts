"""
Editorial metadata input dialog for missing EXIF data.

This dialog collects missing editorial metadata (city, country, date)
when they cannot be extracted from image EXIF data.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Optional, Dict, Tuple
from datetime import datetime, date
import logging


class EditorialMetadataDialog:
    """Dialog for collecting missing editorial metadata."""
    
    def __init__(self, parent: tk.Tk, missing_fields: Dict[str, bool], existing_data: Optional[Dict[str, str]] = None):
        """
        Initialize editorial metadata dialog.
        
        Args:
            parent: Parent tkinter window
            missing_fields: Dict indicating which fields are missing (city, country, date)
            existing_data: Optional existing metadata values
        """
        self.parent = parent
        self.missing_fields = missing_fields
        self.existing_data = existing_data or {}
        self.result = None
        self.dialog = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create and configure the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Editorial Metadata Required")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.center_dialog()
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and explanation
        title_label = ttk.Label(main_frame, text="Editorial Content Metadata", 
                               font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        explanation = ("For editorial content, the following metadata is required "
                      "but could not be extracted from the image file:")
        explanation_label = ttk.Label(main_frame, text=explanation, 
                                     wraplength=350, justify=tk.LEFT)
        explanation_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Input fields frame
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.entries = {}
        row = 0
        
        # City field
        if self.missing_fields.get('city', False):
            ttk.Label(fields_frame, text="City:").grid(row=row, column=0, sticky=tk.W, pady=5)
            self.entries['city'] = ttk.Entry(fields_frame, width=30)
            self.entries['city'].grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
            if 'city' in self.existing_data:
                self.entries['city'].insert(0, self.existing_data['city'])
            row += 1
        
        # Country field
        if self.missing_fields.get('country', False):
            ttk.Label(fields_frame, text="Country:").grid(row=row, column=0, sticky=tk.W, pady=5)
            self.entries['country'] = ttk.Entry(fields_frame, width=30)
            self.entries['country'].grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
            if 'country' in self.existing_data:
                self.entries['country'].insert(0, self.existing_data['country'])
            else:
                # Default to Czech
                self.entries['country'].insert(0, "Czech")
            row += 1
        
        # Date field
        if self.missing_fields.get('date', False):
            ttk.Label(fields_frame, text="Date (DD MM YYYY):").grid(row=row, column=0, sticky=tk.W, pady=5)
            self.entries['date'] = ttk.Entry(fields_frame, width=30)
            self.entries['date'].grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
            
            # Default to today's date if no existing data
            if 'date' in self.existing_data:
                self.entries['date'].insert(0, self.existing_data['date'])
            else:
                today = date.today()
                self.entries['date'].insert(0, today.strftime("%d %m %Y"))
            row += 1
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        
        # Format example
        if self.missing_fields.get('date', False):
            example_frame = ttk.Frame(main_frame)
            example_frame.pack(fill=tk.X, pady=(0, 15))
            
            example_text = ("Example: For a photo taken on March 15, 2024 in Prague, Czech Republic,\n"
                           "the description will start with: \"PRAGUE, CZECH REPUBLIC - 15 03 2024:\"")
            example_label = ttk.Label(example_frame, text=example_text, 
                                     font=("Arial", 8), foreground="gray60",
                                     wraplength=350, justify=tk.LEFT)
            example_label.pack(anchor=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(buttons_frame, text="Cancel", 
                  command=self.on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(buttons_frame, text="OK", 
                  command=self.on_ok).pack(side=tk.RIGHT)
        
        # Focus on first entry
        if self.entries:
            first_entry = list(self.entries.values())[0]
            first_entry.focus()
        
        # Bind Enter key to OK
        self.dialog.bind('<Return>', lambda e: self.on_ok())
        self.dialog.bind('<Escape>', lambda e: self.on_cancel())
    
    def center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        
        # Get dialog size
        dialog_w = self.dialog.winfo_reqwidth()
        dialog_h = self.dialog.winfo_reqheight()
        
        # Calculate center position
        x = parent_x + (parent_w // 2) - (dialog_w // 2)
        y = parent_y + (parent_h // 2) - (dialog_h // 2)
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def on_ok(self):
        """Handle OK button click."""
        result = {}
        
        # Validate and collect input
        for field, entry in self.entries.items():
            value = entry.get().strip()
            
            if not value:
                messagebox.showerror("Missing Data", 
                                   f"Please enter a value for {field.title()}",
                                   parent=self.dialog)
                entry.focus()
                return
            
            # Special validation for date
            if field == 'date':
                if not self.validate_date_format(value):
                    messagebox.showerror("Invalid Date", 
                                       "Date must be in DD MM YYYY format (e.g., 15 03 2024)",
                                       parent=self.dialog)
                    entry.focus()
                    return
            
            result[field] = value
        
        self.result = result
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click."""
        self.result = None
        self.dialog.destroy()
    
    def validate_date_format(self, date_str: str) -> bool:
        """
        Validate date format (DD MM YYYY).
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid format
        """
        try:
            parts = date_str.strip().split()
            if len(parts) != 3:
                return False
            
            day, month, year = parts
            
            # Check if all parts are numeric
            if not (day.isdigit() and month.isdigit() and year.isdigit()):
                return False
            
            # Convert and validate ranges
            day_int = int(day)
            month_int = int(month)
            year_int = int(year)
            
            if not (1 <= day_int <= 31):
                return False
            if not (1 <= month_int <= 12):
                return False
            if not (1900 <= year_int <= 2100):
                return False
            
            # Try to create a valid date
            datetime(year_int, month_int, day_int)
            return True
            
        except (ValueError, TypeError):
            return False
    
    def show_and_get_result(self) -> Optional[Dict[str, str]]:
        """
        Show dialog and return result.
        
        Returns:
            Dict with collected metadata or None if cancelled
        """
        self.parent.wait_window(self.dialog)
        return self.result


def get_editorial_metadata(parent: tk.Tk, missing_fields: Dict[str, bool], 
                          existing_data: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
    """
    Show editorial metadata dialog and get user input.
    
    Args:
        parent: Parent tkinter window
        missing_fields: Dict indicating which fields are missing
        existing_data: Optional existing metadata values
        
    Returns:
        Dict with collected metadata or None if cancelled
    """
    dialog = EditorialMetadataDialog(parent, missing_fields, existing_data)
    return dialog.show_and_get_result()


def format_editorial_prefix(city: str, country: str, date_str: str) -> str:
    """
    Format editorial description prefix.
    
    Args:
        city: City name
        country: Country name
        date_str: Date in DD MM YYYY format
        
    Returns:
        Formatted prefix string
    """
    return f"{city.upper()}, {country.upper()} - {date_str}:"


def extract_editorial_metadata_from_exif(image_path: str) -> Tuple[Dict[str, str], Dict[str, bool]]:
    """
    Extract editorial metadata from image EXIF data.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (extracted_data, missing_fields)
    """
    extracted_data = {}
    missing_fields = {'city': True, 'country': True, 'date': True}
    
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            
            if exif_data:
                # Try to extract date
                date_taken = None
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    if tag == 'DateTime' and value:
                        try:
                            # Convert EXIF datetime to DD MM YYYY format
                            dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            date_taken = dt.strftime("%d %m %Y")
                            break
                        except ValueError:
                            continue
                
                if date_taken:
                    extracted_data['date'] = date_taken
                    missing_fields['date'] = False
                    logging.info(f"Extracted date from EXIF: {date_taken}")
    
    except Exception as e:
        logging.warning(f"Could not extract EXIF data from {image_path}: {e}")
    
    return extracted_data, missing_fields