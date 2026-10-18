"""Shared category taxonomy for collection, pages, search and signup copy."""
import re
import unicodedata

CATEGORY_ORDER = [
    "Cultuur",
    "Economie",
    "Energie & innovatie",
    "Gezondheid",
    "Mens",
    "Natuur & klimaat",
    "Wetenschap",
    "Sport",
]

# Historische categorieën uit eerdere edities worden bij het bouwen samengevoegd
# naar acht vaste hoofdcategorieën. Bekende oude labels blijven ondersteund zodat
# het bestaande archief en oudere links netjes blijven werken.
CATEGORY_ALIASES = {
    "Archeologie & geschiedenis": "Cultuur",
    "Cultuur & erfgoed": "Cultuur",
    "Cultuur & media": "Cultuur",
    "Geschiedenis & mens": "Cultuur",
    "Economie & geld": "Economie",
    "Economie & onderwijs": "Economie",
    "Energie & innovatie": "Energie & innovatie",
    "Gezondheid": "Gezondheid",
    "Gezondheid & basisvoorzieningen": "Gezondheid",
    "Voeding & leefstijl": "Gezondheid",
    "Gewoon leuk": "Mens",
    "Mens & innovatie": "Mens",
    "Mens & samenleving": "Mens",
    "Onderwijs & ontwikkeling": "Mens",
    "Dieren": "Natuur & klimaat",
    "Dieren & natuur": "Natuur & klimaat",
    "Natuur & klimaat": "Natuur & klimaat",
    "Natuur & landbouw": "Natuur & klimaat",
    "Natuur & samenleving": "Natuur & klimaat",
    "Natuur & wetenschap": "Natuur & klimaat",
    "Technologie & innovatie": "Wetenschap",
    "Wetenschap": "Wetenschap",
    "Wetenschap & duurzaamheid": "Wetenschap",
    "Wetenschap & innovatie": "Wetenschap",
    "Wetenschap & ruimtevaart": "Wetenschap",
    "Sport": "Sport",
}

for _category in CATEGORY_ORDER:
    CATEGORY_ALIASES.setdefault(_category, _category)


def slugify_category(value):
    label = str(value or "").strip()
    if not label:
        return ""
    normalized = unicodedata.normalize("NFKD", label)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower().replace("&", " en ")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def category_label(item):
    return str(item.get("category") or item.get("categorie") or "").strip()



def canonical_category(value):
    label = str(value or "").strip()
    if not label:
        return ""
    return CATEGORY_ALIASES.get(label, "")


