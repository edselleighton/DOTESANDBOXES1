from tkinter import Frame

from ui.components.back_button import BackButton
from ui.components.rounded_button import RoundedButton, RoundedPanel
from utils.constants import BG_COLOR, BORDER_COLOR


class DifficultySelect(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=BG_COLOR,
                         highlightbackground=BORDER_COLOR,
                         highlightthickness=6)
        self.manager = manager

        panel = RoundedPanel(self, width=350, height=330, bg=BG_COLOR)
        panel.place(relx=0.5, rely=0.5, anchor="center")

        for index, difficulty in enumerate(("EASY", "MEDIUM", "HARD")):
            RoundedButton(
                panel,
                text=difficulty,
                width=15,
                command=lambda value=difficulty.lower(): manager.show_screen(
                    "GameScreen", mode="AI", difficulty=value
                )
            ).place(relx=0.5, y=76 + index * 90, anchor="center")

        BackButton(
            self,
            command=lambda: manager.show_screen("ModeSelect")
        ).place(x=14, y=600)

    def load(self, **kwargs):
        self.place(relwidth=1, relheight=1)

    def unload(self):
        self.place_forget()
