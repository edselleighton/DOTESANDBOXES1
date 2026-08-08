from tkinter import Frame, Canvas, Label, Button
from utils.constants import BG_COLOR, BORDER_COLOR
import numpy as np

class GameScreen(Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg=BG_COLOR,
                         highlightbackground=BORDER_COLOR,
                         highlightthickness=6)

        self.manager = manager

        self.canvas = Canvas(self, width=600, height=600, bg="white")
        self.canvas.pack(side="left", padx=30, pady=30)

        self.engine = None
        self.canvas.bind("<Button-1>", self._placeholder_click)

        self.right = Frame(self, bg=BG_COLOR, width=300)
        self.right.pack(side="right", fill="y", padx=10, pady=10)
        self.right.pack_propagate(False)
        self.right.configure(highlightbackground=BORDER_COLOR, highlightthickness=4)

        self.title = Label(self.right, text="Player vs Player",
                           fg="white", bg=BG_COLOR, font=("Comic Sans MS", 22),
                           wraplength=270, justify="center")
        self.title.pack(fill="x", padx=10, pady=15)

        self.turn_label = Label(self.right, text="", fg="white",
                                bg=BG_COLOR, font=("Comic Sans MS", 20))
        self.turn_label.pack(pady=15)

        score_frame = Frame(self.right, bg=BG_COLOR)
        score_frame.pack(pady=10)

        self.p1_score_label = Label(score_frame, text="P1: 0",
                                    fg="white", bg=BG_COLOR,
                                    font=("Comic Sans MS", 20))
        self.p1_score_label.pack(pady=5)

        self.p2_score_label = Label(score_frame, text="P2: 0",
                                    fg="white", bg=BG_COLOR,
                                    font=("Comic Sans MS", 20))
        self.p2_score_label.pack(pady=5)

        Button(self.right, text="HINT", font=("Comic Sans MS", 18), width=12,
               command=self.show_hint).pack(pady=10)

        self.undo_button = Button(self.right, text="UNDO", font=("Comic Sans MS", 18), width=12,
               command=self.undo_move)
        self.undo_button.pack(pady=10)

        Button(self.right, text="BACK", font=("Comic Sans MS", 18), width=12,
               command=lambda: manager.show_screen("ModeSelect")).pack(pady=40)

        self.mode = None
        self.difficulty = None

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
            self.title.config(text="Player vs Player")
            self.undo_button.config(state="normal")
        else:
            self.title.config(text=f"AI Mode: {difficulty.upper() if difficulty else 'EASY'}")
            self.undo_button.config(state="disabled")

        self.update_turn_label()
        self.update_score_display()

    def unload(self):
        self.place_forget()

    def update_score_display(self):
        if not self.engine:
            return

        p1 = int(np.count_nonzero(self.engine.box_owner == 1))
        p2 = int(np.count_nonzero(self.engine.box_owner == 2))

        self.p1_score_label.config(text=f"P1: {p1}")
        self.p2_score_label.config(text=f"P2: {p2}")

    def update_turn_label(self):
        if not self.engine:
            return

        player = 1 if self.engine.player1_turn else 2
        color = "#0492CF" if self.engine.player1_turn else "#EE4035"
        self.turn_label.config(text=f"Next turn: Player {player}", fg=color)

        self.canvas.delete("turn")
        self.engine.turntext_handle = None

    def show_hint(self):
        if not self.engine:
            return

        move = self.engine.get_hint()
        if move is None:
            return

        edge_type, pos = move
        self.engine.highlight_edge(edge_type, pos)
    
    def undo_move(self):
        if not self.engine:
            return
        
        result = self.engine.undo_move()
        if result:
            self.update_score_display()
            self.update_turn_label()

    def run_ai_turn(self):
        if not self.engine:
            return

        while self.mode == "AI" and not self.engine.player1_turn:
            gameover = self.engine.ai_move(self.difficulty)

            self.update_score_display()
            self.update_turn_label()
            if gameover:
                p1 = int(np.count_nonzero(self.engine.box_owner == 1))
                p2 = int(np.count_nonzero(self.engine.box_owner == 2))

                winner = "Winner: Player 1" if p1 > p2 else (
                        "Winner: Player 2" if p2 > p1 else "It's a tie")

                self.manager.show_screen("ResultScreen",
                                     result_text=winner,
                                     p1_score=p1,
                                     p2_score=p2)
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
                p2_score=p2
            )
            return

        self.update_turn_label()

