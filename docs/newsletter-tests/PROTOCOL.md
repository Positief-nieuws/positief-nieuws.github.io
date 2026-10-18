# Periodiek nieuwsbriefprotocol

Eigenaar: Tom. Start: 18 oktober 2026. Double opt-in blijft behouden.

## Iedere zes uur en na wijzigingen — automatische controle

GitHub Actions **Nieuwsbriefcontrole** draait om 00:17, 06:17, 12:17 en 18:17 UTC (Amsterdam +1 uur in wintertijd, +2 in zomertijd). Ook lokaal bij pushes naar main en pull requests; na een voltooide GitHub Pages-build wordt de live versie gelezen. Geplande runs kunnen vertragen of door GitHub na langdurige repository-inactiviteit worden uitgeschakeld.

De monitor inventariseert alle HTML-bestanden, echte formulieren en nieuwsbriefverwijzingen. Homepage (2), nieuwsbriefpagina (1), alle artikelpagina's, de acht categorieën en alle specials worden gecontroleerd. Verplichte plaatsingen worden onafhankelijk van de gevonden formulieren bepaald, zodat een verwijderd formulier een fout oplevert. Nieuwe artikelen worden automatisch meegenomen. In `inventory.json` staan pad, bronbestand, plaatsing, endpoint, methode en velden plus aparte regels voor verwijzende knoppen/links.

De controle leest uitsluitend bestanden en publieke GET-responses. Zij controleert HTTP 200, hetzelfde domein na redirects, exacte formulierplaatsing, native POST naar het officiële accountendpoint, één verplicht actief emailveld, verzendknop, embed=1, bronmetadata en afwezigheid van afwijkende redirects of inline afhandeling. Ook formulierankers, gedeelde meetcode, vier bestaande events en beide vervolgpagina's worden gecontroleerd. Het Buttondown-endpoint moet met GET een publiek inschrijfformulier opleveren. Geen automatische POST, mail, activering of verwijdering.

Bij FAIL of WARN wordt de run rood en opent de workflow één GitHub-issue met de titel `[Nieuwsbriefcontrole] Technische storing onderzoeken`. Zolang dat openstaat ontstaan geen duplicaten. Een latere succesvolle live hertest sluit het issue. Een lokale controle sluit een live incident niet. De waarschuwing is zichtbaar bij Issues en Actions; e-mailbezorging hangt af van je bestaande GitHub-notificatievoorkeuren en is niet bewezen. Notificatievoorkeuren worden niet gewijzigd.

Rapporten staan in de Actions Summary en 90 dagen als artifact `nieuwsbriefcontrole-<run-id>` met `local/` en waar uitgevoerd `live/`. MANUAL is uitdrukkelijk ongetest. Een groene technische run bewijst geen succesvolle nieuwe abonnee, mailbezorging of CAPTCHA-verwerking. Storing in Actions of uitgebleven runs detecteert dit systeem zelf niet.

### Ontvangst Simple Analytics

