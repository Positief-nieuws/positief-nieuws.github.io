# Positief nieuws: selectie is het kernproduct
## FAST CONCEPT is de standaard voor een nieuw concept
Bij een opdracht voor een nieuw concept: voer `./pn go` uit; zie
`docs/fast-concept.md`. Gebruik de bestaande actuele kandidaten.json, geen
`auto_news.py --force`, volledige kandidaatbeoordeling, agentdiscussies of
bewijsdossiers vóór de HTML-preview. Lees REDACTIE.txt en voorkeuren; bronfeiten,
regio, eigen tekst en noodzakelijke brongegevens blijven nodig. Toon een
onvolledige run nooit als complete editie. Niets publiceren of verzenden.
De onderstaande uitgebreide selectie- en dossierprocedure hoort voortaan bij
expliciete definitieve redactie/publicatie, niet bij het eerste FAST CONCEPT.

Lees vóór iedere editie REDACTIE.txt en selection_preferences.json. De huidige voorkeuren van de opdrachtgever in de chat gaan voor.

1. Gebruik het geüploade `kandidaten.json`. Kies uit `all_candidates` zes Nederlandse en zes internationale verhalen op nieuwswaarde, betrouwbaarheid, actualiteit, variatie en relevantie. Lees de oorspronkelijke bronnen en geef per keuze een korte motivatie.
2. Verwerk vervangingen, eigen tips en volgorde. Behoud goedgekeurde onderdelen en wacht op selectieakkoord.
3. Controleer bronnen, datums, beeldrechten, de beelden en de inhoud vóór je de definitieve preview toont. Bouw de homepage, editiepagina en twaalf artikelpagina’s met de bestaande generator vanuit één editiebestand. Neem drie actualiteiten, de persoonlijke noot en de opgeslagen beeldkeuzes op. Lever een lokaal te openen preview. Bouw bij correcties opnieuw en gebruik de nieuwste preview.
4. Pas na ‘Zet live’ voor die preview: leg het akkoord vast in het dossier, verifieer de lokale publicatiebestanden en publiceer die in één wijziging. Controleer vervolgens de veertien live pagina’s. De nieuwsbrief heeft een eigen proces.

Gebruik voor websitepublicatie `publish_edition.py` volgens REDACTIE.txt. Combineer editie-inhoud nooit met workflow- of scriptwijzigingen. Laat de redactiecontrole meelopen en los normale technische fouten zelfstandig op.

## Analytics bij websitewerkzaamheden
Lees vóór iedere browsercontrole `docs/analytics-testing.md`. Gebruik eerst een lokale preview. Open live pagina’s voor onderhoud uitsluitend met `?pn_internal=1` in de gekozen browser; verifieer de uitsluiting voordat je navigeert. Een nieuwe browser of nieuw profiel moet opnieuw worden uitgesloten. Voer geen echte tracking- of Buttondown-test uit zonder het gecontroleerde protocol.
