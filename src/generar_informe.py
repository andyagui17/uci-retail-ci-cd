"""
Módulo para la generación del reporte de Data Drift y del dashboard estático.

Lee datos/referencia.csv y datos/actual.csv, ejecuta Evidently con DataDriftPreset
exclusivamente sobre Quantity y UnitPrice, guarda public/informe_drift.html y
crea el dashboard principal public/index.html con métricas del lote actual.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import pandas as pd

# Compatibilidad con diferentes versiones de Evidently (clásica y moderna/legacy)
try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset
except ImportError:
    from evidently.legacy.report import Report
    from evidently.legacy.metric_preset import DataDriftPreset


NOMBRES_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}


def obtener_mes_legible(fechas_series: pd.Series) -> str:
    """Extrae el mes y año predominante en formato legible en español."""
    fechas = pd.to_datetime(fechas_series, errors="coerce").dropna()
    if fechas.empty:
        return "Desconocido"
    mes_num = int(fechas.dt.month.mode()[0])
    anio = int(fechas.dt.year.mode()[0])
    nombre_mes = NOMBRES_MESES.get(mes_num, f"Mes {mes_num}")
    return f"{nombre_mes} {anio}"


def generar_reporte_drift(df_ref: pd.DataFrame, df_act: pd.DataFrame, output_path: Path) -> None:
    """
    Genera el reporte HTML de Data Drift usando Evidently,
    comparando EXCLUSIVAMENTE las columnas Quantity y UnitPrice.
    """
    columnas_drift = ["Quantity", "UnitPrice"]
    
    # Filtrado estricto para asegurar exclusividad en la comparación
    ref_sub = df_ref[columnas_drift]
    act_sub = df_act[columnas_drift]

    print("Calculando Data Drift para columnas:", columnas_drift)
    report = Report(metrics=[DataDriftPreset(columns=columnas_drift)])
    report.run(reference_data=ref_sub, current_data=act_sub)
    report.save_html(str(output_path))
    print(f"Reporte de Data Drift guardado en: {output_path}")


def generar_index_html(
    output_path: Path,
    mes_actual: str,
    filas_analizadas: int,
    mediana_quantity: float,
    mediana_unit_price: float,
    autor: str,
    fecha_generacion: str,
    commit_sha: str
) -> None:
    """
    Genera programáticamente un archivo public/index.html estático y profesional
    con las métricas del lote actual y el enlace al reporte de drift.
    """
    commit_corto = commit_sha[:7] if len(commit_sha) >= 7 else commit_sha

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UCI Retail - Monitoreo de Datos y Calidad</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #273549;
            --accent-primary: #3b82f6;
            --accent-hover: #2563eb;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --badge-bg: rgba(59, 130, 246, 0.15);
            --badge-text: #60a5fa;
            --card-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -4px rgba(0, 0, 0, 0.2);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 860px;
            width: 100%;
        }}

        header {{
            text-align: center;
            margin-bottom: 2.5rem;
        }}

        .badge-pipeline {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--badge-bg);
            color: var(--badge-text);
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 1rem;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }}

        .badge-dot {{
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
        }}

        h1 {{
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        header p {{
            color: var(--text-secondary);
            font-size: 1.05rem;
        }}

        .main-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--card-shadow);
            margin-bottom: 2rem;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }}

        .card-header h2 {{
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .metric-box {{
            background: var(--bg-card-hover);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }}

        .metric-label {{
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .metric-value {{
            font-size: 1.65rem;
            font-weight: 800;
            color: var(--text-primary);
        }}

        .action-container {{
            text-align: center;
            padding: 1rem 0;
            border-top: 1px solid var(--border-color);
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1.5rem;
        }}

        .btn-compare {{
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            background: var(--accent-primary);
            color: #ffffff;
            font-weight: 600;
            padding: 0.85rem 1.75rem;
            border-radius: 0.5rem;
            text-decoration: none;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4);
        }}

        .btn-compare:hover {{
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 6px 10px -1px rgba(59, 130, 246, 0.5);
        }}

        .metadata-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.75rem;
            font-size: 0.88rem;
            color: var(--text-secondary);
        }}

        .metadata-item {{
            display: flex;
            gap: 0.4rem;
        }}

        .metadata-item strong {{
            color: #cbd5e1;
        }}

        .commit-tag {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            background: rgba(255, 255, 255, 0.08);
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            color: #e2e8f0;
            font-size: 0.82rem;
        }}

        footer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.82rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="badge-pipeline">
                <span class="badge-dot"></span> Pipeline CI/CD Activo
            </div>
            <h1>Monitoreo de Calidad y Drift</h1>
            <p>Plataforma de validación continua y detección de desviaciones en ventas</p>
        </header>

        <main class="main-card">
            <div class="card-header">
                <h2>Último lote publicado</h2>
                <span class="commit-tag">Commit: {commit_corto}</span>
            </div>

            <div class="metrics-grid">
                <div class="metric-box">
                    <span class="metric-label">Mes Actual</span>
                    <span class="metric-value">{mes_actual}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Filas Analizadas</span>
                    <span class="metric-value">{filas_analizadas:,}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Mediana Quantity</span>
                    <span class="metric-value">{mediana_quantity:g}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Mediana UnitPrice</span>
                    <span class="metric-value">${mediana_unit_price:0.2f}</span>
                </div>
            </div>

            <div class="action-container">
                <a href="informe_drift.html" class="btn-compare">
                    Comparar lote actual con septiembre
                    <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                    </svg>
                </a>
            </div>

            <div class="metadata-list">
                <div class="metadata-item">
                    <strong>Autor:</strong> <span>{autor}</span>
                </div>
                <div class="metadata-item">
                    <strong>Fecha de generación:</strong> <span>{fecha_generacion}</span>
                </div>
                <div class="metadata-item">
                    <strong>Commit de GitHub:</strong> <span class="commit-tag">{commit_sha}</span>
                </div>
            </div>
        </main>

        <footer>
            <p>UCI Retail CI/CD &bull; Generado automáticamente con Evidently y GitHub Pages</p>
        </footer>
    </div>
</body>
</html>
"""
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Dashboard principal estático guardado en: {output_path}")


