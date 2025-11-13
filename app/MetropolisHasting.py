import numpy as np
import math

class MetropolisHastings:
    def __init__(self):
        pass

    # --- FUNCIONES DE DENSIDAD ---

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

    # --- ¡NUEVAS! ---
    
    def _student_t_pdf(self, x, nu):
        """ T-Student: Similar a normal pero colas pesadas """
        # Proporcional a: (1 + x^2/nu)^(-(nu+1)/2)
        return (1 + (x**2)/nu) ** (-(nu + 1) / 2)

    def _chi_squared_pdf(self, x, k):
        """ Chi-Cuadrada: Solo x > 0 """
        if x <= 0: return 0.0
        try:
            # Proporcional a: x^(k/2 - 1) * e^(-x/2)
            return (x ** (k/2 - 1)) * np.exp(-x/2)
        except: return 0.0

    def _fisher_pdf(self, x, d1, d2):
        """ Fisher-Snedecor: Solo x > 0 """
        if x <= 0: return 0.0
        try:
            # Proporcional a: x^(d1/2 - 1) / (d1*x + d2)^((d1+d2)/2)
            numerador = x ** (d1/2 - 1)
            denominador = (d1 * x + d2) ** ((d1 + d2) / 2)
            return numerador / denominador
        except: return 0.0

    def _bivariada_pdf(self, x, y):
        z1 = np.exp(-1 * ((x + 1)**2 + (y + 1)**2))
        z2 = 0.8 * np.exp(-0.5 * ((x - 1.5)**2 + (y - 1.5)**2))
        return z1 + z2

    # --- MOTOR PRINCIPAL ---

    def ejecutar(self, params):
        tipo = params.get('distribucion', 'bimodal')
        n_iteraciones = int(params.get('iteraciones', 2000))
        x_actual = float(params.get('inicio_x', 0))
        y_actual = float(params.get('inicio_y', 0)) # Para 3D o Bivariada
        sigma = float(params.get('sigma', 1.0))

        # Parametros existentes
        lam = float(params.get('lambda', 4))
        n_binom = int(params.get('n', 10))
        p_binom = float(params.get('p', 0.5))
        alpha_beta = float(params.get('alpha_beta', 2.0))
        beta_beta = float(params.get('beta_beta', 2.0))

        # --- ¡NUEVOS PARÁMETROS! ---
        nu_student = float(params.get('nu', 5.0))      # Grados libertad t-Student
        k_chi = float(params.get('k_chi', 3.0))        # Grados libertad Chi2
        d1_fisher = float(params.get('d1', 10.0))      # Grados libertad 1 Fisher
        d2_fisher = float(params.get('d2', 20.0))      # Grados libertad 2 Fisher

        # Corrección de inicio para distribuciones positivas
        if tipo in ['chi2', 'fisher'] and x_actual <= 0:
            x_actual = 1.0
            y_actual = 1.0

        samples_x = []
        samples_y = []
        aceptados = 0

        for _ in range(n_iteraciones):
            
            # 1. PROPUESTA
            # Para discretas usamos redondeo, para continuas normal
            es_discreta = tipo in ['poisson', 'binomial']
            
            if es_discreta:
                salto_x = int(round(np.random.normal(0, sigma)))
                salto_y = int(round(np.random.normal(0, sigma)))
                if salto_x == 0 and sigma >= 0.5: salto_x = np.random.choice([-1, 1])
                if salto_y == 0 and sigma >= 0.5: salto_y = np.random.choice([-1, 1])
                x_prop = x_actual + salto_x
                y_prop = y_actual + salto_y
            else:
                x_prop = np.random.normal(x_actual, sigma)
                y_prop = np.random.normal(y_actual, sigma)

            # 2. PROBABILIDADES
            if tipo == 'bivariada':
                prob_act = self._bivariada_pdf(x_actual, y_actual)
                prob_new = self._bivariada_pdf(x_prop, y_prop)
            else:
                # Calculamos P(x) y P(y) por separado
                def get_prob(val):
                    if tipo == 'bimodal': return self._bimodal_pdf(val)
                    if tipo == 'poisson': return self._poisson_pmf(val, lam)
                    if tipo == 'binomial': return self._binomial_pmf(val, n_binom, p_binom)
                    if tipo == 'beta': return self._beta_pdf(val, alpha_beta, beta_beta)
                    # Nuevas
                    if tipo == 'student': return self._student_t_pdf(val, nu_student)
                    if tipo == 'chi2': return self._chi_squared_pdf(val, k_chi)
                    if tipo == 'fisher': return self._fisher_pdf(val, d1_fisher, d2_fisher)
                    return 0.0

                p_ax, p_nx = get_prob(x_actual), get_prob(x_prop)
                p_ay, p_ny = get_prob(y_actual), get_prob(y_prop)
                
                prob_act = p_ax * p_ay
                prob_new = p_nx * p_ny

            # 3. RATIO
            if prob_act == 0: ratio = 1.0
            else: ratio = prob_new / prob_act

            # 4. DECISIÓN
            if ratio >= 1 or np.random.rand() < ratio:
                x_actual = x_prop
                y_actual = y_prop
                aceptados += 1
            
            samples_x.append(x_actual)
            samples_y.append(y_actual)

        # --- RESULTADOS ---
        tasa_aceptacion = (aceptados / n_iteraciones) * 100
        
        # Histogramas
        if tipo in ['poisson', 'binomial']:
            min_v, max_v = int(min(samples_x)), int(max(samples_x))
            bins_1d = np.arange(min_v, max_v + 2) - 0.5
            hist_1d, bin_edges_1d = np.histogram(samples_x, bins=bins_1d, density=True)
            centros_1d = (bin_edges_1d[:-1] + bin_edges_1d[1:]) / 2
        elif tipo == 'beta':
            hist_1d, bin_edges_1d = np.histogram(samples_x, bins=50, range=(0, 1), density=True)
            centros_1d = (bin_edges_1d[:-1] + bin_edges_1d[1:]) / 2
        elif tipo in ['chi2', 'fisher']:
             # Limitamos rango para que no se vea feo si hay outliers lejanos
            hist_1d, bin_edges_1d = np.histogram(samples_x, bins=50, density=True)
            centros_1d = (bin_edges_1d[:-1] + bin_edges_1d[1:]) / 2
        else:
            hist_1d, bin_edges_1d = np.histogram(samples_x, bins=50, density=True)
            centros_1d = (bin_edges_1d[:-1] + bin_edges_1d[1:]) / 2

        # Generar Matriz 3D para TODAS las distribuciones
        bins_3d = 30
        range_3d = None
        if tipo == 'beta': range_3d = [[0, 1], [0, 1]]
        
        # Esto crea la "montaña" 3D cruzando X y Y
        hist_2d, x_edges, y_edges = np.histogram2d(samples_x, samples_y, bins=bins_3d, range=range_3d, density=True)

        return {
            "tipo": "bivariada" if tipo == 'bivariada' else "univariada",
            "muestras_x": samples_x,
            "hist1d_y": hist_1d.tolist(),
            "hist1d_x": centros_1d.tolist(),
            "surface_z": hist_2d.T.tolist(),
            "surface_x": ((x_edges[:-1] + x_edges[1:])/2).tolist(),
            "surface_y": ((y_edges[:-1] + y_edges[1:])/2).tolist(),
            "tasa_aceptacion": tasa_aceptacion
        }