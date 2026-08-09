from tkinter import Button

class RoundedButton(Button):
    def __init__(self, parent, text="", command=None, width=15, **kwargs):
        kwargs.setdefault("fg", "white")
        kwargs.setdefault("bg", "black")
        kwargs.setdefault("activeforeground", "white")
        kwargs.setdefault("activebackground", "#202020")
        kwargs.setdefault("relief", "solid")
        kwargs.setdefault("bd", 1)
        kwargs.setdefault("cursor", "hand2")

        super().__init__(
            parent,
            text=text,
            command=command,
            font=("Comic Sans MS", 18),
            width=width,
            **kwargs
        )

