import numpy as np
import random
from collections import defaultdict


class ModeloLDA_DesdeCero:

    def __init__(self, textos_procesados):
        """
        Guarda los textos. textos_procesados es una lista de listas, ej:
        [['hagr', 'vernon'], ['anill', 'sauron']]
        """
        self.textos_procesados = textos_procesados

        # --- Propiedades que crearemos ---
        self.palabra_a_id = None  # Nuestro nuevo "diccionario"
        self.id_a_palabra = None  # Para poder traducir de ID a palabra
        self.corpus = None  # Nuestra nueva "Bolsa de Palabras" (lista de listas de IDs)

        self.V = 0  # Tamaño del vocabulario
        self.D = 0  # Número de documentos (capítulos)
        self.K = 0  # Número de tópicos

        # --- Hiperparámetros Bayesianos ---
        self.alpha = 0.1  # Parámetro Dirichlet para Documento-Tópico
        self.beta = 0.01  # Parámetro Dirichlet para Tópico-Palabra

        # --- Matrices del Modelo (Estado de la Cadena de Markov) ---
        # Estas matrices almacenan los CONTEOS
        self.n_dt = None  # Matriz Documento-Tópico (n_dt[d, k] = conteo de palabras del doc d en tópico k)
        self.n_wt = None  # Matriz Palabra-Tópico (n_wt[w, k] = conteo de la palabra w en tópico k)
        self.n_t = None  # Vector Total-Tópico (n_t[k] = conteo total de palabras en tópico k)

        self.asignaciones_Z = None  # Lista (D) de listas (palabras) que guarda el tópico (k) asignado a cada palabra

    # -----------------------------------------------------------------
    # MÉTODO 1: PREPARAR EL CORPUS (Reemplaza a corpora.Dictionary)
    # -----------------------------------------------------------------
    def preparar_corpus(self, no_below=5, no_above=0.8):
        """
        Construye el vocabulario (diccionario) y el corpus (BoW) desde cero,
        aplicando los filtros.
        """
        print("Creando Bolsa de Palabras (BoW) desde cero...")
        self.D = len(self.textos_procesados)

        # 1. Contar la frecuencia de documentos por palabra (para filtrar)
        frecuencia_doc = defaultdict(int)
        for doc in self.textos_procesados:
            for palabra in set(doc):  # set() para contar solo una vez por documento
                frecuencia_doc[palabra] += 1

        # 2. Aplicar filtros (reemplaza a filter_extremes)
        vocabulario_filtrado = set()
        for palabra, freq in frecuencia_doc.items():
            if no_below <= freq <= self.D * no_above:
                vocabulario_filtrado.add(palabra)

        # 3. Construir nuestros diccionarios (reemplaza a corpora.Dictionary)
        self.id_a_palabra = list(vocabulario_filtrado)
        self.palabra_a_id = {palabra: i for i, palabra in enumerate(self.id_a_palabra)}
        self.V = len(self.id_a_palabra)

        # 4. Construir nuestro corpus (reemplaza a doc2bow)
        # Convertimos cada documento de palabras a una lista de IDs de palabras
        self.corpus = []
        for doc in self.textos_procesados:
            doc_de_ids = [self.palabra_a_id[palabra] for palabra in doc if palabra in self.palabra_a_id]
            self.corpus.append(doc_de_ids)

        print(f"Diccionario creado con {self.V} palabras únicas (después de filtrar).")

    # -----------------------------------------------------------------
    # MÉTODO 2: ENTRENAR (Reemplaza a LdaModel con Muestreo de Gibbs)
    # -----------------------------------------------------------------
    def entrenar(self, num_topicos, iteraciones=1000, passes=1):
        """
        Entrena el modelo LDA usando Muestreo de Gibbs (MCMC / Cadenas de Markov).
        """
        print(f"Entrenando modelo LDA desde cero con {num_topicos} tópicos...")
        self.K = num_topicos

        # --- Inicializar matrices de conteo con ceros usando NumPy ---
        self.n_dt = np.zeros((self.D, self.K), dtype=int)
        self.n_wt = np.zeros((self.V, self.K), dtype=int)
        self.n_t = np.zeros(self.K, dtype=int)

        # --- Inicialización Aleatoria (Paso 0 de MCMC) ---
        # Asignamos un tópico aleatorio a CADA palabra en CADA documento
        print("Inicializando estado aleatorio...")
        self.asignaciones_Z = []
        for d, doc in enumerate(self.corpus):
            doc_asignaciones = []
            for palabra_id in doc:
                # Asignar un tópico (k) aleatorio
                k = random.randint(0, self.K - 1)
                doc_asignaciones.append(k)

                # Poblar nuestras matrices de conteo
                self.n_dt[d, k] += 1
                self.n_wt[palabra_id, k] += 1
                self.n_t[k] += 1
            self.asignaciones_Z.append(doc_asignaciones)

        # --- Bucle de Muestreo de Gibbs (El núcleo de MCMC) ---
        # "passes" es cuántas veces repasamos el libro (como en gensim)
        # "iteraciones" es el número total de pasos de muestreo
        print(f"Iniciando {passes} pasadas de Muestreo de Gibbs...")
        for _ in range(passes):
            # Iteramos sobre cada documento (d) y cada palabra (w)
            for d, doc in enumerate(self.corpus):
                for i, w in enumerate(doc):  # 'i' es la posición, 'w' es el ID de la palabra

                    # 1. Descontar la palabra actual de las matrices
                    #    (la sacamos del modelo temporalmente)
                    t_actual = self.asignaciones_Z[d][i]
                    self.n_dt[d, t_actual] -= 1
                    self.n_wt[w, t_actual] -= 1
                    self.n_t[t_actual] -= 1

                    # 2. Calcular la probabilidad bayesiana (¡Esta es la teoría!)
                    #    Calculamos la probabilidad de esta palabra (w)
                    #    perteneciendo a CADA tópico (k)

                    # P(tópico | documento) ~ (n_dt[d] + alpha)
                    prob_doc_topico = self.n_dt[d] + self.alpha

                    # P(palabra | tópico) ~ (n_wt[w] + beta) / (n_t + V * beta)
                    prob_palabra_topico = (self.n_wt[w] + self.beta) / (self.n_t + self.V * self.beta)

                    # P(tópico | doc, palabra) ~ P(tópico | doc) * P(palabra | tópico)
                    prob_topicos = prob_doc_topico * prob_palabra_topico

                    # 3. Muestrear (El paso de la Cadena de Markov)
                    #    Elegimos un nuevo tópico (t_nuevo) basado en las probabilidades calculadas
                    prob_topicos /= np.sum(prob_topicos)  # Normalizar a 1
                    t_nuevo = np.random.multinomial(1, prob_topicos).argmax()

                    # 4. Re-asignar y re-contar
                    #    Ponemos la palabra de vuelta en el modelo con su nuevo tópico
                    self.asignaciones_Z[d][i] = t_nuevo
                    self.n_dt[d, t_nuevo] += 1
                    self.n_wt[w, t_nuevo] += 1
                    self.n_t[t_nuevo] += 1

        print("¡Modelo entrenado!")

    # -----------------------------------------------------------------
    # MÉTODO 3: MOSTRAR RESULTADOS (Reemplaza a print_topics)
    # -----------------------------------------------------------------
    def mostrar_topicos(self, num_palabras=10):
        """
        Imprime los tópicos en la consola leyendo nuestras matrices de conteo.
        """
        print("\n--- Tópicos Descubiertos (desde cero) ---")

        # Calculamos la matriz de distribución de palabras por tópico (llamada Phi)
        matriz_phi = (self.n_wt + self.beta) / (self.n_t + self.V * self.beta)

        for k in range(self.K):
            # Obtenemos las probabilidades para este tópico
            prob_palabras = matriz_phi[:, k]

            # Obtenemos los IDs de las 'num_palabras' más probables
            # argsort() nos da los índices de menor a mayor
            top_indices = prob_palabras.argsort()[-num_palabras:][::-1]  # Truco para obtener los N más altos

            # Construimos el string del tópico
            topic_str = f"Tópico {k}: "
            for i in top_indices:
                palabra = self.id_a_palabra[i]
                prob = prob_palabras[i]
                topic_str += f'{prob:.4f}*"{palabra}" + '

            print(topic_str.rstrip(" + "))

    # -----------------------------------------------------------------
    # MÉTODO 4: ELIMINADO
    # -----------------------------------------------------------------
    def guardar_visualizacion(self, nombre_archivo):
        """
        Este método ya no es compatible, ya que pyLDAvis depende de gensim.
        """
        print(f"AVISO: 'guardar_visualizacion' no está implementado en la versión 'desde cero'.")
        pass