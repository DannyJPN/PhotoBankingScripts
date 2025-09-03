"""
Gmail-style tag entry widget for keyword input.

Provides a text entry field that converts text into removable tag chips,
similar to how Gmail or Outlook handles email addresses.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional


class TagEntry(tk.Frame):
    """
    Gmail-style tag entry widget.
    
    Acts like a normal text entry until user presses Enter, comma, or semicolon,
    then converts the text into a removable tag chip.
    """
    
    def __init__(self, parent, width: int = 60, height: int = 4, max_tags: int = 50,
                 separators: str = ',;', on_change: Optional[Callable] = None, **kwargs):
        """
        Initialize TagEntry widget.
        
        Args:
            parent: Parent widget
            width: Width in characters
            height: Height in lines
            max_tags: Maximum number of tags allowed
            separators: Characters that trigger tag creation
            on_change: Callback when tags change
            **kwargs: Additional widget options
        """
        super().__init__(parent, **kwargs)
        
        self.max_tags = max_tags
        self.separators = set(separators)
        self.on_change = on_change
        self._tags = []
        
        self.setup_ui(width, height)
        
    def setup_ui(self, width: int, height: int):
        """Setup the UI components."""
        # Main text widget that shows tags and allows input
        self.text_widget = tk.Text(self, width=width, height=height, wrap=tk.WORD,
                                  relief='sunken', borderwidth=1,
                                  font=('Arial', 9), state='normal')
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.text_widget.bind('<Key>', self.on_key)
        self.text_widget.bind('<Button-1>', self.on_click)
        self.text_widget.bind('<BackSpace>', self.on_backspace)
        self.text_widget.bind('<Delete>', self.on_delete)
        
        # Configure tags
        self.text_widget.tag_config('tag', background='lightblue', relief='raised',
                                   borderwidth=1, font=('Arial', 9, 'bold'))
        self.text_widget.tag_config('remove_btn', background='lightblue', foreground='darkred',
                                   font=('Arial', 8, 'bold'))
        
        self.refresh_display()
        
    def on_key(self, event):
        """Handle key presses."""
        # Get current cursor position and text
        cursor_pos = self.text_widget.index(tk.INSERT)
        current_line_text = self.text_widget.get(f"{cursor_pos.split('.')[0]}.0", 
                                                 f"{cursor_pos.split('.')[0]}.end")
        
        # Handle separators
        if event.char in self.separators:
            self.try_create_tag_from_cursor()
            return 'break'
            
        # Handle Enter
        if event.keysym == 'Return':
            self.try_create_tag_from_cursor()
            return 'break'
            
        # Allow only valid characters for tags
        if event.char and event.char.isprintable():
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ')
            if event.char not in allowed_chars:
                return 'break'
                
        return None  # Allow other keys
        
    def on_click(self, event):
        """Handle mouse clicks on tags."""
        # Get clicked position
        click_pos = self.text_widget.index(f"@{event.x},{event.y}")
        
        # Check if click is on a remove button
        tags_at_pos = self.text_widget.tag_names(click_pos)
        if 'remove_btn' in tags_at_pos:
            # Find which tag this remove button belongs to
            for i, tag_info in enumerate(self._get_tag_positions()):
                if (tag_info['remove_start'] <= click_pos <= tag_info['remove_end']):
                    self.remove_tag(i)
                    return 'break'
                    
        return None
        
    def on_backspace(self, event):
        """Handle backspace key."""
        cursor_pos = self.text_widget.index(tk.INSERT)
        
        # If cursor is at start of line and there are tags, remove last tag
        if cursor_pos.endswith('.0') and self._tags:
            # Check if we're at the end of tags
            tag_positions = self._get_tag_positions()
            if tag_positions:
                last_tag_end = tag_positions[-1]['tag_end']
                if cursor_pos <= last_tag_end:
                    self.remove_tag(len(self._tags) - 1)
                    return 'break'
                    
        return None
        
    def on_delete(self, event):
        """Handle delete key."""
        cursor_pos = self.text_widget.index(tk.INSERT)
        
        # If cursor is on a tag, remove it
        tags_at_pos = self.text_widget.tag_names(cursor_pos)
        if 'tag' in tags_at_pos:
            for i, tag_info in enumerate(self._get_tag_positions()):
                if tag_info['tag_start'] <= cursor_pos <= tag_info['tag_end']:
                    self.remove_tag(i)
                    return 'break'
                    
        return None
        
    def try_create_tag_from_cursor(self):
        """Try to create a tag from text before cursor."""
        cursor_pos = self.text_widget.index(tk.INSERT)
        line_num = cursor_pos.split('.')[0]
        col_num = int(cursor_pos.split('.')[1])
        
        # Get text from start of line to cursor
        line_start = f"{line_num}.0"
        text_before_cursor = self.text_widget.get(line_start, cursor_pos)
        
        # Find the last "word" (potential tag)
        words = text_before_cursor.strip().split()
        if words:
            potential_tag = words[-1].strip()
            if len(potential_tag) >= 2 and potential_tag not in self._tags and len(self._tags) < self.max_tags:
                # Add the tag
                self.add_tag(potential_tag)
                
    def add_tag(self, tag_text: str):
        """Add a new tag."""
        if len(tag_text) < 2 or tag_text in self._tags or len(self._tags) >= self.max_tags:
            return False
            
        self._tags.append(tag_text)
        self.refresh_display()
        
        if self.on_change:
            self.on_change()
            
        return True
        
    def remove_tag(self, index: int):
        """Remove a tag by index."""
        if 0 <= index < len(self._tags):
            del self._tags[index]
            self.refresh_display()
            
            if self.on_change:
                self.on_change()
                
    def get_tags(self) -> List[str]:
        """Get current list of tags."""
        return self._tags.copy()
        
    def set_tags(self, tags: List[str]):
        """Set the list of tags."""
        self._tags = []
        for tag in tags:
            if len(tag) >= 2 and len(self._tags) < self.max_tags:
                self._tags.append(tag)
                
        self.refresh_display()
        
        if self.on_change:
            self.on_change()
            
    def clear_tags(self):
        """Clear all tags."""
        self._tags.clear()
        self.refresh_display()
        
        if self.on_change:
            self.on_change()
            
    def refresh_display(self):
        """Refresh the display with current tags."""
        # Store current cursor position
        try:
            cursor_pos = self.text_widget.index(tk.INSERT)
        except tk.TclError:
            cursor_pos = '1.0'
            
        # Clear current content
        self.text_widget.delete('1.0', tk.END)
        
        current_pos = '1.0'
        
        # Add tags
        for i, tag in enumerate(self._tags):
            # Insert tag text
            tag_start = self.text_widget.index(tk.INSERT)
            self.text_widget.insert(tk.INSERT, f" {tag} ")
            tag_end = self.text_widget.index(tk.INSERT)
            
            # Insert remove button
            remove_start = self.text_widget.index(tk.INSERT)
            self.text_widget.insert(tk.INSERT, " × ")
            remove_end = self.text_widget.index(tk.INSERT)
            
            # Add space after
            self.text_widget.insert(tk.INSERT, " ")
            
            # Apply tag formatting
            self.text_widget.tag_add('tag', tag_start, tag_end)
            self.text_widget.tag_add('remove_btn', remove_start, remove_end)
            
        # Add input area
        input_start = self.text_widget.index(tk.INSERT)
        
        # Focus to input area
        self.text_widget.mark_set(tk.INSERT, input_start)
        self.text_widget.focus()
        
    def _get_tag_positions(self):
        """Get positions of all tags in the text widget."""
        positions = []
        content = self.text_widget.get('1.0', tk.END)
        
        for i, tag in enumerate(self._tags):
            # Find tag positions - this is simplified
            # In a real implementation, you'd track positions more precisely
            pass
            
        return positions
        
    def focus(self):
        """Focus the widget."""
        self.text_widget.focus()