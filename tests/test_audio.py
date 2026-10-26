import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from audio_support import FakeSound, quiet_audio
from core.game_engine import MatchConfig, Move
from ui.audio import AudioManager
from ui.qt_app import PaperClubWindow
from utils.assets import asset_path
from utils.setup_preferences import AudioPreferences, SetupChoices, SetupStore, WindowPreferences


class AudioPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SetupStore(Path(self.temp.name) / 'settings.json')

    def test_defaults_and_independent_values_round_trip_without_losing_other_sections(self):
        self.assertEqual(self.store.load_audio(), AudioPreferences(15, 50, False, False))
        self.store.save(SetupChoices('PVP', 'hard', 'Alex', 'Casey'))
        self.store.save_window(WindowPreferences(False))
        self.store.save_reduced_motion(True)
        self.store.save_stronger_contrast(True)
        values = AudioPreferences(23, 68, True, False)
        self.assertTrue(self.store.save_audio(values))
        reopened = SetupStore(self.store.path)
        self.assertEqual(reopened.load_audio(), values)
        self.assertTrue(reopened.load_reduced_motion())
        self.assertTrue(reopened.load_stronger_contrast())
        self.assertEqual(reopened.load().player_one, 'Alex')
        self.assertFalse(reopened.load_window().fullscreen)

    def test_corrupt_and_invalid_audio_data_uses_safe_defaults(self):
        for data in ('broken', '[]', '{"version":9}',
                     '{"version":1,"audio":[]}',
                     '{"version":1,"audio":{"music_volume":true}}',
                     '{"version":1,"audio":{"effects_volume":101}}',
                     '{"version":1,"audio":{"music_muted":"yes"}}'):
            self.store.path.write_text(data, encoding='utf-8')
            self.assertEqual(self.store.load_audio(), AudioPreferences())
        for values in ({'music_volume': -1}, {'effects_volume': 1.5}, {'music_muted': 1}):
            with self.assertRaises(ValueError):
                AudioPreferences(**values)

    def test_atomic_audio_failure_keeps_saved_data_and_cleans_temporary_files(self):
        original = AudioPreferences(70, 20, False, True)
        self.store.save_audio(original)
        with patch('utils.setup_preferences.os.replace', side_effect=PermissionError):
            self.assertFalse(self.store.save_audio(AudioPreferences()))
        self.assertEqual(self.store.load_audio(), original)
        self.assertFalse(list(self.store.path.parent.glob('*.tmp')))


