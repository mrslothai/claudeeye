"""Floating PyQt6 chat window for ClaudeEye — v9: Real logo in tray + header."""
import sys
import os
import re
import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer, QRect, QSize
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPainter, QLinearGradient, QPen,
    QBrush, QPainterPath, QFontDatabase, QPixmap
)


# ─── Design System ────────────────────────────────────────────────────────────
DS = {
    # Window
    'bg': '#f5f5f7',           # Light grey Apple-style bg
    'border': '#d2d2d7',       # Subtle grey border

    # Header
    'header_bg': '#ffffff',    # Pure white header
    'header_border': '#e5e5ea', # Light separator
    'title_color': '#1d1d1f',  # Near black text

    # User bubble (right) — dark, like iMessage
    'user_bg': '#1d1d1f',      # Near black
    'user_text': '#ffffff',    # White text

    # Claude bubble (left) — white card
    'claude_bg': '#ffffff',    # White
    'claude_border': '#e5e5ea', # Subtle border
    'claude_text': '#1d1d1f',  # Dark text

    # Input
    'input_bg': '#ffffff',
    'input_border': '#d2d2d7',
    'input_focus': '#0071e3',  # Apple blue on focus
    'input_text': '#1d1d1f',
    'placeholder': '#8e8e93',

    # Send button
    'send_bg': '#0071e3',      # Apple blue
    'send_hover': '#0077ed',

    # Status / misc
    'status_text': '#8e8e93',
    'timestamp': '#8e8e93',
    'scrollbar': '#c7c7cc',
    'live_dot': '#34c759',     # Apple green
}

FONT_STACK = "SF Pro Display, -apple-system, Segoe UI, Inter, system-ui, sans-serif"
MONO_STACK = "SF Mono, JetBrains Mono, Fira Code, Consolas, monospace"


# ─── Code Block Widget ────────────────────────────────────────────────────────
class CodeBlock(QWidget):
    """Dark code block with language label and copy-to-clipboard button."""

    def __init__(self, lang: str, code: str, parent=None):
        super().__init__(parent)
        self._lang = lang.strip() if lang else ""
        self._code = code
        self._build()

    def _build(self):
        self.setMaximumWidth(255)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Outer container style — dark background with rounded corners
        self.setObjectName("CodeBlockOuter")
        self.setStyleSheet("""
            QWidget#CodeBlockOuter {
                background: #1e1e2e;
                border-radius: 10px;
                border: 1px solid #313244;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top bar (lang label + copy button) ───────────────────────────────
        top_bar = QWidget()
        top_bar.setObjectName("CodeTopBar")
        top_bar.setFixedHeight(28)
        top_bar.setStyleSheet("""
            QWidget#CodeTopBar {
                background: transparent;
                border: none;
            }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 6, 0)
        top_layout.setSpacing(0)

        lang_lbl = QLabel(self._lang or "code")
        lang_lbl.setStyleSheet(f"""
            QLabel {{
                color: #6c7086;
                font-size: 10px;
                font-family: {MONO_STACK};
                background: transparent;
                border: none;
            }}
        """)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedHeight(20)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: #313244;
                color: #cdd6f4;
                border-radius: 4px;
                border: none;
                font-size: 10px;
                font-family: {FONT_STACK};
                padding: 0 8px;
                min-width: 44px;
            }}
            QPushButton:hover {{
                background: #45475a;
            }}
        """)
        self._copy_btn.clicked.connect(self._do_copy)

        top_layout.addWidget(lang_lbl)
        top_layout.addStretch()
        top_layout.addWidget(self._copy_btn)

        # ── Thin divider ─────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: #313244; border: none; margin: 0;")

        # ── Code text ────────────────────────────────────────────────────────
        code_label = QLabel(self._code)
        code_label.setWordWrap(True)
        code_label.setTextFormat(Qt.TextFormat.PlainText)
        code_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        code_label.setStyleSheet(f"""
            QLabel {{
                color: #cdd6f4;
                font-family: {MONO_STACK};
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 10px 12px;
            }}
        """)

        layout.addWidget(top_bar)
        layout.addWidget(div)
        layout.addWidget(code_label)

    def _do_copy(self):
        QApplication.clipboard().setText(self._code)
        self._copy_btn.setText("✓ Copied!")
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("Copy"))


# ─── Worker Thread ─────────────────────────────────────────────────────────────
class WorkerThread(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client, message, screenshot_b64):
        super().__init__()
        self.client = client
        self.message = message
        self.screenshot_b64 = screenshot_b64

    def run(self):
        try:
            response = self.client.send_message(self.message, self.screenshot_b64)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


# ─── User Bubble (dark pill, iMessage style) ───────────────────────────────────
class UserBubble(QWidget):
    """Right-aligned dark pill bubble."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._build()

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 3, 12, 3)
        outer.setSpacing(0)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Message label
        self._label = QLabel()
        self._label.setText(self._format(self._text))
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setMaximumWidth(255)
        self._label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._label.setStyleSheet(f"""
            QLabel {{
                background: {DS['user_bg']};
                color: {DS['user_text']};
                border-radius: 18px;
                padding: 10px 15px;
                font-size: 12px;
                font-family: {FONT_STACK};
                line-height: 1.6;
            }}
        """)

        # Timestamp
        ts = QLabel(datetime.now().strftime("%H:%M"))
        ts.setAlignment(Qt.AlignmentFlag.AlignRight)
        ts.setStyleSheet(f"color: {DS['timestamp']}; font-size: 9px; background: transparent; border: none; padding: 0 2px;")

        col.addWidget(self._label, 0, Qt.AlignmentFlag.AlignRight)
        col.addWidget(ts, 0, Qt.AlignmentFlag.AlignRight)

        outer.addStretch()
        outer.addLayout(col)

    def _format(self, text: str) -> str:
        def escape(s):
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        parts = re.split(r'```(\w*)\n?(.*?)```', text, flags=re.DOTALL)
        result = []
        i = 0
        lang = ""
        while i < len(parts):
            if i % 4 == 0:
                chunk = escape(parts[i])
                chunk = re.sub(
                    r'`([^`]+)`',
                    r'<span style="background:rgba(255,255,255,0.15);color:#ffffff;padding:1px 4px;font-family:' + MONO_STACK + r';font-size:11px;border-radius:3px">\1</span>',
                    chunk
                )
                chunk = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', chunk)
                chunk = chunk.replace('\n', '<br>')
                result.append(chunk)
            elif i % 4 == 1:
                lang = parts[i]
            elif i % 4 == 2:
                code = escape(parts[i].strip())
                result.append(
                    f'<div style="background:rgba(255,255,255,0.1);border-left:2px solid rgba(255,255,255,0.4);'
                    f'padding:6px 10px;margin:6px 0;font-family:{MONO_STACK};font-size:10px;'
                    f'color:#e5e5e7;border-radius:6px"><span style="color:#aeaeb2;font-size:9px">'
                    f'{lang or "code"}</span><br>{code}</div>'
                )
            i += 1
        return ''.join(result)


