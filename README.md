# Prosjektbeskrivelse - TDT4114 Anvendt programmering (2025 VÅR)

Dette prosjektet tar for seg en analyse av værdata fra Oslo og Tromsø fra år 2000 til og med 2024. Hensikten med prosjektet er å lage en applikasjon som brukes for å se på værmønsteret for de to nevnte byene, og å utvikle en prediksjonsmodell for nedbør for en bestemt dag. Kodens funksjonalitet er skrevet i Python, med flere importerte biblioteker for håndtering av dataene som blir hentet ut av et API.

Dataene som hentes ut er fra meteorologisk institutt som er en offisiell og anerkjent kilde for metorologiske observasjoner i Norge som håndterer Norges historiske værdata. Det er enkelt å hente ut data på JSON-foramt fra deres Frost-API og dataene er av høy kvalitet som et resultat av deres profesjonalitet. For oppgavespesifikk informasjon se mappen notebooks.



# Hvordan kjøre prosjektet i notebooks-mappen

## 1. Kjør følgende kommandoer i terminalen for å laste ned avhengigheter
python -m venv venv  # (valgfritt, men anbefalt)

source venv/bin/activate  # (eller "venv\Scripts\activate" på Windows)

pip install -r requirements.txt


## 2. Hente data fra API

Kjør getvaerdata.ipynb i fetchData-mappen.


## 3. Formattere dataene til CSV

Kjør readvaerdata.ipynb i handleData-mappen.


## 3.1. Se manglende verdier (valgfritt)

Kjør findmissingdata.ipynb i missingData-mappen.


## 3.2. Interpolere dataene (valgfritt)

Kjør interpolation.ipynb i interpolateData-mappen.


## 4. Se statistiske verdier for dataene

Kjør analysis.ipynb i analyseData-mappen.


## 5. Se grafer og figurer av dataene

Kjør alle notebooks i mappen 'visualization'


## 6.  for å forutsi om det blir nedbør i morgen 

Kjør prediction.ipynb i prediction-mappen.



# Testing

## Kjøring av tester

Testene sjekker alle python-filer og er plassert i mappen 'tests'. For å kjøre testene, benytt den innebygde funksjonen til VSCode.


# Utvikling av prosjeketet

## Hente endringer

git pull


## Lage ny branch

git checkout -b "navn-på-branch"
Navn for et standard eksempel: "feat(change)/Change-description"

ELLER

lage branch ut ifra issue i GitHub


## Commit og pushe branch

git add .

git commit -m "beskrivelse av hva du har gjort"

git push


## Gå tilbake til main etter push

git checkout main
