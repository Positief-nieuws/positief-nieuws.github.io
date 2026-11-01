# Redactionele controle 2 november 2026

Status: **NIET VOLLEDIG AFGEROND; geen productie-akkoord en geen wijziging aan main.**
De eigenaar gaf expliciet toestemming om de concepteditie na geslaagde controles rechtstreeks live te zetten, zonder verzending van de nieuwsbrief.

## Techniek
- GitHub Actions-run 41360914457 heeft de basistests en de build met 12 artikelpagina's en 12 lokale Pixabay-beelden doorlopen.
- De nieuwe bestandspaden en cacheverwijzingen zijn op de previewbranch gecontroleerd.
- Pixabay-metadata (pagina-URL, foto-ID, maker, tags en afbeeldingspad) zijn vastgelegd in `data/pixabay-images.json`.
- Pixabaybeelden zijn illustratief. Ze tonen niet de betrokken patiënten, opvangcentra of projecten.
- Een op 2 november bijgewerkte `nieuws.json` vereist een nieuwe consistente archiefbuild. De previewworkflow bouwt opnieuw bij updates.

## Inhoud en archief
- Huidige redactionele indeling: 6 Nederland, 6 internationaal, 3 actualiteiten.
- Darmkanker: specifieke dMMR/MSI-patiëntgroep; immuuntherapie vóór operatie; resultaten niet generaliseren.
- Zeehondencentrum: Lauwersoog, vroeger Pieterburen; steun is voorlopig, niet definitieve redding.
- Winterswijk: 83 procent minder contrastvloeistof dankzij gecombineerde maatregelen, geen algemene garantie voor andere watergebieden.
- Meedoenbalies: uitbreiding is een besluit, geen bewezen werkgelegenheidswinst.
- Utrechtse Heuvelrug: nieuwe verbinding aangelegd; natuurgebruik door dieren nog monitoren.
- Erfelijk kankerrisico: minder overgangsklachten; gelijkwaardige preventieve veiligheid nog niet bewezen.
- Egypte: 0,28 procent betreft 15-59-jarigen volgens overheidsrapportage; geen volledige eliminatie.
- Koalapark: besluit goedgekeurd, uitvoering en financiering controversieel.
- Irak: toepassing op deelnemende landbouwbedrijven, niet op heel Irak.
- Negen orang-oetans: eerder artikel van 12 oktober ging over acht andere dieren; onderwerp expliciet als apart nieuwsfeit onderscheiden, maar oorspronkelijke vrijlatingsbron voor definitieve bewijscontrole nogmaals lezen.
- Botswana: routekaart naar landrechten, nog geen restitutie.
- Moedergroepen: toegezegde steun voor continuïteit, niet permanent gegarandeerd.
- NOS-links: gebruik oorspronkelijke korte RSS-links totdat de canonieke URL's daadwerkelijk zijn bevestigd.

## Resterende verplichte controles
1. In de meegestuurde kandidatenpool zijn 8.372 unieke kandidaten en 75 dekkingstaken. Het bronbestand is aangemaakt op **1 november 2026**, niet op editiedag **2 november**. `selection_check.py` eist een bronrun van de editiedag.
2. Alle 8.372 kandidaten moeten inhoudelijk eenmalig getriageerd worden. Dit is niet gebeurd en wordt niet als voltooid aangemerkt.
3. Alle 75 dekkingstaken moeten worden gecontroleerd en gedocumenteerd. Dit is niet gebeurd.
4. Lees ten minste drie reserves per regio en leg selectie- en bewijsafwegingen vast. De eerdere shortlist kent reserves, maar geen compleet formeel beoordelingsrecord.
5. Maak `selectie/2026-11-02-kandidaten.json` en `selectie/2026-11-02.json` met de exacte bronhash, bronchecks en artikelbeoordelingen.
6. Maak `redactie/2026-11-02.json` met bewijs-, dubbelpublicatie- en beeldrechtencontrole, exacte `news_sha256` en expliciet oordeel per bericht.
7. Laat `python selection_check.py --pool selectie/2026-11-02-kandidaten.json --review selectie/2026-11-02.json` en `python editorial_check.py` beide slagen.
8. Pas daarna de definitieve, akkoordbevonden editie via de bestaande live-workflow toe. Een push van `nieuws.json` naar `main` start automatisch `Bewaar editie` en kan daarna een **Buttondown-concept** genereren. Het verstuurt volgens de huidige workflow geen e-mail.

Er is **geen** beroep gedaan op een niet-bestaande uitzonderingsregel, geen controle kunstmatig als voltooid gemarkeerd en geen livepublicatie uitgevoerd.
