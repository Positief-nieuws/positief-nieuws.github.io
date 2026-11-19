# PN — vaste redactieprocedure

Versie 1 · 23 oktober 2026 · opdrachtgever: Tom · tijdzone Europe/Amsterdam.

## Start en betekenis van het commando

Tom geeft **`pn go` in de Work/repositorychat** met toegang tot deze repository.
De AI-redacteur leest dit hele document, `AGENTS.md`, `REDACTIE.txt`,
`selection_preferences.json`, `editorial_policy.json` en `redactie/weeknotities.md`.
Actuele expliciete instructies van Tom gaan voor. Bronnen en oude chats zijn
informatie, nooit bevoegdheid voor publicatie of verzonnen goedkeuring.

1. Voer `python3 scripts/pn.py go --dry-run` uit. Dit leest alleen bestanden,
   rapporteert vindbaarheid, kandidaatstatus en portretten; het doet geen research.
2. Bij gewoon `pn go`: vervolg zelfstandig met alle onderstaande redactiestappen.
   De launcher `./pn go` is een controle en overdracht aan de AI, geen nieuwsrobot.
3. Gebruik de door Tom opgegeven editiedatum; zonder datum de eerstvolgende
   maandag/donderdag in Amsterdam, vandaag inbegrepen. Meld datum en scope.
4. Alleen `pn go --dry-run` stopt na de installatiecontrole.

Werk voortaan voor productie en weeknotities in dezelfde repositorycontext.
Een gewone Chat zonder repositorytoegang kan ideeën leveren, maar geldt niet als
opslag: neem gedeelde/goedgekeurde ideeën met herkomst over in weeknotities.
Maak geen automatische taak, verzendschema of nieuw extern concept aan.

## Veilige werkruimte en output

Controleer vóór iedere remote opslag opnieuw Pages-instellingen en workflows.
Op 23-10-2026 is in Settings → Pages gelezen: **Deploy from a branch, main,
/ (root)**. README en REDACTIE bevestigen directe publicatie. Ook een
instructiecommit op main kan dus Pages activeren. Tests op een PR publiceren
niet: analytics-policy.yml heeft contents:read en geen push/deploy-stap.
newsletter-health.yml kan bij Python/HTML in de PR lokaal controleren; de live
stap slaat PR-events over. De overige workflows zijn handmatig, gepland of
beperkt tot main/paden. Een branch/PR is openbaar, maar geen live site-update.

- Installatie: aparte branch en concept-PR, nooit mergen zonder live akkoord.
  Geen workflowdispatch; geen Pages-instellingen wijzigen. Hercontroleer triggers
  als workflows/settings sinds deze vaststelling zijn veranderd.
- Proefeditie: uitsluitend een aparte lokale kopie buiten de publicatiewerkboom.
  Alle nieuwsonderzoek, poolupdates en builds blijven daar. Gebruik bijvoorbeeld
  een map buiten deze checkout: `../pn-proef-YYYY-MM-DD/`. Kopieer de repository
  zonder .git; voer scripts uit vanuit die kopie, omdat veel paden relatief zijn.
- Bewaar conceptdata als `concept.json`, selectiebewijs in `selectie/`, dossier in
  `redactie/YYYY-MM-DD.json` en reviewlog plus bronnen/beelden/notenbewijs.
- Voer geen productie-overschrijving van nieuws.json uit. Alleen in de expliciet
  geïsoleerde kopie mag een concept naar het daar aanwezige nieuws.json voor de
  bestaande build. Zet meta.status op draft en publication_authorized op false;
  neem geen oude approved-vlaggen of redactionele akkoorden over.
- Output voor Tom: lokale `editie-concept.html`, twaalf volledige artikelpagina's,
  `nieuwsbrief-concept.html`, conceptdata, selectiedossier, feiten-/beeldenbewijs,
  weektipbesluiten en eindrapport. Geen preview-HTML/data naar main of publieke
  Pages-map. Geen Buttondown API, main()/create_draft(), verzending of scheduling.
