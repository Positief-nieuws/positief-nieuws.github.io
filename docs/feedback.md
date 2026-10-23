# Feedback en nieuwstips

Status: voorbereid, NIET geactiveerd of live getest. In feedback.js is formId leeg.
Geen externe Tally-verzoeken of knoppen zolang dat zo is. Deze branch pas mergen
na accountkoppeling, formulierinrichting en onderstaande controles.

## Keuze

Tally Free: onbeperkte inzendingen onder fair use, embeds, verborgen velden,
CSV-export en standaard e-mailmelding. EU-opslag. Geen nieuwe backend of secrets.
Tally-branding blijft zichtbaar. Custom CSS en automatisch verwijderen vereisen
betaald abonnement, dus gebruik gratis kleuren/fonts en handmatig opschonen.
Bestaande mailadressen blijven behouden. Geen wijziging aan Buttondown.

Bronnen gecontroleerd op 23 oktober 2026:
- https://tally.so/help/features
- https://tally.so/help/self-email-notifications
- https://tally.so/help/embed-your-form
- https://developers.tally.so/widgets/events
- https://tally.so/help/gdpr

## Formulier in account van eigenaar inrichten

Titel: Laat van je horen
Intro: Een tip, idee of foutje? Ik hoor het graag.

1. Multiple choice, single answer, verplicht. Vraag: Wat wil je delen?
   - Ik wil feedback geven.
   - Ik heb een positieve nieuwstip.
   - Ik heb een idee of suggestie.
   - Ik heb een foutje gevonden.
2. Long answer, verplicht. Vraag: Je bericht.
   Hint: Bij een nieuwstip helpt een link naar de bron.
   Maximaal 10.000 tekens, minimaal 1. Controleer ook alleen-spaties.
3. Email, optioneel. Vraag: Je e-mailadres (alleen als je een reactie wilt).
4. Hidden field: originPage. Uitsluitend het pad, geen query/fragment.
5. Privacytekst: We gebruiken je bericht alleen om je bijdrage te behandelen
   en eventueel te antwoorden. Je e-mailadres is niet verplicht. Deel geen
   gevoelige persoonsgegevens. We publiceren niets zonder toestemming.
   We verwijderen je bijdrage uiterlijk na twaalf maanden.
   Link: https://positief-nieuws.nl/#privacy
6. Submit-knop: Verstuur je bericht
7. Thank you page: Dank je wel! Met jouw bijdrage maken we Positief Nieuws
   iedere dag een beetje beter.

Kleuren: achtergrond #f7f5ec, tekst #151a17, knop #173f31, accent #d6a13a.
Arial of beschikbare gelijkende sans serif; geen betaalde fonts/CSS nodig.
Geen redirects, partial submissions, advertentiepixels of andere analytics.
Controleer Tally's ingebouwde anti-spammaatregelen. Geen reCAPTCHA toevoegen
zonder noodzaak. De daadwerkelijke spamconfiguratie is nog niet geverifieerd.

Settings: Self email notifications inschakelen. Controleer het ontvangstadres
met de eigenaar en een echte testmelding; geen aanname dat de inbox werkt.
DPA/verwerkersvoorwaarden en subverwerkers in account controleren vóór activatie.

Publiceer formulier, vul alleen publieke form-ID in feedback.js in en verhoog
feedback.js-versie in edition-analytics.js. Geen API-token in repository.

## Beheer

Tally dashboard > formulier > Submissions is het centrale overzicht.
Bekijk type, bericht, email en originPage, filter en exporteer naar CSV.
Standaard meldingen bevatten de ingevulde antwoorden. Behandel de notificatie-
inbox ook als persoonsgegevensopslag. Verwijder maandelijks inzendingen en mails
ouder dan twaalf maanden, ook exports die niet meer nodig zijn. Bewaar geen
publieke exports. Een opslagbeleid in tekst is geen automatische verwijdering.

## Techniek en meting

edition-analytics.js laadt de eigen feedback.js op bestaande en nieuwe pagina's.
Feedback werkt ook bij analyticsuitsluiting. Geen extra externe widgetscripts:
alleen de Tally iframe wordt op verzoek geladen. Native dialog verzorgt modality,
Escape, focus containment en terugkeer naar de opener. CSS reserveert onderaan
ruimte voor de kleine zwevende knop. Mail blijft als terugval beschikbaar.

feedback_open: één per daadwerkelijk geopende dialoog.
feedback_submit: alleen Tally.FormSubmitted van de actieve iframe, origin
https://tally.so, juiste form-ID, met dubbelingsbeveiliging. Het paginapad wordt
bij openen vastgelegd, ook als de homepage ondertussen een andere hash krijgt.
Payload/antwoorden/IDs worden nooit als analyticsmetadata doorgegeven.
feedback_type_select: niet geïmplementeerd. Tally biedt geen gedocumenteerd
veldwijzigingsevent; cross-origin velden zijn niet uitleesbaar. Geen schijnmeting.

Simple Analytics > Events: feedback_open en feedback_submit; vergelijk per
feedback_page / feedback_placement. Ratio submits/opens is een eventratio,
geen unieke-personenconversie. Sluiten en opnieuw openen telt als nieuwe opening.

## Uitgevoerde controles

node --check feedback.js
node tests/test_feedback.js
node tests/test_analytics_policy.js
node tests/test_newsletter_analytics.js
node tests/test_social_sharing.js
python3 -m unittest discover -s tests -p 'test_analytics_policy.py'

Alle geslaagd. Unit-tests simuleren het Tally-bericht, geen bewijs van ontvangst.
Geen productiepageviews, echte Tally-inzendingen of analytics-events aangemaakt.

## Nog uit te voeren voor publicatie

- Lokale visuele controle desktop/mobiel: homepage, artikel, special, contact, tip.
- Formulierconfiguratie, alle categorieën, validatie, zonder e-mail insturen.
- Herkomstpad, daadwerkelijke ontvangst en notificatie, bedanktekst bij succes.
- Netwerkfout mag geen succesvolle bevestiging of submit-event geven.
- Toetsenbord en schermlezer: focus, Escape, iframe navigatie en terugkeer.
- Testinzending verwijderen via normale herstelbare verwijderfunctie.
- Live controle uitsluitend volgens docs/analytics-testing.md.
- Echte analyticsontvangst apart verifiëren met vooraf vastgelegde testbijdrage.
- GitHub Pages deploy controleren en live UI verifiëren na merge.
