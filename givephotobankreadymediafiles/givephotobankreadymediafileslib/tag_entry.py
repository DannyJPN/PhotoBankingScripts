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
        
        # Entry state management
        self._edit_mode = False  # True when editing, False when adding
        self._edit_index = None  # Index of tag being edited
        
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
        self.up_button = ttk.Button(buttons_frame, text="Up", width=8,
                                   command=self.move_up, state='disabled')
        self.up_button.pack(side=tk.LEFT, padx=(0, 2))

        self.down_button = ttk.Button(buttons_frame, text="Down", width=8,
                                     command=self.move_down, state='disabled')
        self.down_button.pack(side=tk.LEFT, padx=(0, 2))

        self.top_button = ttk.Button(buttons_frame, text="Top", width=8,
                                    command=self.move_to_top, state='disabled')
        self.top_button.pack(side=tk.LEFT, padx=(0, 2))

        self.bottom_button = ttk.Button(buttons_frame, text="Bottom", width=8,
                                       command=self.move_to_bottom, state='disabled')
        self.bottom_button.pack(side=tk.LEFT, padx=(0, 10))

        # Edit/Delete buttons
        self.edit_button = ttk.Button(buttons_frame, text="Edit", width=8,
                                     command=self.start_edit_mode, state='disabled')
        self.edit_button.pack(side=tk.LEFT, padx=(0, 2))

        self.delete_button = ttk.Button(buttons_frame, text="Delete", width=8,
                                       command=self.remove_selected_tags, state='disabled')
        self.delete_button.pack(side=tk.LEFT, padx=(0, 10))

        # Counter and clear button
        self.counter_label = ttk.Label(buttons_frame, text="0/50")
        self.counter_label.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_button = ttk.Button(buttons_frame, text="Clear All", width=10,
                                      command=self.clear_tags, state='disabled')
        self.clear_button.pack(side=tk.RIGHT)
        
        # Bottom frame for entry and add
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X)
        
        # Entry field for new tags - starts disabled
        self.entry = tk.Entry(bottom_frame, 
                             font=('Segoe UI', 9),
                             relief='solid',
                             borderwidth=1,
                             state='disabled')
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Add button - now enables entry
        self.add_button = ttk.Button(bottom_frame, text="Add", width=10,
                                    command=self.start_add_mode)
        self.add_button.pack(side=tk.RIGHT)
        
        # Bind events
        self.entry.bind('<Return>', self.on_entry_return)
        self.entry.bind('<KeyPress>', self.on_entry_key)
        self.entry.bind('<Escape>', self.cancel_entry_mode)
        self.entry.bind('<FocusOut>', self.on_entry_focus_out)  # Auto-commit on focus loss
        self.listbox.bind('<Delete>', self.on_delete_key)
        self.listbox.bind('<BackSpace>', self.on_delete_key)
        self.listbox.bind('<Double-Button-1>', self.on_listbox_double_click)
        self.listbox.bind('<<ListboxSelect>>', self.on_selection_change)  # Selection change

        # Simplified click handling - no drag functionality
        self.listbox.bind('<Button-1>', self.on_click)
        
        self.update_counter()
        self.update_button_states()
        
    def on_selection_change(self, event=None):
        """Handle listbox selection change - cancel entry mode if active, then update button states."""
        # If entry is active and selection changed, cancel entry mode
        if self.entry['state'] != 'disabled':
            self.cancel_entry_mode()
        self.update_button_states()
        
    def update_button_states(self):
        """Update button enabled/disabled states based on current selection and content."""
        selection = self.listbox.curselection()
        has_selection = len(selection) > 0
        has_tags = len(self._tags) > 0
        entry_active = self.entry['state'] != 'disabled'
        
        # If entry is active (editing/adding mode), disable most buttons
        if entry_active:
            can_move_up = can_move_down = can_move_to_top = can_move_to_bottom = False
            can_edit = can_delete = can_clear = False
        else:
            # Normal mode - buttons based on selection
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
                
            # Clear button - when there are any tags (independent of selection)
            can_clear = has_tags
        
        # Apply button states
        self.up_button.configure(state='normal' if can_move_up else 'disabled')
        self.down_button.configure(state='normal' if can_move_down else 'disabled')
        self.top_button.configure(state='normal' if can_move_to_top else 'disabled')
        self.bottom_button.configure(state='normal' if can_move_to_bottom else 'disabled')
        self.edit_button.configure(state='normal' if can_edit else 'disabled')
        self.delete_button.configure(state='normal' if can_delete else 'disabled')
        self.clear_button.configure(state='normal' if can_clear else 'disabled')
        
    def on_entry_return(self, event):
        """Handle Enter key in entry field."""
        if self._edit_mode:
            self.confirm_edit()
        else:
            self.confirm_add()
        return 'break'

    def on_entry_focus_out(self, event):
        """Handle FocusOut event - auto-commit typed text."""
        # Only commit if entry is active (in add/edit mode)
        if self.entry['state'] == 'disabled':
            return

        # Get text before committing
        text = self.entry.get().strip()

        # Only commit if there's non-empty text
        if text:
            if self._edit_mode:
                self.confirm_edit()
            else:
                self.confirm_add()

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
        """Handle double-click on listbox item - same as Edit button."""
        self.start_edit_mode()
        
                
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
        """Focus the entry field - start add mode if disabled."""
        if self.entry['state'] == 'disabled':
            self.start_add_mode()
        else:
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
        """Handle click events - simplified without drag functionality."""
        # Get clicked item index first
        index = self.listbox.nearest(event.y)
        
        # Check current selection before making changes
        current_selection = self.listbox.curselection()
        current_index = current_selection[0] if current_selection else None
        
        # If entry is active and clicked on different item, cancel entry mode
        if (self.entry['state'] != 'disabled' and 
            0 <= index < len(self._tags) and 
            current_index != index):
            self.cancel_entry_mode()
            
        # If entry is active and clicked outside items, cancel entry mode  
        if (self.entry['state'] != 'disabled' and 
            not (0 <= index < len(self._tags))):
            self.cancel_entry_mode()
            
        # Simple bounds check - if valid index and within tags range
        if 0 <= index < len(self._tags):
            # Single selection
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
        else:
            # Clicked outside items, clear selection
            self.listbox.selection_clear(0, tk.END)
            
        self.update_button_states()
        return 'break'  # Prevent default behavior
            
    def start_add_mode(self):
        """Start add mode - enable entry for adding new tag."""
        self._edit_mode = False
        self._edit_index = None
        self.entry.configure(state='normal')
        self.entry.delete(0, tk.END)
        self.entry.focus()
        self.add_button.configure(text="Confirm", command=self.confirm_add)
        self.edit_button.configure(text="Cancel", command=self.cancel_entry_mode)
        self.update_button_states()
        
    def start_edit_mode(self):
        """Start edit mode - enable entry for editing selected tag."""
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if 0 <= index < len(self._tags):
            self._edit_mode = True
            self._edit_index = index
            tag_text = self._tags[index]
            
            self.entry.configure(state='normal')
            self.entry.delete(0, tk.END)
            self.entry.insert(0, tag_text)
            self.entry.focus()
            self.entry.select_range(0, tk.END)
            
            self.add_button.configure(text="Confirm", command=self.confirm_edit)
            self.edit_button.configure(text="Cancel", command=self.cancel_entry_mode)
            self.update_button_states()
            
    def cancel_entry_mode(self, event=None):
        """Cancel entry mode and return to normal state."""
        self._edit_mode = False
        self._edit_index = None
        self.entry.configure(state='disabled')
        self.entry.delete(0, tk.END)
        self.add_button.configure(text="Add", command=self.start_add_mode)
        self.edit_button.configure(text="Edit", command=self.start_edit_mode)
        self.update_button_states()
        
    def confirm_add(self):
        """Confirm adding new tag."""
        text = self.entry.get().strip()
        if not text:
            return
            
        # Split by separators to handle multiple tags
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
            self.refresh_listbox()
            self.update_counter()
            if self.on_change:
                self.on_change()
                
        self.cancel_entry_mode()
        
    def confirm_edit(self):
        """Confirm editing existing tag."""
        if self._edit_index is None or not self._edit_mode:
            return
            
        text = self.entry.get().strip()
        if not text or len(text) < 2:
            return
            
        # Check for duplicate (excluding the tag being edited)
        if text in self._tags[:self._edit_index] + self._tags[self._edit_index+1:]:
            return
            
        # Update the tag at the same position
        self._tags[self._edit_index] = text
        self.refresh_listbox()
        self.update_counter()
        
        # Maintain selection on the edited item
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self._edit_index)
        
        if self.on_change:
            self.on_change()
            
        self.cancel_entry_mode()

    def commit_pending_entry(self) -> None:
        """
        Commit any pending entry text before external save actions.

        This lets callers include unconfirmed text (e.g., on Save) without forcing UI interaction.
        """
        if self.entry['state'] == 'disabled':
            return

        text = self.entry.get().strip()
        if not text:
            return

        if self._edit_mode:
            self.confirm_edit()
        else:
            self.confirm_add()
    
    def edit_selected_tag(self):
        """Edit the selected tag - same as double-click."""
        self.start_edit_mode()
    
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
