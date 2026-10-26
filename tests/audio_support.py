"""Silent, observable sound sink for desktop tests; no real speakers are used."""
from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import QSoundEffect

from ui.audio import AudioManager


class FakeSound(QObject):
    statusChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = QSoundEffect.Status.Ready
        self.playing = False
        self.play_count = 0
        self.volume = 0
        self.muted = False

    def setSource(self, source):
        self.source = source

    def setLoopCount(self, count):
        if type(count) is not int:
            raise TypeError("Loop count must be an integer")
        self.loops = count

    def setVolume(self, value):
        self.volume = value

    def setMuted(self, muted):
        self.muted = muted

    def status(self):
        return self.state

    def isPlaying(self):
        return self.playing

    def play(self):
        self.play_count += 1
        self.playing = True

    def stop(self):
        self.playing = False


def quiet_audio(store):
    return AudioManager(store.load_audio(), sound_factory=FakeSound, output_available=lambda: True)
