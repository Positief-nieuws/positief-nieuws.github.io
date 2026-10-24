# FAST CONCEPT: resultaat proef 24 oktober 2026

**Het vijfminutendoel is niet gehaald. Er is geen nieuwe volledige 6+6+3-editie opgeleverd.**
De route staat op een aparte reviewbranch en is niet naar main samengevoegd.

## Wat is gebouwd

`./pn go` gebruikt bestaande kandidaten van maximaal 96 uur oud, maakt één
begrensde shortlist (maximaal 80 metadata-items), leest uitsluitend 16 gekozen
positieve bronnen plus drie Nederlandse headlines en werkt verhalen uit met
het reeds geïnstalleerde lokale Ollama-model `qwen3.5:4b`. Twee reserves per
regio; geen volledige rescan, duizenden modelbeoordelingen, agentoverleg of
zware bewijsdossiers vóór de preview. Er zijn geen betaalde model-API's gebruikt.

Een geslaagde route rendert exact zes Nederlandse en zes internationale eigen
Nederlandstalige artikelen met eigen pagina en bronknop, plus drie directe
externe headlines, met bestaande sjablonen. Dit is technisch getest met een
synthetische complete invoer, niet bewezen met een nieuwe complete journalistieke
editie. Een lokale merkplaceholder vervangt beeldzoekwerk in de conceptroute.
De bestaande Pixabay-verwerking en volledige publicatiegates zijn ongewijzigd.

## Echte proef: laatste gemeten productieroute

- Start: 24 oktober 2026, 16:45:58,968284 Nederlandse tijd.
- Einde, afgeleid van de opgeslagen timingbestandsdatum: 17:20:53,565468.
- **Werkelijke wandklokspanne: 2.094,597184 seconden = 34 min 54,597 sec.**
- De monotone procesklok rapporteerde 300,003 seconden en een timeout.
- Eén shortlistaanroep: 72,205 seconden volgens die procesklok.
- Zestien van negentien bronpagina's konden worden gelezen; drie bronproblemen.
- Vier schrijf-/beoordelingsaanroepen afgerond, een volgende liep tegen de deadline.
- Tussenresultaat: **1 NL, 0 internationaal, 0 headlines in de conceptdata**.
  De drie headlinebronnen waren wel gelezen, maar de complete editie werd niet afgerond.
- **Geen volledig HTML-CONCEPT en dus geen geslaagde proef binnen vijf minuten.**
- `nieuws.json` bleef byte voor byte gelijk. Niets gepubliceerd of verzonden.

Het verschil tussen de twee klokken is niet verklaard. Systeemonderbreking of
klokaanpassing kan een oorzaak zijn; die oorzaak is niet vastgesteld. De eerdere
meting op alleen `time.monotonic()` was daarom onvoldoende voor een wandklokclaim.
De uiteindelijke code telt beide klokken voor de deadline, bewaart begin/eindtijd
en meldt afzonderlijk `within_five_minutes`. Een gesimuleerde pauze van tien
minuten is getest. **Die laatste klokcorrectie is niet opnieuw end-to-end
gebenchmarkt.** Er wordt geen snellere eindprestatie voor geclaimd.

De lokale modeluitvoer bevatte onjuiste regiokeuzes en afwijzingen, ontbrekend
letterlijk kernbewijs en soms ongegronde motiveringen. Een exacte bronpassage
of een numerieke controle bewijst geen volledige journalistieke juistheid.
De route stopt liever onvolledig dan onbevestigde verhalen bij te verzinnen.
Het kleine model en deze beperkte selectie leveren nog niet betrouwbaar een
complete editie op. Een grotere lokale modeloptie is beschikbaar, maar is in
deze nieuwe route niet als oplossing voor vijf minuten aangetoond.

## Geïnspecteerde vertragingen

De eerdere lokale run `20261023-195444` bevat 54 modelaanroepen. De som van de
opgeslagen fase-tijden is 3.070,16 seconden (51 min 10,16 sec); modelaanroepen
zelf sommeren tot 3.032,02 seconden. Dit is een analyse van bestaande logs,
geen nieuwe stopwatchmeting. Selectie, regiocontrole en schrijven samen:
2.055,97 seconden (34 min 15,97 sec).

De bestaande kandidaatworkflow verzamelt bronnen los van de conceptroute.
Twee recente succesvolle runs hebben een zichtbaar tijdvenster van 101 en
293 seconden tussen `run_started_at` en `updated_at`:
[run 39998513826](https://github.com/Positief-nieuws/positief-nieuws.github.io/actions/runs/39998513826)
en [run 39799622333](https://github.com/Positief-nieuws/positief-nieuws.github.io/actions/runs/39799622333).
Dit zijn workflowvensters, niet alleen de verzameltijd.
Recente site-regressieruns: 15–18 seconden; Pages-runs: 72–91 seconden, gemeten
met dezelfde timestampmethode. Deze bouw-/publicatiestappen worden door `pn go`
niet gestart.

De kandidaatfile van 23 oktober bevat 8.662 ruwe kandidaten, 111 actieve
kanalen en één gemelde feedfout. De bestaande AGENTS.md/REDACTIE.txt eisten een
nieuwe bronrun, volledige triage en dossiers vóór het eerste concept. Die eisen
zijn voor FAST CONCEPT verplaatst naar de expliciete definitieve redactie en
publicatie; `selection_check.py`, `editorial_check.py` en workflows zijn intact.

## Gebruiken en begrenzingen

Op de reviewbranch, met draaiende Ollama en het lokale model:

```sh
./pn go
```

Bij succes staan `concept.json`, `timing.json` en `site/index.html` in een nieuwe
map onder `concepten/`. Bekijk die lokaal:

```sh
python3 -m http.server 8000 --directory concepten/<run>/site
```

Open `http://localhost:8000`. Een foutcode of `complete:false` is geen nieuwe
editie. Met `--budget 900` kan bewust langer worden geprobeerd; dat is geen
vijfminutenresultaat. `--model qwen3.5:9b` kiest het grotere aanwezige model,
zonder snelheidsbelofte. De computer moet wakker blijven.

Na inhoudelijke keuze volgen de bestaande volledige bron-, selectie-, feiten-,
rechten-, beeld- en publicatiecontroles en een afzonderlijk expliciet live akkoord.
Buttondown-verzending blijft apart. `pn go` heeft geen publicatie- of verzendfunctie.

## Validatie

67 tests geslaagd, inclusief bronbewijs/getallen, dubbelingen, deadline na een
klokpauze en volledige HTML-structuur met twaalf eigen pagina's, externe
headline-links en nul netwerkverzoeken bij renderen. Live nieuws, kandidaten,
selectie-/publicatiegates en workflows zijn niet gewijzigd. De ruwe tijden en
hashes staan in `fast-concept-proef.json`; ontwikkelproeven zijn daarin apart
zichtbaar en worden niet als complete edities aangemerkt.
