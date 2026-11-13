"""
Suite de pruebas unitarias para el módulo validador.py.

Valida mediante pytest y DataFrames en memoria (sin persistir archivos físicos)
los diferentes escenarios requeridos para asegurar el control de calidad (QA).
"""

import pandas as pd
import pytest
from src.validador import validar_dataframe, validar_datos


@pytest.fixture
def dataframe_valido_base() -> pd.DataFrame:
    """Fixture que provee un DataFrame válido representativo para pruebas."""
    return pd.DataFrame({
        "InvoiceNo": ["565080", "565082"],
        "StockCode": ["20677", "15060B"],
        "Description": ["PINK POLKADOT BOWL", "FAIRY CAKE DESIGN UMBRELLA"],
        "InvoiceDate": ["2011-09-01 08:25:00", "2011-09-01 09:15:00"],
        "Quantity": [8, 4],
        "UnitPrice": [1.25, 3.75],
        "lote": ["referencia", "referencia"]
    })


def test_prueba_1_archivo_valido(dataframe_valido_base: pd.DataFrame):
    """
    Prueba 1: Archivo válido.
    Debe pasar satisfactoriamente y retornar True.
    """
    resultado = validar_dataframe(dataframe_valido_base, nombre_archivo="referencia.csv")
    assert resultado is True


def test_prueba_2_encabezado_faltante(dataframe_valido_base: pd.DataFrame):
    """
    Prueba 2: Encabezado faltante o incompleto.
    Debe fallar con ValueError indicando la fila 0 (encabezado) y la columna afectada.
    """
    # Se elimina una columna requerida (UnitPrice)
    df_incompleto = dataframe_valido_base.drop(columns=["UnitPrice"])

    with pytest.raises(ValueError) as exc_info:
        validar_dataframe(df_incompleto, nombre_archivo="referencia.csv")

    mensaje = str(exc_info.value)
    assert "fila 0" in mensaje.lower()
    assert "unitprice" in mensaje.lower()


def test_prueba_3_fecha_imposible(dataframe_valido_base: pd.DataFrame):
    """
    Prueba 3: Fecha imposible en el calendario (ej. 2011-11-31).
    Debe fallar con ValueError indicando la columna InvoiceDate y la fila correspondiente.
    """
    df_fecha_invalida = dataframe_valido_base.copy()
    # Noviembre solo tiene 30 días: 2011-11-31 no existe
    df_fecha_invalida.loc[0, "InvoiceDate"] = "2011-11-31 10:00:00"

    with pytest.raises(ValueError) as exc_info:
        validar_dataframe(df_fecha_invalida, nombre_archivo="datos.csv")

    mensaje = str(exc_info.value)
    assert "InvoiceDate" in mensaje
    assert "2011-11-31" in mensaje
    assert "fila 0" in mensaje


@pytest.mark.parametrize("cantidad_invalida", [0, -1, -25])
def test_prueba_4_cantidad_no_valida(dataframe_valido_base: pd.DataFrame, cantidad_invalida: int):
    """
    Prueba 4: Cantidad no válida (cero o número negativo).
    Debe fallar con ValueError detallando la columna Quantity y la fila infractora.
    """
    df_cantidad_mala = dataframe_valido_base.copy()
    df_cantidad_mala.loc[1, "Quantity"] = cantidad_invalida

    with pytest.raises(ValueError) as exc_info:
        validar_dataframe(df_cantidad_mala, nombre_archivo="datos.csv")

    mensaje = str(exc_info.value)
    assert "quantity" in mensaje.lower()
    assert "fila 1" in mensaje
    assert "mayor a 0" in mensaje.lower()


def test_prueba_5_precio_negativo(dataframe_valido_base: pd.DataFrame):
    """
    Prueba 5: Precio unitario negativo.
    Debe fallar con ValueError detallando la columna UnitPrice y la fila infractora.
    """
    df_precio_malo = dataframe_valido_base.copy()
    df_precio_malo.loc[0, "UnitPrice"] = -4.50

    with pytest.raises(ValueError) as exc_info:
        validar_dataframe(df_precio_malo, nombre_archivo="datos.csv")

    mensaje = str(exc_info.value)
    assert "unitprice" in mensaje.lower()
    assert "fila 0" in mensaje
    assert "-4.5" in mensaje


def test_prueba_6_factura_repetida():
    """
    Prueba 6: Factura repetida (InvoiceNo duplicado).
    En transacciones de retail, una misma factura contiene múltiples productos,
    por lo que InvoiceNo repetido es un escenario normal y debe ser aceptado.
    """
    df_factura_duplicada = pd.DataFrame({
        "InvoiceNo": ["565080", "565080", "565080"],  # Mismo número de factura
        "StockCode": ["20677", "15060B", "23245"],
        "Description": ["BOWL", "UMBRELLA", "CAKE TINS"],
        "InvoiceDate": ["2011-09-01 08:25:00", "2011-09-01 08:25:00", "2011-09-01 08:25:00"],
        "Quantity": [8, 4, 2],
        "UnitPrice": [1.25, 3.75, 4.95],
        "lote": ["referencia", "referencia", "referencia"]
    })

    resultado = validar_dataframe(df_factura_duplicada, nombre_archivo="referencia.csv")
    assert resultado is True


# Pruebas complementarias de robustez QA
def test_nulos_en_campos_criticos(dataframe_valido_base: pd.DataFrame):
    """Verifica que se detecten nulos en InvoiceNo, StockCode o Description."""
    df_con_nulo = dataframe_valido_base.copy()
    df_con_nulo.loc[0, "Description"] = None

    with pytest.raises(ValueError) as exc_info:
        validar_dataframe(df_con_nulo)

    assert "description" in str(exc_info.value).lower()
    assert "fila 0" in str(exc_info.value)


def test_dataset_vacio():
    """Verifica el rechazo de DataFrames sin filas."""
    df_vacio = pd.DataFrame(columns=[
        "InvoiceNo", "StockCode", "Description", "InvoiceDate", "Quantity", "UnitPrice", "lote"
    ])

    with pytest.raises(ValueError) as exc_info:
        validar_dataframe(df_vacio)

    assert "0 filas" in str(exc_info.value)


def test_reglas_archivo_actual_valido_e_invalido():
    """Verifica que actual.csv acepte control (octubre) o nuevo (noviembre), pero no lotes mezclados."""
    # Caso válido: actual.csv con lote control en Octubre 2011
    df_actual_control = pd.DataFrame({
        "InvoiceNo": ["569204"],
        "StockCode": ["21790"],
        "Description": ["VINTAGE SNAP CARDS"],
        "InvoiceDate": ["2011-10-02 10:43:00"],
        "Quantity": [4],
        "UnitPrice": [0.85],
        "lote": ["control"]
    })
    assert validar_dataframe(df_actual_control, nombre_archivo="actual.csv") is True

    # Caso inválido: actual.csv con lotes mezclados ('control' y 'nuevo')
    df_mezclado = pd.DataFrame({
        "InvoiceNo": ["569204", "574000"],
        "StockCode": ["21790", "21791"],
        "Description": ["ITEM 1", "ITEM 2"],
        "InvoiceDate": ["2011-10-02 10:43:00", "2011-11-02 10:43:00"],
        "Quantity": [4, 2],
        "UnitPrice": [0.85, 1.20],
        "lote": ["control", "nuevo"]
    })
    with pytest.raises(ValueError) as exc_info:
        validar_dataframe(df_mezclado, nombre_archivo="actual.csv")

    assert "lote" in str(exc_info.value).lower()
