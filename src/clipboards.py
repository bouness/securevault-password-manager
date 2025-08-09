from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from themes import ThemeManager


class ClipboardManager(QWidget):
    """Manages clipboard with auto-clear functionality and progress"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self.clear_clipboard)
        self.clipboard_timer.setSingleShot(True)

        # Progress tracking
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.countdown_seconds = 0
        self.total_seconds = 10

        self.setup_ui()

    def setup_ui(self):
        """Setup clipboard progress indicator"""
        colors = ThemeManager.get_theme_colors()

        # Create floating progress widget
        self.progress_widget = QWidget(self.parent_window)
        self.progress_widget.setFixedSize(300, 80)
        self.progress_widget.setStyleSheet(
            f"""
            QWidget {{
                background: {colors['bg_secondary']};
                border: 2px solid {colors['accent']};
                border-radius: 10px;
                color: {colors['text_primary']};
            }}
        """
        )

        layout = QVBoxLayout()
        self.progress_widget.setLayout(layout)

        # Info label
        self.info_label = QLabel("Password copied to clipboard")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 12px; border: none;")
        layout.addWidget(self.info_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(self.total_seconds)
        self.progress_bar.setValue(self.total_seconds)
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                background: {colors['bg_tertiary']};
                height: 8px;
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {colors['accent']};
                border-radius: 4px;
            }}
        """
        )
        layout.addWidget(self.progress_bar)

        # Time label
        self.time_label = QLabel(f"Auto-clear in {self.total_seconds}s")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 12px; border: none;")
        layout.addWidget(self.time_label)

        # Hide initially
        self.progress_widget.hide()

    def copy_to_clipboard(self, text, data_type="data"):
        """Copy text to clipboard with auto-clear"""
        if not text:
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        # Update UI
        self.info_label.setText(f"{data_type.title()} copied to clipboard")
        self.countdown_seconds = self.total_seconds
        self.progress_bar.setValue(self.total_seconds)
        self.time_label.setText(f"Auto-clear in {self.total_seconds}s")

        # Position the progress widget
        self.position_progress_widget()
        self.progress_widget.show()
        self.progress_widget.raise_()

        # Start animation
        self.animate_progress_widget()

        # Start timers
        self.clipboard_timer.start(self.total_seconds * 1000)  # 30 seconds
        self.progress_timer.start(1000)  # Update every second

        # Update status bar
        if self.parent_window:
            title = data_type.title()
            total = self.total_seconds
            self.parent_window.status_bar.showMessage(
                f"{title} copied! Auto-clear in {total}s",
                self.total_seconds * 1000,
            )

    def position_progress_widget(self):
        """Position progress widget in bottom-right of parent window"""
        if self.parent_window:
            parent_rect = self.parent_window.geometry()
            widget_width = self.progress_widget.width()
            widget_height = self.progress_widget.height()

            x = parent_rect.width() - widget_width - 20
            y = (
                parent_rect.height() - widget_height - 60
            )  # Account for status bar

            self.progress_widget.move(x, y)

    def animate_progress_widget(self):
        """Animate progress widget appearance"""
        self.animation = QPropertyAnimation(self.progress_widget, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # Start from below and slide up
        start_rect = self.progress_widget.geometry()
        start_rect.moveTop(start_rect.top() + 50)

        end_rect = self.progress_widget.geometry()

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

    def update_progress(self):
        """Update progress bar countdown"""
        self.countdown_seconds -= 1
        self.progress_bar.setValue(self.countdown_seconds)
        self.time_label.setText(f"Auto-clear in {self.countdown_seconds}s")

        if self.countdown_seconds <= 0:
            self.progress_timer.stop()
            self.hide_progress_widget()

    def clear_clipboard(self):
        """Clear clipboard content"""
        clipboard = QApplication.clipboard()
        clipboard.setText("")
        clipboard.clear()

        self.progress_timer.stop()
        self.hide_progress_widget()

        if self.parent_window:
            self.parent_window.status_bar.showMessage(
                "Clipboard cleared for security", 3000
            )

    def hide_progress_widget(self):
        """Hide progress widget with animation"""
        self.hide_animation = QPropertyAnimation(
            self.progress_widget, b"geometry"
        )
        self.hide_animation.setDuration(200)
        self.hide_animation.setEasingCurve(QEasingCurve.InCubic)

        start_rect = self.progress_widget.geometry()
        end_rect = start_rect
        end_rect.moveTop(end_rect.top() + 50)

        self.hide_animation.setStartValue(start_rect)
        self.hide_animation.setEndValue(end_rect)
        self.hide_animation.finished.connect(self.progress_widget.hide)
        self.hide_animation.start()

    def stop_auto_clear(self):
        """Stop auto-clear timer"""
        self.clipboard_timer.stop()
        self.progress_timer.stop()
        self.hide_progress_widget()
