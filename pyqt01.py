import sys
import logging
import os
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon

# 간단한 로그 포맷 정의
date_strftime_format = "%H:%M:%S"  # 시간만 표시 (시:분:초)
message_format = "%(asctime)s - %(levelname)s : %(message)s"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,  # 로그 수준
    format=message_format,
    datefmt=date_strftime_format,
    encoding="utf-8",
)


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True) #읽기만 가능
        self.widget.setFixedHeight(300) # 로그창 높이 300픽셀

    def emit(self, record): #로그 띄우기
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.ensureCursorVisible()

    def clear(self): #로그 지우기
        self.widget.clear()


class ExternalProcessThread(QThread):
    # 프로세스 출력 신호
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None

    def run(self):
        try:
            # Uvicorn 서버 실행
            self.process = subprocess.Popen(
                ["uvicorn", "imageApi:app", "--reload"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True,  # 프로세스 그룹 생성
            )

            # 실시간으로 출력 읽기
            for line in self.process.stdout:
                self.output_signal.emit(line.strip())

            for line in self.process.stderr:
                self.error_signal.emit(line.strip())

        except Exception as e:
            self.error_signal.emit(f"Error: {str(e)}")

    def stop(self):
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), 9)  # 프로세스 그룹 종료
            except Exception as e:
                self.error_signal.emit(f"Error stopping process: {str(e)}")
            finally:
                self.process = None


class MyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 창 크기 설정
        self.resize(800, 600)

        # 로그 위젯 설정
        self.logTextBox = QTextEditLogger(self)
        self.logTextBox.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s : %(message)s", datefmt="%H:%M:%S")
        )
        logging.getLogger().addHandler(self.logTextBox)
        logging.getLogger().setLevel(logging.DEBUG)

        # 버튼 설정
        self.start_button = QtWidgets.QPushButton(self)
        self.start_button.setText("Start Server")

        self.stop_button = QtWidgets.QPushButton(self)
        self.stop_button.setText("Stop Server")

        self.clear_button = QtWidgets.QPushButton(self)
        self.clear_button.setText("Clear Logs")

        # 레이아웃 설정
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.logTextBox.widget)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.clear_button)
        self.setLayout(layout)

        # 트레이 아이콘 설정
        self.tray_icon = QSystemTrayIcon(QIcon("/Users/woojin/Desktop/test/imageSolution/images/moonicon.png"), self)
        tray_menu = QMenu()

        # 트레이 메뉴 옵션 추가
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show)  # 창 다시 표시
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)  # 애플리케이션 종료

        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("My PyQt Application")

        # 트레이 아이콘 동작 연결
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

        # 버튼 클릭 이벤트 연결
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        self.clear_button.clicked.connect(self.clear_logs)

    def on_tray_icon_activated(self, reason):
        """
        트레이 아이콘 활성화 시 동작 처리.
        """
        if reason == QSystemTrayIcon.DoubleClick:  # 더블 클릭 이벤트 처리
            self.show()  # 창 다시 표시
            self.raise_()  # 창을 최상위로 올림

    def closeEvent(self, event):
        """
        닫기 버튼 클릭 시 창 숨김 및 트레이 아이콘 유지.
        """
        logging.info("Hiding window to menu bar...")
        self.hide()  # 창 숨기기
        self.tray_icon.showMessage(
            "My Application",
            "Application is still running in the menu bar.",
            QSystemTrayIcon.Information,
            2000,
        )
        event.ignore()  # 닫기 이벤트 무시

    def exit_app(self):
        """
        트레이 메뉴에서 종료를 선택했을 때 애플리케이션 종료.
        """
        logging.info("Exiting application...")
        self.tray_icon.hide()  # 트레이 아이콘 숨기기
        self.process_thread.stop()  # 실행 중인 서버 종료
        QtWidgets.QApplication.quit()  # 애플리케이션 종료

    def start_server(self):
        logging.info("Starting server...")
        self.process_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_server(self):
        logging.info("Stopping server...")
        self.process_thread.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def clear_logs(self):
        self.logTextBox.clear()

    def log_output(self, message):
        logging.info(message)

    def log_error(self, message):
        logging.error(message)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dlg = MyDialog()
    dlg.show()
    dlg.raise_()
    sys.exit(app.exec_())
