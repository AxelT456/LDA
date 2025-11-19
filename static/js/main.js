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

    // --- NUEVOS SELECTORES para Modos de Tópicos ---
    const radioTopicModeManual = document.querySelector('input[name="topic_mode"][value="manual"]');
    const radioTopicModeAuto = document.querySelector('input[name="topic_mode"][value="auto"]');
    const manualKConfigDiv = document.getElementById('manual-k-config');
    const autoKConfigDiv = document.getElementById('auto-k-config');

    // --- NUEVO: Función para alternar la visibilidad de los modos de tópico ---
    function toggleTopicMode() {
        if (radioTopicModeManual.checked) {
            manualKConfigDiv.classList.remove('hidden');
            autoKConfigDiv.classList.add('hidden');
            //contenedorOptimizacion.classList.add('hidden'); // Ocultar gráfica si se cambia a manual
        } else { // auto-k está checked
            manualKConfigDiv.classList.add('hidden');
            autoKConfigDiv.classList.remove('hidden');
        }
    }

    // --- NUEVO: Event Listeners para los botones de radio ---
    radioTopicModeManual.addEventListener('change', toggleTopicMode);
    radioTopicModeAuto.addEventListener('change', toggleTopicMode);

    // Ejecutar al cargar para establecer el estado inicial
    toggleTopicMode();

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
        const threshold = parseFloat(document.getElementById('k_threshold').value);
        const st = parseInt(document.getElementById('k_step').value);
        const rep = parseInt(document.getElementById('k_reps').value);

        // VALIDACIÓN CORRECTA
        if (isNaN(ks) || ks < 1) {
            alert("⚠️ El valor de K inicial debe ser un número mayor o igual a 1.");
            return;
        }

        if (isNaN(threshold) || threshold < 0 || threshold > 100) {
            alert("⚠️ El umbral debe estar entre 0% y 100%.");
            return;
        }

        if (isNaN(st) || st < 1) {
            alert("⚠️ El paso debe ser un número mayor o igual a 1.");
            return;
        }

        if (isNaN(rep) || rep < 1) {
            alert("⚠️ Las repeticiones deben ser un número mayor o igual a 1.");
            return;
        }

        const textoOriginal = btnOptimizar.textContent;
        btnOptimizar.disabled = true;
        btnOptimizar.textContent = "⏳ Calculando K óptimo...";

        const formData = new FormData();
        formData.append('pdf_file', fileInput.files[0]);
        formData.append('estrategia', document.getElementById('estrategia_division').value);

        // Config avanzadas
        if (inputIteraciones.value) formData.append('iteraciones', inputIteraciones.value);
        if (inputUmbral.value) formData.append('umbral', inputUmbral.value);
        if (inputPaciencia.value) formData.append('paciencia', inputPaciencia.value);

        // Config de optimización corregida
        formData.append('k_start', ks);
        formData.append('k_threshold', threshold);
        formData.append('k_step', st);
        formData.append('k_reps', rep);

        fetch('/api/lda/optimizar', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
                return;
            }
            contenedorOptimizacion.classList.remove('hidden');
            // 1. Dibujar la gráfica
            renderizarGraficaOptimizacion(data);

            // 2. Encontrar el mejor K
            let mejorK = data[0].k;
            let menorEntropia = data[0].mean;
            data.forEach(punto => {
                if (punto.mean < menorEntropia) {
                    menorEntropia = punto.mean;
                    mejorK = punto.k;
                }
            });

            console.log(`🤖 Mejor K: ${mejorK}`);

            // 3. Poner el valor en el input
            inputTopicos.value = mejorK;
            // Disparamos el evento 'input' para que se actualicen otras cosas si es necesario
            inputTopicos.dispatchEvent(new Event('input'));

            // 4. EJECUTAR AUTOMÁTICAMENTE
            setTimeout(() => {
                const notificacion = document.createElement('div');
                notificacion.textContent = `🚀 K óptimo (${mejorK}) detectado. Ejecutando...`;
                notificacion.style.color = "#28a745";
                notificacion.style.fontWeight = "bold";
                notificacion.style.marginTop = "10px";
                contenedorOptimizacion.appendChild(notificacion);

                // Ya no necesitamos cambiar el radio button a manual,
                // porque en el Paso 2 hicimos que el formulario funcione igual.
                
                boton.click(); // Simula el click en "Ejecutar Análisis"
                
                setTimeout(() => notificacion.remove(), 5000);
            }, 500);
        })
        .catch(err => {
            console.error(err);
            alert("Error al calcular K óptimo.");
        })
        .finally(() => {
            btnOptimizar.disabled = false;
            btnOptimizar.textContent = textoOriginal;
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
            alert("⚠️ Por favor, selecciona un archivo PDF primero.");
            return;
        }

        // --- VALIDACIÓN DE MODO AUTOMÁTICO ---
        if (radioTopicModeAuto.checked) {
            const kActual = parseInt(inputTopicos.value);

            if (isNaN(kActual) || kActual < 2) {
                alert("⚠️ Primero debes calcular el K ideal usando el botón 'Calcular K Ideal'.");
                return;
            }
        }

        // --- Preparar FormData ---
        const formData = new FormData();
        formData.append('pdf_file', fileInput.files[0]);
        formData.append('estrategia', selectEstrategia.value);

        // ANTES: Solo enviaba si estaba en manual
        // if (radioTopicModeManual.checked) {
        //    formData.append('num_topicos', inputTopicos.value);
        // }
        formData.append('num_topicos', inputTopicos.value); 
        formData.append('k', inputTopicos.value);

        // Configuración avanzada (solo si están seteadas)
        if (inputIteraciones.value) formData.append('iteraciones', inputIteraciones.value);
        if (inputUmbral.value)       formData.append('umbral', inputUmbral.value);
        if (inputPaciencia.value)    formData.append('paciencia', inputPaciencia.value);
        if (inputAlpha.value)        formData.append('alpha', inputAlpha.value);
        if (inputBeta.value)         formData.append('beta', inputBeta.value);

        // --- Enviar solicitud ---
        boton.disabled = true;
        boton.textContent = "⏳ Procesando...";

        fetch('/api/procesar', { // Asegúrate de que esta URL sea la correcta (/api/procesar)
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            boton.disabled = false;
            boton.textContent = "Ejecutar Análisis";

            if (data.error) {
                alert("❌ Error: " + data.error);
                return;
            }

            seccionResultados.classList.remove('hidden');
            controlesResultados.classList.remove('hidden');

            // --- 🛠️ BLOQUE CORREGIDO 🛠️ ---

            // 1. Guardar los datos en la variable global que usa tu función de renderizado
            datosCompletosTopicos = data.topicos;

            // 2. Llamar a la función con el nombre CORRECTO (renderizarTopicos)
            renderizarTopicos();

            // 3. Llamar a la gráfica de entropía con el nombre y dato CORRECTOS
            // (Tu backend manda 'entropia_data', no 'entropia')
            if (data.entropia_data) {
                detailsEntropia.classList.remove('hidden'); 
                detailsEntropia.open = true;
                renderizarGraficaEntropia(data.entropia_data);
            }
            
            // --- FIN BLOQUE CORREGIDO ---
        })
        .catch(err => {
            console.error(err);
            alert("❌ Error inesperado al ejecutar el análisis.");
            boton.disabled = false;
            boton.textContent = "Ejecutar Análisis";
        });
    });

    // --- FUNCIONES DE RENDERIZADO (Gráficas y Listas) ---

    // 1. Actualizar vista cuando cambias el número en el input
    inputPalabrasVisibles.addEventListener('input', () => {
        renderizarTopicos();
    });

    // 2. Descargar JSON cuando das click en Guardar
    btnGuardar.addEventListener('click', () => {
        if (!datosCompletosTopicos || datosCompletosTopicos.length === 0) {
            alert("⚠️ No hay datos procesados para guardar.");
            return;
        }
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(datosCompletosTopicos, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", "resultados_lda.json");
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    });
    
    function renderizarGraficaEntropia(datosEntropia) {
        const ctx = canvasEntropia.getContext("2d");
        let labels = [];
        let dataPoints = [];
        
        // Muestreo para no saturar la gráfica si son muchas iteraciones
        if (datosEntropia.length > 500) {
            const paso = Math.ceil(datosEntropia.length / 500);
            datosEntropia.forEach((valor, index) => {
                if (index % paso === 0) {
                    labels.push(`It. ${index + 1}`);
                    dataPoints.push(valor);
                }
            });
        } else {
            labels = datosEntropia.map((_, i) => `It. ${i + 1}`);
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
                    borderColor: '#28a745', // Verde para diferenciar
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 0, // Sin puntos para que sea más limpia
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, 
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: { display: true, title: { display: true, text: 'Iteraciones' } },
                    y: { display: true, title: { display: true, text: 'Entropía' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
    function obtenerNumPalabrasSeguro() {
        // Si el input está vacío o es inválido, usamos 10 por defecto
        let val = parseInt(inputPalabrasVisibles.value, 10);
        if (isNaN(val) || val < 1) {
            val = 10;
            // Opcional: Rellenar el input visualmente para que el usuario sepa
            inputPalabrasVisibles.value = 10; 
        }
        return val;
    }
    function dibujarVistaLista(container, topico, numPalabras) {
        container.innerHTML = "";
        const lista = document.createElement('ul');
        lista.className = 'lista-palabras-topico';
        
        const palabrasAMostrar = topico.palabras.slice(0, numPalabras);
        
        palabrasAMostrar.forEach(item => {
            const li = document.createElement('li');
            // Estilos inline para asegurar que se vea bien
            li.innerHTML = `
                <span style="font-weight: 600; color:#333;">"${item.palabra}"</span> 
                <span style="color: #666; font-family:monospace;">${(item.prob * 100).toFixed(2)}%</span>
            `;
            lista.appendChild(li);
        });
        container.appendChild(lista);
    }
    function dibujarVistaGrafica(container, topico, numPalabras) {
        container.innerHTML = "";
        // Invertimos para que la barra más larga salga arriba en el gráfico horizontal
        const palabrasAMostrar = topico.palabras.slice(0, numPalabras); 
        const labels = palabrasAMostrar.map(item => item.palabra);
        const dataPoints = palabrasAMostrar.map(item => item.prob * 100);

        const canvas = document.createElement('canvas');
        canvas.style.height = "100%";
        container.appendChild(canvas);

        container.chartInstance = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Probabilidad (%)',
                    data: dataPoints,
                    backgroundColor: 'rgba(0, 86, 179, 0.7)',
                    borderColor: 'rgba(0, 86, 179, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', // Gráfica Horizontal
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    x: { beginAtZero: true, grid: { display: false } },
                    y: { grid: { display: false } }
                }
            }
        });
    }
    function toggleVista(button, container, topico) {
        const numPalabras = obtenerNumPalabrasSeguro();
        const currentView = button.dataset.currentView;

        // Destruir gráfica anterior si existe para liberar memoria
        if (container.chartInstance) {
            container.chartInstance.destroy();
            container.chartInstance = null;
        }

        if (currentView === 'list') {
            dibujarVistaGrafica(container, topico, numPalabras);
            button.textContent = '📜 Ver Lista';
            button.dataset.currentView = 'graph';
        } else {
            dibujarVistaLista(container, topico, numPalabras);
            button.textContent = '📊 Graficar';
            button.dataset.currentView = 'list';
        }
    }
    function renderizarTopicos() {
        contenedor.innerHTML = '';
        // Usamos la función segura para evitar que falle si borras el input
        const numPalabras = obtenerNumPalabrasSeguro();

        if (!datosCompletosTopicos || datosCompletosTopicos.length === 0) return;

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
            btnToggle.textContent = '📊 Graficar';
            btnToggle.dataset.currentView = 'list';

            topicoHeader.appendChild(titulo);
            topicoHeader.appendChild(btnToggle);

            const contentContainer = document.createElement('div');
            contentContainer.className = 'topico-contenido';
            // Forzamos altura mínima para que la gráfica no se aplaste
            contentContainer.style.minHeight = "300px"; 
            contentContainer.chartInstance = null; 

            // Dibujamos lista por defecto
            dibujarVistaLista(contentContainer, topico, numPalabras);

            // Evento del botón "Graficar" individual
            btnToggle.addEventListener('click', () => {
                toggleVista(btnToggle, contentContainer, topico);
            });

            topicoDiv.appendChild(topicoHeader);
            topicoDiv.appendChild(contentContainer);
            contenedor.appendChild(topicoDiv);
        });
    }
});