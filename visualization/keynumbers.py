import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Les inn de to csv-filene
df1 = pd.read_csv('../data/processed/vaerdata_oslo.csv')
df2 = pd.read_csv('../data/processed/vaerdata_tromso.csv')

# Konverter verdien til numerisk type dersom nødvendig
df1['value'] = pd.to_numeric(df1['value'], errors='coerce')
df2['value'] = pd.to_numeric(df2['value'], errors='coerce')

# Eksempel: Filtrér ut temperaturdata
temp_df1 = df1[df1['elementId'].str.contains('air_temperature')]
temp_df2 = df2[df2['elementId'].str.contains('air_temperature')]

# Beregn gjennomsnitt, median og standardavvik
mean_temp1 = temp_df1['value'].mean()
median_temp1 = temp_df1['value'].median()
std_temp1 = temp_df1['value'].std()

mean_temp2 = temp_df2['value'].mean()
median_temp2 = temp_df2['value'].median()
std_temp2 = temp_df2['value'].std()

print("Gjennomsnittlig temperatur Oslo:", mean_temp1)
print("Median temperatur Oslo:", median_temp1)
print("Standardavvik Oslo:", std_temp1)

print("Gjennomsnittlig temperatur Tromsø:", mean_temp2)
print("Median temperatur Tromsø:", median_temp2)
print("Standardavvik Tromsø:", std_temp2)

plt.hist(temp_df1['value'], bins=40, edgecolor='black')
plt.hist(temp_df2['value'], bins=40, edgecolor='blue')
plt.title("Histogram over lufttemperatur")
plt.xlabel("Temperatur (degC)")
plt.ylabel("Frekvens")
plt.show()
