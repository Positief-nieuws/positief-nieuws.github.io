# Nieuwstipformulier

Het formulier gebruikt een native POST naar FormSubmit.co, met standaard reCAPTCHA en honeypot. Geen mailto, geen nieuwe Kit-inschrijving. Analytics registreert uitsluitend de verzendpoging, geen veldwaarden.

## Voor livegang
- Controleer de voorwaarden, verwerkersafspraken en privacyinformatie van de externe formulierdienst (https://formsubmit.co/privacy.pdf); FormSubmit bewaart inzendingen volgens de documentatie 30 dagen. Gebruik geen echte persoonsgegevens voor tests.
- Activeer het ontvangstadres redactie@positief-nieuws.nl eenmalig via de activatiemail die FormSubmit bij de eerste testinzending verstuurt. Test op een goedgekeurde preview via HTTPS; geen echte bezoeker als eerste test gebruiken. Gebruik de bevestigde formulier-ID als die beschikbaar is.
- Verifieer met een tweede synthetische tip de bezorging, de eigen bedankmelding, captcha en foutafhandeling. Controleer desktop en mobiel. Pas zo nodig het privacybeleid aan voordat het formulier publiek wordt aangeboden.
- Zet pas live na geslaagde end-to-endtest en akkoord. Geen nieuwsbrief versturen.
