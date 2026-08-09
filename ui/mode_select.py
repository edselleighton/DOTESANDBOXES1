from tkinter import Frame

from ui.components.back_button import BackButton
from ui.components.rounded_button import RoundedButton
from utils.constants import BG_COLOR, BORDER_COLOR


class ModeSelect(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=BG_COLOR,
                         highlightbackground=BORDER_COLOR,
                         highlightthickness=6)
        self.manager = manager

        panel = Frame(self, bg=BG_COLOR, width=350, height=270,
                      highlightbackground="#555555", highlightthickness=1)
        panel.place(relx=0.5, rely=0.5, anchor="center")
        panel.pack_propagate(False)

        RoundedButton(
            panel,
            text="VS. AI",
            width=15,
            command=lambda: manager.show_screen("DifficultySelect")
        ).pack(pady=(55, 15))

        RoundedButton(
            panel,
            text="VS. PLAYER",
            width=15,
            command=lambda: manager.show_screen("GameScreen", mode="PVP")
        ).pack(pady=15)

        BackButton(
            self,
            command=lambda: manager.show_screen("MainMenu")
        ).place(x=14, y=640)

    def load(self, **kwargs):
        self.place(relwidth=1, relheight=1)

    def unload(self):
        self.place_forget()

