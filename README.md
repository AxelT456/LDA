# 🔥 Topic Modeling: Harry Potter (Teoría vs. Práctica)

> Implementación de LDA desde cero (Muestreo de Gibbs) vs. `gensim` para Topic Modeling en *Harry Potter*. 🐍

Este proyecto explora la extracción de tópicos analizando *"Harry Potter y la piedra filosofal"*. Su característica principal es la **comparación directa** entre un modelo de librería (`gensim`) y un modelo implementado manualmente desde cero (`numpy`).



## 🔬 El Modelo: Teoría vs. Práctica

Este repositorio contiene dos "motores" de LDA que se ejecutan sobre el mismo texto procesado:

* **`ModeloLDA` (La Librería):** Utiliza `gensim.LdaModel`, que está altamente optimizado y usa **Inferencia Variacional** para converger rápidamente.
* **`ModeloLDA_DesdeCero` (La Teoría):** Es una implementación manual que utiliza **Muestreo de Gibbs (MCMC)**. Demuestra la teoría bayesiana subyacente y el funcionamiento de las Cadenas de Markov para asignar palabras a tópicos iterativamente.

## 🚀 Características

* **Parseo de PDF:** Lee `.pdf` y extrae el texto (`pypdf`).
* **División Semántica:** Divide el libro en capítulos usando Expresiones Regulares (`re`).
* **Pipeline de NLP:** Limpieza de texto, tokenización y *stemming* (`nltk`, `Snowball`).
* **BoW:** Creación de Bolsa de Palabras (manual y con `gensim`).
* **Comparación de Modelos:** Ejecuta `gensim` y el Muestreo de Gibbs uno tras otro.

## 🛠️ Tecnologías Utilizadas

* Python
* `numpy` (para el modelo MCMC)
* `gensim` (para el modelo de librería)
* `nltk` & `SnowballStemmer` (para limpieza y stemming)
* `pypdf` (para leer el PDF)
* `pyLDAvis` (para visualizar los resultados de `gensim`)

## ⚙️ Cómo Empezar

1.  Clona este repositorio:
    ```bash
    git clone [TU_URL_DE_GITHUB]
    cd [TU_REPOSITORIO]
    ```
2.  Crea y activa el entorno de Conda:
    ```bash
    # (Asegúrate de tener Miniconda instalado)
    conda create -n lda-env python=3.11
    conda activate lda-env
    ```
3.  Instala las dependencias:
    ```bash
    conda install -c conda-forge nltk gensim pandas scikit-learn pyldavis numpy
    pip install pypdf
    ```
4.  Descarga los recursos de NLTK (ejecuta en la terminal de PyCharm o en la consola de Python):
    ```python
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('punkt_tab')
    ```
5.  Coloca tu PDF (`Harry_Potter_y_la_Piedra_filosofal.pdf`) en la carpeta raíz.
6.  ¡Ejecuta el comparador!
    ```bash
    python main.py
    ```
