import numpy as np
import random
from collections import defaultdict
from numba import jit

# --- EL MOTOR TURBO (Compilado JIT) ---
# Esta función se compila a código máquina para velocidad extrema
@jit(nopython=True, cache=True)
def fast_gibbs_sampling(docs_indices, word_indices, z_assignments, n_dt, n_wt, n_t, K, V, alpha, beta):
    """
    Realiza una pasada completa de Muestreo de Gibbs usando Numba.
    """
    n_tokens = len(docs_indices)
    
    # Constante del denominador (parte derecha de la fórmula)
    v_beta = V * beta
    
    for i in range(n_tokens):
        d = docs_indices[i]
        w = word_indices[i]
        old_topic = z_assignments[i]

        # 1. Descontar (Removemos la palabra actual de los conteos)
        n_dt[d, old_topic] -= 1
        n_wt[w, old_topic] -= 1
        n_t[old_topic] -= 1

        # 2. Calcular Probabilidades (Fórmula de Gibbs Colapsado)
        # P(z=k) propto (n_d,k + alpha) * (n_w,k + beta) / (n_k + V*beta)
        
        # Vectorización manual para velocidad en Numba
        prob_sum = 0.0
        prob_dist = np.zeros(K)
        
        for k in range(K):
            # Parte Doc-Topico * Parte Topico-Palabra
            p = (n_dt[d, k] + alpha) * (n_wt[w, k] + beta) / (n_t[k] + v_beta)
            prob_dist[k] = p
            prob_sum += p

        # 3. Muestrear nuevo tópico (Sampling)
        # Método de la ruleta (Cumulative Sum)
        r = np.random.random() * prob_sum
        new_topic = K - 1 # Default al último por seguridad
        cumulative = 0.0
        for k in range(K):
            cumulative += prob_dist[k]
            if cumulative >= r:
                new_topic = k
                break

        # 4. Asignar y re-contar
        z_assignments[i] = new_topic
        n_dt[d, new_topic] += 1
        n_wt[w, new_topic] += 1
        n_t[new_topic] += 1

@jit(nopython=True, cache=True)
def calcular_log_entropia_fast(n_dt, n_wt, n_t, docs_indices, word_indices, K, V, alpha, beta):
    """Versión acelerada del cálculo de entropía"""
    # Calcular Theta y Phi
    # Nota: En Numba hacemos bucles explícitos para evitar overhead de numpy broadcasting complejo
    
    log_likelihood = 0.0
    
    # Precalcular denominador de Phi
    denom_phi = n_t + (V * beta)
    
    # Iterar sobre cada token del corpus
    for i in range(len(docs_indices)):
        d = docs_indices[i]
        w = word_indices[i]
        
        # Probabilidad de la palabra w en el documento d
        # P(w|d) = sum_k ( Phi[w,k] * Theta[d,k] )
        prob_w_d = 0.0
        
        # Denominador de Theta para este documento
        denom_theta_d = np.sum(n_dt[d]) + (K * alpha)
        
        for k in range(K):
            phi_wk = (n_wt[w, k] + beta) / denom_phi[k]
            theta_dk = (n_dt[d, k] + alpha) / denom_theta_d
            prob_w_d += phi_wk * theta_dk
            
        if prob_w_d > 0:
            log_likelihood += np.log(prob_w_d)
            
    return -log_likelihood / len(docs_indices)


