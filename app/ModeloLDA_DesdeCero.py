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
        self.N_corpus = 0 #Guardar el total de palabras

    # -----------------------------------------------------------------
    # MÉTODO 1: PREPARAR EL CORPUS (Robustecido)
    # -----------------------------------------------------------------
    def preparar_corpus(self, no_below=5, no_above=0.8):
        """
        Construye el vocabulario (diccionario) y el corpus (BoW) desde cero,
        aplicando filtros inteligentes.
        """
        print("Creando Bolsa de Palabras (BoW) desde cero...")
        self.D = len(self.textos_procesados)

        # 1. Contar frecuencia de documentos por palabra
        frecuencia_doc = defaultdict(int)
        for doc in self.textos_procesados:
            for palabra in set(doc):
                frecuencia_doc[palabra] += 1

        # --- ARREGLO CRÍTICO: Ajuste de filtros para corpus pequeños ---
        # Si hay menos de 5 documentos, 'no_above' borraría todo.
        # Lo desactivamos (poniéndolo en 1.1, o sea 110%) en esos casos.
        if self.D < 5:
            print(f"⚠️ Corpus pequeño detectado ({self.D} docs). Desactivando filtro de frecuencia máxima.")
            limite_superior = self.D + 1 # Imposible de alcanzar, no borra nada
            # ¡CORRECCIÓN AQUÍ! Bajamos a 1 para que no borre palabras si D=1
            limite_inferior = 1 
        else:
            limite_superior = self.D * no_above
            limite_inferior = no_below

        # 2. Aplicar filtros
        vocabulario_filtrado = set()
        for palabra, freq in frecuencia_doc.items():
            if limite_inferior <= freq <= limite_superior:
                vocabulario_filtrado.add(palabra)

        # 3. Construir diccionarios
        self.id_a_palabra = list(vocabulario_filtrado)
        self.palabra_a_id = {palabra: i for i, palabra in enumerate(self.id_a_palabra)}
        self.V = len(self.id_a_palabra)

        # 4. Construir corpus
        self.corpus = []
        total_palabras = 0
        for doc in self.textos_procesados:
            doc_de_ids = [self.palabra_a_id[palabra] for palabra in doc if palabra in self.palabra_a_id]
            total_palabras += len(doc_de_ids)
            self.corpus.append(doc_de_ids)
            
        self.N_corpus = total_palabras 
        print(f"Diccionario creado con {self.V} palabras únicas.")
        print(f"{self.N_corpus} palabras totales en el corpus.")
        
        # Validación final para evitar división por cero más adelante
        if self.V == 0:
            raise ValueError("El vocabulario está vacío tras el filtrado. Intenta con un texto más largo o cambia la estrategia de división.")

    # -----------------------------------------------------------------
    # MÉTODO 2: ENTRENAR (Reemplaza a LdaModel con Muestreo de Gibbs)
    # -----------------------------------------------------------------
    def entrenar(self, num_topicos, iteraciones=1000, passes=1, alpha=None, beta=None, umbral=None, paciencia=None):
        """
        Entrena el modelo con Early Stopping configurable.
        Nota: 'iteraciones' actúa como límite máximo. Ignoramos 'passes' antiguo.
        """
        self.K = num_topicos
        
        # --- Auto-Configuración de Hiperparámetros ---
        if alpha is not None:
            self.alpha = alpha
        else:
            self.alpha = 50.0 / self.K
            
        if beta is not None:
            self.beta = beta
        else:
            if self.V > 0:
                self.beta = 1.0 / self.V
            else:
                self.beta = 0.01

        # --- Configuración de Convergencia (Defaults más tolerantes) ---
        # Por defecto: 0.01% de mejora (0.0001)
        umbral_mejora = umbral if umbral is not None else 0.01 
        # Convertimos porcentaje a decimal para el cálculo (ej: 0.01 -> 0.0001)
        # Si el usuario pone "0.01" en el input, lo interpretamos como %
        umbral_decimal = umbral_mejora / 100.0 
        
        # Por defecto: 10 intentos de paciencia
        paciencia_limite = paciencia if paciencia is not None else 10

        print(f"Entrenando LDA (K={num_topicos}). Max Iteraciones: {iteraciones}")
        print(f"Auto-Stop: Umbral={umbral_mejora}% ({umbral_decimal:.6f}), Paciencia={paciencia_limite}")

        # --- Inicialización Aleatoria ---
        self.n_dt = np.zeros((self.D, self.K), dtype=int)
        self.n_wt = np.zeros((self.V, self.K), dtype=int)
        self.n_t = np.zeros(self.K, dtype=int)
        self.asignaciones_Z = []
        
        for d, doc in enumerate(self.corpus):
            doc_asignaciones = []
            for palabra_id in doc:
                k = random.randint(0, self.K - 1)
                doc_asignaciones.append(k)
                self.n_dt[d, k] += 1
                self.n_wt[palabra_id, k] += 1
                self.n_t[k] += 1
            self.asignaciones_Z.append(doc_asignaciones)
            
        historial_entropia = []
        
        # Variables de control
        contador_sin_mejora = 0
        ultima_entropia = float('inf')
        
        total_iteraciones = iteraciones
        
        for i in range(total_iteraciones):
            
            # --- Paso de Gibbs ---
            for d, doc in enumerate(self.corpus):
                for idx_w, w in enumerate(doc):
                    t_actual = self.asignaciones_Z[d][idx_w]
                    self.n_dt[d, t_actual] -= 1
                    self.n_wt[w, t_actual] -= 1
                    self.n_t[t_actual] -= 1

                    prob_doc_topico = self.n_dt[d] + self.alpha
                    prob_palabra_topico = (self.n_wt[w] + self.beta) / (self.n_t + self.V * self.beta)
                    prob_topicos = prob_doc_topico * prob_palabra_topico
                    prob_topicos /= np.sum(prob_topicos)
                    
                    t_nuevo = np.random.multinomial(1, prob_topicos).argmax()

                    self.asignaciones_Z[d][idx_w] = t_nuevo
                    self.n_dt[d, t_nuevo] += 1
                    self.n_wt[w, t_nuevo] += 1
                    self.n_t[t_nuevo] += 1
            
            # --- Cálculo de Convergencia ---
            entropia_actual = self._calcular_log_entropia()
            historial_entropia.append(entropia_actual)
            
            if i > 0:
                # Calculamos mejora relativa
                mejora = (ultima_entropia - entropia_actual) / abs(ultima_entropia)
                
                if mejora < umbral_decimal:
                    contador_sin_mejora += 1
                    print(f"Iteración {i+1}: Mejora marginal ({mejora:.5%}). Paciencia: {contador_sin_mejora}/{paciencia_limite}")
                else:
                    contador_sin_mejora = 0 
                    print(f"Iteración {i+1}: Mejora significativa ({mejora:.5%}).")
            else:
                print(f"Iteración {i+1}: Entropía inicial = {entropia_actual:.4f}")

            ultima_entropia = entropia_actual

            # --- Chequeo de Parada ---
            if contador_sin_mejora >= paciencia_limite:
                print(f"⏹️ CONVERGENCIA ALCANZADA en la iteración {i+1}.")
                break

        print("¡Modelo entrenado!")
        return historial_entropia

    # -----------------------------------------------------------------
    # MÉTODO 3: MOSTRAR RESULTADOS (Reemplaza a print_topics)
    # -----------------------------------------------------------------
    def mostrar_topicos(self, num_palabras=10):
        """
        Imprime los tópicos y DEVUELVE una estructura de datos con ellos.
        """
        print("\n--- Tópicos Descubiertos (desde cero) ---")
        
        # Lista para guardar los datos que irán al JSON
        topicos_data = []

        # Calculamos la matriz de distribución de palabras por tópico (llamada Phi)
        matriz_phi = (self.n_wt + self.beta) / (self.n_t + self.V * self.beta)

        for k in range(self.K):
            prob_palabras = matriz_phi[:, k]

            # 1. Definimos cuántas palabras enviaremos al JSON (frontend)
            num_palabras_para_json = 30
            top_indices_json = prob_palabras.argsort()[-num_palabras_para_json:][::-1]

            # 2. Creamos la lista de palabras para el JSON
            palabras_del_topico = []
            for i in top_indices_json:
                palabra = self.id_a_palabra[i]
                prob = prob_palabras[i]
                palabras_del_topico.append({"palabra": palabra, "prob": float(prob)})
            
            topicos_data.append({
                "topico_id": k,
                "palabras": palabras_del_topico # Esta lista ahora tiene 30 palabras
            })

            # 3. El string para la consola sigue usando 'num_palabras' (ej. 10)
            topic_str = f"Tópico {k}: "
            # Usamos slicing en la lista que ya creamos
            for item in palabras_del_topico[:num_palabras]: 
                topic_str += f'{item["prob"]:.4f}*"{item["palabra"]}" + '

            print(topic_str.rstrip(" + "))
        
        return topicos_data

    # -----------------------------------------------------------------
    # MÉTODO 4: ELIMINADO
    # -----------------------------------------------------------------
    def guardar_visualizacion(self, nombre_archivo):
        """
        Este método ya no es compatible, ya que pyLDAvis depende de gensim.
        """
        print(f"AVISO: 'guardar_visualizacion' no está implementado en la versión 'desde cero'.")
        pass
    
    #-----------------------------------------------------------------
    # Metodo 5
    #-----------------------------------------------------------------
    def _calcular_log_entropia(self):
        """
        Calcula el log(entropia) / -log-likelihood normalizado
        según la fórmula de la imagen.
        """
        if self.N_corpus == 0:
            return 0.0

        # 1. Calcular matrices de probabilidad Theta (Doc-Topic) y Phi (Word-Topic)
        # (np.newaxis) es para hacer broadcasting de las sumas
        
        # Theta (D x K)
        suma_dt = self.n_dt.sum(axis=1) # Suma de palabras por doc (N_d)
        # Evitar división por cero si un doc quedó vacío tras filtrar
        suma_dt[suma_dt == 0] = 1 
        theta = (self.n_dt + self.alpha) / (suma_dt[:, np.newaxis] + self.K * self.alpha)
        
        # Phi (V x K)
        phi = (self.n_wt + self.beta) / (self.n_t[np.newaxis, :] + self.V * self.beta)
        
        log_likelihood_total = 0.0
        
        # Iterar sobre cada documento y sus palabras
        for d, doc in enumerate(self.corpus):
            if not doc:
                continue # Documento vacío
                
            # 2. Calcular P(w|d) para todas las palabras del vocabulario en este doc
            # P(w|d) = sum_k ( P(w|k) * P(k|d) )
            # P(w|d) = sum_k ( Phi[w, k] * Theta[d, k] )
            # Esto es un producto punto de Phi (V x K) y Theta[d] (1 x K)
            prob_palabras_doc = phi.dot(theta[d]) # Vector (V,)
            
            # 3. Acumular el log-likelihood
            # Contamos las palabras en el doc actual
            conteo_palabras_doc = defaultdict(int)
            for w_id in doc:
                conteo_palabras_doc[w_id] += 1
                
            for w_id, n_dw in conteo_palabras_doc.items():
                # n_{d,v} * log( P(w|d) )
                if prob_palabras_doc[w_id] > 0:
                    log_likelihood_total += n_dw * np.log(prob_palabras_doc[w_id])

        # 4. Aplicar la fórmula final de la imagen
        # log(entropia) = - (log_likelihood) / (Total Palabras)
        if log_likelihood_total == 0:
            return 0.0

        log_entropia = -log_likelihood_total / self.N_corpus
        return log_entropia