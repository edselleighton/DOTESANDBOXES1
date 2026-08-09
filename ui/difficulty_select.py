from tkinter import Frame

from ui.components.back_button import BackButton
from ui.components.rounded_button import RoundedButton, RoundedPanel
from utils.constants import BG_COLOR, MENU_FRAME_COLOR


class DifficultySelect(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=MENU_FRAME_COLOR)
        self.manager = manager

        content = Frame(self, bg=BG_COLOR, width=974, height=621)
        content.place(x=13, y=53)

        panel = RoundedPanel(
            content,
            width=449,
            height=502,
            radius=67,
            bg=BG_COLOR,
            outline="white",
        )
        panel.place(x=263, y=59)

        button_positions = (("EASY", 33), ("MEDIUM", 192), ("HARD", 350))
        for difficulty, y_position in button_positions:
            RoundedButton(
                panel,
                text=difficulty,
                width=263,
                height=92,
                radius=13,
                font=("Comic Sans MS", 39),
                outline="white",
                command=lambda value=difficulty.lower(): manager.show_screen(
                    "GameScreen", mode="AI", difficulty=value
                )
            ).place(relx=0.5, y=y_position, anchor="n")

        BackButton(
            content,
            command=lambda: manager.show_screen("ModeSelect")
        ).place(x=13, y=555)

    def load(self, **kwargs):
        self.place(relwidth=1, relheight=1)

    def unload(self):
        self.place_forget()
