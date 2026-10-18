# Eerste controle — 18 oktober 2026

Onderzoek via repository, live GET-verzoeken en ingelogde dashboards. Geen inschrijving, mail of bevestiging uitgevoerd; geen testadres aangewezen. Maandelijkse end-to-endtest: BLOCKED tot gecontroleerd testadres beschikbaar is.

| Datum | Locatie | Controlepunt | Uitkomst | Bewijs |
| --- | --- | --- | --- | --- |
| 2026-10-18 | Homepage home_hero + home_end | HTTP, POST-URL, email en embed=1 | PASS | Live monitorrapport vóór wijziging |
| 2026-10-18 | /nieuwsbrief/ landing_main | HTTP, POST-URL, email en embed=1 | PASS | Live monitorrapport vóór wijziging |
| 2026-10-18 | Beide pagina's | Gedeelde meetcode gekoppeld, events aanwezig | PASS | Live broncontrole |
| 2026-10-18 | Buttondown Embedding | Account-URL positiefnieuws en embed action | PASS | Instellingen gelezen, niet gewijzigd |
| 2026-10-18 | Buttondown Subscribing | Na aanmelden /?inschrijving=bevestigen | PASS | Instelling gelezen |
| 2026-10-18 | Buttondown Subscribing | Na bevestigen /?inschrijving=bevestigd | PASS | Instelling gelezen |
| 2026-10-18 | Website na bevestigen | Toont opnieuw Nog één stap | FAIL → herstel geïmplementeerd | Router verwees naar signup-pending; aparte signup-confirmed-weergave toegevoegd |
| 2026-10-18 | Simple Analytics hele site | newsletter_view / newsletter_cta_click / newsletter_form_submit | PASS voor historische ontvangst | Events Explorer 19 september t/m 18 oktober: 310 / 8 / 6; geen uitsplitsing per formulier bewezen |
| 2026-10-18 | /nieuwsbrief/ | newsletter_landing_view | PASS voor historische ontvangst | Events Explorer zelfde periode: 1 |
| 2026-10-18 | Simple Analytics API | Zonder sleutel toegang tot tellingen | MANUAL | HTTP 400, sleutel vereist |
| 2026-10-18 | Buttondown + mailbox | Double opt-in daadwerkelijk doorlopen en opruimen | BLOCKED | Geen gecontroleerd testadres; account toont bestaande Unactivated en Regular records, maar dat is geen end-to-endbewijs |

Bestaande events en Buttondown-instellingen zijn behouden. De correctie voegt geen bevestigings-event toe: een openbare URL bewijst geen bevestigde abonnee.

## Verificatie na publicatie

Gepubliceerd in commit bb99c580d49c11865c2027c71fb9d2c6b84a533f. GitHub Pages-publicatie #457 geslaagd. De eerste monitorrun vond nog de oude live versie tijdens de publicatie; hertest van run 39118086162 is geslaagd (12 seconden), met rapporten als artifacts. Live controle om 12:09 Amsterdam: alle 23 automatische controlepunten PASS; drie handmatige onderdelen blijven MANUAL. Vijf tests van de controlelogica geslaagd.

Browsercontrole: `/?inschrijving=bevestigen` toont Nog één stap; `/?inschrijving=bevestigd` toont Bedankt voor het bevestigen. Dit test de bestemmingspagina's, niet de echte Buttondown-bevestigingslink. Geen echte inschrijving of mail uitgevoerd.

Resultaten: https://github.com/Positief-nieuws/positief-nieuws.github.io/actions/runs/39118086162
