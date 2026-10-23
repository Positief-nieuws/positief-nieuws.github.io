# Installatiecontrole pn go — 23 oktober 2026

Onderzochte uitgangsversie: 95a75df5a0da10f6e306ed8b885255d50bce05dc.
Veilige opslag: branch redactie/pn-go-installatie-20261023; concept-PR, geen merge.

## Publicatieonderzoek vóór opslag

Settings → Pages (ingelogd, alleen gelezen) toont Deploy from a branch,
main, / (root), domein positief-nieuws.nl. De openbare API gaf 404; daarom is de
instelling rechtstreeks in GitHub bekeken. README en REDACTIE bevestigen dit.
Geen instelling gewijzigd en geen live site geopend.

Alle tien .github/workflows/*.yml onderzocht. PR activeert build/regressietest
(contents:read, geen deploy of commit). Python in PR kan ook lokale
nieuwsbriefcontrole activeren; live controle slaat PR-events over. Push naar een
andere branch activeert geen van de aanwezige push-workflows. Pages publiceert
main/root; installatiebranch/PR wordt niet gepubliceerd. Main blijft ongewijzigd.
Een merge zou wel Pages kunnen activeren, ook bij uitsluitend documentatie.
Wijziging nieuws.json op main activeert Bewaar editie en daarna mogelijk een
extern Buttondown-concept. Geen workflow gestart of dispatch uitgevoerd.

## Onderzochte productie en input

- nieuws.json: goedgekeurde editie 22-10-2026, nl/int/headlines en volledige
  article_body; niet aangepast.
- auto_news.py, bronnenregister/-status, selectie- en feitencheck, dossiermaker,
  build_editions.py en Buttondown-render/API-pad onderzocht. Renderen en extern
  concept maken zijn afzonderlijke functies; main/create_draft niet aangeroepen.
- Kandidaten: 23-10-2026 19:53:03 +02:00; 8.662 all_candidates, twee top40-lijsten.
  collection_complete=false, editorial_coverage_complete=false. Eén feedfout:
  Nature nature-2457669d, XML ParseError (invalid token, line 14 column 4).
  Registry-hash komt overeen. Deze run is niet ververst: installatiecontrole
  doet geen volledige nieuwsproductie. Een volledige proef moet dit onderzoeken;
  voor 26 oktober is bovendien een bronrun van die editiedag vereist.
- De referentiechat is gelezen. Twee originele PNG's zijn toegankelijk gebleken,
  visueel bekeken en ongewijzigd gekopieerd; checksums en herkomst in manifest.
  Geen verdere inhoudelijke weektips verifieerbaar uit de beschikbare chat.
- Persoonlijke noot wordt door bestaande renderers niet vanzelf opgenomen;
  de procedure verplicht opname en controle in beide lokale HTML-concepten.
  Geen live-templatewijziging verricht.

## Uitgevoerde verificatie

- ./pn go --dry-run: exit 0; alle 17 vereiste bestanden gevonden, twee portretten
  geldig als PNG en checksum gelijk aan manifest; onvolledige pool eerlijk gemeld.
- Launcher ook gestart vanuit /private/tmp: exit 0; vindt repository via eigen pad.
- Voor/na SHA-256 van alle door Git gevolgde bestanden: identiek tijdens dry-run.
- 21 bestaande tests in tests/test_editorial_workflow.py: geslaagd.
- Git-diff gecontroleerd: uitsluitend installatiebestanden en verwijzing in
  AGENTS; geen wijziging aan productiecontent, workflows, generators of site-HTML.

Dit bewijst vindbaarheid en technische installatie, geen afgerond brononderzoek,
geverifieerde levensdelictcijfers, geschreven editie of goedgekeurde persoonlijke
noot. De eerste volledige proef start in de repositorychat met pn go en de
gewenste editiedatum, op deze branch; niet eerst mergen. Zie PN_WORKFLOW.md.
