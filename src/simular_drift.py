import pandas as pd
df = pd.read_csv('datos/nuevo.csv')
df['Quantity'] = df['Quantity'] * 5  # Simulamos compras por volumen
df['UnitPrice'] = df['UnitPrice'] * 0.5  # Simulamos 50% de descuento
df.to_csv('datos/actual.csv', index=False)