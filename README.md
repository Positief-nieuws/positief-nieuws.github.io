# Positief nieuws

Statische GitHub Pages-site op positief-nieuws.nl. Python bouwt HTML en zoekdata;
JavaScript verzorgt dynamische homepage, zoeken, delen, analytics en offline lezen.
Geen package manager, framework of externe Python-/Node-packages nodig.
Gebruik Python 3.13 en Node 22, zoals in GitHub Actions.

## Bronnen en gegenereerde bestanden

- `nieuws.json`: goedgekeurde huidige editie; `edities/*.json`: historisch archief.
- `REDACTIE.txt`, `selection_preferences.json`, `editorial_policy.json`,
  `redactie/` en vanaf 19 oktober 2026 `selectie/`: redactionele werkwijze en bewijs.
- `sources.json`: bronregister. `auto_news.py` verzamelt kandidaten;
  `source_state.json` bewaart ontdekkingsmetadata, `source_health.json` bronstatus.
  Deze bestanden zijn operationele staat, geen wegwerpbare buildcache.
- `build_editions.py`: editie-, artikel-, onderwerp- en sitemapgenerator;
  `categories.py`: gedeelde Python-taxonomie, inclusief historische labels.
- `index.html`: tevens handgeschreven homepage/app-shell. De generator vervangt
  alleen gemarkeerde nieuwsblokken. Overige informatiepagina's en specials zijn
  ook bronbestanden; verwijder niet zomaar alle HTML om opnieuw te bouwen.
- `newsletter_conversion.py`, `social_sharing.py`, `mission_copy.py`,
  `article_layout.py`, `analytics_policy.py`: gedeelde paginacomponenten en
  normalisatie van bestaande en nieuwe pagina's.
- `site-theme.css`, `newsletter-conversion.css`: rechtstreeks onderhouden
  stylesheets; de build overschrijft ze niet met Python-kopieën.
- `build_search.py`: zoekindex uit edities en aanwezige informatie-/specialpagina's.
- `images/artikelen/` en `data/pixabay-images.json`: opgeslagen beeldkeuzes en
  herkomst/licentiegegevens. Behouden voor reproduceerbare builds zonder API-key.
- `edities/*/`, `artikelen/*/`, onderwerp-HTML, `onderwerpen/index.json`,
  `edities/index.json`, `zoeken/index.json`, `sitemap.xml`: gepubliceerde buildoutput.
  Deze blijft in Git omdat GitHub Pages rechtstreeks de repository publiceert.
- Oude onderwerp-URLs en concept-URLs zijn redirects; oude conceptdata blijven
  beschikbaar in `nieuws-2026-10-12-CONCEPT.json` als historisch redactioneel record.

## Lokaal controleren

```sh
python3 build_editions.py --validate-current
python3 editorial_check.py
python3 build_editions.py
python3 -m unittest discover -s tests
node tests/test_analytics_policy.js
node tests/test_newsletter_analytics.js
node tests/test_social_sharing.js
python3 scripts/check_newsletter.py --local --output /tmp/pn-newsletter-check
```

Controleer tests ook **na** de build. De volledige build behoudt de opgeslagen
beeldkeuzes; nieuwe beelden hebben internet en eventueel `PIXABAY_API_KEY` nodig.
`buttondown_draft.py` maakt via `BUTTONDOWN_API_KEY` een echt extern concept;
voer dat niet uit als lokale rooktest. Het script controleert eerst het dossier.

Lees vóór browsergebruik [het analyticsprotocol](docs/analytics-testing.md).
Een lokale preview kan met `python3 -m http.server 8000 --bind 127.0.0.1`.
Test homepage → artikel, onderwerp/archief, zoeken en nieuwsbrief; de terugkeer
van Buttondown gebruikt `?inschrijving=bevestigen` en `?inschrijving=bevestigd`.
Een echte inschrijving/verzending is een aparte handeling.

## Publicatie en controles

`.github/workflows/analytics-policy.yml` bouwt en test elke pull request.
`daily-news.yml` verzamelt uitsluitend kandidaten. Een goedgekeurde wijziging
van `nieuws.json` activeert `Bewaar editie`, daarna `Maak Buttondown concept`.
Live publicatie en verzending volgen de afzonderlijke akkoordstappen in
`REDACTIE.txt`. `newsletter-health.yml` doet iedere zes uur en na wijzigingen/publicatie broncontroles voor alle inschrijfpunten;
`docs/newsletter-tests/` beschrijft de aanvullende maandtest.
De gerichte workflows voor zoekindex, vormgeving en nieuwsbrief blijven bruikbaar.

Zie [de opruimverantwoording](docs/cleanup-2026-10-18.md) voor afwegingen en grenzen.
