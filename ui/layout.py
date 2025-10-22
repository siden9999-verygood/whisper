import tkinter as tk
from tkinter import ttk


class AppShell:
    """Application shell with a left sidebar and a right content area."""

    def __init__(self, root: tk.Tk, sidebar_width: int = 280):
        self.root = root
        self.container = ttk.Frame(root)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Grid with 2 columns: sidebar | content
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=0)
        self.container.grid_columnconfigure(1, weight=1)

        self.sidebar = ttk.Frame(self.container, width=sidebar_width)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_propagate(False)

        self.content = ttk.Frame(self.container)
        self.content.grid(row=0, column=1, sticky="nswe")

    def clear_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()

    def set_sidebar_visible(self, visible: bool = True):
        if visible:
            try:
                self.sidebar.grid()
                self.container.grid_columnconfigure(0, weight=0)
            except Exception:
                pass
        else:
            try:
                self.sidebar.grid_remove()
                # Let content take full width
                self.container.grid_columnconfigure(0, weight=0)
                self.container.grid_columnconfigure(1, weight=1)
            except Exception:
                pass
