import tkinter as tk

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        self.id = self.widget.after(500, self._show_tooltip_after_delay)

    def _show_tooltip_after_delay(self):
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) # Remove window decorations
        self.tooltip_window.wm_geometry("+0+0") # Set a temporary geometry to allow winfo_width/height to work

        label = tk.Label(self.tooltip_window,
                         text=self.text,
                         background="#FFFFEA",
                         relief="solid",
                         borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(padx=1)

        # Force the tooltip window to update its geometry so winfo_width/height return correct values
        self.tooltip_window.update_idletasks()

        # Get widget's absolute position and size
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty()
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()

        # Calculate tooltip position (below the widget)
        tooltip_x = x
        tooltip_y = y + height + 5

        # Get screen dimensions
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        # Get tooltip dimensions
        tooltip_width = self.tooltip_window.winfo_width()
        tooltip_height = self.tooltip_window.winfo_height()

        # Adjust tooltip_x if it goes off-screen to the right
        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = screen_width - tooltip_width - 5 # 5 pixels padding from right edge

        # Adjust tooltip_y if it goes off-screen to the bottom
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = y - tooltip_height - 5 # Display above the widget if no space below

        # Ensure tooltip_x is not negative
        if tooltip_x < 0:
            tooltip_x = 0

        # Ensure tooltip_y is not negative
        if tooltip_y < 0:
            tooltip_y = 0

        self.tooltip_window.wm_geometry(f"{tooltip_width}x{tooltip_height}+{tooltip_x}+{tooltip_y}")

    def hide_tooltip(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
        self.id = None