import json
from flask import Flask, render_template, request, jsonify

# --- 1. Importaciones de Lógica ---
from app.LectorDocumentos import LectorDocumentos
from app.ProcesadorTexto import ProcesadorTexto
from app.ModeloLDA_DesdeCero import ModeloLDA_DesdeCero
from app.GeneradorMarkov import GeneradorMarkov # ¡NUEVA IMPORTACIÓN!

# --- 2. Configuración Inicial ---
app = Flask(__name__) # (Asumiendo que tu 'static' ya está bien)

# --- 3. Objetos Reutilizables ---
# (Estos son para la herramienta LDA)
procesador_lda = ProcesadorTexto(idioma='spanish')
lector_paginas = LectorDocumentos(patron_division=None)
# (El generador de Markov se instancia por petición)


# -----------------------------------------------------------------
# --- RUTAS DE PÁGINAS (Frontend) ---
# -----------------------------------------------------------------

@app.route('/')
def index_general():
    """ 
    Sirve el NUEVO ÍNDICE GENERAL.
    Busca 'templates/index.html'
    """
    return render_template('index.html')

@app.route('/lda')
def herramienta_lda():
    """
    Sirve la HERRAMIENTA LDA (tu página antigua).
    Busca 'templates/lda.html'
    """
    return render_template('lda.html')

@app.route('/markov')
def herramienta_markov():
    """
    Sirve la NUEVA HERRAMIENTA DE MARKOV.
    Busca 'templates/markov.html'
    """
    return render_template('markov.html')


# -----------------------------------------------------------------
# --- RUTAS DE API (Backend) ---
# -----------------------------------------------------------------

@app.route('/api/procesar', methods=['POST'])
def procesar_lda_api():
    """
    Este es el API Endpoint para la herramienta LDA.
    (Este código es el que ya tenías, no ha cambiado)
    """
    print("\n¡Petición recibida en /api/procesar (LDA)!")
    
    try:
        # ... (Todo tu código de procesamiento de LDA va aquí) ...
        # 1. Recibir el archivo y los datos del formulario
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No se encontró ningún archivo PDF en la solicitud."}), 400
        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo."}), 400
        
        num_topicos = int(request.form.get('k', 10))
        alpha = float(request.form.get('alpha', 0.1))
        beta = float(request.form.get('beta', 0.01))
        iteraciones = int(request.form.get('iteraciones', 50))

        # 2. Leer y procesar el PDF
        documentos_por_pagina = lector_paginas.extraer_texto_por_paginas(file, min_longitud=150)
        if not documentos_por_pagina:
             return jsonify({"error": "El PDF está vacío o no se pudo leer."}), 400

        # 3. Procesar el texto
        textos_procesados = [procesador_lda.limpiar_y_tokenizar(doc) for doc in documentos_por_pagina]

        # 4. Ejecutar el Modelo LDA
        lda = ModeloLDA_DesdeCero(textos_procesados)
        lda.preparar_corpus(no_below=2, no_above=0.9)
        lda.entrenar(
            num_topicos=num_topicos, 
            passes=iteraciones, 
            alpha=alpha, 
            beta=beta
        )

        # 5. Obtener resultados
        datos_topicos = lda.mostrar_topicos()
        return jsonify(datos_topicos)

    except Exception as e:
        print(f"Error durante el procesamiento de LDA: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/markov/generar', methods=['POST'])
def generar_markov_api():
    """
    ¡NUEVO API ENDPOINT!
    Este es para la herramienta de Cadenas de Markov.
    """
    print("\n¡Petición recibida en /api/markov/generar!")
    
    try:
        data = request.get_json()
        texto_fuente = data.get('texto')
        num_palabras = int(data.get('palabras', 100))
        
        if not texto_fuente or len(texto_fuente) < 20:
            return jsonify({"error": "El texto fuente es muy corto."}), 400
            
        # 1. Crear el modelo
        generador = GeneradorMarkov(texto_fuente)
        
        # 2. Generar el texto
        texto_nuevo = generador.generar_texto(num_palabras)
        
        # 3. Devolver el resultado
        return jsonify({"texto_generado": texto_nuevo})

    except Exception as e:
        print(f"Error durante la generación de Markov: {e}")
        return jsonify({"error": str(e)}), 500


# --- 5. Ejecutar el Servidor ---
if __name__ == "__main__":
    print("Iniciando servidor Flask en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)