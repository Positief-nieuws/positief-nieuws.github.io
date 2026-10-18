# Periodiek nieuwsbriefprotocol

Eigenaar: Tom. Start: 18 oktober 2026. Double opt-in blijft behouden.

## Wekelijks — automatische controle

GitHub Actions: **Wekelijkse nieuwsbriefcontrole**, dinsdag 07:17 UTC (08:17 wintertijd / 09:17 zomertijd Amsterdam). Ook handmatig te starten en bij wijzigingen aan de monitor. GitHub kan geplande runs vertragen; controleer bij uitblijven van rapporten de Actions-pagina. Op publieke repositories kan GitHub schedules na 60 dagen inactiviteit uitschakelen.

De monitor doet uitsluitend GET-verzoeken. Hij controleert HTTP 200, geen omleiding naar een ander domein, alle drie bestaande formulierplaatsingen (`home_hero`, `home_end`, `landing_main`), exact één formulier per plaatsing, POST naar `https://buttondown.com/api/emails/embed-subscribe/positiefnieuws`, een verplicht actief `type=email name=email`-veld en verborgen `embed=1`. Hij controleert de koppeling en aanwezigheid van de drie bestaande events in de gedeelde meetcode en de bereikbaarheid plus routerbron van de twee redirectdoelen. Dit is broncontrole, geen bewijs dat JavaScript werkt in een echte browser of dat Buttondown-instellingen onveranderd zijn.

Per run staan datum (UTC), locatie, controlepunt, status en toelichting in de Actions Summary en in `results.json` en `report.md` in het artifact `nieuwsbriefcontrole-<run-id>`. Bewaartermijn 90 dagen; download belangrijke incidentrapporten voor langere bewaring. FAIL en WARN maken de run rood. GitHub-notificaties hangen af van je bestaande Actions-notificatievoorkeuren; er is geen apart e-mailkanaal ingesteld. MANUAL betekent ongetest/handmatig, ook als het technische deel groen is. Een groene run is nooit een volledige conversiegoedkeuring.

### Ontvangst Simple Analytics

Zonder `SIMPLE_ANALYTICS_API_KEY` in GitHub Actions Secrets blijft ontvangst **MANUAL**. Er worden geen sleutels aangemaakt en geen account- of privacyinstellingen gewijzigd. Een beheerder kan later een bestaande geschikte sleutel als secret toevoegen. De monitor leest dan de [Stats API](https://docs.simpleanalytics.com/api/stats), per pagina, over de afgelopen zeven volledige dagen (Europe/Amsterdam). Hij slaat alleen tellingen op. Positieve telling = PASS; nul = WARN (ook mogelijk bij weinig verkeer), API-fout = FAIL. Geen kunstmatige inzendingen of verzonnen events.

Controleer zolang dit MANUAL is iedere week [Events](https://dashboard.simpleanalytics.com/events/positief-nieuws.nl), de afgelopen zeven volledige dagen, met `current_page` en `placement` waar beschikbaar. Noteer per formulierlocatie tellingen van `newsletter_view`, `newsletter_cta_click`, `newsletter_form_submit` en ook `newsletter_landing_view` voor de landingspagina. Nul events is aanleiding voor onderzoek, geen bewezen storing. Noteer ontbrekende uitsplitsing als ONBEKEND; gebruik een sitetotaal niet als bewijs voor beide formulieren.

`newsletter_form_submit` betekent **submitted_unconfirmed**: een geldig formulier is verstuurd. Het bewijst geen succesvolle opslag, mailbezorging of bevestiging. Alleen de status in Buttondown bewijst de geactiveerde abonnee. Oudere events zoals `nieuwsbrief_inschrijving` en `newsletter_submit` blijven intact en worden niet opgeteld bij de nieuwe funnel.

## Maandelijks — echte end-to-endtest (eerste werkdag)

Even maanden: homepage; oneven maanden: `/nieuwsbrief/`. Op de homepage wissel je `home_hero` en `home_end` af tussen de homepage-testmaanden. Beide pagina's krijgen zo minstens iedere twee maanden een echte test. Haal een gemiste test zo snel mogelijk in en wijzig de vaste afwisseling niet.

Gebruik een eigen, controleerbare testmailbox of door de eigenaar goedgekeurde alias. Het adres moet nog niet in Buttondown staan. Een plusalias van een bestaand adres is alleen geschikt als ontvangst en acceptatie vooraf zijn vastgesteld. Gebruik nooit adressen van anderen. Bewaar het volledige adres en subscriber-ID uitsluitend in een privétestlog, niet in deze publieke repository. Zonder geschikte mailbox: noteer BLOCKED; geen inschrijving doen.

1. Maak een nieuwe kopie van `MAANDLOG.md`; vul datum/tijd Amsterdam, uitvoerder, pagina, plaatsing en een privé verwijzing naar de testmailbox in. Controleer vooraf dat alleen dit testadres gebruikt wordt en hoe je het na afloop uitschrijft.
2. Lees in Buttondown **Settings → Subscribing** de redirects: na aanmelden `https://positief-nieuws.nl/?inschrijving=bevestigen`, na bevestigen `https://positief-nieuws.nl/?inschrijving=bevestigd`. Behoud double opt-in; zet geen bypass aan. Noteer afwijkingen, wijzig geen instellingen om de test te laten slagen.
3. Open de aangewezen pagina in een normale browser zonder meetblokkade. Noteer formulierweergave en plaatsing in Simple Analytics. Klik en verstuur eenmaal met het testadres; noteer tijdstip, `newsletter_cta_click` en `newsletter_form_submit`, met `signup_status=submitted_unconfirmed`. Analytics kan vertraagd zijn: controleer na enkele minuten, nogmaals na 30 minuten; daarna ONBEKEND/onderzoek.
4. Controleer direct de bestemming `/?inschrijving=bevestigen` met “Nog één stap”. Zoek in Buttondown exact het testadres op: de status moet **Unactivated/onbevestigd** zijn. Leg dat vast vóórdat je bevestigt. Geen onbevestigde status gezien = geen PASS voor deze stap.
5. Controleer inbox en spam op de double opt-inmail. Noteer ontvangsttijd en afzender, geen geheime bevestigingslink in het publieke log. Geen mail binnen 15 minuten: FAIL, onderzoek bezorging; niet herhaald aanmelden.
6. Klik de bevestigingslink eenmaal. Controleer `/?inschrijving=bevestigd`, de passende bedanktekst en vervolgens de status **Regular/geactiveerd** in Buttondown. De openbare bedankpagina op zichzelf bewijst geen abonnee. Noteer ook de welkomstmail indien ontvangen.
7. Ruim in alle gevallen op, ook bij een mislukte test: schrijf uitsluitend het testadres uit via de welkomstmail of Buttondown. Verifieer **Unsubscribed** en dat het niet meer actief is. Indien verwijderen nodig is, doe dat bewust en alleen voor het gecontroleerde testrecord. Noteer tijdstip en eindstatus. Vertrouw niet op algemene automatische subscriber cleanup. Een volgende test gebruikt een nieuw, gecontroleerd adres; importeer/activeer nooit handmatig om double opt-in te omzeilen.
8. Vul elk controlepunt in met PASS, FAIL, ONBEKEND of BLOCKED en bewijsverwijzing. Geen lege vakken. Herhaal bij herstel alleen de relevante controles en leg de hertest apart vast. Onderzoek technische FAIL dezelfde werkdag; noteer oorzaak, herstel en eigenaar.

Er is bewust geen automatische inschrijving, bevestiging of verwijdering: er is geen goedgekeurd testadres met gegarandeerde automatische opruiming ingericht.
