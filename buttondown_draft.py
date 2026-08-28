#!/usr/bin/env python3

import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

NEWS_FILE = Path("nieuws.json")
BUTTONDOWN_URL = "https://api.buttondown.com/v1/emails"
SITE_URL = "https://positief-nieuws.github.io/"

SHARE_TEXT = (
    "Positief nieuws. Dit gebeurt ook. "
    "12 positieve verhalen en 3 belangrijke nieuwsitems om bij te blijven."
)
WHATSAPP_SHARE_URL = (
    "https://wa.me/?text="
    + urllib.parse.quote(f"{SHARE_TEXT}\n\n{SITE_URL}")
)
EMAIL_SHARE_URL = (
    "mailto:?subject="
    + urllib.parse.quote("Positief nieuws. Dit gebeurt ook.")
    + "&body="
    + urllib.parse.quote(f"{SHARE_TEXT}\n\n{SITE_URL}")
)


def load_news():
    if not NEWS_FILE.exists():
        raise FileNotFoundError("nieuws.json niet gevonden.")

    with NEWS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    nl = data.get("nl", [])
    international = data.get("int", [])
    headlines = (
        data.get("headlines")
        or data.get("nieuwskoppen")
        or data.get("main_news")
        or []
    )

    if len(nl) < 6:
        raise ValueError("nieuws.json moet 6 Nederlandse positieve verhalen bevatten.")

    if len(international) < 6:
        raise ValueError("nieuws.json moet 6 internationale positieve verhalen bevatten.")

    if len(headlines) < 3:
        raise ValueError("nieuws.json moet 3 berichten bevatten onder 'headlines'.")

    return data, nl[:6], international[:6], headlines[:3]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def article_html(article):
    title = esc(article.get("title"))
    teaser = esc(article.get("teaser") or article.get("summary"))
    source = esc(article.get("source"))
    category = esc(article.get("category"))
    url = esc(article.get("url"))

    meta_parts = [part for part in (category, source) if part]
    meta = " &nbsp;·&nbsp; ".join(meta_parts)

    image = article.get("image")
    image_alt = esc(article.get("imageAlt") or title)

    image_html = ""
    if image:
        image_html = f"""
        <p style="margin:16px 0;">
          <img
            src="{esc(image)}"
            alt="{image_alt}"
            style="display:block;width:100%;max-width:640px;height:auto;border-radius:12px;"
          >
        </p>
        """

    return f"""
      <div style="margin:0 0 30px 0;padding:0 0 26px 0;border-bottom:1px solid #d7dfd8;">
        {image_html}

        <p style="margin:0 0 7px 0;font:700 12px Arial,sans-serif;letter-spacing:.05em;text-transform:uppercase;color:#24523f;">
          {meta}
        </p>

        <h2 style="margin:0 0 10px 0;font:700 25px Georgia,serif;line-height:1.12;color:#17382b;">
          <a
            href="{url}"
            style="color:#17382b;text-decoration:none;"
          >
            {title}
          </a>
        </h2>

        <p style="margin:0 0 12px 0;font:16px Georgia,serif;line-height:1.55;color:#445149;">
          {teaser}
        </p>
      </div>
    """


