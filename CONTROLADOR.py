from MODELO import ModeloUsuario, NIfTI, DICOM
import os

class ControladorLogin:
    def __init__(self, vista):
        self.vista = vista
        self.modelo = ModeloUsuario()

    def autenticar(self, usuario, contrasena):
        if not usuario or not contrasena:
            self.vista.mostrar_mensaje("⚠️ Por favor ingresa usuario y contraseña.")
            return

        try:
            tipo = self.modelo.verificar_usuario(usuario, contrasena)
            if tipo == "imagen":
                self.vista.abrir_menu_imagenes()
            elif tipo == "senal":
                print("✅ Usuario tipo senal autenticado")
                self.vista.abrir_menu_senales()
            else:
                self.vista.mostrar_mensaje("❌ Usuario o contraseña incorrectos.")
        except Exception as e:
            self.vista.mostrar_mensaje(f"⚠️ {str(e)}")



class ControladorDicom:
    def __init__(self, vista):
        self.vista = vista
        self.dicom_obj = None
        self.nifti_obj = None
        self.modelo = ModeloUsuario()

    # ----------- DICOM -----------
    def cargar_dicom_desde_carpeta(self, carpeta):
        try:
            self.dicom_obj = DICOM(carpeta)
            self.dicom_obj.cargar_cortes()
            self.vista.mostrar_mensaje("✅ Volumen DICOM cargado correctamente.")
            self.vista.habilitar_botones(True)
            print(f"Volumen DICOM cargado: forma {self.dicom_obj.get_volumen().shape}")
        except Exception as e:
            self.vista.mostrar_mensaje(f"❌ Error al cargar DICOM: {str(e)}")
            self.vista.habilitar_botones(False)

    def ver_metadatos(self):
        if self.dicom_obj:
            metadatos = self.dicom_obj.get_metadatos_principales()
            self.vista.mostrar_metadatos(metadatos)
        else:
            self.vista.mostrar_mensaje("⚠️ No hay DICOM cargado.")

    # ----------- NIfTI -----------
    def cargar_nifti(self, ruta_archivo):
        try:
            self.nifti_obj = NIfTI(ruta_archivo)
            self.nifti_obj.cargar_volumen()
            self.dicom_obj = None
            print(f"Volumen NIfTI cargado: forma {self.nifti_obj.get_volumen().shape}")
        except Exception as e:
            self.vista.mostrar_mensaje(f"❌ Error al cargar NIfTI: {str(e)}")
            self.vista.habilitar_botones(False)

    # ----------- ACCESO UNIFICADO -----------
    def get_volumen(self):
        if self.dicom_obj:
            return self.dicom_obj.get_volumen()
        elif self.nifti_obj:
            return self.nifti_obj.get_volumen()
        return None

    def get_pixel_spacing(self):
        if self.dicom_obj:
            return self.dicom_obj.get_pixel_spacing()
        elif self.nifti_obj:
            return self.nifti_obj.get_pixel_spacing()
        return [1.0, 1.0, 1.0]

    # ----------- CONVERSIÓN -----------
    def convertir_a_nifti(self):
        if not self.dicom_obj:
            self.vista.mostrar_mensaje("⚠️ No hay DICOM cargado para convertir.")
            return

        try:
            ruta_nifti = self.dicom_obj.convertir_a_nifti()
            self.vista.mostrar_mensaje(f"✅ Conversión exitosa. Archivo guardado en:\n{ruta_nifti}")
        except Exception as e:
            self.vista.mostrar_mensaje(f"❌ Error al convertir a NIfTI: {e}")

    # ----------- GUARDAR EN BD -----------
    def guardar_datos(self):
        if self.dicom_obj:
            try:
                ruta_dicom = self.dicom_obj.get_ruta()
                ruta_nifti = self.dicom_obj.get_ruta_nifti()

                # Extraer nombres
                nombre_dicom = os.path.basename(ruta_dicom)
                nombre_nifti = os.path.basename(ruta_nifti)

                # Guardar DICOM
                self.modelo.guardar_en_bd("DICOM", nombre_dicom, ruta_dicom)

                # Guardar NIfTI
                self.modelo.guardar_en_bd("NIFTI", nombre_nifti, ruta_nifti)

                self.vista.mostrar_mensaje("✅ Datos guardados en la base de datos.")
                # Para debug:
                self.modelo.mostrar_imagenes_guardadas()

            except Exception as e:
                self.vista.mostrar_mensaje(f"❌ No se pudo guardar: {e}")
        else:
            self.vista.mostrar_mensaje("❌ No hay datos para guardar.")


### IMAGENES CONVENCIONALES
from MODELO import ProcesadorImagenConvencional
class ControladorImagenConvencional:
    def __init__(self, vista):
        self.vista = vista
        self.modelo = ProcesadorImagenConvencional()
        self.imagen_original = None
        self.imagen_actual = None

    def cargar_imagen(self, ruta):
        self.imagen_original = self.modelo.cargar_imagen(ruta)
        self.imagen_actual = self.imagen_original.copy()
        return self.imagen_original

    def reiniciar_imagen(self):
        self.imagen_actual = self.imagen_original.copy()
        return self.imagen_actual

    def cambiar_espacio_color(self, espacio):
        self.imagen_actual = self.modelo.cambiar_espacio_color(self.imagen_original, espacio)
        return self.imagen_actual

    def ecualizar_imagen(self):
        self.imagen_actual = self.modelo.ecualizar_imagen(self.imagen_actual)
        return self.imagen_actual

    def binarizar_imagen(self, umbral):
        self.imagen_actual = self.modelo.binarizar_imagen(self.imagen_actual, umbral)
        return self.imagen_actual

    def aplicar_morfologia(self, tipo, kernel):
        self.imagen_actual = self.modelo.aplicar_morfologia(self.imagen_actual, tipo, kernel)
        return self.imagen_actual

    def contar_celulas(self):
        imagen_contornos, cantidad = self.modelo.contar_celulas(self.imagen_actual)
        self.imagen_actual = imagen_contornos
        return cantidad, self.imagen_actual


    # ✅ NUEVO MÉTODO para filtro extra (bilateral)
    def aplicar_filtro_extra(self):
        self.imagen_actual = self.modelo.aplicar_filtro_bilateral(self.imagen_actual)
        return self.imagen_actual


### SEÑALES

class ControladorMenuSenales:
    def __init__(self):
        pass  # Ya no gestiona ventanas, solo lógica si se necesita más adelante

from MODELO import ProcesadorMat
from PyQt5.QtWidgets import QFileDialog

class ControladorMenuMat:
    def __init__(self, vista):
        self.vista = vista
        self.modelo = ProcesadorMat()

    def cargar_archivo_mat(self):
        ruta, _ = QFileDialog.getOpenFileName(self.vista, "Seleccionar archivo .mat", "", "Archivos MAT (*.mat)")
        if ruta:
            try:
                self.modelo.cargar_archivo(ruta)
                variables = self.modelo.get_variables_validas()
                if not variables:
                    self.vista.mostrar_error("⚠️ El archivo no contiene variables tipo array.")
                    return
                self.vista.mostrar_variables_en_combo(variables)
                self.vista.mostrar_mensaje(f"✅ Archivo cargado. Variables encontradas: {len(variables)}")
            except Exception as e:
                self.vista.mostrar_error(f"❌ Error al cargar archivo: {e}")
