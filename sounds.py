"""Sound effects + background music (ElevenLabs-generated files in sounds/). Usage: import sounds; sounds.play('shoot')"""
from pathlib import Path
from PyQt6.QtCore import QUrl, QElapsedTimer
from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput

_DIR = Path(__file__).parent / "assets"
_fx = {}
_music = {}


VOICES = 8     # copies of each sound that can overlap
RATE_MS = 55   # min gap between plays of the same sound (machine-gun speed)
_next = {}
_clock = {}


def preload(*names, volume=0.6):
    """Create the sound players up front so the first play() doesn't stall the game."""
    for name in names:
        _fx[name] = []
        for _ in range(VOICES):
            e = QSoundEffect()
            e.setSource(QUrl.fromLocalFile(str(_DIR / f"{name}.wav")))
            e.setVolume(volume)
            _fx[name].append(e)
        _next[name] = 0
        _clock[name] = QElapsedTimer()


def play(name, volume=0.6):
    """Play sounds/<name>.wav (shoot, explosion, player_hit, boss_hit).
    Safe to call every frame: plays at most once per RATE_MS, cycling through
    VOICES players so shots overlap instead of queuing up."""
    if name not in _fx:
        preload(name, volume=volume)
    clock = _clock[name]
    if clock.isValid() and clock.elapsed() < RATE_MS:
        return
    clock.start()
    e = _fx[name][_next[name]]
    _next[name] = (_next[name] + 1) % VOICES
    if e.isPlaying():
        e.stop()
    e.play()


def start_music(volume=0.35):
    """Loop sounds/bgm.mp3 forever. Call once after QApplication is created."""
    if "player" in _music:
        return
    out = QAudioOutput()
    out.setVolume(volume)
    p = QMediaPlayer()
    p.setAudioOutput(out)
    p.setSource(QUrl.fromLocalFile(str(_DIR / "bgm.mp3")))
    p.setLoops(QMediaPlayer.Loops.Infinite)
    p.play()
    _music.update(player=p, out=out)
