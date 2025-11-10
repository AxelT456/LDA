document.addEventListener('DOMContentLoaded', () => {

    // --- Selectores de elementos ---
    const form = document.getElementById('form-lda');
    const contenedor = document.getElementById('contenedor-topicos');
    const estadoDiv = document.getElementById('estado-proceso');
    const boton = document.getElementById('btn-ejecutar');
    const fileInput = document.getElementById('pdf_file');
    
    // --- ¡NUEVO! Selector para la sección de resultados completa ---
    const seccionResultados = document.getElementById('resultados');

    const controlesResultados = document.getElementById('controles-resultados');
    const inputPalabrasVisibles = document.getElementById('num_palabras_visibles');
    const btnGuardar = document.getElementById('btn-guardar');

    // --- Variable global para guardar los datos ---
    let datosCompletosTopicos = [];

    // --- Evento principal del formulario (Submit) ---
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        if (!fileInput.files || fileInput.files.length === 0) {
            estadoDiv.innerHTML = '<p class="error">Por favor, selecciona un archivo PDF.</p>';
            // Asegurarse de que la sección de resultados se muestre para ver el error
            seccionResultados.classList.remove('hidden');
            return;
        }

        // 1. Mostrar estado de carga
        boton.disabled = true;
        boton.textContent = 'Procesando...';

        // Mostrar solo mensaje de carga (sin mostrar aún la sección de resultados)
        estadoDiv.innerHTML = '<p class="loading">Iniciando análisis. Esto puede tardar...</p>';
        contenedor.innerHTML = '';
        
        // Se asegura de ocultar los controles de *resultados* (botones)
        controlesResultados.classList.add('hidden'); 

        // 2. Preparar FormData
        const formDataManual = new FormData();
        formDataManual.append('pdf_file', fileInput.files[0]);
        formDataManual.append('k', document.getElementById('num_topicos').value);
        formDataManual.append('iteraciones', document.getElementById('iteraciones').value);
        formDataManual.append('alpha', document.getElementById('alpha').value);
        formDataManual.append('beta', document.getElementById('beta').value);
        
        // 3. Enviar datos al backend (Flask)
        fetch('/api/procesar', {
            method: 'POST',
            body: formDataManual
        })
        .then(response => {
            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
            return response.json();
        })
        .then(topicos => {
            // 4. ¡Éxito!
            estadoDiv.innerHTML = `<p class="success">Análisis completado.</p>`;
            
            if (topicos.error) {
                estadoDiv.innerHTML = `<p class="error">Error en Python: ${topicos.error}</p>`;
                datosCompletosTopicos = [];
                // No mostramos los controles si hay error
                return;
            }
            
            datosCompletosTopicos = topicos; 
            inputPalabrasVisibles.value = "10"; 
            
            // Solo mostramos los controles si todo salió bien
            seccionResultados.classList.remove('hidden');
            controlesResultados.classList.remove('hidden'); 
            
            renderizarTopicos(); 
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

    // --- Event listener para el input de palabras visibles ---
    inputPalabrasVisibles.addEventListener('change', renderizarTopicos);
    inputPalabrasVisibles.addEventListener('keyup', renderizarTopicos);

    // --- Event listener para el botón de Guardar ---
    btnGuardar.addEventListener('click', () => {
        // Usamos los títulos editados
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


    /**
     * Dibuja la VISTA DE LISTA para un tópico
     */
    function dibujarVistaLista(container, topico, numPalabras) {
        container.innerHTML = ""; // Limpiar
        
        const palabrasAMostrar = topico.palabras.slice(0, numPalabras);
        
        const listaPalabras = document.createElement('ul');
        listaPalabras.style.paddingLeft = '0';
        listaPalabras.style.listStyleType = 'none';

        palabrasAMostrar.forEach(item => {
            const li = document.createElement('li');
            li.style.display = 'flex';
            li.style.justifyContent = 'space-between';
            li.style.fontSize = '0.95rem';
            li.style.marginBottom = '0.5rem';

            const probFormateada = (item.prob * 100).toFixed(2);
            li.innerHTML = `
                <span class="palabra" style="font-weight: 600;">"${item.palabra}"</span>
                <span class="probabilidad" style="color: #555;">(${probFormateada}%)</span>
            `;
            listaPalabras.appendChild(li);
        });
        container.appendChild(listaPalabras);
    }

    /**
     * Dibuja la VISTA DE GRÁFICA para un tópico
     */
    function dibujarVistaGrafica(container, topico, numPalabras) {
        container.innerHTML = ""; // Limpiar
        
        const palabrasAMostrar = topico.palabras.slice(0, numPalabras).reverse();
        const labels = palabrasAMostrar.map(item => item.palabra);
        const dataPoints = palabrasAMostrar.map(item => item.prob * 100);

        const canvas = document.createElement('canvas');
        container.appendChild(canvas);

        const colorBarra = 'rgba(0, 86, 179, 0.7)';
        const colorBorde = 'rgba(0, 86, 179, 1)';

        new Chart(canvas.getContext('2d'), {
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

    /**
     * Función para cambiar entre vistas
     */
    function toggleVista(button, container, topico) {
        const numPalabras = parseInt(inputPalabrasVisibles.value, 10);
        const currentView = button.dataset.currentView;

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

    /**
     * Crea la estructura de las cards
     * y asigna los botones de toggle.
     */
    function renderizarTopicos() {
        contenedor.innerHTML = '';
        
        const numPalabras = parseInt(inputPalabrasVisibles.value, 10);
        if (isNaN(numPalabras) || numPalabras <= 0) return;

        datosCompletosTopicos.forEach(topico => {
            // 1. Crear la card
            const topicoDiv = document.createElement('div');
            topicoDiv.className = 'topico';

            // 2. Crear la cabecera (título + botón)
            const topicoHeader = document.createElement('div');
            topicoHeader.className = 'topico-header';

            // Título editable
            const titulo = document.createElement('h4');
            titulo.className = 'topico-titulo';
            titulo.textContent = topico.nombre_personalizado || `Tópico ${topico.topico_id}`;
            titulo.setAttribute('contenteditable', 'true');
            titulo.setAttribute('spellcheck', 'false');

            // Botón de Toggle
            const btnToggle = document.createElement('button');
            btnToggle.className = 'btn-toggle-view';
            btnToggle.textContent = 'Graficar';
            btnToggle.dataset.currentView = 'list';
            
            topicoHeader.appendChild(titulo);
            topicoHeader.appendChild(btnToggle);
            
            // 3. Crear el contenedor del contenido
            const contentContainer = document.createElement('div');
            contentContainer.className = 'topico-contenido';

            // 4. Dibujar la vista por defecto (lista)
            dibujarVistaLista(contentContainer, topico, numPalabras);

            // 5. Añadir listener al botón
            btnToggle.addEventListener('click', () => {
                toggleVista(btnToggle, contentContainer, topico);
            });

            // 6. Ensamblar la card
            topicoDiv.appendChild(topicoHeader);
            topicoDiv.appendChild(contentContainer);
            contenedor.appendChild(topicoDiv);
        });
    }
});