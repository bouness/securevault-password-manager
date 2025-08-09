import base64
import json
import os
from datetime import datetime

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clipboards import ClipboardManager
from security import SecurityManager
from tables import ModernTable
from themes import ModernButton, ModernLineEdit, ThemeManager


class PasswordStrengthMeter(QWidget):
    """Visual indicator for password strength"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        self.setLayout(layout)

        # Strength label
        self.strength_label = QLabel("Strength: N/A")
        self.strength_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.strength_label)

        # Progress bar container
        meter_container = QWidget()
        meter_layout = QHBoxLayout(meter_container)
        meter_layout.setContentsMargins(0, 0, 0, 0)
        meter_layout.setSpacing(5)

        # Create 4 segments
        self.segments = []
        for i in range(4):
            segment = QFrame()
            segment.setFixedHeight(6)
            segment.setStyleSheet("background: #e0e0e0; border-radius: 3px;")
            meter_layout.addWidget(segment)
            self.segments.append(segment)

        layout.addWidget(meter_container)

    def update_strength(self, password):
        """Update strength meter based on password"""
        if not password:
            self.strength_label.setText("Strength: N/A")
            for segment in self.segments:
                segment.setStyleSheet(
                    "background: #e0e0e0; border-radius: 3px;"
                )
            return

        score, feedback = self.calculate_strength(password)

        # Update label
        strength_text = {
            0: "Very Weak",
            1: "Weak",
            2: "Medium",
            3: "Strong",
            4: "Very Strong",
        }.get(score, "N/A")
        self.strength_label.setText(f"Strength: {strength_text}")

        # Update segments
        colors = ["#ff5252", "#ffb142", "#feca57", "#1dd1a1", "#10ac84"]
        for i in range(5):
            if i < len(self.segments):
                if i <= score:
                    self.segments[i].setStyleSheet(
                        f"background: {colors[score]}; border-radius: 3px;"
                    )
                else:
                    self.segments[i].setStyleSheet(
                        "background: #e0e0e0; border-radius: 3px;"
                    )

    def calculate_strength(self, password):
        """Calculate password strength score (0-4) with feedback"""
        score = 0
        feedback = []

        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters")

        # Character diversity
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        char_types = sum([has_lower, has_upper, has_digit, has_special])
        if char_types >= 2:
            score += 1
        if char_types >= 3:
            score += 1
        if char_types == 4:
            score += 1

        if not has_lower:
            feedback.append("Add lowercase letters")
        if not has_upper:
            feedback.append("Add uppercase letters")
        if not has_digit:
            feedback.append("Add numbers")
        if not has_special:
            feedback.append("Add special characters")

        # Entropy calculation
        charset_size = 0
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_special:
            charset_size += 32

        entropy = len(password) * (charset_size**0.5) / 10
        if entropy > 15:  # Very strong
            score = min(score + 1, 4)
        elif entropy > 10:  # Strong
            score = min(score + 0.5, 4)

        # Common password check
        common_passwords = [
            "password",
            "123456",
            "qwerty",
            "letmein",
            "welcome",
        ]
        if password.lower() in common_passwords:
            score = 0
            feedback.append("Avoid common passwords")

        # Sequential characters check
        if any(
            password[i : i + 3] in "abcdefghijklmnopqrstuvwxyz"
            for i in range(len(password) - 2)
        ):
            score = max(score - 1, 0)
            feedback.append("Avoid sequential characters")

        return int(score), feedback


class PasswordDatabase:
    def __init__(self):
        self.entries = []
        self.categories = [
            "General",
            "Social Media",
            "Email",
            "Banking",
            "Work",
        ]

    def add_entry(self, entry):
        entry["id"] = len(self.entries)
        entry["created"] = datetime.now().isoformat()
        entry["modified"] = entry["created"]
        self.entries.append(entry)

    def update_entry(self, entry_id, entry):
        if 0 <= entry_id < len(self.entries):
            entry["id"] = entry_id
            entry["modified"] = datetime.now().isoformat()
            self.entries[entry_id] = entry

    def delete_entry(self, entry_id):
        if 0 <= entry_id < len(self.entries):
            del self.entries[entry_id]
            # Reindex entries
            for i, entry in enumerate(self.entries):
                entry["id"] = i

    def get_entries_by_category(self, category):
        return [e for e in self.entries if e.get("category") == category]

    def search_entries(self, query):
        query = query.lower()
        results = []

        for entry in self.entries:
            if (
                query in entry.get("title", "").lower()
                or query in entry.get("username", "").lower()
                or query in entry.get("url", "").lower()
                or query in entry.get("notes", "").lower()
            ):
                results.append(entry)
        return results


class PasswordGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.setFixedSize(400, 300)
        self.setup_ui()
        self.apply_modern_style()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Generate Secure Password")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            """font-size: 18px;
            font-weight:
            bold; margin: 10px;"""
        )
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()

        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 128)
        self.length_spin.setValue(16)
        form_layout.addRow("Length:", self.length_spin)

        self.uppercase_cb = QCheckBox("Include Uppercase (A-Z)")
        self.uppercase_cb.setChecked(True)
        form_layout.addRow(self.uppercase_cb)

        self.lowercase_cb = QCheckBox("Include Lowercase (a-z)")
        self.lowercase_cb.setChecked(True)
        form_layout.addRow(self.lowercase_cb)

        self.numbers_cb = QCheckBox("Include Numbers (0-9)")
        self.numbers_cb.setChecked(True)
        form_layout.addRow(self.numbers_cb)

        self.symbols_cb = QCheckBox("Include Symbols (!@#$%^&*)")
        self.symbols_cb.setChecked(True)
        form_layout.addRow(self.symbols_cb)

        layout.addLayout(form_layout)

        # Generated password display
        self.password_edit = QLineEdit()
        self.password_edit.setReadOnly(True)
        self.password_edit.setStyleSheet(
            "font-family: monospace; font-size: 14px;"
        )
        layout.addWidget(self.password_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        self.generate_btn = ModernButton("Generate")
        self.copy_btn = ModernButton("Copy")
        self.use_btn = ModernButton("Use Password")

        self.generate_btn.clicked.connect(self.generate_password)
        self.copy_btn.clicked.connect(self.copy_password)
        self.use_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.use_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Generate initial password
        self.generate_password()

    def generate_password(self):
        length = self.length_spin.value()
        use_uppercase = self.uppercase_cb.isChecked()
        use_lowercase = self.lowercase_cb.isChecked()
        use_numbers = self.numbers_cb.isChecked()
        use_symbols = self.symbols_cb.isChecked()

        password = SecurityManager.generate_password(
            length, use_symbols, use_numbers, use_uppercase, use_lowercase
        )
        self.password_edit.setText(password)

    def copy_password(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.password_edit.text())
        self.parent().clipboard_manager.copy_to_clipboard(
            self.password_edit.text(), "password"
        )

    def get_password(self):
        return self.password_edit.text()

    def apply_modern_style(self):
        colors = ThemeManager.get_theme_colors()
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            QCheckBox {{
                font-size: 12px;
                spacing: 10px;
                color: {colors['text_primary']};
            }}
            QSpinBox {{
                padding: 8px;
                border: 2px solid {colors['border']};
                border-radius: 6px;
                font-size: 14px;
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
        """
        )


