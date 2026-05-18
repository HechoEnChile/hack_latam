import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
class Leo:
    def __init__(self, leofile, times = [], xs = [], ys = [], zs = [], vxs = [], vys = [], vzs = [], nombre = ""):
        self.leofile = leofile
        filename = os.path.basename(leofile)

        name_without_ext = os.path.splitext(filename)[0]

        self.nombre = name_without_ext.replace("Report", "")
        df = pd.read_fwf(leofile,skiprows=1, names=["times", "x", "y", "z", "vx", "vy", "vz"])        
        self.times = df["times"].to_numpy()
        self.xs = df["x"].to_numpy()
        self.ys = df["y"].to_numpy()
        self.zs = df["z"].to_numpy()
        self.vxs = df["vx"].to_numpy()
        self.vys = df["vy"].to_numpy()
        self.vzs = df["vz"].to_numpy()
    
    def speed(self,t):
        return np.sqrt(self.xs[t]**2 + self.ys[t]**2 + self.zs[t]**2)
    
    def posVector(self,t):
        return [self.xs[t], self.ys[t], self.zs[t]]

    def posVelocity(self,t):
        return np.array([self.vxs[t], self.vys[t], self.vzs[t]])
    
    def buildVacummWave(self, metrics: dict,tref: int):
        f_visual = 5000  # Hz

        t = np.linspace(
            float(tref),
            float(tref) + 0.01,     # 10 ms
            10000
        )

        doppler = metrics['desplazamiento_doppler_hz']

        # Escalamos Doppler para visualización
        doppler_visual = doppler * 0.01

        f_rx = f_visual + doppler_visual
        A = np.sqrt(metrics['potencia_recibida_w'])
        A *= 1e5
        tau = metrics['retardo_propagacion_s']
        signal = A * np.cos(
            2 * np.pi * f_rx * (t - tau)
        )
        noise_power = metrics['ruido_termico_w']

        noise = np.random.normal(
            0,
            np.sqrt(noise_power) * 1e5,
            len(t)
        )

        signal += noise
        power_signal = signal**2

        FS, señal = plt.subplots()
        señal.plot(t, signal)

        señal.set_title("Señal RF recibida entre satélites")
        señal.set_xlabel("Tiempo [s]")
        señal.set_ylabel("Amplitud")

        señal.grid(True)

        FP, potencia = plt.subplots()
        potencia.plot(t, power_signal)

        potencia.set_title("Potencia instantánea de la señal recibida")
        potencia.set_xlabel("Tiempo [s]")
        potencia.set_ylabel("Potencia relativa")
        potencia.grid(True)
        
        figures = {"señal": FS, "potencia": FP}
        return figures

    def buildInterferenceWave(self, metrics, tref):
        f_visual = 5000

        # Doppler
        doppler = metrics['desplazamiento_doppler_hz']

        # Escalado visual
        doppler_visual = doppler * 0.01

        f_rx = f_visual + doppler_visual

        t = np.linspace(
            float(tref),
            float(tref) + 0.01,     
            20000
        )
        A_direct = np.sqrt(metrics['potencia_recibida_w'])

        # Escalado visual
        A_direct *= 1e5
        tau_direct = metrics['retardo_propagacion_s']

        # Delay adicional reflejado
        extra_delay = (
            metrics['distancia_reflejada_m']
            - metrics['distancia_m']
        ) / 299792458

        tau_reflected = tau_direct + extra_delay
        power_factor = metrics['factor_interferencia']

        # Aproximamos amplitud reflejada
        A_reflected = A_direct * (
            np.sqrt(power_factor) - 1
        )
        lambda_visual = 299792458 / f_visual

        extra_path = (
            metrics['distancia_reflejada_m']
            - metrics['distancia_m']
        )

        phase_diff = (
            2 * np.pi * extra_path
        ) / lambda_visual

        signal_direct = A_direct * np.cos(
            2 * np.pi * f_rx * (t - tau_direct)
        )
        signal_reflected = A_reflected * np.cos(
            2 * np.pi * f_rx * (t - tau_reflected)
            + phase_diff
        )
        signal_total = signal_direct + signal_reflected
        noise_power = metrics['ruido_termico_w']

        noise = np.random.normal(
            0,
            np.sqrt(noise_power) * 1e5,
            len(t)
        )

        signal_total += noise
        power_signal = signal_total**2

        FS, señal = plt.subplots()
        señal.plot(t, signal_direct, label="Directa")
        señal.plot(t, signal_reflected, label="Reflejada")

        señal.set_title("Componentes de la señal RF")
        señal.set_xlabel("Tiempo [s]")
        señal.set_ylabel("Amplitud")

        señal.legend()
        señal.grid(True)

        FI, inter = plt.subplots()
        inter.plot(t, signal_total)

        inter.set_title("Señal RF con interferencia por reflexión")

        inter.set_xlabel("Tiempo [s]")
        inter.set_ylabel("Amplitud")

        inter.grid(True)


        FP, potencia = plt.subplots()
        potencia.plot(t, power_signal)

        potencia.set_title("Potencia instantánea con interferencia")

        potencia.set_xlabel("Tiempo [s]")
        potencia.set_ylabel("Potencia relativa")

        potencia.grid(True)

        figures = {"señal": FP,"interferencia": FI, "potencia": FP}
        return figures

    def buildCompositeWave(
        self,
        vacuum_metrics,
        interference_metrics,
        tref
    ):

        # =====================================================
        # CONFIGURACIÓN VISUAL
        # =====================================================

        f_visual = 5000

        duration = 0.01

        n_samples = 10000

        # =====================================================
        # FUNCIÓN AUXILIAR
        # =====================================================

        def generate_signal(metrics, interfered=False):

            t = np.linspace(
                0,
                duration,
                n_samples
            )

            doppler = metrics[
                'desplazamiento_doppler_hz'
            ]

            doppler_visual = doppler * 0.01

            f_rx = f_visual + doppler_visual

            A = np.sqrt(
                metrics['potencia_recibida_w']
            )

            A *= 1e5

            tau = metrics[
                'retardo_propagacion_s'
            ]

            signal = A * np.cos(
                2 * np.pi * f_rx * (t - tau)
            )
            if interfered:

                extra_delay = (
                    metrics['distancia_reflejada_m']
                    - metrics['distancia_m']
                ) / 299792458

                tau_reflected = tau + extra_delay

                power_factor = metrics[
                    'factor_interferencia'
                ]

                A_reflected = A * (
                    np.sqrt(power_factor) - 1
                )

                lambda_visual = (
                    299792458 / f_visual
                )

                extra_path = (
                    metrics['distancia_reflejada_m']
                    - metrics['distancia_m']
                )

                phase_diff = (
                    2 * np.pi * extra_path
                ) / lambda_visual

                reflected = A_reflected * np.cos(
                    2 * np.pi * f_rx * (
                        t - tau_reflected
                    ) + phase_diff
                )

                signal += reflected
            noise_power = metrics[
                'ruido_termico_w'
            ]

            noise = np.random.normal(
                0,
                np.sqrt(noise_power) * 1e5,
                len(t)
            )

            signal += noise

            return t, signal

        t1, s1 = generate_signal(
            vacuum_metrics,
            interfered=False
        )

        t2, s2 = generate_signal(
            interference_metrics,
            interfered=True
        )

        t3, s3 = generate_signal(
            vacuum_metrics,
            interfered=False
        )

        t2 += t1[-1]

        t3 += t2[-1]

        t_total = np.concatenate([
            t1,
            t2,
            t3
        ])

        signal_total = np.concatenate([
            s1,
            s2,
            s3
        ])

        power_total = signal_total**2

        FS, ax_signal = plt.subplots(
            figsize=(15,5)
        )

        ax_signal.plot(
            t_total,
            signal_total
        )

        # Región interferida
        ax_signal.axvspan(
            t2[0],
            t2[-1],
            alpha=0.25,
            label="Interferencia debris"
        )

        ax_signal.set_title(
            "Señal RF recibida"
        )

        ax_signal.set_xlabel(
            "Tiempo [s]"
        )

        ax_signal.set_ylabel(
            "Amplitud"
        )

        ax_signal.grid(True)

        ax_signal.legend()

        FP, ax_power = plt.subplots(
            figsize=(15,5)
        )

        ax_power.plot(
            t_total,
            power_total
        )

        ax_power.axvspan(
            t2[0],
            t2[-1],
            alpha=0.25,
            label="Interferencia debris"
        )

        ax_power.set_title(
            "Potencia instantánea RF"
        )

        ax_power.set_xlabel(
            "Tiempo [s]"
        )

        ax_power.set_ylabel(
            "Potencia"
        )

        ax_power.grid(True)

        ax_power.legend()

        figures = {
            "señal": FS,
            "potencia": FP
        }

        return figures


        
