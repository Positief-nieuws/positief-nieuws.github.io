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

PAPER = "#f7f5ec"
INK = "#151a17"
GREEN = "#1f5b45"
GREEN_DARK = "#173f31"
ACCENT = "#d6a13a"
MUTED = "#68716b"
LINE = "rgba(23,63,49,.16)"
NL_BG = "#f8f3e8"
WORLD_BG = "#eef3ed"
BRIEFING_BG = "#f3efe7"

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


def raw_edition_date(data):
    return (
        data.get("meta", {}).get("edition_date")
        or data.get("edition", {}).get("date")
        or datetime.now().strftime("%Y-%m-%d")
    )


def edition_date_text(data):
    raw_date = raw_edition_date(data)
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


def edition_date_short_text(data):
    raw_date = raw_edition_date(data)
    try:
        date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        return (
            f"{DUTCH_DAYS[date_obj.weekday()]} "
            f"{date_obj.day} "
            f"{DUTCH_MONTHS[date_obj.month - 1]}"
        )
    except (TypeError, ValueError):
        return str(raw_date)


def edition_weekday(data):
    raw_date = raw_edition_date(data)
    try:
        date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        return DUTCH_DAYS[date_obj.weekday()]
    except (TypeError, ValueError):
        return "nieuwe"


def edition_url(data):
    """Schone editie-URL, onder meer voor canonical en gedeelde links."""
    raw_date = raw_edition_date(data)
    if isinstance(raw_date, str):
        try:
            datetime.strptime(raw_date, "%Y-%m-%d")
            return f"{SITE_URL}?editie={urllib.parse.quote(raw_date)}"
        except ValueError:
            pass
    return SITE_URL


def buttondown_edition_url(data):
    """Editie-URL met UTM-tracking voor verkeer vanuit de nieuwsbrief."""
    raw_date = raw_edition_date(data)
    clean_url = edition_url(data)

    if not isinstance(raw_date, str):
        return clean_url

    try:
        datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        return clean_url

    params = {
        "utm_source": "buttondown",
        "utm_medium": "email",
        "utm_campaign": f"editie_{raw_date.replace('-', '_')}",
    }

    separator = "&" if "?" in clean_url else "?"
    return f"{clean_url}{separator}{urllib.parse.urlencode(params)}"


def reading_time_label(article):
    value = (
        article.get("reading_time_minutes")
        or article.get("readingTimeMinutes")
        or article.get("reading_time")
        or article.get("readingTime")
        or article.get("leestijd")
    )
    if value in (None, ""):
        return ""

    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return ""

    minutes = int(digits)
    return f"{minutes} min lezen" if minutes > 0 else ""


def article_html(article):
    title = esc(article.get("title"))
    teaser = esc(article.get("teaser") or article.get("summary"))
    source = esc(article.get("source"))
    category = esc(article.get("category"))
    url = esc(article.get("url"))

    meta_parts = [part for part in (category, source, reading_time_label(article)) if part]
    meta = " &nbsp;·&nbsp; ".join(meta_parts)

    return f"""
      <div style="margin:0;padding:22px 0;border-bottom:1px solid rgba(23,63,49,.12);">
        <h2 style="margin:0 0 8px 0;font:700 22px Georgia,'Times New Roman',serif;line-height:1.2;letter-spacing:-.02em;color:{INK};">
          <a href="{url}" style="color:{INK};text-decoration:none;">
            {title}
          </a>
        </h2>

        <p style="margin:0;font:15px Arial,Helvetica,sans-serif;line-height:1.5;color:#3f4742;">
          {teaser}
        </p>

        <p style="margin:10px 0 0 0;font:700 11px Arial,Helvetica,sans-serif;line-height:1.35;color:{GREEN};">
          {meta}
        </p>
      </div>
    """


