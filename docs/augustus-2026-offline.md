# Augustus 2026 tijdelijk offline

Op verzoek van de eigenaar zijn de edities van 26, 27, 28 en 31 augustus
2026 op 20 oktober 2026 uit de gepubliceerde website gehaald. De JSON-bronnen
en editiepagina's staan niet meer op main. Archief, onderwerpen, zoeken en
sitemap zijn opnieuw opgebouwd; de offlinecache heeft een nieuwe versie.

De oorspronkelijke bestanden blijven bewaard op GitHub in de branch
`archief/augustus-2026-offline`, vanaf commit
`11068b500cbb3056b5253e6e818c52577193baa5`. Deze branch wordt niet gepubliceerd.
De Git-geschiedenis blijft eveneens intact.

Terugzetten kan door de gewenste `edities/2026-08-*.json` uit deze branch
terug te halen en `python3 build_editions.py` uit te voeren. Controleer daarna
de site en publiceer pas op verzoek van de eigenaar. Zolang de JSON-bronnen
niet worden teruggezet, bouwen volgende sitebuilds deze edities niet opnieuw.
