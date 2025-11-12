import re
from pypdf import PdfReader

class LectorDocumentos:
    def __init__(self, patron_division=None):
        # Patrón por defecto para detectar capítulos (Capítulo X, Chapter X, números romanos, etc.)
        # Explicación del Regex:
        # (?i) -> Insensible a mayúsculas/minúsculas
        # (?:^|\n) -> Que esté al inicio del texto o después de un salto de línea
        # \s* -> Espacios opcionales
        # (?:cap[íi]tulo|chapter|parte|secci[óo]n)? -> Palabra clave opcional
        # \s+ -> Espacios obligatorios
        # (?:[ivxlcdm]+|\d+) -> Números romanos o dígitos
        if patron_division:
            self.patron_capitulo = patron_division
        else:
            # Este es un patrón genérico bastante robusto
            self.patron_capitulo = r"(?i)(?:^|\n)\s*(?:cap[íi]tulo|chapter|parte)\s+(?:[ivxlcdm]+|\d+).*"

    def extraer_texto_por_paginas(self, file_stream, min_longitud=150):
        """ ESTRATEGIA 1: Documento = 1 Página """
        print(f"Leyendo PDF por páginas...")
        documentos = []
        try:
            reader = PdfReader(file_stream)
            for page in reader.pages:
                texto = page.extract_text()
                if texto and len(texto.strip()) > min_longitud:
                    documentos.append(texto)
            print(f"PDF leído. {len(documentos)} páginas extraídas.")
            return documentos
        except Exception as e:
            print(f"Error al leer PDF: {e}")
            return []

    def extraer_texto_por_capitulos(self, file_stream, min_longitud=500):
        """ ESTRATEGIA 2: Documento = 1 Capítulo (Usando Regex) """
        print(f"Leyendo PDF por capítulos...")
        full_text = ""
        try:
            # 1. Unir todo el PDF en un solo string gigante
            reader = PdfReader(file_stream)
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    full_text += texto + "\n"
            
            # 2. Dividir usando la expresión regular
            # re.split devolverá una lista con los fragmentos
            fragmentos = re.split(self.patron_capitulo, full_text)
            
            # 3. Filtrar fragmentos vacíos o muy cortos (índices, portadas)
            documentos = [frag.strip() for frag in fragmentos if len(frag.strip()) > min_longitud]
            
            # Si la regex no encontró nada, devolvemos el libro entero como 1 documento
            # o hacemos fallback a páginas (opcional). Aquí devolvemos todo junto.
            if len(documentos) < 2:
                print("⚠️ No se detectaron capítulos con el patrón estándar. Se usará el texto completo o división por páginas sugerida.")
                # Si falla, podrías intentar devolver extraer_texto_por_paginas aquí
                
            print(f"PDF dividido. {len(documentos)} capítulos/secciones detectados.")
            return documentos

        except Exception as e:
            print(f"Error al procesar capítulos: {e}")
            return []
    
    def extraer_texto_completo(self, file_stream, min_longitud=100):
        """ ESTRATEGIA 3: Documento = Todo el Libro (1 solo documento) """
        print(f"Leyendo PDF completo como un único documento...")
        full_text = ""
        try:
            reader = PdfReader(file_stream)
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    full_text += texto + "\n"
            
            # Limpieza básica y validación
            if len(full_text.strip()) > min_longitud:
                print(f"PDF leído. Texto total unificado ({len(full_text)} caracteres).")
                return [full_text] # Devolvemos una lista con 1 solo elemento
            else:
                return []
        except Exception as e:
            print(f"Error al leer PDF completo: {e}")
            return []