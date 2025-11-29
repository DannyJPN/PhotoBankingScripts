"""
UI component builders and helpers.

This module handles:
- UI component setup and configuration
- Style configuration
- Layout helpers
- Window utilities
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


def setup_ttk_styles() -> None:
    """
    Setup custom styles for UI components.
    """
    style = ttk.Style()

    # Configure tag frame style
    style.configure(
        'Tag.TFrame',
        background='lightblue',
        relief='raised',
        borderwidth=1
    )

    # Configure reject button style (red text)
    style.configure('Reject.TButton', foreground='red')


def create_labeled_frame(parent: tk.Widget, text: str) -> ttk.LabelFrame:
    """
    Create a labeled frame widget.

    :param parent: Parent widget
    :param text: Label text
    :return: Created LabelFrame widget
    """
    return ttk.LabelFrame(parent, text=text)


def create_label(
    parent: tk.Widget,
    text: str,
    anchor: Optional[str] = None,
    wraplength: Optional[int] = None,
    justify: Optional[str] = None
) -> ttk.Label:
    """
    Create a label widget.

    :param parent: Parent widget
    :param text: Label text
    :param anchor: Anchor position (e.g., tk.W, tk.CENTER)
    :param wraplength: Maximum line length before wrapping
    :param justify: Text justification (e.g., tk.LEFT)
    :return: Created Label widget
    """
    kwargs = {'text': text}
    if anchor is not None:
        kwargs['anchor'] = anchor
    if wraplength is not None:
        kwargs['wraplength'] = wraplength
    if justify is not None:
        kwargs['justify'] = justify

    return ttk.Label(parent, **kwargs)


def create_entry(parent: tk.Widget, width: Optional[int] = None) -> ttk.Entry:
    """
    Create an entry widget.

    :param parent: Parent widget
    :param width: Entry width in characters
    :return: Created Entry widget
    """
    kwargs = {}
    if width is not None:
        kwargs['width'] = width

    return ttk.Entry(parent, **kwargs)


def create_text(
    parent: tk.Widget,
    height: int = 5,
    width: int = 40,
    wrap: str = tk.WORD,
    font: Optional[tuple] = None
) -> tk.Text:
    """
    Create a text widget.

    :param parent: Parent widget
    :param height: Text height in lines
    :param width: Text width in characters
    :param wrap: Wrap mode (tk.WORD, tk.CHAR, tk.NONE)
    :param font: Font tuple (family, size)
    :return: Created Text widget
    """
    kwargs = {
        'height': height,
        'width': width,
        'wrap': wrap
    }
    if font is not None:
        kwargs['font'] = font

    return tk.Text(parent, **kwargs)


def create_button(
    parent: tk.Widget,
    text: str,
    command: Callable,
    style: Optional[str] = None
) -> ttk.Button:
    """
    Create a button widget.

    :param parent: Parent widget
    :param text: Button text
    :param command: Command to execute on click
    :param style: Style name (optional)
    :return: Created Button widget
    """
    kwargs = {
        'text': text,
        'command': command
    }
    if style is not None:
        kwargs['style'] = style

    return ttk.Button(parent, **kwargs)


def create_combobox(
    parent: tk.Widget,
    values: list,
    state: str = "readonly",
    width: Optional[int] = None
) -> ttk.Combobox:
    """
    Create a combobox widget.

    :param parent: Parent widget
    :param values: List of values for combobox
    :param state: Combobox state ('readonly', 'normal')
    :param width: Combobox width in characters
    :return: Created Combobox widget
    """
    kwargs = {
        'values': values,
        'state': state
    }
    if width is not None:
        kwargs['width'] = width

    return ttk.Combobox(parent, **kwargs)


def create_checkbutton(
    parent: tk.Widget,
    text: str,
    variable: tk.BooleanVar
) -> ttk.Checkbutton:
    """
    Create a checkbutton widget.

    :param parent: Parent widget
    :param text: Checkbutton text
    :param variable: BooleanVar to store value
    :return: Created Checkbutton widget
    """
    return ttk.Checkbutton(parent, text=text, variable=variable)


def create_scale(
    parent: tk.Widget,
    orient: str = tk.HORIZONTAL,
    from_: float = 0,
    to: float = 100,
    command: Optional[Callable] = None
) -> ttk.Scale:
    """
    Create a scale widget.

    :param parent: Parent widget
    :param orient: Orientation (tk.HORIZONTAL, tk.VERTICAL)
    :param from_: Minimum value
    :param to: Maximum value
    :param command: Command to execute on value change
    :return: Created Scale widget
    """
    kwargs = {
        'orient': orient,
        'from_': from_,
        'to': to
    }
    if command is not None:
        kwargs['command'] = command

    return ttk.Scale(parent, **kwargs)


def create_paned_window(parent: tk.Widget, orient: str = tk.HORIZONTAL) -> ttk.PanedWindow:
    """
    Create a paned window widget.

    :param parent: Parent widget
    :param orient: Orientation (tk.HORIZONTAL, tk.VERTICAL)
    :return: Created PanedWindow widget
    """
    return ttk.PanedWindow(parent, orient=orient)


def create_frame(parent: tk.Widget) -> ttk.Frame:
    """
    Create a frame widget.

    :param parent: Parent widget
    :return: Created Frame widget
    """
    return ttk.Frame(parent)


def bind_key_event(widget: tk.Widget, event: str, handler: Callable) -> None:
    """
    Bind a key event to a widget.

    :param widget: Widget to bind event to
    :param event: Event string (e.g., '<Return>', '<KeyRelease>')
    :param handler: Event handler function
    """
    widget.bind(event, handler)


def center_window(root: tk.Tk) -> None:
    """
    Center a window on the screen.

    :param root: Root window to center
    """
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")


def set_window_protocol(root: tk.Tk, protocol: str, handler: Callable) -> None:
    """
    Set window protocol handler (e.g., for close event).

    :param root: Root window
    :param protocol: Protocol name (e.g., "WM_DELETE_WINDOW")
    :param handler: Handler function
    """
    root.protocol(protocol, handler)


def pack_widget(
    widget: tk.Widget,
    side: Optional[str] = None,
    fill: Optional[str] = None,
    expand: Optional[bool] = None,
    padx: Optional[int] = None,
    pady: Optional[int] = None,
    anchor: Optional[str] = None
) -> None:
    """
    Pack a widget with specified options.

    :param widget: Widget to pack
    :param side: Side to pack on (tk.LEFT, tk.RIGHT, tk.TOP, tk.BOTTOM)
    :param fill: Fill direction (tk.X, tk.Y, tk.BOTH, tk.NONE)
    :param expand: Whether to expand to fill space
    :param padx: Horizontal padding
    :param pady: Vertical padding
    :param anchor: Anchor position
    """
    kwargs = {}
    if side is not None:
        kwargs['side'] = side
    if fill is not None:
        kwargs['fill'] = fill
    if expand is not None:
        kwargs['expand'] = expand
    if padx is not None:
        kwargs['padx'] = padx
    if pady is not None:
        kwargs['pady'] = pady
    if anchor is not None:
        kwargs['anchor'] = anchor

    widget.pack(**kwargs)


def configure_widget(widget: tk.Widget, **kwargs) -> None:
    """
    Configure widget properties.

    :param widget: Widget to configure
    :param kwargs: Properties to set
    """
    widget.configure(**kwargs)