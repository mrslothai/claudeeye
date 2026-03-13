"""Floating PyQt6 chat window for ClaudeEye — v5: Premium cyberpunk-lite redesign."""
import sys
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
    QBrush, QPainterPath, QFontDatabase
)


# ─── Design System ────────────────────────────────────────────────────────────
DS = {
    "bg":           "#080812",
    "surface":      "#0d0d1f",
    "purple":       "#8b5cf6",
    "purple_dark":  "#7c3aed",
    "purple_deep":  "#6d28d9",
    "purple_glow":  "#a78bfa",
    "text":         "#f1f5f9",
    "text_muted":   "#94a3b8",
    "text_dim":     "#475569",
    "border":       "rgba(139, 92, 246, 0.2)",
    "glass_bg":     "rgba(255, 255, 255, 0.04)",
    "glass_border": "rgba(139, 92, 246, 0.15)",
}

FONT_STACK = "SF Pro Display, -apple-system, Segoe UI, Inter, system-ui, sans-serif"
MONO_STACK = "SF Mono, JetBrains Mono, Fira Code, Consolas, monospace"


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


# ─── User Bubble (gradient pill) ──────────────────────────────────────────────
class UserBubble(QWidget):
    """Right-aligned gradient purple pill bubble."""

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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #6d28d9);
                color: #ffffff;
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
        ts.setStyleSheet(f"color: {DS['text_dim']}; font-size: 9px; background: transparent; border: none; padding: 0 2px;")

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
                    r'<span style="background:rgba(0,0,0,0.3);color:#e2e8f0;padding:1px 4px;font-family:' + MONO_STACK + r';font-size:11px;border-radius:3px">\1</span>',
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
                    f'<div style="background:rgba(0,0,0,0.35);border-left:2px solid rgba(167,139,250,0.6);'
                    f'padding:6px 10px;margin:6px 0;font-family:{MONO_STACK};font-size:10px;'
                    f'color:#c4b5fd;border-radius:6px"><span style="color:#a78bfa;font-size:9px">'
                    f'{lang or "code"}</span><br>{code}</div>'
                )
            i += 1
        return ''.join(result)


# ─── Claude Bubble (glass card) ───────────────────────────────────────────────
class ClaudeBubble(QWidget):
    """Left-aligned glass-effect card with purple accent line."""

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
        col.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._label = QLabel()
        self._label.setText(self._format(self._text))
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setMaximumWidth(255)
        self._label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._label.setStyleSheet(f"""
            QLabel {{
                background: rgba(255, 255, 255, 0.04);
                color: #e2e8f0;
                border-radius: 0 18px 18px 0;
                border: 1px solid rgba(139, 92, 246, 0.12);
                border-left: 2px solid #8b5cf6;
                padding: 10px 15px 10px 13px;
                font-size: 12px;
                font-family: {FONT_STACK};
                line-height: 1.6;
            }}
        """)

        ts = QLabel(datetime.now().strftime("%H:%M"))
        ts.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ts.setStyleSheet(f"color: {DS['text_dim']}; font-size: 9px; background: transparent; border: none; padding: 0 2px;")

        col.addWidget(self._label, 0, Qt.AlignmentFlag.AlignLeft)
        col.addWidget(ts, 0, Qt.AlignmentFlag.AlignLeft)

        outer.addLayout(col)
        outer.addStretch()

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
                    r'<span style="background:#1e1e3a;color:#a78bfa;padding:1px 4px;font-family:' + MONO_STACK + r';font-size:11px;border-radius:3px">\1</span>',
                    chunk
                )
                chunk = re.sub(r'\*\*(.+?)\*\*', r'<b style="color:#c4b5fd">\1</b>', chunk)
                chunk = re.sub(r'\*(.+?)\*', r'<i>\1</i>', chunk)
                # Bullet points
                chunk = re.sub(r'^[-•] (.+)$', r'• \1', chunk, flags=re.MULTILINE)
                chunk = chunk.replace('\n', '<br>')
                result.append(chunk)
            elif i % 4 == 1:
                lang = parts[i]
            elif i % 4 == 2:
                code = escape(parts[i].strip())
                result.append(
                    f'<div style="background:#0a0a1a;border-left:2px solid #7c3aed;'
                    f'padding:6px 10px;margin:6px 0;font-family:{MONO_STACK};font-size:10px;'
                    f'color:#a5b4fc;border-radius:0 6px 6px 0">'
                    f'<span style="color:#6366f1;font-size:9px;font-weight:bold">'
                    f'{lang.upper() if lang else "CODE"}</span><br>{code}</div>'
                )
            i += 1
        return ''.join(result)


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
                background: rgba(255,255,255,0.04);
                color: {DS['purple']};
                border-radius: 0 16px 16px 0;
                border: 1px solid {DS['glass_border']};
                border-left: 2px solid {DS['purple']};
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