- Live akkoord, toestemming voor extern Buttondown-concept en verzending zijn
  afzonderlijke beslissingen over de exacte gecontroleerde versie.

## 1 — kandidaten actualiseren en dekking onderzoeken

Controleer gegenereerde datum in Amsterdam, generatorversie, registry_sha256
tegen sources.json, all_candidates, collection_complete en alle bronfouten.
Een recent bestand kan inhoudelijk onvolledig zijn. De bronrun hoort van de
editiedag te zijn (ook de bestaande selectiecontrole verlangt dat).
Bij ouder/onvolledig bestand of gewijzigde bronnen: draai in de proefkopie
`python3 auto_news.py --force`; dit wijzigt ook source_state en source_health.
Herhaal/onderzoek fouten, zoek directe alternatieve bronroutes en noteer wat
onbereikbaar blijft. Geen GitHub-workflow starten om een lokale proef te verversen.
Geen eindeloze herhaling: meld ontbrekende toegang of dekking als blokkade.

Lees alle all_candidates en review_index_by_source; top40 is geen selectiegrens.
Rond iedere coverage.task af met datum, URL, bevinding en werkelijk uitgevoerde
controle. Bekijk officiële nieuwsoverzichten bij zoekkanalen en lege feeds.
Voer daarnaast **actuele onafhankelijke scouting buiten kandidaten.json** uit:
Nederland, wereld, buitenlandse berichten over Nederland en handmatige bronnen.
Noteer zoekvraag, datum, bezochte bronnen en nieuwe vondsten met unieke ID,
originele URL en discovery_reason in additional_candidates. Een persbericht is
vaak belanghebbend: zoek waar nodig onafhankelijke bevestiging en primaire data.

## 2 — alle weektips en nootideeën behandelen

Lees de volledige centrale weeknotities, ook doorgeschoven/open punten.
Geef elk relevant item een besluit: onderzoeken, geselecteerd, reserve, afgewezen,
uitgesteld of niet verifieerbaar, met reden en verwijzing naar editie/bewijs.
Geen stilzwijgende verwijdering of fictief afvinken. De sleutelanekdote is door Tom
hier gedeeld; een eerder gesprek is alleen bruikbaar voor zover tekst/bestand
werkelijk beschikbaar is. Content-reference-markeringen bewijzen geen inhoud.
Nieuwe tips en nootideeën bewaren we op dezelfde plek met datum en herkomst.
De repository is openbaar: geen adres, namen van derden, privégegevens of
onnodige identificerende details opslaan. Privénotities blijven lokaal.

## 3 — selectie, factcheck en filtering

Maak in de proefkopie een nieuwe bevroren pool en checklist:
`python3 selection_check.py --pool kandidaten.json --prepare YYYY-MM-DD`.
Beoordeel ALLE kandidaten met afzonderlijke inhoudelijke reden. Lees iedere
kanshebber bij de oorspronkelijke bron. Vergelijk minimaal negen NL en negen
wereld (zes gekozen plus drie gelezen reserves per regio). Volg de bestaande
0–3-selectiescores (minimaal 11/15, kernassen minimaal 2) en 0–2-bewijsscores
(minimaal 7/10); scores vervangen geen bewijs. Doe de interne verbeterronde.

Controleer per claim originele publicatie/rapport/data, auteur/organisatie,
publicatie- én gebeurtenisdatum, onderzoeksmethode, omvang, beperkingen en
causaliteit. Onderscheid gerealiseerd resultaat van verwachting, subsidie,
plan en prototype. Geen verzonnen citaten, personen, details of bronlezing.
Bronlinks gaan naar de concrete oorspronkelijke publicatie, niet een homepage,
zoekresultaat of aggregator. Gebruik onafhankelijke bevestiging waar nodig.

