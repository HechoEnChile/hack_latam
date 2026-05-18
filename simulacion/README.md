import numpy as np
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gps import gps
    from leo import leo


class wave:
    """
    Representa un pulso electromagnético GNSS emitido por un satélite GPS.
    Incluye propagación en vacío y caso de interferencia por reflexión causada
    por un objeto interpuesto (con propiedades físicas generadas).
    """

    SPEED_OF_LIGHT: float = 299_792_458.0
    BOLTZMANN_K: float = 1.380649e-23
    TEMPERATURA_RUIDO: float = 290.0
    ANCHO_BANDA: float = 20.0e6
    RETARDO_IONO_BASE: float = 5.0

    def __init__(
        self,
        gps: 'gps',
        t_recepcion: int,
        potencia_tx: float = 25.0,
        frecuencia: float = 1.57542e9
    ) -> None:
        self._gps = gps
        self._t_recepcion = t_recepcion
        self._potencia_tx = potencia_tx
        self._frecuencia = frecuencia

    @property
    def gps(self) -> 'gps':
        return self._gps

    @property
    def t_recepcion(self) -> int:
        return self._t_recepcion

    def generateObject(self) -> Dict[str, float]:
        """
        Genera las propiedades físicas de un objeto que causa interferencia por reflexión.
        Retorna un diccionario con:
            - velocidad (m/s)
            - diametro (metros)
            - distancia_hacia_gps (metros)
        """
        return {
            'velocidad': float(np.random.uniform(100, 8000)),           # velocidad orbital típica
            'diametro': float(np.random.uniform(0.5, 15.0)),            # desde pequeño debris hasta satélite grande
            'distancia_hacia_gps': float(np.random.uniform(50, 800))    # distancia al GPS (metros)
        }

    def vacuum_propagation(self, leo: 'leo') -> Dict[str, float]:
        """Propagación en vacío (sin objeto interferente)."""
        pos_gps = np.array(self.gps.posVector(self.gps, self.t_recepcion))
        vel_gps = np.array(self.gps.posVelocity(self.gps, self.t_recepcion))
        pos_leo = np.array(leo.posVector(leo, self.t_recepcion))
        vel_leo = np.array(leo.posVelocity(leo, self.t_recepcion))

        d_vec = pos_leo - pos_gps
        d = float(np.linalg.norm(d_vec))
        if d < 1e-6:
            raise ValueError("Distancia cero entre GPS y LEO")

        unit_vec = d_vec / d

        retardo = d / self.SPEED_OF_LIGHT
        v_rel = vel_leo - vel_gps
        v_radial = float(np.dot(v_rel, unit_vec))
        doppler = - (v_radial / self.SPEED_OF_LIGHT) * self._frecuencia

        densidad_potencia = self._potencia_tx / (4.0 * np.pi * d * d)
        lambda_ = self.SPEED_OF_LIGHT / self._frecuencia
        fspl = (4.0 * np.pi * d / lambda_) ** 2
        potencia_recibida = self._potencia_tx / fspl

        ruido_termico = self.BOLTZMANN_K * self.TEMPERATURA_RUIDO * self.ANCHO_BANDA
        atenuacion_iono = self.RETARDO_IONO_BASE * (1.0 + np.random.normal(0.0, 2.0))

        return {
            'distancia_m': d,
            'potencia_recibida_w': potencia_recibida,
            'retardo_propagacion_s': retardo,
            'desplazamiento_doppler_hz': doppler,
            'densidad_potencia_w_m2': densidad_potencia,
            'ruido_termico_w': ruido_termico,
            'atenuacion_iono_m': atenuacion_iono,
            'tipo_propagacion': 'vacuum'
        }

    def interference_propagation(self, leo: 'leo', obj: Dict[str, float] = None) -> Dict[str, float]:
        """
        Propagación con interferencia por reflexión causada por un objeto.
        Si no se pasa un objeto, se genera automáticamente con generateObject().
        """
        if obj is None:
            obj = self.generateObject()

        # Camino directo
        metrics_vacuum = self.vacuum_propagation(leo)
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
