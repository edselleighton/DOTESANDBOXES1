from tkinter import Frame, Label
from ui.components.rounded_button import RoundedButton
from utils.constants import BG_COLOR, MENU_FRAME_COLOR

class MainMenu(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=MENU_FRAME_COLOR)
        self.manager = manager

        content = Frame(self, bg=BG_COLOR, width=974, height=621)
        content.place(x=13, y=40)

        Label(
            content,
            text="DOTS AND BOXES",
            font=("Comic Sans MS", 74, "bold"),
            fg="white",
            bg=BG_COLOR
        ).place(relx=0.5, y=79, anchor="n")

        RoundedButton(
            content,
            text="START",
            width=199,
            height=92,
            radius=13,
            font=("Comic Sans MS", 39),
            outline="white",
            command=lambda: manager.show_screen("ModeSelect")
        ).place(relx=0.5, y=303, anchor="n")

        RoundedButton(
            content,
            text="EXIT",
            width=199,
            height=92,
            radius=13,
            font=("Comic Sans MS", 39),
            outline="white",
            command=self.quit
        ).place(relx=0.5, y=422, anchor="n")

    def load(self, **kwargs):
        self.place(relwidth=1, relheight=1)

    def unload(self):
        self.place_forget()
