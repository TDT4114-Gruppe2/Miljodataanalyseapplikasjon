# data-mappens innhold

Datamappen inneholder all data som benyttes i prosjektet. Dataene er delt opp i tre mapper.

## raw

Inneholder rådata som er hentet fra met.no sitt Frost-API. Disse dataene er på JSON-format og ikke bearbeidet eller renset. Alle verdier fra alle lokasjoner ligger altså i samme JSON-fil.

## processed

Inneholder bearbeidede data som er klargjort for analysen. Disse dataene tar utgangspunkt i JSON-filen fra raw-mappen, men er skrevet om til CSV. Dataene er renset og inneholder kun de verdiene som er relevante for prosjektet. I tillegg er det lagt til en kolonne for lokasjon. Her er det to filer for hver av byene, imputert og ikke imputert, for om dataene er interpolert eller ikke.

## missing

Inneholder ufullstendige data fra de aktuelle lokasjonene skrevet om til CSV. Dataene baserer deg på CSV-filene i processed-mappen. Her er det to filer, `missing_in_both.csv` som viser manglende verdier fra begge lokasjonene i samme fil og `missing_summary` som viser totalt antall manglende verdier for hver kategori (elementId) for hver lokasjon. I oppsumeringen vises ikke kategorier som ikke har manglende verdier.