Zonder `SIMPLE_ANALYTICS_API_KEY` in GitHub Actions Secrets blijft ontvangst **MANUAL**. Er worden geen sleutels aangemaakt en geen account- of privacyinstellingen gewijzigd. Een beheerder kan later een bestaande geschikte sleutel als secret toevoegen. De monitor leest dan de [Stats API](https://docs.simpleanalytics.com/api/stats), per pagina, over de afgelopen zeven volledige dagen (Europe/Amsterdam). Hij slaat alleen tellingen op. Positieve telling = PASS; nul = WARN (ook mogelijk bij weinig verkeer), API-fout = FAIL. Geen kunstmatige inzendingen of verzonnen events.

Controleer zolang dit MANUAL is iedere week [Events](https://dashboard.simpleanalytics.com/events/positief-nieuws.nl), de afgelopen zeven volledige dagen, met `current_page` en `placement` waar beschikbaar. Noteer per formulierlocatie tellingen van `newsletter_view`, `newsletter_cta_click`, `newsletter_form_submit` en ook `newsletter_landing_view` voor de landingspagina. Nul events is aanleiding voor onderzoek, geen bewezen storing. Noteer ontbrekende uitsplitsing als ONBEKEND; gebruik een sitetotaal niet als bewijs voor beide formulieren.

`newsletter_form_submit` betekent **submitted_unconfirmed**: een geldig formulier is verstuurd. Het bewijst geen succesvolle opslag, mailbezorging of bevestiging. Alleen de status in Buttondown bewijst de geactiveerde abonnee. Oudere events zoals `nieuwsbrief_inschrijving` en `newsletter_submit` blijven intact en worden niet opgeteld bij de nieuwe funnel.

## Maandelijks — echte end-to-endtest (eerste werkdag)

Test maandelijks één route met een nieuw toegestaan adres; wissel homepage boven/onder, nieuwsbriefpagina, artikel, categorie en special af. Na relevante wijzigingen test je iedere gewijzigde plaatsing afzonderlijk. Voor volledige acceptatie is per formulier een aantoonbare praktijktest nodig; één gedeelde implementatie of één test vervangt dat bewijs niet.

Gebruik een eigen, controleerbare testmailbox of door de eigenaar goedgekeurde alias. Het adres moet nog niet in Buttondown staan. Een plusalias van een bestaand adres is alleen geschikt als ontvangst en acceptatie vooraf zijn vastgesteld. Gebruik nooit adressen van anderen. Bewaar het volledige adres en subscriber-ID uitsluitend in een privétestlog, niet in deze publieke repository. Zonder geschikte mailbox: noteer BLOCKED; geen inschrijving doen.

1. Maak een nieuwe kopie van `MAANDLOG.md`; vul datum/tijd Amsterdam, uitvoerder, pagina, plaatsing en een privé verwijzing naar de testmailbox in. Controleer vooraf dat alleen dit testadres gebruikt wordt en hoe je het na afloop uitschrijft.
2. Lees in Buttondown **Settings → Subscribing** de redirects: na aanmelden `https://positief-nieuws.nl/?inschrijving=bevestigen`, na bevestigen `https://positief-nieuws.nl/?inschrijving=bevestigd`. Behoud double opt-in; zet geen bypass aan. Noteer afwijkingen, wijzig geen instellingen om de test te laten slagen.
3. Open de aangewezen pagina in een normale browser zonder meetblokkade. Noteer formulierweergave en plaatsing in Simple Analytics. Klik en verstuur eenmaal met het testadres; noteer tijdstip, `newsletter_cta_click` en `newsletter_form_submit`, met `signup_status=submitted_unconfirmed`. Analytics kan vertraagd zijn: controleer na enkele minuten, nogmaals na 30 minuten; daarna ONBEKEND/onderzoek.
4. Controleer direct de bestemming `/?inschrijving=bevestigen` met “Nog één stap”. Zoek in Buttondown exact het testadres op: de status moet **Unactivated/onbevestigd** zijn. Leg dat vast vóórdat je bevestigt. Geen onbevestigde status gezien = geen PASS voor deze stap.
5. Controleer inbox en spam op de double opt-inmail. Noteer ontvangsttijd en afzender, geen geheime bevestigingslink in het publieke log. Geen mail binnen 15 minuten: FAIL, onderzoek bezorging; niet herhaald aanmelden.
6. Klik de bevestigingslink eenmaal. Controleer `/?inschrijving=bevestigd`, de passende bedanktekst en vervolgens de status **Regular/geactiveerd** in Buttondown. De openbare bedankpagina op zichzelf bewijst geen abonnee. Noteer ook de welkomstmail indien ontvangen.
7. Ruim uitsluitend expliciet als wegwerp-testrecord aangewezen adressen op: schrijf die uit via de welkomstmail of Buttondown. Behoud bestaande echte abonnees en hun status; bij een bestaand adres bepaalt de eigenaar of opruimen gewenst is. Verifieer **Unsubscribed** en dat het niet meer actief is. Indien verwijderen nodig is, doe dat bewust en alleen voor het gecontroleerde testrecord. Noteer tijdstip en eindstatus. Vertrouw niet op algemene automatische subscriber cleanup. Een volgende test gebruikt een nieuw, gecontroleerd adres; importeer/activeer nooit handmatig om double opt-in te omzeilen.
8. Vul elk controlepunt in met PASS, FAIL, ONBEKEND of BLOCKED en bewijsverwijzing. Geen lege vakken. Herhaal bij herstel alleen de relevante controles en leg de hertest apart vast. Onderzoek technische FAIL dezelfde werkdag; noteer oorzaak, herstel en eigenaar.

Er is bewust geen automatische inschrijving, bevestiging of verwijdering: er is geen goedgekeurd testadres met gegarandeerde automatische opruiming ingericht.

## Bestaande en geïmporteerde adressen

Gebruik de lifecycle-status in Properties (Regular/Unactivated/etc.). Een metadata-veld `status=inactive` uit een import is geen actuele abonnee-status. Een terugkerende abonnee kan het oorspronkelijke ID en de oorspronkelijke inschrijfdatum behouden; zoek dus op adres en alle statussen, niet alleen nieuwste inschrijvingen. Opnieuw aanmelden is geen bewijs van een volledig nieuwe registratie. Verwijder of activeer geen bestaande abonnee om een test te laten slagen.

Bij lege/ongeldige invoer hoort de browser verzending te blokkeren. Bij een netwerkfout hoort de browser/Buttondown een fout te tonen; de site maakt nooit zelf een geslaagde inschrijving op basis van een klik of verzend-event. De openbare vervolgpagina's controleren geen abonnee-status en tellen daarom nooit als conversiebewijs. Herhaald verzenden wordt tijdens dezelfde navigatie geblokkeerd; terugkeren via de browser maakt een bewuste nieuwe poging mogelijk.
