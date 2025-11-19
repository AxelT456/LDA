import json
import hashlib
import io
import numpy as np
from flask import Flask, render_template, request, jsonify
from app.LectorDocumentos import LectorDocumentos
from app.ProcesadorTexto import ProcesadorTexto
from app.ModeloLDA_DesdeCero import ModeloLDA_DesdeCero
from app.GeneradorMarkov import GeneradorMarkov
from app.MetropolisHasting import MetropolisHastings

app = Flask(__name__)

# --- CACHÉ EN MEMORIA ---
# Esto guardará los datos procesados del último archivo subido
class DataCache:
    def __init__(self):
        self.file_hash = None       # Huella digital del archivo
        self.strategy = None        # Estrategia usada (paginas/capitulos)
        self.textos_procesados = None # El resultado del NLP (lo que tarda mucho)

# Instancia global de la caché
cache = DataCache()

# Objetos reutilizables
procesador_lda = ProcesadorTexto(idioma='spanish')
lector_paginas = LectorDocumentos(patron_division=None)

# --- RUTAS DE PÁGINAS ---
@app.route('/')
def index_general(): return render_template('index.html')

@app.route('/lda')
def herramienta_lda(): return render_template('lda.html')

@app.route('/markov')
def herramienta_markov(): return render_template('markov.html')

@app.route('/metropolis')
def herramienta_metropolis(): return render_template('metropolis.html')


# --- FUNCIÓN HELPER: PROCESAMIENTO CON CACHÉ ---
def obtener_textos_procesados(file_storage, estrategia):
    """
    Verifica si el archivo es el mismo que está en memoria.
    Si es el mismo, devuelve los datos cacheados.
    Si no, procesa y actualiza la caché.
    """
    global cache

    # 1. Leer el archivo en memoria (bytes)
    # Usamos .read() para obtener los bytes y calcular el hash
    file_bytes = file_storage.read()
    
    # Calculamos el hash MD5 (Huella digital única del contenido)
    current_hash = hashlib.md5(file_bytes).hexdigest()
    
    # Rebobinamos el puntero del archivo por si se necesita leer de nuevo,
    # aunque usaremos BytesIO para pasarle el objeto en memoria a pypdf.
    file_storage.seek(0)
    file_stream = io.BytesIO(file_bytes)

    # 2. Verificar Caché
    if cache.file_hash == current_hash and cache.strategy == estrategia and cache.textos_procesados:
        print("⚡ CACHÉ HIT: Usando datos procesados en memoria (se saltó lectura y NLP).")
        return cache.textos_procesados

    # 3. Si no está en caché, procesar
    print("🐢 CACHÉ MISS: Procesando archivo nuevo o cambio de estrategia...")
    
    # A. Extracción de Texto
    documentos = []
    if estrategia == 'capitulos':
        documentos = lector_paginas.extraer_texto_por_capitulos(file_stream, min_longitud=500)
        if len(documentos) < 2:
            print("⚠️ Pocos capítulos. Fallback a páginas.")
            file_stream.seek(0)
            documentos = lector_paginas.extraer_texto_por_paginas(file_stream, min_longitud=150)
    elif estrategia == 'completo':
        documentos = lector_paginas.extraer_texto_completo(file_stream, min_longitud=500)
    else:
        documentos = lector_paginas.extraer_texto_por_paginas(file_stream, min_longitud=150)

    if not documentos:
        return None

    # B. Limpieza NLP (Esto es lo que más tarda)
    print("   Ejecutando NLP (spaCy)...")
    textos_procesados = [procesador_lda.limpiar_y_tokenizar(doc) for doc in documentos]

    # 4. Guardar en Caché
    cache.file_hash = current_hash
    cache.strategy = estrategia
    cache.textos_procesados = textos_procesados
    print("💾 Datos guardados en caché temporal.")

    return textos_procesados


# --- RUTAS DE API (LDA) ---

