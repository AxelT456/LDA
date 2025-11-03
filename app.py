import os
import sys
import io
import contextlib
from flask import Flask, render_template, request, url_for, send_from_directory
from werkzeug.utils import secure_filename
import numpy as np
import traceback # Importamos traceback para imprimir errores

# Importa tus clases existentes
from LectorDocumentos import LectorDocumentos
from ProcesadorTexto import ProcesadorTexto
from ModeloLDA import ModeloLDA # El modelo de Gensim
from ModeloLDA_DesdeCero import ModeloLDA_DesdeCero # Tu modelo manual

# --- Configuración de Flask ---
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

# --- Base de datos de Patrones Conocidos ---
# ¡He añadido tu nuevo libro!
KNOWN_PATTERNS = {
    'Harry_Potter_y_la_Piedra_filosofal.pdf': r'\s*(\d+)\s*\n\s*([^\n]+)\s*',
    'Yo, robot - Isaac Asimov.pdf': r'\s*(\d+)\.\s*([^\n]+)\s*',
    'El Imperio Final Ed Ilustrada - Brandon Sanderson.pdf': r'\s*(\d+)\s*\n\s*([^\n]+)\s*',
    'Bovedas_de_acero_Traduccion_de_Luis_G_Prado_-_Isaac_Asimov.pdf': r'\s*(\d+)\.\s*([^\n]+)\s*' # Asume patrón "Yo, robot"
}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Verifica si la extensión del archivo es .pdf"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Muestra el formulario principal."""
    # Valores por defecto para la primera carga
    return render_template('index.html', 
                           num_topicos=10, 
                           num_pasadas=100, 
                           model_choice='gensim',
                           console_output=None,
                           viz_file_path=None,
                           manual_topics=None,
                           error=None) 

