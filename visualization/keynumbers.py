import pandas as pd
import numpy as np

# Les inn de to csv-filene
df1 = pd.read_csv('vaerdata_oslo.csv')
df2 = pd.read_csv('vaerdata_tromso.csv')

# Kombiner dataene
df = pd.concat([df1, df2], ignore_index=True)

# Konverter verdien til numerisk type dersom nødvendig
df['value'] = pd.to_numeric(df['value'], errors='coerce')

# Eksempel: Filtrér ut temperaturdata
temp_df = df[df['elementId'].str.contains('air_temperature')]

# Beregn gjennomsnitt, median og standardavvik
mean_temp = temp_df['value'].mean()
median_temp = temp_df['value'].median()
std_temp = temp_df['value'].std()

print("Gjennomsnittlig temperatur:", mean_temp)
print("Median temperatur:", median_temp)
print("Standardavvik:", std_temp)
