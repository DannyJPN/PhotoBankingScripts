"""
Clean Listbox-style tag entry widget for keyword input.

Provides a listbox showing tags in rows with an entry field below for adding new tags.
Much cleaner and more professional than the previous text-based approach.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
import math


class TagEntry(tk.Frame):
    """
    Clean tag entry widget using Listbox + Entry field.
    
    Shows tags in a listbox with horizontal wrapping, 
    plus entry field for adding new tags.
    """
    
    def __init__(self, parent, width: int = 60, height: int = 4, max_tags: int = 50,
                 separators: str = ',;', on_change: Optional[Callable] = None, **kwargs):
        """
        Initialize TagEntry widget.
        
        Args:
            parent: Parent widget
            width: Width in characters  
            height: Height in lines (for listbox)
            max_tags: Maximum number of tags allowed
            separators: Characters that trigger tag creation
            on_change: Callback when tags change
            **kwargs: Additional widget options
        """
        super().__init__(parent, **kwargs)
        
        self.max_tags = max_tags
        self.separators = set(separators)
        self.on_change = on_change
        self._tags = []  # List of tag text strings
        
        self.setup_ui(width, height)
        
    def setup_ui(self, width: int, height: int):
        """Setup the UI components with C# ListBox style."""
        # Main container
        self.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for listbox and scrollbar
        listbox_frame = ttk.Frame(self)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Tags listbox with C# style - disable default selection behavior
        self.listbox = tk.Listbox(listbox_frame, 
                                 selectmode=tk.BROWSE,  # Single selection mode initially
                                 font=('Segoe UI', 9),
                                 relief='solid',
                                 borderwidth=1,
                                 bg='white',
                                 fg='black', 
                                 selectbackground='#0078d4',  # Windows blue
                                 selectforeground='white',
                                 activestyle='none',  # Disable dotted focus rectangle
                                 highlightthickness=0,  # Remove focus border
                                 exportselection=False)  # Keep selection when losing focus
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons frame (right side of listbox)
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Reordering buttons - all text
        self.up_button = ttk.Button(buttons_frame, text="Up", width=5, 
                                   command=self.move_up, state='disabled')
        self.up_button.pack(side=tk.LEFT, padx=(0, 2))
        
        self.down_button = ttk.Button(buttons_frame, text="Down", width=5,
                                     command=self.move_down, state='disabled')  
        self.down_button.pack(side=tk.LEFT, padx=(0, 2))
        
        self.top_button = ttk.Button(buttons_frame, text="Top", width=5,
                                    command=self.move_to_top, state='disabled')
        self.top_button.pack(side=tk.LEFT, padx=(0, 2))
        
        self.bottom_button = ttk.Button(buttons_frame, text="Bottom", width=6,
                                       command=self.move_to_bottom, state='disabled')
        self.bottom_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Edit/Delete buttons
        self.edit_button = ttk.Button(buttons_frame, text="Edit", width=6,
                                     command=self.edit_selected_tag, state='disabled')
        self.edit_button.pack(side=tk.LEFT, padx=(0, 2))
        
        self.delete_button = ttk.Button(buttons_frame, text="Delete", width=6, 
                                       command=self.remove_selected_tags, state='disabled')
        self.delete_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Counter and clear button
        self.counter_label = ttk.Label(buttons_frame, text="0/50")
        self.counter_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(buttons_frame, text="Clear All", width=8,
                                      command=self.clear_tags, state='disabled')  
        self.clear_button.pack(side=tk.RIGHT)
        
        # Bottom frame for entry and add
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X)
        
        # Entry field for new tags
        self.entry = tk.Entry(bottom_frame, 
                             font=('Segoe UI', 9),
                             relief='solid',
                             borderwidth=1)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Add button
        self.add_button = ttk.Button(bottom_frame, text="Add", width=8,
                                    command=self.add_tag_from_entry)
        self.add_button.pack(side=tk.RIGHT)
        
        # Bind events
        self.entry.bind('<Return>', self.on_entry_return)
        self.entry.bind('<KeyPress>', self.on_entry_key)
        self.listbox.bind('<Delete>', self.on_delete_key)
        self.listbox.bind('<BackSpace>', self.on_delete_key)
        self.listbox.bind('<Double-Button-1>', self.on_listbox_double_click)
        self.listbox.bind('<<ListboxSelect>>', self.on_selection_change)  # Selection change
        
        # Bind custom events - override default listbox behavior
        self.listbox.bind('<Button-1>', self.on_click)
        self.listbox.bind('<B1-Motion>', self.on_drag_motion)  
        self.listbox.bind('<ButtonRelease-1>', self.on_drag_end)
        
        # Drag state
        self._drag_start_index = None
        self._drag_active = False
        
        self.update_counter()
        self.update_button_states()
        
    def on_selection_change(self, event=None):
        """Handle listbox selection change - update button states."""
        self.update_button_states()
        
    def update_button_states(self):
        """Update button enabled/disabled states based on current selection and content."""
        selection = self.listbox.curselection()
        has_selection = len(selection) > 0
        has_tags = len(self._tags) > 0
        
        # All buttons require single selection only (simplified logic)
        if has_selection and len(selection) == 1:
            index = selection[0]
            total_tags = len(self._tags)
            
            # Position-based button states
            can_move_up = index > 0                    # Not first item
            can_move_down = index < total_tags - 1     # Not last item  
            can_move_to_top = index > 0                # Not first item
            can_move_to_bottom = index < total_tags - 1 # Not last item
            
            # All editing buttons active when item selected
            can_edit = True
            can_delete = True
        else:
            # No selection or invalid selection - disable all movement/edit buttons
            can_move_up = can_move_down = can_move_to_top = can_move_to_bottom = False
            can_edit = can_delete = False
        
        # Apply button states
        self.up_button.configure(state='normal' if can_move_up else 'disabled')
        self.down_button.configure(state='normal' if can_move_down else 'disabled')
        self.top_button.configure(state='normal' if can_move_to_top else 'disabled')
        self.bottom_button.configure(state='normal' if can_move_to_bottom else 'disabled')
        self.edit_button.configure(state='normal' if can_edit else 'disabled')
        self.delete_button.configure(state='normal' if can_delete else 'disabled')
        
        # Clear button - when there are any tags (independent of selection)
        self.clear_button.configure(state='normal' if has_tags else 'disabled')
        
    def on_entry_return(self, event):
        """Handle Enter key in entry field."""
        self.add_tag_from_entry()
        return 'break'
        
    def on_entry_key(self, event):
        """Handle key presses in entry field."""
        # Handle separators - add tag immediately
        if event.char in self.separators:
            self.add_tag_from_entry()
            return 'break'
            
        # Allow only valid characters for tags
        if event.char and event.char.isprintable():
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ')
            if event.char not in allowed_chars:
                return 'break'
                
        return None
        
    def on_delete_key(self, event):
        """Handle Delete/Backspace key in listbox."""
        self.remove_selected_tags()
        return 'break'
        
    def on_listbox_double_click(self, event):
        """Handle double-click on listbox item - edit tag."""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self._tags):
                tag_text = self._tags[index]
                # Remove tag and put text back in entry for editing
                del self._tags[index]
                self.refresh_listbox()
                self.update_counter()
                self.update_button_states()
                self.entry.delete(0, tk.END)
                self.entry.insert(0, tag_text)
                self.entry.focus()
                self.entry.select_range(0, tk.END)
                
                if self.on_change:
                    self.on_change()
        
    def add_tag_from_entry(self):
        """Add tag(s) from entry field."""
        text = self.entry.get().strip()
        if not text:
            return
            
        # Split by separators to handle multiple tags: "tag1,tag2;tag3"
        import re
        separator_pattern = '[' + ''.join(self.separators) + ']+'
        potential_tags = re.split(separator_pattern, text)
        
        # Add each valid tag
        added_any = False
        for tag_text in potential_tags:
            tag_text = tag_text.strip()
            if (len(tag_text) >= 2 and 
                tag_text not in self._tags and 
                len(self._tags) < self.max_tags):
                self._tags.append(tag_text)
                added_any = True
        
        if added_any:
            self.entry.delete(0, tk.END)
            self.refresh_listbox()
            self.update_counter()
            self.update_button_states()
            
            if self.on_change:
                self.on_change()
                
    def remove_selected_tags(self):
        """Remove selected tags from listbox."""
        selection = self.listbox.curselection()
        if not selection:
            return
            
        # Remove tags in reverse order to maintain indices
        for index in reversed(selection):
            if 0 <= index < len(self._tags):
                del self._tags[index]
                
        self.refresh_listbox()
        self.update_counter()
        self.update_button_states()
        
        if self.on_change:
            self.on_change()
            
    def refresh_listbox(self):
        """Refresh the listbox with current tags, showing order numbers."""
        self.listbox.delete(0, tk.END)
        for i, tag in enumerate(self._tags):
            # Add order number prefix to each tag
            display_text = f"{i+1:2d}. {tag}"
            self.listbox.insert(tk.END, display_text)
            
    def update_counter(self):
        """Update the tag counter."""
        count = len(self._tags)
        self.counter_label.configure(text=f"{count}/{self.max_tags}")
        if count >= self.max_tags:
            self.counter_label.configure(foreground='red')
        else:
            self.counter_label.configure(foreground='black')
    
    def add_tag(self, tag_text: str):
        """Add a new tag."""
        if (len(tag_text) >= 2 and 
            tag_text not in self._tags and 
            len(self._tags) < self.max_tags):
            self._tags.append(tag_text)
            self.refresh_listbox()
            self.update_counter()
            self.update_button_states()
            
            if self.on_change:
                self.on_change()
            return True
        return False
        
    def remove_tag(self, index: int):
        """Remove a tag by index."""
        if 0 <= index < len(self._tags):
            del self._tags[index]
            self.refresh_listbox()
            self.update_counter()
            self.update_button_states()
            
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
                
        self.refresh_listbox()
        self.update_counter()
        self.update_button_states()
        
        if self.on_change:
            self.on_change()
            
    def clear_tags(self):
        """Clear all tags."""
        self._tags.clear()
        self.refresh_listbox()
        self.update_counter()
        self.update_button_states()
        
        if self.on_change:
            self.on_change()
            
    def focus(self):
        """Focus the entry field."""
        self.entry.focus()
        
    def get_text(self) -> str:
        """Get all tags as comma-separated string."""
        return ', '.join(self._tags)
        
    def set_text(self, text: str):
        """Set tags from comma-separated string."""
        if text.strip():
            tags = [tag.strip() for tag in text.split(',') if tag.strip()]
            self.set_tags(tags)
        else:
            self.clear_tags()
            
    def on_click(self, event):
        """Handle click events - single selection only."""
        # Get clicked item index
        index = self.listbox.nearest(event.y)
        
        # Check if the click is actually on an item
        # listbox.nearest() returns closest index even for clicks in empty space
        listbox_height = self.listbox.winfo_height()
        item_count = len(self._tags)
        
        # Estimate item height (approximately)
        if item_count > 0:
            item_height = max(listbox_height // max(item_count, 1), 15)  # Minimum 15px per item
            max_item_y = item_count * item_height
            
            # Check if click is within actual items area
            if 0 <= index < len(self._tags) and event.y <= max_item_y:
                self._drag_start_index = index
                self._drag_start_pos = (event.x, event.y)
                self._drag_active = False  # Will be activated on motion if needed
                
                # Always single selection - no modifier keys
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                self.update_button_states()  # Explicitly update buttons
                return 'break'  # Prevent default behavior
        
        # If clicked outside items, clear selection
        self.listbox.selection_clear(0, tk.END)
        self.update_button_states()  # Explicitly update buttons
        return 'break'  # Prevent default behavior
            
    def on_drag_motion(self, event):
        """Handle drag motion - activate drag if moved enough."""
        if self._drag_start_index is None:
            return
            
        # Check if we've moved enough to start a drag operation (threshold)
        if not self._drag_active and hasattr(self, '_drag_start_pos'):
            dx = abs(event.x - self._drag_start_pos[0])
            dy = abs(event.y - self._drag_start_pos[1])
            # Only start drag if no modifier keys and moved enough
            if dx > 5 or dy > 5:
                if not (event.state & 0x4) and not (event.state & 0x1):  # No Ctrl or Shift
                    self._drag_active = True
                    
        if not self._drag_active:
            return
            
        # Get current position for visual feedback
        current_index = self.listbox.nearest(event.y)
        
        # Visual feedback could be added here (highlighting target position)
        # For now, just ensure we stay within bounds
        if current_index < 0:
            current_index = 0
        elif current_index >= len(self._tags):
            current_index = len(self._tags) - 1
            
    def on_drag_end(self, event):
        """Handle end of drag operation - reorder tags only if drag was active."""
        try:
            # Only perform drag operation if we actually started dragging
            if self._drag_active and self._drag_start_index is not None:
                # Get drop position
                drop_index = self.listbox.nearest(event.y)
                
                # Ensure valid drop position
                if drop_index < 0:
                    drop_index = 0
                elif drop_index >= len(self._tags):
                    drop_index = len(self._tags) - 1
                    
                # Only move if position changed
                if drop_index != self._drag_start_index:
                    # Move the tag
                    tag_to_move = self._tags.pop(self._drag_start_index)
                    self._tags.insert(drop_index, tag_to_move)
                    
                    # Refresh display
                    self.refresh_listbox()
                    
                    # Select the moved item at new position
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(drop_index)
                    self.update_button_states()
                    
                    # Notify of change
                    if self.on_change:
                        self.on_change()
                    
        finally:
            # Always reset drag state
            self._drag_active = False
            self._drag_start_index = None
            if hasattr(self, '_drag_start_pos'):
                delattr(self, '_drag_start_pos')
    
    
    def edit_selected_tag(self):
        """Edit the selected tag (same as double-click)."""
        selection = self.listbox.curselection()
        if selection:
            self.on_listbox_double_click(None)
    
    def move_up(self):
        """Move selected tag up by one position."""
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index > 0:
            # Swap with previous item
            self._tags[index], self._tags[index-1] = self._tags[index-1], self._tags[index]
            self.refresh_listbox()
            
            # Maintain selection and update button states
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index-1)
            self.update_button_states()
            
            if self.on_change:
                self.on_change()
    
    def move_down(self):
        """Move selected tag down by one position."""
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index < len(self._tags) - 1:
            # Swap with next item
            self._tags[index], self._tags[index+1] = self._tags[index+1], self._tags[index]
            self.refresh_listbox()
            
            # Maintain selection and update button states
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index+1)
            self.update_button_states()
            
            if self.on_change:
                self.on_change()
    
    def move_to_top(self):
        """Move selected tag to the top of the list."""
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index > 0:
            # Move to top
            tag_to_move = self._tags.pop(index)
            self._tags.insert(0, tag_to_move)
            self.refresh_listbox()
            
            # Select at new position and update button states
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.update_button_states()
            
            if self.on_change:
                self.on_change()
    
    def move_to_bottom(self):
        """Move selected tag to the bottom of the list."""
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index < len(self._tags) - 1:
            # Move to bottom
            tag_to_move = self._tags.pop(index)
            self._tags.append(tag_to_move)
            self.refresh_listbox()
            
            # Select at new position and update button states
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(len(self._tags) - 1)
            self.update_button_states()
            
            if self.on_change:
                self.on_change()