class EntryDialog(QDialog):
    def __init__(self, entry=None, categories=None, parent=None):
        super().__init__(parent)
        self.entry = entry or {}
        self.categories = categories or ["General"]
        self.setWindowTitle("Add Entry" if not entry else "Edit Entry")
        self.setFixedSize(550, 600)
        self.setup_ui()
        self.apply_modern_style()

    def update_password_strength(self):
        """Update password strength meter"""
        password = self.password_edit.text()
        self.password_strength.update_strength(password)

    def setup_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Add New Entry" if not self.entry else "Edit Entry")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin: 10px;"
        )
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()

        self.title_edit = ModernLineEdit("Entry Title")
        self.title_edit.setText(self.entry.get("title", ""))
        form_layout.addRow("Title:", self.title_edit)

        self.username_edit = ModernLineEdit("Username/Email")
        self.username_edit.setText(self.entry.get("username", ""))
        form_layout.addRow("Username:", self.username_edit)

        password_layout = QHBoxLayout()
        self.password_edit = ModernLineEdit("Password")
        self.password_edit.setText(self.entry.get("password", ""))
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(40, 40)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)

        self.generate_password_btn = QPushButton("🎲")
        self.generate_password_btn.setFixedSize(40, 40)
        self.generate_password_btn.clicked.connect(
            self.open_password_generator
        )

        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(self.show_password_btn)
        password_layout.addWidget(self.generate_password_btn)

        form_widget = QWidget()
        form_widget.setLayout(password_layout)
        form_layout.addRow("Password:", form_widget)

        self.url_edit = ModernLineEdit("Website URL")
        self.url_edit.setText(self.entry.get("url", ""))
        form_layout.addRow("URL:", self.url_edit)

        # Category dropdown
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        if self.entry.get("category") in self.categories:
            self.category_combo.setCurrentText(self.entry.get("category"))
        form_layout.addRow("Category:", self.category_combo)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setText(self.entry.get("notes", ""))
        self.notes_edit.setPlaceholderText("Additional notes...")
        form_layout.addRow("Notes:", self.notes_edit)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = ModernButton("Save")
        self.cancel_btn = ModernButton("Cancel")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Add password strength meter
        self.password_strength = PasswordStrengthMeter()
        password_layout.addWidget(self.password_strength)

        # Connect password field to strength meter
        self.password_edit.textChanged.connect(self.update_password_strength)

    def toggle_password_visibility(self):
        if self.password_edit.echoMode() == QLineEdit.Password:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("👁")

    def open_password_generator(self):
        dialog = PasswordGeneratorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.password_edit.setText(dialog.get_password())

    def get_entry_data(self):
        return {
            "title": self.title_edit.text(),
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
            "url": self.url_edit.text(),
            "category": self.category_combo.currentText(),
            "notes": self.notes_edit.toPlainText(),
        }

    def apply_modern_style(self):
        colors = ThemeManager.get_theme_colors()
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            QTextEdit {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            QComboBox {{
                padding: 8px;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                font-size: 14px;
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                background: {colors['bg_secondary']};
            }}
            QComboBox::down-arrow {{
                border: none;
            }}
            QPushButton {{
                border: 2px solid {colors['border']};
                border-radius: 6px;
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            QPushButton:hover {{
                background: {colors['bg_secondary']};
                border-color: {colors['accent']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
        """
        )


class PasswordManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.database = PasswordDatabase()
        self.current_file = None
        self.encryption_key = None
        self.is_locked = True
        self.salt = None  # Initialize salt

        self.clipboard_manager = ClipboardManager(self)

        self.setWindowTitle("SecureVault - Password Manager")
        self.setGeometry(100, 100, 1280, 720)
        self.setup_ui()
        self.apply_modern_theme()
        self.settings = QSettings("SecureVault", "PasswordManager")
        self.dirty = False  # Track unsaved changes
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(5 * 60 * 1000)  # Auto-save every 5 minutes

    def setup_ui(self):
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Sidebar
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)

        # Main content
        main_content = self.create_main_content()
        splitter.addWidget(main_content)

        # Set splitter proportions
        splitter.setSizes([250, 950])

        # Create toolbar
        self.create_toolbar()

        # Create status bar
        self.create_status_bar()

    def mark_dirty(self):
        """Mark database as having unsaved changes"""
        self.dirty = True
        self.update_window_title()

    def mark_clean(self):
        """Mark database as saved"""
        self.dirty = False
        self.update_window_title()

    def update_window_title(self):
        """Update window title with modified indicator"""
        base_title = "SecureVault - Password Manager"
        if self.current_file:
            filename = os.path.basename(self.current_file)
            title = f"{filename} - {base_title}"
        else:
            title = f"Unsaved Database - {base_title}"

        if self.dirty:
            title = "* " + title

        self.setWindowTitle(title)

    def auto_save(self):
        """Auto-save functionality"""
        if self.dirty and self.current_file and not self.is_locked:
            try:
                self.save_database_file(self.current_file)
                self.status_bar.showMessage(
                    f"Auto-saved at {datetime.now().strftime('%H:%M:%S')}",
                    5000,
                )
                self.mark_clean()
            except Exception as e:
                self.status_bar.showMessage(
                    f"Auto-save failed: {str(e)}", 10000
                )

    def create_sidebar(self):
        colors = ThemeManager.get_theme_colors()
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(
            f"""
            QWidget {{
                background: {colors['bg_secondary']};
                color: {colors['text_primary']};
            }}
        """
        )

        layout = QVBoxLayout()
        sidebar.setLayout(layout)

        # Logo/Title
        title = QLabel("🔐 Secure Vault")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"""
            font-size: 20px;
            font-weight: bold;
            padding: 20px;
            color: {colors['text_primary']};
            background: {colors['bg_tertiary']};
            border-radius: 8px;
            margin: 10px;
        """
        )
        layout.addWidget(title)

        # Search
        self.search_edit = ModernLineEdit("Search entries...")
        self.search_edit.textChanged.connect(self.filter_entries)
        layout.addWidget(self.search_edit)

        # Categories
        categories_label = QLabel("Categories")
        categories_label.setStyleSheet(
            f"""
                font-weight: bold;
                padding: 10px;
                color: {colors['text_secondary']};
            """
        )
        layout.addWidget(categories_label)

        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setStyleSheet(
            f"""
            QTreeWidget {{
                background: {colors['bg_tertiary']};
                border: none;
                color: {colors['text_primary']};
                font-size: 13px;
            }}
            QTreeWidget::item {{
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
                color: {colors['text_primary']};
            }}
            QTreeWidget::item:selected {{
                background: {colors['selection_bg']};
                color: {colors['selection']};
            }}
            QTreeWidget::item:hover {{
                background: {colors['bg_primary']};
            }}
        """
        )
        self.populate_categories()
        self.category_tree.itemClicked.connect(self.on_category_selected)
        layout.addWidget(self.category_tree)

        layout.addStretch()

        # Security info
        security_info = QLabel("🔒 Database Encrypted\n✓ Auto-lock enabled")
        security_info.setStyleSheet(
            f"""
            color: #27ae60;
            font-size: 11px;
            padding: 10px;
            background: {colors['bg_tertiary']};
            border-radius: 6px;
            margin: 10px;
        """
        )
        layout.addWidget(security_info)

        return sidebar

    def create_main_content(self):
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Header with buttons
        header_layout = QHBoxLayout()

        add_btn = ModernButton("➕ Add Entry")
        edit_btn = ModernButton("✏️ Edit")
        delete_btn = ModernButton("🗑️ Delete")

        add_btn.clicked.connect(self.add_entry)
        edit_btn.clicked.connect(self.edit_entry)
        delete_btn.clicked.connect(self.delete_entry)

        header_layout.addWidget(add_btn)
        header_layout.addWidget(edit_btn)
        header_layout.addWidget(delete_btn)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Entries table
        self.entries_table = ModernTable()
        self.setup_entries_table()
        layout.addWidget(self.entries_table)

        return main_widget

    def setup_entries_table(self):
        headers = [
            "Title",
            "Username",
            "URL",
            "Category",
            "Modified",
            "Actions",
        ]
        self.entries_table.setColumnCount(len(headers))
        self.entries_table.setHorizontalHeaderLabels(headers)

        # Set column widths
        header = self.entries_table.horizontalHeader()
        header.resizeSection(0, 180)  # Title
        header.resizeSection(1, 140)  # Username
        header.resizeSection(2, 180)  # URL
        header.resizeSection(3, 100)  # Category
        header.resizeSection(4, 130)  # Modified
        header.resizeSection(5, 200)  # Actions

        self.entries_table.itemDoubleClicked.connect(
            self.on_entry_double_click
        )

    def populate_categories(self):
        self.category_tree.clear()

        # All entries
        all_item = QTreeWidgetItem(["📁 All Entries"])
        self.category_tree.addTopLevelItem(all_item)

        # Categories
        for category in self.database.categories:
            count = len(self.database.get_entries_by_category(category))
            item = QTreeWidgetItem([f"📂 {category} ({count})"])
            self.category_tree.addTopLevelItem(item)

    def create_toolbar(self):
        colors = ThemeManager.get_theme_colors()
        toolbar = self.addToolBar("Main")
        toolbar.setStyleSheet(
            f"""
            QToolBar {{
                background: {colors['bg_secondary']};
                border: none;
                padding: 8px;
                color: {colors['text_primary']};
            }}
            QToolButton {{
                background: transparent;
                border: none;
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                color: {colors['text_primary']};
            }}
            QToolButton:hover {{
                background: {colors['bg_tertiary']};
            }}
        """
        )

        # File actions
        new_action = QAction("🆕 New Database", self)
        open_action = QAction("📁 Open Database", self)
        save_action = QAction("💾 Save", self)
        lock_action = QAction("🔒 Lock", self)

        # Clipboard actions
        stop_autoclear_action = QAction("⏹️ Stop Auto-Clear", self)
        stop_autoclear_action.setToolTip("Stop clipboard auto-clear countdown")

        new_action.triggered.connect(self.new_database)
        open_action.triggered.connect(self.open_database)
        save_action.triggered.connect(self.save_database)
        lock_action.triggered.connect(self.lock_database)
        stop_autoclear_action.triggered.connect(
            self.clipboard_manager.stop_auto_clear
        )

        toolbar.addAction(new_action)
        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addSeparator()
        toolbar.addAction(lock_action)
        toolbar.addSeparator()
        toolbar.addAction(stop_autoclear_action)

    def create_status_bar(self):
        colors = ThemeManager.get_theme_colors()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet(
            f"""
            QStatusBar {{
                background: {colors['bg_secondary']};
                border-top: 1px solid {colors['border']};
                color: {colors['text_primary']};
            }}
        """
        )
        self.status_bar.showMessage("Ready")

    def apply_modern_theme(self):
        colors = ThemeManager.get_theme_colors()
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
        """
        )

    def show_login_dialog(self):
        colors = ThemeManager.get_theme_colors()
        dialog = QDialog(self)
        dialog.setWindowTitle("SecureVault - Login")
        dialog.setModal(True)
        dialog.setFixedSize(550, 480)
        dialog.setStyleSheet(f"background: {colors['bg_primary']};")

        # Main layout with margins
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # Header section
        header_frame = QFrame()
        header_frame.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 10, 0, 10)

        title = QLabel("🔐 SecureVault")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"""
            font-size: 28px;
            font-weight: bold;
            color: {colors['text_primary']};
            margin: 10px 0px;
            """
        )

        subtitle = QLabel("Access Your Encrypted Database")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"""
            font-size: 14px;
            color: {colors['text_secondary']};
            margin-bottom: 10px;
            """
        )

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_frame)

        # File selection section
        file_section = QFrame()
        file_layout = QVBoxLayout(file_section)
        file_layout.setSpacing(12)

        # File section header
        file_label = QLabel("Database File")
        file_layout.addWidget(file_label)

        # File selection row
        file_row = QHBoxLayout()
        file_row.setSpacing(10)

        self.file_combo = QComboBox()
        self.file_combo.setMinimumHeight(40)

        # Load recent files - ensure it's a list
        recent_files = self.settings.value("recent_files", [])
        if isinstance(recent_files, str):
            recent_files = [recent_files] if recent_files else []
        elif not isinstance(recent_files, list):
            recent_files = []

        # Add placeholder text
        self.file_combo.addItem("Select a database file...")
        if recent_files:
            self.file_combo.addItems(recent_files)
            # Select last used file
            last_file = self.settings.value("last_database", "")
            if last_file and last_file in recent_files:
                self.file_combo.setCurrentText(last_file)

        browse_btn = ModernButton("Browse")
        browse_btn.setMinimumHeight(40)
        browse_btn.setMinimumWidth(100)
        browse_btn.clicked.connect(lambda: self.browse_database_file(dialog))

        file_row.addWidget(self.file_combo, 1)
        file_row.addWidget(browse_btn, 1)
        file_layout.addLayout(file_row)

        main_layout.addWidget(file_section)

        # Password section
        password_section = QFrame()
        password_layout = QVBoxLayout(password_section)
        password_layout.setSpacing(12)

        # Password section header
        password_label = QLabel("Master Password")
        password_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['text_primary']};
                margin-bottom: 5px;
            }}
            """
        )
        password_layout.addWidget(password_label)

        self.master_password_edit = ModernLineEdit("")
        self.master_password_edit.setPlaceholderText(
            "Enter your master password..."
        )
        self.master_password_edit.setEchoMode(QLineEdit.Password)
        self.master_password_edit.setMinimumHeight(40)
        password_layout.addWidget(self.master_password_edit)

        main_layout.addWidget(password_section)

        # Add some flexible space
        main_layout.addStretch(1)

        # Action buttons section
        button_frame = QFrame()
        button_frame.setStyleSheet("background: transparent;")
        button_layout = QVBoxLayout(button_frame)
        button_layout.setSpacing(12)

        # Primary action button (full width)
        unlock_btn = ModernButton("Unlock Database")
        unlock_btn.setMinimumHeight(45)
        unlock_btn.setStyleSheet(
            f"""
            ModernButton {{
                font-size: 15px;
                font-weight: bold;
                background: {colors.get('accent', '#007ACC')};
                color: white;
                border-radius: 10px;
                padding: 12px;
            }}
            ModernButton:hover {{
                background: {colors.get('accent_hover', '#005a9e')};
            }}
            """
        )
        unlock_btn.clicked.connect(lambda: self.authenticate_user(dialog))
        button_layout.addWidget(unlock_btn)

        # Secondary actions row
        secondary_row = QHBoxLayout()
        secondary_row.setSpacing(10)

        create_btn = ModernButton("Create New Database")
        create_btn.setMinimumHeight(40)
        create_btn.setStyleSheet(
            f"""
            ModernButton {{
                font-size: 14px;
                background: transparent;
                color: {colors['text_secondary']};
                border: 2px solid {colors['border']};
                border-radius: 8px;
                padding: 10px;
            }}
            ModernButton:hover {{
                background: {colors['bg_secondary']};
                color: {colors['text_primary']};
                border-color: {colors.get('accent', '#007ACC')};
            }}
            """
        )
        create_btn.clicked.connect(lambda: self.create_new_database(dialog))

        secondary_row.addWidget(create_btn)
        button_layout.addLayout(secondary_row)

        main_layout.addWidget(button_frame)

        dialog.setLayout(main_layout)

        # Set focus to password field if file is selected
        if self.file_combo.currentIndex() > 0:
            self.master_password_edit.setFocus()

        dialog.exec()

    def browse_database_file(self, dialog):
        """Open file dialog to select database file"""
        file_path, _ = QFileDialog.getOpenFileName(
            dialog,
            "Select SecureVault Database",
            self.settings.value("last_directory", ""),
            "SecureVault Files (*.svdb);;All Files (*)",
        )

        if file_path:
            # Remove placeholder if it exists
            if self.file_combo.itemText(0) == "Select a database file...":
                self.file_combo.removeItem(0)

            # Update combo box - check if item already exists
            existing_items = [
                self.file_combo.itemText(i)
                for i in range(self.file_combo.count())
            ]
            if file_path not in existing_items:
                self.file_combo.insertItem(0, file_path)  # Add at top

            self.file_combo.setCurrentText(file_path)

            # Save to settings
            self.settings.setValue(
                "last_directory", os.path.dirname(file_path)
            )

            # Add to recent files
            recent_files = self.settings.value("recent_files", [])
            if isinstance(recent_files, str):
                recent_files = [recent_files] if recent_files else []
            elif not isinstance(recent_files, list):
                recent_files = []

            if file_path not in recent_files:
                recent_files.insert(0, file_path)
                recent_files = recent_files[:5]  # Keep only last 5 files
                self.settings.setValue("recent_files", recent_files)

            # Focus password field after file selection
            self.master_password_edit.setFocus()

    def authenticate_user(self, dialog):
        file_path = self.file_combo.currentText()
        password = self.master_password_edit.text()

        if not file_path:
            QMessageBox.warning(
                dialog, "Error", "Please select a database file!"
            )
            return

        if not password:
            QMessageBox.warning(dialog, "Error", "Please enter your password!")
            return

        try:
            # Remember this file for next time
            self.settings.setValue("last_database", file_path)
            self.settings.setValue(
                "last_directory", os.path.dirname(file_path)
            )

            # Load the database
            self.current_file = file_path
            self.load_database_file(file_path, password)

            self.is_locked = False
            dialog.accept()
            self.refresh_ui()
            self.status_bar.showMessage("Database unlocked successfully")
        except Exception as e:
            QMessageBox.warning(
                dialog, "Error", f"Failed to unlock database:\n{str(e)}"
            )

    def refresh_ui(self):
        self.populate_entries_table()
        self.populate_categories()

    def populate_entries_table(self, entries=None):
        if entries is None:
            entries = self.database.entries

        self.entries_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            self.entries_table.setRowHeight(row, 50)

            # Helper to create centered item
            def centered_item(text):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                return item

            # Regular columns
            self.entries_table.setItem(
                row, 0, centered_item(entry.get("title", ""))
            )
            self.entries_table.setItem(
                row, 1, centered_item(entry.get("username", ""))
            )
            self.entries_table.setItem(
                row, 2, centered_item(entry.get("url", ""))
            )
            self.entries_table.setItem(
                row, 3, centered_item(entry.get("category", ""))
            )

            # Format modified date
            modified = entry.get("modified", "")
            if modified:
                try:
                    dt = datetime.fromisoformat(modified)
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    formatted_date = modified
            else:
                formatted_date = ""
            self.entries_table.setItem(row, 4, centered_item(formatted_date))

            # Action buttons
            self.add_action_buttons(row, entry)

    def add_action_buttons(self, row, entry):
        """Add copy buttons for username and password"""
        colors = ThemeManager.get_theme_colors()

        # Create container widget for buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(5)
        actions_layout.setAlignment(Qt.AlignCenter)

        # Copy Username button
        copy_user_btn = QPushButton("👤")
        copy_user_btn.setFixedSize(30, 25)
        copy_user_btn.setToolTip("Copy Username")
        copy_user_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {colors['bg_tertiary']};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {colors['accent_hover']};
            }}
        """
        )
        copy_user_btn.clicked.connect(lambda: self.copy_username(entry))

        # Copy Password button
        copy_pass_btn = QPushButton("🔑")
        copy_pass_btn.setFixedSize(30, 25)
        copy_pass_btn.setToolTip("Copy Password")
        copy_pass_btn.setStyleSheet(
            """
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """
        )
        copy_pass_btn.clicked.connect(lambda: self.copy_password(entry))

        # Quick Edit button
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(30, 25)
        edit_btn.setToolTip("Quick Edit")
        edit_btn.setStyleSheet(
            """
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """
        )
        edit_btn.clicked.connect(lambda: self.quick_edit_entry(row))

        # Add buttons to layout - REMOVE THE addStretch() CALL
        actions_layout.addWidget(copy_user_btn)
        actions_layout.addWidget(copy_pass_btn)
        actions_layout.addWidget(edit_btn)

        # Set the widget in the table (no need to set layout separately)
        self.entries_table.setCellWidget(row, 5, actions_widget)

    def copy_username(self, entry):
        """Copy username to clipboard with auto-clear"""
        username = entry.get("username", "")
        if username:
            self.clipboard_manager.copy_to_clipboard(username, "username")
        else:
            QMessageBox.information(
                self, "Info", "No username available for this entry."
            )

    def copy_password(self, entry):
        """Copy password to clipboard with auto-clear"""
        password = entry.get("password", "")
        if password:
            self.clipboard_manager.copy_to_clipboard(password, "password")
        else:
            QMessageBox.information(
                self, "Info", "No password available for this entry."
            )

    def quick_edit_entry(self, row):
        """Quick edit entry"""
        if row < len(self.database.entries):
            entry = self.database.entries[row]
            dialog = EntryDialog(
                entry=entry, categories=self.database.categories, parent=self
            )
            if dialog.exec() == QDialog.Accepted:
                entry_data = dialog.get_entry_data()
                if entry_data["title"]:
                    self.database.update_entry(row, entry_data)
                    self.mark_dirty()
                    self.refresh_ui()
                    self.status_bar.showMessage("Entry updated successfully")
                else:
                    QMessageBox.warning(
                        self, "Error", "Title cannot be empty!"
                    )

    def filter_entries(self, text):
        if not text:
            self.populate_entries_table()
        else:
            filtered_entries = self.database.search_entries(text)
            self.populate_entries_table(filtered_entries)

    def on_category_selected(self, item):
        category_text = item.text(0)

        if "All Entries" in category_text:
            self.populate_entries_table()
        else:
            # Extract category name (remove emoji and count)
            category = category_text.split(" ", 1)[1].split(" (")[0]
            entries = self.database.get_entries_by_category(category)
            self.populate_entries_table(entries)

    def add_entry(self):
        if self.is_locked:
            QMessageBox.warning(self, "Locked", "Database is locked!")
            return

        dialog = EntryDialog(categories=self.database.categories, parent=self)
        if dialog.exec() == QDialog.Accepted:
            entry_data = dialog.get_entry_data()
            if entry_data["title"]:  # Ensure title is not empty
                self.database.add_entry(entry_data)
                self.refresh_ui()
                self.mark_dirty()  # Mark as dirty
                self.status_bar.showMessage("Entry added successfully")
            else:
                QMessageBox.warning(self, "Error", "Title cannot be empty!")

    def edit_entry(self):
        if self.is_locked:
            QMessageBox.warning(self, "Locked", "Database is locked!")
            return

        current_row = self.entries_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "Selection", "Please select an entry to edit."
            )
            return

        # Get the entry data
        entry_id = current_row
        if entry_id < len(self.database.entries):
            entry = self.database.entries[entry_id]
            dialog = EntryDialog(
                entry=entry, categories=self.database.categories, parent=self
            )
            if dialog.exec() == QDialog.Accepted:
                entry_data = dialog.get_entry_data()
                if entry_data["title"]:
                    self.database.update_entry(entry_id, entry_data)
                    self.refresh_ui()
                    self.mark_dirty()
                    self.status_bar.showMessage("Entry updated successfully")
                else:
                    QMessageBox.warning(
                        self, "Error", "Title cannot be empty!"
                    )

    def delete_entry(self):
        if self.is_locked:
            QMessageBox.warning(self, "Locked", "Database is locked!")
            return

        current_row = self.entries_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "Selection", "Please select an entry to delete."
            )
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this entry?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.database.delete_entry(current_row)
            self.refresh_ui()
            self.status_bar.showMessage("Entry deleted successfully")

    def on_entry_double_click(self, item):
        """Handle double-click on entry to show details"""
        if self.is_locked:
            return

        row = item.row()
        if row < len(self.database.entries):
            entry = self.database.entries[row]

            # Show entry details dialog
            details_dialog = QDialog(self)
            details_dialog.setWindowTitle(
                f"Entry Details - {entry.get('title', 'Unknown')}"
            )
            details_dialog.setFixedSize(420, 300)

            layout = QVBoxLayout()
            colors = ThemeManager.get_theme_colors()

            # Entry info
            info_text = f"""
            <h3>{entry.get('title', 'N/A')}</h3>
            <p><b>Username:</b> {entry.get('username', 'N/A')}</p>
            <p><b>URL:</b> {entry.get('url', 'N/A')}</p>
            <p><b>Category:</b> {entry.get('category', 'N/A')}</p>
            <p><b>Notes:</b> {entry.get('notes', 'N/A')}</p>
            """

            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setStyleSheet(
                f"color: {colors['text_primary']}; padding: 10px;"
            )
            layout.addWidget(info_label)

            # Action buttons
            btn_layout = QHBoxLayout()

            copy_user_btn = ModernButton("Copy Username")
            copy_pass_btn = ModernButton("Copy Password")
            close_btn = ModernButton("Close")

            copy_user_btn.clicked.connect(lambda: self.copy_username(entry))
            copy_pass_btn.clicked.connect(lambda: self.copy_password(entry))
            close_btn.clicked.connect(details_dialog.close)

            btn_layout.addWidget(copy_user_btn)
            btn_layout.addWidget(copy_pass_btn)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)
            details_dialog.setLayout(layout)

            details_dialog.setStyleSheet(
                f"""
                QDialog {{
                    background: {colors['bg_primary']};
                    color: {colors['text_primary']};
                }}
            """
            )

            details_dialog.exec()

    def new_database(self):
        """Create a new database"""
        reply = QMessageBox.question(
            self,
            "New Database",
            "Create a new database? Unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.show_login_dialog()

    def open_database(self):
        """Open an existing database file"""
        from PySide6.QtWidgets import QFileDialog, QInputDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Database",
            "",
            "SecureVault Files (*.svdb);;All Files (*)",
        )

        if file_path:
            try:
                # First load the salt from file (without decrypting)
                with open(file_path, "rb") as f:
                    encrypted_data = f.read()

                # Prompt for password
                password, ok = QInputDialog.getText(
                    self,
                    "Unlock Database",
                    "Enter master password:",
                    QLineEdit.Password,
                )

                if not ok or not password:
                    return

                # Try to decrypt to extract salt
                try:
                    temp_key = SecurityManager.generate_key_from_password(
                        password, b"temp_salt"
                    )
                    decrypted_data = SecurityManager.decrypt_data(
                        encrypted_data, temp_key
                    )
                    data = json.loads(decrypted_data)
                    salt = (
                        base64.b64decode(data["salt"])
                        if "salt" in data
                        else b"salt_"
                    )
                except Exception:
                    # If we can't extract salt, use fallback
                    salt = b"salt_"

                # Now generate actual key with correct salt
                self.encryption_key = (
                    SecurityManager.generate_key_from_password(password, salt)
                )
                self.current_file = file_path
                self.salt = salt
                self.load_database_file(file_path, password)
                self.status_bar.showMessage(
                    f"Opened database: {os.path.basename(file_path)}"
                )
                self.refresh_ui()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to open database:\n{str(e)}"
                )

    def create_new_database(self, dialog):
        password = self.master_password_edit.text()
        if len(password) < 8:
            QMessageBox.warning(
                dialog, "Error", "Password must be at least 8 characters!"
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Create New Database",
            self.settings.value("last_directory", ""),
            "SecureVault Files (*.svdb);;All Files (*)",
        )

        if not file_path:
            return

        # Save directory for future use
        self.settings.setValue("last_directory", os.path.dirname(file_path))

        # Generate salt and key
        self.salt = SecurityManager.generate_salt()
        self.encryption_key = SecurityManager.generate_key_from_password(
            password, self.salt
        )

        # Initialize and save
        self.database = PasswordDatabase()
        self.current_file = file_path
        self.is_locked = False

        try:
            self.save_database_file(file_path)
            self.settings.setValue(
                "last_database", file_path
            )  # Remember this file
            dialog.accept()
            self.refresh_ui()
            self.status_bar.showMessage(
                "New database created and saved successfully"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to create database:\n{str(e)}"
            )
            self.current_file = None
            self.salt = None
            self.encryption_key = None

    def save_database(self):
        """Save with automatic handling for new databases"""
        if not self.current_file:
            return self.save_database_as()  # Handle first-time save

        try:
            self.save_database_file(self.current_file)
            self.mark_clean()  # Mark as clean after save
            self.status_bar.showMessage("Database saved successfully")
            return True
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save database:\n{str(e)}"
            )
            return False

    def save_database_as(self):
        """Save database with a new filename"""
        default_path = self.settings.value("last_directory", "")
        if self.current_file:
            default_path = os.path.dirname(self.current_file)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database As",
            default_path,
            "SecureVault Files (*.svdb);;All Files (*)",
        )

        if file_path:
            try:
                self.save_database_file(file_path)
                self.current_file = file_path
                self.mark_clean()
                self.settings.setValue("last_database", file_path)
                self.settings.setValue(
                    "last_directory", os.path.dirname(file_path)
                )
                self.status_bar.showMessage(
                    f"Database saved as: {os.path.basename(file_path)}"
                )
                return True
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save database:\n{str(e)}"
                )
        return False

    def save_database_file(self, file_path):
        """Save database to encrypted file with salt header"""
        if not self.encryption_key:
            QMessageBox.warning(self, "Error", "No encryption key available!")
            return

        # Generate salt if not exists (for new databases)
        if not self.salt:
            self.salt = SecurityManager.generate_salt()
            self.encryption_key = SecurityManager.generate_key_from_password(
                self.master_password_edit.text(), self.salt
            )

        data = {
            "entries": self.database.entries,
            "categories": self.database.categories,
            "created": datetime.now().isoformat(),
            "version": "1.3",
        }

        json_data = json.dumps(data, indent=2)
        encrypted_data = SecurityManager.encrypt_data(
            json_data, self.encryption_key
        )

        # Save with salt as header
        with open(file_path, "wb") as f:
            f.write(self.salt)  # Write salt first (16 bytes)
            f.write(encrypted_data)

        self.mark_clean()

    def load_database_file(self, file_path, password):
        """Load database from file with password verification"""
        try:
            with open(file_path, "rb") as f:
                salt = f.read(16)  # Read salt from header
                encrypted_data = f.read()

            # Generate key using salt from file
            key = SecurityManager.generate_key_from_password(password, salt)

            # Verify password by attempting decryption
            decrypted_data = SecurityManager.decrypt_data(encrypted_data, key)
            data = json.loads(decrypted_data)

            self.database.entries = data.get("entries", [])
            self.database.categories = data.get(
                "categories", self.database.categories
            )
            self.salt = salt
            self.encryption_key = key
            self.mark_clean()
        except Exception as e:
            raise Exception("Incorrect password or corrupted file") from e

    def lock_database(self):
        """Lock the database"""
        self.is_locked = True
        self.encryption_key = None
        self.entries_table.setRowCount(0)
        self.status_bar.showMessage("Database locked")

        # Show login dialog again
        self.show_login_dialog()

    def closeEvent(self, event):
        """Handle application close"""
        # Stop clipboard manager
        self.clipboard_manager.stop_auto_clear()

        # Stop auto-save timer
        self.auto_save_timer.stop()

        if self.dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                if not self.save_database():
                    # Save failed or user canceled - don't close
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()

        if self.database.entries and not self.current_file:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self.save_database_as()
                if not self.current_file:  # User cancelled save dialog
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()

    def resizeEvent(self, event):
        """Handle window resize to reposition clipboard progress"""
        super().resizeEvent(event)
        if hasattr(self, "clipboard_manager"):
            self.clipboard_manager.position_progress_widget()
