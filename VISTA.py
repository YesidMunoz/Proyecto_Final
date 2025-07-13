import sys
import os
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import cv2
from CONTROLADOR import ControladorLogin, ControladorDicom, ControladorImagenConvencional, ControladorMenuSenales, ControladorMenuMat, ControladorCSV
from PyQt5.QtWidgets import (QApplication, QDialog, QMessageBox, QFileDialog,QVBoxLayout,QTableWidgetItem)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from scipy.ndimage import zoom 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas





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

# ------------------------ VENTANA DE CORTES (sliders) ------------------------
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
        self.boton_guardar.clicked.connect(self.controlador.guardar_en_bd)

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
    def mostrar_mensaje(self, mensaje):
        QMessageBox.information(self, "Mensaje", mensaje)
    def volver_al_menu(self):
        self.menu_anterior.show()
        self.close()

# ------------------------ MENÚ PRINCIPAL SEÑALES ------------------------
class MenuSenales(QDialog):
    def __init__(self, login_window):
        super().__init__()
        loadUi("menuppal_senales.ui", self)
        self.setWindowTitle("Menú Principal Señales")
        self.login_window = login_window
        self.controlador = ControladorMenuSenales()

        # Conectar botones a métodos locales
        self.boton_mat.clicked.connect(self.abrir_menu_mat)
        self.boton_CSV.clicked.connect(self.abrir_menu_csv) 
        self.boton_salir.clicked.connect(self.salir)

    def abrir_menu_mat(self):
        self.ventana_mat = MenuMAT(self)
        self.ventana_mat.show()
        self.hide()
    
    def abrir_menu_csv(self):
        self.ventana_csv = MenuCSV(self) 
        self.ventana_csv.show()
        self.hide()


    def salir(self):
        self.login_window.show()
        self.close()

# ------------------------ MENÚ MAT  ------------------------
class MenuMAT(QDialog): 
    def __init__(self, menu_anterior):
        super().__init__()
        self.menu_anterior = menu_anterior  # Guarda referencia al menú anterior
        loadUi("vista_mat.ui", self)
        self.setWindowTitle("Menú de visualización de señales .mat")
        self.habilita_botones_mat(cargar=True)
        self.controlador = ControladorMenuMat(self) 
        # Crear la figura y canvas de matplotlib
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        # Agregar canvas al widget de la interfaz
        layout = QVBoxLayout(self.widget_grafica)  # ← asegúrate que este widget exista en el .ui
        layout.addWidget(self.canvas)

        # Conectar botón volver si existe
        if hasattr(self, 'boton_volver'):
            self.boton_volver.clicked.connect(self.volver_al_menu)

    def volver_al_menu(self):
        self.menu_anterior.show()
        self.close()

    def mostrar_mensaje(self, mensaje):
        QMessageBox.information(self, "Información", mensaje)

    def mostrar_error(self, mensaje):
        QMessageBox.warning(self, "Error", mensaje)

    def habilita_botones_mat(self, cargar=False, graficar=False, segmento=False, promedio=False, rango=False,guardar=False):
        self.boton_cargar.setEnabled(cargar)
        self.boton_graficar.setEnabled(graficar)
        self.boton_segmento.setEnabled(segmento)
        self.boton_promedio.setEnabled(promedio)
        self.boton_rango_canales.setEnabled(rango)
        self.boton_guardar.setEnabled(guardar)

    def actualizar_forma(self, texto):
        self.label_forma.setText(texto)

    def mostrar_variables_en_combo(self, llaves):
        self.combo_llaves.clear()
        self.combo_llaves.addItems(llaves)

    def get_llave_seleccionada(self):
        return self.combo_llaves.currentText()

    def get_parametros_segmento(self, ndim):
        try:
            inicio = int(self.input_inicio.text())
            fin = int(self.input_fin.text())
            canal = int(self.input_canal.text())
            if ndim == 3:
                ensayo = int(self.input_ensayo.text())
                return (inicio, fin, canal, ensayo)
            elif ndim == 2:
                return (inicio, fin, canal)
            elif ndim == 1:
                return (inicio, fin)
            else:
                return None
        except ValueError:
            return None

    def get_rango_canales(self):
        try:
            return (
                int(self.input_canal_inicio.text()),
                int(self.input_canal_fin.text())
            )
        except ValueError:
            return None

    def configurar_campos_segmento(self, ndim):
        self.input_canal.setEnabled(ndim >= 2)
        self.input_ensayo.setEnabled(ndim == 3)

    def mostrar_grafica(self, datos, titulo):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(datos)
        ax.set_title(titulo)
        ax.set_xlabel("Muestras")
        ax.set_ylabel("Amplitud")
        self.canvas.draw()

    def mostrar_promedio(self, datos, titulo):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.stem(datos)
        ax.set_title(titulo)
        ax.set_xlabel("Canales")
        ax.set_ylabel("Promedio")
        self.canvas.draw()

    def mostrar_rango_canales(self, datos_dict, titulo):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        offset = 0
        for canal, datos in datos_dict.items():
            ax.plot(np.arange(len(datos)), datos + offset, label=f"C {canal}")
            offset += np.max(np.abs(datos)) * 3

        ax.set_title(titulo)
        ax.set_xlabel("Muestras")
        ax.set_ylabel("Amplitud (desplazada)")
        ax.legend(
            loc='center left',
            bbox_to_anchor=(1.01, 0.5),
            borderaxespad=0.
        )

        self.canvas.draw()

