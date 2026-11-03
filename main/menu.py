from pathlib import Path
import queue
import random
import shutil
import subprocess
import sys
import threading

import pygame
import qtawesome as qta
from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


ROOT = Path(__file__).resolve().parent
BACKGROUND_DIR = ROOT.parent / "assets" / "background"
SONGS_DIR = ROOT.parent / "assets" / "songs"
OPTIONS_DIR = ROOT.parent / "settings" / "options"

MENU_ITEMS = [
    ("Version orale", "version_orale.py"),
    ("Scan identité", "scan.py"),
    ("Tableau", "tableau.py"),
    ("Ajouter personne", "ajouter_personne.py"),
    ("Scan réseau", "scan_reseau.py"),
    ("Recherche", "recherche.py"),
    ("Aide", "aide.py"),
    ("Dev Space", "dev_space.py"),
]

OPTION_DESCRIPTIONS = {
    "version_orale.py": "Active ou désactive la lecture vocale des descriptions au survol des boutons.",
    "scan.py": "Ouvre le module de scan identité.",
    "tableau.py": "Ouvre le tableau de bord.",
    "ajouter_personne.py": "Ouvre le formulaire pour ajouter une personne.",
    "scan_reseau.py": "Ouvre le module de scan réseau.",
    "recherche.py": "Ouvre le module de recherche.",
    "aide.py": "Ouvre l'aide générale de l'application.",
    "dev_space.py": "Ouvre l'espace de développement.",
}


def get_background():
    if not BACKGROUND_DIR.exists():
        raise FileNotFoundError(f"Background introuvable : {BACKGROUND_DIR}")

    images = [
        path for path in BACKGROUND_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ]
    if not images:
        raise FileNotFoundError(f"Aucune image dans {BACKGROUND_DIR}")

    images.sort(key=lambda path: ("background" not in path.name.lower(), path.name.lower()))
    return QPixmap(str(images[0]))


