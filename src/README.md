# src-mappens innhold

src-mappen inneholder alle klasser og tilhørende notebooks som utgjør funksjonaliteten i prosjektet. Dette er grunnlaget for at prosjektet skal gi ønsket output. Hver klasse har en egen notebook som kjører klassen for å separere funksjonaliteten fra visning av dataene.

## fetchData

I fetchData hentes data fra met.no sitt Frost-API og lagrer det i en JSON-fil under /data/raw. Den henter data for temperatur, nedbør og vindhastighet fra Tromsø og Oslo.


## handleData

handleData inneholder en klasse som håndterer dataene som er hentet i fetchData. Den skriver de om på et mer oversiktlig CSV-format for hver av byene og lagrer det under /data/processed.

## missingData

missingData håndterer manglende verdier i dataene. Den skriver de ufullstendige dateaene til to CSV-filer under /data/missing som viser dataene og antall manglende verdier for hver lokasjon.

## analysis

analysis er den faktiske analysen av de innhentede og prosesserte dataene. Der beregnes gjennomsnitt, median og standardavvik.

## visualization

visualisation håndterer visualisering av dataene som er analysert. Her er forskjellige typer grafer og diagrammer som kan tilpasses interaktivt av brukeren

## prediction

prediction utfører en prediksjon basert på de analyserte dataene. Her er fokuset på å skape nyttig informasjon for brukeren.