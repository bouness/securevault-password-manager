from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class SplashScreen(QWidget):
    """Modern splash screen for application startup"""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Center the splash screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

        self.setup_ui()

        # Auto close after 1.5 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.finish)
        self.timer.start(1500)

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Main container with rounded corners
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 20px;
            }
        """
        )
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)

        # Logo
        logo = QLabel("🔐")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 64px; color: white; margin: 20px;")
        container_layout.addWidget(logo)

        # Title
        title = QLabel("SecureVault")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            """
            font-size: 28px;
            font-weight: bold;
            color: white;
            margin: 0 20px;
        """
        )
        container_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Professional Password Manager")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            """
            font-size: 14px;
            color: rgba(255,255,255,0.8);
            margin: 0 20px 20px 20px;
        """
        )
        container_layout.addWidget(subtitle)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setStyleSheet(
            """
            QProgressBar {
                border: none;
                background: rgba(255,255,255,0.2);
                height: 4px;
                border-radius: 2px;
                margin: 0 20px 20px 20px;
            }
            QProgressBar::chunk {
                background: white;
                border-radius: 2px;
            }
        """
        )
        container_layout.addWidget(self.progress)

        layout.addWidget(container)

    def finish(self):
        self.timer.stop()
        self.close()
        self.callback()
