import sys
from PyQt5 import QtWidgets
import logging

date_strftime_format = "%d-%b-%y %H:%M:%S"
message_format = "%(asctime)s - %(levelname)s : %(message)s"
logging.basicConfig(filename='log.log', level=logging.INFO, format=message_format, datefmt=date_strftime_format,
                    encoding='utf-8')


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.widget.setFixedHeight(150)
        self.widget.verticalScrollBar().setValue(
            self.widget.verticalScrollBar().maximum())

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.ensureCursorVisible()
        self.widget.viewport().update()

    def clear(self):
        self.widget.clear()


class MyDialog(QtWidgets.QDialog, QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.logTextBox = QTextEditLogger(self)
        self.logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        logging.getLogger().setLevel(logging.DEBUG)

        self._button1 = QtWidgets.QPushButton(self)
        self._button1.setText('Test Me')

        self._button2 = QtWidgets.QPushButton(self)
        self._button2.setText('Clear')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.logTextBox.widget)
        layout.addWidget(self._button1)
        layout.addWidget(self._button2)
        self.setLayout(layout)

        self._button1.clicked.connect(self.test)
        self._button2.clicked.connect(self.clear)

    def test(self):
        logging.debug('test 안녕')

    def clear(self):
        self.logTextBox.clear()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dlg = MyDialog()
    dlg.show()
    dlg.raise_()
    sys.exit(app.exec_())