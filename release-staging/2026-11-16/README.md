# Releasevoorbereiding Positief Nieuws, 16 november 2026

Status: klaar als redactionele input, **niet publicatieklaar zonder controles**.

Deze branch bewaart de exact door de eigenaar goedgekeurde content en de laatste HTML-conceptpreview. Er staat niets op main of in Buttondown. De HTML-preview bevat opzettelijk nog beeldplaatsaanduidingen en is **niet** de door build_editions.py gebouwde sitepreview.

## Morgen: gebruikerscommando

**pn go**

Voer in Work de publicatie uit vanaf deze branch, op de actuele main. Controleer eerst bron-ID's/bronregister voor ACM en KVK en verwijder eventuele bronlabelafwijkingen. Gebruik de 12 uniek geselecteerde Pixabay-ID's uit beeldselectie.json en de id:-velden in nieuws.json. Download en controleer de werkelijke foto-binaries via de bestaande Pixabay-integratie, controleer uitsnede, beeldenrechten en herkomst, en leg die in het publicatiedossier vast. Vul redactie/2026-11-16.json met daadwerkelijke broncontrole (geen fictieve verificatie) en genereer met de bestaande build_editions.py en publish_edition.py --prepare de homepage, editie en 12 artikelpagina's. Houd persoonlijke noot afwezig. Volg REDACTIE.txt, AGENTS.md, huidige generator-SEO (H2's, contextuele interne links, onderwerp-link, canonical, JSON-LD). Vergelijk het resultaat met de goedgekeurde preview. Publiceer alleen bij alle geslaagde controles en expliciete pn go-toestemming, en verander geen scripts of workflows in de editiecommit. Controleer na Pages-deployment 14 pagina's live met ?pn_internal=1 en verifieer laatste editie-titel en datum. Maak **daarna** met buttondown_draft.py het nieuwsbriefconcept; controleer idempotentie op editie-URL; verstuur via Buttondown PATCH van draft naar about_to_send pas bij volledige livecontrole. Niets dubbel versturen. Maak bij mislukte livecontrole geen verzending.

## Grenzen

- Geen automatische publicatie vóór 16 november.
- De huidige Buttondown-koppeling maakt alleen concepten; het echte verzenden is een **extra** actie.
- Alle 12 Pixabay-beeldkeuzes zijn alvast individueel geselecteerd en van bron-URL en beschrijvende alt-tekst voorzien in beeldselectie.json. De foto-bestanden zijn NOG NIET gedownload/opgeslagen. Laat morgen de Pixabay-API de exacte ID's ophalen en controleer de echte beelden en licentie vóór publicatie. Niet als beeld-gereed markeren.
- Eerste bestaande publicatiecontrole hoeft niet te worden aangepast.
- Drie mainstream actualiteiten, geen persoonlijke noot, geen '01/03'-nummering.
- De inhoud is vastgezet; bij een inhoudelijke wijziging eerst opnieuw akkoord vragen.

## Fotopreview (15 november)
De gebruiker heeft een bijgewerkt HTML-concept met de 12 Pixabay-foto's ontvangen (externe CDN-links, geen lokale binaries). De staging-beeldselectie is afgestemd op die fotopreview. Dit is geen definitief offline beeldpakket: vóór livegang moet de bestaande Pixabay-infrastructuur de gekozen ID's downloaden, visueel controleren en in de cache opslaan. De site en nieuwsbrief blijven ongewijzigd tot `pn go`.

## Harde bescherming huidige homepage-design bij pn go

De losstaande "goedgekeurde-preview.html" / "met-fotos.html" is een inhoudelijke redactiepreview met ANDERE vormgeving. **Kopieer deze HTML NOOIT naar de productie-index.html**. Bouw uitsluitend met de bestaande actuele main-versie van index.html en de huidige site-theme.css, edition-layout.css, JS, mobiele layout, reviews, header, footer, kleurgebruik en branding. Geen wijzigingen aan ontwerp-/CSS-/JS-bestanden in deze editie-release.

Na `publish_edition.py --prepare` moet de diff van index.html gecontroleerd worden. Alleen de generator-gerelateerde inhoudsblokken, publicatiedatum, nieuwsitems, schema/SEO en de bewust verwijderde persoonlijke noot mogen verschillen. Besteed aandacht aan behoud van header, navigatie, hero, eigen homepage-layout, review-swiper, footer en responsive instellingen. CSS, JS en design-elementen buiten de nieuwsblokken mogen NIET veranderen.

Als de generator onverwachte ontwerp-/structuurwijzigingen veroorzaakt: STOP, niet committen, niet live zetten, geen nieuwsbrief versturen. Herstel op een schone actuele main en draai de preview- en diffcontrole opnieuw. Laat gewijzigde vormgeving vooraf opnieuw beoordelen.
