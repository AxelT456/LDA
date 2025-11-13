import json
from flask import Flask, render_template, request, jsonify
from app.LectorDocumentos import LectorDocumentos
from app.ProcesadorTexto import ProcesadorTexto
from app.ModeloLDA_DesdeCero import ModeloLDA_DesdeCero
from app.GeneradorMarkov import GeneradorMarkov
from app.MetropolisHasting import MetropolisHastings

app = Flask(__name__)

# Objetos reutilizables
procesador_lda = ProcesadorTexto(idioma='spanish')
lector_paginas = LectorDocumentos(patron_division=None)

# --- RUTAS DE PÁGINAS ---
@app.route('/')
def index_general():
    return render_template('index.html')

@app.route('/lda')
def herramienta_lda():
    return render_template('lda.html')

@app.route('/markov')
def herramienta_markov():
    return render_template('markov.html')

@app.route('/metropolis')
def herramienta_metropolis():
    return render_template('metropolis.html')

# --- RUTAS DE API ---
@app.route('/api/procesar', methods=['POST'])
def procesar_lda_api():
    print("\n📩 Petición recibida en /api/procesar (LDA)")

    try:
        # 1. Validaciones de archivo
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No se encontró archivo PDF."}), 400
        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify({"error": "Archivo vacío o no seleccionado."}), 400

        # 2. Obtener parámetros básicos
        num_topicos = int(request.form.get('k', 10))
        
        # Iteraciones (Default alto para permitir auto-stop si no se especifica)
        iteraciones_input = request.form.get('iteraciones')
        iteraciones = int(iteraciones_input) if iteraciones_input else 1000

        # Estrategia de división (Capítulos vs Páginas)
        estrategia = request.form.get('estrategia', 'paginas')
        print(f"🔎 Estrategia seleccionada: {estrategia}")

        # 3. Obtener Parámetros Avanzados (Opcionales)
        # Convergencia (Umbral y Paciencia)
        umbral_input = request.form.get('umbral')
        paciencia_input = request.form.get('paciencia')
        umbral = float(umbral_input) if umbral_input else None
        paciencia = int(paciencia_input) if paciencia_input else None

        # Hiperparámetros (Alpha y Beta)
        alpha_input = request.form.get('alpha')
        beta_input = request.form.get('beta')
        alpha = float(alpha_input) if alpha_input else None
        beta = float(beta_input) if beta_input else None

        # 4. Procesar PDF según estrategia
        if estrategia == 'capitulos':
            # Intenta dividir por capítulos
            documentos = lector_paginas.extraer_texto_por_capitulos(file, min_longitud=500)
            # Fallback si falla la detección
            if len(documentos) < 2:
                print("⚠️ Pocos capítulos detectados. Usando división por páginas como respaldo.")
                file.seek(0)
                documentos = lector_paginas.extraer_texto_por_paginas(file, min_longitud=150)
        elif estrategia == 'completo':
            # Estrategia Completa (¡NUEVO!)
            documentos = lector_paginas.extraer_texto_completo(file, min_longitud=500)
        else:
            # Estrategia Páginas (Default)
            documentos = lector_paginas.extraer_texto_por_paginas(file, min_longitud=150)

        if not documentos:
            return jsonify({"error": "El PDF está vacío o ilegible."}), 400

        # 5. NLP y Modelo
        textos_procesados = [procesador_lda.limpiar_y_tokenizar(doc) for doc in documentos]

        lda = ModeloLDA_DesdeCero(textos_procesados)
        lda.preparar_corpus(no_below=2, no_above=0.9)

        # Entrenar (pasando todos los parámetros de control)
        historial_entropia = lda.entrenar(
            num_topicos=num_topicos,
            iteraciones=iteraciones,
            alpha=alpha,
            beta=beta,
            umbral=umbral,       
            paciencia=paciencia  
        )

        datos_topicos = lda.mostrar_topicos()

        # 6. Respuesta
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
        
        # --- ¡NUEVO! Obtener datos estadísticos ---
        # Devolvemos todo el modelo para que el JS lo filtre
        matriz_datos = generador.obtener_datos_visualizacion() 
        
        return jsonify({
            "texto_generado": texto_nuevo,
            "matriz": matriz_datos # Enviamos la matriz al frontend
        })

    except Exception as e:
        print(f"❌ Error Markov: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/metropolis/run', methods=['POST'])
def run_metropolis_api():
    try:
        # Recibimos todo el JSON de parámetros
        params = request.get_json()
        
        mh = MetropolisHastings()
        # Pasamos el diccionario completo al método ejecutar
        resultados = mh.ejecutar(params)
        
        return jsonify(resultados)
    except Exception as e:
        print(f"Error en Metropolis: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Servidor corriendo en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)