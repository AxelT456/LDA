import re
from pypdf import PdfReader


class LectorDocumentos:
    def __init__(self, patron_division):
        self.patron_capitulo = re.compile(patron_division)

    def extraer_texto_de_pdf(self, pdf_path):
        """Abre un PDF y extrae todo su texto en una sola cadena."""
        print(f"Leyendo PDF desde: {pdf_path}")
        try:
            reader = PdfReader(pdf_path)
            texto_completo = ""
            for i, page in enumerate(reader.pages):
                texto = page.extract_text()
                if texto:  # Solo añade texto si se extrajo algo
                    texto_completo += texto + "\n"  # Añadimos un salto de línea por página
            print(f"PDF leído. {len(reader.pages)} páginas extraídas.")
            return texto_completo
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo PDF en '{pdf_path}'")
            return None
        except Exception as e:
            print(f"Error al leer el PDF: {e}")
            return None
        pass

    def dividir_en_documentos(self, texto_completo, min_longitud=500):
        """Divide el texto completo usando el patrón de la clase."""
        documentos = []
        trozos = self.patron_capitulo.split(texto_completo)

        if len(trozos) > 1:
            print(f"Patrón encontrado. Reconstruyendo {len(trozos) // 3} capítulos...")
            for i in range(1, len(trozos), 3):
                try:
                    titulo = f"{trozos[i]} {trozos[i + 1]}"
                    texto = trozos[i + 2]
                    documentos.append(titulo + " " + texto)
                except IndexError:
                    pass
        else:
            print("Patrón no encontrado. Dividiendo por párrafos (Plan B)...")
            documentos = texto_completo.split('\n\n')

        documentos_filtrados = [doc for doc in documentos if len(doc) > min_longitud]
        print(f"Texto dividido en {len(documentos_filtrados)} documentos.")
        return documentos_filtrados