# src-mappens innhold

src-mappen inneholder alle klasser som utgjør funksjonaliteten i prosjektet. Dette er grunnlaget for at prosjektet skal gi ønsket output. Klasse har egne notebooks i mappen notebooks som kjører klassene for å separere funksjonaliteten fra kjøring og visning av dataene.


## analyseData

analyseData er den faktiske analysen av de innhentede og prosesserte dataene. Der beregnes blant annet gjennomsnitt, median og standardavvik.


## fetchData

I fetchData hentes data fra met.no sitt Frost-API og lagrer det i en JSON-fil under /data/raw. Den henter data for temperatur, nedbør og vindhastighet fra Tromsø og Oslo.


## handleData

handleData håndterer dataene som er hentet i fetchData. Den skriver de om på et mer oversiktlig CSV-format for hver av byene og lagrer det under /data/processed.


## interpolateData

interpolation håndterer interpolering av dataene som er hentet. Den interpolerer manglende verdier i dataene og lagrer de interpolerte dataene i en ny CSV-fil under /data/processed.


## missingData

missingData håndterer manglende verdier i dataene. Den skriver de ufullstendige dataene til to CSV-filer under /data/missing som viser dataene og antall manglende verdier for hver lokasjon.