def build_share_block():
    return f"""
  <div style="margin-top:36px;padding:26px;border-radius:16px;background:#17382b;text-align:center;">

    <p style="margin:0 0 8px 0;font:700 24px Georgia,serif;color:#ffffff;">
      Ken je iemand die ook wel nieuws wil lezen zonder eindeloos te blijven scrollen?
    </p>

    <p style="margin:0 0 20px 0;font:15px Arial,sans-serif;line-height:1.5;color:#dfe8e2;">
      Deel deze editie gerust.
    </p>

    <table
      role="presentation"
      cellspacing="0"
      cellpadding="0"
      border="0"
      align="center"
      style="margin:0 auto 12px auto;"
    >
      <tr>
        <td
          bgcolor="#ed6a38"
          style="border-radius:999px;text-align:center;"
        >
          <a
            href="{WHATSAPP_SHARE_URL}"
            style="display:inline-block;padding:12px 22px;text-decoration:none !important;"
          >
            <font
              face="Arial, Helvetica, sans-serif"
              color="#ffffff"
              size="2"
              style="font-weight:700;color:#ffffff !important;"
            >
              Deel via WhatsApp
            </font>
          </a>
        </td>
      </tr>
    </table>

    <table
      role="presentation"
      cellspacing="0"
      cellpadding="0"
      border="0"
      align="center"
      style="margin:0 auto;"
    >
      <tr>
        <td
          bgcolor="#ed6a38"
          style="border-radius:999px;text-align:center;"
        >
          <a
            href="{EMAIL_SHARE_URL}"
            style="display:inline-block;padding:12px 22px;text-decoration:none !important;"
          >
            <font
              face="Arial, Helvetica, sans-serif"
              color="#ffffff"
              size="2"
              style="font-weight:700;color:#ffffff !important;"
            >
              Deel via e-mail
            </font>
          </a>
        </td>
      </tr>
    </table>

    <p style="margin:20px 0 0 0;font:13px Arial,sans-serif;color:#dfe8e2;">
      <a
        href="{SITE_URL}"
        style="color:#ffffff;text-decoration:underline;"
      >
        Lees deze editie ook online
      </a>
    </p>

  </div>
"""



DUTCH_DAYS = [
    "maandag",
    "dinsdag",
    "woensdag",
    "donderdag",
    "vrijdag",
    "zaterdag",
    "zondag",
]

DUTCH_MONTHS = [
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
]


def edition_date_text(data):
    raw_date = (
        data.get("meta", {}).get("edition_date")
        or data.get("edition", {}).get("date")
        or datetime.now().strftime("%Y-%m-%d")
    )

    try:
        date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        return (
            f"{DUTCH_DAYS[date_obj.weekday()]} "
            f"{date_obj.day} "
            f"{DUTCH_MONTHS[date_obj.month - 1]} "
            f"{date_obj.year}"
        )
    except (TypeError, ValueError):
        return str(raw_date)


def intro_label(article):
    return str(
        article.get("intro_label")
        or article.get("introLabel")
        or article.get("title")
        or ""
    ).strip()


def today_intro_text(nl):
    items = [intro_label(article) for article in nl[:3]]
    items = [item for item in items if item]

    if not items:
        return "Vandaag lees je onder meer over drie positieve ontwikkelingen uit Nederland."

    if len(items) == 1:
        return f"Vandaag lees je onder meer over {items[0]}."

    if len(items) == 2:
        return f"Vandaag lees je onder meer over {items[0]} en {items[1]}."

    return f"Vandaag lees je onder meer over {items[0]}, {items[1]} en {items[2]}."


