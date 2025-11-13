import random

class GeneradorMarkov:
    def __init__(self, texto_crudo):
        """
        Toma texto crudo, limpia, cuenta y luego CALCULA PROBABILIDADES.
        """
        self.conteos = {} # Matriz de conteos (bruta)
        self.matriz_prob = {} # Matriz de transición (normalizada)
        
        palabras = texto_crudo.lower().split()
        
        # 1. Fase de Conteo (Igual que antes)
        for i in range(len(palabras) - 1):
            palabra_actual = palabras[i]
            palabra_siguiente = palabras[i+1]
            
            if palabra_actual not in self.conteos:
                self.conteos[palabra_actual] = {}
            
            if palabra_siguiente not in self.conteos[palabra_actual]:
                self.conteos[palabra_actual][palabra_siguiente] = 0
            
            self.conteos[palabra_actual][palabra_siguiente] += 1
            
        # 2. Fase de Probabilidad (Normalización)
        print("\n--- 📊 Matriz de Transición de Markov (Extracto) ---")
        print(f"{'ESTADO ACTUAL':<15} | {'SIGUIENTES POSIBLES (Probabilidad)'}")
        print("-" * 60)
        
        limit_print = 0 # Para no llenar la consola si el texto es enorme
        
        for estado, transiciones in self.conteos.items():
            total_transiciones = sum(transiciones.values())
            self.matriz_prob[estado] = {}
            
            # String para imprimir en consola
            debug_str = []
            
            for siguiente, conteo in transiciones.items():
                # CÁLCULO DE PROBABILIDAD: Conteo / Total
                probabilidad = conteo / total_transiciones
                self.matriz_prob[estado][siguiente] = probabilidad
                
                # Formato visual (ej: "perro": 0.50)
                debug_str.append(f"'{siguiente}': {probabilidad:.2f}")
            
            # Imprimir solo los primeros 10 para ilustrar
            if limit_print < 10:
                print(f"'{estado}'".ljust(15) + " -> " + ", ".join(debug_str))
                limit_print += 1
                
        print("... (resto de la matriz procesada) ...\n")

    def generar_texto(self, num_palabras=50):
        """
        Genera texto usando la MATRIZ DE PROBABILIDADES explícita.
        """
        if not self.matriz_prob:
            return "El modelo está vacío."
            
        # 1. Elegir inicio
        palabra_actual = random.choice(list(self.matriz_prob.keys()))
        texto_generado = [palabra_actual.capitalize()]
        
        for _ in range(num_palabras - 1):
            # 2. Verificar si existe en la matriz
            if palabra_actual not in self.matriz_prob or not self.matriz_prob[palabra_actual]:
                palabra_actual = random.choice(list(self.matriz_prob.keys()))
                continue
                
            # 3. Seleccionar basado en PROBABILIDAD
            opciones = list(self.matriz_prob[palabra_actual].keys())
            probs = list(self.matriz_prob[palabra_actual].values())
            
            # random.choices usa los pesos decimales (probabilidades)
            palabra_siguiente = random.choices(opciones, weights=probs, k=1)[0]
            
            texto_generado.append(palabra_siguiente)
            palabra_actual = palabra_siguiente
            
        return " ".join(texto_generado) + "."
    
    def obtener_datos_visualizacion(self, top_n=None):
        """
        Devuelve la matriz de transición formateada para el frontend.
        Estructura: [{'palabra': 'el', 'siguientes': [{'palabra': 'perro', 'prob': 0.5}, ...]}, ...]
        """
        datos = []
        
        for estado, transiciones in self.matriz_prob.items():
            # Lista de siguientes palabras ordenadas por probabilidad
            lista_siguientes = []
            for sig, prob in transiciones.items():
                lista_siguientes.append({
                    "palabra": sig,
                    "prob": prob
                })
            
            # Ordenar las siguientes de mayor a menor probabilidad
            lista_siguientes.sort(key=lambda x: x['prob'], reverse=True)
            
            datos.append({
                "palabra_actual": estado,
                "siguientes": lista_siguientes,
                "total_opciones": len(lista_siguientes)
            })
        
        # Ordenar las palabras "padre" por cantidad de conexiones (las más interesantes primero)
        datos.sort(key=lambda x: x['total_opciones'], reverse=True)
        
        if top_n:
            return datos[:top_n]
        return datos