# Steunonderdelen aan- en uitzetten

Voer vanuit een schone checkout van de website op `main` uit:

```sh
python3 scripts/steun.py online
```

Dit haalt de nieuwste versie op, herstelt de steunpagina en alle steunblokken,
links en privacytekst, bouwt de site en zoekindex opnieuw, voert de tests uit
en publiceert via GitHub. GitHub Pages verwerkt daarna de publicatie.
Git moet op deze computer aangemeld zijn met schrijfrechten op de repository.

Weer offline zetten kan met `python3 scripts/steun.py offline`.
Voeg `--local` toe om alleen lokaal te wijzigen en te controleren.

`support-settings.json` bewaart de stand. Iedere sitebuild past deze toe,
zodat steunblokken niet vanzelf terugkomen. De originele pagina en fragmenten
staan in `_offline/steun/content.json`. GitHub Pages sluit deze map expliciet
uit via `_config.yml`; bewaar deze herstelbestanden in Git.

Dit schakelt alleen steun aan Positief nieuws uit. Redactionele verhalen over
steun aan anderen, nieuwsbriefinschrijvingen en de augustus-instelling blijven
behouden.
