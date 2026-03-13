"""Floating PyQt6 chat window for ClaudeEye — v3 with widget-based chat bubbles."""
import sys
import re
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette


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


class MessageBubble(QWidget):
    """A single chat message bubble."""

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self._build(text)

    def _build(self, text: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 2, 8, 2)
        outer.setSpacing(0)

        # Build label text (handle code blocks simply)
        display_text = self._format(text)

        label = QLabel()
        label.setText(display_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setMaximumWidth(260)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        if self.is_user:
            label.setStyleSheet("""
                QLabel {
                    background-color: #7c3aed;
                    color: white;
                    border-radius: 16px;
                    padding: 8px 12px;
                    font-size: 12px;
                    line-height: 1.5;
                }
            """)
            outer.addStretch()
            outer.addWidget(label)
        else:
            label.setStyleSheet("""
                QLabel {
                    background-color: #1a1a2e;
                    color: #e2e8f0;
                    border-radius: 16px;
                    border-left: 3px solid #7c3aed;
                    padding: 8px 12px;
                    font-size: 12px;
                    line-height: 1.5;
                }
            """)
            outer.addWidget(label)
            outer.addStretch()

    def _format(self, text: str) -> str:
        """Simple text formatting for Qt RichText."""
        def escape(s):
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Split code blocks from regular text
        parts = re.split(r'```(\w*)\n?(.*?)```', text, flags=re.DOTALL)
        result = []
        i = 0
        while i < len(parts):
            if i % 4 == 0:
                chunk = escape(parts[i])
                # Inline code
                chunk = re.sub(r'`([^`]+)`', r'<span style="background:#1e1e2e;color:#a78bfa;padding:1px 3px;font-family:monospace;font-size:11px">\1</span>', chunk)
                # Bold
                chunk = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', chunk)
                # Newlines
                chunk = chunk.replace('\n', '<br>')
                result.append(chunk)
            elif i % 4 == 1:
                lang = parts[i]
            elif i % 4 == 2:
                code = escape(parts[i].strip())
                result.append(f'<div style="background:#0d0d1a;border-left:2px solid #7c3aed;padding:4px 8px;margin:4px 0;font-family:Courier New,monospace;font-size:11px;color:#a5b4fc;border-radius:4px"><span style="color:#6366f1;font-size:9px">{lang or "code"}</span><br>{code}</div>')
            i += 1
        return ''.join(result)


class ClaudeEyeWindow(QWidget):
    _status_update = pyqtSignal(str)
    _add_message = pyqtSignal(str, bool)  # text, is_user

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.drag_pos = QPoint()
        self._worker = None
        self._init_ui()
        self._status_update.connect(self.status_label.setText)
        self._add_message.connect(self._append_bubble)

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 560)
        self.move(50, 100)

        main = QWidget(self)
        main.setObjectName("main")
        main.setStyleSheet("""
            QWidget#main {
                background-color: rgba(10, 10, 20, 248);
                border-radius: 18px;
                border: 1px solid rgba(120, 80, 255, 0.4);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main)

        inner = QVBoxLayout(main)
        inner.setContentsMargins(0, 0, 0, 12)
        inner.setSpacing(0)

        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: rgba(120, 80, 255, 0.12);
                border-radius: 18px 18px 0 0;
            }
        """)
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(14, 10, 10, 10)

        eye = QLabel("👁")
        eye.setStyleSheet("font-size:16px;background:transparent;border:none;")
        title = QLabel("ClaudeEye")
        title.setStyleSheet("color:#a78bfa;font-weight:bold;font-size:13px;background:transparent;border:none;")

        clear_btn = QPushButton("⟳")
        clear_btn.setFixedSize(26, 26)
        clear_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.08);color:#9ca3af;border-radius:13px;border:none;font-size:13px;}QPushButton:hover{background:rgba(120,80,255,0.4);color:white;}")
        clear_btn.clicked.connect(self._clear_chat)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.08);color:#9ca3af;border-radius:13px;border:none;font-size:11px;}QPushButton:hover{background:rgba(239,68,68,0.7);color:white;}")
        close_btn.clicked.connect(self.hide)

        header.addWidget(eye)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        header.addWidget(close_btn)
        inner.addWidget(header_widget)

        # Scroll area for chat bubbles
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: rgba(120,80,255,0.4); border-radius: 2px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 8, 0, 8)
        self.chat_layout.setSpacing(4)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        inner.addWidget(self.scroll_area, 1)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: rgba(120,80,255,0.15);")
        inner.addWidget(div)

        # Bottom
        bottom = QWidget()
        bottom.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(12, 8, 12, 0)
        bl.setSpacing(6)

        self.status_label = QLabel("📸 Screen captured with every message")
        self.status_label.setStyleSheet("color:#4b5563;font-size:10px;")
        bl.addWidget(self.status_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask about your screen...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.06);
                color: #f1f5f9;
                border: 1px solid rgba(120,80,255,0.3);
                border-radius: 12px;
                padding: 9px 14px;
                font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid rgba(120,80,255,0.7); }
        """)
        self.input_field.returnPressed.connect(self._send_message)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(38, 38)
        self.send_btn.setStyleSheet("""
            QPushButton { background: #7c3aed; color: white; border-radius: 19px; border: none; font-size: 17px; font-weight: bold; }
            QPushButton:hover { background: #8b5cf6; }
            QPushButton:disabled { background: #374151; color: #6b7280; }
        """)
        self.send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)
        bl.addLayout(input_row)
        inner.addWidget(bottom)

        # Welcome message
        self._append_bubble("👁 **ClaudeEye v3** — I can see your screen!\n\nHotkey: `Ctrl+Shift+Space`\nAsk me anything!", False)

    def _append_bubble(self, text: str, is_user: bool):
        """Add a message bubble widget to the chat."""
        bubble = MessageBubble(text, is_user)
        # Insert before the stretch at the end
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def _clear_chat(self):
        self.client.clear_history()
        # Remove all bubbles (keep the stretch)
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._append_bubble("Conversation cleared. Ask me anything!", False)

    def _send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.send_btn.setEnabled(False)
        self._append_bubble(text, True)
        self.status_label.setText("📸 Capturing screen...")

        def capture_and_send():
            from screenshot import capture_screen_silent
            try:
                screenshot = capture_screen_silent()
                self._status_update.emit("🤔 Thinking...")
            except Exception as e:
                screenshot = None
                self._status_update.emit(f"⚠ Screenshot failed: {e}")

            self._worker = WorkerThread(self.client, text, screenshot)
            self._worker.response_ready.connect(self._on_response)
            self._worker.error_occurred.connect(self._on_error)
            self._worker.start()

        threading.Thread(target=capture_and_send, daemon=True).start()

    def _on_response(self, response: str):
        self._add_message.emit(response, False)
        self.status_label.setText("📸 Screen captured with every message")
        self.send_btn.setEnabled(True)

    def _on_error(self, error: str):
        self._add_message.emit(f"⚠ Error: {error}", False)
        self.status_label.setText("📸 Screen captured with every message")
        self.send_btn.setEnabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_pos)
