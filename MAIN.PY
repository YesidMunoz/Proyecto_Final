from VISTA import *
# ------------------------ EJECUCIÓN ------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaLogin()
    ventana.show()
    sys.exit(app.exec_())
