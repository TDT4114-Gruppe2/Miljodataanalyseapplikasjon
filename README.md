# Anvendt_Prog
TDT4114 Anvendt programmering (2025 VÅR)

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

## Kjør følgende kommandoer for å laste ned avhengiheter
python -m venv venv  # (valgfritt, men anbefalt)
source venv/bin/activate  # (eller "venv\Scripts\activate" på Windows)
pip install -r requirements.txt