class ModeloLDA_DesdeCero:

    def __init__(self, textos_procesados):
        self.textos_procesados = textos_procesados
        self.palabra_a_id = None
        self.id_a_palabra = None
        # Ya no usamos self.corpus como lista de listas para el entrenamiento
        # Usaremos arrays planos para Numba
        self.docs_array = None 
        self.words_array = None
        
        self.V = 0
        self.D = 0
        self.K = 0
        self.alpha = 0.1
        self.beta = 0.01

        self.n_dt = None
        self.n_wt = None
        self.n_t = None
        self.asignaciones_Z = None # Array plano
        self.N_corpus = 0

    def preparar_corpus(self, no_below=5, no_above=0.8):
        print("Creando Bolsa de Palabras (BoW) optimizada...")
        self.D = len(self.textos_procesados)

        frecuencia_doc = defaultdict(int)
        for doc in self.textos_procesados:
            for palabra in set(doc):
                frecuencia_doc[palabra] += 1

        # Filtros inteligentes
        if self.D < 5:
            limite_superior = self.D + 1
            limite_inferior = 1 
        else:
            limite_superior = self.D * no_above
            limite_inferior = no_below

        vocabulario_filtrado = set()
        for palabra, freq in frecuencia_doc.items():
            if limite_inferior <= freq <= limite_superior:
                vocabulario_filtrado.add(palabra)

        self.id_a_palabra = list(vocabulario_filtrado)
        self.palabra_a_id = {palabra: i for i, palabra in enumerate(self.id_a_palabra)}
        self.V = len(self.id_a_palabra)

        # --- APLANAR EL CORPUS PARA NUMBA ---
        # En lugar de [[1,2], [3,4]], creamos dos arrays largos:
        # docs:  [0, 0, 1, 1]
        # words: [1, 2, 3, 4]
        doc_list = []
        word_list = []
        
        for doc_id, doc in enumerate(self.textos_procesados):
            for palabra in doc:
                if palabra in self.palabra_a_id:
                    word_id = self.palabra_a_id[palabra]
                    doc_list.append(doc_id)
                    word_list.append(word_id)
        
        # Convertir a arrays de Numpy (int32 o int64)
        self.docs_array = np.array(doc_list, dtype=np.int32)
        self.words_array = np.array(word_list, dtype=np.int32)
        self.N_corpus = len(self.words_array)
        
        print(f"Diccionario: {self.V} palabras. Corpus: {self.N_corpus} tokens procesados.")
        
        if self.V == 0:
            raise ValueError("El vocabulario está vacío.")

    def entrenar(self, num_topicos, iteraciones=1000, passes=1, alpha=None, beta=None, umbral=None, paciencia=None):
        self.K = num_topicos
        
        # Configuración de Hiperparámetros
        self.alpha = alpha if alpha is not None else 50.0 / self.K
        self.beta = beta if beta is not None else (1.0 / self.V if self.V > 0 else 0.01)

        umbral_mejora = umbral if umbral is not None else 0.01 
        umbral_decimal = umbral_mejora / 100.0 
        paciencia_limite = paciencia if paciencia is not None else 10

        print(f"Entrenando LDA (Numba Acelerado). K={self.K}, Iter={iteraciones}")

        # Inicialización de Matrices
        self.n_dt = np.zeros((self.D, self.K), dtype=np.int32)
        self.n_wt = np.zeros((self.V, self.K), dtype=np.int32)
        self.n_t = np.zeros(self.K, dtype=np.int32)
        self.asignaciones_Z = np.zeros(self.N_corpus, dtype=np.int32)
        
        # Estado inicial aleatorio
        for i in range(self.N_corpus):
            d = self.docs_array[i]
            w = self.words_array[i]
            k = random.randint(0, self.K - 1)
            
            self.asignaciones_Z[i] = k
            self.n_dt[d, k] += 1
            self.n_wt[w, k] += 1
            self.n_t[k] += 1
            
        historial_entropia = []
        contador_sin_mejora = 0
        ultima_entropia = float('inf')
        
        # Bucle Principal
        for i in range(iteraciones):
            
            # --- PASO RÁPIDO CON NUMBA ---
            fast_gibbs_sampling(
                self.docs_array, 
                self.words_array, 
                self.asignaciones_Z, 
                self.n_dt, 
                self.n_wt, 
                self.n_t, 
                self.K, self.V, self.alpha, self.beta
            )
            
            # Calcular Entropía (También optimizado)
            entropia_actual = calcular_log_entropia_fast(
                self.n_dt, self.n_wt, self.n_t,
                self.docs_array, self.words_array,
                self.K, self.V, self.alpha, self.beta
            )
            historial_entropia.append(entropia_actual)
            
            # Lógica de Parada
            if i > 0:
                mejora = (ultima_entropia - entropia_actual) / abs(ultima_entropia)
                if mejora < umbral_decimal:
                    contador_sin_mejora += 1
                    # Opcional: Imprimir menos frecuente para no saturar consola si va muy rápido
                    if i % 10 == 0: 
                        print(f"Iter {i+1}: Mejora marginal ({mejora:.5%}). Paciencia: {contador_sin_mejora}")
                else:
                    contador_sin_mejora = 0
                    if i % 10 == 0:
                        print(f"Iter {i+1}: Mejora ({mejora:.5%}).")
            else:
                print(f"Iter 1: Entropía = {entropia_actual:.4f}")

            ultima_entropia = entropia_actual

            if contador_sin_mejora >= paciencia_limite:
                print(f"⏹️ CONVERGENCIA ALCANZADA en iteración {i+1}.")
                break

        return historial_entropia

    def mostrar_topicos(self, num_palabras=10):
        # Reutilizamos las matrices n_wt para mostrar los datos
        topicos_data = []
        
        # Calculamos Phi usando operaciones vectorizadas de numpy (ya son arrays)
        # (n_wt + beta) / (n_t + V*beta)
        # n_t necesita broadcasting
        matriz_phi = (self.n_wt + self.beta) / (self.n_t[np.newaxis, :] + self.V * self.beta)

        for k in range(self.K):
            prob_palabras = matriz_phi[:, k]
            num_json = 30
            top_indices = prob_palabras.argsort()[-num_json:][::-1]

            palabras_del_topico = []
            for idx in top_indices:
                palabra = self.id_a_palabra[idx]
                prob = prob_palabras[idx]
                palabras_del_topico.append({"palabra": palabra, "prob": float(prob)})
            
            topicos_data.append({
                "topico_id": k,
                "palabras": palabras_del_topico
            })
        
        return topicos_data
    
    # (Método antiguo eliminado por redundancia)
    def _calcular_log_entropia(self):
        pass