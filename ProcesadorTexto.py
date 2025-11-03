import re
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import nltk


class ProcesadorTexto:
    def __init__(self, idioma='spanish'):
        self.stemmer = SnowballStemmer(idioma)
        # Usamos 'try-except' por si las stopwords no están descargadas
        try:
            self.stop_words = set(stopwords.words(idioma))
        except LookupError:
            print("Descargando recursos de NLTK (stopwords)...")
            nltk.download('stopwords')
            self.stop_words = set(stopwords.words(idioma))

    def limpiar_y_tokenizar(self, texto_crudo):
        """Toma un texto crudo y devuelve una lista de tokens limpios y stemizados."""
        texto = re.sub(r'[^a-záéíóúüñ]', ' ', texto_crudo.lower())
        tokens = nltk.word_tokenize(texto, language='spanish')

        tokens_finales = [
            self.stemmer.stem(palabra)
            for palabra in tokens
            if palabra not in self.stop_words and len(palabra) > 3
        ]
        return tokens_finales