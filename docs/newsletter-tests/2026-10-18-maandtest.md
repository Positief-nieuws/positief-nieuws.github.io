# Echte maandtest — 18 oktober 2026

Formulier: homepage, home_hero. Testadres door eigenaar aangewezen en na afloop met diens akkoord uitgeschreven. Double opt-in behouden. Geen automatische inschrijvingen ingericht.

| Datum/tijd Amsterdam | Formulierlocatie | Controlepunt | Uitkomst | Bewijs |
| --- | --- | --- | --- | --- |
| 18-10-2026 vóór 12:13 | / home_hero | Testadres nog niet aanwezig | PASS | Volledige Buttondown-lijst, 41 records, testadres afwezig |
| 18-10-2026 circa 12:13 | / home_hero | Eenmalige echte formulierinzending | PASS | Native POST via zichtbaar formulier |
| 18-10-2026 circa 12:13 | / home_hero | Redirect na aanmelden | PASS | /?inschrijving=bevestigen, Nog één stap |
| 18-10-2026 circa 12:13 | / home_hero | Vóór bevestigen Unactivated | PASS | Rechtstreeks in Buttondown; signup_source=home_hero, signup_page_path=/ |
| 18-10-2026 12:13 | Testmailbox | Double opt-inmail aangekomen | PASS | Bevestigingsmail zichtbaar in STRATO Webmail, gericht aan aangewezen testadres |
| 18-10-2026 circa 12:20 | Testmailbox | Bevestigingslink werkt | PASS | Eigenaar klikte en meldde bevestigd; Buttondown wijzigde naar Regular |
| 18-10-2026 na 12:20 | /?inschrijving=bevestigd | Bestemming na bevestigen | PASS | Geopende browserpagina geverifieerd: Bedankt voor het bevestigen |
| 18-10-2026 na 12:20 | Buttondown | Geactiveerde abonnee | PASS | Status Regular en activiteit Became a Regular subscriber |
| 18-10-2026 12:20 | Testmailbox | Welkomstmail ontvangen | PASS | Zichtbaar in STRATO Webmail |
| 18-10-2026 na bevestiging | / home_hero | Testadres opruimen | PASS | Na expliciet akkoord Unsubscribe uitgevoerd; eindstatus Unsubscribed, niet meer actief |
| 18-10-2026 hercontrole | Simple Analytics | newsletter_view | WAARGENOMEN TOENAME | Sitetotaal 310 naar 311; geen sluitende individuele toeschrijving |
| 18-10-2026 hercontrole | Simple Analytics | newsletter_cta_click | WAARGENOMEN TOENAME | Sitetotaal 8 naar 9; geen sluitende individuele toeschrijving |
| 18-10-2026 hercontrole | Simple Analytics | newsletter_form_submit van deze proef | ONBEKEND / ONDERZOEK | Sitetotaal bleef 6; ontvangst van deze proef niet bewezen |
| 18-10-2026 | GitHub Actions Secrets | Simple Analytics-sleutel beschikbaar | NEE | Alleen BUTTONDOWN_API_KEY en PIXABAY_API_KEY; geen environment- of organization-secrets beschikbaar |

## Beoordeling

De echte inschrijving, double opt-in, bevestiging, bestemmingspagina's en het opruimen zijn geslaagd. De volledige analyticsketen is nog niet goedgekeurd: een bevestigde abonnee bewijst geen ontvangen formulierinzending-event. Geen bestaande events of Buttondown-instellingen gewijzigd. Er is geen ongecontroleerde testabonnee actief achtergelaten.

Volgende maandtest: november 2026, /nieuwsbrief/ landing_main. Voor het opnieuw gebruiken van hetzelfde uitgeschreven testadres moet opnieuw double opt-in worden doorlopen; zet het nooit handmatig naar Regular. Als Buttondown het bestaande adres niet als nieuwe proef kan behandelen, gebruik dan een door de eigenaar gecontroleerde nieuwe alias.

Open acties: ontvangst van het formulierinzending-event onderzoeken, en een geschikte Simple Analytics-sleutel beschikbaar maken als GitHub-secret SIMPLE_ANALYTICS_API_KEY. Tot die tijd blijft eventontvangst handmatig.
