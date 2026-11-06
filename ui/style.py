DARK_THEME_QSS = """
/* Professional Engineering Dark Theme (JetBrains / VS Code aesthetic) */

/* Global Reset */
QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 11px;
    selection-background-color: #264f78;
    selection-color: #ffffff;
}

/* Main Window & Surfaces */
QMainWindow {
    background-color: #181818;
}

/* Splitters: Crisp 1px appearance with subtle drag area */
QSplitter::handle {
    background-color: #2d2d30;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QSplitter::handle:hover {
    background-color: #007acc;
}

/* Top Action Bar & Containers */
QWidget#topBar {
    background-color: #252526;
    border-bottom: 1px solid #333337;
    padding: 2px 6px;
}

/* Sidebar Navigation */
QWidget#sidebar {
    background-color: #252526;
    border-right: 1px solid #333337;
}

QWidget#sidebar QPushButton {
    text-align: left;
    padding: 6px 10px;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 0px;
    font-size: 11px;
    font-weight: 500;
    color: #969696;
    background-color: transparent;
    letter-spacing: 0.3px;
}

QWidget#sidebar QPushButton:hover {
    background-color: #2a2d2e;
    color: #e0e0e0;
}

QWidget#sidebar QPushButton:checked {
    background-color: #1e1e1e;
    color: #ffffff;
    font-weight: 600;
    border-left: 2px solid #007acc;
}

/* Inputs & Editors */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #181818;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    padding: 3px 6px;
    selection-background-color: #264f78;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #007acc;
    background-color: #141414;
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: #222222;
    color: #666666;
    border-color: #333333;
}

/* Push Buttons - Clean Industrial */
QPushButton {
    background-color: #333337;
    color: #cccccc;
    border: 1px solid #3e3e42;
    border-radius: 2px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 400;
}

QPushButton:hover {
    background-color: #3e3e42;
    border-color: #555555;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #252526;
}

QPushButton:disabled {
    background-color: #252526;
    color: #555555;
    border-color: #2d2d30;
}

/* Primary Action Button (Send) */
QPushButton#btnSend {
    background-color: #0e639c;
    color: #ffffff;
    border: 1px solid #1177bb;
    font-weight: 600;
    padding: 3px 12px;
}

QPushButton#btnSend:hover {
    background-color: #1177bb;
    border-color: #1688d0;
}

QPushButton#btnSend:pressed {
    background-color: #094771;
}

QPushButton#btnSend:disabled {
    background-color: #252526;
    color: #555555;
    border-color: #2d2d30;
}

/* Danger / Cancel Button */
QPushButton#btnCancel {
    background-color: #5a1d1d;
    color: #f8d7da;
    border: 1px solid #782626;
    padding: 3px 8px;
}

QPushButton#btnCancel:hover {
    background-color: #782626;
    border-color: #9c3232;
    color: #ffffff;
}

QPushButton#btnCancel:pressed {
    background-color: #3f1414;
}

QPushButton#btnCancel:disabled {
    background-color: #252526;
    color: #555555;
    border-color: #2d2d30;
}

/* Accent Buttons */
QPushButton#btnAccent {
    background-color: #0e639c;
    color: #ffffff;
    border: 1px solid #1177bb;
}

QPushButton#btnAccent:hover {
    background-color: #1177bb;
}

/* Tabs - Professional Flat Editor Tabs */
QTabWidget::pane {
    border: 1px solid #2d2d30;
    background-color: #181818;
    top: -1px;
}

QTabBar::tab {
    background-color: #252526;
    color: #969696;
    border: 1px solid #2d2d30;
    border-bottom: none;
    padding: 4px 10px;
    margin-right: 1px;
    font-size: 11px;
    border-top: 1px solid transparent;
}

QTabBar::tab:selected {
    background-color: #181818;
    color: #ffffff;
    border-top: 2px solid #007acc;
    border-bottom: 1px solid #181818;
    font-weight: 500;
}

QTabBar::tab:hover:!selected {
    background-color: #2d2d30;
    color: #cccccc;
}

/* Table Widgets & Grids */
QTableWidget, QTableView {
    background-color: #181818;
    gridline-color: #2d2d30;
    border: 1px solid #2d2d30;
    color: #cccccc;
    font-size: 11px;
}

QTableWidget::item {
    padding: 2px 4px;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #252526;
    color: #858585;
    padding: 3px 6px;
    border: 1px solid #2d2d30;
    border-top: none;
    border-left: none;
    font-weight: 600;
    font-size: 10px;
    text-transform: uppercase;
}

/* Status Badges */
QLabel#badgeStatus {
    font-size: 11px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 2px;
}

/* SpinBoxes */
QSpinBox, QDoubleSpinBox {
    background-color: #181818;
    color: #cccccc;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    padding: 2px 4px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #007acc;
}

/* Checkboxes */
QCheckBox {
    color: #cccccc;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    background-color: #181818;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}

QCheckBox::indicator:hover {
    border-color: #007acc;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #333337;
    border-radius: 2px;
    margin-top: 12px;
    font-weight: 600;
    font-size: 11px;
    color: #858585;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    background-color: #1e1e1e;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: #1e1e1e;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 20px;
    border-radius: 0px;
}

QScrollBar::handle:vertical:hover {
    background-color: #686868;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #1e1e1e;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #424242;
    min-width: 20px;
    border-radius: 0px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #686868;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Tooltips */
QToolTip {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3e3e42;
    padding: 3px 6px;
    border-radius: 2px;
    font-size: 10px;
}

/* Progress Bar */
QProgressBar {
    background-color: #252526;
    border: 1px solid #333337;
    border-radius: 1px;
}

QProgressBar::chunk {
    background-color: #007acc;
}
"""