def build_body(data, nl, international, headlines):
    nl_html = "\n".join(article_html(article) for article in nl)
    int_html = "\n".join(article_html(article) for article in international)
    headlines_html = "\n".join(article_html(article) for article in headlines)
    share_block = build_share_block()

    return f"""<!-- buttondown-editor-mode: fancy -->
<div style="max-width:680px;margin:0 auto;background:#fbf7ea;padding:28px;font-family:Georgia,serif;color:#1e2923;">

  <div style="margin-bottom:28px;">
    <h1 style="margin:0;font:700 42px Georgia,serif;line-height:1;color:#17382b;">
      Positief nieuws
    </h1>

    <p style="margin:8px 0 0 0;font:700 14px Arial,sans-serif;color:#ed6a38;">
      Dit gebeurt ook.
    </p>

    <p style="margin:10px 0 0 0;font:700 13px Arial,sans-serif;color:#667068;">
      {esc(edition_date_text(data))}
    </p>
  </div>

  <p style="margin:0 0 10px 0;font:700 16px Georgia,serif;line-height:1.6;color:#17382b;">
    Positief nieuws laat zien wat er óók gebeurt.
  </p>

  <p style="margin:0 0 10px 0;font:16px Georgia,serif;line-height:1.6;color:#445149;">
    In een paar minuten weet je wat er goed gaat én wat je verder moet weten. Zonder eindeloos scrollen.
  </p>

  <p style="margin:0 0 34px 0;font:700 16px Georgia,serif;line-height:1.6;color:#17382b;">
    {esc(today_intro_text(nl))}
  </p>

  <p style="margin:0 0 6px 0;font:700 12px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#ed6a38;">
    6 verhalen
  </p>

  <h2 style="margin:0 0 8px 0;font:700 34px Georgia,serif;line-height:1;color:#17382b;">
    Goed nieuws uit Nederland
  </h2>

  <p style="margin:0 0 26px 0;font:15px Georgia,serif;line-height:1.5;color:#667068;">
    Zes positieve ontwikkelingen uit Nederland. Over mensen, gezondheid, wetenschap, natuur, sport en andere dingen die de goede kant op bewegen.
  </p>

  {nl_html}

  <div style="margin:42px -28px 32px -28px;padding:32px 28px;background:#e6f1dc;">
    <p style="margin:0 0 6px 0;font:700 12px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#ed6a38;">
      6 verhalen
    </p>

    <h2 style="margin:0 0 8px 0;font:700 34px Georgia,serif;line-height:1;color:#17382b;">
      Goed nieuws uit de wereld
    </h2>

    <p style="margin:0;font:15px Georgia,serif;line-height:1.5;color:#667068;">
      Omdat goed nieuws zich niet aan landsgrenzen houdt. Zes positieve ontwikkelingen van buiten Nederland die het waard zijn om te weten. De artikelen waar we naar verwijzen zijn Engelstalig.
    </p>
  </div>

  {int_html}

  <div style="margin:42px -28px 32px -28px;padding:32px 28px;background:#fffdf6;border-top:2px solid #17382b;border-bottom:1px solid #d7dfd8;">
    <p style="margin:0 0 6px 0;font:700 12px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#ed6a38;">
      3 berichten
    </p>

    <h2 style="margin:0 0 8px 0;font:700 34px Georgia,serif;line-height:1;color:#17382b;">
      Wat je verder moet weten
    </h2>

    <p style="margin:0;font:15px Georgia,serif;line-height:1.5;color:#667068;">
      Drie onderwerpen die het Nederlandse nieuws op dit moment domineren. Niet per se positief, wel belangrijk om van op de hoogte te zijn. Kort, feitelijk en zonder sensatie.
    </p>
  </div>

  {headlines_html}

  {share_block}

  <p style="margin:30px 0 0 0;text-align:center;font:14px Georgia,serif;line-height:1.5;color:#445149;">
    Dit was het voor vandaag. Je bent weer bij. Geniet van je dag.
  </p>

  <p style="margin:12px 0 0 0;text-align:center;font:12px Arial,sans-serif;color:#667068;">
    Positief nieuws. Dit gebeurt ook.
  </p>

</div>
"""


def edition_date_short_text(data):
    raw_date = (
        data.get("meta", {}).get("edition_date")
        or data.get("edition", {}).get("date")
        or datetime.now().strftime("%Y-%m-%d")
    )

    try:
        date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        return (
            f"{DUTCH_DAYS[date_obj.weekday()]} "
            f"{date_obj.day} "
            f"{DUTCH_MONTHS[date_obj.month - 1]}"
        )
    except (TypeError, ValueError):
        return str(raw_date)


def build_subject(data):
    return f"Dit gebeurt ook · {edition_date_short_text(data)}"


def create_draft(api_key, subject, body):
    payload = {
        "subject": subject,
        "body": body,
        "status": "draft",
        "canonical_url": SITE_URL,
        "description": (
            "12 positieve verhalen + 3 belangrijke nieuwsitems om bij te blijven."
        ),
    }

    request = urllib.request.Request(
        BUTTONDOWN_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Buttondown API gaf HTTP {exc.code}: {error_body}"
        ) from exc


def main():
    api_key = os.environ.get("BUTTONDOWN_API_KEY")

    if not api_key:
        print("FOUT: BUTTONDOWN_API_KEY ontbreekt.", file=sys.stderr)
        sys.exit(1)

    try:
        data, nl, international, headlines = load_news()
        subject = build_subject(data)
        body = build_body(data, nl, international, headlines)
        draft = create_draft(api_key, subject, body)
    except Exception as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Buttondown-concept aangemaakt.")
    print(f"Onderwerp: {draft.get('subject', subject)}")
    print(f"ID: {draft.get('id', 'onbekend')}")
    print(f"Status: {draft.get('status', 'onbekend')}")


if __name__ == "__main__":
    main()
