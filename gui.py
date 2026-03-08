"""Floating PyQt6 chat window for ClaudeEye."""
import sys
import threading
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QTextEdit, QLineEdit, QPushButton, QLabel)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon


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


class ClaudeEyeWindow(QWidget):
    # Signal to update status from non-main thread
    _status_update = pyqtSignal(str)
    _start_worker = pyqtSignal(str, object)  # message, screenshot

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.drag_pos = QPoint()
        self._worker = None
        self._init_ui()
        self._status_update.connect(self.status_label.setText)

    def _init_ui(self):
        # Window flags: always on top, frameless, tool window (doesn't appear in taskbar)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(380, 520)
        self.move(50, 100)

        # Main container
        main = QWidget(self)
        main.setObjectName("main")
        main.setStyleSheet("""
            QWidget#main {
                background-color: rgba(15, 15, 20, 235);
                border-radius: 16px;
                border: 1px solid rgba(120, 80, 255, 0.4);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main)

        inner = QVBoxLayout(main)
        inner.setContentsMargins(12, 10, 12, 12)
        inner.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title = QLabel("👁 ClaudeEye")
        title.setStyleSheet("color: #a78bfa; font-weight: bold; font-size: 13px;")

        clear_btn = QPushButton("⟳")
        clear_btn.setFixedSize(24, 24)
        clear_btn.setToolTip("Clear conversation")
        clear_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.1); color: #aaa;
                         border-radius: 12px; border: none; font-size: 13px; }
            QPushButton:hover { background: rgba(100,100,255,0.4); color: white; }
        """)
        clear_btn.clicked.connect(self._clear_chat)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.1); color: #aaa;
                         border-radius: 12px; border: none; font-size: 11px; }
            QPushButton:hover { background: rgba(255,80,80,0.6); color: white; }
        """)
        close_btn.clicked.connect(self.hide)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        header.addWidget(close_btn)
        inner.addLayout(header)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background: rgba(0,0,0,0);
                color: #e2e8f0;
                border: none;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                selection-background-color: rgba(120,80,255,0.4);
            }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: rgba(120,80,255,0.5); border-radius: 2px; }
        """)
        inner.addWidget(self.chat_display, 1)

        # Status label
        self.status_label = QLabel("📸 Screenshots auto-captured")
        self.status_label.setStyleSheet("color: #64748b; font-size: 10px;")
        inner.addWidget(self.status_label)

        # Input area
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask about your screen...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.07);
                color: white;
                border: 1px solid rgba(120,80,255,0.3);
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid rgba(120,80,255,0.7); }
        """)
        self.input_field.returnPressed.connect(self._send_message)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setStyleSheet("""
            QPushButton { background: #7c3aed; color: white; border-radius: 18px;
                         border: none; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background: #6d28d9; }
            QPushButton:disabled { background: #374151; color: #6b7280; }
        """)
        self.send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)
        inner.addLayout(input_row)

        # Welcome message
        self._append_message("ClaudeEye", "👁 I can see your screen. Ask me anything!", "#a78bfa")

    def _append_message(self, sender: str, text: str, color: str = "#e2e8f0"):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.append(f'<span style="color:{color};font-weight:bold">{sender}</span>')
        self.chat_display.append(f'<span style="color:#e2e8f0">{text}</span><br>')
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def _clear_chat(self):
        self.client.clear_history()
        self.chat_display.clear()
        self._append_message("ClaudeEye", "👁 Conversation cleared. Ask me anything!", "#a78bfa")

    def _send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.send_btn.setEnabled(False)
        self._append_message("You", text, "#60a5fa")
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
        self._append_message("ClaudeEye", response, "#a78bfa")
        self.status_label.setText("📸 Screenshots auto-captured")
        self.send_btn.setEnabled(True)

    def _on_error(self, error: str):
        self._append_message("Error", error, "#f87171")
        self.status_label.setText("📸 Screenshots auto-captured")
        self.send_btn.setEnabled(True)

    # Drag to move
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_pos)