# ------------------------ MENU CSV ------------------------
class MenuCSV(QDialog):
    def __init__(self, menu_anterior):
        super().__init__()
        self.menu_anterior = menu_anterior
        loadUi("vista_csv.ui", self)
        self.setWindowTitle("Visualización de Archivos CSV")
        self.label_grafico.setAlignment(Qt.AlignCenter)

        # Controlador
        self.controlador = ControladorCSV(self)

        # Conexiones de botones
        self.boton_cargar.clicked.connect(self.controlador.cargar_csv)
        self.boton_graficar.clicked.connect(self.graficar_click)
        self.boton_volver.clicked.connect(self.volver_al_menu)
        self.boton_guardar_csv.clicked.connect(self.controlador.guardar_en_bd)

    def volver_al_menu(self):
        self.menu_anterior.show()
        self.close()

    def mostrar_datos_csv(self, datos, encabezados):
        self.tabla_csv.setRowCount(len(datos))
        self.tabla_csv.setColumnCount(len(encabezados))
        self.tabla_csv.setHorizontalHeaderLabels(encabezados)
        for i, fila in enumerate(datos):
            for j, item in enumerate(fila):
                self.tabla_csv.setItem(i, j, QTableWidgetItem(str(item)))

    def actualizar_combobox_columnas(self, columnas):
        self.combo_x.clear()
        self.combo_y.clear()
        self.combo_x.addItems(columnas)
        self.combo_y.addItems(columnas)

    def mostrar_mensaje(self, mensaje):
        self.label_estado.setText(mensaje)

   
    def crear_grafico(self, datos_x, datos_y, eje_x, eje_y):
        fig = plt.figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.scatter(datos_x, datos_y)
        ax.set_xlabel(eje_x)
        ax.set_ylabel(eje_y)
        fig.tight_layout()

        archivo_temporal = "grafico_temp.png"
        fig.savefig(archivo_temporal)
        plt.close(fig)

        # Cargar imagen y ajustarla al QLabel correctamente
        pixmap = QPixmap(archivo_temporal)
        pixmap = pixmap.scaled(
            self.label_grafico.size(),  # <- este es tu QLabel real
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.label_grafico.setPixmap(pixmap)

        if os.path.exists(archivo_temporal):
            os.remove(archivo_temporal)

    def graficar_click(self):
        columna_x = self.combo_x.currentText()
        columna_y = self.combo_y.currentText()
        self.controlador.generar_grafico_dispersion(columna_x, columna_y)

    