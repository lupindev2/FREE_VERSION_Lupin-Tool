import sys
import json
import math
import uuid
import random
from pathlib import Path

from PySide6.QtCore import (
    Qt, QUrl, QTimer, QPointF, QRectF,
    QPropertyAnimation, QEasingCurve, Signal
)
from PySide6.QtGui import (
    QColor, QPen, QBrush, QFont, QPainter,
    QPixmap, QPainterPath, QAction, QKeySequence,
    QRadialGradient, QIcon, QLinearGradient
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsPathItem,
    QGraphicsItem, QLineEdit, QTextEdit, QComboBox,
    QFileDialog, QMessageBox, QFrame, QSplitter,
    QGraphicsTextItem, QGraphicsDropShadowEffect,
    QColorDialog, QToolButton, QSizePolicy
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


BASE_DIR = Path(__file__).resolve().parent
VIDEO_PATH = (BASE_DIR / "../../assets/videos/videoB2.mp4").resolve()
AUTOSAVE_PATH = BASE_DIR / "autosave_enquete.json"

STATES = ["témoin", "suspect", "victime", "indice", "lieu"]

COLORS = {
    "témoin": "#558FDC",
    "suspect": "#C32D2D",
    "victime": "#AF5FBE",
    "indice": "#D7AF41",
    "lieu": "#5AA06E",
}

BLACK = "#000000"
PANEL = "#080808"
BORDER = "#242424"
WHITE = "#EAEAEA"


def uid():
    return str(uuid.uuid4())


def clamp(value, low, high):
    return max(low, min(high, value))


                                                         
def icon_button(symbol, tooltip, callback, label=None):
    button = QToolButton()
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFixedSize(56, 56 if label else 43)
    button.clicked.connect(callback)
    button.setToolTip(tooltip)
    button.setStyleSheet("""
        QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #171717, stop:1 #0c0c0c);
            color: #EAEAEA;
            border: 1px solid #2b2b2b;
            border-radius: 14px;
            font-size: 18px;
            font-weight: normal;
            padding: 4px 2px;
        }
        QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2c2c2c, stop:1 #1a1a1a);
            border: 1px solid #6a6a6a;
            color: #ffffff;
        }
        QToolButton:pressed {
            background: #333333;
            border: 1px solid #999999;
        }
    """)
    if label:
        button.setText(f"{symbol}\n{label}")
        button.setFont(QFont("Arial", 7))
    else:
        button.setText(symbol)
    return button


                                                            
class BoardBackground(QGraphicsRectItem):
    def __init__(self):
        super().__init__(-2600, -1900, 5200, 3800)
        self.setZValue(-100)
        self.setPen(QPen(Qt.PenStyle.NoPen))

    def paint(self, painter, option, widget=None):
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                                                        
        grad = QRadialGradient(rect.center(), rect.width() * 0.6)
        grad.setColorAt(0.0, QColor("#0e0e12"))
        grad.setColorAt(1.0, QColor("#000000"))
        painter.fillRect(rect, QBrush(grad))

                         
        painter.setPen(QPen(QColor(30, 30, 36, 90), 1))
        step = 60
        x = int(rect.left())
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += step
        y = int(rect.top())
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += step

                                             
        painter.setPen(QPen(QColor(20, 20, 24, 120), 1))
        step = 90
        for px in range(int(rect.left()), int(rect.right()), step):
            for py in range(int(rect.top()), int(rect.bottom()), step):
                painter.drawPoint(px, py)


                             
class IntroWindow(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background:black;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video = QVideoWidget()
        self.video.setStyleSheet("background:black;")
        layout.addWidget(self.video)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)

        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.audio.setVolume(1.0)

        self.player.mediaStatusChanged.connect(self.media_status)
        self.player.errorOccurred.connect(lambda *args: self.begin_transition())

        self.finished_once = False

        self.fade = QWidget(self)
        self.fade.setStyleSheet("background:black;")
        self.fade.hide()

        self.animation = QPropertyAnimation(self.fade, b"windowOpacity")
        self.animation.setDuration(700)
        self.animation.finished.connect(self.finish)

    def start(self):
        self.showFullScreen()
        if VIDEO_PATH.exists():
            self.player.setSource(QUrl.fromLocalFile(str(VIDEO_PATH)))
            self.player.play()
        else:
            QTimer.singleShot(300, self.begin_transition)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fade.setGeometry(self.rect())

    def media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.begin_transition()

    def begin_transition(self):
        if self.finished_once:
            return
        self.finished_once = True
        self.player.stop()
        self.fade.setWindowOpacity(0)
        self.fade.show()
        self.fade.raise_()
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def finish(self):
        self.finished.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.begin_transition()


                                                   
class EvidenceCard(QGraphicsRectItem):
    def __init__(self, data, changed_callback=None):
        super().__init__(0, 0, 190, 125)

        self.data = data
        self.changed_callback = changed_callback

        self.card_id = data.get("id", uid())
        self.state = data.get("state", "indice")
        self.label = data.get("label", "")
        self.description = data.get("description", "")
        self.photo_path = data.get("photo")
        self.custom_color = data.get("custom_color")
        self.is_note = data.get("is_note", False)
        self.photo = None

        self.setPos(float(data.get("x", 100)), float(data.get("y", 100)))

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(5)

        self.title_item = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(QColor("#222222"))
        self.title_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.title_item.setTextWidth(165)
        self.title_item.setPos(12, 35)

        self.category_item = QGraphicsTextItem(self)
        self.category_item.setDefaultTextColor(QColor("#555555"))
        self.category_item.setFont(QFont("Arial", 8))
        self.category_item.setPos(12, 9)

        self.pin = QGraphicsEllipseItem(-7, -7, 14, 14, self)
        self.pin.setPos(95, -5)
        self.pin.setBrush(QColor("#777777"))
        self.pin.setPen(QPen(QColor("#222222"), 2))
        self.pin.setZValue(10)

        if self.photo_path:
            self.load_photo()

        self.refresh()

    def color(self):
        return QColor(self.custom_color or COLORS.get(self.state, COLORS["indice"]))

    def load_photo(self):
        pixmap = QPixmap(self.photo_path)
        if not pixmap.isNull():
            self.photo = pixmap

    def refresh(self):
        self.category_item.setPlainText("" if self.is_note else self.state.upper())
        self.title_item.setPlainText(self.label or "...")
        if self.is_note:
            self.setRect(0, 0, 220, 145)
        elif self.photo:
            self.setRect(0, 0, 190, 145)
        else:
            self.setRect(0, 0, 190, 125)
        self.update()

    def paint(self, painter, option, widget=None):
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        paper = QColor("#D8D8D8" if not self.is_note else "#C9C9C9")
        painter.setPen(QPen(QColor("#777777"), 1))
        painter.setBrush(QBrush(paper))
        painter.drawRoundedRect(rect, 5, 5)

        if self.photo:
            target = QRectF(12, 48, 166, 75)
            pix = self.photo.scaled(
                int(target.width()), int(target.height()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(
                int(target.x() + (target.width() - pix.width()) / 2),
                int(target.y() + (target.height() - pix.height()) / 2),
                pix
            )

        painter.setPen(QPen(self.color(), 4))
        painter.drawLine(0, 0, int(rect.width()), 0)

        if self.isSelected():
            painter.setPen(QPen(QColor("#FFFFFF"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-5, -5, 5, 5), 5, 5)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
                and self.changed_callback):
            self.changed_callback(self)
        return result

    def to_dict(self):
        return {
            "id": self.card_id,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "label": self.label,
            "description": self.description,
            "state": self.state,
            "photo": self.photo_path,
            "custom_color": self.custom_color,
            "is_note": self.is_note
        }


class EvidenceLink(QGraphicsPathItem):
    def __init__(self, first, second):
        super().__init__()
        self.first = first
        self.second = second
        self.setZValue(1)
        self.setPen(QPen(QColor("#A51C1C"), 2))
        self.update_path()

    def update_path(self):
        a = self.first.sceneBoundingRect().center()
        b = self.second.sceneBoundingRect().center()
        path = QPainterPath(a)
        middle = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2 + 30)
        path.quadTo(middle, b)
        self.setPath(path)

    def paint(self, painter, option, widget=None):
        self.update_path()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#8D1717"), 2))
        painter.drawPath(self.path())


class BoardView(QGraphicsView):
    card_clicked = Signal(object)
    background_clicked = Signal(QPointF)

    def __init__(self, scene):
        super().__init__(scene)

        self.zoom = 1.0
        self.pan_active = False
        self.last_pan = None

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setBackgroundBrush(QColor(BLACK))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def wheelEvent(self, event):
        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self.zoom = clamp(self.zoom * factor, 0.2, 3.5)
        self.setTransform(self.transform().fromScale(self.zoom, self.zoom))

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if event.button() == Qt.MouseButton.MiddleButton:
            self.pan_active = True
            self.last_pan = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if event.button() == Qt.MouseButton.LeftButton and item:
            parent = item
            while parent and not isinstance(parent, EvidenceCard):
                parent = parent.parentItem()
            if parent:
                self.card_clicked.emit(parent)
        elif event.button() == Qt.MouseButton.LeftButton:
            self.background_clicked.emit(self.mapToScene(event.position().toPoint()))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.pan_active and self.last_pan is not None:
            current = event.position().toPoint()
            delta = current - self.last_pan
            self.last_pan = current
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.pan_active = False
            self.last_pan = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        super().mouseReleaseEvent(event)

    def zoom_by(self, factor):
        self.zoom = clamp(self.zoom * factor, 0.2, 3.5)
        self.setTransform(self.transform().fromScale(self.zoom, self.zoom))


class Inspector(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.card = None
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #0e0e12, stop:1 #060608);
                color:#EEEEEE;
                font-family:Arial;
            }
            QLabel#title {
                color:#9a9aa6;
                font-size:11px;
                letter-spacing:2px;
                font-weight:bold;
                padding:4px 2px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background:#101014;
                border:1px solid #2a2a33;
                border-radius:9px;
                padding:9px;
                color:#EEEEEE;
                selection-background-color:#44444f;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border:1px solid #6a6a85;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #181820, stop:1 #0d0d12);
                border:1px solid #2a2a33;
                border-radius:10px;
                padding:10px;
                color:#EEEEEE;
            }
            QPushButton:hover {
                background:#2a2a33;
                border:1px solid #5a5a70;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(10)

        header = QLabel("FICHE D'ENQUÊTE")
        header.setObjectName("title")
        layout.addWidget(header)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Nom")
        layout.addWidget(self.name)

        self.category = QComboBox()
        self.category.addItems(STATES)
        layout.addWidget(self.category)

        self.description = QTextEdit()
        self.description.setPlaceholderText("Description")
        self.description.setMinimumHeight(130)
        layout.addWidget(self.description)

        self.color_button = QPushButton("◉  Couleur")
        self.color_button.setToolTip("Couleur")
        layout.addWidget(self.color_button)

        self.photo_button = QPushButton("▧  Photo")
        self.photo_button.setToolTip("Photo")
        layout.addWidget(self.photo_button)

        self.reset_button = QPushButton("↺  Défaut")
        self.reset_button.setToolTip("Couleur par défaut")
        layout.addWidget(self.reset_button)

        layout.addStretch()

        self.name.editingFinished.connect(self.apply)
        self.category.currentTextChanged.connect(self.apply)
        self.description.textChanged.connect(self.apply)
        self.color_button.clicked.connect(self.choose_color)
        self.photo_button.clicked.connect(self.choose_photo)
        self.reset_button.clicked.connect(self.reset_color)

    def set_card(self, card):
        self.card = card
        self.name.blockSignals(True)
        self.category.blockSignals(True)
        self.description.blockSignals(True)
        self.name.setText(card.label if card else "")
        self.category.setCurrentText(card.state if card else "indice")
        self.description.setPlainText(card.description if card else "")
        self.name.blockSignals(False)
        self.category.blockSignals(False)
        self.description.blockSignals(False)

    def apply(self):
        if not self.card:
            return
        self.card.label = self.name.text()
        self.card.state = self.category.currentText()
        self.card.description = self.description.toPlainText()
        self.card.refresh()
        self.changed.emit()

    def choose_color(self):
        if not self.card:
            return
        color = QColorDialog.getColor(
            QColor(self.card.custom_color or COLORS[self.card.state]), self)
        if color.isValid():
            self.card.custom_color = color.name()
            self.card.refresh()
            self.changed.emit()

    def reset_color(self):
        if self.card:
            self.card.custom_color = None
            self.card.refresh()
            self.changed.emit()

    def choose_photo(self):
        if not self.card:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Photo", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.card.photo_path = path
            self.card.load_photo()
            self.card.refresh()
            self.changed.emit()


class MiniMap(QWidget):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.setFixedHeight(120)
        self.setStyleSheet("""
            background: #060608;
            border:1px solid #2a2a33;
            border-radius:10px;
        """)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(500)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#060608"))

        cards = [i for i in self.scene.items() if isinstance(i, EvidenceCard)]
        if not cards:
            return

        bounds = self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80)
        if bounds.width() <= 0 or bounds.height() <= 0:
            return

        scale = min((self.width() - 20) / bounds.width(),
                    (self.height() - 20) / bounds.height())

        for card in cards:
            pos = card.scenePos()
            x = 10 + (pos.x() - bounds.x()) * scale
            y = 10 + (pos.y() - bounds.y()) * scale
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(card.custom_color or COLORS[card.state]))
            painter.drawRoundedRect(QRectF(x, y, 7, 6), 2, 2)


