import re
from pypdf import PdfReader

class LectorDocumentos:
    def __init__(self, patron_division=None):
        if patron_division:
            self.patron_capitulo = re.compile(patron_division)
        else:
            self.patron_capitulo = None

    def extraer_texto_por_paginas(self, file_stream, min_longitud=150):
        """
        Abre un PDF desde un stream de archivo (ej. un archivo subido)
        y devuelve una LISTA donde cada elemento es el texto de una página.
        """
        print(f"Leyendo PDF por páginas desde stream...")
        paginas = []
        try:
            # ¡CAMBIO CLAVE! PdfReader ahora lee el stream de archivo
            reader = PdfReader(file_stream)
            for i, page in enumerate(reader.pages):
                texto = page.extract_text()
                if texto and len(texto.strip()) > min_longitud: # Filtro mejorado
                    paginas.append(texto)
            print(f"PDF leído. {len(paginas)} páginas extraídas (de {len(reader.pages)} totales).")
            return paginas
        except Exception as e:
            # Captura errores de pypdf (ej. PDF corrupto o encriptado)
            print(f"Error al leer el PDF: {e}")
            raise Exception(f"Error de pypdf: {e}")