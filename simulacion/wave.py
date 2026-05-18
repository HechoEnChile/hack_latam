import numpy as np 
from typing import Dict, TYPE_CHECKING
from gps import Gps
from leo import Leo

class Wave:

# Constantes físicas universales (valores exactos según estándares)
    SPEED_OF_LIGHT: float = 299_792_458.0          # m/s
    BOLTZMANN_K: float = 1.380649e-23              # J/K
    TEMPERATURA_RUIDO: float = 290.0               # K (temperatura de ruido equivalente)
    ANCHO_BANDA: float = 20.0e6                    # Hz (ancho de banda típico GPS L1 C/A)
    RETARDO_IONO_BASE: float = 5.0                 # metros equivalentes (modelo simplificado)

    def __init__(
        self,
        gps: 'Gps',
        t_recepcion: int,
        potencia_tx: float = 25.0,          
        frecuencia: float = 1.57542e9       
    ) -> None:

        self._gps = gps
        self._t_recepcion = t_recepcion
        self._potencia_tx = potencia_tx
        self._frecuencia = frecuencia

    @property
    def gps(self) -> 'Gps':
        return self._gps

    @property
    def t_recepcion(self) -> int:
        return self._t_recepcion

    def VacummProp(self, leo: 'Leo') -> Dict[str, float]:
        # Obtener estados orbitales en el instante de recepción común

        pos_gps = self.gps.posVector(self.t_recepcion)
        vel_gps = self.gps.posVelocity(self.t_recepcion)
        pos_leo = leo.posVector(self.t_recepcion)
        vel_leo = leo.posVelocity(self.t_recepcion)

        # Vector de línea de vista y distancia
        d_vec = pos_leo - pos_gps
        d = float(np.linalg.norm(d_vec))
        if d < 1e-6:
            raise ValueError("Distancia cero detectada entre GPS y LEO; verifique datos orbitales.")

        unit_vec = d_vec / d

        # 1. Retardo de propagación
        retardo = d / self.SPEED_OF_LIGHT

        # 2. Desplazamiento Doppler
        v_rel = vel_leo - vel_gps
        v_radial = float(np.dot(v_rel, unit_vec))
        doppler = - (v_radial / self.SPEED_OF_LIGHT) * self._frecuencia

        # 3. Densidad de potencia (ley del inverso del cuadrado)
        densidad_potencia = self._potencia_tx / (4.0 * np.pi * d * d)

        # 4. Potencia recibida (FSPL con ganancias de antena unitarias)
        lambda_ = self.SPEED_OF_LIGHT / self._frecuencia
        fspl = (4.0 * np.pi * d / lambda_) ** 2
        potencia_recibida = self._potencia_tx / fspl

        # 5. Ruido térmico
        ruido_termico = self.BOLTZMANN_K * self.TEMPERATURA_RUIDO * self.ANCHO_BANDA

        # 6. Atenuación ionosférica (modelo simplificado con variabilidad realista)
        atenuacion_iono = self.RETARDO_IONO_BASE * (1.0 + np.random.normal(0.0, 2.0))

        return {
            'distancia_m': d,
            'potencia_recibida_w': potencia_recibida,
            'retardo_propagacion_s': retardo,
            'desplazamiento_doppler_hz': doppler,
            'densidad_potencia_w_m2': densidad_potencia,
            'ruido_termico_w': ruido_termico,
            'atenuacion_iono_m': atenuacion_iono
        }

    def generateObject(self) -> Dict[str, float]:
        return {
            'velocidad': float(np.random.uniform(100, 8000)),           # velocidad orbital típica
            'diametro': float(np.random.uniform(0.5, 15.0)),            # desde pequeño debris hasta satélite grande
            'distancia_hacia_gps': float(np.random.uniform(50, 800))    # distancia al GPS (metros)
        }

    def interference_propagation(self, leo: 'Leo', obj: Dict[str, float] = None) -> Dict[str, float]:
        if obj is None:
            obj = self.generateObject()

        # Camino directo
        metrics_vacuum = self.VacummProp(leo)
        d_direct = metrics_vacuum['distancia_m']

        # Camino reflejado (más largo según distancia del objeto al GPS)
        extra_path = 2 * obj['distancia_hacia_gps']   # ida y vuelta aproximada
        d_reflected = d_direct + extra_path

        # Coeficiente de reflexión (depende del tamaño del objeto)
        reflection_coeff = min(0.9, 0.4 + 0.04 * obj['diametro'])   # mayor diámetro → más reflexión

        # Amplitud de la señal reflejada
        amplitude_reflected = reflection_coeff * (d_direct / d_reflected)

        # Diferencia de fase
        phase_diff = (2 * np.pi * extra_path) / (self.SPEED_OF_LIGHT / self._frecuencia)

        # Interferencia (suma de campos)
        field_direct = 1.0
        field_reflected = amplitude_reflected * np.exp(1j * phase_diff)
        total_field = field_direct + field_reflected
        power_factor = float(np.abs(total_field) ** 2)

        # Potencia final interferida
        potencia_interferida = metrics_vacuum['potencia_recibida_w'] * power_factor

        # Resultado final
        metrics = metrics_vacuum.copy()
        metrics.update({
            'distancia_reflejada_m': d_reflected,
            'potencia_recibida_w': potencia_interferida,
            'factor_interferencia': power_factor,
            'objeto_interferente': obj,
            'tipo_propagacion': 'interference_reflection'
        })

        return metrics