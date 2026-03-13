"""Floating PyQt6 chat window for ClaudeEye — v2 with chat bubbles + code blocks."""
import sys
import re
import threading
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QTextBrowser, QLineEdit, QPushButton, QLabel, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QFont, QTextCursor


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


def format_message_html(text: str, is_user: bool) -> str:
    """Convert plain text (with code blocks) to chat bubble HTML using table layout."""

    def escape(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def render_code_block(lang, code):
        code_escaped = escape(code.strip())
        lang_label = f'<div style="color:#a78bfa;font-size:9px;font-family:monospace;margin-bottom:4px">{lang or "code"}</div>'
        return f'<div style="background:#0f0f1a;border-left:3px solid #7c3aed;border-radius:4px;padding:8px 10px;margin:4px 0;font-family:Courier New,monospace;font-size:11px;color:#e2e8f0;white-space:pre-wrap">{lang_label}{code_escaped}</div>'

    # Split on code blocks
    parts = re.split(r'```(\w*)\n?(.*?)```', text, flags=re.DOTALL)

    html_parts = []
    i = 0
    lang = ''
    while i < len(parts):
        if i % 4 == 0:
            chunk = parts[i]
            if chunk.strip():
                chunk = re.sub(r'`([^`]+)`', r'<span style="background:#1e1e2e;color:#a78bfa;padding:1px 3px;border-radius:3px;font-family:monospace;font-size:11px">\1</span>', escape(chunk))
                chunk = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', chunk)
                chunk = chunk.replace('\n', '<br>')
                html_parts.append(f'<span style="font-size:12px;line-height:1.6;color:#e2e8f0">{chunk}</span>')
        elif i % 4 == 1:
            lang = parts[i]
        elif i % 4 == 2:
            html_parts.append(render_code_block(lang, parts[i]))
        i += 1

    content = ''.join(html_parts)

    if is_user:
        # User message — right aligned using table
        return f'''<table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td width="30%"></td>
            <td width="70%" align="right">
                <table cellpadding="0" cellspacing="0"><tr><td>
                <div style="background:#7c3aed;color:white;border-radius:16px 16px 4px 16px;padding:8px 12px;font-size:12px;margin:2px 0 6px 0">
                    {content}
                </div>
                </td></tr></table>
            </td>
        </tr></table>'''
    else:
        # Claude message — left aligned using table
        return f'''<table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td width="70%" align="left">
                <table cellpadding="0" cellspacing="0"><tr><td>
                <div style="background:#1e1e2e;border:1px solid #3b2d6e;border-radius:16px 16px 16px 4px;padding:8px 12px;font-size:12px;margin:2px 0 6px 0;color:#e2e8f0">
                    {content}
                </div>
                </td></tr></table>
            </td>
            <td width="30%"></td>
        </tr></table>'''


class ClaudeEyeWindow(QWidget):
    _status_update = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.drag_pos = QPoint()
        self._worker = None
        self._init_ui()
        self._status_update.connect(self.status_label.setText)

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
                background-color: rgba(10, 10, 18, 245);
                border-radius: 18px;
                border: 1px solid rgba(120, 80, 255, 0.35);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main)

        inner = QVBoxLayout(main)
        inner.setContentsMargins(0, 0, 0, 12)
        inner.setSpacing(0)

        # Header bar
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: rgba(120, 80, 255, 0.15);
                border-radius: 18px 18px 0 0;
                border-bottom: 1px solid rgba(120,80,255,0.2);
            }
        """)
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(14, 10, 10, 10)

        eye_label = QLabel("👁")
        eye_label.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        title = QLabel("ClaudeEye")
        title.setStyleSheet("color: #a78bfa; font-weight: bold; font-size: 13px; background: transparent; border: none;")

        clear_btn = QPushButton("⟳")
        clear_btn.setFixedSize(26, 26)
        clear_btn.setToolTip("Clear conversation")
        clear_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.08); color: #9ca3af;
                         border-radius: 13px; border: none; font-size: 13px; }
            QPushButton:hover { background: rgba(120,80,255,0.4); color: white; }
        """)
        clear_btn.clicked.connect(self._clear_chat)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.08); color: #9ca3af;
                         border-radius: 13px; border: none; font-size: 11px; }
            QPushButton:hover { background: rgba(239,68,68,0.7); color: white; }
        """)
        close_btn.clicked.connect(self.hide)

        header.addWidget(eye_label)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        header.addWidget(close_btn)
        inner.addWidget(header_widget)

        # Chat area
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                border: none;
                padding: 8px 12px;
                color: #e2e8f0;
            }
            QScrollBar:vertical {
                background: transparent; width: 4px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(120,80,255,0.4); border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        inner.addWidget(self.chat_display, 1)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(120,80,255,0.15);")
        inner.addWidget(divider)

        # Status + input
        bottom = QWidget()
        bottom.setStyleSheet("background: transparent;")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 8, 12, 0)
        bottom_layout.setSpacing(6)

        self.status_label = QLabel("📸 Screen captured with every message")
        self.status_label.setStyleSheet("color: #4b5563; font-size: 10px;")
        bottom_layout.addWidget(self.status_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask about your screen...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.06);
                color: #f1f5f9;
                border: 1px solid rgba(120,80,255,0.25);
                border-radius: 12px;
                padding: 9px 14px;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid rgba(120,80,255,0.65);
                background: rgba(255,255,255,0.09);
            }
        """)
        self.input_field.returnPressed.connect(self._send_message)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(38, 38)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #7c3aed,stop:1 #6d28d9);
                color: white; border-radius: 19px; border: none;
                font-size: 17px; font-weight: bold;
            }
            QPushButton:hover { background: #8b5cf6; }
            QPushButton:disabled { background: #374151; color: #6b7280; }
        """)
        self.send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)
        bottom_layout.addLayout(input_row)
        inner.addWidget(bottom)

        # Welcome
        self._append_html(format_message_html("👁 **ClaudeEye v2** — I can see your screen!\n\nHotkey: `Ctrl+Shift+Space`\nAsk me anything about what's on your screen.", is_user=False))

    def _append_html(self, html: str):
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_display.insertHtml(html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def _clear_chat(self):
        self.client.clear_history()
        self.chat_display.clear()
        self._append_html(format_message_html("Conversation cleared. Ask me anything!", is_user=False))

    def _send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.send_btn.setEnabled(False)
        self._append_html(format_message_html(text, is_user=True))
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
        self._append_html(format_message_html(response, is_user=False))
        self.status_label.setText("📸 Screen captured with every message")
        self.send_btn.setEnabled(True)

    def _on_error(self, error: str):
        self._append_html(format_message_html(f"⚠ Error: {error}", is_user=False))
        self.status_label.setText("📸 Screen captured with every message")
        self.send_btn.setEnabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_pos)
