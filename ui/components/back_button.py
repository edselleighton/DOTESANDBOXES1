from tkinter import Button, TclError

from utils.assets import load_image

class BackButton(Button):
    def __init__(self, parent, command=None, **kwargs):
        kwargs.setdefault("bg", "black")
        kwargs.setdefault("activebackground", "black")
        kwargs.setdefault("bd", 0)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("cursor", "hand2")

        self.icon = None
        try:
            self.icon = load_image("back_button.png", (3, 3))
            kwargs["image"] = self.icon
        except (OSError, TclError):
            kwargs.setdefault("text", "<")
            kwargs.setdefault("fg", "white")
            kwargs.setdefault("font", ("Arial", 18, "bold"))

        super().__init__(parent, command=command, **kwargs)
