"""Remember match setup, window, and display preferences in versioned settings."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile

from core.game_engine import MatchConfig


@dataclass(frozen=True)
class SetupChoices:
    mode: str = "AI"
    difficulty: str = "medium"
    player_one: str = "Player 1"
    player_two: str = "Player 2"

    def __post_init__(self):
        if self.difficulty not in ("easy", "medium", "hard"):
            raise ValueError("Unknown difficulty")
        MatchConfig(self.mode, self.difficulty, (self.player_one, self.player_two))
        if any(len(name) > 24 for name in (self.player_one, self.player_two)):
            raise ValueError("Player names must be 24 characters or fewer")

    def match_config(self):
        return MatchConfig(
            self.mode, self.difficulty if self.mode == "AI" else None,
            (self.player_one, "Computer" if self.mode == "AI" else self.player_two),
        )


@dataclass(frozen=True)
class WindowPreferences:
    fullscreen: bool = True
    maximized: bool = False
    width: int = 1180
    height: int = 780

    def __post_init__(self):
        if type(self.fullscreen) is not bool or type(self.maximized) is not bool:
            raise ValueError("Window modes must be boolean values")
        for value, minimum in ((self.width, 800), (self.height, 480)):
            if type(value) is not int or not minimum <= value <= 16384:
                raise ValueError("Window dimensions are outside the supported range")


class SetupStore:
    def __init__(self, path=None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
        self.path = Path(path) if path is not None else base / "DotsAndBoxes" / "settings.json"

    def _read(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) and data.get("version") == 1 else {}
        except (OSError, ValueError):
            return {}

    def load(self):
        try:
            data = self._read().get("setup", {})
            if not isinstance(data, dict):
                return SetupChoices()
            keys = ("mode", "difficulty", "player_one", "player_two")
            return SetupChoices(**{key: data[key] for key in keys if key in data})
        except (TypeError, ValueError):
            return SetupChoices()

    def save(self, choices: SetupChoices):
        return self._save_section("setup", asdict(choices))

    def load_window(self):
        try:
            data = self._read().get("window", {})
            if not isinstance(data, dict):
                return WindowPreferences()
            keys = ("fullscreen", "maximized", "width", "height")
            return WindowPreferences(**{key: data[key] for key in keys if key in data})
        except (TypeError, ValueError):
            return WindowPreferences()

    def save_window(self, preferences: WindowPreferences):
        return self._save_section("window", asdict(preferences))

    def load_reduced_motion(self, default: bool = False) -> bool:
        if type(default) is not bool:
            raise ValueError("Reduced motion default must be a boolean")
        display = self._read().get("display", {})
        value = display.get("reduced_motion") if isinstance(display, dict) else None
        return value if type(value) is bool else default

    def save_reduced_motion(self, enabled: bool) -> bool:
        if type(enabled) is not bool:
            return False
        return self._save_section("display", {"reduced_motion": enabled}, merge=True)

    def _save_section(self, section, values, *, merge=False):
        temporary = None
        try:
            data = self._read()
            data["version"] = 1
            if merge and isinstance(data.get(section), dict):
                values = {**data[section], **values}
            data[section] = values
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="settings-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, self.path)
            return True
        except OSError:
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
