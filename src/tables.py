from PySide6.QtWidgets import QTableWidget

from themes import ThemeManager


class ModernTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()

    def setup_table(self):
        colors = ThemeManager.get_theme_colors()
        self.setStyleSheet(
            f"""
            QTableWidget {{
                background: {colors['bg_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                gridline-color: {colors['border']};
                font-size: 13px;
                color: {colors['text_primary']};
                selection-background-color: {colors['selection_bg']};
            }}
            QTableWidget::item {{
                padding: 12px 8px;
                border-bottom: 1px solid {colors['border']};
                color: {colors['text_primary']};
            }}
            QTableWidget::item:selected {{
                background: {colors['selection_bg']};
                color: {colors['selection']};
            }}
            QHeaderView::section {{
                background: {colors['bg_secondary']};
                border: none;
                border-bottom: 2px solid {colors['border']};
                padding: 12px 8px;
                font-weight: bold;
                color: {colors['text_primary']};
            }}
        """
        )
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