def section_header(label, count, note=""):
    note_html = ""
    if note:
        note_html = f"""
        <p style="margin:11px 0 0 0;font:14px Arial,Helvetica,sans-serif;line-height:1.5;color:{MUTED};">
          {esc(note)}
        </p>
        """

    return f"""
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
             style="width:100%;border-collapse:collapse;border-bottom:1px solid {GREEN_DARK};">
        <tr>
          <td style="padding:0 0 10px 0;font:800 12px Arial,Helvetica,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:{GREEN};">
            {esc(label)}
          </td>
          <td align="right" style="padding:0 0 10px 12px;font:12px Arial,Helvetica,sans-serif;color:{INK};white-space:nowrap;">
            {esc(count)}
          </td>
        </tr>
      </table>
      {note_html}
    """


def build_share_block(data):
    # Gedeelde links blijven bewust schoon. Zo wordt verkeer dat later via
    # WhatsApp/e-mail binnenkomt niet ten onrechte als Buttondown toegeschreven.
    share_url = edition_url(data)

    # Alleen de directe klik vanuit deze nieuwsbrief krijgt Buttondown-UTM's.
    newsletter_online_url = buttondown_edition_url(data)

    share_text = (
        "Positief nieuws. In een paar minuten weet je wat er goed gaat "
        "én wat je verder moet weten. Zonder eindeloos scrollen."
    )
    whatsapp_share_url = (
        "https://wa.me/?text="
        + urllib.parse.quote(f"{share_text}\n\n{share_url}")
    )
    email_share_url = (
        "mailto:?subject="
        + urllib.parse.quote("Positief nieuws. Dit gebeurt ook.")
        + "&body="
        + urllib.parse.quote(f"{share_text}\n\n{share_url}")
    )

    return f"""
    <div style="margin:46px 0 0 0;padding:28px 22px;border:1px solid rgba(23,63,49,.18);text-align:center;background:rgba(255,255,255,.34);">
      <p style="margin:0 0 7px 0;font:700 22px Georgia,'Times New Roman',serif;line-height:1.15;color:{INK};">
        Ken je iemand die dit ook fijn zou vinden?
      </p>

      <p style="margin:0 0 20px 0;font:14px Arial,Helvetica,sans-serif;line-height:1.5;color:{MUTED};">
        Deel deze editie gerust.
      </p>

      <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
        <tr>
          <td style="padding:0 5px 10px 5px;">
            <a href="{whatsapp_share_url}"
               style="display:inline-block;padding:10px 16px;border:1px solid rgba(214,161,58,.65);border-radius:999px;font:800 12px Arial,Helvetica,sans-serif;color:{GREEN_DARK};text-decoration:none;">
              Deel via WhatsApp
            </a>
          </td>
          <td style="padding:0 5px 10px 5px;">
            <a href="{email_share_url}"
               style="display:inline-block;padding:10px 16px;border:1px solid rgba(214,161,58,.65);border-radius:999px;font:800 12px Arial,Helvetica,sans-serif;color:{GREEN_DARK};text-decoration:none;">
              Deel via e-mail
            </a>
          </td>
        </tr>
      </table>

      <p style="margin:8px 0 0 0;font:12px Arial,Helvetica,sans-serif;color:{MUTED};">
        <a href="{newsletter_online_url}" style="color:{GREEN_DARK};text-decoration:underline;text-underline-offset:2px;">
          Lees deze editie online
        </a>
      </p>
    </div>
    """