@app.route('/api/procesar', methods=['POST'])
def procesar_lda_api():
    print("\n📩 Petición recibida en /api/procesar (LDA)")
    try:
        if 'pdf_file' not in request.files: return jsonify({"error": "Falta PDF"}), 400
        file = request.files['pdf_file']
        if file.filename == '': return jsonify({"error": "Archivo vacío"}), 400

        # Parámetros
        num_topicos = int(request.form.get('k', 10))
        iter_input = request.form.get('iteraciones')
        iteraciones = int(iter_input) if iter_input else 1000
        estrategia = request.form.get('estrategia', 'paginas')
        
        # Avanzados
        umbral = float(request.form.get('umbral')) if request.form.get('umbral') else None
        paciencia = int(request.form.get('paciencia')) if request.form.get('paciencia') else None
        alpha = float(request.form.get('alpha')) if request.form.get('alpha') else None
        beta = float(request.form.get('beta')) if request.form.get('beta') else None

        # --- USAR SISTEMA DE CACHÉ ---
        textos_procesados = obtener_textos_procesados(file, estrategia)
        
        if not textos_procesados:
            return jsonify({"error": "El PDF está vacío o ilegible."}), 400

        # Entrenamiento
        lda = ModeloLDA_DesdeCero(textos_procesados)
        lda.preparar_corpus(no_below=2, no_above=0.9)

        historial_entropia = lda.entrenar(
            num_topicos=num_topicos,
            iteraciones=iteraciones,
            alpha=alpha, beta=beta,
            umbral=umbral, paciencia=paciencia
        )

        datos_topicos = lda.mostrar_topicos()

        return app.response_class(
            response=json.dumps({
                "topicos": datos_topicos,
                "entropia_data": historial_entropia
            }, ensure_ascii=False),
            mimetype='application/json'
        )

    except Exception as e:
        print(f"❌ Error en LDA: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/lda/optimizar', methods=['POST'])
def optimizar_k_api():
    """
    Barrido dinámico de K: Continúa indefinidamente hasta que la mejora
    de la entropía sea menor al umbral especificado.
    """
    print("\n🔎 Buscando K ideal (Barrido Dinámico)...")

    try:
        if 'pdf_file' not in request.files: return jsonify({"error": "Falta PDF"}), 400
        file = request.files['pdf_file']
        
        # 1. Cargar datos
        estrategia = request.form.get('estrategia', 'paginas')
        textos_procesados = obtener_textos_procesados(file, estrategia)
        if not textos_procesados: return jsonify({"error": "PDF vacío"}), 400

        # 2. Parámetros del barrido
        k_start = int(request.form.get('k_start', 2))
        k_step_input = request.form.get('k_step')
        
        # Paso automático si no se define
        if k_step_input and int(k_step_input) > 0:
            k_step = int(k_step_input)
        else:
            # (Lógica de paso automático simplificada para este ejemplo)
            k_step = 4 

        # Umbral de parada del barrido (ej. 0.01%)
        k_threshold_percent = float(request.form.get('k_threshold', 0.001))
        k_stop_threshold = k_threshold_percent / 100.0

        reps = int(request.form.get('k_reps', 3))

        # 3. Parámetros de convergencia (del modelo LDA)
        iter_input = request.form.get('iteraciones')
        iteraciones = int(iter_input) if iter_input else 1000
        umbral = float(request.form.get('umbral')) if request.form.get('umbral') else None
        paciencia = int(request.form.get('paciencia')) if request.form.get('paciencia') else None

        # 4. Preparar corpus
        print("   Preparando corpus base...")
        lda_base = ModeloLDA_DesdeCero(textos_procesados)
        lda_base.preparar_corpus(no_below=2, no_above=0.9)

        # 5. Bucle Indefinido (While)
        resultados = []
        k = k_start
        prev_entropy = float('inf') # Infinito para empezar
        
        print(f"   Iniciando barrido: Start K={k}, Step={k_step}, Stop Threshold={k_threshold_percent}%")

        # Límite de seguridad hardcodeado para evitar bucles eternos si nunca converge
        SAFETY_LIMIT_K = 200 

        while k <= SAFETY_LIMIT_K:
            entropias_rep = []
            
            # Repeticiones para promediar
            for r in range(reps):
                seed_base = np.random.randint(0, 99999999)
                historial = lda_base.entrenar(
                    num_topicos=k,
                    iteraciones=iteraciones,
                    alpha=50.0/k,
                    beta=None,
                    umbral=umbral,
                    paciencia=paciencia,
                    seed_base=seed_base
                )
                entropias_rep.append(historial[-1])
            
            mean_val = float(np.mean(entropias_rep))
            std_val = float(np.std(entropias_rep))
            
            # Calcular mejora respecto al K anterior
            # (La entropía debería BAJAR, así que (prev - current) debería ser positivo)
            if prev_entropy != float('inf'):
                mejora = (prev_entropy - mean_val) / abs(prev_entropy)
            else:
                mejora = 1.0 # Primera iteración siempre "mejora"

            resultados.append({
                "k": k, "mean": mean_val, "std": std_val
            })
            
            print(f"   K={k} -> Entropía: {mean_val:.4f}. Mejora: {mejora:.5%}")

            # --- CRITERIO DE PARADA ---
            # Si no es la primera vuelta Y la mejora es menor al umbral
            if prev_entropy != float('inf'):
                if mejora < k_stop_threshold:
                    print(f"   ⏹️ Deteniendo barrido: La mejora ({mejora:.4%}) es menor al umbral ({k_threshold_percent}%).")
                    break
                
                # También paramos si la entropía empieza a SUBIR (mejora negativa)
                # Esto indica sobreajuste o inestabilidad.
                if mejora < 0:
                    print(f"   ⏹️ Deteniendo barrido: La entropía empezó a subir.")
                    break

            prev_entropy = mean_val
            k += k_step

        if k > SAFETY_LIMIT_K:
            print("   ⚠️ Se alcanzó el límite de seguridad de K=200.")

        return jsonify(resultados)

    except Exception as e:
        print(f"❌ Error en Optimización: {e}")
        return jsonify({"error": str(e)}), 500



# --- RUTAS DE API (OTROS) ---
@app.route('/api/markov/generar', methods=['POST'])
def generar_markov_api():
    try:
        data = request.get_json()
        texto_fuente = data.get('texto')
        num_palabras = int(data.get('palabras', 100))

        if not texto_fuente or len(texto_fuente) < 20:
            return jsonify({"error": "El texto fuente es muy corto."}), 400

        generador = GeneradorMarkov(texto_fuente)
        texto_nuevo = generador.generar_texto(num_palabras)
        matriz_datos = generador.obtener_datos_visualizacion() 
        
        return jsonify({"texto_generado": texto_nuevo, "matriz": matriz_datos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/metropolis/run', methods=['POST'])
def run_metropolis_api():
    try:
        params = request.get_json()
        mh = MetropolisHastings()
        resultados = mh.ejecutar(params)
        return jsonify(resultados)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Servidor corriendo en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)