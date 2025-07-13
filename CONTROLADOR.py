from MODELO import ModeloUsuario, NIfTI, DICOM, ModeloImagenConvencional, ModeloMat, ModeloCSV
import os
import numpy as np
from PyQt5.QtWidgets import QFileDialog

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

class ControladorImagenConvencional:
    def __init__(self, vista):
        self.vista = vista
        self.modelo = ModeloImagenConvencional()
        self.imagen_original = None
        self.imagen_actual = None
        self.ruta_imagen = None

    def cargar_imagen(self, ruta):
        self.ruta_imagen = ruta 
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

    def guardar_en_bd(self):
        try:
            if not self.ruta_imagen:
                raise ValueError("No hay ruta de imagen cargada.")
            nombre = os.path.basename(self.ruta_imagen)
            extension = os.path.splitext(nombre)[1].replace(".", "").upper()  # "JPG", "PNG"
            self.modelo.guardar_en_bd(extension, nombre, self.ruta_imagen)
            self.vista.mostrar_mensaje("✅ Imagen guardada en la base de datos.")
        except Exception as e:
            self.vista.mostrar_mensaje(f"❌ Error al guardar en BD: {e}")

class ControladorMenuSenales:
    def __init__(self):
        pass  # Ya no gestiona ventanas, solo lógica si se necesita más adelante

class ControladorMenuMat:
    def __init__(self, vista):
        self.vista = vista
        self.modelo = ModeloMat()

        # Inicialmente solo botón cargar habilitado
        self.vista.habilita_botones_mat(cargar=True)

        # Conectar botones y combos
        self.vista.boton_cargar.clicked.connect(self.cargar_archivo_mat)
        self.vista.boton_graficar.clicked.connect(self.graficar)
        self.vista.boton_segmento.clicked.connect(self.graficar_segmento)
        self.vista.boton_promedio.clicked.connect(self.promediar)
        self.vista.boton_rango_canales.clicked.connect(self.graficar_canales)
        self.vista.combo_llaves.currentIndexChanged.connect(self.forma_matriz)
        self.vista.boton_guardar.clicked.connect(self.guardar_en_bd)  # ✅ NUEVO

    def cargar_archivo_mat(self):
        ruta, _ = QFileDialog.getOpenFileName(self.vista, "Seleccionar archivo .mat", "", "Archivos MAT (*.mat)")
        if ruta:
            try:
                self.modelo.cargar_archivo(ruta)
                variables = self.modelo.get_todas_las_llaves()
                if not variables:
                    self.vista.mostrar_error("El archivo no contiene variables.")
                    return

                self.vista.mostrar_variables_en_combo(variables)
                self.vista.mostrar_mensaje(f"Archivo cargado. Variables encontradas: {len(variables)}")

                self.vista.habilita_botones_mat(
                    cargar=True,
                    graficar=True,
                    segmento=False,
                    promedio=False,
                    rango=False,
                    guardar=True  # ✅ Habilita guardar luego de cargar
                )

                if variables:
                    self.forma_matriz()

            except Exception as e:
                self.vista.mostrar_error(f"Error al cargar archivo: {e}")

    def graficar(self):
        clave = self.vista.get_llave_seleccionada()
        array = self.modelo.obtener_array(clave)
        if not self.validar_array_para_graficar(array):
            return
        try:
            segmento = self.modelo.get_segmento(clave)
            self.vista.mostrar_grafica(segmento, f"Señal de {clave} (Canal 0, Ensayo 0)")
        except Exception as e:
            self.vista.mostrar_error(f"Error al graficar: {e}")

    def graficar_segmento(self):
        clave = self.vista.get_llave_seleccionada()
        array = self.modelo.obtener_array(clave)

        if not self.validar_array_para_graficar(array):
            return

        ndim = array.ndim
        parametros = self.vista.get_parametros_segmento(ndim)
        if parametros is None:
            self.vista.mostrar_error("Datos inválidos para segmento.")
            return

        try:
            if ndim == 3:
                inicio, fin, canal, ensayo = parametros
                segmento = self.modelo.get_segmento(clave, canal, ensayo, inicio, fin)
                titulo = f"{clave} | Canal {canal}, Ensayo {ensayo}, {inicio}-{fin}"
            elif ndim == 2:
                inicio, fin, canal = parametros
                segmento = self.modelo.get_segmento(clave, canal, 0, inicio, fin)
                titulo = f"{clave} | Canal {canal}, {inicio}-{fin}"
            elif ndim == 1:
                inicio, fin = parametros
                segmento = self.modelo.get_segmento(clave, 0, 0, inicio, fin)
                titulo = f"{clave} | Muestras {inicio}-{fin}"
            else:
                raise ValueError("No se puede graficar el segmento.")

            self.vista.mostrar_grafica(segmento, titulo)

        except Exception as e:
            self.vista.mostrar_error(f"No se puede graficar el segmento: {e}")

    def promediar(self):
        clave = self.vista.get_llave_seleccionada()
        array = self.modelo.obtener_array(clave)
        if not self.validar_array_para_graficar(array):
            return
        try:
            promedio = self.modelo.get_promedio(clave)
            self.vista.mostrar_promedio(promedio, f"Promedio Eje 1 de {clave}")
        except Exception as e:
            self.vista.mostrar_error(f"Error al promediar: {e}")

    def graficar_canales(self):
        clave = self.vista.get_llave_seleccionada()
        array = self.modelo.obtener_array(clave)

        if not self.validar_array_para_graficar(array):
            return

        rango = self.vista.get_rango_canales()
        if rango is None:
            self.vista.mostrar_error("Datos inválidos para los canales.")
            return

        canal_inicio, canal_final = rango

        try:
            if array.ndim < 2:
                raise ValueError("La variable no tiene suficientes dimensiones para representar canales.")

            max_canal = array.shape[0] - 1
            if canal_inicio < 0 or canal_final > max_canal or canal_inicio > canal_final:
                raise ValueError(f"El rango de canales debe estar entre 0 y {max_canal}.")

            canal_clave = {}
            for c in range(canal_inicio, canal_final + 1):
                datos = self.modelo.get_segmento(clave, c, 0)
                canal_clave[c] = datos

            titulo = f"Canales {canal_inicio}-{canal_final} de {clave}"
            self.vista.mostrar_rango_canales(canal_clave, titulo)

        except Exception as e:
            self.vista.mostrar_error(f"Error al graficar rango de canales: {e}")

    def forma_matriz(self):
        clave = self.vista.get_llave_seleccionada()
        matriz = self.modelo.obtener_array(clave)

        if not isinstance(matriz, np.ndarray):
            self.vista.actualizar_forma("Forma: No es una matriz válida para graficar.")
            self.vista.habilita_botones_mat(cargar=True, graficar=True)
            self.vista.configurar_campos_segmento(0)
            return

        forma = matriz.shape
        if len(forma) == 3:
            mssg = f"Forma: {forma} → Canales: {forma[0]}, Muestras: {forma[1]}, Ensayos: {forma[2]}"
        elif len(forma) == 2:
            mssg = f"Forma: {forma} → Canales: {forma[0]}, Muestras: {forma[1]}"
        elif len(forma) == 1:
            mssg = f"Forma: {forma} → Muestras: {forma[0]}"
        else:
            mssg = f"Forma no soportada: {forma}"

        self.vista.actualizar_forma(mssg)

        self.vista.habilita_botones_mat(
            cargar=True,
            graficar=True,
            segmento=True,
            promedio=True,
            rango=matriz.ndim >= 2,
            guardar=True
        )

        self.vista.configurar_campos_segmento(matriz.ndim)

    def validar_array_para_graficar(self, array):
        if not isinstance(array, np.ndarray):
            self.vista.mostrar_error("La variable seleccionada no es un array. Por favor selecciona otra variable.")
            return False
        if array.dtype.fields is not None:
            self.vista.mostrar_error("La variable seleccionada no es un array válido para graficar.")
            return False
        return True

    def guardar_en_bd(self):
        try:
            self.modelo.guardar_mat()
            self.vista.mostrar_mensaje("✅ Archivo .mat guardado en la base de datos.")
        except Exception as e:
            self.vista.mostrar_error(f"❌ Error al guardar en BD: {e}")

