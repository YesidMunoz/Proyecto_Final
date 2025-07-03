import mysql.connector
import os
import numpy as np
import pydicom
import nibabel as nib
import glob

# --------- BASE DE DATOS (LOGIN) ---------
class ModeloUsuario:
    def __init__(self):
        self.config = {
            "host": "localhost",
            "user": "root",
            "password": "info2",
            "database": "sistema_biomedico",
            "port": 3306
        }

    def verificar_usuario(self, nombre_usuario, contrasena):
        try:
            conexion = mysql.connector.connect(**self.config)
            cursor = conexion.cursor()
            consulta = """
                SELECT tipo_usuario 
                FROM usuarios 
                WHERE nombre_usuario = %s AND contrasena = %s
            """
            cursor.execute(consulta, (nombre_usuario, contrasena))
            resultado = cursor.fetchone()
            conexion.close()
            return resultado[0] if resultado else None
        except mysql.connector.Error as err:
            raise Exception(f"Error de conexión a la base de datos: {err}")

    def guardar_en_bd(self, tipo_archivo, nombre_archivo, ruta_archivo, id_usuario=None):
        conexion = mysql.connector.connect(**self.config)
        cursor = conexion.cursor()
        consulta = """
            INSERT INTO imagenes_medicas (tipo_archivo, nombre_archivo, ruta_archivo, id_usuario)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(consulta, (tipo_archivo, nombre_archivo, ruta_archivo, id_usuario))
        conexion.commit()
        conexion.close()

    def mostrar_imagenes_guardadas(self):
        conexion = mysql.connector.connect(**self.config)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM imagenes_medicas")
        resultados = cursor.fetchall()
        for fila in resultados:
            print(fila)
        conexion.close()


# --------- CLASE DICOM ---------
class DICOM:
    def __init__(self, carpeta):
        self.__carpeta = carpeta
        self.__slices = []
        self.__volumen = None

    def cargar_cortes(self):
        archivos = [f for f in os.listdir(self.__carpeta) if f.endswith('.dcm')]
        self.__slices = [pydicom.dcmread(os.path.join(self.__carpeta, archivo)) for archivo in archivos]
        self.__slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
        self.__volumen = np.stack([s.pixel_array for s in self.__slices], axis=0)

    def get_volumen(self):
        return self.__volumen

    def get_pixel_spacing(self):
        if not self.__slices:
            return [1.0, 1.0, 1.0]
        slice0 = self.__slices[0]
        spacing_xy = slice0.PixelSpacing if "PixelSpacing" in slice0 else [1.0, 1.0]
        spacing_z = slice0.SliceThickness if "SliceThickness" in slice0 else 1.0
        return [float(spacing_xy[0]), float(spacing_xy[1]), float(spacing_z)]

    def get_metadatos_principales(self):
        if not self.__slices:
            return "⚠️ No hay archivos DICOM cargados."

        dcm = self.__slices[0]
        campos = {
            "👤 Nombre del paciente": dcm.get("PatientName", "N/A"),
            "🆔 ID del paciente": dcm.get("PatientID", "N/A"),
            "🏥 Institución": dcm.get("InstitutionName", "N/A"),
            "🏭 Fabricante": dcm.get("Manufacturer", "N/A"),
            "📅 Fecha del estudio": dcm.get("StudyDate", "N/A"),
            "🩻 Modalidad": dcm.get("Modality", "N/A"),
            "📝 Descripción de la serie": dcm.get("SeriesDescription", "N/A"),
            "📏 Espesor de corte": dcm.get("SliceThickness", "N/A"),
            "📐 Espaciado de pixeles": dcm.get("PixelSpacing", "N/A"),
        }

        texto = "\n".join([f"{clave}: {valor}" for clave, valor in campos.items()])
        try:
            dims = dcm.pixel_array.shape
            texto += f"\n📸 Dimensiones de imagen: {dims}"
        except:
            pass

        return texto

    def convertir_a_nifti(self):
        if not self.__slices:
            raise Exception("⚠️ No hay DICOM cargado para convertir.")

        print("🧾 Estás convirtiendo un estudio de:", self.__slices[0].PatientID)

        volumen = self.__volumen.astype(np.float32)
        spacing = self.get_pixel_spacing()
        affine = np.diag([spacing[0], spacing[1], spacing[2], 1.0])

        nifti_img = nib.Nifti1Image(volumen, affine)

        nombre_archivo = f"{self.__slices[0].PatientID}.nii.gz"
        ruta_nifti = os.path.join(self.__carpeta, nombre_archivo)

        nib.save(nifti_img, ruta_nifti)

        if os.path.exists(ruta_nifti):
            return ruta_nifti
        else:
            raise Exception("❌ La conversión no generó un archivo NIfTI.")

    def get_ruta(self):
        return self.__carpeta

    def get_ruta_nifti(self):
        return os.path.join(self.__carpeta, f"{self.__slices[0].PatientID}.nii.gz")


# --------- CLASE NIFTI ---------
class NIfTI:
    def __init__(self, ruta_archivo):
        self.ruta_archivo = ruta_archivo
        self.volumen = None
        self.pixel_spacing = None

    def cargar_volumen(self):
        img = nib.load(self.ruta_archivo)
        self.volumen = img.get_fdata()
        affine = img.affine
        spacing_x, spacing_y, spacing_z = np.abs(np.diag(affine))[:3]
        self.pixel_spacing = [spacing_y, spacing_x, spacing_z]

    def get_volumen(self):
        return self.volumen

    def get_pixel_spacing(self):
        return self.pixel_spacing


### CLASE IMAGENES CONVENCIONALES
import cv2
import numpy as np

class ProcesadorImagenConvencional:
    def cargar_imagen(self, ruta):
        imagen = cv2.imread(ruta)
        if imagen is None:
            raise Exception("No se pudo cargar la imagen.")
        return imagen

    def cambiar_espacio_color(self, imagen, espacio):
        if espacio == "RGB":
            return cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        elif espacio == "GRAY":
            return cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        elif espacio == "HSV":
            return cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
        elif espacio == "LAB":
            return cv2.cvtColor(imagen, cv2.COLOR_BGR2LAB)
        else:
            raise Exception("Espacio de color no válido.")

    def ecualizar_imagen(self, imagen):
        if len(imagen.shape) == 2:
            return cv2.equalizeHist(imagen)
        elif len(imagen.shape) == 3 and imagen.shape[2] == 3:
            canales = cv2.split(imagen)
            canales_ecualizados = [cv2.equalizeHist(c) for c in canales]
            return cv2.merge(canales_ecualizados)
        else:
            raise Exception("Formato de imagen no compatible para ecualización.")

    def binarizar_imagen(self, imagen, umbral=127):
        if len(imagen.shape) == 3:
            try:
                imagen_gray = cv2.cvtColor(imagen, cv2.COLOR_RGB2GRAY)
            except:
                imagen_gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        else:
            imagen_gray = imagen
        _, binaria = cv2.threshold(imagen_gray, umbral, 255, cv2.THRESH_BINARY)
        return binaria

    def aplicar_morfologia(self, imagen, operacion="apertura", kernel_size=3):
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        if operacion == "apertura":
            return cv2.morphologyEx(imagen, cv2.MORPH_OPEN, kernel)
        elif operacion == "cierre":
            return cv2.morphologyEx(imagen, cv2.MORPH_CLOSE, kernel)
        else:
            raise Exception("Operación morfológica no válida.")

    def contar_celulas(self, imagen):
        """
        Procesa una imagen binaria o de un solo canal y cuenta los contornos (células).
        Devuelve la imagen con los contornos dibujados y la cantidad encontrada.
        """
        # Convertir a escala de grises si es necesario
        if len(imagen.shape) == 3:
            imagen = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

        # Binarizar para asegurar que está en blanco y negro
        _, binaria = cv2.threshold(imagen, 50, 255, cv2.THRESH_BINARY)

        # Buscar contornos externos
        contornos, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Dibujar contornos sobre una copia en color
        imagen_con_contornos = cv2.cvtColor(binaria, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(imagen_con_contornos, contornos, -1, (0, 255, 0), 2)

        return imagen_con_contornos, len(contornos)

    def aplicar_filtro_bilateral(self, imagen):
        # cv2.bilateralFilter(src, diameter, sigmaColor, sigmaSpace)
        return cv2.bilateralFilter(imagen, d=9, sigmaColor=75, sigmaSpace=75)


from scipy.io import loadmat
import numpy as np

class ProcesadorMat:
    def __init__(self):
        self.datos = {}

    def cargar_archivo(self, ruta):
        self.datos = loadmat(ruta)

    def get_variables_validas(self):
        if not self.datos:
            return []
        return [
            key for key, value in self.datos.items()
            if not key.startswith("__") and isinstance(value, np.ndarray)
        ]