# ─── Claude Bubble (white card, with proper code blocks) ─────────────────────
class ClaudeBubble(QWidget):
    """Left-aligned white card bubble with syntax-aware code block rendering."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._build()

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 3, 12, 3)
        outer.setSpacing(0)

        col = QVBoxLayout()
        col.setSpacing(4)
        col.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Parse text into alternating text/code segments and build widgets
        for seg in self._parse_segments(self._text):
            if seg[0] == 'text':
                if seg[1].strip():
                    col.addWidget(self._make_text_label(seg[1]), 0, Qt.AlignmentFlag.AlignLeft)
            else:  # 'code'
                col.addWidget(CodeBlock(seg[1], seg[2]), 0, Qt.AlignmentFlag.AlignLeft)

        ts = QLabel(datetime.now().strftime("%H:%M"))
        ts.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ts.setStyleSheet(f"color: {DS['timestamp']}; font-size: 9px; background: transparent; border: none; padding: 0 2px;")
        col.addWidget(ts, 0, Qt.AlignmentFlag.AlignLeft)

        outer.addLayout(col)
        outer.addStretch()

    def _parse_segments(self, text: str):
        """Return list of ('text', content) and ('code', lang, code) tuples."""
        # re.split with 2 capture groups → parts repeat as: text, lang, code, text, lang, code ...
        parts = re.split(r'```(\w*)\n?(.*?)```', text, flags=re.DOTALL)
        segments = []
        i = 0
        lang = ""
        while i < len(parts):
            idx = i % 3
            if idx == 0:
                segments.append(('text', parts[i]))
            elif idx == 1:
                lang = parts[i]
            else:  # idx == 2
                segments.append(('code', lang, parts[i].strip()))
            i += 1
        return segments

    def _make_text_label(self, text: str) -> QLabel:
        """Build a styled QLabel for a plain-text (non-code) segment."""
        label = QLabel()
        label.setText(self._format_text(text))
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setMaximumWidth(255)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label.setStyleSheet(f"""
            QLabel {{
                background: {DS['claude_bg']};
                color: {DS['claude_text']};
                border-radius: 18px;
                border: 1px solid {DS['claude_border']};
                padding: 10px 15px;
                font-size: 12px;
                font-family: {FONT_STACK};
                line-height: 1.6;
            }}
        """)
        return label

    def _format_text(self, text: str) -> str:
        """Format a plain-text segment (no fenced code blocks) as HTML."""
        def escape(s):
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        chunk = escape(text)
        # Inline code spans
        chunk = re.sub(
            r'`([^`]+)`',
            r'<span style="background:#f2f2f7;color:#1d1d1f;padding:1px 4px;font-family:'
            + MONO_STACK + r';font-size:11px;border-radius:3px">\1</span>',
            chunk
        )
        chunk = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', chunk)
        chunk = re.sub(r'\*(.+?)\*', r'<i>\1</i>', chunk)
        # Bullet points
        chunk = re.sub(r'^[-•] (.+)$', r'• \1', chunk, flags=re.MULTILINE)
        chunk = chunk.replace('\n', '<br>')
        return chunk


# ─── Typing Indicator ──────────────────────────────────────────────────────────
class TypingIndicator(QWidget):
    """Animated dots to show Claude is thinking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 12, 4)
        self._label = QLabel("●  ●  ●")
        self._label.setStyleSheet(f"""
            QLabel {{
                background: {DS['claude_bg']};
                color: {DS['status_text']};
                border-radius: 18px;
                border: 1px solid {DS['claude_border']};
                padding: 8px 14px;
                font-size: 11px;
                letter-spacing: 3px;
            }}
        """)
        layout.addWidget(self._label)
        layout.addStretch()

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        dots = ["●  ○  ○", "●  ●  ○", "●  ●  ●", "○  ●  ●"][self._dots]
        self._label.setText(dots)

    def start(self):
        self._timer.start(400)

    def stop(self):
        self._timer.stop()


