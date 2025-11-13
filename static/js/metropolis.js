document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-metropolis');
    const seccionResultados = document.getElementById('resultados');
    const tasaValor = document.getElementById('tasa-valor');
    const selectDistribucion = document.getElementById('distribucion');
    
    // Grupos de parámetros
    const gruposParams = {
        'poisson': document.querySelectorAll('.params-poisson'),
        'binomial': document.querySelectorAll('.params-binomial'),
        'beta': document.querySelectorAll('.params-beta'),
        'student': document.querySelectorAll('.params-student'),
        'chi2': document.querySelectorAll('.params-chi2'),
        'fisher': document.querySelectorAll('.params-fisher')
    };

    let chartTrace = null;
    let chartHist = null;

    // 1. CAMBIAR VISIBILIDAD DE INPUTS
    selectDistribucion.addEventListener('change', () => {
        const tipo = selectDistribucion.value;
        
        // Ocultar todo primero
        Object.values(gruposParams).forEach(grupo => {
            grupo.forEach(el => el.classList.add('hidden'));
        });

        // Mostrar el seleccionado si existe en el mapa
        if (gruposParams[tipo]) {
            gruposParams[tipo].forEach(el => el.classList.remove('hidden'));
        }
    });

    // 2. ENVIAR Y GRAFICAR
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const data = {
            distribucion: selectDistribucion.value,
            iteraciones: document.getElementById('iteraciones').value,
            inicio_x: document.getElementById('inicio_x').value,
            inicio_y: document.getElementById('inicio_y').value,
            sigma: document.getElementById('sigma').value,
            
            // Params existentes
            lambda: document.getElementById('lambda').value,
            n: document.getElementById('n_binom').value,
            p: document.getElementById('p_binom').value,
            alpha_beta: document.getElementById('alpha_beta').value,
            beta_beta: document.getElementById('beta_beta').value,

            // ¡Nuevos Params!
            nu: document.getElementById('nu').value,
            k_chi: document.getElementById('k_chi').value,
            d1: document.getElementById('d1').value,
            d2: document.getElementById('d2').value
        };

        seccionResultados.classList.remove('hidden');

        fetch('/api/metropolis/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
                return;
            }
            tasaValor.textContent = data.tasa_aceptacion.toFixed(2);
            renderChartJS(data);
            renderPlotlySurface(data);
        });
    });

    // --- RENDER 2D (Chart.js) con Burn-in ---
    function renderChartJS(data) {
        const ctxTrace = document.getElementById('chart-trace').getContext('2d');
        const ctxHist = document.getElementById('chart-hist').getContext('2d');

        // 1. Procesar datos para Burn-in (Primer 10%)
        const totalPuntos = data.muestras_x.length;
        const puntoCorte = Math.floor(totalPuntos * 0.1); // 10% de Burn-in

        // Separamos datos en dos series, pero para que la línea sea continua,
        // la serie "Real" debe empezar donde termina la "Burn-in".
        
        // Datos Burn-in (0 a 10%)
        const dataBurnIn = data.muestras_x.slice(0, puntoCorte + 1);
        const labelsBurnIn = dataBurnIn.map((_, i) => i);

        // Datos Reales (10% a 100%)
        // Rellenamos con 'null' al principio para que empiece a la derecha
        const dataReal = new Array(puntoCorte).fill(null).concat(data.muestras_x.slice(puntoCorte));
        const labelsTotal = data.muestras_x.map((_, i) => i);

        // TRACEPLOT MEJORADO
        if (chartTrace) chartTrace.destroy();
        chartTrace = new Chart(ctxTrace, {
            type: 'line',
            data: {
                labels: labelsTotal,
                datasets: [
                    {
                        label: 'Burn-in (Calentamiento)',
                        data: dataBurnIn,
                        borderColor: 'rgba(200, 200, 200, 0.8)', // Gris/Rojo claro
                        borderWidth: 1,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: 'Muestreo (Convergencia)',
                        data: dataReal,
                        borderColor: 'rgba(54, 162, 235, 0.8)', // Azul
                        borderWidth: 1,
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { 
                    title: { display: true, text: 'Traceplot con Burn-in (Primer 10%)' },
                    tooltip: { enabled: true } 
                },
                scales: { 
                    x: { title: { display: true, text: 'Iteraciones' } },
                    y: { title: { display: true, text: 'Valor de X' } } 
                },
                animation: false
            }
        });

        // HISTOGRAMA (Solo usamos los datos post-burn-in para ser más exactos)
        if (chartHist) chartHist.destroy();
        
        // Nota: El histograma que viene del backend ya usa todos los datos.
        // Visualmente está bien, pero idealmente debería calcularse sin el burn-in.
        // Por ahora usaremos los datos del backend para coincidir con la gráfica 3D.
        chartHist = new Chart(ctxHist, {
            type: 'bar',
            data: {
                labels: data.hist1d_x.map(n => n.toFixed(2)),
                datasets: [{
                    label: 'Densidad Estimada',
                    data: data.hist1d_y,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    barPercentage: 1.0,
                    categoryPercentage: 1.0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { title: { display: true, text: 'Distribución Resultante' } }
            }
        });
    }

    // --- RENDER 3D MEJORADO ---
    function renderPlotlySurface(data) {
        const plotDiv = 'plotly-div';
        
        // Detectar si es discreta para cambiar el estilo visual
        // (Esto lo deducimos si los inputs de poisson/binomial están visibles o por lógica simple)
        // Pero 'surface' funciona bien para ambos si ajustamos contornos.

        const trace = {
            z: data.surface_z,
            x: data.surface_x,
            y: data.surface_y,
            type: 'surface',
            colorscale: 'Viridis',
            contours: {
                z: { 
                    show: true, 
                    usecolormap: true, 
                    highlightcolor: "#42f462", 
                    project: { z: true } 
                },
                // Agregamos líneas de contorno negras para resaltar la forma
                x: { show: true, color: 'rgba(0,0,0,0.1)' },
                y: { show: true, color: 'rgba(0,0,0,0.1)' }
            },
            // Suavizado: false ayuda a que las discretas se vean más "cuadradas"
            // pero true se ve más bonito para continuas. Dejémoslo automático.
        };

        const layout = {
            title: 'Superficie de Densidad 3D',
            autosize: true,
            scene: {
                xaxis: { title: 'X' },
                yaxis: { title: 'Y' },
                zaxis: { title: 'Probabilidad' },
                camera: { eye: { x: 1.5, y: 1.5, z: 1.2 } }
            },
            margin: { t: 50, r: 10, l: 10, b: 10 }
        };

        Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
    }


});