class DetectiveBoard(QWidget):
    def __init__(self):
        super().__init__()

        self.cards = {}
        self.links = []
        self.selected = None
        self.link_mode = False
        self.link_first = None
        self.undo_stack = []
        self.redo_stack = []
        self.loading = False

        self.setStyleSheet("""
            QWidget {
                background:#000000;
                color:#EEEEEE;
                font-family:Arial;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(9)

                                                     
        toolbar = QHBoxLayout()
        toolbar.setSpacing(7)
        toolbar.addStretch()

        buttons = [
            ("＋", "Nouvel élément", self.add_card, "Élément"),
            ("▧", "Photo", self.add_photo, "Photo"),
            ("▤", "Note", self.add_note, "Note"),
            ("↗", "Créer un lien", self.toggle_link, "Lien"),
            ("⧉", "Dupliquer", self.duplicate_card, "Copier"),
            ("⌫", "Supprimer", self.delete_card, "Suppr."),
            ("↶", "Annuler", self.undo, "Annul."),
            ("↷", "Rétablir", self.redo, "Rétab."),
            ("↥", "Ouvrir", self.load_file, "Ouvrir"),
            ("↓", "Enregistrer", self.save_file, "Sauver"),
            ("▣", "Exporter PNG", self.export_image, "Export"),
        ]
        for symbol, tooltip, callback, label in buttons:
            toolbar.addWidget(icon_button(symbol, tooltip, callback, label))

        toolbar.addStretch()
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#1a1a22; width:2px; }
        """)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2500, -1800, 5000, 3600)
        self.scene.setBackgroundBrush(QColor("#000000"))

                                      
        self.background = BoardBackground()
        self.scene.addItem(self.background)

        self.view = BoardView(self.scene)
        self.view.card_clicked.connect(self.card_clicked)
        self.view.background_clicked.connect(self.background_clicked)
        self.view.setStyleSheet("background:#000000;")
        splitter.addWidget(self.view)

        side = QWidget()
        side.setMinimumWidth(270)
        side.setMaximumWidth(310)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(8, 0, 0, 0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("⌕  Rechercher")
        self.search.setStyleSheet("""
            QLineEdit {
                background:#0e0e12;
                color:white;
                border:1px solid #2a2a33;
                border-radius:12px;
                padding:12px;
            }
            QLineEdit:focus { border:1px solid #6a6a85; }
        """)
        self.search.textChanged.connect(self.search_cards)
        side_layout.addWidget(self.search)

        self.inspector = Inspector()
        self.inspector.changed.connect(self.record_change)
        side_layout.addWidget(self.inspector, 1)

        self.minimap = MiniMap(self.scene)
        side_layout.addWidget(self.minimap)

        zoom_row = QHBoxLayout()
        zoom_row.addWidget(icon_button("−", "Dézoomer", lambda: self.view.zoom_by(1 / 1.2)))
        zoom_row.addWidget(icon_button("+", "Zoomer", lambda: self.view.zoom_by(1.2)))
        zoom_row.addWidget(icon_button("⌖", "Centrer", self.center_board))
        side_layout.addLayout(zoom_row)

        splitter.addWidget(side)
        splitter.setSizes([1100, 290])
        root.addWidget(splitter, 1)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(30000)

        self.add_shortcuts()

    def add_shortcuts(self):
        shortcuts = [
            ("Ctrl+S", self.save_file),
            ("Ctrl+O", self.load_file),
            ("Ctrl+Z", self.undo),
            ("Ctrl+Y", self.redo),
            ("Ctrl+D", self.duplicate_card),
            ("Delete", self.delete_card),
            ("Escape", self.cancel_modes),
            ("Ctrl+E", self.export_image),
            ("Ctrl+N", self.add_card),
        ]
        for key, callback in shortcuts:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(callback)
            self.addAction(action)

    def snapshot(self):
        return {
            "cards": [card.to_dict() for card in self.cards.values()],
            "links": [
                {"a": link.first.card_id, "b": link.second.card_id}
                for link in self.links
            ]
        }

    def record_change(self, *args):
        if self.loading:
            return
        self.undo_stack.append(self.snapshot())
        if len(self.undo_stack) > 60:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def restore_snapshot(self, data):
        self.loading = True
        self.scene.clear()
        self.background = BoardBackground()
        self.scene.addItem(self.background)
        self.cards.clear()
        self.links.clear()

        for card_data in data.get("cards", []):
            self.create_card(card_data, record=False)

        for link_data in data.get("links", []):
            first = self.cards.get(link_data["a"])
            second = self.cards.get(link_data["b"])
            if first and second:
                self.create_link(first, second)

        self.loading = False
        self.selected = None
        self.inspector.set_card(None)

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.snapshot())
        self.restore_snapshot(self.undo_stack.pop())

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.snapshot())
        self.restore_snapshot(self.redo_stack.pop())

    def create_card(self, data, record=True):
        card = EvidenceCard(data, self.card_moved)
        self.scene.addItem(card)
        self.cards[card.card_id] = card
        if record:
            self.record_change()
        return card

    def card_moved(self, card):
        for link in self.links:
            if link.first == card or link.second == card:
                link.update_path()

    def add_card(self):
        self.record_change()
        center = self.view.mapToScene(self.view.viewport().rect().center())
        data = {
            "id": uid(),
            "x": center.x(),
            "y": center.y(),
            "label": "Nouvel élément",
            "description": "",
            "state": "indice",
            "photo": None
        }
        card = self.create_card(data, False)
        self.select_card(card)

    def add_note(self):
        self.record_change()
        center = self.view.mapToScene(self.view.viewport().rect().center())
        data = {
            "id": uid(),
            "x": center.x(),
            "y": center.y(),
            "label": "Note",
            "description": "",
            "state": "indice",
            "photo": None,
            "is_note": True
        }
        card = self.create_card(data, False)
        self.select_card(card)

    def add_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Photo", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path:
            return
        self.record_change()
        center = self.view.mapToScene(self.view.viewport().rect().center())
        data = {
            "id": uid(),
            "x": center.x(),
            "y": center.y(),
            "label": Path(path).stem,
            "description": "",
            "state": "indice",
            "photo": path
        }
        card = self.create_card(data, False)
        self.select_card(card)

    def select_card(self, card):
        self.selected = card
        self.scene.clearSelection()
        card.setSelected(True)
        self.inspector.set_card(card)

    def card_clicked(self, card):
        if self.link_mode:
            self.handle_link_click(card)
        else:
            self.select_card(card)

    def background_clicked(self, position):
        if self.link_mode:
            return
        self.selected = None
        self.inspector.set_card(None)

    def create_link(self, first, second):
        if first == second:
            return
        for link in self.links:
            if ((link.first == first and link.second == second) or
                    (link.first == second and link.second == first)):
                return
        link = EvidenceLink(first, second)
        self.scene.addItem(link)
        self.links.append(link)

    def toggle_link(self):
        self.link_mode = not self.link_mode
        self.link_first = None

    def handle_link_click(self, card):
        if not self.link_first:
            self.link_first = card
            self.select_card(card)
            return
        if self.link_first == card:
            return
        self.record_change()
        self.create_link(self.link_first, card)
        self.link_first = None
        self.link_mode = False

    def cancel_modes(self):
        self.link_mode = False
        self.link_first = None

    def delete_card(self):
        if not self.selected:
            return
        self.record_change()
        card = self.selected
        remaining = []
        for link in self.links:
            if link.first == card or link.second == card:
                self.scene.removeItem(link)
            else:
                remaining.append(link)
        self.links = remaining
        self.scene.removeItem(card)
        self.cards.pop(card.card_id, None)
        self.selected = None
        self.inspector.set_card(None)

    def duplicate_card(self):
        if not self.selected:
            return
        self.record_change()
        data = self.selected.to_dict()
        data["id"] = uid()
        data["x"] += 45
        data["y"] += 45
        data["label"] += " (copie)"
        card = self.create_card(data, False)
        self.select_card(card)

    def search_cards(self, text):
        text = text.lower().strip()
        for card in self.cards.values():
            content = (card.label + " " + card.description + " " + card.state).lower()
            card.setOpacity(1.0 if not text or text in content else 0.15)
        matches = [
            card for card in self.cards.values()
            if text and text in (card.label + " " + card.description + " " + card.state).lower()
        ]
        if matches:
            self.select_card(matches[0])
            self.view.centerOn(matches[0])

    def center_board(self):
        if self.selected:
            self.view.centerOn(self.selected)
        else:
            self.view.centerOn(0, 0)

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer", str(BASE_DIR / "enquete.json"), "JSON (*.json)")
        if path:
            self.write_json(Path(path))

    def write_json(self, path):
        data = self.snapshot()
        data["zoom"] = self.view.zoom
        path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")

    def autosave(self):
        try:
            self.write_json(AUTOSAVE_PATH)
        except Exception as error:
            print("Autosave :", error)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.record_change()
            self.restore_snapshot(data)
            self.view.zoom = float(data.get("zoom", 1))
            self.view.setTransform(self.view.transform().fromScale(self.view.zoom, self.view.zoom))
        except Exception as error:
            QMessageBox.critical(self, "Erreur", str(error))

    def export_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter", str(BASE_DIR / "tableau.png"), "PNG (*.png)")
        if not path:
            return
        bounds = self.scene.itemsBoundingRect().adjusted(-100, -100, 100, 100)
        if bounds.isEmpty():
            bounds = QRectF(0, 0, 1200, 800)
        image = QPixmap(max(1, int(bounds.width())), max(1, int(bounds.height())))
        image.fill(QColor("#000000"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, QRectF(image.rect()), bounds)
        painter.end()
        image.save(path, "PNG")

    def closeEvent(self, event):
        self.autosave()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Investigation")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background:black;")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.intro = IntroWindow()
        self.board = DetectiveBoard()
        self.stack.addWidget(self.intro)
        self.stack.addWidget(self.board)

        self.intro.finished.connect(self.show_board)

        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background:black;")
        self.overlay.hide()

        self.fade = QPropertyAnimation(self.overlay, b"windowOpacity")
        self.fade.setDuration(700)
        self.fade.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.fade.finished.connect(self.finish_transition)

        self.transition_started = False

    def start(self):
        self.showFullScreen()
        self.intro.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())

    def show_board(self):
        self.overlay.setWindowOpacity(0)
        self.overlay.show()
        self.overlay.raise_()
        self.fade.setStartValue(0)
        self.fade.setEndValue(1)
        self.fade.start()

    def finish_transition(self):
        if not self.transition_started:
            self.transition_started = True
            self.stack.setCurrentWidget(self.board)
            try:
                if AUTOSAVE_PATH.exists():
                    data = json.loads(AUTOSAVE_PATH.read_text(encoding="utf-8"))
                    if data.get("cards"):
                        self.board.restore_snapshot(data)
            except Exception as error:
                print("Autosave :", error)
            self.fade.setStartValue(1)
            self.fade.setEndValue(0)
            self.fade.start()
        else:
            self.overlay.hide()
            self.board.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.stack.currentWidget() == self.board:
                self.close()
            else:
                self.intro.begin_transition()
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Investigation")
    app.setStyle("Fusion")
    window = MainWindow()
    window.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()