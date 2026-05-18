import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from gps import Gps
from leo import Leo
from wave import Wave

def buildSTList(files, data_dir: Path):
    StarLinkList = []
    for file in files:
        full_path = data_dir / file
        StarLinkList.append(Leo(str(full_path)))
    return StarLinkList

def buildGPSList(files, data_dir: Path):
    GPSList = []
    for file in files:
        full_path = data_dir / file
        GPSList.append(Gps(str(full_path)))
    return GPSList

def linkProtocol(leo, gpsList, t):
    minDist = float('inf')
    linkG = None
    for g in gpsList:
        d = np.linalg.norm(np.array(g.posVector(t)) - np.array(leo.posVector(t)))
        if d < minDist:
            minDist = d
            linkG = g
    return linkG

def helloProtocol(gps, leo, t, potencia_tx=25, frecuencia=2.37542e9):
    wave = Wave(gps, t, potencia_tx, frecuencia)
    metricV = wave.VacummProp(leo)
    metricI = wave.interference_propagation(leo)
    return metricV, metricI

def hearProtocol(leo, linkG, t):
    metricV, metricI = helloProtocol(linkG, leo, t)
    figs = leo.buildCompositeWave(metricV, metricI, t)
    return figs, metricV, metricI

def main():
    # ==================== CONFIGURACIÓN ====================
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    output_figuras = script_dir / "Figuras"
    output_figuras.mkdir(exist_ok=True)

    if not data_dir.exists():
        print("❌ Error: La carpeta 'data' no existe.")
        print(f"   Crea la carpeta: {data_dir}")
        print("   y copia dentro todos los ReportSL*.txt y ReportGPS*.txt")
        return

    filesST = [f"ReportSL{i}.txt" for i in range(1, 9)]
    filesGP = [f"ReportGPS{i}.txt" for i in range(1, 5)]

    listST = buildSTList(filesST, data_dir)
    listGPS = buildGPSList(filesGP, data_dir)

    metrics_list = []

    print("🚀 Iniciando simulación...")

    for t in range(len(listST[0].times)):   # ← Cambia a range(0, 20) para pruebas rápidas
        for leo in listST:
            linkG = linkProtocol(leo, listGPS, t)
            figs, metricV, metricI = hearProtocol(leo, linkG, t)

            # Guardar gráficos
            timestamp_str = str(leo.times[t]).replace(":", "-").replace(" ", "_")
            figs["señal"].savefig(output_figuras / f"{leo.nombre}_{timestamp_str}_Señal.png")
            figs["potencia"].savefig(output_figuras / f"{leo.nombre}_{timestamp_str}_Potencia.png")
            plt.close(figs["señal"])
            plt.close(figs["potencia"])

            # Guardar todas las métricas para el CSV
            row = {
                "time_index": t,
                "timestamp": str(leo.times[t]),
                "leo_name": leo.nombre,
                "gps_name": Path(getattr(linkG, "gpsfile", "unknown")).name,
                "distance_m": metricV["distancia_m"],
                "power_received_vacuum_w": metricV["potencia_recibida_w"],
                "propagation_delay_s": metricV["retardo_propagacion_s"],
                "doppler_shift_hz": metricV["desplazamiento_doppler_hz"],
                "power_density_w_m2": metricV["densidad_potencia_w_m2"],
                "thermal_noise_w": metricV["ruido_termico_w"],
                "iono_attenuation_m": metricV["atenuacion_iono_m"],
                "distance_reflected_m": metricI["distancia_reflejada_m"],
                "interference_factor": metricI["factor_interferencia"],
                "power_received_interfered_w": metricI["potencia_recibida_w"],
                "object_diameter_m": metricI["objeto_interferente"]["diametro"],
                "object_velocity_m_s": metricI["objeto_interferente"]["velocidad"],
                "object_dist_to_gps_m": metricI["objeto_interferente"]["distancia_hacia_gps"],
            }
            metrics_list.append(row)

    # ==================== GENERAR CSV ====================
    df_metrics = pd.DataFrame(metrics_list)
    csv_path = script_dir / "simulation_metrics.csv"
    df_metrics.to_csv(csv_path, index=False, encoding="utf-8")

    print(f"✅ Simulación finalizada correctamente.")
    print(f"   • Gráficos → carpeta '{output_figuras.name}'")
    print(f"   • CSV con todos los cálculos → '{csv_path.name}'")
    print(f"   • Total de registros: {len(df_metrics):,}")

if __name__ == "__main__":
    main()