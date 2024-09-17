import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit

class SimpleInputTest(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.textEdit = QTextEdit()
        layout.addWidget(self.textEdit)
        self.setLayout(layout)
        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Simple PyQt Input Test')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SimpleInputTest()
    ex.show()
    sys.exit(app.exec_())