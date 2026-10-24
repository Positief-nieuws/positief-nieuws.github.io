# Eén lokaal HTML-CONCEPT

In de repository:

```sh
./pn go
```

Vereist Python 3.9+, draaiende Ollama en het reeds beschikbare model
`qwen3.5:4b`. Er worden geen betaalde model-API's aangeroepen. Geen extra
modeldownload, bronrescan, GitHub Actions-run of agentteam nodig.

Het commando gebruikt de lokale `kandidaten.json` (maximaal 96 uur oud).
Werk je vanuit een oude checkout, haal dan eerst de laatste repositoryversie op.
Een te oude kandidatenlijst geeft een duidelijke stop; verzamelen blijft een
aparte taak van de bestaande dagelijkse workflow. Een gedeeltelijke bronrun
mag voor een concept worden gebruikt; de bronfouten staan in `input.json`.

De route filtert recente, niet eerder gelinkte bron-URL's met metadata en neemt
maximaal 80 kandidaten verdeeld over bronnen en bronregio mee in één modelselectie.
Dit is bewust geen volledige beoordeling van alle kandidaten en garandeert
geen optimale selectie. Google-zoekverwijzingen worden alleen voor gekozen verhalen opgelost met de
bestaande lokale bronresolver; een onoplosbare verwijzing is geen bronbewijs. Per regio zijn twee reserves beschikbaar. Alleen de
19 gekozen bronpagina's worden opgehaald, met maximaal acht gelijktijdige
verzoeken en tien seconden wachttijd per verzoek. Het oplossen van een
Google-verwijzing kan extra verzoeken vragen.

Daarna schrijft één lokaal model zes Nederlandse en zes internationale eigen
Nederlandstalige artikelen. Elk artikel moet een letterlijk herleidbaar
kernbewijs en onderbouwde regio hebben. Niet in de bron aangetroffen getallen
worden geweigerd. Dit zijn beperkte consistentiecontroles, geen sluitende
factcheck; de tekst vraagt menselijke eindcontrole. De drie Nederlandse
headlines linken rechtstreeks naar de gelezen externe bron, zonder eigen
artikelpagina.

Het resultaat staat in een nieuwe map `concepten/<run>/`:

- `site/index.html` en twaalf eigen artikelpagina's;
- `concept.json`, met `status: CONCEPT` en `publication_authorized: false`;
- compacte selectie-/bronnotities en `timing.json` met gemeten totale tijd.

Bekijk de nieuwste geslaagde run lokaal, bijvoorbeeld:

```sh
python3 -m http.server 8000 --directory concepten/<run>/site
```

Open `http://localhost:8000`. De bestaande artikel- en editiesjablonen worden
hergebruikt. Voor het concept blijft beeld een lokale merkplaceholder; er is
geen Pixabay-zoekopdracht of beeldbeoordeling op het kritieke pad. De bestaande
Pixabay-verwerking blijft ongewijzigd beschikbaar voor de definitieve editie.

Standaard is het tijdbudget 300 seconden. De deadline telt zowel wandkloktijd
als de monotone looptijd; na systeemonderbreking stopt de route bij de
eerstvolgende controle. De computer moet wakker blijven om werk te doen. Bij een model-/bronfout, onvoldoende
goede verhalen of overschrijding wordt geen compleet HTML-CONCEPT geclaimd.
De run bewaart zijn tussenresultaat en de reden. Een bewuste langere proef kan
met `./pn go --budget 900`; dat is geen resultaat binnen vijf minuten.
`--model qwen3.5:9b` gebruikt het grotere reeds geïnstalleerde model.
Snelheid hangt af van hardware, model, bronbereikbaarheid en kwaliteit van de
kandidaten; vijf minuten is een meetdoel, geen gegarandeerde snelheid.

## Afzonderlijk akkoord en publiceren

Dit commando heeft geen publicatie- of verzendfunctie. Het schrijft nooit naar
live `nieuws.json`, `edities/`, `selectie/` of `redactie/`, pusht niets en roept
Buttondown niet aan. De conceptmap is uitgesloten van Git.

Na expliciete keuze voor de definitieve editie volgen de volledige bestaande
selectie-, bron-, feiten-, rechten-, duplicaat-, beeld- en dossiercontroles
uit REDACTIE.txt. `selection_check.py` en `editorial_check.py` blijven vereist
voor publicatie. Pas na een afzonderlijk menselijk live akkoord mag exact de
gecontroleerde editie naar main. Een nieuwsbrief verzenden blijft een aparte
beslissing. Kopieer een concept of een AI-goedkeuringsvlag nooit rechtstreeks
naar live om een publicatiegate te omzeilen.

De gemeten beperkingen staan in [het proefrapport](fast-concept-proef.md).
