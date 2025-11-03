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
        print("Creando Bolsa de Palabras (BoW)...")
        self.diccionario = corpora.Dictionary(self.textos_procesados)
        self.diccionario.filter_extremes(no_below=no_below, no_above=no_above)
        self.corpus_bow = [self.diccionario.doc2bow(texto) for texto in self.textos_procesados]
        print(f"Diccionario creado con {len(self.diccionario)} palabras únicas.")

    def entrenar(self, num_topicos, passes=10):
        """Entrena el modelo LDA."""
        print(f"Entrenando modelo LDA con {num_topicos} tópicos...")
        self.modelo = LdaModel(
            corpus=self.corpus_bow,
            id2word=self.diccionario,
            num_topics=num_topicos,
            random_state=100,
            passes=passes,
            per_word_topics=True
        )
        print("¡Modelo entrenado!")

    def mostrar_topicos(self, num_palabras=10):
        """Imprime los tópicos en la consola."""
        print("\n--- Tópicos Descubiertos ---")
        for idx, topic in self.modelo.print_topics(-1, num_words=num_palabras):
            print(f"Tópico {idx}: {topic}")

    def guardar_visualizacion(self, nombre_archivo):
        """Genera y guarda el archivo HTML interactivo."""
        print(f"Generando visualización en {nombre_archivo}...")
        vis_data = pyLDAvis.gensim_models.prepare(self.modelo, self.corpus_bow, self.diccionario)
        pyLDAvis.save_html(vis_data, nombre_archivo)
        print(f"¡HECHO! Revisa el archivo '{nombre_archivo}'.")