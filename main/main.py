import sys
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QUrl
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

BASE_DIR = Path(__file__).resolve().parent
VIDEO_DIR = BASE_DIR.parent / "assets" / "videos"

sys.path.insert(0, str(BASE_DIR))
from menu import MenuWidget


class IntroWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lupin")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self.pages = QStackedWidget(self)
        self.video_page = QWidget()
        video_layout = QVBoxLayout(self.video_page)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
        video_layout.addWidget(self.video_widget)
        self.pages.addWidget(self.video_page)

        self.menu = MenuWidget()
        self.pages.addWidget(self.menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pages)

        self.transition_overlay = QLabel(self)
        self.transition_overlay.setStyleSheet("background: #05060b;")
        self.transition_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.transition_overlay.setGeometry(self.rect())
        self.transition_effect = QGraphicsOpacityEffect(self.transition_overlay)
        self.transition_effect.setOpacity(0)
        self.transition_overlay.setGraphicsEffect(self.transition_effect)
        self.transition_overlay.hide()

        self.transition_animation = QPropertyAnimation(
            self.transition_effect, b"opacity", self
        )
        self.transition_animation.setDuration(850)
        self.transition_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.transition_animation.finished.connect(self.finish_transition_phase)
        self.transitioning = False
        self.showing_menu = False

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.errorOccurred.connect(self.handle_media_error)

        self.video_files = self.find_video_files()
        self.showFullScreen()
        if self.video_files:
            self.pages.setCurrentWidget(self.video_page)
            self.player.setSource(QUrl.fromLocalFile(str(self.video_files[0])))
            self.player.play()
        else:
            self.pages.setCurrentWidget(self.menu)
            self.menu.start_music()

    def find_video_files(self):
        extensions = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
        if not VIDEO_DIR.exists():
            return []
        return sorted(
            (
                path for path in VIDEO_DIR.iterdir()
                if path.is_file() and path.suffix.lower() in extensions
            ),
            key=lambda path: path.name.lower(),
        )

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.begin_menu_transition()

    def handle_media_error(self, error, error_string):
        print(f"Erreur vidéo : {error_string}")
        self.begin_menu_transition()

    def begin_menu_transition(self):
        if self.transitioning:
            return
        self.transitioning = True
        self.player.stop()
        self.transition_overlay.setGeometry(self.rect())
        self.transition_overlay.show()
        self.transition_overlay.raise_()
        self.transition_effect.setOpacity(0)
        self.transition_animation.setStartValue(0)
        self.transition_animation.setEndValue(1)
        self.transition_animation.start()

    def finish_transition_phase(self):
        if not self.showing_menu:
            self.pages.setCurrentWidget(self.menu)
            self.showing_menu = True
            self.transition_animation.setStartValue(1)
            self.transition_animation.setEndValue(0)
            self.transition_animation.start()
            return

        self.transition_overlay.hide()
        self.transitioning = False
        self.menu.start_music()

    def resizeEvent(self, event):
        self.transition_overlay.setGeometry(self.rect())
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.pages.currentWidget() is self.menu and not self.transitioning:
                self.close()
            event.accept()
            return
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Lupin")
    window = IntroWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
