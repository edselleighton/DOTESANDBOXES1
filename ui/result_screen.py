from tkinter import Frame, Label
from ui.components.back_button import BackButton
from ui.components.rounded_button import RoundedButton
from utils.assets import load_image
from utils.constants import BG_COLOR, BORDER_COLOR

class ResultScreen(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=0)
        self.manager = manager

        self.img_p1 = load_image("player_blue.png", (4, 4))
        self.img_p2 = load_image("player_red.png", (3, 3))
        self.img_ai = load_image("ai_icon.png", (4, 4))

        container = Frame(self, bg=BG_COLOR)
        container.pack(pady=(50, 20))

        self.lbl_winner_name = Label(container, text="PLAYER",
                                     font=("Comic Sans MS", 48, "bold"),
                                     fg="white", bg=BG_COLOR)
        self.lbl_winner_name.pack()

        self.lbl_wins_text = Label(container, text="WINS",
                                   font=("Comic Sans MS", 48, "bold"),
                                   fg="white", bg=BG_COLOR)
        self.lbl_wins_text.pack()

        score_frame = Frame(self, bg=BG_COLOR)
        score_frame.pack(pady=30)

        p1_panel = Frame(score_frame, bg=BG_COLOR)
        p1_panel.pack(side="left", padx=30)
        Label(p1_panel, image=self.img_p1, bg=BG_COLOR).pack(side="left", padx=5)
        self.lbl_p1_score = Label(p1_panel, text="", font=("Arial", 20, "bold"),
                                  fg="white", bg="#111111", width=5,
                                  highlightbackground="#888888",
                                  highlightthickness=1)
        self.lbl_p1_score.pack(side="left")

        p2_panel = Frame(score_frame, bg=BG_COLOR)
        p2_panel.pack(side="left", padx=30)
        self.p2_icon_label = Label(p2_panel, image=self.img_p2, bg=BG_COLOR)
        self.p2_icon_label.pack(side="left", padx=5)
        self.lbl_p2_score = Label(p2_panel, text="", font=("Arial", 20, "bold"),
                                  fg="white", bg="#111111", width=5,
                                  highlightbackground="#888888",
                                  highlightthickness=1)
        self.lbl_p2_score.pack(side="left")

        self.btn_play_again = RoundedButton(
            self, text="PLAY AGAIN", width=12,
            command=lambda: manager.show_screen("ModeSelect")
        )
        self.btn_play_again.pack(pady=50, ipadx=20, ipady=5)

        self.btn_back = BackButton(
            self,
            command=lambda: manager.show_screen("MainMenu")
        )

    def load(self, result_text="", p1_score=0, p2_score=0, mode=None, **kwargs):
        self.place(relwidth=1, relheight=1)
        self.btn_back.place(x=14, y=600)

        raw = str(result_text).upper()

        if mode == "AI" and "PLAYER 1" in raw:
            self.lbl_winner_name.config(text="YOU WIN")
            self.lbl_wins_text.config(text="")
        elif mode == "AI" and "PLAYER 2" in raw:
            self.lbl_winner_name.config(text="NICE TRY")
            self.lbl_wins_text.config(text="")
        elif "PLAYER 1" in raw:
            self.lbl_winner_name.config(text="PLAYER 1")
            self.lbl_wins_text.config(text="WINS")
        elif "PLAYER 2" in raw:
            self.lbl_winner_name.config(text="PLAYER 2")
            self.lbl_wins_text.config(text="WINS")
        else:
            self.lbl_winner_name.config(text="IT'S A")
            self.lbl_wins_text.config(text="TIE")

        self.lbl_p1_score.config(text=str(int(p1_score)))
        self.lbl_p2_score.config(text=str(int(p2_score)))
        self.p2_icon_label.config(image=self.img_ai if mode == "AI" else self.img_p2)

    def unload(self):
        self.place_forget()
        try: self.btn_back.place_forget()
        except: pass
