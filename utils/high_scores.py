"""Persistent local high scores, kept apart from preferences.

Ranked records come only from matches that reach all 25 boxes. The one-box
instructions exercise is recorded separately and never reaches the ranked
table. Every record carries the match identifier that produced it, so a
repeated write cannot create a duplicate entry.
"""

from dataclasses import asdict, dataclass
from datetime import date
import json
import os
from pathlib import Path
import tempfile

TOTAL_BOXES = 25
CAPACITY = 10


def _valid_day(value):
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def today():
    return date.today().isoformat()


@dataclass(frozen=True)
class ScoreRecord:
    """One completed match, named for the player who claimed the most boxes."""

    match_id: str
    name: str
    boxes: int
    opponent: str
    opponent_boxes: int
    mode: str = "PVP"
    difficulty: str | None = None
    completed_on: str = ""

    def __post_init__(self):
        if not isinstance(self.match_id, str) or not self.match_id.strip():
            raise ValueError("A match identifier is required")
        for name in (self.name, self.opponent):
            if not isinstance(name, str) or not name.strip() or len(name) > 24:
                raise ValueError("Player names must be one to 24 characters")
        for value in (self.boxes, self.opponent_boxes):
            if type(value) is not int or not 0 <= value <= TOTAL_BOXES:
                raise ValueError("Box counts must be between zero and 25")
        if self.boxes + self.opponent_boxes != TOTAL_BOXES:
            raise ValueError("A completed match claims exactly 25 boxes")
        if self.boxes <= self.opponent_boxes:
            raise ValueError("A record names the player who claimed the most boxes")
        if self.mode not in ("PVP", "AI"):
            raise ValueError("Mode must be PVP or AI")
        if self.mode == "AI":
            if self.difficulty not in ("easy", "medium", "hard"):
                raise ValueError("A computer match records its difficulty")
        elif self.difficulty is not None:
            raise ValueError("A local match does not record a difficulty")
        if not _valid_day(self.completed_on):
            raise ValueError("A record needs an ISO completion date")

    @property
    def opponent_label(self):
        return (f"Computer ({self.difficulty})" if self.mode == "AI"
                else self.opponent)

    def _order(self):
        return (-self.boxes, self.opponent_boxes, self.completed_on, self.name)


@dataclass(frozen=True)
class PracticeRecord:
    """One finished run of the instructions exercise, measured in attempts."""

    match_id: str
    attempts: int
    completed_on: str = ""

    def __post_init__(self):
        if not isinstance(self.match_id, str) or not self.match_id.strip():
            raise ValueError("An exercise identifier is required")
        if type(self.attempts) is not int or not 1 <= self.attempts <= 999:
            raise ValueError("Attempts must be between one and 999")
        if not _valid_day(self.completed_on):
            raise ValueError("A record needs an ISO completion date")

    def _order(self):
        return (self.attempts, self.completed_on)


def match_record(match_id, config, scores, completed_on=None):
    """Build a ranked record from a finished match, or None if it is unfinished."""
    if sum(scores) != TOTAL_BOXES or scores[0] == scores[1]:
        return None
    winner = 0 if scores[0] > scores[1] else 1
    try:
        return ScoreRecord(
            match_id=match_id,
            name=config.player_names[winner],
            boxes=int(scores[winner]),
            opponent=config.player_names[1 - winner],
            opponent_boxes=int(scores[1 - winner]),
            mode=config.mode,
            difficulty=config.difficulty if config.mode == "AI" else None,
            completed_on=completed_on if completed_on is not None else today(),
        )
    except ValueError:
        return None


class HighScoreStore:
    """Versioned score file with atomic writes, beside the settings file."""

    SECTIONS = {"ranked": ScoreRecord, "practice": PracticeRecord}

    def __init__(self, path=None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
        self.path = Path(path) if path is not None else base / "DotsAndBoxes" / "scores.json"

    def _read(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) and data.get("version") == 1 else {}
        except (OSError, ValueError):
            return {}

    def _load(self, section):
        """Read one section, skipping rows that no longer satisfy the rules."""
        rows = self._read().get(section, [])
        if not isinstance(rows, list):
            return ()
        record_type = self.SECTIONS[section]
        fields = record_type.__dataclass_fields__
        records, seen = [], set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                record = record_type(**{key: row[key] for key in fields if key in row})
            except (TypeError, ValueError):
                continue
            if record.match_id in seen:
                continue
            seen.add(record.match_id)
            records.append(record)
        return tuple(sorted(records, key=lambda record: record._order())[:CAPACITY])

    def load_ranked(self):
        return self._load("ranked")

    def load_practice(self):
        return self._load("practice")

    def best_practice(self):
        records = self.load_practice()
        return records[0] if records else None

    def record_match(self, record: ScoreRecord):
        return self._record("ranked", record)

    def record_practice(self, record: PracticeRecord):
        return self._record("practice", record)

    def _record(self, section, record):
        """Add one record. A match identifier already present is left alone."""
        if not isinstance(record, self.SECTIONS[section]):
            return False
        existing = self._load(section)
        if any(kept.match_id == record.match_id for kept in existing):
            return True
        kept = sorted([*existing, record], key=lambda item: item._order())[:CAPACITY]
        return self._save(section, [asdict(item) for item in kept])

    def _save(self, section, rows):
        temporary = None
        try:
            data = self._read()
            data["version"] = 1
            data[section] = rows
            for name in self.SECTIONS:
                data.setdefault(name, [])
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="scores-", suffix=".tmp", delete=False) as stream:
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
