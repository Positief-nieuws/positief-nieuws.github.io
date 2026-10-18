# Analytics veilig controleren

Lees dit vóór iedere browsercontrole, ook in een nieuwe AI-sessie. `AGENTS.md` verwijst hiernaar.

## Dagelijks werk

1. Wijzig bestanden via Git of GitHub. Dit voert de website-JavaScript niet uit en veroorzaakt geen Simple Analytics-pageview. De huidige Python/Node-controles doen dat evenmin. Een deploy op zichzelf is geen bezoek.
2. Gebruik eerst een lokale preview: `python3 -m http.server 8000 --bind 127.0.0.1`. Alleen HTTPS op `positief-nieuws.nl` en `www.positief-nieuws.nl` zonder afwijkende poort mag productietracking laden. Andere hosts, localhost en bestanden niet. `data-hostname` kan een preview dus niet meer naar productie sturen.
3. Voor live onderhoud open je **als eerste URL** `https://positief-nieuws.nl/?pn_internal=1` in de te gebruiken browser. Op een andere startpagina voeg je `?pn_internal=1` toe (of `&pn_internal=1` bij bestaande parameters). De uitsluiting werkt vóór de trackingloader en wordt opgeslagen onder `pn_internal_analytics_v1` in localStorage van deze oorsprong. Alle tabs op die oorsprong nemen dit bij hun volgende paginalading over.
4. Controleer in de DOM dat `<html data-pn-analytics="internal">` aanwezig is en dat er geen script van `scripts.simpleanalyticscdn.com` staat. Controleer bij twijfel in Network dat geen `simple.gif`/events worden verstuurd. Doe daarna navigaties en een herlaadactie. De URL-parameter wordt verwijderd om verspreiding via gedeelde links te beperken.
5. `internal-temporary` betekent: opslag geblokkeerd. Dan geldt de uitsluiting alleen voor deze pagina. Voeg de parameter toe aan **iedere** nieuwe URL, of gebruik een aantoonbaar blokkerende browserextensie. Begin geen vrije navigatietest.
6. Een nieuw browserprofiel, andere browser, gewiste opslag of andere oorsprong vereist opnieuw uitsluiten. Reeds geopende pagina's met geladen analytics moet je opnieuw laden via de uitsluitings-URL. De vlag stopt geen reeds verstuurde requests. Oude offline caches kunnen oude code tonen; verifieer altijd het DOM-kenmerk.

De site onderdrukt geen algemene AI-useragents en geen alle automatisering om legitieme bezoekers niet willekeurig uit te sluiten. Een AI die een gewone browser gebruikt, is zonder expliciete uitsluiting technisch niet betrouwbaar van een bezoeker te onderscheiden. Dit protocol is daarom verplicht, ook bij ChatGPT Work.

## Browserextensie en IP

De officiële [Simple Analytics-extensie](https://docs.simpleanalytics.com/extension) blokkeert requests voor de sites waarvoor je toestemming geeft. Dit is een aanvullende optie voor een vaste werkbrowser; controleer de actieve blokkade en teller per site. Deze extensie is niet door deze implementatie geïnstalleerd of als actief geverifieerd. Ze verhuist niet automatisch mee naar een AI-browser.

[IP-uitsluiting](https://docs.simpleanalytics.com/exclude-ips) geldt accountbreed, ondersteunt volgens de documentatie IPv4 en is ongeschikt als standaardoplossing bij gedeelde, wisselende of AI-infrastructuur-IP's. Geen IP toevoegen zonder vast te stellen dat geen echte bezoekers of andere websites worden geraakt. [Geavanceerde botfiltering](https://docs.simpleanalytics.com/robot-blocking) is eveneens accountbreed; standaard botfiltering blijft een aanvulling, geen garantie voor AI-browserbezoeken. Bestaande Do Not Track- en adblockerkeuzes blijven gerespecteerd.

## Echte trackingtest: alleen bij wijzigingen aan analytics/funnel

- Gebruik een afzonderlijk testprofiel zonder uitsluiting of extensieblokkade. `?pn_internal=0` verwijdert expliciet de uitsluiting voor deze oorsprong; gebruik dat niet in de vaste werkbrowser. `data-pn-analytics="production"` bevestigt alleen dat laden is toegestaan, niet dat Simple Analytics iets heeft opgeslagen.
- Leg vooraf UTC-tijd, starttellingen, pagina's, browser, acties en campagne `utm_campaign=analytics-validation-YYYYMMDD` vast. Voeg die campagne aan iedere gecontroleerde navigatie toe: hij blijft niet automatisch in interne links staan. Maak geen nieuwe eventnamen. Noteer het precieze aantal bewuste productiepageviews/events in het testverslag.
- Controleer één pageview, `newsletter_cta_click`, formulier zichtbaar (`newsletter_view`), de landingspagina (`newsletter_landing_view`) en delen (`article_share_click`; kopieer link, verstuur geen bericht). Test waar nodig andere bestaande events. Klik niet herhaaldelijk om ontvangst af te dwingen.
- Gebruik voor één echte inschrijving uitsluitend een door de eigenaar aangewezen testadres. Controleer geldig formulier, `newsletter_form_submit` en verwerking in Buttondown. Een inzending is **submitted_unconfirmed**, geen bevestigde abonnee. Alleen Buttondown bepaalt de bevestigde status. Stuur geen nieuwsbrief en bevestig geen inschrijving namens de gebruiker.
- Controleer de request en respons/feedback in Network én daarna ontvangst in Simple Analytics Events/Visitors met tijd, pad en campagne. Een technisch request of HTTP-succes is geen bewijs van een geregistreerde pageview: botfiltering, DNT en verwerking kunnen verschillen. Wacht op rapportage; ververs na enkele minuten. Als ontvangst uitblijft, noteer ONBEVESTIGD en onderzoek, herhaal de test niet blind.
- De bewuste live proef meet mee. Rapporteer de bekende testbijdrage; wijzig/verwijder historische gegevens niet. Sluit het testprofiel na afloop weer uit of sluit het profiel.

## Na codewijzigingen

```sh
node tests/test_analytics_policy.js
node tests/test_newsletter_analytics.js
node tests/test_social_sharing.js
python3 -m unittest discover -s tests -p 'test_analytics_policy.py'
```

`analytics-loader.js` beheert productiehost, uitsluiting en één trackingloader. Hij laat alle bestaande eventnamen/metadata en Buttondown-formulieren intact. Bij uitsluiting worden de eventqueue en toekomstige events weggegooid; formulieren en delen werken wel. De vlag bevat geen persoons-ID. `analytics_policy.py` normaliseert oude laadpunten en is idempotent. `build_editions.analytics_html()` gebruikt de gedeelde loader voor nieuwe pagina's; `refresh_edition_analytics()` normaliseert bestaande pagina's. Voer na een nieuw handgeschreven paginalaadpunt `python3 analytics_policy.py` uit. De controle op alle HTML-pagina's voorkomt een directe CDN-loader buiten het beleid.

De serviceworker gebruikt versie v10; de beleidsloader wordt via het netwerk ververst. Normale browserupdates en de allereerste verse paginalading blijven nodig voor al geopende/oude pagina's. Als de eigen loader niet beschikbaar is, kan analytics niet laden; controleer dat bestand daarom bij deployment.
