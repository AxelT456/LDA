import numpy as np
import math

class MetropolisHastings:
    def __init__(self):
        pass

    # --- FUNCIONES DE DENSIDAD (PDF/PMF) ---
    # (Estas funciones calculan la probabilidad de un punto)

    def _bimodal_pdf(self, x):
        return np.exp(-0.5 * ((x + 2) / 0.8) ** 2) + 1.5 * np.exp(-0.5 * ((x - 2) / 0.8) ** 2)

    def _poisson_pmf(self, k, lam):
        if k < 0 or not float(k).is_integer(): return 0.0
        try: return np.exp(int(k) * np.log(lam) - lam - math.lgamma(int(k) + 1))
        except: return 0.0

    def _binomial_pmf(self, k, n, p):
        if k < 0 or k > n or not float(k).is_integer(): return 0.0
        try: return math.comb(n, int(k)) * (p ** int(k)) * ((1 - p) ** (n - int(k)))
        except: return 0.0

    def _beta_pdf(self, x, alpha, beta):
        if x <= 0 or x >= 1: return 0.0
        try: return (x ** (alpha - 1)) * ((1 - x) ** (beta - 1))
        except: return 0.0

    def _bivariada_pdf(self, x, y):
        # Dos montañas acopladas en 2D
        z1 = np.exp(-1 * ((x + 1)**2 + (y + 1)**2))
        z2 = 0.8 * np.exp(-0.5 * ((x - 1.5)**2 + (y - 1.5)**2))
        return z1 + z2

    # --- MOTOR PRINCIPAL ---

    def ejecutar(self, params):
        tipo = params.get('distribucion', 'bimodal')
        n_iteraciones = int(params.get('iteraciones', 2000))
        
        # --- ¡CAMBIO! Recibir X e Y independientes ---
        # Si no vienen, usamos 0 como default
        x_actual = float(params.get('inicio_x', 0))
        y_actual = float(params.get('inicio_y', 0))
        
        sigma = float(params.get('sigma', 1.0))

        # Params específicos
        lam = float(params.get('lambda', 4))
        n_binom = int(params.get('n', 10))
        p_binom = float(params.get('p', 0.5))
        alpha_beta = float(params.get('alpha_beta', 2.0))
        beta_beta = float(params.get('beta_beta', 2.0))

        # Validación inicial para Beta (debe estar entre 0 y 1)
        # Si el usuario pone un inicio fuera de rango, lo corregimos para evitar crash
        if tipo == 'beta':
            if x_actual <= 0 or x_actual >= 1: x_actual = 0.5
            if y_actual <= 0 or y_actual >= 1: y_actual = 0.5

        samples_x = []
        samples_y = []
        aceptados = 0

        for _ in range(n_iteraciones):
            
            # --- 1. PROPUESTA (Salto) ---
            if tipo in ['bimodal', 'beta', 'bivariada']:
                # Continuo
                x_prop = np.random.normal(x_actual, sigma)
                y_prop = np.random.normal(y_actual, sigma)
            else:
                # Discreto
                salto_x = int(round(np.random.normal(0, sigma)))
                salto_y = int(round(np.random.normal(0, sigma)))
                # Evitar estancamiento si sigma es muy chico
                if salto_x == 0 and sigma >= 0.5: salto_x = np.random.choice([-1, 1])
                if salto_y == 0 and sigma >= 0.5: salto_y = np.random.choice([-1, 1])
                x_prop = x_actual + salto_x
                y_prop = y_actual + salto_y

            # --- 2. PROBABILIDADES ---
            if tipo == 'bivariada':
                # Caso especial: X e Y dependen uno del otro
                prob_act = self._bivariada_pdf(x_actual, y_actual)
                prob_new = self._bivariada_pdf(x_prop, y_prop)
            else:
                # Caso general: X e Y son independientes (P(x,y) = P(x)*P(y))
                # Esto crea una "montaña simétrica" 3D para las distribuciones 1D
                if tipo == 'bimodal':
                    p_ax, p_nx = self._bimodal_pdf(x_actual), self._bimodal_pdf(x_prop)
                    p_ay, p_ny = self._bimodal_pdf(y_actual), self._bimodal_pdf(y_prop)
                elif tipo == 'poisson':
                    p_ax, p_nx = self._poisson_pmf(x_actual, lam), self._poisson_pmf(x_prop, lam)
                    p_ay, p_ny = self._poisson_pmf(y_actual, lam), self._poisson_pmf(y_prop, lam)
                elif tipo == 'binomial':
                    p_ax, p_nx = self._binomial_pmf(x_actual, n_binom, p_binom), self._binomial_pmf(x_prop, n_binom, p_binom)
                    p_ay, p_ny = self._binomial_pmf(y_actual, n_binom, p_binom), self._binomial_pmf(y_prop, n_binom, p_binom)
                elif tipo == 'beta':
                    p_ax, p_nx = self._beta_pdf(x_actual, alpha_beta, beta_beta), self._beta_pdf(x_prop, alpha_beta, beta_beta)
                    p_ay, p_ny = self._beta_pdf(y_actual, alpha_beta, beta_beta), self._beta_pdf(y_prop, alpha_beta, beta_beta)
                
                prob_act = p_ax * p_ay
                prob_new = p_nx * p_ny

            # --- 3. RATIO & DECISIÓN ---
            if prob_act == 0: ratio = 1.0
            else: ratio = prob_new / prob_act

            if ratio >= 1 or np.random.rand() < ratio:
                x_actual = x_prop
                y_actual = y_prop
                aceptados += 1
            
            samples_x.append(x_actual)
            samples_y.append(y_actual)

        # --- RESULTADOS ---
        tasa_aceptacion = (aceptados / n_iteraciones) * 100
        
        # 1. Histograma 1D (Para Chart.js) - Solo usamos X
        if tipo in ['poisson', 'binomial']:
            min_v, max_v = int(min(samples_x)), int(max(samples_x))
            bins_1d = np.arange(min_v, max_v + 2) - 0.5
            hist_1d, bin_edges_1d = np.histogram(samples_x, bins=bins_1d, density=True)
            centros_1d = (bin_edges_1d[:-1] + bin_edges_1d[1:]) / 2
        elif tipo == 'beta':
            hist_1d, bin_edges_1d = np.histogram(samples_x, bins=50, range=(0, 1), density=True)
            centros_1d = (bin_edges_1d[:-1] + bin_edges_1d[1:]) / 2
        else:
            hist_1d, bin_edges_1d = np.histogram(samples_x, bins=50, density=True)
            centros_1d = (bin_edges_1d[:-1] + bin_edges_1d[1:]) / 2

        # 2. Matriz 3D (Para Plotly Surface) - Usamos X e Y
        # Creamos un histograma 2D (30x30 bins) para obtener las alturas Z
        bins_3d = 30
        range_3d = None
        if tipo == 'beta': range_3d = [[0, 1], [0, 1]]
        
        hist_2d, x_edges, y_edges = np.histogram2d(samples_x, samples_y, bins=bins_3d, range=range_3d, density=True)
        
        # Suavizado simple (opcional, para que la montaña se vea más bonita)
        # (Si prefieres datos crudos, comenta esto, pero ayuda visualmente)
        # hist_2d = scipy.ndimage.gaussian_filter(hist_2d, sigma=1) 

        return {
            "muestras_x": samples_x, # Para Traceplot
            "hist1d_y": hist_1d.tolist(), # Para Histograma 2D
            "hist1d_x": centros_1d.tolist(),
            
            # Datos para Plotly 3D Surface
            "surface_z": hist_2d.T.tolist(), # Transpuesta para alinear con Plotly
            "surface_x": ((x_edges[:-1] + x_edges[1:])/2).tolist(),
            "surface_y": ((y_edges[:-1] + y_edges[1:])/2).tolist(),
            
            "tasa_aceptacion": tasa_aceptacion
        }