class AudioPlaybackTests(unittest.TestCase):
    def create_audio(self, **kwargs):
        audio = AudioManager(AudioPreferences(), sound_factory=FakeSound,
                             output_available=kwargs.pop('output_available', lambda: True), **kwargs)
        self.addCleanup(audio.close)
        return audio

    def test_music_loops_and_music_mute_preserves_effects_and_volume(self):
        audio = self.create_audio()
        music = audio.sounds['music']
        self.assertFalse(music.isPlaying())
        audio.start()
        self.assertTrue(music.isPlaying())
        self.assertEqual(music.loops, QSoundEffect.Infinite.value)
        self.assertEqual(music.volume, .15)
        audio.set_preferences(AudioPreferences(37, 80, True, False))
        self.assertFalse(music.isPlaying())
        self.assertTrue(audio.play('capture'))
        self.assertEqual(audio.sounds['capture'].volume, .8)
        audio.set_preferences(AudioPreferences(37, 80, False, True))
        self.assertTrue(music.isPlaying())
        self.assertEqual(music.volume, .37)
        self.assertFalse(audio.play('capture'))

    def test_zero_volume_minimize_and_close_never_replay_old_effects(self):
        audio = self.create_audio()
        audio.start()
        self.assertTrue(audio.play('move'))
        audio.set_suspended(True)
        self.assertTrue(all(not s.isPlaying() for s in audio.sounds.values()))
        self.assertFalse(audio.play('result'))
        audio.set_suspended(False)
        self.assertTrue(audio.sounds['music'].isPlaying())
        self.assertEqual(audio.sounds['move'].play_count, 1)
        audio.set_preferences(AudioPreferences(0, 0))
        self.assertFalse(audio.sounds['music'].isPlaying())
        self.assertFalse(audio.play('menu'))
        audio.close()
        audio.start()
        audio.set_preferences(AudioPreferences())
        self.assertFalse(audio.play('result'))
        self.assertTrue(all(not s.isPlaying() for s in audio.sounds.values()))

    def test_absent_device_missing_file_and_decode_error_are_recoverable(self):
        output = [False]
        audio = self.create_audio(output_available=lambda: output[0])
        audio.start()
        self.assertIn('No audio output', audio.message)
        self.assertFalse(audio.play('move'))
        output[0] = True
        audio._refresh_status()
        self.assertTrue(audio.sounds['music'].isPlaying())
        audio.sounds['capture'].state = QSoundEffect.Status.Error
        audio.sounds['capture'].statusChanged.emit()
        self.assertIn('could not load', audio.message)
        self.assertFalse(audio.play('capture'))
        self.assertTrue(audio.play('move'))
        missing = self.create_audio(resolve_asset=lambda _: str(Path(tempfile.gettempdir()) / 'missing-paper-sound.wav'))
        self.assertIn('could not load', missing.message)
        missing.start()
        self.assertFalse(missing.play('result'))

    def test_bundled_audio_is_pcm_and_loop_has_no_boundary_click(self):
        for name in AudioManager.NAMES:
            with wave.open(asset_path(f'audio/{name}.wav'), 'rb') as stream:
                self.assertEqual((stream.getnchannels(), stream.getsampwidth(), stream.getframerate()), (1, 2, 22050))
                samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2') / 32768
            self.assertGreater(float(np.sqrt(np.mean(samples ** 2))), .02)
            self.assertLess(float(np.max(np.abs(samples))), .5)
            if name == 'music':
                self.assertEqual(len(samples), 24 * 22050)
                # A continuous waveform need not end at zero. Its wrap step
                # must remain within the ordinary changes between samples.
                steps = np.abs(np.diff(samples))
                self.assertLess(abs(float(samples[0] - samples[-1])), float(np.percentile(steps, 99)) * 1.5)
                self.assertLess(abs(float(samples[0] - 2 * samples[-1] + samples[-2])),
                                float(np.percentile(np.abs(np.diff(samples, n=2)), 99)) * 1.5)
            else:
                self.assertLess(abs(float(samples[0])), .001)
                self.assertLess(abs(float(samples[-1])), .001)


class AudioSettingsFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if os.name == 'nt':
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SetupStore(Path(self.temp.name) / 'settings.json')
        self.store.save_reduced_motion(True)
        self.audio = quiet_audio(self.store)
        self.window = PaperClubWindow(self.store, audio=self.audio)
        self.addCleanup(self.window.close)
        self.window.resize(1180, 780)
        self.window.show()
        self.app.processEvents()

    def test_keyboard_audio_controls_live_update_and_done_flushes_settings(self):
        self.window.show_settings()
        settings = self.window.settings
        settings.music_slider.setFocus()
        QTest.keyClick(settings.music_slider, Qt.Key.Key_Right)
        settings.effects_slider.setValue(72)
        settings.music_mute.setFocus()
        QTest.keyClick(settings.music_mute, Qt.Key.Key_Space)
        self.assertEqual(self.audio.preferences, AudioPreferences(16, 72, True, False))
        self.assertEqual(settings.music_value.text(), '16%')
        settings.sample_button.click()
        self.assertEqual(self.audio.sounds['capture'].play_count, 1)
        settings.effects_mute.setChecked(True)
        self.assertFalse(settings.sample_button.isEnabled())
        settings.sample_button.click()
        self.assertEqual(self.audio.sounds['capture'].play_count, 1)
        self.window.close_settings()
        self.assertEqual(self.store.load_audio(), AudioPreferences(16, 72, True, True))

    def test_sound_only_follows_valid_moves_captures_and_one_final_result(self):
        self.window.start_match(MatchConfig('PVP'))
        match = self.window.match
        first = Move('row', (0, 0))
        match.play_human(first)
        match.play_human(first)
        self.assertEqual(self.audio.sounds['move'].play_count, 1)
        for move in (Move('row', (0, 1)), Move('col', (0, 0)), Move('col', (1, 0))):
            match.play_human(move)
        self.assertEqual(self.audio.sounds['capture'].play_count, 1)
        self.window.show_settings()
        history = match.engine.history
        self.window.settings.music_mute.setChecked(True)
        self.window.close_settings()
        self.assertTrue(match.controller.paused)
        self.assertEqual(match.engine.history, history)
        self.window.resume_match()
        for edge, columns, rows in (('row', 5, 6), ('col', 6, 5)):
            for x in range(columns):
                for y in range(rows):
                    match.play_human(Move(edge, (x, y)))
        self.assertTrue(match.engine.finished)
        self.assertEqual(self.audio.sounds['result'].play_count, 1)
        match.controller.pause()
        self.assertEqual(self.audio.sounds['result'].play_count, 1)

    def test_stronger_contrast_persists_and_changes_open_edge_visibility_only(self):
        self.window.start_match(MatchConfig('PVP'))
        board = self.window.match.board
        move = Move('row', (2, 2))
        def edge_lightness():
            picture = board.grab()
            point = board.edge_center(move) * picture.devicePixelRatio()
            image = picture.toImage()
            # QPixmap contains physical pixels on high-DPI displays. Sample the
            # antialiased line around its center, not a logical-coordinate pixel.
            x, y = round(point.x()), round(point.y())
            return min(image.pixelColor(x + dx, y + dy).lightness()
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        before = edge_lightness()
        history = board.engine.history
        self.window.set_stronger_contrast(True)
        after = edge_lightness()
        self.assertLess(after, before - 20)
        self.assertTrue(self.store.load_stronger_contrast())
        self.assertEqual(board.engine.history, history)

    def test_new_settings_controls_remain_reachable_in_a_short_window(self):
        self.window.resize(800, 480)
        self.window.show_settings()
        self.app.processEvents()
        page = self.window.settings
        for control in (page.music_slider, page.effects_slider, page.music_mute,
                        page.effects_mute, page.sample_button, page.fullscreen,
                        page.reduced_motion, page.stronger_contrast):
            page.display_scroll.ensureWidgetVisible(control)
            control.setFocus()
            self.app.processEvents()
            center = control.mapTo(page.display_scroll.viewport(), control.rect().center())
            self.assertTrue(page.display_scroll.viewport().rect().contains(center))
            self.assertTrue(control.accessibleName() or control.text())
            self.assertGreaterEqual(control.height(), 44)
        self.assertTrue(page.done_button.isVisible())

    def test_minimizing_stops_audio_and_restoring_keeps_the_match_paused(self):
        self.window.start_match(MatchConfig('PVP'))
        self.window.match.play_human(Move('row', (0, 0)))
        count = self.audio.sounds['move'].play_count
        self.window.showMinimized()
        self.app.processEvents()
        self.assertTrue(self.audio.suspended)
        self.assertTrue(all(not sound.isPlaying() for sound in self.audio.sounds.values()))
        self.window.showNormal()
        self.app.processEvents()
        self.assertFalse(self.audio.suspended)
        self.assertTrue(self.audio.sounds['music'].isPlaying())
        self.assertEqual(self.audio.sounds['move'].play_count, count)
        self.assertTrue(self.window.match.controller.paused)


if __name__ == '__main__':
    unittest.main()