class ControladorCSV:
    def __init__(self, vista):
        self.vista = vista
        self.modelo = ModeloCSV() # Instancia del modelo CSV

    def cargar_csv(self): 
        """
        Maneja la lógica de cargar el archivo CSV.
        Solicita la ruta a la vista (o la obtiene directamente aquí con QFileDialog),
        llama al modelo y actualiza la vista.
        """
        ruta_archivo, _ = QFileDialog.getOpenFileName(self.vista, "Abrir archivo CSV", "", "Archivos CSV (*.csv)") 
        if ruta_archivo: 
            try:
                self.modelo.cargar_csv(ruta_archivo) 
                
                # Pasa los datos procesados del modelo a la vista para que los muestre en la tabla
                datos, encabezados = self.modelo.lista_dataframe() # <--- Variables y método en español
                self.vista.mostrar_datos_csv(datos, encabezados) 

                # Obtener columnas numéricas del modelo y pasarlas a la vista para los combobox
                columnas_numericas = self.modelo.nombres_columnas_num() # <--- Variables y método en español
                self.vista.actualizar_combobox_columnas(columnas_numericas) 

                self.vista.mostrar_mensaje("Archivo CSV cargado correctamente.")
            except Exception as e:
                self.vista.mostrar_mensaje(f"Error al cargar el archivo CSV: {e}")

    def generar_grafico_dispersion(self, columna_x, columna_y): 
        """
        Obtiene los datos para graficar del modelo y le pide a la vista que genere el gráfico.
        """
        try:
            # Obtiene los datos (x, y) directamente del modelo
            datos_x, datos_y = self.modelo.obtener_datos_para_grafico(columna_x, columna_y) # <--- Variables y método en español
            
            # La vista es la que sabe cómo dibujar el gráfico con matplotlib y Qt
            self.vista.crear_grafico(datos_x, datos_y, columna_x, columna_y) 
            self.vista.mostrar_mensaje("Gráfico de dispersión generado.")
        except (ValueError, TypeError) as e:
            self.vista.mostrar_mensaje(f"Error al generar gráfico: {e}")
        except Exception as e:
            self.vista.mostrar_mensaje(f"Ocurrió un error inesperado al graficar: {e}")


    def guardar_en_bd(self):
        try:
            self.modelo.guardar_csv()
            self.vista.mostrar_mensaje("✅ Archivo .csv guardado en la base de datos.")
        except Exception as e:
            self.vista.mostrar_error(f"❌ Error al guardar en BD: {e}")