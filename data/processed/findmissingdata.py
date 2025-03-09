import os
import pandas as pd
from pandasql import sqldf

# Finn stien til mappen der denne filen ligger, for å konstruere filstier til CSV-filene
script_dir = os.path.dirname(__file__)

# Definer filstier til CSV-filene med værdata for Oslo og Tromsø
oslo_csv = os.path.join(script_dir, "vaerdata_oslo.csv")
tromso_csv = os.path.join(script_dir, "vaerdata_tromso.csv")

# Les inn dataene fra CSV-filene til Pandas DataFrames
df_oslo = pd.read_csv(oslo_csv)
df_tromso = pd.read_csv(tromso_csv)

# Ekstraher datoen (YYYY-MM-DD) fra 'referenceTime'-kolonnen for enklere gruppering av dataene
# Her brukes de 10 første tegnene, som tilsvarer datoen
df_oslo["date"] = df_oslo["referenceTime"].str[:10]
df_tromso["date"] = df_tromso["referenceTime"].str[:10]

# Vi ønsker å identifisere hvilke (date, timeOffset, elementId)-kombinasjoner som mangler i en by,
# sammenlignet med den andre. Dette gjøres ved å utføre en full ytre join på de relevante kolonnene.

# Forbered et "slankere" datasett for Oslo ved å velge kun de relevante kolonnene, 
# og endre navn på 'value' til 'oslo_value' for klarhet.
df_oslo_small = df_oslo[["date", "timeOffset", "elementId", "value"]].copy()
df_oslo_small.rename(columns={"value": "oslo_value"}, inplace=True)

# Gjør det samme for Tromsø, og kall 'value' for 'tromso_value'
df_tromso_small = df_tromso[["date", "timeOffset", "elementId", "value"]].copy()
df_tromso_small.rename(columns={"value": "tromso_value"}, inplace=True)

# Utfør en full ytre join på de to "smale" DataFrames for å inkludere alle kombinasjoner
# som finnes i én by, men eventuelt mangler i den andre.
merged_measurements = pd.merge(
    df_oslo_small,
    df_tromso_small,
    on=["date", "timeOffset", "elementId"],
    how="outer"
)

# Identifiser målinger som mangler i Oslo:
# Disse radene har 'oslo_value' som er NULL, mens 'tromso_value' er tilgjengelig.
missing_in_oslo = merged_measurements[
    merged_measurements["oslo_value"].isnull() &
    merged_measurements["tromso_value"].notnull()
].copy()
# Legg til en kolonne for byinformasjon
missing_in_oslo["city"] = "Oslo"

# Identifiser målinger som mangler i Tromsø:
# Her er 'tromso_value' NULL, mens 'oslo_value' er tilgjengelig.
missing_in_tromso = merged_measurements[
    merged_measurements["tromso_value"].isnull() &
    merged_measurements["oslo_value"].notnull()
].copy()
# Legg til en kolonne for byinformasjon
missing_in_tromso["city"] = "Tromsø"

# Kombiner de manglende målingene fra begge byene til én samlet DataFrame
df_missing = pd.concat([missing_in_oslo, missing_in_tromso], ignore_index=True)

# Definer filstien for CSV-filen som skal inneholde alle manglende målinger
missing_in_both_csv = os.path.join(script_dir, "missing_in_both.csv")
# Lagre den samlede DataFrame til en CSV-fil med UTF-8-koding
df_missing.to_csv(missing_in_both_csv, index=False, encoding="utf-8")

# Ved hjelp av pandasql (sqldf) utfører vi en SQL-spørring for å telle antall manglende
# målinger for hver kombinasjon av by (city) og værparameter (elementId).
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

# Definer filstien for oppsummerings-CSV-filen og lagre resultatet
missing_summary_csv = os.path.join(script_dir, "missing_summary.csv")
missing_grouped.to_csv(missing_summary_csv, index=False, encoding="utf-8")

# Skriver ut en bekreftelse
print("Ferdig! Følgende CSV-filer er opprettet:")
print(" -", missing_in_both_csv)
print(" -", missing_summary_csv)
