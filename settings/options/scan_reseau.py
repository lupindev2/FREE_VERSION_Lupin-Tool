
import sys
import re
import socket
import ssl
import math
import requests
import dns.resolver

from datetime import datetime
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QLabel, QGraphicsDropShadowEffect
)


class Background(QWidget):
    def __init__(self):
        super().__init__()
        self.phase = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(40)

    def animate(self):
        self.phase += 0.012
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#000000"))

        x = self.width() * (
            0.5 + 0.12 * math.sin(self.phase)
        )
        y = self.height() * 0.28

        gradient = QRadialGradient(
            x, y, self.width() * 0.6
        )
        gradient.setColorAt(0, QColor(255, 255, 255, 15))
        gradient.setColorAt(0.4, QColor(255, 255, 255, 5))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.fillRect(self.rect(), gradient)


class AuditWorker(QThread):
    log = Signal(str, str)
    done = Signal()

    def __init__(self, domain):
        super().__init__()
        self.domain = domain

    def write(self, message, level="normal"):
        time = datetime.now().strftime("%H:%M:%S")
        self.log.emit(f"{time}   {message}", level)

    def run(self):
        domain = self.domain

        self.write(f"INITIALISATION  /  {domain}", "bright")

        for record in ["A", "AAAA", "MX", "NS", "TXT"]:
            try:
                answers = dns.resolver.resolve(domain, record)
                self.write(f"\n{record}", "bright")
                for answer in answers:
                    self.write(str(answer))
            except Exception:
                self.write(f"{record} : aucune donnée")

        try:
            ip = socket.gethostbyname(domain)
            self.write(f"\nADRESSE IP  /  {ip}", "bright")
        except Exception as error:
            self.write(f"DNS impossible : {error}", "error")
            self.done.emit()
            return

        self.write("\nCERTIFICAT TLS", "bright")

        try:
            context = ssl.create_default_context()

            with socket.create_connection(
                (domain, 443), timeout=5
            ) as sock:
                with context.wrap_socket(
                    sock, server_hostname=domain
                ) as secure:

                    cert = secure.getpeercert()

                    self.write(
                        f"Protocole : {secure.version()}"
                    )
                    self.write(
                        f"Émetteur : {cert.get('issuer')}"
                    )
                    self.write(
                        f"Expiration : {cert.get('notAfter')}"
                    )

        except Exception as error:
            self.write(f"TLS indisponible : {error}")

        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{domain}"
                self.write(f"\nREQUÊTE  /  {url}", "bright")

                response = requests.get(
                    url,
                    timeout=8,
                    allow_redirects=True,
                    headers={"User-Agent": "LUPIN-Audit/1.0"}
                )

                self.write(
                    f"HTTP STATUS  /  {response.status_code}",
                    "bright"
                )
                self.write(f"URL finale : {response.url}")
                self.write(
                    f"Serveur : {response.headers.get('Server', 'Non déclaré')}"
                )

                headers = [
                    "Strict-Transport-Security",
                    "Content-Security-Policy",
                    "X-Content-Type-Options",
                    "X-Frame-Options",
                    "Referrer-Policy",
                    "Permissions-Policy"
                ]

                self.write("\nEN-TÊTES DE SÉCURITÉ", "bright")

                for header in headers:
                    present = header in response.headers
                    self.write(
                        f"{header} : "
                        f"{'Présent' if present else 'Absent'}",
                        "bright" if present else "normal"
                    )

                self.write(
                    f"\nRedirections : {len(response.history)}"
                )
                self.write(
                    f"Taille : {len(response.content)} octets"
                )
                break

            except requests.RequestException as error:
                self.write(f"{scheme.upper()} : {error}")

        self.write("\nAUDIT TERMINÉ", "bright")
        self.done.emit()


class Lupin(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LUPIN")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background:#000000;")

        self.worker = None

        self.background = Background()
        self.background.setParent(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(100, 60, 100, 60)
        layout.setSpacing(0)

        layout.addStretch(2)

        self.title = QLabel("LUPIN")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 54px;
                font-weight: 200;
                letter-spacing: 15px;
                background: transparent;
            }
        """)

        title_glow = QGraphicsDropShadowEffect()
        title_glow.setBlurRadius(55)
        title_glow.setColor(QColor(255, 255, 255, 100))
        title_glow.setOffset(0, 0)
        self.title.setGraphicsEffect(title_glow)

        layout.addWidget(self.title)
        layout.addSpacing(48)

                                               
        input_container = QHBoxLayout()
        input_container.setContentsMargins(0, 0, 0, 0)

        self.input = QLineEdit()
        self.input.setPlaceholderText("exemple.com")
        self.input.setFixedSize(480, 54)
        self.input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,12);
                border: 1px solid rgba(255,255,255,45);
                border-radius: 27px;
                color: white;
                font-size: 15px;
                font-weight: 300;
                letter-spacing: 1px;
                padding: 0 20px;
            }

            QLineEdit:focus {
                background: rgba(255,255,255,19);
                border: 1px solid rgba(255,255,255,180);
            }

            QLineEdit::placeholder {
                color: rgba(255,255,255,100);
            }
        """)

        input_glow = QGraphicsDropShadowEffect()
        input_glow.setBlurRadius(30)
        input_glow.setColor(QColor(255, 255, 255, 30))
        input_glow.setOffset(0, 0)
        self.input.setGraphicsEffect(input_glow)

        input_container.addStretch()
        input_container.addWidget(self.input)
        input_container.addStretch()

        layout.addLayout(input_container)
        layout.addSpacing(28)

                   
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,5);
                border: 1px solid rgba(255,255,255,18);
                border-radius: 18px;
                color: #BDBDBD;
                padding: 22px;
                font-family: Consolas;
                font-size: 12px;
                selection-background-color: #555555;
            }
        """)

        layout.addWidget(self.results, 1)
        layout.addStretch(2)

        self.input.returnPressed.connect(self.start_audit)

        self.showFullScreen()
        self.input.setFocus()

    def resizeEvent(self, event):
        self.background.setGeometry(self.rect())
        self.background.lower()
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def add_log(self, message, level="normal"):
        colors = {
            "normal": "#A5A5A5",
            "bright": "#FFFFFF",
            "error": "#D0D0D0"
        }

        color = colors.get(level, "#A5A5A5")

        self.results.append(
            f'<span style="color:{color}">{message}</span>'
        )

    def start_audit(self):
        domain = self.input.text().strip()
        domain = re.sub(r"^https?://", "", domain)
        domain = domain.split("/")[0].split(":")[0]

        if not re.fullmatch(
            r"(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
            r"[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}",
            domain
        ):
            self.add_log("Nom de domaine invalide.", "error")
            return

        if self.worker and self.worker.isRunning():
            return

        self.results.clear()

        self.worker = AuditWorker(domain)
        self.worker.log.connect(self.add_log)
        self.worker.done.connect(self.audit_finished)
        self.worker.start()

    def audit_finished(self):
        self.input.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    window = Lupin()
    sys.exit(app.exec())
