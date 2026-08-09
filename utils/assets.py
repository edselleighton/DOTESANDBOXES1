import base64
import sys
from pathlib import Path
from tkinter import PhotoImage


def asset_path(filename):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return str(root / "assets" / filename)


def load_image(filename, subsample=None):
    data = base64.b64encode(Path(asset_path(filename)).read_bytes())
    image = PhotoImage(data=data)
    return image.subsample(*subsample) if subsample else image

