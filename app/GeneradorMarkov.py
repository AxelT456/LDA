import random

class GeneradorMarkov:
    def __init__(self, texto_crudo):
        """
        Toma texto crudo, lo limpia y construye el modelo de Markov.
        """
        self.modelo = {}
        palabras = texto_crudo.lower().split()
        
        # 1. Construir el modelo
        for i in range(len(palabras) - 1):
            palabra_actual = palabras[i]
            palabra_siguiente = palabras[i+1]
            
            # Si la palabra actual no está en el modelo, la añadimos
            if palabra_actual not in self.modelo:
                self.modelo[palabra_actual] = {}
            
            # Si la palabra siguiente no está registrada para la actual, la añadimos
            if palabra_siguiente not in self.modelo[palabra_actual]:
                self.modelo[palabra_actual][palabra_siguiente] = 0
            
            # Aumentamos el conteo
            self.modelo[palabra_actual][palabra_siguiente] += 1
            
        # 2. Convertir conteos a probabilidades (aunque para 'random.choices' no es
        #    estrictamente necesario, es bueno tenerlo si se quiere)
        # Por simplicidad, usaremos los conteos como pesos.

    def generar_texto(self, num_palabras=50):
        """
        Genera nuevo texto basado en el modelo construido.
        """
        if not self.modelo:
            return "El modelo está vacío. Proporciona más texto."
            
        # 1. Elegir un punto de inicio aleatorio
        palabra_actual = random.choice(list(self.modelo.keys()))
        texto_generado = [palabra_actual.capitalize()]
        
        for _ in range(num_palabras - 1):
            # 2. Verificar si la palabra actual tiene sucesores
            if palabra_actual not in self.modelo or not self.modelo[palabra_actual]:
                # Si no hay sucesores (ej. es la última palabra del texto),
                # elegimos una nueva palabra aleatoria para reiniciar.
                palabra_actual = random.choice(list(self.modelo.keys()))
                continue
                
            # 3. Elegir la siguiente palabra basada en los pesos (conteos)
            siguientes_palabras = list(self.modelo[palabra_actual].keys())
            pesos = list(self.modelo[palabra_actual].values())
            
            palabra_siguiente = random.choices(siguientes_palabras, weights=pesos, k=1)[0]
            
            texto_generado.append(palabra_siguiente)
            palabra_actual = palabra_siguiente
            
        return " ".join(texto_generado) + "."