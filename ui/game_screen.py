from tkinter import Frame, Canvas, Label, Button
from ui.components.back_button import BackButton
from utils.assets import load_image
from utils.constants import BG_COLOR, BOARD_SIZE, MENU_FRAME_COLOR, SIDE_PANEL_COLOR
from core.game_engine import GameEngine, MatchConfig
from core.match_controller import MatchController
from ui.tk_board import TkBoardRenderer

class GameScreen(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=MENU_FRAME_COLOR)

        self.manager = manager

        self.content = Frame(self, bg=BG_COLOR, width=984, height=632)
        self.content.place(x=6, y=32)
        self.content.pack_propagate(False)

        self.canvas = Canvas(
            self.content,
            width=BOARD_SIZE,
            height=BOARD_SIZE,
            bg="white",
            bd=0,
            highlightthickness=0,
        )
        self.canvas.place(x=95, y=37)

        self.engine = GameEngine()
        self.renderer = TkBoardRenderer(self.canvas, self.engine, BOARD_SIZE)
        self.canvas.bind("<Button-1>", self.on_click)

        self.right = Frame(self.content, bg=SIDE_PANEL_COLOR, width=260)
        self.right.place(x=694, y=23, width=260, height=584)
        self.right.pack_propagate(False)
        self.right.configure(highlightbackground="#DDDDDD", highlightthickness=1)

        self.img_player1 = load_image("player_blue.png", (3, 3))
        self.img_player2 = load_image("player_red.png").zoom(3, 3).subsample(7, 7)
        self.img_ai = load_image("ai_icon.png").zoom(2, 2).subsample(7, 7)
        self.img_hint = load_image("hint_button.png", (3, 3))
        self.img_undo = load_image("undo_button.png", (3, 3))

        score_frame = Frame(self.right, bg=SIDE_PANEL_COLOR)
        score_frame.pack(pady=(4, 10))

        p1_panel = Frame(score_frame, bg=SIDE_PANEL_COLOR)
        p1_panel.pack(pady=8)
        Label(p1_panel, image=self.img_player1, bg=SIDE_PANEL_COLOR).pack(side="left", padx=8)
        self.p1_score_label = Label(p1_panel, text="0",
                                    fg="white", bg=SIDE_PANEL_COLOR, width=3,
                                    font=("Comic Sans MS", 18),
                                    highlightbackground="#888888",
                                    highlightthickness=1, bd=0)
        self.p1_score_label.pack(side="left", padx=8)

        p2_panel = Frame(score_frame, bg=SIDE_PANEL_COLOR)
        p2_panel.pack(pady=8)
        self.p2_icon_label = Label(p2_panel, image=self.img_player2, bg=SIDE_PANEL_COLOR)
        self.p2_icon_label.pack(side="left", padx=8)
        self.p2_score_label = Label(p2_panel, text="0",
                                    fg="white", bg=SIDE_PANEL_COLOR, width=3,
                                    font=("Comic Sans MS", 18),
                                    highlightbackground="#888888",
                                    highlightthickness=1, bd=0)
        self.p2_score_label.pack(side="left", padx=8)

        actions = Frame(self.right, bg=SIDE_PANEL_COLOR)
        actions.pack(side="bottom", pady=5)

        self.hint_button = Button(actions, image=self.img_hint, bg=SIDE_PANEL_COLOR, activebackground=SIDE_PANEL_COLOR,
               bd=0, highlightthickness=0, cursor="hand2",
               command=self.show_hint)
        self.hint_button.pack(side="left", padx=12)

        self.undo_button = Button(
            actions, image=self.img_undo, bg=SIDE_PANEL_COLOR, activebackground=SIDE_PANEL_COLOR,
            bd=0, highlightthickness=0, cursor="hand2", command=self.undo_move
        )
        self.undo_button.pack(side="left", padx=12)

        BackButton(
            self.content,
            command=lambda: manager.show_screen("ModeSelect")
        ).place(x=18, y=544)

        self.mode = None
        self.difficulty = None
        self.controller = MatchController(
            self.engine, self.after, self.after_cancel,
            self.on_move, self.on_finished,
        )

    def load(self, mode=None, difficulty=None, **kwargs):
        self.mode = mode or "PVP"
        self.difficulty = difficulty
        self.p2_icon_label.config(
            image=self.img_ai if self.mode == "AI" else self.img_player2
        )
        self.place(relwidth=1, relheight=1)
        self.controller.start(MatchConfig(mode=self.mode, difficulty=difficulty))

    def unload(self):
        self.controller.stop()
        self.place_forget()

    def on_move(self, outcome):
        self.renderer.render()
        p1, p2 = self.engine.scores
        self.p1_score_label.config(text=str(p1))
        self.p2_score_label.config(text=str(p2))
        self.undo_button.config(
            state="normal" if self.controller.can_undo else "disabled",
            cursor="hand2" if self.controller.can_undo else "arrow",
        )
        self.hint_button.config(
            state="normal" if self.controller.accepts_human_move else "disabled"
        )

    def on_finished(self, outcome):
        p1, p2 = outcome.scores
        winner = "Winner: Player 1" if p1 > p2 else (
            "Winner: Player 2" if p2 > p1 else "It's a tie"
        )
        self.manager.show_screen(
            "ResultScreen", result_text=winner,
            p1_score=p1, p2_score=p2, mode=self.mode,
        )

    def show_hint(self):
        move = self.controller.get_hint()
        if move is not None:
            self.renderer.highlight(move)

    def undo_move(self):
        return self.controller.undo_move()

    def on_click(self, event):
        move = self.renderer.geometry.hit_test(event.x, event.y)
        if move is not None:
            self.controller.play_human(move)
