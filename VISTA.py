import sys
import numpy as np
import nibabel as nib
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from scipy.ndimage import zoom
import cv2

from CONTROLADOR import ControladorLogin, ControladorDicom


# ------------------------ VENTANA LOGIN ------------------------
class VentanaLogin(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("VentanaLogin.ui", self)
        self.setWindowTitle("Login")
        self.controlador = ControladorLogin(self)
        self.boton_ingresar.clicked.connect(self.intentar_login)

    def intentar_login(self):
        usuario = self.campo_usuario.text()
        contrasena = self.campo_contrasena.text()
        self.controlador.autenticar(usuario, contrasena)

    def mostrar_mensaje(self, mensaje):
        self.label_info.setText(mensaje)

    def abrir_menu_imagenes(self):
        self.menu_imagenes = MenuImagenes(self)
        self.menu_imagenes.show()
        self.hide()

    def abrir_menu_senales(self):
        print("📣 Se ejecutó abrir_menu_senales")  # DEPURACIÓN
        QMessageBox.information(self, "Debug", "Se ejecutó abrir_menu_senales")
        self.menu_senales = MenuSenales(self)
        self.menu_senales.show()
        self.hide()

# ------------------------ MENÚ PRINCIPAL IMÁGENES ------------------------
class MenuImagenes(QDialog):
    def __init__(self, login_window):
        super().__init__()
        loadUi("menuppal_imagenes.ui", self)
        self.setWindowTitle("Menú Imágenes")
        self.login_window = login_window

        self.boton_imagmed.clicked.connect(self.abrir_menu_imagenes_medicas)
        self.boton_salir_imagenes.clicked.connect(self.volver_login)
        self.boton_imagconven.clicked.connect(self.abrir_menu_imagenes_convencionales)

    def abrir_menu_imagenes_medicas(self):
        self.menu_medicas = MenuImagenesMedicas(self)
        self.menu_medicas.show()
        self.hide()
    
    def abrir_menu_imagenes_convencionales(self):
        self.menu_convencionales = MenuImagenesConvencionales(self)
        self.menu_convencionales.show()
        self.hide()


    def volver_login(self):
        self.login_window.show()
        self.close()


# ------------------------ MENÚ IMÁGENES MÉDICAS ------------------------
class MenuImagenesMedicas(QDialog):
    def __init__(self, menu_anterior):
        super().__init__()
        loadUi("menu_imagenes_medicas.ui", self)
        self.setWindowTitle("Menú Imágenes Médicas")
        self.menu_anterior = menu_anterior
        self.controlador = ControladorDicom(self)
        self.nifti_cargado = False
        self.nifti_convertido = False  # 🔹 Bandera de conversión

        # Conectar botones
        self.boton_volver.clicked.connect(self.volver_menu_anterior)
        self.boton_cargar_dicom.clicked.connect(self.cargar_dicom)
        self.boton_cargar_nifti.clicked.connect(self.cargar_nifti)
        self.boton_convertir_a_nifti.clicked.connect(self.convertir_a_nifti)
        self.boton_guardar_datos.clicked.connect(self.guardar_datos)  # ✅ CONEXIÓN NUEVA
        self.boton_ver_metadatos.clicked.connect(self.ver_metadatos)
        self.boton_mostrar_cortes.clicked.connect(self.abrir_ventana_cortes)

        # 🔹 Estado inicial de botones
        self.boton_convertir_a_nifti.setEnabled(False)
        self.boton_guardar_datos.setEnabled(False)
        self.habilitar_botones(False)

    def volver_menu_anterior(self):
        self.menu_anterior.show()
        self.close()

    def cargar_dicom(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta DICOM")
        if carpeta:
            self.controlador.cargar_dicom_desde_carpeta(carpeta)
            self.nifti_cargado = False
            self.nifti_convertido = False
            self.boton_convertir_a_nifti.setEnabled(True)
            self.boton_guardar_datos.setEnabled(False)

    def cargar_nifti(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo NIfTI", "", "NIfTI files (*.nii *.nii.gz)")
        if archivo:
            try:
                self.nifti_data = nib.load(archivo).get_fdata()
                self.nifti_cargado = True
                self.nifti_convertido = False
                self.mostrar_mensaje("✅ NIfTI cargado correctamente.")
                self.boton_convertir_a_nifti.setEnabled(False)
                self.boton_guardar_datos.setEnabled(False)
            except Exception as e:
                self.mostrar_mensaje(f"❌ Error al cargar NIfTI: {e}")
                self.nifti_cargado = False
                self.boton_guardar_datos.setEnabled(False)

    def convertir_a_nifti(self):
        try:
            self.controlador.convertir_a_nifti()
            self.mostrar_mensaje("✅ Conversión a NIfTI completada.")
            self.nifti_convertido = True
            self.boton_guardar_datos.setEnabled(True)  # ✅ Se habilita solo si fue exitoso
        except Exception as e:
            self.mostrar_mensaje(f"❌ Error en la conversión: {e}")
            self.boton_guardar_datos.setEnabled(False)

    def guardar_datos(self):
        if self.nifti_convertido:
            try:
                self.controlador.guardar_datos()
            except Exception as e:
                self.mostrar_mensaje(f"❌ No se pudo guardar: {e}")
        else:
            self.mostrar_mensaje("⚠️ Primero debes convertir el DICOM a NIfTI.")

    def ver_metadatos(self):
        self.controlador.ver_metadatos()

    def mostrar_metadatos(self, texto):
        msg = QMessageBox(self)
        msg.setWindowTitle("Metadatos DICOM")
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg.setIcon(QMessageBox.Information)
        if len(texto) > 4000:
            texto = texto[:4000] + "\n\n... (truncado)"
        msg.setText(texto)
        msg.exec_()

    def mostrar_mensaje(self, mensaje):
        QMessageBox.information(self, "Mensaje", mensaje)

    def habilitar_botones(self, estado):
        self.boton_ver_metadatos.setEnabled(estado)
        self.boton_mostrar_cortes.setEnabled(estado)

    def abrir_ventana_cortes(self):
        volumen = self.controlador.get_volumen()
        pixel_spacing = self.controlador.get_pixel_spacing()
        self.ventana_cortes = VentanaCortes(volumen, pixel_spacing, self)
        self.ventana_cortes.show()
        self.hide()

# ------------------------ VENTANA DE CORTES ------------------------
class VentanaCortes(QDialog):
    def __init__(self, volumen, pixel_spacing, menu_anterior):
        super().__init__()
        loadUi("ventana_cortes.ui", self)
        self.setWindowTitle("Visualizador de Cortes")

        self.volumen = volumen
        self.pixel_spacing = pixel_spacing
        self.menu_anterior = menu_anterior

        self.slider_transversal.setMaximum(self.volumen.shape[0] - 1)
        self.slider_coronal.setMaximum(self.volumen.shape[1] - 1)
        self.slider_sagital.setMaximum(self.volumen.shape[2] - 1)

        self.slider_transversal.valueChanged.connect(self.actualizar_transversal)
        self.slider_coronal.valueChanged.connect(self.actualizar_coronal)
        self.slider_sagital.valueChanged.connect(self.actualizar_sagital)
        self.boton_volver.clicked.connect(self.volver_al_menu)

        self.actualizar_transversal()
        self.actualizar_coronal()
        self.actualizar_sagital()

    def volver_al_menu(self):
        self.menu_anterior.show()
        self.close()

    def normalizar_img(self, img):
        img = img.astype(np.float32)
        img -= img.min()
        if img.max() > 0:
            img /= img.max()
        img *= 255
        return img.astype(np.uint8)

    def np2qimage(self, img):
        qimg = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_Grayscale8)
        return QPixmap.fromImage(qimg)

    def mostrar_en_label(self, img, label):
        pixmap = self.np2qimage(img).scaled(label.size(), Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

    def actualizar_transversal(self):
        idx = self.slider_transversal.value()
        corte = self.volumen[idx, :, :]
        self.mostrar_en_label(self.normalizar_img(corte), self.label_transversal)

    def actualizar_coronal(self):
        idx = self.slider_coronal.value()
        corte = self.volumen[:, idx, :]
        factor = self.pixel_spacing[2] / self.pixel_spacing[0]
        corte_resized = zoom(corte, (factor, 1.0), order=1)
        self.mostrar_en_label(self.normalizar_img(corte_resized), self.label_coronal)

    def actualizar_sagital(self):
        idx = self.slider_sagital.value()
        corte = self.volumen[:, :, idx]
        factor = self.pixel_spacing[2] / self.pixel_spacing[1]
        corte_resized = zoom(corte, (factor, 1.0), order=1)
        self.mostrar_en_label(self.normalizar_img(corte_resized), self.label_sagital)

# ------------------------ MENÚ IMÁGENES CONVENCIONALES ------------------------
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
import cv2
from CONTROLADOR import ControladorImagenConvencional

class MenuImagenesConvencionales(QDialog):
    def __init__(self, menu_anterior):
        super().__init__()
        loadUi("Menu_imagenes_convencionales.ui", self)
        self.setWindowTitle("Procesamiento de Imágenes Convencionales")
        self.menu_anterior = menu_anterior
        self.controlador = ControladorImagenConvencional(self)

        # Inicialización de widgets
        self.spin_umbral.setRange(0, 255)
        self.spin_umbral.setValue(127)

        self.combo_morfologia.addItems(["Apertura", "Cierre"])
        self.combo_morfologia.setEnabled(False)

        self.spin_kernel.setMinimum(1)
        self.spin_kernel.setSingleStep(2)
        self.spin_kernel.setValue(3)
        self.spin_kernel.setEnabled(False)

        self.combo_espacio_color.addItems(["RGB", "GRAY", "HSV", "LAB"])
        self.combo_espacio_color.setEnabled(False)

        # Conectar botones
        self.boton_cargar_imagen.clicked.connect(self.cargar_imagen)
        self.boton_aplicar_color.clicked.connect(self.aplicar_cambio_color)
        self.boton_ecualizar.clicked.connect(self.aplicar_ecualizacion)
        self.boton_binarizar.clicked.connect(self.aplicar_binarizacion)
        self.boton_morfologia.clicked.connect(self.aplicar_morfologia)
        self.boton_contar.clicked.connect(self.contar_celulas)
        self.boton_filtro_extra.clicked.connect(self.aplicar_filtro_extra)  # ✅ Nuevo botón
        self.boton_reiniciar.clicked.connect(self.reiniciar_imagen)
        self.boton_volver.clicked.connect(self.volver_al_menu)

        self.habilitar_botones(False)

    def habilitar_botones(self, estado):
        self.boton_aplicar_color.setEnabled(estado)
        self.boton_ecualizar.setEnabled(estado)
        self.boton_binarizar.setEnabled(estado)
        self.spin_umbral.setEnabled(estado)
        self.boton_morfologia.setEnabled(estado)
        self.combo_morfologia.setEnabled(estado)
        self.spin_kernel.setEnabled(estado)
        self.boton_contar.setEnabled(estado)
        self.combo_espacio_color.setEnabled(estado)
        self.boton_filtro_extra.setEnabled(estado)  # ✅ Activar nuevo botón
        self.boton_reiniciar.setEnabled(estado)
        self.boton_cargar_imagen.setEnabled(True)
        self.boton_volver.setEnabled(True)
        self.boton_filtro_extra.setEnabled(estado)


    def cargar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)"
        )
        if ruta:
            try:
                imagen = self.controlador.cargar_imagen(ruta)
                self.mostrar_imagen(imagen, self.label_imagen_original)

                if hasattr(self, 'label_imagen_procesada'):
                    self.label_imagen_procesada.clear()

                if hasattr(self, 'label_resultado_celulas'):
                    self.label_resultado_celulas.setText("")
                else:
                    print("⚠️ Advertencia: No se encontró 'label_resultado_celulas' en el UI.")

                self.habilitar_botones(True)
            except Exception as e:
                print(f"❌ Error al cargar imagen: {e}")

    def mostrar_imagen(self, img, label):
        if len(img.shape) == 2:
            qimg = QImage(
                img.data, img.shape[1], img.shape[0], img.strides[0],
                QImage.Format_Grayscale8
            )
        else:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            qimg = QImage(
                img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], img.strides[0],
                QImage.Format_RGB888
            )
        pixmap = QPixmap.fromImage(qimg).scaled(label.size(), Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

    def aplicar_cambio_color(self):
        try:
            espacio = self.combo_espacio_color.currentText()
            img = self.controlador.cambiar_espacio_color(espacio)
            self.mostrar_imagen(img, self.label_imagen_procesada)
        except Exception as e:
            print(f"❌ Error al cambiar espacio de color: {e}")

    def aplicar_ecualizacion(self):
        try:
            img = self.controlador.ecualizar_imagen()
            self.mostrar_imagen(img, self.label_imagen_procesada)
        except Exception as e:
            print(f"❌ Error al ecualizar imagen: {e}")

    def aplicar_binarizacion(self):
        try:
            umbral = self.spin_umbral.value()
            img = self.controlador.binarizar_imagen(umbral)
            self.mostrar_imagen(img, self.label_imagen_procesada)
        except Exception as e:
            print(f"❌ Error al binarizar imagen: {e}")

    def aplicar_morfologia(self):
        try:
            tipo = self.combo_morfologia.currentText().lower()
            kernel = self.spin_kernel.value()
            img = self.controlador.aplicar_morfologia(tipo, kernel)
            self.mostrar_imagen(img, self.label_imagen_procesada)
        except Exception as e:
            print(f"❌ Error en operación morfológica: {e}")

    def contar_celulas(self):
        try:
            cantidad, img = self.controlador.contar_celulas()
            self.mostrar_imagen(img, self.label_imagen_procesada)
            if hasattr(self, 'label_resultado_celulas'):
                self.label_resultado_celulas.setText(f"Células detectadas: {cantidad}")
            else:
                print(f"🔎 Resultado: {cantidad} células detectadas.")
        except Exception as e:
            print(f"❌ Error al contar células: {e}")

    def aplicar_filtro_extra(self):  # ✅ Nuevo método
        try:
            img = self.controlador.aplicar_filtro_extra()
            self.mostrar_imagen(img, self.label_imagen_procesada)
        except Exception as e:
            print(f"❌ Error al aplicar filtro extra: {e}")

    def reiniciar_imagen(self):
        try:
            img = self.controlador.reiniciar_imagen()
            self.mostrar_imagen(img, self.label_imagen_procesada)
            if hasattr(self, 'label_resultado_celulas'):
                self.label_resultado_celulas.setText("")
        except Exception as e:
            print(f"❌ Error al reiniciar imagen: {e}")

    def volver_al_menu(self):
        self.menu_anterior.show()
        self.close()

# ------------------------ MENÚ PRINCIPAL SEÑALES ------------------------
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from CONTROLADOR import ControladorMenuSenales

class MenuSenales(QDialog):
    def __init__(self, login_window):
        super().__init__()
        loadUi("menuppal_senales.ui", self)
        self.setWindowTitle("Menú Principal Señales")
        self.login_window = login_window
        self.controlador = ControladorMenuSenales()

        # Conectar botones a métodos locales
        self.boton_mat.clicked.connect(self.abrir_menu_mat)
        #self.boton_csv.clicked.connect(self.abrir_menu_csv)
        self.boton_salir.clicked.connect(self.salir)

    def abrir_menu_mat(self):
        self.ventana_mat = MenuMat(self)
        self.ventana_mat.show()
        self.hide()


    def salir(self):
        self.login_window.show()
        self.close()

### MENU MAT

from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.uic import loadUi
from CONTROLADOR import ControladorMenuMat

class MenuMat(QDialog):
    def __init__(self, menu_anterior):
        super().__init__()
        loadUi("menu_mat.ui", self)
        self.setWindowTitle("Procesamiento de Señales - .mat")
        self.menu_anterior = menu_anterior
        self.controlador = ControladorMenuMat(self)

        self.boton_cargar_mat.clicked.connect(self.controlador.cargar_archivo_mat)
        self.boton_volver.clicked.connect(self.volver)

    def mostrar_variables_en_combo(self, variables):
        self.combo_variables.clear()
        self.combo_variables.addItems(variables)

    def mostrar_mensaje(self, texto):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Mensaje", texto)

    def mostrar_error(self, texto):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", texto)

    def volver(self):
        self.menu_anterior.show()
        self.close()



# ------------------------ EJECUCIÓN ------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaLogin()
    ventana.show()
    sys.exit(app.exec_())
