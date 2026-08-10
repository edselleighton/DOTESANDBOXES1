from tkinter import Frame, Canvas, Label, Button
from ui.components.back_button import BackButton
from utils.assets import load_image
from utils.constants import BG_COLOR, BOARD_SIZE, MENU_FRAME_COLOR, SIDE_PANEL_COLOR
import numpy as np

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

        self.engine = None
        self.canvas.bind("<Button-1>", self._placeholder_click)

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

        Button(actions, image=self.img_hint, bg=SIDE_PANEL_COLOR, activebackground=SIDE_PANEL_COLOR,
               bd=0, highlightthickness=0, cursor="hand2",
               command=self.show_hint).pack(side="left", padx=12)

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
        self.undo_enabled = False

    def _placeholder_click(self, event):
        return "no-engine"

    def load(self, mode=None, difficulty=None, **kwargs):
        if self.engine is None:
            try:
                from core.game_engine import GameEngine
                self.engine = GameEngine(self.canvas)
            except Exception as e:
                print("[GameScreen] Error creating GameEngine:", e)
                self.engine = None

        if self.engine:
            self.canvas.unbind("<Button-1>")
            self.canvas.bind("<Button-1>", self.on_click)

        self.mode = mode
        self.difficulty = difficulty

        self.place(relwidth=1, relheight=1)

        if self.engine and hasattr(self.engine, "reset_game_state"):
            try:
                self.engine.reset_game_state()
            except Exception as e:
                print("[GameScreen] reset_game_state error:", e)

        if mode == "PVP" or mode is None:
            self.p2_icon_label.config(image=self.img_player2)
            self.undo_enabled = True
            self.undo_button.config(cursor="hand2")
        else:
            self.p2_icon_label.config(image=self.img_ai)
            self.undo_enabled = False
            self.undo_button.config(cursor="arrow")

        self.update_score_display()

    def unload(self):
        self.place_forget()

    def update_score_display(self):
        if not self.engine:
            return

        p1 = int(np.count_nonzero(self.engine.box_owner == 1))
        p2 = int(np.count_nonzero(self.engine.box_owner == 2))

        self.p1_score_label.config(text=str(p1))
        self.p2_score_label.config(text=str(p2))

    def show_hint(self):
        if not self.engine:
            return

        move = self.engine.get_hint()
        if move is None:
            return

        edge_type, pos = move
        self.engine.highlight_edge(edge_type, pos)
    
    def undo_move(self):
        if not self.engine or not self.undo_enabled:
            return
        
        result = self.engine.undo_move()
        if result:
            self.update_score_display()

    def run_ai_turn(self):
        if not self.engine:
            return

        while self.mode == "AI" and not self.engine.player1_turn:
            gameover = self.engine.ai_move(self.difficulty)

            self.update_score_display()
            if gameover:
                p1 = int(np.count_nonzero(self.engine.box_owner == 1))
                p2 = int(np.count_nonzero(self.engine.box_owner == 2))

                winner = "Winner: Player 1" if p1 > p2 else (
                        "Winner: Player 2" if p2 > p1 else "It's a tie")

                self.manager.show_screen("ResultScreen",
                                     result_text=winner,
                                     p1_score=p1,
                                     p2_score=p2,
                                     mode=self.mode)
                return

            if self.engine.player1_turn:
                break

    def on_click(self, event):
        if not self.engine:
            return

        try:
            result = self.engine.click(event)
        except Exception as e:
            print("[GameScreen] engine.click error:", e)
            result = None

        self.update_score_display()

        if self.mode == "AI" and not self.engine.player1_turn:
            self.after(300, self.run_ai_turn)

        if isinstance(result, dict):
            winner = result.get("result_text", "")
            p1 = int(result.get("player1_score", 0))
            p2 = int(result.get("player2_score", 0))

            self.manager.show_screen(
                "ResultScreen",
                result_text=winner,
                p1_score=p1,
                p2_score=p2,
                mode=self.mode
            )
            return
