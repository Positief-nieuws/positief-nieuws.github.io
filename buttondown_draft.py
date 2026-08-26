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
    "13 positieve verhalen en 3 onderwerpen om bij te blijven."
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

    if len(nl) < 7:
        raise ValueError("nieuws.json moet 7 Nederlandse positieve verhalen bevatten.")

    if len(international) < 6:
        raise ValueError("nieuws.json moet 6 internationale positieve verhalen bevatten.")

    if len(headlines) < 3:
        raise ValueError("nieuws.json moet 3 berichten bevatten onder 'headlines'.")

    return data, nl[:7], international[:6], headlines[:3]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def article_html(article):
    title = esc(article.get("title"))
    teaser = esc(article.get("teaser") or article.get("summary"))
    source = esc(article.get("source"))
    category = esc(article.get("category"))
    url = esc(article.get("url"))

    meta = " · ".join([part for part in (category, source) if part])

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
          {title}
        </h2>

        <p style="margin:0 0 12px 0;font:16px Georgia,serif;line-height:1.55;color:#445149;">
          {teaser}
        </p>

        <p style="margin:0;">
          <a
            href="{url}"
            style="font:700 14px Arial,sans-serif;color:#d95727;text-decoration:none;"
          >
            Lees het verhaal →
          </a>
        </p>
      </div>
    """


def build_share_block():
    return f"""
  <div style="margin-top:36px;padding:26px;border-radius:16px;background:#17382b;text-align:center;">

    <p style="margin:0 0 8px 0;font:700 24px Georgia,serif;color:#ffffff;">
      Ken je iemand die dit ook kan gebruiken?
    </p>

    <p style="margin:0 0 20px 0;font:15px Arial,sans-serif;line-height:1.5;color:#dfe8e2;">
      Stuur Positief nieuws gerust door.
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


def build_body(nl, international, headlines):
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
  </div>

  <p style="margin:0 0 34px 0;font:16px Georgia,serif;line-height:1.6;color:#445149;">
    Veel van het nieuws dat dagelijks langskomt gaat over wat misgaat. Logisch, maar daardoor verdwijnen de dingen die wél vooruitgaan makkelijk uit beeld. Daarom verzamelen we hier het nieuws dat ook verteld mag worden: <strong>7 positieve verhalen uit Nederland en 6 uit de rest van de wereld.</strong> En omdat je ook gewoon wilt weten wat er speelt, sluiten we af met <strong>3 nieuwsverhalen die de Nederlandse nieuwskoppen op dit moment domineren.</strong>
  </p>

  <p style="margin:0 0 6px 0;font:700 12px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#ed6a38;">
    7 verhalen
  </p>

  <h2 style="margin:0 0 8px 0;font:700 34px Georgia,serif;line-height:1;color:#17382b;">
    Goed nieuws uit Nederland
  </h2>

  <p style="margin:0 0 26px 0;font:15px Georgia,serif;line-height:1.5;color:#667068;">
    Zeven positieve ontwikkelingen uit Nederland. Over mensen, gezondheid, wetenschap, natuur, sport en andere dingen die de goede kant op bewegen.
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
      Omdat goed nieuws zich niet aan landsgrenzen houdt. Zes positieve ontwikkelingen van buiten Nederland die het waard zijn om te weten.
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

  <p style="margin:30px 0 0 0;text-align:center;font:12px Arial,sans-serif;color:#667068;">
    Positief nieuws. Dit gebeurt ook.
  </p>

</div>
"""


def build_subject(data):
    raw_date = (
        data.get("meta", {}).get("edition_date")
        or data.get("edition", {}).get("date")
        or datetime.now().strftime("%Y-%m-%d")
    )

    try:
        date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        date_text = date_obj.strftime("%d-%m-%Y")
    except ValueError:
        date_text = raw_date

    return f"Positief nieuws · {date_text}"


def create_draft(api_key, subject, body):
    payload = {
        "subject": subject,
        "body": body,
        "status": "draft",
        "canonical_url": SITE_URL,
        "description": (
            "7 positieve verhalen uit Nederland, 6 uit de wereld "
            "en 3 belangrijke nieuwsitems om bij te blijven."
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
        body = build_body(nl, international, headlines)
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
