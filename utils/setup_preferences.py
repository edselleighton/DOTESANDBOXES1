"""Remember match setup in the shared versioned settings file."""

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
        temporary = None
        try:
            data = self._read()
            data.update(version=1, setup=asdict(choices))
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
