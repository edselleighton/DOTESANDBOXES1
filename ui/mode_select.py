from tkinter import Frame

from ui.components.back_button import BackButton
from ui.components.rounded_button import RoundedButton, RoundedPanel
from utils.constants import BG_COLOR, BORDER_COLOR


class ModeSelect(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=BG_COLOR,
                         highlightbackground=BORDER_COLOR,
                         highlightthickness=6)
        self.manager = manager

        panel = RoundedPanel(self, width=350, height=270, bg=BG_COLOR)
        panel.place(relx=0.5, rely=0.5, anchor="center")

        RoundedButton(
            panel,
            text="VS. AI",
            width=15,
            command=lambda: manager.show_screen("DifficultySelect")
        ).place(relx=0.5, y=88, anchor="center")

        RoundedButton(
            panel,
            text="VS. PLAYER",
            width=15,
            command=lambda: manager.show_screen("GameScreen", mode="PVP")
        ).place(relx=0.5, y=176, anchor="center")

        BackButton(
            self,
            command=lambda: manager.show_screen("MainMenu")
        ).place(x=14, y=600)

    def load(self, **kwargs):
        self.place(relwidth=1, relheight=1)

    def unload(self):
        self.place_forget()
