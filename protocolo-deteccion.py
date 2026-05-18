import pandas as pd import numpy as np from pathlib import Path from datetime import datetime

====================== CONFIGURACIÓN ======================
THRESHOLD_INTERFERENCE = 0.65 # Factor de interferencia fuerte THRESHOLD_POWER_LOSS_DB = 3.0 # Caída de potencia en dB que considera detección CONFIDENCE_THRESHOLD = 0.75 # Umbral de confianza para alerta

print("🚀 DebrisNet - Protocolo de Detección Space Degree") print("=" * 70)

def detect_debris(row): """Función principal de detección (se ejecuta en cada medición).""" vacuum_w = row['power_received_vacuum_w'] interfered_w = row['power_received_interfered_w'] interference_factor = row['interference_factor']

# Cálculo de pérdida de potencia en dB
if interfered_w <= 0:
    power_loss_db = 100.0
else:
    power_loss_db = 10 * np.log10(vacuum_w / interfered_w)

# Detección de debris
is_debris = (
    (interference_factor < THRESHOLD_INTERFERENCE) or 
    (power_loss_db > THRESHOLD_POWER_LOSS_DB)
)

if not is_debris:
    return None  # No hay detección

# Cálculo de confianza
confidence = min(1.0, (THRESHOLD_INTERFERENCE - interference_factor) / 0.4 + 
                 (power_loss_db - THRESHOLD_POWER_LOSS_DB) / 5.0)
confidence = max(0.0, min(1.0, confidence))

if confidence < CONFIDENCE_THRESHOLD:
    return None  # Detección débil → descartada

detection = {
    "timestamp": row['timestamp'],
    "leo_name": row['leo_name'],
    "detected": True,
    "interference_factor": round(interference_factor, 4),
    "power_loss_db": round(power_loss_db, 2),
    "object_diameter_m": round(row['object_diameter_m'], 2),
    "object_velocity_m_s": round(row['object_velocity_m_s'], 2),
    "object_dist_to_gps_m": round(row['object_dist_to_gps_m'], 2),
    "doppler_shift_hz": round(row['doppler_shift_hz'], 2),
    "confidence": round(confidence * 100, 1),
    "alert": "¡ALERTA DE DEBRIS!" if confidence > 0.85 else "Posible debris"
}
return detection
def main(): script_dir = Path(file).parent csv_path = script_dir / "simulation_metrics.csv"

if not csv_path.exists():
    print("❌ No se encontró simulation_metrics.csv")
    print("   Ejecuta primero protocol.py para generar los datos.")
    return

print(f"📂 Cargando datos de simulación: {csv_path.name}")
df = pd.read_csv(csv_path)

detections = []
print(f"🔍 Analizando {len(df):,} mediciones...\n")

for _, row in df.iterrows():
    result = detect_debris(row)
    if result:
        detections.append(result)
        # Mostrar alerta en consola (simula salida en satélite)
        print(f"[{result['timestamp']}] {result['alert']} | "
              f"LEO: {result['leo_name']} | "
              f"Diámetro: {result['object_diameter_m']} m | "
              f"Velocidad: {result['object_velocity_m_s']:.0f} m/s | "
              f"Confianza: {result['confidence']}%")

# Guardar reporte de detecciones
if detections:
    df_detections = pd.DataFrame(detections)
    report_path = script_dir / "detecciones_debris.csv"
    df_detections.to_csv(report_path, index=False)
    
    print(f"\n✅ Detecciones encontradas: {len(detections):,}")
    print(f"   📄 Reporte guardado en: {report_path.name}")
    print(f"   📊 Máximo diámetro detectado: {df_detections['object_diameter_m'].max():.2f} m")
else:
    print("\nℹ️  No se detectaron objetos de debris en esta simulación.")

print("\n🎯 Protocolo Space Degree finalizado. Listo para ejecución en satélite.")
if name == "main": main()