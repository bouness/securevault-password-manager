import os
import sys

from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication

from passwords import PasswordManager
from screens import SplashScreen
from themes import ThemeManager


def resource_path(relative_path):
    """Get path relative to the executable or script."""
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("SecureVault")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("SecureVault Inc.")
    app_icon = QIcon(resource_path("assets/icon.png"))
    app.setWindowIcon(app_icon)

    # Apply modern style
    app.setStyle("Fusion")

    # Set palette based on system theme
    if ThemeManager.is_dark_theme():
        dark_palette = QPalette()
        colors = ThemeManager.get_theme_colors()

        # Configure dark palette
        dark_palette.setColor(QPalette.Window, QColor(colors["bg_primary"]))
        dark_palette.setColor(
            QPalette.WindowText, QColor(colors["text_primary"])
        )
        dark_palette.setColor(QPalette.Base, QColor(colors["bg_primary"]))
        dark_palette.setColor(
            QPalette.AlternateBase, QColor(colors["bg_secondary"])
        )
        dark_palette.setColor(
            QPalette.ToolTipBase, QColor(colors["bg_tertiary"])
        )
        dark_palette.setColor(
            QPalette.ToolTipText, QColor(colors["text_primary"])
        )
        dark_palette.setColor(QPalette.Text, QColor(colors["text_primary"]))
        dark_palette.setColor(QPalette.Button, QColor(colors["bg_secondary"]))
        dark_palette.setColor(
            QPalette.ButtonText, QColor(colors["text_primary"])
        )
        dark_palette.setColor(
            QPalette.BrightText, QColor(colors["text_primary"])
        )
        dark_palette.setColor(QPalette.Link, QColor(colors["accent"]))
        dark_palette.setColor(QPalette.Highlight, QColor(colors["selection"]))
        dark_palette.setColor(
            QPalette.HighlightedText, QColor(colors["text_primary"])
        )

        app.setPalette(dark_palette)

    # Create main window but don't show yet
    window = PasswordManager()
    window.hide()

    def show_main_window():
        """Callback to show main window after splash"""
        window.show()
        window.show_login_dialog()

    # Show splash screen
    splash = SplashScreen(callback=show_main_window)
    splash.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