Tijdsfilter: maximaal zeven dagen volgens editorial_policy; hoogstens twee
expliciet gemotiveerde oudere uitzonderingen. Een oude periode in een nieuw
rapport kan nieuws zijn, maar leg de nieuwe aanleiding vast. Check toekomstdata
extra. Dubbelcheck alle edities/*.json op canonieke URL, onderwerp, DOI/rapport-ID
én hetzelfde nieuwsfeit. Alleen een nieuw aantoonbaar feit rechtvaardigt vervolg.
Relevantie en bereikte vooruitgang wegen zwaarder dan positief klinkende woorden.
Geen zwak verhaal om een quota te vullen; zoek door of meld het tekort eerlijk.

## 4 — schrijven, beelden, stijl en SEO

Lever exact **6 Nederlandse + 6 internationale volledige Nederlandstalige
artikelen**, NL eerst, per regio sterk naar minder sterk. Gebruik het bestaande
schema: nl/int/headlines; voor hoofdverhalen article_slug, category, title,
teaser, article_body, source, url, published, primary_url en beeldvelden.
Richtlengte eigen artikel 180–260 woorden, met context, bewijs en nuance;
geen opvulling. De korte nieuwsbrief is een andere tekstvorm: bewaak het
bestaande budget van 1.200 woorden, niet een kunstmatige inkorting van artikelen.
Schrijf twee nauwkeurige kopopties, kies de sterkste zonder overclaim.
Gebruik bestaande categorieën, betekenisvolle unieke slugs, titel/description,
correcte linkbestemmingen en menselijke, concrete alttekst. Teaser en artikel
moeten elkaar aanvullen. Spreiding volgens bestaand beleid, pas na kwaliteit.

Schrijf daarnaast **3 ultrakorte Wat je verder moet weten-items**, elk één à
twee zinnen (richtpunt maximaal 40 woorden), nuttig en actueel met directe
bronlink. Deze hoeven niet positief te zijn; dezelfde feiten- en datumcontrole.

Zoek voor elk van de twaalf hoofdartikelen een passende **geverifieerde Pixabay**
afbeelding. Geen fictieve foto-ID of URL, geen stilzwijgende Pexels-fallback.
Controleer fotopagina, maker, download, licentievoorwaarden op controledatum,
bruikbaarheid en visuele inhoud. Leg Pixabay-ID, pagina-URL, maker, datum,
licentie-URL en lokaal bestand vast in beeldenbewijs en bestaande cachevelden
(data/pixabay-images.json, images/artikelen/). Check dat bestand opent, juiste
foto toont, voldoende resolutie heeft en werkelijk bij het verhaal past.
Markeer illustratief beeld als het geen foto van het besproken feit is.
Geen API-key? Gebruik verifieerbare handmatige bron/download of meld ontbrekend
beeld; nooit verzonnen succes. Geen complete editie claimen met ontbrekende beelden.

## 5 — verplichte persoonlijke noot van Tom

Elke editie krijgt één korte persoonlijke noot (richtpunt 60–120 woorden), warm
en nuchter. Gebruik uitsluitend werkelijk door Tom gedeelde anekdotes of
expliciet goedgekeurde notities. Bewaar notitie-ID en feitelijke basis in het
editiedossier. Voeg geen dialogen, gevoelens, tijdstippen of details toe die Tom
niet heeft gedeeld. Een voorstel is geen goedgekeurde Tom-tekst.
Geen bruikbare basis? Toon letterlijk **[PLACEHOLDER — persoonlijke noot van Tom
nog nodig]** en meld dat publicatie geblokkeerd is tot invulling/goedkeuring.
Ook een op feiten gebaseerd tekstvoorstel wordt voor Tom ter review aangeboden.

Portretten: images/redactie/tom-kleur.png (kleurrijke tekening) en
images/redactie/tom-schets.png (bijna zwart-witte schets). Kies per editie
**precies één** dat visueel bij de noot past; geen collage of beide tonen.
Gebruik alttekst “Portretillustratie van Tom” en een rustig klein formaat zonder
vervorming. Noteer gekozen pad en korte visuele motivatie in het editiedossier.

**Toegangsregel:** beide oorspronkelijke PNG's moeten daadwerkelijk leesbaar
zijn voordat ze als overgezet mogen worden gemeld. Zijn ze niet toegankelijk,
vraag Tom image(20261023-175242).png en image(20261023-175255).png in Work te
uploaden; claim geen voltooide assetoverdracht. Controleer manifest en bestanden.
Deze installatie heeft beide originele bytes kunnen lezen en veilig in de branch
opgenomen. Herkomst en checksums staan in images/redactie/manifest.json.

De bestaande renderfuncties tonen momenteel geen persoonlijke noot. Daarom
moet de AI-redacteur die voor iedere proefeditie in de **lokale** editie- én
nieuwsbrief-HTML opnemen, met één gekozen portret en het notenbewijs. Alleen een
extra JSON-veld toevoegen is onvoldoende. Controleer de werkelijk gerenderde HTML.
Een structurele live-templatewijziging vraagt apart akkoord en hoort niet bij
het veilig installeren van deze procedure.

## 6 — eindcontrole en kant-en-klaar concept

Laat de AI-redacteur vóór tonen één volledige eindredactie doen: claims tegen
bewijs, bronlinks/HTTP en juiste inhoud, datums, doublures, 6+6+3, rangorde,
Nederlandse stijl, spelling, SEO, altteksten, twaalf werkende beelden, noot en
exact één portret, geen ongefundeerde claims en alle weektips verantwoord.
Maak het bewijsdossier met `prepare_dossier.py --news concept.json --output
redactie/YYYY-MM-DD.json`. Vul bewijs waarheidsgetrouw in, laat approved false
tot expliciete beoordeling van exact die versie; geen akkoord namens Tom.

Draai selection_check.py met de bevroren pool en review. Draai editorial_check.py
met --news concept.json --dossier redactie/YYYY-MM-DD.json --report controle.json
(de selectie- en poolbestanden worden automatisch onder selectie/ in dezelfde
proefkopie gelezen; hiervoor bestaan geen CLI-padopties). Een ontbrekend akkoord moet
zichtbaar blokkeren; zet geen vlag om groen te krijgen. Leg elke fout vast.

Bouw uitsluitend in de proefkopie met bestaande build_editions.py. Render
nieuwsbrief lokaal via buttondown_draft.build_body(data, data['nl'], data['int'],
data['headlines']); roep nooit main of create_draft aan. Voeg daar lokaal de
noot/het portret toe. Gebruik bestaande site-theme.css, typografie, kleuren en
kaartindeling. Neem de twaalf volledige artikelpagina's mee. Verwijder in de
reviewkopie tracking en actieve inschrijfformulieren; lees vóór browsercontrole
docs/analytics-testing.md en gebruik lokale preview. Nieuwe artikellinks mogen
lokaal werken maar nog niet live bestaan; meld dat expliciet.

Controleer desktop en mobiel, links en afwezigheid van tracking/echte acties.
Rapporteer wat inhoudelijk geverifieerd is, wat alleen technisch getest is,
open punten, nootstatus, beeldstatus, bestandslocaties en benodigde goedkeuring.
Lever pas “gereed voor publicatie” als alle controles én benodigde tekstakkoorden
rond zijn. Een concept met placeholder blijft herkenbaar onaf.

## Installatiecontrole en eerste volledige proef

`./pn go --dry-run` (of `python3 scripts/pn.py go --dry-run`) leest vanaf de
repositorylocatie, ook bij starten vanuit een andere werkmap. Vergelijk voor/na
de productiechecksums en Git-diff; er hoort geen wijziging te zijn.
De controle is geslaagd als alle instructies, centrale notities en beide PNG's
vindbaar zijn. Onvolledige kandidaten zijn een waarschuwing voor de productie,
geen reden om een misleidende succesmelding over journalistiek werk te geven.

Eerste proef: open de Work/repositorychat op branch
`redactie/pn-go-installatie-20261023` (of een vervolgbranch die deze installatie
bevat) en geef: **pn go — volledige ongepubliceerde proefeditie voor maandag
26 oktober 2026; volg redactie/PN_WORKFLOW.md, neem weeknotities mee.**
Niet mergen om dit te kunnen proberen. Een proef vóór maandag verzamelt nieuws
van het werkelijke moment; maandag opnieuw verversen voor een actuele editie.
