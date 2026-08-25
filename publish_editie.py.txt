import json
import subprocess
import sys
from pathlib import Path

NEWS_FILE = Path("nieuws.json")

def fail(message):
    print(f"FOUT: {message}")
    sys.exit(1)

def run_git(*args, capture=False):
    result = subprocess.run(["git", *args], text=True, capture_output=capture)
    if result.returncode != 0:
        if capture and result.stderr:
            print(result.stderr.strip())
        fail(f"Git-commando mislukt: git {' '.join(args)}")
    return result.stdout.strip() if capture else ""

def load_and_validate_news():
    if not NEWS_FILE.exists():
        fail("nieuws.json niet gevonden.")

    try:
        data = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"nieuws.json bevat ongeldige JSON: {exc}")

    for section in ("nl", "int"):
        items = data.get(section)

        if not isinstance(items, list):
            fail(f"'{section}' moet een lijst zijn.")

        if len(items) != 7:
            fail(f"'{section}' moet precies 7 artikelen bevatten; gevonden: {len(items)}.")

        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                fail(f"{section} artikel {index} is geen geldig object.")

            for field in ("title", "url", "source", "category"):
                value = item.get(field)
                if not isinstance(value, str) or not value.strip():
                    fail(f"{section} artikel {index} mist een geldige '{field}'.")

            teaser = item.get("teaser") or item.get("summary")
            if not isinstance(teaser, str) or not teaser.strip():
                fail(f"{section} artikel {index} mist een teaser/summary.")

    return data

def get_edition_date(data):
    meta = data.get("meta")
    if isinstance(meta, dict) and meta.get("edition_date"):
        return str(meta["edition_date"])

    edition = data.get("edition")
    if isinstance(edition, dict) and edition.get("date"):
        return str(edition["date"])

    return "nieuwe-editie"

def main():
    print("1/4 Nieuws controleren...")
    data = load_and_validate_news()
    print("OK: 7 NL + 7 internationaal en JSON is geldig.")

    print("2/4 Controleren of nieuws.json gewijzigd is...")
    status = run_git("status", "--porcelain", "--", str(NEWS_FILE), capture=True)

    if not status:
        print("Geen wijziging in nieuws.json. Niets om te publiceren.")
        return

    edition_date = get_edition_date(data)

    print("3/4 Editie committen...")
    run_git("add", str(NEWS_FILE))
    run_git("commit", "-m", f"Publiceer editie {edition_date}")

    print("4/4 Naar GitHub pushen...")
    run_git("push")

    print()
    print("KLAAR.")
    print("GitHub werkt nu automatisch de site bij en maakt de Buttondown-conceptmail.")

if __name__ == "__main__":
    main()
