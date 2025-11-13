# 🧰 Toolkit de NLP Interactivo (LDA y Cadenas de Markov)

> Una aplicación web de Flask que implementa algoritmos de NLP desde cero, incluyendo Topic Modeling (LDA con Muestreo de Gibbs) y Generación de Texto (Cadenas de Markov).

Este proyecto sirve como un laboratorio interactivo para algoritmos de Procesamiento de Lenguaje Natural (NLP). En lugar de ser un script estático, es una **suite de herramientas web** donde puedes subir tus propios datos y experimentar con los modelos en tiempo real.

## 🚀 Herramientas Disponibles

Este toolkit actualmente contiene dos herramientas principales:

1.  **🔬 Topic Modeling (LDA desde Cero)**
    * Sube cualquier archivo `.pdf`.
    * Define los hiperparámetros (Tópicos, Alpha, Beta, Iteraciones).
    * Ejecuta un modelo LDA implementado manualmente con **Muestreo de Gibbs (MCMC)**.
    * Visualiza los resultados en **gráficas de barras interactivas** (`Chart.js`).
    * Edita los nombres de los tópicos y guarda los resultados en `JSON`.

2.  **🔗 Generador de Texto (Cadenas de Markov)**
    * Pega un bloque de texto de muestra.
    * El modelo aprende las probabilidades de la siguiente palabra.
    * Genera nuevo texto "al estilo de" la muestra original.

## 🛠️ Tecnologías Utilizadas

### Backend (Python)
* **Flask:** Para el servidor web y la API REST.
* **spaCy:** Para el pipeline de NLP (tokenización y **lematización**).
* **NumPy:** Para los cálculos matriciales del Muestreo de Gibbs en LDA.
* **pypdf:** Para leer el texto de los archivos PDF subidos.

### Frontend
* HTML5 / CSS3
* **JavaScript (ES6+):** Para manejar la lógica de la API (`fetch`), la interactividad y la manipulación del DOM.
* **Chart.js:** Para crear las visualizaciones de tópicos como gráficas de barras.

## ⚙️ Cómo Empezar

1.  Clona este repositorio:
    ```bash
    git clone [TU_URL_DE_GITHUB]
    cd [TU_REPOSITORIO]
    ```

2.  (Recomendado) Crea y activa un entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  Instala las dependencias de Python:
    ```bash
    pip install Flask numpy spacy pypdf
    pip install numba
    ```

4.  **¡IMPORTANTE!** Descarga el modelo de español para `spaCy`:
    ```bash
    python -m spacy download es_core_news_sm
    ```

5.  Ejecuta el servidor de Flask:
    ```bash
    python main.py
    ```

6.  ¡Abre la aplicación en tu navegador!
    * Ve a `http://127.0.0.1:5000`