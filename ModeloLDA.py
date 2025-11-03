import os  # <-- ¡ASEGÚRATE DE AÑADIR ESTO!
from gensim import corpora
from gensim.models import LdaModel
import pyLDAvis.gensim_models
import pyLDAvis

class ModeloLDA:
    def __init__(self, textos_procesados):
        self.textos_procesados = textos_procesados
        self.diccionario = None
        self.corpus_bow = None
        self.modelo = None

    def preparar_corpus(self, no_below=5, no_above=0.8):
        """Crea el diccionario y el corpus BoW."""
        print("Creando Bolsa de Palabras (BoW) con Gensim...")
        self.diccionario = corpora.Dictionary(self.textos_procesados)
        self.diccionario.filter_extremes(no_below=no_below, no_above=no_above)
        self.corpus_bow = [self.diccionario.doc2bow(texto) for texto in self.textos_procesados]
        
        if len(self.diccionario) == 0:
            print("¡ADVERTENCIA (Gensim)! El diccionario está vacío.")
        else:
            print(f"Diccionario de Gensim creado con {len(self.diccionario)} palabras únicas.")

    def entrenar(self, num_topicos, passes=10):
        """Entrena el modelo LDA."""
        if not self.corpus_bow or not self.diccionario or len(self.diccionario) == 0:
            print("Error: El corpus está vacío o no ha sido preparado. Saltando entrenamiento.")
            return

        print(f"Entrenando modelo LDA de Gensim con {num_topicos} tópicos...")
        self.modelo = LdaModel(
            corpus=self.corpus_bow,
            id2word=self.diccionario,
            num_topics=num_topicos,
            random_state=100,
            passes=passes,
            per_word_topics=True
        )
        print("¡Modelo Gensim entrenado!")

    def mostrar_topicos(self, num_palabras=10):
        """Imprime los tópicos en la consola."""
        if not self.modelo:
            print("Error: El modelo no ha sido entrenado.")
            return
            
        print("\n--- Tópicos Descubiertos (Gensim) ---")
        for idx, topic in self.modelo.print_topics(-1, num_words=num_palabras):
            print(f"Tópico {idx}: {topic}")

    def guardar_visualizacion(self, nombre_archivo):
        """Genera y guarda el archivo HTML interactivo en la carpeta 'static'."""
        if not self.modelo:
            print("Error: El modelo no ha sido entrenado. No se puede generar visualización.")
            return

        # --- ¡CAMBIO IMPORTANTE AQUÍ! ---
        # Define la ruta para la carpeta 'static'
        output_path = os.path.join('static', nombre_archivo)
        
        print(f"Generando visualización en {output_path}...")
        try:
            vis_data = pyLDAvis.gensim_models.prepare(self.modelo, self.corpus_bow, self.diccionario)
            pyLDAvis.save_html(vis_data, output_path)
            print(f"¡HECHO! Visualización guardada en '{output_path}'.")
        except Exception as e:
            print(f"Error al generar la visualización pyLDAvis: {e}")
            print("Asegúrate de tener 'pyLDAvis' instalado: pip install pyLDAvis")