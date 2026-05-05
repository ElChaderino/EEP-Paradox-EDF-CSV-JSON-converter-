"""Shared Qt stylesheet for EEG_EDF_Standalone_Tool."""

ACCENT = "#3db8a6"
ACCENT_HOVER = "#52d4c2"
ACCENT_MUTED = "#2d8a7c"
BG_MAIN = "#181b20"
BG_ELEVATED = "#222730"
BG_INPUT = "#11151b"
BG_SOFT = "#1d222a"
BORDER = "#3b4453"
TEXT = "#edf0f4"
TEXT_DIM = "#aab3c2"
TEXT_MUTED = "#737d8d"
WARNING = "#d8b45f"


def application_stylesheet() -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {BG_MAIN};
        color: {TEXT};
        font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
        font-size: 13px;
    }}

    QLabel#HeaderTitle {{
        font-size: 23px;
        font-weight: 650;
        color: {TEXT};
    }}
    QLabel#HeaderSubtitle {{
        font-size: 12px;
        color: {TEXT_DIM};
        margin-top: 2px;
    }}
    QLabel#SectionHint {{
        font-size: 11px;
        color: {TEXT_MUTED};
        padding: 4px 0 8px 0;
    }}
    QLabel#ChecklistLine {{
        color: {TEXT_DIM};
        background: {BG_SOFT};
        border: 1px solid #303846;
        border-radius: 6px;
        padding: 8px 10px;
    }}
    QLabel#SignalTitle {{
        color: {ACCENT_HOVER};
        font-size: 16px;
        font-weight: 650;
        padding-bottom: 6px;
    }}
    QLabel#SummaryValue {{
        color: {TEXT};
        font-weight: 550;
    }}

    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        background: {BG_ELEVATED};
        top: -1px;
        padding: 12px;
    }}
    QTabBar::tab {{
        background: {BG_INPUT};
        color: {TEXT_DIM};
        padding: 10px 22px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border: 1px solid {BORDER};
        border-bottom: none;
        min-width: 110px;
    }}
    QTabBar::tab:selected {{
        background: {BG_ELEVATED};
        color: {ACCENT_HOVER};
        font-weight: 650;
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        color: {TEXT};
        background: #29303a;
    }}

    QGroupBox {{
        font-weight: 650;
        font-size: 12px;
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 14px;
        padding: 18px 12px 12px 12px;
        background: {BG_INPUT};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        color: {ACCENT};
    }}

    QPushButton {{
        background-color: {BG_ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        padding: 9px 18px;
        border-radius: 6px;
        min-height: 22px;
    }}
    QPushButton:hover {{
        border-color: {ACCENT_MUTED};
        background: #2a3240;
    }}
    QPushButton:pressed {{
        background: {BG_INPUT};
    }}
    QPushButton:disabled {{
        color: {TEXT_MUTED};
        border-color: #333842;
        background: #1e2229;
    }}
    QPushButton#PrimaryButton {{
        background-color: {ACCENT_MUTED};
        color: #ffffff;
        border: none;
        font-weight: 650;
        padding: 11px 24px;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {ACCENT};
    }}
    QPushButton#PrimaryButton:pressed {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#AccentOutline {{
        border: 1px solid {ACCENT};
        color: {ACCENT_HOVER};
        background: transparent;
        font-weight: 600;
    }}
    QPushButton#AccentOutline:hover {{
        background: #1d302f;
    }}

    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
        background: {BG_MAIN};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        min-height: 20px;
        selection-background-color: {ACCENT_MUTED};
    }}
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
        border-color: {ACCENT};
    }}
    QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        border: none;
        width: 22px;
    }}
    QComboBox QAbstractItemView {{
        background: {BG_ELEVATED};
        color: {TEXT};
        selection-background-color: {ACCENT_MUTED};
        border: 1px solid {BORDER};
    }}

    QTextEdit {{
        background: {BG_MAIN};
        color: #cfd5df;
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px;
        font-family: "Cascadia Code", "Consolas", ui-monospace, monospace;
        font-size: 11px;
        line-height: 1.35;
    }}

    QListWidget {{
        background: {BG_MAIN};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 9px 10px;
        border-radius: 5px;
        margin: 2px 0;
        color: {TEXT_DIM};
    }}
    QListWidget::item:selected {{
        background: rgba(61, 184, 166, 0.22);
        color: {TEXT};
        border-left: 3px solid {ACCENT};
    }}
    QListWidget::item:hover:!selected {{
        background: #252c36;
        color: {TEXT};
    }}

    QCheckBox {{
        spacing: 10px;
        color: {TEXT_DIM};
    }}
    QCheckBox:hover {{
        color: {TEXT};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {BORDER};
        background: {BG_MAIN};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT_MUTED};
        border-color: {ACCENT};
    }}

    QSplitter::handle {{
        background: {BORDER};
        width: 2px;
    }}
    QSplitter::handle:hover {{
        background: {ACCENT};
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QSlider::groove:horizontal {{
        height: 8px;
        background: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT};
        width: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: rgba(61, 184, 166, 0.35);
        border-radius: 4px;
    }}
    QScrollBar:vertical {{
        background: {BG_INPUT};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: #4a5568;
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {ACCENT_MUTED};
    }}

    QStatusBar {{
        background: {BG_INPUT};
        color: {TEXT_DIM};
        border-top: 1px solid {BORDER};
        padding: 6px 12px;
        font-size: 11px;
    }}
    """
