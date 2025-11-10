import re
import spacy # ¡Nuevo!
# Ya no necesitamos NLTK aquí

class ProcesadorTexto:
    def __init__(self, idioma='spanish'):
        # --- Eliminamos el Stemmer y las stopwords de NLTK ---
        # self.stemmer = SnowballStemmer(idioma)
        # self.stop_words = set(stopwords.words(idioma))
        
        # --- ¡NUEVO! Cargamos el modelo de spaCy ---
        try:
            # 'es_core_news_sm' es el modelo que descargamos
            self.nlp = spacy.load('es_core_news_sm') 
        except IOError:
            print("="*50)
            print("Error: Modelo de spaCy 'es_core_news_sm' no encontrado.")
            print("Por favor, ejecuta en tu terminal:")
            print("python -m spacy download es_core_news_sm")
            print("="*50)
            raise
            
        # Usamos el set de stopwords de spaCy, que es más completo
        self.stop_words = self.nlp.Defaults.stop_words

    def limpiar_y_tokenizar(self, texto_crudo):
        """
        Toma un texto crudo y devuelve una lista de tokens limpios 
        y LELEMATEADOS (ej. 'corriendo' -> 'correr').
        """
        
        # spaCy procesa el texto
        doc = self.nlp(texto_crudo.lower()) 

        tokens_finales = [
            token.lemma_  # <-- ¡Esta es la magia! Obtenemos el LEMA
            for token in doc
            # Filtramos de forma más inteligente con spaCy:
            if not token.is_stop and \
               not token.is_punct and \
               token.is_alpha and \
               len(token.text) > 3
        ]
        
        return tokens_finales