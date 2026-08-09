from tkinter import Frame

from ui.components.back_button import BackButton
from ui.components.rounded_button import RoundedButton, RoundedPanel
from utils.constants import BG_COLOR, MENU_FRAME_COLOR


class ModeSelect(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=MENU_FRAME_COLOR)
        self.manager = manager

        content = Frame(self, bg=BG_COLOR, width=974, height=621)
        content.place(x=13, y=53)

        panel = RoundedPanel(
            content,
            width=449,
            height=357,
            radius=52,
            bg=BG_COLOR,
            outline="white",
        )
        panel.place(x=263, y=119)

        RoundedButton(
            panel,
            text="VS. AI",
            width=308,
            height=92,
            radius=13,
            font=("Comic Sans MS", 39),
            outline="white",
            command=lambda: manager.show_screen("DifficultySelect")
        ).place(relx=0.5, y=53, anchor="n")

        RoundedButton(
            panel,
            text="VS. PLAYER",
            width=308,
            height=92,
            radius=13,
            font=("Comic Sans MS", 39),
            outline="white",
            command=lambda: manager.show_screen("GameScreen", mode="PVP")
        ).place(relx=0.5, y=198, anchor="n")

        BackButton(
            content,
            command=lambda: manager.show_screen("MainMenu")
        ).place(x=13, y=555)

    def load(self, **kwargs):
        self.place(relwidth=1, relheight=1)

    def unload(self):
        self.place_forget()
