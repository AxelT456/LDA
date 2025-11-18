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
    const selectEstrategia = document.getElementById('estrategia_division');
    
    // --- Configuración Avanzada ---
    const btnAvanzada = document.getElementById('btn-avanzada');
    const divAvanzada = document.getElementById('config-avanzada');
    const inputAlpha = document.getElementById('alpha');
    const inputBeta = document.getElementById('beta');
    const inputUmbral = document.getElementById('umbral');
    const inputPaciencia = document.getElementById('paciencia');
    const inputIteraciones = document.getElementById('iteraciones');

    // --- Selectores para Optimización ---
    const btnOptimizar = document.getElementById('btn-optimizar');
    const contenedorOptimizacion = document.getElementById('contenedor-optimizacion');
    const canvasOptimizacion = document.getElementById('grafica-optimizacion');
    const btnAvanzadaK = document.getElementById('btn-avanzada-k');
    const divConfigOptimizacion = document.getElementById('config-optimizacion');
    const canvasEntropia = document.getElementById('grafica-entropia');
    const detailsEntropia = document.getElementById('details-entropia');

    // --- NUEVO: Selectores del Modal ---
    const btnOpenModal = document.getElementById('btn-open-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const modalOverlay = document.getElementById('modal-info');

    if (btnOpenModal) {
        // --- EVENTO: Abrir y Cerrar Modal de Info ---
        btnOpenModal.addEventListener('click', () => {
            modalOverlay.classList.remove('hidden');
        });

        btnCloseModal.addEventListener('click', () => {
            modalOverlay.classList.add('hidden');
        });

        // Cerrar también al hacer clic en el fondo
        modalOverlay.addEventListener('click', (e) => {
            // Solo cierra si se hace clic en el fondo (overlay) y no en el contenido
            if (e.target === modalOverlay) {
                modalOverlay.classList.add('hidden');
            }
        });
    }
    
    // --- Variables de Instancia de Gráficas ---
    let chartOptimizacion = null;
    let graficaEntropiaInstance = null; // ¡ARREGLO! Movido aquí arriba.
    
    // --- Variable de Datos ---
    let datosCompletosTopicos = [];

    // --- EVENTO: Click en "Configurar barrido de K" ---
    btnAvanzadaK.addEventListener('click', () => {
        divConfigOptimizacion.classList.toggle('hidden');
    });

    // --- EVENTO: Click en "Calcular K Ideal" ---
    btnOptimizar.addEventListener('click', () => {
        if (!fileInput.files || fileInput.files.length === 0) {
            alert("⚠️ Por favor, selecciona un archivo PDF primero.");
            return;
        }
        const ks = parseInt(document.getElementById('k_start').value);
        const ke = parseInt(document.getElementById('k_end').value);
        const st = parseInt(document.getElementById('k_step').value);
        const rep = parseInt(document.getElementById('k_reps').value);

        if (ks < 1 || ke <= ks || st < 1 || rep < 1) {
            alert("⚠️ Parámetros inválidos para barrido de K");
            btnOptimizar.disabled = false;
            btnOptimizar.textContent = "🔍 Calcular K Ideal";
            return;
        }


        const textoOriginal = btnOptimizar.textContent;
        btnOptimizar.disabled = true;
        btnOptimizar.textContent = "⏳ Calculando...";
        
        const formData = new FormData();
        formData.append('pdf_file', fileInput.files[0]);
        formData.append('estrategia', document.getElementById('estrategia_division').value);

        if (inputIteraciones.value) formData.append('iteraciones', inputIteraciones.value);
        if (inputUmbral.value) formData.append('umbral', inputUmbral.value);
        if (inputPaciencia.value) formData.append('paciencia', inputPaciencia.value);

        formData.append('k_start', document.getElementById('k_start').value);
        formData.append('k_end', document.getElementById('k_end').value);
        formData.append('k_step', document.getElementById('k_step').value);
        formData.append('k_reps', document.getElementById('k_reps').value);

        fetch('/api/lda/optimizar', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("❌ Error: " + data.error);
                console.error("Error recibido:", data.error);
                return;
            }
            contenedorOptimizacion.classList.remove('hidden');
            renderizarGraficaOptimizacion(data);
        })
        .catch(err => {
            console.error(err);
            alert("Error al calcular K óptimo.");
        })
        .finally(() => {
            btnOptimizar.disabled = false;
            btnOptimizar.textContent = "🔍 Calcular K Ideal";
        });
    });

    // --- FUNCIÓN: Renderizar Gráfica K vs Entropía ---
    function renderizarGraficaOptimizacion(datos) {
        const ctx = canvasOptimizacion.getContext('2d');
        
        const labels = datos.map(d => `K=${d.k}`);
        const values = datos.map(d => d.mean); 
        const stdDev = datos.map(d => d.std);

        const dataUpper = values.map((val, i) => val + stdDev[i]);
        const dataLower = values.map((val, i) => val - stdDev[i]);

        if (chartOptimizacion) chartOptimizacion.destroy();

        chartOptimizacion = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                {
                    label: 'Entropía Promedio',
                    data: values,
                    borderColor: '#e67e22',
                    backgroundColor: 'rgba(230, 126, 34, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#d35400',
                    pointRadius: 4,
                    fill: 'origin',
                    tension: 0.3
                },
                {
                    label: 'Desviación Estándar',
                    data: dataUpper,
                    fill: '+1', 
                    backgroundColor: 'rgba(230, 126, 34, 0.15)',
                    borderColor: 'rgba(230, 126, 34, 0.2)',
                    borderWidth: 1,
                    pointRadius: 0,
                    tension: 0.3
                },
                {
                    label: 'Desv. Inf',
                    data: dataLower,
                    fill: false,
                    borderColor: 'rgba(230, 126, 34, 0.2)',
                    borderWidth: 1,
                    pointRadius: 0,
                    tension: 0.3
                }
            ]},
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `Entropía: ${ctx.parsed.y.toFixed(4)}`
                        }
                    },
                    legend: {
                        labels: {
                            filter: item => item.text === 'Entropía Promedio'
                        }
                    }
                },
                scales: {
                    y: { title: { display: true, text: 'Entropía (Perplejidad)' } },
                    x: { title: { display: true, text: 'Número de Tópicos (K)' } }
                },
                onClick: (e, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const kElegido = datos[index].k;
                        document.getElementById('num_topicos').value = kElegido;
                        document.getElementById('num_topicos').dispatchEvent(new Event('input'));
                    }
                }
            }
        });
    }
    
    // --- LÓGICA DE INTERFAZ (Placeholder y Toggle) ---
    btnAvanzada.addEventListener('click', () => {
        divAvanzada.classList.toggle('hidden');
        btnAvanzada.textContent = divAvanzada.classList.contains('hidden') ? 
            '⚙️ Mostrar Configuración Avanzada (Alpha/Beta/Stop)' : 
            '⚙️ Ocultar Configuración Avanzada';
    });

    function actualizarPlaceholderAlpha() {
        const k = parseInt(inputTopicos.value) || 10;
        const alphaDefault = k > 0 ? 50 / k : 0.1;
        inputAlpha.placeholder = `Auto (${alphaDefault.toFixed(4)})`;
    }
    inputTopicos.addEventListener('input', actualizarPlaceholderAlpha);
    actualizarPlaceholderAlpha();

    // --- LÓGICA PRINCIPAL (SUBMIT) ---
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!fileInput.files || fileInput.files.length === 0) {
            estadoDiv.innerHTML = '<p class="error">Por favor, selecciona un archivo PDF primero.</p>';
            seccionResultados.classList.remove('hidden');
            return;
        }
        boton.disabled = true;
        boton.textContent = 'Procesando...';
        seccionResultados.classList.remove('hidden');
        estadoDiv.innerHTML = '<p class="loading">Iniciando análisis. Esto puede tardar...</p>';
        contenedor.innerHTML = '';
        controlesResultados.classList.add('hidden'); 
        detailsEntropia.classList.add('hidden');
        detailsEntropia.open = false; 
        
        // ¡ARREGLO! Ahora esta variable existe y puede ser accedida.
        if (graficaEntropiaInstance) {
            graficaEntropiaInstance.destroy();
            graficaEntropiaInstance = null;
        }
        const formDataManual = new FormData();
        formDataManual.append('pdf_file', fileInput.files[0]);
        formDataManual.append('k', inputTopicos.value);
        if (selectEstrategia) {
            formDataManual.append('estrategia', selectEstrategia.value);
        }
        if (inputIteraciones.value) formDataManual.append('iteraciones', inputIteraciones.value);
        if (inputAlpha.value) formDataManual.append('alpha', inputAlpha.value);
        if (inputBeta.value) formDataManual.append('beta', inputBeta.value);
        if (inputUmbral.value) formDataManual.append('umbral', inputUmbral.value);
        if (inputPaciencia.value) formDataManual.append('paciencia', inputPaciencia.value);
        
        fetch('/api/procesar', {
            method: 'POST',
            body: formDataManual
        })
        .then(response => response.json())
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

    // --- FUNCIONES DE RENDERIZADO (Gráficas y Listas) ---
    
    function renderizarGraficaEntropia(datosEntropia) {
        // La variable 'graficaEntropiaInstance' ya está declarada arriba
        const ctx = canvasEntropia.getContext("2d");
        let labels = [];
        let dataPoints = [];
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