# ─── Clean Frame (window chrome) ─────────────────────────────────────────────
class GlassFrame(QWidget):
    """Main window frame with subtle light border."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 18, 18)

        # Fill with light grey background
        painter.fillPath(path, QColor(DS['bg']))

        # Subtle grey border — no glow
        pen = QPen(QColor(DS['border']), 1)
        painter.setPen(pen)
        painter.drawPath(path)


# ─── Focus-aware Input ────────────────────────────────────────────────────────
class GlassInput(QLineEdit):
    """Input with Apple blue focus ring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._focused = False
        self._apply_style(False)

    def _apply_style(self, focused: bool):
        border = DS['input_focus'] if focused else DS['input_border']
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {DS['input_bg']};
                color: {DS['input_text']};
                border: 1.5px solid {border};
                border-radius: 22px;
                padding: 10px 16px;
                font-size: 12px;
                font-family: {FONT_STACK};
            }}
            QLineEdit::placeholder {{
                color: {DS['placeholder']};
            }}
        """)

    def focusInEvent(self, event):
        self._apply_style(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._apply_style(False)
        super().focusOutEvent(event)


# ─── Main Window ──────────────────────────────────────────────────────────────
class ClaudeEyeWindow(QWidget):
    _status_update = pyqtSignal(str)
    _add_message   = pyqtSignal(str, bool)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.drag_pos = QPoint()
        self._worker = None
        self._typing = None
        self._init_ui()
        self._status_update.connect(self._on_status)
        self._add_message.connect(self._append_bubble)

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 580)
        self.move(50, 80)

        # Outer wrapper (transparent, for translucency)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)

        # Clean frame
        self.frame = GlassFrame()
        self.frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outer_layout.addWidget(self.frame)

        inner = QVBoxLayout(self.frame)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header_widget = QWidget()
        header_widget.setFixedHeight(48)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background: {DS['header_bg']};
                border-radius: 18px 18px 0 0;
                border-bottom: 1px solid {DS['header_border']};
            }}
        """)
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(14, 0, 10, 0)
        header.setSpacing(8)

        eye_label = QLabel("👁")
        eye_label.setStyleSheet("font-size: 15px; background: transparent; border: none;")

        title_label = QLabel("ClaudeEye")
        title_label.setStyleSheet(f"""
            color: {DS['title_color']};
            font-weight: 700;
            font-size: 13px;
            font-family: {FONT_STACK};
            background: transparent;
            border: none;
            letter-spacing: 0.3px;
        """)

        # Version badge
        badge = QLabel("v7")
        badge.setStyleSheet(f"""
            background: #f2f2f7;
            color: {DS['status_text']};
            font-size: 9px;
            font-family: {FONT_STACK};
            font-weight: 600;
            border: 1px solid {DS['border']};
            border-radius: 6px;
            padding: 1px 5px;
        """)

        self._mode_label = QLabel("● LIVE")
        self._mode_label.setStyleSheet(f"color: {DS['live_dot']}; font-size: 9px; font-family: {FONT_STACK}; background: transparent; border: none;")

        clear_btn = QPushButton("⟳")
        clear_btn.setFixedSize(28, 28)
        clear_btn.setToolTip("Clear conversation")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: #f2f2f7;
                color: {DS['status_text']};
                border-radius: 14px;
                border: 1px solid {DS['border']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {DS['border']};
                color: {DS['title_color']};
            }}
        """)
        clear_btn.clicked.connect(self._clear_chat)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Hide window (Ctrl+Shift+Space to show)")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: #f2f2f7;
                color: {DS['status_text']};
                border-radius: 14px;
                border: 1px solid {DS['border']};
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(239,68,68,0.12);
                color: #e53e3e;
                border-color: rgba(239,68,68,0.3);
            }}
        """)
        close_btn.clicked.connect(self.hide)

        header.addWidget(eye_label)
        header.addWidget(title_label)
        header.addWidget(badge)
        header.addStretch()
        header.addWidget(self._mode_label)
        header.addSpacing(6)
        header.addWidget(clear_btn)
        header.addWidget(close_btn)
        inner.addWidget(header_widget)

        # ── Chat scroll area ──────────────────────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 3px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {DS['scrollbar']};
                border-radius: 1px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #aeaeb2;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 10, 0, 10)
        self.chat_layout.setSpacing(6)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        inner.addWidget(self.scroll_area, 1)

        # Thin divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {DS['header_border']}; border: none;")
        inner.addWidget(div)

        # ── Bottom bar ────────────────────────────────────────────────────────
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background: transparent;")
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(12, 8, 12, 14)
        bottom_layout.setSpacing(8)

        # Status
        self.status_label = QLabel("📸 Screen captured with every message")
        self.status_label.setStyleSheet(f"""
            color: {DS['status_text']};
            font-size: 10px;
            font-family: {FONT_STACK};
            background: transparent;
        """)
        bottom_layout.addWidget(self.status_label)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_field = GlassInput()
        self.input_field.setPlaceholderText("Ask about your screen…")
        self.input_field.returnPressed.connect(self._send_message)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(42, 42)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DS['send_bg']};
                color: white;
                border-radius: 21px;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {DS['send_hover']};
            }}
            QPushButton:pressed {{
                background: #005bbf;
            }}
            QPushButton:disabled {{
                background: {DS['border']};
                color: {DS['status_text']};
            }}
        """)
        self.send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)
        bottom_layout.addLayout(input_row)
        inner.addWidget(bottom_widget)

        # ── Welcome message ───────────────────────────────────────────────────
        self._append_bubble(
            "👁 **ClaudeEye v7** — Code blocks with copy button!\n\n"
            "I can see your screen in real-time.\n"
            "Hotkey: `Ctrl+Shift+Space`\n\n"
            "Ask me anything about what's on screen.",
            False
        )

    # ── Message Handling ──────────────────────────────────────────────────────
    def _append_bubble(self, text: str, is_user: bool):
        if is_user:
            bubble = UserBubble(text)
        else:
            bubble = ClaudeBubble(text)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(60, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _show_typing(self):
        self._typing = TypingIndicator()
        self._typing.start()
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._typing)
        QTimer.singleShot(60, self._scroll_to_bottom)

    def _hide_typing(self):
        if self._typing:
            self._typing.stop()
            self._typing.deleteLater()
            self._typing = None

    def _clear_chat(self):
        self.client.clear_history()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._append_bubble("Conversation cleared. Ask me anything!", False)

    def _on_status(self, text: str):
        self.status_label.setText(text)

    # ── Send Flow ─────────────────────────────────────────────────────────────
    def _send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.send_btn.setEnabled(False)
        self._append_bubble(text, True)
        self._status_update.emit("📸 Capturing screen…")

        def capture_and_send():
            from screenshot import capture_screen_silent
            try:
                screenshot = capture_screen_silent()
                self._status_update.emit("🤔 Thinking…")
            except Exception as e:
                screenshot = None
                self._status_update.emit(f"⚠ Screenshot failed: {e}")

            self._worker = WorkerThread(self.client, text, screenshot)
            self._worker.response_ready.connect(self._on_response)
            self._worker.error_occurred.connect(self._on_error)
            self._worker.started.connect(self._show_typing)
            self._worker.start()

        threading.Thread(target=capture_and_send, daemon=True).start()

    def _on_response(self, response: str):
        self._hide_typing()
        self._add_message.emit(response, False)
        self._status_update.emit("📸 Screen captured with every message")
        self.send_btn.setEnabled(True)

    def _on_error(self, error: str):
        self._hide_typing()
        self._add_message.emit(f"⚠ **Error:** {error}", False)
        self._status_update.emit("📸 Screen captured with every message")
        self.send_btn.setEnabled(True)

    # ── Window close → hide to tray (don't hang) ─────────────────────────────
    def closeEvent(self, event):
        event.ignore()  # Don't actually close
        self.hide()     # Just hide to tray

    # ── Drag to move ──────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_pos)
