"""Denne koden finner alle manglende værmålinger i Oslo og Tromsø.

Disse skrives til to CSV-filer.
"""

import os
import pandas as pd
from pandasql import sqldf


# Finner stien til mappen der denne filen ligger, for å konstruere filstier
# til CSV-filene
script_dir = os.path.dirname(__file__)

# Definerer filstier til CSV-filene med værdata for Oslo og Tromsø
oslo_csv = os.path.join(script_dir, "vaerdata_oslo.csv")
tromso_csv = os.path.join(script_dir, "vaerdata_tromso.csv")

# Leser inn dataene fra CSV-filene til Pandas DataFrames
df_oslo = pd.read_csv(oslo_csv)
df_tromso = pd.read_csv(tromso_csv)

# Henter dato fra 'referenceTime'-kolonnen for enklere gruppering av dataene
# Bruker de 10 første tegnene, som tilsvarer datoen
df_oslo["date"] = df_oslo["referenceTime"].str[:10]
df_tromso["date"] = df_tromso["referenceTime"].str[:10]

# Identifiserer hvilke (date, timeOffset, elementId)-kombinasjoner som
# mangler i en by, sammenlignet med den andre. Dette gjøres ved å utføre
# en full ytre join på de relevante kolonnene.

# Lager et "slankere" datasett for Oslo ved å kun velge de relevante
# kolonnene, og endre navn på 'value' til 'oslo_value' for klarhet.
df_oslo_small = df_oslo[["date", "timeOffset", "elementId", "value"]].copy()
df_oslo_small.rename(columns={"value": "oslo_value"}, inplace=True)

# Gjør det samme for Tromsø, og endrer 'value' til 'tromso_value'
df_tromso_small = df_tromso[["date", "timeOffset",
                             "elementId", "value"]].copy()
df_tromso_small.rename(columns={"value": "tromso_value"}, inplace=True)

# Utfører en full ytre join på de "smale" DataFrames'ene for å inkludere alle
# kombinasjoner som finnes i én by, men evt mangler i den andre.
merged_measurements = pd.merge(
    df_oslo_small,
    df_tromso_small,
    on=["date", "timeOffset", "elementId"],
    how="outer"
)

# Identifiserer målinger som mangler i Oslo
# Radene har 'oslo_value' som er NULL, mens 'tromso_value' finnes
missing_in_oslo = merged_measurements[
    merged_measurements["oslo_value"].isnull() &
    merged_measurements["tromso_value"].notnull()
].copy()
# Legger til en kolonne for byinformasjon
missing_in_oslo["city"] = "Oslo"

# Identifiser målinger som mangler i Tromsø
# Her er 'tromso_value' NULL, mens 'oslo_value' er finnes.
missing_in_tromso = merged_measurements[
    merged_measurements["tromso_value"].isnull() &
    merged_measurements["oslo_value"].notnull()
].copy()
# Legger til en kolonne for byinformasjon
missing_in_tromso["city"] = "Tromsø"

# Kombinerer manglende målinger fra begge byene til én samlet DataFrame
df_missing = pd.concat(
    [missing_in_oslo, missing_in_tromso],
    ignore_index=True
)

# Definerer filstien for CSV-filen som skal inneholde manglende målinger
missing_in_both_csv = os.path.join(script_dir, "missing_in_both.csv")
# Lagrer den samlede DataFrame til en CSV-fil med UTF-8-koding
df_missing.to_csv(
    missing_in_both_csv, index=False, encoding="utf-8"
)

# Ved hjelp av pandasql (sqldf) utføres en SQL-spørring for å telle
# antall manglende målinger for hver kombinasjon av by (city) og
# værparameter (elementId).
query_missing_grouped = """
SELECT
    city,
    elementId,
    COUNT(*) AS num_missing
FROM df_missing
GROUP BY city, elementId
ORDER BY city, num_missing DESC
"""
missing_grouped = sqldf(query_missing_grouped, locals())

# Definerer filstien for oppsummerings-CSV-filen og lagre resultatet
missing_summary_csv = os.path.join(script_dir, "missing_summary.csv")
missing_grouped.to_csv(
    missing_summary_csv, index=False, encoding="utf-8"
)

# Skriver ut en bekreftelse
print("Ferdig! Følgende CSV-filer er opprettet:")
print(" -", missing_in_both_csv)
print(" -", missing_summary_csv)