class MusicPlayer:
    def __init__(self):
        self.songs = sorted(
            (path for path in SONGS_DIR.glob("*.mp3") if path.is_file()),
            key=lambda path: path.name.lower(),
        ) if SONGS_DIR.exists() else []
        self.history = []
        self.index = -1
        self.volume = 0.65
        self.playing = False
        self.available = False

    def start(self):
        if self.available or not self.songs or pygame.mixer.get_init() is None:
            return
        self.available = True
        pygame.mixer.music.set_volume(self.volume)
        self.next()

    def next(self):
        if not self.available:
            return
        choices = list(self.songs)
        current = self.history[self.index] if 0 <= self.index < len(self.history) else None
        if len(choices) > 1 and current in choices:
            choices.remove(current)
        song = random.choice(choices)
        self.history = self.history[:self.index + 1]
        self.history.append(song)
        self.index = len(self.history) - 1
        self.play(song)

    def previous(self):
        if self.available and self.index > 0:
            self.index -= 1
            self.play(self.history[self.index])

    def play(self, song):
        try:
            pygame.mixer.music.load(str(song))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            self.playing = True
        except pygame.error as error:
            print(f"[MUSIC] {error}")
            self.playing = False

    def toggle(self):
        if not self.available:
            return
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
        elif self.index >= 0:
            pygame.mixer.music.unpause()
            if not pygame.mixer.music.get_busy():
                self.play(self.history[self.index])
            else:
                self.playing = True
        else:
            self.next()

    def set_volume(self, value):
        self.volume = max(0.0, min(1.0, value))
        if self.available:
            pygame.mixer.music.set_volume(self.volume)

    def update(self):
        if self.available and self.playing and not pygame.mixer.music.get_busy():
            self.next()

    def stop(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()


class WindowsMasterVolume:
    def __init__(self):
        self.endpoint = None
        self.error = None
        self.com_error = None
        self.available = False

        if sys.platform != "win32":
            return

        try:
            from comtypes import COMError
            from pycaw.pycaw import AudioUtilities
        except ImportError as error:
            self.error = f"pycaw/comtypes indisponible : {error}"
            return

        self.com_error = COMError
        try:
            speakers = AudioUtilities.GetSpeakers()
            self.endpoint = speakers.EndpointVolume
            self.endpoint.GetMasterVolumeLevelScalar()
            self.available = True
        except (OSError, COMError) as error:
            self.error = f"Contrôle du volume Windows impossible : {error}"

    def get_state(self):
        if not self.available:
            return None
        try:
            level = self.endpoint.GetMasterVolumeLevelScalar()
            muted = bool(self.endpoint.GetMute())
            return level, muted
        except (OSError, self.com_error) as error:
            self.error = f"Lecture du volume Windows impossible : {error}"
            self.available = False
            return None

    def set_level(self, value):
        if not self.available:
            return False
        try:
            self.endpoint.SetMasterVolumeLevelScalar(value, None)
            self.endpoint.SetMute(value <= 0, None)
            return True
        except (OSError, self.com_error) as error:
            self.error = f"Réglage du volume Windows impossible : {error}"
            self.available = False
            return False


class IconButton(QPushButton):
    ICONS = {
        "play": "fa5s.play",
        "pause": "fa5s.pause",
        "previous": "fa5s.backward",
        "next": "fa5s.forward",
        "volume": "fa5s.volume-up",
        "muted": "fa5s.volume-mute",
    }

    def __init__(self, icon_name, tooltip, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.playing = False
        self.setObjectName("musicControl")
        self.setFixedSize(46, 46)
        self.setIconSize(QSize(18, 18))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        self.set_icon()

    def set_playing(self, playing):
        self.playing = playing
        self.setToolTip("Mettre la musique en pause" if playing else "Reprendre la musique")
        self.set_icon()

    def set_muted(self, muted):
        self.icon_name = "muted" if muted else "volume"
        self.setToolTip("Le son système est coupé" if muted else "Afficher le volume")
        self.set_icon()

    def set_icon(self):
        icon_name = self.icon_name
        if icon_name == "play" and self.playing:
            icon_name = "pause"
        self.setIcon(qta.icon(self.ICONS[icon_name], color="#ddd5ca"))


class VolumeSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setRange(0, 100)
        self.setFixedSize(190, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Volume de la musique")
        self.setToolTip("Régler le volume")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        start = 10.0
        end = self.width() - 10.0
        center_y = self.height() / 2 - 1
        knob_x = start + (end - start) * self.value() / self.maximum()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(230, 220, 205, 48))
        painter.drawRoundedRect(QRect(int(start), int(center_y - 2), int(end - start), 4), 2, 2)

        fill = QLinearGradient(start, 0, knob_x, 0)
        fill.setColorAt(0, QColor("#80634a"))
        fill.setColorAt(1, QColor("#f0c99b"))
        painter.setBrush(fill)
        painter.drawRoundedRect(
            QRect(int(start), int(center_y - 2), max(1, int(knob_x - start)), 4),
            2,
            2,
        )

        for tick in range(0, 101, 10):
            x = start + (end - start) * tick / 100
            painter.setBrush(QColor(238, 224, 207, 135 if tick <= self.value() else 48))
            painter.drawEllipse(QRect(int(x - 1), int(center_y + 8), 2, 2))

        halo = QRadialGradient(knob_x, center_y, 14)
        halo.setColorAt(0, QColor(239, 196, 148, 105))
        halo.setColorAt(1, QColor(239, 196, 148, 0))
        painter.setBrush(halo)
        painter.drawEllipse(QRect(int(knob_x - 14), int(center_y - 14), 28, 28))

        painter.setPen(QPen(QColor("#f5dec2"), 1.5))
        painter.setBrush(QColor("#211b17"))
        painter.drawEllipse(QRect(int(knob_x - 6), int(center_y - 6), 12, 12))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f2d3ad"))
        painter.drawEllipse(QRect(int(knob_x - 2), int(center_y - 2), 4, 4))
        painter.end()


class VoiceGuide:
    def __init__(self):
        self.enabled = False
        self.messages = queue.Queue()
        self.last_target = None
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def toggle(self):
        self.enabled = not self.enabled
        self.last_target = None
        message = "Version orale activée." if self.enabled else "Version orale désactivée."
        self.messages.put(message)

    def say(self, message):
        if not self.enabled:
            return
        try:
            while True:
                self.messages.get_nowait()
        except queue.Empty:
            pass
        self.messages.put(message)

    def hover(self, target, message):
        if self.enabled and target != self.last_target:
            self.last_target = target
            self.say(message)

    def _worker(self):
        engine = None
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
        except Exception:
            pass

        while True:
            message = self.messages.get()
            try:
                if engine is not None:
                    engine.say(message)
                    engine.runAndWait()
                elif sys.platform == "win32":
                    escaped = message.replace("'", "''")
                    script = (
                        "Add-Type -AssemblyName System.Speech; "
                        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                        f"$s.Speak('{escaped}')"
                    )
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                        check=False,
                    )
                elif sys.platform == "darwin" and shutil.which("say"):
                    subprocess.run(["say", message], check=False)
                elif shutil.which("espeak"):
                    subprocess.run(["espeak", "-v", "fr", message], check=False)
                elif shutil.which("espeak-ng"):
                    subprocess.run(["espeak-ng", "-v", "fr", message], check=False)
            except Exception as error:
                print(f"[VERSION ORALE] {error}")


class MenuOptionButton(QPushButton):
    hovered = Signal()
    left = Signal()

    def enterEvent(self, event):
        self.hovered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)


class MenuWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = get_background()
        self.voice = VoiceGuide()
        self.music = MusicPlayer()
        self.volume_controller = WindowsMasterVolume()
        self.music_started = False
        volume_state = self.volume_controller.get_state()
        self.system_volume_muted = False
        initial_volume = self.music.volume
        if volume_state is not None:
            initial_volume, self.system_volume_muted = volume_state
            if self.system_volume_muted:
                initial_volume = 0.0
            self.music.volume = 1.0

        self.setObjectName("menuPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(42, 30, 42, 0)
        top_bar.setSpacing(10)

        self.play_button = self._control_button("play", "Reprendre la musique")
        self.previous_button = self._control_button("previous", "Piste précédente")
        self.next_button = self._control_button("next", "Piste suivante")
        self.volume_button = self._control_button("volume", "Afficher le volume")
        self.volume_button.set_muted(self.system_volume_muted)
        self.play_button.clicked.connect(self.toggle_music)
        self.previous_button.clicked.connect(self.previous_track)
        self.next_button.clicked.connect(self.next_track)
        self.volume_button.clicked.connect(self.toggle_volume)
        for button in (
            self.play_button,
            self.previous_button,
            self.next_button,
            self.volume_button,
        ):
            top_bar.addWidget(button)

        self.volume_panel = QFrame()
        self.volume_panel.setObjectName("volumePanel")
        volume_layout = QHBoxLayout(self.volume_panel)
        volume_layout.setContentsMargins(12, 5, 12, 5)
        volume_layout.setSpacing(10)

        self.volume_title = QLabel(
            "SYSTÈME" if self.volume_controller.available else "MUSIQUE"
        )
        self.volume_title.setObjectName("volumeTitle")
        self.volume_title.setToolTip(
            "Volume général de Windows"
            if self.volume_controller.available
            else self.volume_controller.error or "Volume de la musique du menu"
        )
        volume_layout.addWidget(self.volume_title)

        self.volume_slider = VolumeSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setValue(round(initial_volume * 100))
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(self.volume_slider)

        self.volume_value = QLabel(f"{round(initial_volume * 100)}%")
        self.volume_value.setObjectName("volumeValue")
        self.volume_value.setMinimumWidth(38)
        self.volume_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        volume_layout.addWidget(self.volume_value)
        self.volume_panel.setVisible(False)
        top_bar.addWidget(self.volume_panel)
        top_bar.addStretch(1)
        root_layout.addLayout(top_bar)

        content = QHBoxLayout()
        content.setContentsMargins(0, 40, 8, 40)
        content.setSpacing(30)
        content.addStretch(3)

        left_column = QVBoxLayout()
        left_column.setSpacing(14)
        eyebrow = QLabel("by lupin")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("MENU")
        title.setObjectName("menuTitle")
        accent = QFrame()
        accent.setObjectName("accentLine")
        accent.setFixedSize(58, 2)
        subtitle = QLabel("Choisissez votre prochaine destination.")
        subtitle.setObjectName("subtitle")
        left_column.addStretch(1)
        left_column.addWidget(eyebrow)
        left_column.addWidget(title)
        left_column.addWidget(accent)
        left_column.addSpacing(6)
        left_column.addWidget(subtitle)
        left_column.addStretch(1)
        content.addLayout(left_column, 5)

        options = QVBoxLayout()
        options.setSpacing(5)
        self.option_buttons = []
        for label, filename in MENU_ITEMS:
            button = MenuOptionButton(label)
            button.setObjectName("menuOption")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(54)
            button.setProperty("filename", filename)
            button.hovered.connect(
                lambda current=filename, text=label: self.voice.hover(
                    current, OPTION_DESCRIPTIONS.get(current, text)
                )
            )
            button.left.connect(lambda: setattr(self.voice, "last_target", None))
            button.clicked.connect(
                lambda checked=False, current=filename: self.activate_option(current)
            )
            options.addWidget(button)
            self.option_buttons.append(button)
        options.addStretch(1)
        content.addLayout(options, 4)
        root_layout.addLayout(content, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(42, 0, 42, 28)
        footer.addWidget(QLabel("by lupin"))
        footer.addStretch(1)
        footer.addWidget(QLabel("ESC  ·  QUITTER"))
        root_layout.addLayout(footer)

        self.setStyleSheet("""
            QWidget#menuPage {
                color: #eee9df;
                font-family: "Segoe UI";
            }
            QLabel {
                background: transparent;
            }
            QLabel#eyebrow {
                color: #c3a17d;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 3px;
            }
            QLabel#menuTitle {
                color: #f4f0e9;
                font-family: Georgia;
                font-size: 64px;
                font-weight: 500;
                letter-spacing: 8px;
            }
            QFrame#accentLine {
                background: #b99268;
                border: none;
            }
            QLabel#subtitle {
                color: #b7b4af;
                font-size: 16px;
            }
            QPushButton#menuOption {
                color: #c4c0ba;
                background: rgba(8, 9, 12, 125);
                border: 1px solid rgba(220, 210, 195, 28);
                border-radius: 6px;
                padding: 0 20px;
                text-align: left;
                font-size: 17px;
            }
            QPushButton#menuOption:hover {
                color: #fff;
                background: rgba(177, 139, 99, 150);
                border: 1px solid rgba(225, 194, 158, 180);
                padding-left: 26px;
            }
            QPushButton#musicControl {
                color: #ddd5ca;
                background: rgba(10, 11, 14, 150);
                border: 1px solid rgba(220, 210, 195, 45);
                border-radius: 23px;
            }
            QPushButton#musicControl:hover {
                border-color: #b99268;
                background: rgba(177, 139, 99, 120);
            }
            QFrame#volumePanel {
                background: rgba(12, 13, 16, 218);
                border: 1px solid rgba(199, 160, 119, 105);
                border-radius: 12px;
            }
            QLabel#volumeTitle {
                color: #c3a17d;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 2px;
            }
            QLabel#volumeValue {
                color: #f0dfcc;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_music)
        self.update_timer.start(500)

    def _control_button(self, icon_name, tooltip):
        return IconButton(icon_name, tooltip, self)

    def toggle_music(self):
        self.music.toggle()
        self.play_button.set_playing(self.music.playing)

    def start_music(self):
        if self.music_started:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error as error:
            print(f"[MUSIC] Impossible d'initialiser le son : {error}")
            return
        if self.volume_controller.available:
            self.music.set_volume(1.0)
        self.music.start()
        self.music_started = True
        self.play_button.set_playing(self.music.playing)

    def previous_track(self):
        self.music.previous()
        self.play_button.set_playing(self.music.playing)

    def next_track(self):
        self.music.next()
        self.play_button.set_playing(self.music.playing)

    def toggle_volume(self):
        self.volume_panel.setVisible(not self.volume_panel.isVisible())

    def update_volume(self, value):
        level = value / 100
        if self.volume_controller.available:
            if self.volume_controller.set_level(level):
                self.system_volume_muted = value == 0
                self.volume_button.set_muted(self.system_volume_muted)
            else:
                self.volume_title.setText("MUSIQUE")
                self.volume_title.setToolTip(self.volume_controller.error)
                self.volume_controller.available = False
                self.music.set_volume(level)
        else:
            self.music.set_volume(level)
        self.volume_value.setText(f"{value}%")

    def update_music(self):
        self.music.update()
        self.play_button.set_playing(self.music.playing)

    def activate_option(self, filename):
        if filename == "version_orale.py":
            self.voice.toggle()
            button = self.option_buttons[0]
            button.setText(
                f"Version orale  ·  {'ACTIVÉE' if self.voice.enabled else 'DÉSACTIVÉE'}"
            )
            return

        target = (OPTIONS_DIR / filename).resolve()
        if target.parent != OPTIONS_DIR or target.suffix != ".py":
            QMessageBox.warning(self, "Option indisponible", "Chemin de module invalide.")
            return
        if not target.is_file():
            QMessageBox.information(
                self, "Option indisponible", f"Le module n'existe pas encore :\n{target.name}"
            )
            return

        try:
            subprocess.Popen([sys.executable, str(target)], cwd=str(ROOT))
        except OSError as error:
            QMessageBox.critical(
                self, "Erreur de lancement", f"Impossible de lancer {target.name} :\n{error}"
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self.background.isNull():
            scaled = self.background.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(
                self.rect(),
                scaled,
                QRect(x, y, self.width(), self.height()),
            )
        else:
            painter.fillRect(self.rect(), QColor("#101116"))

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(5, 6, 9, 225))
        gradient.setColorAt(0.45, QColor(5, 6, 9, 150))
        gradient.setColorAt(1, QColor(5, 6, 9, 185))
        painter.fillRect(self.rect(), gradient)
        painter.end()

    def closeEvent(self, event):
        self.update_timer.stop()
        self.music.stop()
        super().closeEvent(event)
