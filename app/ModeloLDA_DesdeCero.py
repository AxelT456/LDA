import numpy as np
from collections import defaultdict
from numba import jit

# --- FUNCIONES JIT NUMBA --- #
@jit(nopython=True, cache=True)
def fast_gibbs_sampling(docs_indices, word_indices, z_assignments, n_dt, n_wt, n_t, K, V, alpha, beta):
    n_tokens = len(docs_indices)
    v_beta = V * beta
    
    for i in range(n_tokens):
        d = docs_indices[i]
        w = word_indices[i]
        old_topic = z_assignments[i]

        # remover conteo
        n_dt[d, old_topic] -= 1
        n_wt[w, old_topic] -= 1
        n_t[old_topic] -= 1

        # calcular probabilidades
        prob_sum = 0.0
        prob_dist = np.zeros(K)
        for k in range(K):
            p = (n_dt[d, k] + alpha) * (n_wt[w, k] + beta) / (n_t[k] + v_beta)
            prob_dist[k] = p
            prob_sum += p

        # muestreo ruleta
        r = np.random.random() * prob_sum
        new_topic = K - 1 
        cumulative = 0.0
        for k in range(K):
            cumulative += prob_dist[k]
            if cumulative >= r:
                new_topic = k
                break

        # reasignar conteo
        z_assignments[i] = new_topic
        n_dt[d, new_topic] += 1
        n_wt[w, new_topic] += 1
        n_t[new_topic] += 1


@jit(nopython=True, cache=True)
def calcular_log_entropia_fast(n_dt, n_wt, n_t, docs_indices, word_indices, K, V, alpha, beta):
    log_likelihood = 0.0
    denom_phi = n_t + (V * beta)

    for i in range(len(docs_indices)):
        d = docs_indices[i]
        w = word_indices[i]
        prob_w_d = 0.0

        denom_theta_d = np.sum(n_dt[d]) + (K * alpha)

        for k in range(K):
            phi_wk = (n_wt[w, k] + beta) / denom_phi[k]
            theta_dk = (n_dt[d, k] + alpha) / denom_theta_d
            prob_w_d += phi_wk * theta_dk

        if prob_w_d > 0:
            log_likelihood += np.log(prob_w_d)

    return -log_likelihood / len(docs_indices)


# -------------------- CLASE MODELO LDA -------------------- #

class ModeloLDA_DesdeCero:

    def __init__(self, textos_procesados):
        self.textos_procesados = textos_procesados
        self.docs_array = None
        self.words_array = None
        self.V = 0
        self.D = 0
        self.K = 0
        self.alpha = 0.1
        self.beta = 0.01

    def preparar_corpus(self, no_below=5, no_above=0.8):
        from collections import defaultdict
        print("Creando BoW optimizado...")

        self.D = len(self.textos_procesados)
        frecuencia_doc = defaultdict(int)

        for doc in self.textos_procesados:
            for palabra in set(doc):
                frecuencia_doc[palabra] += 1

        if self.D < 5:
            limite_sup = self.D + 1
            limite_inf = 1 
        else:
            limite_sup = self.D * no_above
            limite_inf = no_below

        vocab = {palabra for palabra, freq in frecuencia_doc.items()
                 if limite_inf <= freq <= limite_sup}

        self.id_a_palabra = list(vocab)
        self.palabra_a_id = {palabra: i for i, palabra in enumerate(self.id_a_palabra)}
        self.V = len(self.palabra_a_id)

        doc_list, word_list = [], []
        for doc_id, doc in enumerate(self.textos_procesados):
            for palabra in doc:
                if palabra in self.palabra_a_id:
                    doc_list.append(doc_id)
                    word_list.append(self.palabra_a_id[palabra])

        self.docs_array = np.array(doc_list, dtype=np.int32)
        self.words_array = np.array(word_list, dtype=np.int32)
        self.N_corpus = len(self.words_array)

        print(f"Diccionario: {self.V} palabras | Tokens: {self.N_corpus}")
        if self.V == 0:
            raise ValueError("El vocabulario está vacío.")

    def entrenar(self, num_topicos, iteraciones=1000, alpha=None, beta=None,
                 umbral=None, paciencia=None, seed_base=None):

        self.K = num_topicos
        self.alpha = alpha if alpha is not None else 50.0 / self.K
        self.beta = beta if beta is not None else (1.0 / self.V)

        umbral_improv = (umbral if umbral is not None else 0.01) / 100
        paciencia_lim = paciencia if paciencia is not None else 10

        # ---------- SEED CONTROL ---------- #
        if seed_base is None:
            seed_base = np.random.randint(0, 99999999)
        np.random.seed(seed_base)

        # inicializar matrices
        self.n_dt = np.zeros((self.D, self.K), dtype=np.int32)
        self.n_wt = np.zeros((self.V, self.K), dtype=np.int32)
        self.n_t = np.zeros(self.K, dtype=np.int32)
        self.z_assign = np.random.randint(0, self.K, size=self.N_corpus).astype(np.int32)

        for i in range(self.N_corpus):
            d = self.docs_array[i]
            w = self.words_array[i]
            k = self.z_assign[i]
            self.n_dt[d, k] += 1
            self.n_wt[w, k] += 1
            self.n_t[k] += 1

        historial = []
        sin_mejora = 0
        last_ent = float("+inf")

        for i in range(iteraciones):
            fast_gibbs_sampling(self.docs_array, self.words_array,
                                self.z_assign, self.n_dt, self.n_wt,
                                self.n_t, self.K, self.V, self.alpha, self.beta)

            ent = calcular_log_entropia_fast(self.n_dt, self.n_wt, self.n_t,
                                             self.docs_array, self.words_array,
                                             self.K, self.V, self.alpha, self.beta)
            historial.append(ent)

            if ent > last_ent or (last_ent - ent) / abs(last_ent) < umbral_improv:
                sin_mejora += 1
            else:
                sin_mejora = 0

            last_ent = ent
            if sin_mejora >= paciencia_lim:
                break

        return historial

    def mostrar_topicos(self, num_palabras=10):
        matriz_phi = (self.n_wt + self.beta) / (self.n_t[np.newaxis, :] + self.V * self.beta)

        resultado = []
        for k in range(self.K):
            prob = matriz_phi[:, k]
            top = prob.argsort()[-num_palabras:][::-1]

            palabras = [{"palabra": self.id_a_palabra[idx], "prob": float(prob[idx])}
                        for idx in top]
            resultado.append({"topico_id": k, "palabras": palabras})

        return resultado