# ─── Glass Frame (window chrome) ─────────────────────────────────────────────
class GlassFrame(QWidget):
    """Main window frame with glow border."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 18, 18)

        # Fill
        painter.fillPath(path, QColor("#080812"))

        # Glow border
        pen = QPen(QColor(139, 92, 246, 60), 1)
        painter.setPen(pen)
        painter.drawPath(path)

        # Subtle top highlight
        highlight = QPainterPath()
        highlight.addRoundedRect(rect.x(), rect.y(), rect.width(), 1, 1, 1)
        painter.fillPath(highlight, QColor(167, 139, 250, 40))


# ─── Focus-aware Input ────────────────────────────────────────────────────────
class GlassInput(QLineEdit):
    """Input with purple glow on focus."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._focused = False
        self._apply_style(False)

    def _apply_style(self, focused: bool):
        border = "rgba(139,92,246,0.8)" if focused else "rgba(139,92,246,0.25)"
        shadow = "0 0 0 2px rgba(139,92,246,0.15)" if focused else "none"
        self.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255,255,255,0.05);
                color: {DS['text']};
                border: 1px solid {border};
                border-radius: 22px;
                padding: 10px 16px;
                font-size: 12px;
                font-family: {FONT_STACK};
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
        outer_layout.setContentsMargins(6, 6, 6, 6)  # room for glow

        # Glass frame
        self.frame = GlassFrame()
        self.frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outer_layout.addWidget(self.frame)

        inner = QVBoxLayout(self.frame)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header_widget = QWidget()
        header_widget.setFixedHeight(48)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(124,58,237,0.18), stop:1 rgba(109,40,217,0.06));
                border-radius: 18px 18px 0 0;
                border-bottom: 1px solid rgba(139,92,246,0.12);
            }
        """)
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(14, 0, 10, 0)
        header.setSpacing(8)

        eye_label = QLabel("👁")
        eye_label.setStyleSheet("font-size: 15px; background: transparent; border: none;")

        title_label = QLabel("ClaudeEye")
        title_label.setStyleSheet(f"""
            color: {DS['purple_glow']};
            font-weight: 700;
            font-size: 13px;
            font-family: {FONT_STACK};
            background: transparent;
            border: none;
            letter-spacing: 0.3px;
        """)

        # Version badge
        badge = QLabel("v5")
        badge.setStyleSheet(f"""
            background: rgba(139,92,246,0.15);
            color: {DS['purple']};
            font-size: 9px;
            font-family: {FONT_STACK};
            font-weight: 600;
            border: 1px solid rgba(139,92,246,0.3);
            border-radius: 6px;
            padding: 1px 5px;
        """)

        self._mode_label = QLabel("● LIVE")
        self._mode_label.setStyleSheet(f"color: #34d399; font-size: 9px; font-family: {FONT_STACK}; background: transparent; border: none;")

        clear_btn = QPushButton("⟳")
        clear_btn.setFixedSize(28, 28)
        clear_btn.setToolTip("Clear conversation")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.06);
                color: {DS['text_muted']};
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.06);
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: rgba(139,92,246,0.3);
                color: white;
                border-color: rgba(139,92,246,0.5);
            }}
        """)
        clear_btn.clicked.connect(self._clear_chat)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Hide window (Ctrl+Shift+Space to show)")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06);
                color: #94a3b8;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.06);
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239,68,68,0.65);
                color: white;
                border-color: rgba(239,68,68,0.5);
            }
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
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 3px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(139, 92, 246, 0.35);
                border-radius: 1px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(139, 92, 246, 0.6);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
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
        div.setStyleSheet("background: rgba(139,92,246,0.1); border: none;")
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
            color: {DS['text_dim']};
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
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                color: white;
                border-radius: 21px;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a78bfa, stop:1 #8b5cf6);
            }
            QPushButton:pressed {
                background: #6d28d9;
            }
            QPushButton:disabled {
                background: rgba(55, 65, 81, 0.8);
                color: #4b5563;
            }
        """)
        self.send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)
        bottom_layout.addLayout(input_row)
        inner.addWidget(bottom_widget)

        # ── Welcome message ───────────────────────────────────────────────────
        self._append_bubble(
            "👁 **ClaudeEye v5** — Premium redesign!\n\n"
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

    # ── Drag to move ──────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_pos)
