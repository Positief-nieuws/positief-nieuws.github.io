# Nieuwsbriefcontrole

Broncontrole is geen end-to-endtest. Formulierinzending ≠ bevestigde abonnee.

| Datum (UTC) | Locatie | Controlepunt | Status | Toelichting |
| --- | --- | --- | --- | --- |
| 2026-10-18T10:06:35.746957+00:00 | / | pagina laden | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_end | formulier aanwezig (exact één) | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_end | Buttondown action en POST | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_end | emailveld | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_end | embed=1 | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_hero | formulier aanwezig (exact één) | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_hero | Buttondown action en POST | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_hero | emailveld | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#home_hero | embed=1 | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /#alle | gedeelde meetcode gekoppeld | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /nieuwsbrief/ | pagina laden | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /nieuwsbrief/#landing_main | formulier aanwezig (exact één) | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /nieuwsbrief/#landing_main | Buttondown action en POST | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /nieuwsbrief/#landing_main | emailveld | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /nieuwsbrief/#landing_main | embed=1 | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /nieuwsbrief/#alle | gedeelde meetcode gekoppeld | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | beide formulieren | meetcode newsletter_view | PASS | Broncontrole; geen bewijs van ontvangst |
| 2026-10-18T10:06:35.746957+00:00 | beide formulieren | meetcode newsletter_cta_click | PASS | Broncontrole; geen bewijs van ontvangst |
| 2026-10-18T10:06:35.746957+00:00 | beide formulieren | meetcode newsletter_form_submit | PASS | Broncontrole; geen bewijs van ontvangst |
| 2026-10-18T10:06:35.746957+00:00 | /?inschrijving=bevestigen | redirectdoel en routerbron | PASS | Accountinstelling en echte redirect vereisen maandtest |
| 2026-10-18T10:06:35.746957+00:00 | /?inschrijving=bevestigen | doel bereikbaar | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | /?inschrijving=bevestigd | redirectdoel en routerbron | FAIL | Accountinstelling en echte redirect vereisen maandtest |
| 2026-10-18T10:06:35.746957+00:00 | /?inschrijving=bevestigd | doel bereikbaar | PASS |  |
| 2026-10-18T10:06:35.746957+00:00 | Simple Analytics | eventontvangst | MANUAL | Geen API-sleutel; controleer Events over de afgelopen 7 volledige dagen |
| 2026-10-18T10:06:35.746957+00:00 | Buttondown | redirectinstellingen en double opt-in | MANUAL | Geen account-API aangesloten; controleer maandelijks in dashboard |
| 2026-10-18T10:06:35.746957+00:00 | Buttondown + mailbox | inschrijven, mail, bevestigen en opruimen | MANUAL | Alleen met gecontroleerd testadres; nooit automatisch |
