document.addEventListener('DOMContentLoaded', () => {

    const form = document.getElementById('form-markov');
    const seccionResultados = document.getElementById('resultados');
    const estadoDiv = document.getElementById('estado-proceso');
    const contenedor = document.getElementById('contenedor-resultado');
    const boton = document.getElementById('btn-ejecutar');

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        // 1. Recolectar datos
        const textoFuente = document.getElementById('texto_fuente').value;
        const numPalabras = document.getElementById('num_palabras').value;

        if (textoFuente.trim().length < 20) {
            seccionResultados.classList.remove('hidden');
            estadoDiv.innerHTML = '<p class="error">Por favor, introduce un texto fuente más largo.</p>';
            contenedor.innerHTML = '';
            return;
        }

        // 2. Mostrar estado de carga
        boton.disabled = true;
        boton.textContent = 'Generando...';
        seccionResultados.classList.remove('hidden');
        estadoDiv.innerHTML = '<p class="loading">Procesando modelo...</p>';
        contenedor.innerHTML = '';

        const datos = {
            texto: textoFuente,
            palabras: numPalabras
        };

        // 3. Enviar al nuevo API de Flask
        fetch('/api/markov/generar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        })
        .then(response => {
            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
            return response.json();
        })
        .then(data => {
            // 4. Mostrar resultados
            if (data.error) {
                estadoDiv.innerHTML = `<p class="error">${data.error}</p>`;
            } else {
                estadoDiv.innerHTML = `<p class="success">Texto generado exitosamente.</p>`;
                contenedor.textContent = data.texto_generado;
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

});