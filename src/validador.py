"""
Módulo de validación de calidad de datos (QA) para ventas de retail.

Asegura la integridad y consistencia de los datos conforme a las reglas de negocio:
- Existencia y orden exacto de las 7 columnas requeridas.
- Conjunto de datos no vacío (al menos 1 fila).
- Ausencia de nulos en InvoiceNo, StockCode y Description.
- Formato estricto YYYY-MM-DD HH:MM:SS y validez de calendario para InvoiceDate.
- Quantity debe ser entero estrictamente mayor a 0.
- UnitPrice debe ser un valor numérico finito estrictamente mayor a 0.
- Reglas específicas para referencia.csv (lote == 'referencia', Septiembre 2011)
  y actual.csv (lote único 'control' o 'nuevo', Octubre o Noviembre 2011).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Union
import numpy as np
import pandas as pd


COLUMNAS_ESPERADAS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "InvoiceDate",
    "Quantity",
    "UnitPrice",
    "lote"
]

REGEX_FECHA_ESTRICTA = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"


def validar_datos(
    origen: Union[str, Path, pd.DataFrame],
    nombre_archivo: Optional[str] = None
) -> bool:
    """
    Valida un conjunto de datos (DataFrame o archivo CSV en disco).

    Args:
        origen: Ruta al archivo CSV (str o Path) o DataFrame de pandas en memoria.
        nombre_archivo: Nombre descriptivo del archivo (usado para reglas específicas
                        y mensajes de error). Si no se indica y origen es una ruta,
                        se toma el nombre del archivo.

    Returns:
        bool: True si el archivo cumple todas las reglas de validación.

    Raises:
        ValueError: Si alguna regla de validación falla, detallando archivo,
                    fila y columna del error.
    """
    if isinstance(origen, (str, Path)):
        ruta = Path(origen)
        if nombre_archivo is None:
            nombre_archivo = ruta.name

        if not ruta.is_file():
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila N/A, columna N/A: "
                f"el archivo no existe o no es accesible en '{ruta}'."
            )

        try:
            df = pd.read_csv(ruta)
        except Exception as exc:
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila N/A, columna N/A: "
                f"no se pudo leer el archivo CSV ({exc})."
            ) from exc
    elif isinstance(origen, pd.DataFrame):
        df = origen
        if nombre_archivo is None:
            nombre_archivo = "datos_en_memoria.csv"
    else:
        raise TypeError("El argumento 'origen' debe ser una ruta (str, Path) o un pd.DataFrame.")

    nombre_base = Path(nombre_archivo).name.lower()

    # 1. Validación de columnas exactas (7 columnas requeridas y su orden)
    columnas_actuales = list(df.columns)
    if columnas_actuales != COLUMNAS_ESPERADAS:
        faltantes = [c for c in COLUMNAS_ESPERADAS if c not in columnas_actuales]
        sobrantes = [c for c in columnas_actuales if c not in COLUMNAS_ESPERADAS]
        col_detalle = (
            f"Faltantes: {faltantes}" if faltantes else f"No esperadas: {sobrantes}"
        )
        col_afectada = faltantes[0] if faltantes else (sobrantes[0] if sobrantes else "columnas")
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila 0 (encabezado), columna '{col_afectada}': "
            f"las columnas no coinciden con las 7 esperadas. {col_detalle}. "
            f"Esperadas: {COLUMNAS_ESPERADAS}. Obtenidas: {columnas_actuales}."
        )

    # 2. Al menos una fila
    if len(df) == 0:
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila 0, columna N/A: "
            f"el archivo no contiene registros (0 filas de datos)."
        )

    # 3. Sin nulos en InvoiceNo, StockCode, Description
    for col_no_null in ["InvoiceNo", "StockCode", "Description"]:
        mascara_nulos = df[col_no_null].isna()
        if mascara_nulos.any():
            fila_error = df.index[mascara_nulos][0]
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna '{col_no_null}': "
                f"se encontró un valor nulo (NaN) no permitido."
            )

    # 4. Formato estricto YYYY-MM-DD HH:MM:SS y fecha real para InvoiceDate
    fechas_str = df["InvoiceDate"].astype(str)
    formato_valido = fechas_str.str.match(REGEX_FECHA_ESTRICTA).fillna(False)
    if not formato_valido.all():
        fila_error = df.index[~formato_valido][0]
        valor_invalido = df.loc[fila_error, "InvoiceDate"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'InvoiceDate': "
            f"el valor '{valor_invalido}' no cumple con el formato estricto 'YYYY-MM-DD HH:MM:SS'."
        )

    fechas_parseadas = pd.to_datetime(fechas_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    fechas_imposibles = fechas_parseadas.isna()
    if fechas_imposibles.any():
        fila_error = df.index[fechas_imposibles][0]
        valor_invalido = df.loc[fila_error, "InvoiceDate"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'InvoiceDate': "
            f"la fecha '{valor_invalido}' es imposible o no existe en el calendario."
        )

    # 5. Quantity entero > 0
    cantidad_numerica = pd.to_numeric(df["Quantity"], errors="coerce")
    if cantidad_numerica.isna().any():
        fila_error = df.index[cantidad_numerica.isna()][0]
        valor_invalido = df.loc[fila_error, "Quantity"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'Quantity': "
            f"el valor '{valor_invalido}' no es numérico."
        )

    # Comprobación de valor entero finito
    es_entero = (cantidad_numerica % 1 == 0) & np.isfinite(cantidad_numerica)
    if not es_entero.all():
        fila_error = df.index[~es_entero][0]
        valor_invalido = df.loc[fila_error, "Quantity"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'Quantity': "
            f"el valor '{valor_invalido}' debe ser un número entero."
        )

    es_mayor_cero = cantidad_numerica > 0
    if not es_mayor_cero.all():
        fila_error = df.index[~es_mayor_cero][0]
        valor_invalido = df.loc[fila_error, "Quantity"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'Quantity': "
            f"el valor '{valor_invalido}' no es mayor a 0 (debe ser un entero positivo)."
        )

    # 6. UnitPrice numérico finito > 0
    precio_numerico = pd.to_numeric(df["UnitPrice"], errors="coerce")
    if precio_numerico.isna().any():
        fila_error = df.index[precio_numerico.isna()][0]
        valor_invalido = df.loc[fila_error, "UnitPrice"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'UnitPrice': "
            f"el valor '{valor_invalido}' no es numérico."
        )

    es_precio_finito = np.isfinite(precio_numerico)
    if not es_precio_finito.all():
        fila_error = df.index[~es_precio_finito][0]
        valor_invalido = df.loc[fila_error, "UnitPrice"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'UnitPrice': "
            f"el valor '{valor_invalido}' debe ser un número finito."
        )

    es_precio_mayor_cero = precio_numerico > 0
    if not es_precio_mayor_cero.all():
        fila_error = df.index[~es_precio_mayor_cero][0]
        valor_invalido = df.loc[fila_error, "UnitPrice"]
        raise ValueError(
            f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'UnitPrice': "
            f"el valor '{valor_invalido}' no es mayor a 0 (debe ser un número positivo)."
        )

    # 7. Reglas específicas por nombre de archivo
    if nombre_base == "referencia.csv":
        # lote debe ser solo 'referencia'
        lote_valido = df["lote"] == "referencia"
        if not lote_valido.all():
            fila_error = df.index[~lote_valido][0]
            valor_invalido = df.loc[fila_error, "lote"]
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'lote': "
                f"el valor '{valor_invalido}' es inválido. En 'referencia.csv' la columna lote solo debe ser 'referencia'."
            )

        # Fechas deben ser de Septiembre 2011 (mes 9, año 2011)
        fechas_sept_2011 = (fechas_parseadas.dt.year == 2011) & (fechas_parseadas.dt.month == 9)
        if not fechas_sept_2011.all():
            fila_error = df.index[~fechas_sept_2011][0]
            valor_invalido = df.loc[fila_error, "InvoiceDate"]
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'InvoiceDate': "
                f"la fecha '{valor_invalido}' no corresponde a Septiembre 2011."
            )

    elif nombre_base == "actual.csv":
        # lote debe tener un único valor ('control' o 'nuevo')
        lotes_unicos = df["lote"].dropna().unique()
        if len(lotes_unicos) != 1:
            fila_error = df.index[0]
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'lote': "
                f"debe tener un solo valor ('control' o 'nuevo'), pero se encontraron varios: {list(lotes_unicos)}."
            )

        valor_lote = lotes_unicos[0]
        if valor_lote not in ["control", "nuevo"]:
            fila_error = df.index[df["lote"] == valor_lote][0]
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'lote': "
                f"el valor '{valor_lote}' no es permitido para 'actual.csv'. Debe ser 'control' o 'nuevo'."
            )

        # Fechas deben corresponder a Octubre 2011 para 'control' o Noviembre 2011 para 'nuevo'
        if valor_lote == "control":
            fechas_esperadas = (fechas_parseadas.dt.year == 2011) & (fechas_parseadas.dt.month == 10)
            mes_esperado = "Octubre 2011"
        else:
            fechas_esperadas = (fechas_parseadas.dt.year == 2011) & (fechas_parseadas.dt.month == 11)
            mes_esperado = "Noviembre 2011"

        if not fechas_esperadas.all():
            fila_error = df.index[~fechas_esperadas][0]
            valor_invalido = df.loc[fila_error, "InvoiceDate"]
            raise ValueError(
                f"Error en archivo '{nombre_archivo}', fila {fila_error}, columna 'InvoiceDate': "
                f"la fecha '{valor_invalido}' no corresponde a {mes_esperado} para el lote '{valor_lote}'."
            )

    print(f"Validación exitosa para '{nombre_archivo}' ({len(df):,} filas analizadas).")
    return True


def validar_csv(ruta_csv: Union[str, Path]) -> bool:
    """
    Función de entrada para validar un archivo CSV según su ruta.

    Args:
        ruta_csv: Ruta absoluta o relativa al archivo CSV.

    Returns:
        bool: True si la validación es satisfactoria.
    """
    return validar_datos(ruta_csv)


def validar_dataframe(df: pd.DataFrame, nombre_archivo: str = "datos.csv") -> bool:
    """
    Función auxiliar para validar DataFrames en memoria.

    Args:
        df: DataFrame de pandas a validar.
        nombre_archivo: Nombre simulado del archivo para aplicar reglas contextuales.

    Returns:
        bool: True si la validación es satisfactoria.
    """
    return validar_datos(df, nombre_archivo=nombre_archivo)


if __name__ == "__main__":
    # Autovalidación de archivos generados en datos/
    proyecto_raiz = Path(__file__).resolve().parent.parent
    datos_dir = proyecto_raiz / "datos"

    archivos_a_validar = ["referencia.csv", "actual.csv"]
    print("Iniciando validación de archivos en carpeta datos/...\n")
    for nombre in archivos_a_validar:
        archivo_path = datos_dir / nombre
        if archivo_path.exists():
            validar_csv(archivo_path)
        else:
            print(f"Aviso: {nombre} no encontrado en {datos_dir}")
