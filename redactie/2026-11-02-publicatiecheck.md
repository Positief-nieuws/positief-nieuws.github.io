# Publicatiecheck editie 2026-11-02
Datum controle: 2026-11-01 (Europe/Amsterdam)

## Opdracht
Eigenaar heeft gevraagd de previewstap over te slaan en de overeengekomen 6 NL + 6 internationaal + 3 actualiteiten direct live te publiceren. Dit is toestemming voor live publicatie na kwaliteitscontrole, niet voor nieuwsbriefverzending.

## Status
**NIET GEPUBLICEERD.** De hoofdbranch en live site zijn ongemoeid.

## Blokkades vóór wijziging van main
1. De bestaande `editorial_check.py` weigert een editie waarvan de editiedatum in de toekomst ligt. Op het controlemoment was het 2026-11-01 23:54 uur Nederlandse tijd en de editie staat op 2026-11-02.
2. `redactie/2026-11-02.json` ontbreekt, inclusief brondossier en exacte hash van `nieuws.json`. Niet kunstmatig op goedgekeurd zetten zonder controles.
3. `selectie/2026-11-02.json` en de bevroren kandidaatbronrun volgens de verplichte selectiecontrole ontbreken op deze branch.
4. De 12 `image_query: id:...`-verwijzingen zijn voorgestelde Pixabay-ID's. De foto's zijn nog niet als lokale bestanden opgeslagen en rechten/beeldbeschrijvingen zijn niet bij alle 12 gecontroleerd. Een API-key voor Pixabay zit alleen in de workflow, niet in deze chatomgeving.
5. De volledige builder en checks zijn niet uitgevoerd op deze conceptbranch; een push van alleen `nieuws.json` naar main kan daardoor een live-site geven zonder actuele artikelpagina's.
6. Een push van `nieuws.json` naar main start `Bewaar editie`, gevolgd door `Maak Buttondown concept` bij succes. Geen newsletter send uitvoeren; een Buttondown-concept kan wel automatisch ontstaan.

## Uitgangspunt bij afronden
- Behoud de opmaak van de huidige live homepage.
- NL 1 darmkankeronderzoek, 2 zeehondencentrum, 3 Winterswijk, 4 Meedoenbalies, 5 Utrechtse Heuvelrug, 6 overgangsklachten.
- INT 1 Egypte, 2 koalapark, 3 Irak zonpompen, 4 orang-oetans, 5 Botswana San-landrechten, 6 Britse moedergroepen.
- Headlines 1 VS Congresverkiezingen, 2 Gaza, 3 Brazilië.
- Geen nieuwsbrief versturen.
- Controleer beeld-ID's, bronclaims, dubbele artikelen en de drie headline-URLs direct voor publicatie.
