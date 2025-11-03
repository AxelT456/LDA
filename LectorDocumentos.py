import re
from pypdf import PdfReader

class LectorDocumentos:
    def __init__(self, patron_division):
        """
        Guarda el patrón RegEx. Si es None o está vacío, 
        se usará el Plan B (dividir por página).
        """
        if patron_division:
            try:
                self.patron_capitulo = re.compile(patron_division)
                print(f"Usando patrón RegEx: {patron_division}")
            except re.error as e:
                print(f"Error al compilar RegEx: {e}. Se usará el Plan B.")
                self.patron_capitulo = None
        else:
            self.patron_capitulo = None

    def extraer_texto_de_pdf(self, pdf_path):
        """Abre un PDF y extrae el texto PÁGINA POR PÁGINA, devolviendo una lista."""
        print(f"Leyendo PDF desde: {pdf_path}")
        paginas_texto = []
        try:
            reader = PdfReader(pdf_path)
            print(f"PDF leído. Extrayendo texto de {len(reader.pages)} páginas.")
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    paginas_texto.append(texto)
            return paginas_texto # Devuelve una LISTA de strings, no un solo string
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo PDF en '{pdf_path}'")
            return None
        except Exception as e:
            print(f"Error al leer el PDF: {e}")
            return None

    def dividir_en_documentos(self, paginas_texto, min_longitud=200):
        """
        Divide el texto en documentos.
        paginas_texto: Es una lista de strings (un string por página).
        """
        documentos = []
        
        # Primero, une todas las páginas en un solo bloque de texto
        # Usamos un separador especial por si el RegEx lo necesita
        texto_completo = "\n--- NUEVA PAGINA ---\n".join(paginas_texto)

        # PLAN A: Usar el patrón RegEx si existe Y si encuentra coincidencias
        if self.patron_capitulo and self.patron_capitulo.search(texto_completo):
            # El split con grupos de captura (paréntesis en el RegEx) es complejo.
            # Asumimos que el patrón tiene 2 grupos de captura (número y título)
            trozos = self.patron_capitulo.split(texto_completo)
            
            if len(trozos) > 1:
                print(f"Patrón RegEx encontrado. Reconstruyendo {len(trozos) // 3} capítulos...")
                # Empezamos desde 1 para saltar el prólogo/texto antes del primer capítulo
                for i in range(1, len(trozos), 3):
                    try:
                        # Reconstruye el documento con su título (Grupo 1 + Grupo 2)
                        titulo = f"{trozos[i]} {trozos[i + 1]}" 
                        texto = trozos[i + 2]
                        documentos.append(titulo + " " + texto)
                    except IndexError:
                        pass # Ignora el último trozo si no es un capítulo completo
            else:
                 # El patrón se compiló pero no encontró nada, usamos Plan B
                 print("Patrón RegEx no encontró coincidencias. Dividiendo por PÁGINA (Plan B)...")
                 documentos = paginas_texto
        
        # PLAN B: Si no hay patrón (es None), usar cada página como un documento
        else:
            print("Patrón no proporcionado. Dividiendo por PÁGINA (Plan B)...")
            documentos = paginas_texto # Usa la lista de páginas directamente

        # Filtro final de longitud
        documentos_filtrados = [doc for doc in documentos if len(doc) > min_longitud]
        print(f"Texto dividido en {len(documentos_filtrados)} documentos finales (con longitud > {min_longitud} caracteres).")
        return documentos_filtrados