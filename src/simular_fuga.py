import pandas as pd
df_oct = pd.read_csv('datos/control.csv')
df_nov = pd.read_csv('datos/nuevo.csv')
pd.concat([df_oct, df_nov]).to_csv('datos/actual.csv', index=False)