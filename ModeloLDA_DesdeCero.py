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
        self.palabra_a_id = None
        self.id_a_palabra = None
        self.corpus = None
        self.V = 0
        self.D = 0
        self.K = 0
        self.alpha = 0.1
        self.beta = 0.01
        self.n_dt = None
        self.n_wt = None
        self.n_t = None
        self.asignaciones_Z = None

    def preparar_corpus(self, no_below=5, no_above=0.8):
        """
        Construye el vocabulario (diccionario) y el corpus (BoW) desde cero,
        aplicando los filtros.
        """
        print("Creando Bolsa de Palabras (BoW) desde cero...")
        self.D = len(self.textos_procesados)
        frecuencia_doc = defaultdict(int)
        for doc in self.textos_procesados:
            for palabra in set(doc):
                frecuencia_doc[palabra] += 1

        vocabulario_filtrado = set()
        for palabra, freq in frecuencia_doc.items():
            if no_below <= freq <= self.D * no_above:
                vocabulario_filtrado.add(palabra)

        self.id_a_palabra = list(vocabulario_filtrado)
        self.palabra_a_id = {palabra: i for i, palabra in enumerate(self.id_a_palabra)}
        self.V = len(self.id_a_palabra)

        self.corpus = []
        for doc in self.textos_procesados:
            doc_de_ids = [self.palabra_a_id[palabra] for palabra in doc if palabra in self.palabra_a_id]
            self.corpus.append(doc_de_ids)

        if self.V == 0:
             print("¡ADVERTENCIA! El diccionario está vacío. Esto puede deberse a que 'no_below' es muy alto o el texto es muy corto.")
        else:
            print(f"Diccionario manual creado con {self.V} palabras únicas (después de filtrar).")


    def entrenar(self, num_topicos, iteraciones=1000, passes=None):
        """
        Entrena el modelo LDA usando Muestreo de Gibbs (MCMC / Cadenas de Markov).
        'passes' es un alias para 'iteraciones' para compatibilidad.
        """
        if passes:
            iteraciones = passes 

        print(f"Entrenando modelo LDA desde cero con {num_topicos} tópicos y {iteraciones} iteraciones...")
        self.K = num_topicos

        self.n_dt = np.zeros((self.D, self.K), dtype=int)
        self.n_wt = np.zeros((self.V, self.K), dtype=int)
        self.n_t = np.zeros(self.K, dtype=int)

        print("Inicializando estado aleatorio...")
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

        print(f"Iniciando {iteraciones} iteraciones de Muestreo de Gibbs...")
        
        for iter_num in range(iteraciones):
            if iter_num % 100 == 0:
                print(f"Iteración {iter_num}/{iteraciones}...")
                
            for d, doc in enumerate(self.corpus):
                for i, w in enumerate(doc): 
                    t_actual = self.asignaciones_Z[d][i]
                    self.n_dt[d, t_actual] -= 1
                    self.n_wt[w, t_actual] -= 1
                    self.n_t[t_actual] -= 1

                    prob_doc_topico = self.n_dt[d] + self.alpha
                    prob_palabra_topico = (self.n_wt[w] + self.beta) / (self.n_t + self.V * self.beta)
                    prob_topicos = prob_doc_topico * prob_palabra_topico

                    sum_prob_topicos = np.sum(prob_topicos)
                    if sum_prob_topicos == 0:
                        prob_topicos = np.ones(self.K) / self.K
                    else:
                        prob_topicos /= sum_prob_topicos
                    
                    t_nuevo = np.random.multinomial(1, prob_topicos).argmax()

                    self.asignaciones_Z[d][i] = t_nuevo
                    self.n_dt[d, t_nuevo] += 1
                    self.n_wt[w, t_nuevo] += 1
                    self.n_t[t_nuevo] += 1

        print("¡Modelo manual entrenado!")

    # -----------------------------------------------------------------
    # MÉTODO 3: MOSTRAR RESULTADOS (¡MODIFICADO!)
    # -----------------------------------------------------------------
    def mostrar_topicos(self, num_palabras=10):
        """
        Imprime los tópicos en la consola Y DEVUELVE los datos para los gráficos.
        """
        if self.V == 0:
             print("No se pueden mostrar tópicos porque el vocabulario está vacío.")
             return None # Devolver None si no hay datos
             
        print("\n--- Tópicos Descubiertos (Desde Cero / Manual) ---")

        # --- ¡CAMBIO AQUÍ! ---
        # topics_data_for_charting: Lista para guardar los datos para los gráficos
        topics_data_for_charting = [] 

        denominador_phi = self.n_t + self.V * self.beta
        # Usamos .T (transponer) para que el broadcasting de numpy funcione
        matriz_phi = (self.n_wt + self.beta) / denominador_phi[np.newaxis, :] 
        
        # Si matriz_phi no es (V, K), la transponemos
        if matriz_phi.shape[0] != self.V:
             matriz_phi = matriz_phi.T

        for k in range(self.K):
            prob_palabras = matriz_phi[:, k]
            top_indices = prob_palabras.argsort()[-num_palabras:][::-1]

            topic_str = f"Tópico {k}: "
            
            # --- ¡CAMBIO AQUÍ! ---
            # Guardamos las palabras y sus probabilidades para este tópico
            topic_terms = [] 
            for i in top_indices:
                palabra = self.id_a_palabra[i]
                prob = prob_palabras[i]
                topic_str += f'{prob:.4f}*"{palabra}" + '
                # Lo guardamos en el formato que usará Chart.js
                topic_terms.append({"palabra": palabra, "prob": prob})

            print(topic_str.rstrip(" + "))
            
            # Añadimos los datos de este tópico (ID, y lista de términos)
            # Invertimos los términos para que el gráfico de barras se muestre de mayor a menor
            topics_data_for_charting.append({
                "topic_id": k, 
                "terms": list(reversed(topic_terms))
            })
        
        # Devolvemos los datos para los gráficos
        return topics_data_for_charting