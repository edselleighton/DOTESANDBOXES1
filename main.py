import argparse

from tkinter import Tk
from ui.main_menu import MainMenu
from ui.mode_select import ModeSelect
from ui.difficulty_select import DifficultySelect
from ui.game_screen import GameScreen
from ui.result_screen import ResultScreen


class ScreenManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Dots and Boxes")
        self.root.geometry("1000x700")   # Window size
        self.root.configure(bg="black")

        # Storage for all screens
        self.screens = {}

        # Create all screens
        self.register_screens()

        # Show the first screen
        self.show_screen("MainMenu")

    def register_screens(self):
       
        self.screens["MainMenu"] = MainMenu(self.root, self)
        self.screens["ModeSelect"] = ModeSelect(self.root, self)
        self.screens["DifficultySelect"] = DifficultySelect(self.root, self)
        self.screens["GameScreen"] = GameScreen(self.root, self)
        self.screens["ResultScreen"] = ResultScreen(self.root, self)

        # start all screens hidden
        for scr in self.screens.values():
            # prefer unload if implemented, otherwise place_forget
            if hasattr(scr, "unload"):
                try:
                    scr.unload()
                except Exception:
                    scr.place_forget()
            else:
                scr.place_forget()

    def show_screen(self, name, **kwargs):
        """Switch to the selected screen properly."""

        for scr in self.screens.values():
            if hasattr(scr, "unload"):
                try:
                    scr.unload()
                except Exception:
                    scr.place_forget()
            else:
                scr.place_forget()

        screen = self.screens[name]
        screen.tkraise()

        if hasattr(screen, "load"):
            try:
                screen.load(**kwargs)
            except TypeError:
                screen.load()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Dots and Boxes desktop game")
    parser.add_argument("--paper-club", action="store_true",
                        help="Open the new Paper Club application shell")
    parser.add_argument("--mode", choices=("PVP", "AI"), help="Start a configured match")
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    parser.add_argument("--player-one", default="Player 1")
    parser.add_argument("--player-two", default="Player 2")
    args = parser.parse_args(argv)
    if args.paper_club and args.mode:
        parser.error("--paper-club cannot be combined with --mode")
    if args.difficulty and args.mode != "AI":
        parser.error("--difficulty requires --mode AI")
    if args.paper_club:
        from ui.qt_app import run
        return run()
    root = Tk()
    app = ScreenManager(root)
    if args.mode:
        app.show_screen("GameScreen", mode=args.mode, difficulty=args.difficulty,
                        player_names=(args.player_one, args.player_two))
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
