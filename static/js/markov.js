document.addEventListener('DOMContentLoaded', () => {

    const form = document.getElementById('form-markov');
    const seccionResultados = document.getElementById('resultados');
    const estadoDiv = document.getElementById('estado-proceso');
    const contenedorTexto = document.getElementById('contenedor-resultado');
    const boton = document.getElementById('btn-ejecutar');

    // --- Nuevos Selectores ---
    const seccionEstadisticas = document.getElementById('seccion-estadisticas');
    const contenedorTransiciones = document.getElementById('contenedor-transiciones');
    const inputVisibles = document.getElementById('palabras_visibles');
    const btnGuardar = document.getElementById('btn-guardar');

    // Variable global para guardar la matriz
    let matrizCompleta = [];

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        // 1. Recolectar datos
        const textoFuente = document.getElementById('texto_fuente').value;
        const numPalabras = document.getElementById('num_palabras').value;

        if (textoFuente.trim().length < 20) {
            seccionResultados.classList.remove('hidden');
            estadoDiv.innerHTML = '<p class="error">Por favor, introduce un texto fuente más largo.</p>';
            contenedorTexto.innerHTML = '';
            seccionEstadisticas.classList.add('hidden');
            return;
        }

        // 2. UI Carga
        boton.disabled = true;
        boton.textContent = 'Generando...';
        seccionResultados.classList.remove('hidden');
        estadoDiv.innerHTML = '<p class="loading">Procesando modelo...</p>';
        contenedorTexto.innerHTML = '';
        seccionEstadisticas.classList.add('hidden'); // Ocultar stats mientras carga

        // 3. Fetch
        fetch('/api/markov/generar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ texto: textoFuente, palabras: numPalabras })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                estadoDiv.innerHTML = `<p class="error">${data.error}</p>`;
            } else {
                estadoDiv.innerHTML = `<p class="success">Texto generado exitosamente.</p>`;
                contenedorTexto.textContent = data.texto_generado;
                
                // --- ¡NUEVO! Procesar Matriz ---
                matrizCompleta = data.matriz;
                seccionEstadisticas.classList.remove('hidden');
                renderizarMatriz(); // Dibujar las tarjetas
            }
        })
        .catch(error => {
            estadoDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        })
        .finally(() => {
            boton.disabled = false;
            boton.textContent = 'Generar Texto';
        });
    });

    // --- Eventos de Control ---
    inputVisibles.addEventListener('change', renderizarMatriz);
    inputVisibles.addEventListener('keyup', renderizarMatriz);

    btnGuardar.addEventListener('click', () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(matrizCompleta, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", "modelo_markov.json");
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    });

    // --- Función de Renderizado (Estilo LDA) ---
    function renderizarMatriz() {
        contenedorTransiciones.innerHTML = '';
        const limite = parseInt(inputVisibles.value) || 50;
        
        // Tomamos las primeras N palabras (que ya vienen ordenadas por 'importancia' desde Python)
        const datosAVisualizar = matrizCompleta.slice(0, limite);

        datosAVisualizar.forEach(item => {
            // Crear Card
            const card = document.createElement('div');
            card.className = 'topico'; // Reusamos la clase de LDA para estilo consistente

            // Título (Palabra Actual)
            const header = document.createElement('div');
            header.className = 'topico-header';
            header.innerHTML = `<h4 style="margin:0; color:#0056b3;">"${item.palabra_actual}"</h4>`;
            
            // Contenido (Lista de siguientes)
            const lista = document.createElement('ul');
            lista.style.paddingLeft = '0';
            lista.style.listStyle = 'none';
            lista.style.marginBottom = '0';

            // Mostramos solo las top 5 siguientes para no saturar la card
            const topSiguientes = item.siguientes.slice(0, 5); 
            
            topSiguientes.forEach(sig => {
                const li = document.createElement('li');
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.borderBottom = '1px solid #eee';
                li.style.padding = '4px 0';
                li.style.fontSize = '0.9rem';
                
                const probPercent = (sig.prob * 100).toFixed(1);
                
                li.innerHTML = `
                    <span>"${sig.palabra}"</span>
                    <span style="color:#666; font-size:0.85rem;">${probPercent}%</span>
                `;
                lista.appendChild(li);
            });

            // Si hay más opciones, mostramos un pequeño texto
            if (item.siguientes.length > 5) {
                const more = document.createElement('div');
                more.style.textAlign = 'center';
                more.style.fontSize = '0.8rem';
                more.style.color = '#999';
                more.style.marginTop = '5px';
                more.textContent = `+ ${item.siguientes.length - 5} opciones más...`;
                lista.appendChild(more);
            }

            card.appendChild(header);
            card.appendChild(lista);
            contenedorTransiciones.appendChild(card);
        });
    }

    // --- Función de Renderizado (Estilo Tabla) ---
    function renderizarMatriz() {
        contenedorTransiciones.innerHTML = '';
        const limite = parseInt(inputVisibles.value) || 50;
        
        // 1. Crear estructura de la tabla
        const tabla = document.createElement('table');
        tabla.className = 'markov-table';
        
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th style="width: 20%;">Palabra Actual</th>
                <th>Siguientes Posibles (Probabilidad)</th>
            </tr>
        `;
        tabla.appendChild(thead);

        const tbody = document.createElement('tbody');

        // 2. Obtener datos y limitar
        const datosAVisualizar = matrizCompleta.slice(0, limite);

        // 3. Llenar filas
        datosAVisualizar.forEach(item => {
            const tr = document.createElement('tr');
            
            // Columna 1: Palabra Origen
            const tdPalabra = document.createElement('td');
            tdPalabra.innerHTML = `<strong style="color: #333;">"${item.palabra_actual}"</strong>`;
            tr.appendChild(tdPalabra);

            // Columna 2: Transiciones
            const tdTransiciones = document.createElement('td');
            
            // Construimos las "badges" para cada transición
            const transicionesHTML = item.siguientes.map(sig => {
                const probPercent = (sig.prob * 100).toFixed(1);
                // Formato: "palabra" (15%)
                return `<span class="prob-badge">"${sig.palabra}" <span>(${probPercent}%)</span></span>`;
            }).join(' '); // Los unimos con espacios

            tdTransiciones.innerHTML = transicionesHTML;
            tr.appendChild(tdTransiciones);

            tbody.appendChild(tr);
        });

        tabla.appendChild(tbody);
        contenedorTransiciones.appendChild(tabla);
    }

});