@app.route('/run', methods=['POST'])
def run_lda():
    """
    Recibe los datos del formulario, ejecuta el pipeline y 
    vuelve a renderizar la misma página (index.html) con los resultados.
    """
    # Leemos los valores del formulario PRIMERO.
    num_topics = int(request.form.get('num_topicos', 10))
    # --- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
    # Esta línea faltaba en la versión anterior.
    num_pasadas = int(request.form.get('num_pasadas', 100)) 
    model_choice = request.form.get('model_choice', 'gensim')

    # Función para renderizar la plantilla con todos los valores necesarios en caso de error
    def render_error(error_message):
        return render_template('index.html', 
                               error=error_message,
                               num_topicos=num_topics, 
                               num_pasadas=num_pasadas, # Ahora 'num_pasadas' está definido
                               model_choice=model_choice,
                               console_output=None,
                               viz_file_path=None,
                               manual_topics=None) 

    # 1. Validar y guardar el archivo PDF
    if 'pdf_file' not in request.files:
        return render_error("Error: No se encontró el archivo PDF.")
    
    file = request.files['pdf_file']
    if file.filename == '':
        return render_error("Error: No se seleccionó ningún archivo.")

    if not (file and allowed_file(file.filename)):
         return render_error("Error: Tipo de archivo no permitido. Sube un .pdf")
        
    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(pdf_path)

    # 2. Lógica de Patrón Automático
    final_pattern = None 
    print_source = ""
    
    # Comprobamos el nombre del archivo original
    original_filename = file.filename 
    if original_filename in KNOWN_PATTERNS:
        final_pattern = KNOWN_PATTERNS[original_filename]
        print_source = f"Patrón RegEx conocido encontrado para '{original_filename}'."
    elif filename in KNOWN_PATTERNS: # Como fallback
        final_pattern = KNOWN_PATTERNS[filename]
        print_source = f"Patrón RegEx conocido encontrado para '{filename}'."
    else:
        final_pattern = None # Usará el Plan B (dividir por página)
        print_source = f"Libro '{filename}' no conocido. Se usará división por página (Plan B)."
    
    # --- 3. Capturar la salida de la consola ---
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        
        # Variables para los resultados
        viz_file_path = None 
        manual_topics_data = None 
        
        try:
            print(f"--- Iniciando Proceso ---")
            print(f"Archivo: {filename}")
            # Esta línea ahora funcionará
            print(f"Tópicos: {num_topics}, Pasadas/Iteraciones: {num_pasadas}, Modelo: {model_choice}") 
            print(print_source)

            # --- 4. Ejecutar el Pipeline de NLP ---
            print("\nPASO 1: Leyendo y dividiendo PDF...")
            lector = LectorDocumentos(patron_division=final_pattern)
            paginas_texto = lector.extraer_texto_de_pdf(pdf_path) 
            
            if not paginas_texto:
                raise Exception("Error fatal: No se pudo leer el texto del PDF.")

            documentos = lector.dividir_en_documentos(paginas_texto)
            if not documentos:
                raise Exception("Error fatal: No se pudieron extraer documentos. (PDF vacío o longitud mínima muy alta).")

            print(f"\nPASO 2: Procesando {len(documentos)} documentos...")
            procesador = ProcesadorTexto(idioma='spanish')
            textos_procesados = [procesador.limpiar_y_tokenizar(doc) for doc in documentos]

            # --- 5. Ejecutar el Modelo(s) LDA ---
            no_below = 3
            no_above = 0.85

            # Modelo "Desde Cero"
            if model_choice == 'cero' or model_choice == 'ambos':
                print("\n" + "="*50)
                print("== EJECUTANDO: ModeloLDA_DesdeCero (Manual) ==")
                print("="*50)
                lda_cero = ModeloLDA_DesdeCero(textos_procesados)
                lda_cero.preparar_corpus(no_below=no_below, no_above=no_above)
                lda_cero.entrenar(num_topicos=num_topics, iteraciones=num_pasadas)
                manual_topics_data = lda_cero.mostrar_topicos()
                print("="*50)
                print("== ModeloDesdeCero finalizado. ==")

            # Modelo "Gensim"
            if model_choice == 'gensim' or model_choice == 'ambos':
                print("\n" + "="*50)
                print("== EJECUTANDO: ModeloLDA (Gensim) ==")
                print("="*50)
                lda_gensim = ModeloLDA(textos_procesados)
                lda_gensim.preparar_corpus(no_below=no_below, no_above=no_above)
                
                if len(lda_gensim.diccionario) == 0:
                     print("\nError: El diccionario de Gensim está vacío. El PDF es muy corto o los filtros son muy estrictos.")
                else:
                    lda_gensim.entrenar(num_topicos=num_topics, passes=num_pasadas)
                    lda_gensim.mostrar_topicos() 
                    
                    output_filename = "lda_visualizacion.html"
                    lda_gensim.guardar_visualizacion(output_filename) 
                    viz_file_path = url_for('static_files', filename=output_filename) 
                    print("="*50)
                    print(f"== ModeloGensim finalizado. Visualización generada. ==")
            
            print("\n✨ Proceso completado.")
        
        except Exception as e:
            # Capturamos cualquier error inesperado durante el análisis
            print(f"\n--- ¡ERROR DURANTE EL ANÁLISIS! ---")
            print(f"Ha ocurrido un error inesperado:")
            traceback.print_exc(file=f) # Imprime el traceback completo en la consola web

    # --- 6. Enviar resultados de VUELTA al index.html ---
    console_output = f.getvalue() # Obtener todo lo que se "imprimió"
    
    return render_template('index.html', 
                           console_output=console_output, 
                           viz_file_path=viz_file_path,
                           manual_topics=manual_topics_data, 
                           num_topicos=num_topics,
                           num_pasadas=num_pasadas,
                           model_choice=model_choice,
                           error=None) 

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

if __name__ == "__main__":
    print("Iniciando servidor Flask...")
    print("Abre http://127.0.0.1:5000 en tu navegador.")
    app.run(debug=True, port=5000)