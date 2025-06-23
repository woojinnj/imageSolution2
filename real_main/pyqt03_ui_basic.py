from PyQt5 import QtWidgets
import logging
import threading
from uvicorn import Config, Server
from fastapi import FastAPI

# PyQt 로그 핸들러 정의
class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.widget.setFixedHeight(400)
        self.widget.setFixedWidth(400)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


# PyQt UI 정의
class LogViewer(QtWidgets.QDialog):
    def __init__(self, app: FastAPI, parent=None):
        super().__init__(parent)
        self.fastapi_app = app  # FastAPI 애플리케이션 저장

        self.logTextBox = QTextEditLogger(self)
        self.logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        logging.getLogger().setLevel(logging.INFO)

        self.startButton = QtWidgets.QPushButton("서버 시작")
        self.stopButton = QtWidgets.QPushButton("서버 중지")
        self.stopButton.setEnabled(False)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.logTextBox.widget)
        layout.addWidget(self.startButton)
        layout.addWidget(self.stopButton)
        self.setLayout(layout)

        self.startButton.clicked.connect(self.start_server)
        self.stopButton.clicked.connect(self.stop_server)

        self.server_thread = None
        self.server_running = False
        self.server_instance = None

    def start_server(self):
        if not self.server_running:
            logging.info("FastAPI 서버를 시작합니다.")
            self.server_running = True
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            self.startButton.setEnabled(False)
            self.stopButton.setEnabled(True)

    def stop_server(self):
        if self.server_running and self.server_instance:
            logging.info("FastAPI 서버를 중지합니다.")
            self.server_instance.should_exit = True  # 서버 종료 플래그 설정
            self.server_running = False
            self.startButton.setEnabled(True)
            self.stopButton.setEnabled(False)
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=1)  # 스레드 종료 대기

    def run_server(self):
        config = Config(app=self.fastapi_app, host="127.0.0.1", port=8000, log_level="info")
        self.server_instance = Server(config)
        self.server_instance.run()

    def closeEvent(self, event):
        event.ignore()
        self.hide()



