from tkinter import Frame, Label
from ui.components.rounded_button import RoundedButton
from utils.constants import BG_COLOR, BORDER_COLOR

class MainMenu(Frame):
    def __init__(self, parent, manager):
        super().__init__(
            parent,
            bg=BG_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=6
        )
        self.manager = manager

        Label(
            self,
            text="DOTS AND BOXES",
            font=("Comic Sans MS", 40, "bold"),
            fg="white",
            bg=BG_COLOR
        ).pack(pady=80)

        RoundedButton(
            self,
            text="START",
            width=15,
            command=lambda: manager.show_screen("ModeSelect")
        ).pack(pady=15)

        RoundedButton(
            self,
            text="EXIT",
            width=15,
            command=self.quit
        ).pack(pady=10)

    def load(self, **kwargs):
        self.place(relwidth=1, relheight=1)

    def unload(self):
        self.place_forget()
