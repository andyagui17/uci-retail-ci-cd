"""
Script para la preparación y particionamiento de datos de ventas.

Lee el archivo CSV maestro en la raíz del proyecto y lo fracciona según
la columna 'lote' en tres conjuntos:
- referencia.csv (lote == 'referencia')
- control.csv (lote == 'control')
- nuevo.csv (lote == 'nuevo')

Además, genera una copia exacta de control.csv denominada actual.csv.
Todos los archivos se exportan en la carpeta datos/.
"""

from pathlib import Path
import shutil
import pandas as pd


def main() -> None:
    # Definición de rutas base relativas a la ubicación del script
    base_dir = Path(__file__).resolve().parent.parent
    master_csv_path = base_dir / "ventas_regalos_2011 (1).csv"
    datos_dir = base_dir / "datos"

    if not master_csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo maestro en: {master_csv_path}")

    # Asegurar la creación del directorio datos/
    datos_dir.mkdir(parents=True, exist_ok=True)
    print(f"Directorio de datos preparado: {datos_dir}")

    # Lectura del archivo maestro con pandas
    print(f"Cargando dataset maestro desde: {master_csv_path.name}...")
    df = pd.read_csv(master_csv_path)
    print(f"Total de registros leídos: {len(df):,}")

    if "lote" not in df.columns:
        raise KeyError("La columna 'lote' no existe en el archivo maestro.")

    # Particiones requeridas
    lotes = ["referencia", "control", "nuevo"]

    for lote in lotes:
        df_lote = df[df["lote"] == lote]
        output_file = datos_dir / f"{lote}.csv"

        df_lote.to_csv(
            output_file,
            index=False,
            sep=",",
            decimal="."
        )
        print(f"Generado '{output_file.name}' con {len(df_lote):,} registros.")

    # Copia exacta de control.csv como actual.csv
    control_file = datos_dir / "control.csv"
    actual_file = datos_dir / "actual.csv"
    shutil.copy2(control_file, actual_file)
    print(f"Copia exacta creada: '{actual_file.name}' a partir de '{control_file.name}'.")

    print("\nProceso de preparación de datos completado exitosamente.")


if __name__ == "__main__":
    main()
