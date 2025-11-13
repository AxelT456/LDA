document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-metropolis');
    const seccionResultados = document.getElementById('resultados');
    const tasaValor = document.getElementById('tasa-valor');
    const selectDistribucion = document.getElementById('distribucion');
    
    // Grupos de parámetros
    const paramsPoisson = document.querySelectorAll('.params-poisson');
    const paramsBinomial = document.querySelectorAll('.params-binomial');
    const paramsBeta = document.querySelectorAll('.params-beta');

    let chartTrace = null;
    let chartHist = null;

    // 1. CAMBIAR VISIBILIDAD DE INPUTS
    selectDistribucion.addEventListener('change', () => {
        const tipo = selectDistribucion.value;
        paramsPoisson.forEach(el => el.classList.add('hidden'));
        paramsBinomial.forEach(el => el.classList.add('hidden'));
        paramsBeta.forEach(el => el.classList.add('hidden'));

        if (tipo === 'poisson') paramsPoisson.forEach(el => el.classList.remove('hidden'));
        if (tipo === 'binomial') paramsBinomial.forEach(el => el.classList.remove('hidden'));
        if (tipo === 'beta') paramsBeta.forEach(el => el.classList.remove('hidden'));
    });

    // 2. ENVIAR Y GRAFICAR
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const data = {
            distribucion: selectDistribucion.value,
            iteraciones: document.getElementById('iteraciones').value,
            
            // --- ¡CAMBIO! Ahora enviamos X e Y por separado ---
            inicio_x: document.getElementById('inicio_x').value,
            inicio_y: document.getElementById('inicio_y').value,
            
            sigma: document.getElementById('sigma').value,
            lambda: document.getElementById('lambda').value,
            n: document.getElementById('n_binom').value,
            p: document.getElementById('p_binom').value,
            alpha_beta: document.getElementById('alpha_beta').value,
            beta_beta: document.getElementById('beta_beta').value
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

            // Renderizar SIEMPRE ambas vistas
            renderChartJS(data);
            renderPlotlySurface(data);
        });
    });

    // --- RENDER 2D (Chart.js) ---
    function renderChartJS(data) {
        const ctxTrace = document.getElementById('chart-trace').getContext('2d');
        const ctxHist = document.getElementById('chart-hist').getContext('2d');

        // Traceplot
        if (chartTrace) chartTrace.destroy();
        chartTrace = new Chart(ctxTrace, {
            type: 'line',
            data: {
                labels: data.muestras_x.map((_, i) => i),
                datasets: [{
                    label: 'Caminante (X)',
                    data: data.muestras_x,
                    borderColor: 'rgba(54, 162, 235, 0.6)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { title: { display: true, text: 'Traceplot (Evolución Temporal)' } },
                animation: false,
                scales: { x: { display: false } } // Ocultar etiquetas X para limpiar
            }
        });

        // Histograma 1D
        if (chartHist) chartHist.destroy();
        chartHist = new Chart(ctxHist, {
            type: 'bar',
            data: {
                labels: data.hist1d_x.map(n => n.toFixed(2)),
                datasets: [{
                    label: 'Distribución Marginal X',
                    data: data.hist1d_y,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    barPercentage: 1.0,
                    categoryPercentage: 1.0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { title: { display: true, text: 'Histograma (Vista Frontal)' } }
            }
        });
    }

    // --- RENDER 3D (Plotly Surface) ---
    function renderPlotlySurface(data) {
        const plotDiv = 'plotly-div';
        
        // Datos para la superficie 3D
        const trace = {
            z: data.surface_z, // Matriz de alturas
            x: data.surface_x, // Coordenadas X
            y: data.surface_y, // Coordenadas Y
            type: 'surface',   // ¡Esto hace la magia 3D real!
            colorscale: 'Viridis',
            contours: {
                z: {
                    show: true,
                    usecolormap: true,
                    highlightcolor: "#42f462",
                    project: { z: true } // Dibuja el contorno plano abajo también
                }
            }
        };

        const layout = {
            title: 'Superficie de Densidad Estimada (3D)',
            autosize: true,
            scene: {
                xaxis: { title: 'X' },
                yaxis: { title: 'Y' },
                zaxis: { title: 'Densidad' },
                camera: {
                    eye: { x: 1.5, y: 1.5, z: 1.2 } // Ángulo de cámara inicial
                }
            },
            margin: { t: 50, r: 10, l: 10, b: 10 }
        };

        const config = { responsive: true };

        Plotly.newPlot(plotDiv, [trace], layout, config);
    }
});