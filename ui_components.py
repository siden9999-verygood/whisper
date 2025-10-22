from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class UITheme:
    """Lightweight theme and style presets for a modern look."""

    COLORS = {
        "bg": "#F7F8FA",
        "card": "#FFFFFF",
        "text": "#1F2937",
        "muted": "#6B7280",
        "border": "#E5E7EB",
        "accent": "#2563EB",
        "accent_fg": "#FFFFFF",
    }

    @classmethod
    def apply_style(cls, root: tk.Tk) -> None:
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        root.configure(bg=cls.COLORS["bg"])

        style.configure("TFrame", background=cls.COLORS["bg"])
        style.configure("TLabel", background=cls.COLORS["bg"], foreground=cls.COLORS["text"], font=("Arial", 10))
        style.configure("TButton", padding=(10, 6))

        # Accent button
        style.configure(
            "Accent.TButton",
            background=cls.COLORS["accent"],
            foreground=cls.COLORS["accent_fg"],
            bordercolor=cls.COLORS["accent"],
            focusthickness=1,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#1D4ED8")],
            foreground=[("disabled", "#D1D5DB")],
        )

        # Card style
        style.configure(
            "Card.TFrame",
            background=cls.COLORS["card"],
            bordercolor=cls.COLORS["border"],
            relief="solid",
            borderwidth=1,
        )

        # Toolbar style
        style.configure("Toolbar.TFrame", background=cls.COLORS["bg"])
        style.configure("ToolbarTitle.TLabel", font=("Arial", 12, "bold"))


class Toolbar:
    def __init__(self, parent: tk.Widget, title: Optional[str] = None):
        self.frame = ttk.Frame(parent, style="Toolbar.TFrame")
        self.frame.pack(fill=tk.X, pady=(0, 10))

        self.left = ttk.Frame(self.frame, style="Toolbar.TFrame")
        self.left.pack(side=tk.LEFT)

        self.right = ttk.Frame(self.frame, style="Toolbar.TFrame")
        self.right.pack(side=tk.RIGHT)

        if title:
            ttk.Label(self.left, text=title, style="ToolbarTitle.TLabel").pack(side=tk.LEFT)

    def add_button(self, text: str, command: Callable, accent: bool = False):
        style = "Accent.TButton" if accent else "TButton"
        btn = ttk.Button(self.right, text=text, command=command, style=style)
        btn.pack(side=tk.LEFT, padx=(8, 0))
        return btn


class Card:
    def __init__(self, parent: tk.Widget, padding: int = 10):
        outer = ttk.Frame(parent, style="Card.TFrame")
        outer.pack(fill=tk.X, pady=5, padx=5)
        # inner padding frame
        inner = ttk.Frame(outer, style="Card.TFrame")
        inner.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)
        self.frame = inner

    def add_title(self, text: str):
        ttk.Label(self.frame, text=text, font=("Arial", 10, "bold")).pack(anchor="w")


class Toast:
    @staticmethod
    def show(root: tk.Tk, message: str, duration: int = 2000):
        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.configure(bg="#111827")
        label = tk.Label(win, text=message, bg="#111827", fg="#F9FAFB", padx=12, pady=8)
        label.pack()

        win.update_idletasks()
        x = root.winfo_x() + root.winfo_width() - win.winfo_width() - 20
        y = root.winfo_y() + root.winfo_height() - win.winfo_height() - 40
        win.geometry(f"+{x}+{y}")
        win.after(duration, win.destroy)


class ConfirmDialog:
    @staticmethod
    def confirm(title: str, message: str) -> bool:
        from tkinter import messagebox

        return bool(messagebox.askyesno(title, message))


def compute_columns(width: int, min_card_width: int = 260, max_cols: int = 6) -> int:
    if width <= 0:
        return 1
    return max(1, min(max_cols, width // max(min_card_width, 1)))


class ProgressOverlay:
    """Lightweight progress overlay with optional cancel.

    Usage:
        ov = ProgressOverlay.show(root, "Processing...", on_cancel=callback)
        ov.update("Step 1/3", 33)
        ov.close()
    """

    def __init__(self, root: tk.Tk, message: str = "", on_cancel: Optional[Callable] = None):
        self.root = root
        self.on_cancel = on_cancel
        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.configure(bg="#000000")
        self.top.attributes("-alpha", 0.3)

        # Centered card
        self.card = tk.Toplevel(root)
        self.card.overrideredirect(True)
        self.card.attributes("-topmost", True)
        self.card.configure(bg="#111827")

        frame = ttk.Frame(self.card)
        frame.pack(padx=16, pady=16)
        self.label = ttk.Label(frame, text=message or "處理中...", foreground="#F9FAFB")
        self.label.pack()
        try:
            pb = ttk.Progressbar(frame, mode='determinate', length=260)
            pb.pack(pady=(8, 0))
            self.pb = pb
        except Exception:
            self.pb = None

        if on_cancel is not None:
            ttk.Button(frame, text="取消", command=self._cancel).pack(pady=(10, 0))

        self._reposition()
        self.root.bind('<Configure>', self._on_root_configure)

    def _reposition(self):
        # Cover root
        self.top.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_x()}+{self.root.winfo_y()}")
        # Center card
        cw, ch = 320, 120
        x = self.root.winfo_x() + (self.root.winfo_width() - cw) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - ch) // 2
        self.card.geometry(f"{cw}x{ch}+{x}+{y}")

    def _on_root_configure(self, _event=None):
        try:
            self._reposition()
        except Exception:
            pass

    def _cancel(self):
        if self.on_cancel:
            try:
                self.on_cancel()
            except Exception:
                pass

    def update(self, message: Optional[str] = None, progress: Optional[float] = None):
        if message is not None:
            self.label.config(text=message)
        if progress is not None and self.pb is not None:
            self.pb['value'] = max(0, min(100, float(progress)))

    @classmethod
    def show(cls, root: tk.Tk, message: str = "", on_cancel: Optional[Callable] = None) -> 'ProgressOverlay':
        return cls(root, message, on_cancel)

    def close(self):
        try:
            self.root.unbind('<Configure>')
        except Exception:
            pass
        try:
            self.card.destroy()
        except Exception:
            pass
        try:
            self.top.destroy()
        except Exception:
            pass


class ErrorDialog:
    """Simple modal error dialog with optional 'Open Logs' action."""

    @staticmethod
    def show(root: tk.Tk, title: str, message: str, on_open_logs: Optional[Callable] = None):
        win = tk.Toplevel(root)
        win.title(title or "錯誤")
        win.transient(root)
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=message, wraplength=420).pack(anchor='w')

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(12, 0))

        def _open_logs():
            if on_open_logs:
                try:
                    on_open_logs()
                except Exception:
                    pass

        if on_open_logs is not None:
            ttk.Button(btns, text="開啟日誌", command=_open_logs).pack(side=tk.LEFT)
        ttk.Button(btns, text="關閉", command=win.destroy).pack(side=tk.RIGHT)

        # center
        win.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() - win.winfo_width()) // 2
        y = root.winfo_y() + (root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")
