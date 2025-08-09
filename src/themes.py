from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton


class ThemeManager:
    @staticmethod
    def is_dark_theme():
        """Detect if system is using dark theme"""
        app = QApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(QPalette.Window)
            # If background is dark, assume dark theme
            return bg_color.lightness() < 128
        return False

    @staticmethod
    def get_theme_colors():
        """Get theme-appropriate colors"""
        if ThemeManager.is_dark_theme():
            return {
                "bg_primary": "#2b2b2b",
                "bg_secondary": "#3c3c3c",
                "bg_tertiary": "#4a4a4a",
                "text_primary": "#ffffff",
                "text_secondary": "#cccccc",
                "text_muted": "#999999",
                "accent": "#0078d4",
                "accent_hover": "#106ebe",
                "accent_pressed": "#005a9e",
                "border": "#555555",
                "border_focus": "#0078d4",
                "selection": "#0078d4",
                "selection_bg": "#264f78",
            }
        else:
            return {
                "bg_primary": "#ffffff",
                "bg_secondary": "#f8f9fa",
                "bg_tertiary": "#e9ecef",
                "text_primary": "#212529",
                "text_secondary": "#495057",
                "text_muted": "#6c757d",
                "accent": "#0d6efd",
                "accent_hover": "#0b5ed7",
                "accent_pressed": "#0a58ca",
                "border": "#dee2e6",
                "border_focus": "#0d6efd",
                "selection": "#0d6efd",
                "selection_bg": "#cfe2ff",
            }


class ModernButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self.update_theme()

    def update_theme(self):
        colors = ThemeManager.get_theme_colors()
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {colors['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {colors['accent_hover']};
            }}
            QPushButton:pressed {{
                background: {colors['accent_pressed']};
            }}
            QPushButton:disabled {{
                background: {colors['border']};
                color: {colors['text_muted']};
            }}
        """
        )


class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(40)
        self.update_theme()

    def update_theme(self):
        colors = ThemeManager.get_theme_colors()
        self.setStyleSheet(
            f"""
            QLineEdit {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 14px;
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {colors['border_focus']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {colors['accent']};
            }}
        """
        )
