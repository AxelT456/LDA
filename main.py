# Importamos las clases que ya teníamos
from LectorDocumentos import LectorDocumentos
from ProcesadorTexto import ProcesadorTexto
# --- ¡CAMBIO AQUÍ! ---
from ModeloLDA_DesdeCero import ModeloLDA_DesdeCero

# --- 1. Configuración ---
NOMBRE_PDF = 'Harry_Potter_y_la_Piedra_filosofal.pdf'
PATRON = r'\s*(\d+)\s*\n\s*([^\n]+)\s*'  # Patrón de Harry Potter
NUM_TOPICOS = 19

# --- 2. Ejecución del Pipeline ---
if __name__ == "__main__":
    lector = LectorDocumentos(patron_division=PATRON)
    procesador = ProcesadorTexto(idioma='spanish')

    texto_crudo = lector.extraer_texto_de_pdf(NOMBRE_PDF)
    documentos = lector.dividir_en_documentos(texto_crudo)

    textos_procesados = [procesador.limpiar_y_tokenizar(doc) for doc in documentos]

    # --- ¡CAMBIO AQUÍ! ---
    # Usamos nuestra nueva clase
    lda = ModeloLDA_DesdeCero(textos_procesados)

    # Estos métodos son los que programamos nosotros
    lda.preparar_corpus(no_below=5, no_above=0.8)
    lda.entrenar(num_topicos=NUM_TOPICOS, passes=100)  # 'passes' es el número de repasos

    # Fase 4: Resultados
    lda.mostrar_topicos()

    # --- ¡CAMBIO AQUÍ! ---
    # lda.guardar_visualizacion(...) # Esta línea la eliminamos o comentamos