document.addEventListener('DOMContentLoaded', () => {

    // --- Selectores de elementos UI ---
    const form = document.getElementById('form-lda');
    const contenedor = document.getElementById('contenedor-topicos');
    const estadoDiv = document.getElementById('estado-proceso');
    const boton = document.getElementById('btn-ejecutar');
    const fileInput = document.getElementById('pdf_file');
    const seccionResultados = document.getElementById('resultados');
    const controlesResultados = document.getElementById('controles-resultados');
    const inputPalabrasVisibles = document.getElementById('num_palabras_visibles');
    const btnGuardar = document.getElementById('btn-guardar');

    // --- Selectores de Configuración ---
    const inputTopicos = document.getElementById('num_topicos');
    const selectEstrategia = document.getElementById('estrategia_division'); // ¡Nuevo!
    
    // --- Configuración Avanzada ---
    const btnAvanzada = document.getElementById('btn-avanzada');
    const divAvanzada = document.getElementById('config-avanzada');
    const inputAlpha = document.getElementById('alpha');
    const inputBeta = document.getElementById('beta');
    const inputUmbral = document.getElementById('umbral');     // ¡Nuevo!
    const inputPaciencia = document.getElementById('paciencia'); // ¡Nuevo!
    const inputIteraciones = document.getElementById('iteraciones');

    // --- Selectores para la gráfica de entropía ---
    const detailsEntropia = document.getElementById('details-entropia');
    const canvasEntropia = document.getElementById('grafica-entropia');
    
    // Variables de instancia para gráficas (para evitar superposiciones)
    let graficaEntropiaInstance = null;
    let datosCompletosTopicos = [];

    // ------------------------------------------------------
    // 1. LÓGICA DE INTERFAZ (Placeholder y Toggle)
    // ------------------------------------------------------
    
    // Mostrar/Ocultar Configuración Avanzada
    btnAvanzada.addEventListener('click', () => {
        if (divAvanzada.classList.contains('hidden')) {
            divAvanzada.classList.remove('hidden');
            btnAvanzada.textContent = '⚙️ Ocultar Configuración Avanzada';
        } else {
            divAvanzada.classList.add('hidden');
            btnAvanzada.textContent = '⚙️ Mostrar Configuración Avanzada (Alpha/Beta/Stop)';
        }
    });

    // Calcular Placeholder de Alpha dinámicamente (50/K)
    function actualizarPlaceholderAlpha() {
        const k = parseInt(inputTopicos.value) || 10;
        const alphaDefault = k > 0 ? 50 / k : 0.1;
        inputAlpha.placeholder = `Auto (${alphaDefault.toFixed(4)})`;
    }
    inputTopicos.addEventListener('input', actualizarPlaceholderAlpha);
    actualizarPlaceholderAlpha();

    // ------------------------------------------------------
    // 2. LÓGICA PRINCIPAL (SUBMIT)
    // ------------------------------------------------------
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        if (!fileInput.files || fileInput.files.length === 0) {
            estadoDiv.innerHTML = '<p class="error">Por favor, selecciona un archivo PDF.</p>';
            seccionResultados.classList.remove('hidden');
            return;
        }

        // --- UI de Carga ---
        boton.disabled = true;
        boton.textContent = 'Procesando...';
        seccionResultados.classList.remove('hidden');
        estadoDiv.innerHTML = '<p class="loading">Iniciando análisis. Esto puede tardar...</p>';
        contenedor.innerHTML = '';
        controlesResultados.classList.add('hidden'); 

        // --- Resetear Entropía ---
        detailsEntropia.classList.add('hidden');
        detailsEntropia.open = false; 
        if (graficaEntropiaInstance) {
            graficaEntropiaInstance.destroy();
            graficaEntropiaInstance = null;
        }

        // --- Preparar Datos ---
        const formDataManual = new FormData();
        formDataManual.append('pdf_file', fileInput.files[0]);
        formDataManual.append('k', inputTopicos.value);
        
        // Estrategia de división (Capítulos vs Páginas)
        if (selectEstrategia) {
            formDataManual.append('estrategia', selectEstrategia.value);
        }

        // Iteraciones (Si está vacío, el backend usará 1000 por defecto)
        if (inputIteraciones.value) formDataManual.append('iteraciones', inputIteraciones.value);
        
        // Parámetros Avanzados (Solo si el usuario escribió algo)
        if (inputAlpha.value) formDataManual.append('alpha', inputAlpha.value);
        if (inputBeta.value) formDataManual.append('beta', inputBeta.value);
        if (inputUmbral.value) formDataManual.append('umbral', inputUmbral.value);
        if (inputPaciencia.value) formDataManual.append('paciencia', inputPaciencia.value);
        
        // --- Enviar al Backend ---
        fetch('/api/procesar', {
            method: 'POST',
            body: formDataManual
        })
        .then(response => {
            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
            return response.json();
        })
        .then(data => { 
            estadoDiv.innerHTML = `<p class="success">Análisis completado.</p>`;
            
            if (data.error) {
                estadoDiv.innerHTML = `<p class="error">Error en Python: ${data.error}</p>`;
                datosCompletosTopicos = [];
                return;
            }
            
            datosCompletosTopicos = data.topicos; 
            const historialEntropia = data.entropia_data;

            inputPalabrasVisibles.value = "10"; 
            controlesResultados.classList.remove('hidden'); 
            
            renderizarTopicos(); 
            
            if (historialEntropia && historialEntropia.length > 0) {
                renderizarGraficaEntropia(historialEntropia);
                detailsEntropia.classList.remove('hidden'); 
                detailsEntropia.open = true; 
            }
        })
        .catch(error => {
            console.error('Error al procesar LDA:', error);
            estadoDiv.innerHTML = `<p class="error"><strong>Error al procesar la solicitud.</strong><br>${error.message}.</p>`;
            datosCompletosTopicos = [];
            controlesResultados.classList.add('hidden'); 
        })
        .finally(() => {
            boton.disabled = false;
            boton.textContent = 'Ejecutar Análisis';
        });
    });

    // ------------------------------------------------------
    // 3. EVENT LISTENERS SECUNDARIOS
    // ------------------------------------------------------
    inputPalabrasVisibles.addEventListener('change', renderizarTopicos);
    inputPalabrasVisibles.addEventListener('keyup', renderizarTopicos);

    btnGuardar.addEventListener('click', () => {
        document.querySelectorAll('.topico-titulo').forEach((tituloEl, index) => {
            if (datosCompletosTopicos[index]) {
                datosCompletosTopicos[index].nombre_personalizado = tituloEl.textContent;
            }
        });
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(datosCompletosTopicos, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", "resultados_lda.json");
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    });

    // ------------------------------------------------------
    // 4. FUNCIONES DE RENDERIZADO (Gráficas y Listas)
    // ------------------------------------------------------

    function renderizarGraficaEntropia(datosEntropia) {
        const ctx = canvasEntropia.getContext("2d");
        let labels = [];
        let dataPoints = [];

        // Optimización visual para muchas iteraciones
        if (datosEntropia.length > 500) {
            const paso = Math.ceil(datosEntropia.length / 500);
            datosEntropia.forEach((valor, index) => {
                if (index % paso === 0) {
                    labels.push(`Iteración ${index + 1}`);
                    dataPoints.push(valor);
                }
            });
            if ((datosEntropia.length - 1) % paso !== 0) {
                labels.push(`Iteración ${datosEntropia.length}`);
                dataPoints.push(datosEntropia[datosEntropia.length - 1]);
            }
        } else {
            labels = datosEntropia.map((_, i) => `Iteración ${i + 1}`);
            dataPoints = datosEntropia;
        }

        if (graficaEntropiaInstance) {
            graficaEntropiaInstance.destroy();
        }

        graficaEntropiaInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Log(Entropía)',
                    data: dataPoints,
                    borderColor: 'rgba(0, 86, 179, 0.8)',
                    backgroundColor: 'rgba(0, 86, 179, 0.2)',
                    tension: 0.2,
                    fill: true,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, 
                scales: {
                    x: {
                        title: { display: true, text: 'Pasadas de Gibbs' },
                        ticks: { maxTicksLimit: 10, maxRotation: 0 }
                    },
                    y: {
                        title: { display: true, text: 'Log(Entropía)' },
                        beginAtZero: false
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    function dibujarVistaLista(container, topico, numPalabras) {
        container.innerHTML = "";
        const lista = document.createElement('ul');
        lista.className = 'lista-palabras-topico';
        lista.style.listStyleType = 'none';
        lista.style.paddingLeft = '0';

        const palabrasAMostrar = topico.palabras.slice(0, numPalabras);
        palabrasAMostrar.forEach(item => {
            const li = document.createElement('li');
            li.style.display = 'flex';
            li.style.justifyContent = 'space-between';
            li.style.marginBottom = '0.5rem';
            li.style.fontSize = '0.95rem';
            
            li.innerHTML = `
                <span style="font-weight: 600;">"${item.palabra}"</span> 
                <span style="color: #555;">(${(item.prob * 100).toFixed(2)}%)</span>
            `;
            lista.appendChild(li);
        });
        container.appendChild(lista);
    }

    function dibujarVistaGrafica(container, topico, numPalabras) {
        container.innerHTML = "";
        const palabrasAMostrar = topico.palabras.slice(0, numPalabras).reverse();
        const labels = palabrasAMostrar.map(item => item.palabra);
        const dataPoints = palabrasAMostrar.map(item => item.prob * 100);
        
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);

        const colorBarra = 'rgba(0, 86, 179, 0.7)';
        const colorBorde = 'rgba(0, 86, 179, 1)';
        
        container.chartInstance = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Probabilidad (%)',
                    data: dataPoints,
                    backgroundColor: colorBarra,
                    borderColor: colorBorde,
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, ticks: { callback: (v) => v + '%' } } }
            }
        });
    }

    function toggleVista(button, container, topico) {
        const numPalabras = parseInt(inputPalabrasVisibles.value, 10);
        const currentView = button.dataset.currentView;

        if (container.chartInstance) {
            container.chartInstance.destroy();
            container.chartInstance = null;
        }

        if (currentView === 'list') {
            dibujarVistaGrafica(container, topico, numPalabras);
            button.textContent = 'Ver Lista';
            button.dataset.currentView = 'graph';
        } else {
            dibujarVistaLista(container, topico, numPalabras);
            button.textContent = 'Graficar';
            button.dataset.currentView = 'list';
        }
    }

    function renderizarTopicos() {
        contenedor.innerHTML = '';
        const numPalabras = parseInt(inputPalabrasVisibles.value, 10);
        if (isNaN(numPalabras) || numPalabras <= 0) return;

        datosCompletosTopicos.forEach(topico => {
            const topicoDiv = document.createElement('div');
            topicoDiv.className = 'topico';

            const topicoHeader = document.createElement('div');
            topicoHeader.className = 'topico-header';
            
            const titulo = document.createElement('h4');
            titulo.className = 'topico-titulo';
            titulo.textContent = topico.nombre_personalizado || `Tópico ${topico.topico_id}`;
            titulo.setAttribute('contenteditable', 'true');
            titulo.setAttribute('spellcheck', 'false');
            
            const btnToggle = document.createElement('button');
            btnToggle.className = 'btn-toggle-view';
            btnToggle.textContent = 'Graficar';
            btnToggle.dataset.currentView = 'list';
            
            topicoHeader.appendChild(titulo);
            topicoHeader.appendChild(btnToggle);
            
            const contentContainer = document.createElement('div');
            contentContainer.className = 'topico-contenido';
            contentContainer.chartInstance = null; 

            dibujarVistaLista(contentContainer, topico, numPalabras);
            
            btnToggle.addEventListener('click', () => {
                toggleVista(btnToggle, contentContainer, topico);
            });
            
            topicoDiv.appendChild(topicoHeader);
            topicoDiv.appendChild(contentContainer);
            contenedor.appendChild(topicoDiv);
        });
    }
});