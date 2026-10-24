# Positief nieuws: selectie is het kernproduct
Lees vóór iedere editie REDACTIE.txt en selection_preferences.json. De huidige voorkeuren van de opdrachtgever in de chat gaan voor.

- Werk eerst aan een nieuwe kandidaten.json met auto_news.py --force. Controleer de complete all_candidates-lijst per bron. De twee top40-lijsten zijn alleen navigatie, nooit de redactionele grens.
- Sluit alle dekkingsvragen af: lees bij zoekkanalen ook het oorspronkelijke nieuwsoverzicht, controleer mislukte/lege bronnen direct en bekijk de handmatige bewijsbronnen. Noteer datum, link en bevinding. Voeg nieuw gevonden verhalen met herkomst toe; onderzoek ook buitenlandse berichten over Nederland.
- Maak vóór het eerste concept een selectiedossier met selection_check.py --prepare YYYY-MM-DD. Beoordeel alle kandidaten; lees de oorspronkelijke bronnen van iedere kanshebber. Vergelijk 6 NL en 6 wereld met ten minste 3 gelezen reserves per regio. Vul de rubriek en de vergelijking eerlijk in. Een vlag bewijst geen broncontrole.
- Maak zelf de interne verbeterronde vóór je een eerste concept toont. Vraag niet aan de eigenaar om vanzelfsprekende ruis, routinecampagnes, prijzen zonder resultaat en herstel van eerdere fouten uit de eerste selectie te halen.
- Vanaf 19 oktober 2026 horen selectie/YYYY-MM-DD.json en de bevroren selectie/YYYY-MM-DD-kandidaten.json bij de editie. selection_check.py moet klaar zijn vóór het eerste concept; editorial_check.py controleert de koppeling aan de definitieve inhoud/volgorde.
- Geen zwak verhaal toevoegen om 6+6 of themaspreiding te vullen. Zoek verder. Kunnen onvoldoende goede verhalen of bronnen worden bevestigd, meld precies wat ontbreekt; nooit volledigheid of kwaliteit veinzen.
- NL eerst, daarna wereld, per groep van sterk naar minder sterk. Inhoudelijke regio gaat voor taal of bronland.
- Eerste concept blijft ongepubliceerd; live akkoord en nieuwsbriefverzending zijn afzonderlijke stappen. Geen wijzigingen aan nieuws.json om een procesproef te laten slagen.

## Analytics bij websitewerkzaamheden
Lees vóór iedere browsercontrole `docs/analytics-testing.md`. Gebruik eerst een lokale preview. Open live pagina’s voor onderhoud uitsluitend met `?pn_internal=1` in de gekozen browser; verifieer de uitsluiting voordat je navigeert. Een nieuwe browser of nieuw profiel moet opnieuw worden uitgesloten. Voer geen echte tracking- of Buttondown-test uit zonder het gecontroleerde protocol.

## Commando pn go
Wanneer Tom `pn go` in deze repositorychat geeft, lees en volg volledig
`redactie/PN_WORKFLOW.md` en `redactie/weeknotities.md`, naast bovenstaande
instructies. Voer eerst `python3 scripts/pn.py go --dry-run` uit en ga daarna
als AI-redacteur verder met de volledige ongepubliceerde proefeditie.
`pn go --dry-run` vraagt uitsluitend de installatiecontrole, geen nieuwsproductie.
De lokale launcher `./pn go` toont de opdracht en controleert vindbaarheid;
hij voert zelf geen autonoom brononderzoek uit. Geen impliciete publicatie.