def main() -> None:
    # Rutas base
    proyecto_raiz = Path(__file__).resolve().parent.parent
    datos_dir = proyecto_raiz / "datos"
    public_dir = proyecto_raiz / "public"

    ref_path = datos_dir / "referencia.csv"
    act_path = datos_dir / "actual.csv"

    if not ref_path.exists():
        raise FileNotFoundError(f"No existe el archivo de referencia en: {ref_path}")
    if not act_path.exists():
        raise FileNotFoundError(f"No existe el archivo actual en: {act_path}")

    # Asegurar creación del directorio public/
    public_dir.mkdir(parents=True, exist_ok=True)
    print(f"Directorio de salida preparado: {public_dir}")

    # 1. Lectura de datasets
    print(f"Leyendo referencia: {ref_path.name}...")
    df_ref = pd.read_csv(ref_path)
    print(f"Leyendo lote actual: {act_path.name}...")
    df_act = pd.read_csv(act_path)

    # 2. Generación del reporte de Data Drift
    informe_drift_path = public_dir / "informe_drift.html"
    generar_reporte_drift(df_ref, df_act, informe_drift_path)

    # 3. Extracción de estadísticas del lote actual
    mes_actual = obtener_mes_legible(df_act["InvoiceDate"])
    filas_analizadas = len(df_act)
    mediana_quantity = float(df_act["Quantity"].median())
    mediana_unit_price = float(df_act["UnitPrice"].median())

    # Metadatos del entorno
    autor = os.getenv("GITHUB_ACTOR", "Equipo de Ingeniería de Datos")
    commit_sha = os.getenv("GITHUB_SHA", "local-dev-placeholder")
    fecha_generacion = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"\nResumen del lote actual:")
    print(f"  - Mes: {mes_actual}")
    print(f"  - Filas: {filas_analizadas:,}")
    print(f"  - Mediana Quantity: {mediana_quantity}")
    print(f"  - Mediana UnitPrice: {mediana_unit_price:.2f}")
    print(f"  - Autor: {autor}")
    print(f"  - Commit: {commit_sha}")
    print(f"  - Fecha: {fecha_generacion}")

    # 4. Generación de index.html
    index_html_path = public_dir / "index.html"
    generar_index_html(
        output_path=index_html_path,
        mes_actual=mes_actual,
        filas_analizadas=filas_analizadas,
        mediana_quantity=mediana_quantity,
        mediana_unit_price=mediana_unit_price,
        autor=autor,
        fecha_generacion=fecha_generacion,
        commit_sha=commit_sha
    )

    print("\nProceso de generación de informe y dashboard finalizado exitosamente.")


if __name__ == "__main__":
    main()