def build_body(data, nl, international, headlines):
    nl_html = "\n".join(article_html(article) for article in nl)
    int_html = "\n".join(article_html(article) for article in international)
    headlines_html = "\n".join(article_html(article) for article in headlines)
    share_block = build_share_block(data)
    weekday = esc(edition_weekday(data))

    return f"""<!-- buttondown-editor-mode: fancy -->
<div style="max-width:680px;margin:0 auto;background:{PAPER};padding:32px 28px;color:{INK};font-family:Arial,Helvetica,sans-serif;">

  <div style="margin-bottom:48px;">
    <p style="margin:0;font:800 19px Arial,Helvetica,sans-serif;letter-spacing:-.02em;color:{INK};">
      <span style="color:{ACCENT};font-size:22px;vertical-align:-1px;">☀</span>&nbsp; Positief nieuws.
    </p>
  </div>

  <div style="margin-bottom:42px;">
    <p style="margin:0 0 7px 0;font:13px Arial,Helvetica,sans-serif;color:{GREEN_DARK};">
      {esc(edition_date_text(data))}
    </p>

    <h1 style="margin:0;font:700 46px Georgia,'Times New Roman',serif;line-height:.98;letter-spacing:-.045em;color:{INK};">
      Dit gebeurt ook<span style="color:{ACCENT};">.</span>
    </h1>

    <p style="margin:20px 0 0 0;font:17px Arial,Helvetica,sans-serif;line-height:1.55;color:#2d342f;">
      In een paar minuten weet je wat er goed gaat én wat je verder moet weten
      in deze {weekday}-editie. Zonder eindeloos scrollen.
    </p>

    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
           style="width:100%;margin-top:22px;border-collapse:collapse;border-top:1px solid rgba(23,63,49,.22);">
      <tr>
        <td style="padding-top:13px;font:11px Arial,Helvetica,sans-serif;color:{MUTED};">
          maandag · woensdag · vrijdag
        </td>
        <td align="right" style="padding-top:13px;font:11px Arial,Helvetica,sans-serif;color:{MUTED};white-space:nowrap;">
          15 verhalen &nbsp;&nbsp; ongeveer 6 minuten
        </td>
      </tr>
    </table>
  </div>

  <div style="margin:0 -28px;padding:34px 28px;background:{NL_BG};">
    {section_header("Goed nieuws uit Nederland", "6 verhalen")}
    {nl_html}
  </div>

  <div style="margin:0 -28px;padding:34px 28px;background:{WORLD_BG};">
    {section_header(
        "Goed nieuws uit de wereld",
        "6 verhalen",
        "Zes positieve ontwikkelingen van buiten Nederland. De artikelen waar we naar verwijzen zijn Engelstalig."
    )}
    {int_html}
  </div>

  <div style="margin:0 -28px;padding:34px 28px;background:{BRIEFING_BG};">
    {section_header(
        "Wat je verder moet weten",
        "3 verhalen",
        "Niet per se positief, wel belangrijk. Drie onderwerpen die vandaag de Nederlandse nieuwskoppen domineren. Kort en feitelijk."
    )}
    {headlines_html}
  </div>

  <div style="padding:68px 0 18px 0;text-align:center;">
    <p style="margin:0 0 16px 0;font:30px Arial,Helvetica,sans-serif;color:{ACCENT};">☀</p>

    <h2 style="margin:0;font:700 34px Georgia,'Times New Roman',serif;line-height:1.02;letter-spacing:-.04em;color:{INK};">
      Dit was het voor vandaag.<br>Je bent weer bij.
    </h2>

    <p style="margin:16px 0 0 0;font:14px Arial,Helvetica,sans-serif;color:{MUTED};">
      Geniet van je dag.
    </p>
  </div>

  {share_block}

  <p style="margin:34px 0 0 0;text-align:center;font:11px Arial,Helvetica,sans-serif;color:#8b928e;">
    Positief nieuws · Dit gebeurt ook.
  </p>

</div>
"""


def build_subject(data):
    return f"Dit gebeurt ook · {edition_date_short_text(data)}"


def create_draft(api_key, subject, body, data):
    payload = {
        "subject": subject,
        "body": body,
        "status": "draft",
        # Canonical blijft bewust zonder UTM-parameters.
        "canonical_url": edition_url(data),
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
        draft = create_draft(api_key, subject, body, data)
    except Exception as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Buttondown-concept aangemaakt.")
    print(f"Onderwerp: {draft.get('subject', subject)}")
    print(f"ID: {draft.get('id', 'onbekend')}")
    print(f"Status: {draft.get('status', 'onbekend')}")


if __name__ == "__main__":
    main()
