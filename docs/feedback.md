# Feedback en nieuwstips

Live sinds 24 oktober 2026. Formulier: https://tally.so/r/rDj4EL
Integratie gepubliceerd via PR #14. Form-ID rDj4EL is openbaar, geen credential.

## Beheer

Open het formulier in je Tally-dashboard en kies Submissions. Daar staan categorie,
bericht, optioneel e-mailadres en originPage. Je kunt inzendingen naar CSV exporteren.
Publiceer berichten of persoonsgegevens alleen met expliciete toestemming.

Schakel onder Settings de gratis Self email notifications in. De standaardmelding
bevat de ingevulde antwoorden en gaat naar het ingestelde accountadres. De eigenaar
moet de daadwerkelijke ontvangst bevestigen: de beheer- en mailboxsessie zijn niet
beschikbaar voor deze werksessie. Er is geen extra koppeling met Buttondown.

Verwijder iedere maand inzendingen, notificatiemails en niet meer benodigde exports
ouder dan twaalf maanden. Tally Free verwijdert niet automatisch op die termijn.
Verwijderde gegevens kunnen volgens Tally nog maximaal 90 dagen in back-ups blijven.
Verwijderverzoeken: privacy@positief-nieuws.nl. Ook anonieme inzenders kunnen met
voldoende inhoud/datum hun bericht laten terugvinden. De homepageprivacyverklaring
beschrijft doel, gegevens, dienst, bewaartermijn, grondslag en rechten.

## Werking

De kleine knop Feedback of tip? opent een native dialog. Onder artikelen en specials
staat ook Deel je reactie. Contact en Tip hebben een ingang naar hetzelfde formulier;
bestaande mailmogelijkheden blijven beschikbaar. De Tally-iframe laadt alleen na klik.
Geen extern embedscript nodig. Tally-branding blijft staan op het gratis abonnement.
De introductie staat uitsluitend in Tally om dubbele tekst in de pop-up te vermijden.

De herkomst bevat alleen location.pathname, geen queryparameters, fragment of titel.
originPage wordt als hidden field door Tally opgeslagen. Geen persoonsgegevens naar
analytics. Het formulier zelf bevat verplichte categorie en bericht, optionele e-mail.
Geen nieuwsbriefinschrijving, account of registratie voor de inzender.

## Analytics

- feedback_open: eenmaal per daadwerkelijk geopende dialoog.
- feedback_submit: alleen Tally.FormSubmitted van de actieve iframe, origin
  https://tally.so, juiste form-ID en met dubbele-ontvangstbeveiliging.
- feedback_type_select: niet beschikbaar. Er is geen gedocumenteerd Tally-event
  voor veldwijzigingen. Cross-origin formuliervelden zijn niet uitleesbaar.

Metadata: feedback_page en feedback_placement. Antwoorden, e-mailadressen,
respondent-ID en inzendings-ID worden nooit doorgestuurd. Bestaande analyticsuitsluiting
blijft gelden; feedback werkt ook als analytics wordt geblokkeerd.

Simple Analytics > Events: vergelijk feedback_open en feedback_submit, eventueel per
feedback_page/feedback_placement. Submit/open is een eventratio, geen unieke-personen-
conversie. Opnieuw openen telt opnieuw. Ontvangst in het Simple Analytics-dashboard
is nog niet geverifieerd; de beheersessie ontbreekt. Geen onbevestigde ontvangstclaim.

## Verificatie op 24 oktober 2026

Geslaagd:
- Syntax en unit-tests feedback: deduplicatie, origin/source/form-ID checks,
  focusherstel, uitsluiting en geen persoonsgegevens in analyticsmetadata.
- Analyticsbeleid, nieuwsbriefanalytics, social sharing en Python analyticsbeleid.
- Alle 135 inhoudspagina’s laden het gedeelde script; toekomstige pagina’s gebruiken
  hetzelfde laadpunt. Buttondown-formulieren op vijf representatieve pagina’s zijn
  bytegelijk aan de voorafgaande versie.
- GitHub build/regressiecontrole, nieuwsbriefcontrole en Pages deployment geslaagd.
- Publiek Tally-formulier: alle vier categorieën selecteerbaar; lege inzending geeft
  twee validatiefouten en geen bedanktekst. Slechts één categorie tegelijk geselecteerd.
- Live homepage: pop-up opent; Escape sluit; focus keert terug naar de knop.
- Eén echte inzending zonder e-mailadres: Tally toont Formulier verzonden en de
  opgegeven bedanktekst. Bericht begint met TEST PN 24 oktober 2026. Herkomst /.
- Contact, Tip, artikel kwelders-beschermen-kust en special waarom-nieuws-zo-negatief-lijkt:
  juiste knop/uitnodiging, één uitnodiging, juiste herkomst in iframe-URL.
- Werkbrowser overal data-pn-analytics=internal; geen Simple Analytics CDN-script.
  Geen productie-feedbackevents bewust aangemaakt tijdens deze controles.
- Desktop pop-up visueel gecontroleerd. Tally past de iframe aan een smalle breedte aan.

Nog te bevestigen:
- Tom: testbericht in Submissions, herkomst /, e-mailmelding en testbericht verwijderen.
- Full-page mobiele viewport en echte schermlezertest zijn niet uitgevoerd.
- Spaminstellingen en accountvoorwaarden/DPA zijn niet in het account gecontroleerd.
- Echte ontvangst van analytics-events in Simple Analytics. Volg hiervoor
  docs/analytics-testing.md; niet blind herhaaldelijk productie-events versturen.

De lokale HTTP-preview is vanuit de cloudbrowser niet bereikbaar (andere host).
Daarom zijn de visuele/bedieningstests na publicatie uitgevoerd met analyticsuitsluiting.

Bronnen voor de gekozen Tally-functionaliteit:
- https://tally.so/help/features
- https://tally.so/help/self-email-notifications
- https://tally.so/help/embed-your-form
- https://developers.tally.so/widgets/events
- https://tally.so/help/gdpr
