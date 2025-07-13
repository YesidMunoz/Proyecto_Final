import sys
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.uic import loadUi

app = QApplication(sys.argv)
ventana = QDialog()
loadUi("menuppal_senales.ui", ventana)
ventana.show()
sys.exit(app.exec_())
