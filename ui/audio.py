"""Independent music/effect playback; failed audio never interrupts a match."""

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QMediaDevices, QSoundEffect

from utils.assets import asset_path


class AudioManager(QObject):
    status_changed = Signal(str)
    NAMES = ("music", "move", "capture", "menu", "result")

    def __init__(self, preferences, parent=None, *, sound_factory=QSoundEffect,
                 output_available=None, resolve_asset=asset_path):
        super().__init__(parent)
        self.preferences = preferences
        self.suspended = False
        self.started = False
        self.closed = False
        self.message = ""
        self.sounds = {}
        self._missing = set()
        self._devices = QMediaDevices(self) if output_available is None else None
        self._output_available = output_available or (lambda: bool(QMediaDevices.audioOutputs()))
        if self._devices:
            self._devices.audioOutputsChanged.connect(self._devices_changed)
        for name in self.NAMES:
            path = Path(resolve_asset(f"audio/{name}.wav"))
            if not path.is_file():
                self._missing.add(name)
                continue
            try:
                sound = sound_factory(self)
                self.sounds[name] = sound
                sound.setLoopCount(QSoundEffect.Infinite.value if name == "music" else 1)
                sound.statusChanged.connect(self._refresh_status)
                sound.setSource(QUrl.fromLocalFile(str(path)))
            except (OSError, RuntimeError):
                self._missing.add(name)
        self.set_preferences(preferences)
        self._refresh_status()

    def _devices_changed(self):
        # Rebind after headphones/output devices change. Nothing is queued for
        # later playback while output is absent or the window is minimized.
        device = QMediaDevices.defaultAudioOutput()
        for sound in self.sounds.values():
            sound.stop()
            sound.setAudioDevice(device)
        self._refresh_status()

    def _refresh_status(self):
        if not self._output_available():
            message = "No audio output is available. You can keep playing and change sound settings."
        elif self._missing or any(s.status() == QSoundEffect.Status.Error for s in self.sounds.values()):
            message = "Some sounds could not load. You can keep playing; available sounds still work."
        else:
            message = ""
        if message != self.message:
            self.message = message
            self.status_changed.emit(message)
        self._sync_music()

    def start(self):
        if not self.closed:
            self.started = True
            self._sync_music()

    def set_preferences(self, preferences):
        self.preferences = preferences
        for name, sound in self.sounds.items():
            music = name == "music"
            muted = preferences.music_muted if music else preferences.effects_muted
            volume = preferences.music_volume if music else preferences.effects_volume
            sound.setVolume(volume / 100)
            sound.setMuted(muted)
            if muted or volume == 0:
                sound.stop()
        self._sync_music()

    def _sync_music(self):
        sound = self.sounds.get("music")
        if sound is None:
            return
        allowed = (self.started and not self.closed and not self.suspended
                   and self._output_available() and not self.preferences.music_muted
                   and self.preferences.music_volume > 0)
        if not allowed:
            sound.stop()
        elif sound.status() == QSoundEffect.Status.Ready and not sound.isPlaying():
            sound.play()

    def play(self, name):
        sound = self.sounds.get(name)
        if (name == "music" or sound is None or self.closed or self.suspended
                or not self._output_available() or self.preferences.effects_muted
                or self.preferences.effects_volume == 0
                or sound.status() != QSoundEffect.Status.Ready):
            return False
        sound.play()
        return True

    def set_suspended(self, suspended):
        self.suspended = suspended
        if suspended:
            for sound in self.sounds.values():
                sound.stop()
        self._sync_music()

    def close(self):
        self.closed = True
        self.started = False
        for sound in self.sounds.values():
            sound.stop()
