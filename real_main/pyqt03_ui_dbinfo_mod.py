import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pyqt03_dbinfo import db_info,update_engine
from pyqt03_ui_basic import LogViewer

##### 메인윈도우
class Mainwindow(QMainWindow):
    def __init__(self, parent=None):
        super(Mainwindow, self).__init__(parent)

        ##### 메인화면 꾸미기 함수 실행
        self.initUi()

        ##### 위젯클래스 메인윈도우의 센터에 셋팅
        self.mywidget = Widgets(self)
        self.setCentralWidget(self.mywidget)

    ##### 메인화면 꾸미기
    def initUi(self):
        self.setWindowTitle("Database Connection Settings")
        self.setGeometry(300, 300, 400, 300)


##### 위젯영역
class Widgets(QWidget):
    def __init__(self, parent):
        super(Widgets, self).__init__(parent)

        ##### 위젯 함수 실행
        self.initWidget()

    ##### 위젯셋팅
    def initWidget(self):
        # 레이블과 입력 필드 생성
        label_username = QLabel("Username:", self)
        self.text_username = QLineEdit(self)

        label_password = QLabel("Password:", self)
        self.text_password = QLineEdit(self)
        self.text_password.setEchoMode(QLineEdit.Password)  # 비밀번호 감추기

        label_database = QLabel("Database:", self)
        self.text_database = QLineEdit(self)

        label_host = QLabel("Host:", self)
        self.text_host = QLineEdit(self)

        label_port = QLabel("Port:", self)
        self.text_port = QLineEdit(self)

        # 확인 버튼
        self.btn_submit = QPushButton("Submit", self)
        self.btn_submit.clicked.connect(self.submit)

        # 레이아웃 설정
        form_layout = QFormLayout(self)
        form_layout.addRow(label_username, self.text_username)
        form_layout.addRow(label_password, self.text_password)
        form_layout.addRow(label_database, self.text_database)
        form_layout.addRow(label_host, self.text_host)
        form_layout.addRow(label_port, self.text_port)
        form_layout.addRow(self.btn_submit)

        self.setLayout(form_layout)

    ##### 데이터 제출
    def submit(self):
        try:
            db_info["username"]= self.text_username.text()
            db_info["password"] = self.text_password.text()
            db_info["database"] = self.text_database.text()
            db_info["host"] = self.text_host.text()
            db_info["port"] = self.text_port.text()

            update_engine()
            # 입력된 데이터 출력
            QMessageBox.information(self, "Notification", "수정되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"DB 연결 수정 중 오류 발생: {str(e)}")
