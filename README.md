# Prosjektbeskrivelse - TDT4114 Anvendt programmering (2025 VÅR)
Dette prosjektet tar for seg en analyse av værdata fra Oslo og Tromsø fra år 2000 til og med 2024. Hensikter med prosjektet er å lage en appplikasjon som brukes for å se på langsiktige endringer i spesifikke elementer i værmønsteret for de to nevnte byene. Kodens funksjonalitet er skrevet i Python, med flere importerte biblioteker for håndtering av dataene som blir hentet ut.

Dataene som hentes ut er fra meteorologisk institutt som er en offisiell og anerkjent kilde for metorologiske observasjoner i Norge som håndterer Norges historiske værdata. Det er enkelt å hente ut data på JSON-foramt fra deres Frost-API og dataene er av høy kvalitet som et resultat av deres profesjonalitet. For oppgavespesifikk informasjon se noteboks/mappeX.ipynb.

# Hvordan kjøre prosjektet

## Kjør følgende kommandoer for å laste ned avhengigheter
python -m venv venv  # (valgfritt, men anbefalt)

source venv/bin/activate  # (eller "venv\Scripts\activate" på Windows)

pip install -r requirements.txt

## Kjør deretter følgende kode for å hente data fra API
vaerdata.py

## Kjør følgende kode formattere dataene til CSV
readvaerdata.py

## Kjør følgende kode for å se alle poster uten verdier
findmissingdata.py

# Testing

## Hvordan kjøre tester
Kjør hver av test-filene i mappen /tests for å sjekke at hver av filene fungerer som de skal.

Dersom terminal skriver OK tilbake er testen godkjent.

# Utvikling av prosjeketet

## Hente endringer
git pull


## Lage ny branch
git checkout -b "navn-på-branch"

Navn standard eksempel: "feat(change)/Change-description"

## Commit og pushe branch
git add .

git commit -m "beskrivelse av hva du har gjort"

git push

## Gå tilbake til main etter push
git checkout main

## Se alle branches
git branch -a

## Se alle lokale branches
git branch


## Se alle remote branches
git branch -r