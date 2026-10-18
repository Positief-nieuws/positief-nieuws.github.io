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
SITE_URL = "https://positief-nieuws.nl/"

PAPER = "#fffcf7"
INK = "#182e35"
GREEN = "#176e5c"
GREEN_DARK = "#0e5947"
MUTED = "#64777a"

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

    if len(nl) != 6:
        raise ValueError("nieuws.json moet 6 Nederlandse positieve verhalen bevatten.")
    if len(international) != 6:
        raise ValueError("nieuws.json moet 6 internationale positieve verhalen bevatten.")
    if len(headlines) != 3:
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


def build_preheader(data, nl):
    """Inbox-preview: liefst redactioneel uit nieuws.json, anders de eerste twee NL-koppen."""
    custom = (
        data.get("meta", {}).get("email_preheader")
        or data.get("edition", {}).get("email_preheader")
        or ""
    )
    custom = " ".join(str(custom).split()).strip()
    if custom:
        return custom[:180]

    titles = []
    for article in nl[:2]:
        title = " ".join(str(article.get("title") or "").split()).strip()
        if title:
            titles.append(title)

    if not titles:
        return "12 positieve verhalen + 3 belangrijke nieuwsitems om bij te blijven."

    preview = " · ".join(titles)
    if len(preview) > 180:
        preview = preview[:177].rstrip(" ,.;:–—-") + "…"
    return preview


def edition_url(data):
    """Permanente schone editie-URL, onder meer voor canonical en gedeelde links."""
    raw_date = raw_edition_date(data)
    if isinstance(raw_date, str):
        try:
            datetime.strptime(raw_date, "%Y-%m-%d")
            return f"{SITE_URL}edities/{urllib.parse.quote(raw_date)}/"
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


def buttondown_article_url(data, article):
    """Eigen artikelpagina met UTM-tracking voor de directe klik vanuit Buttondown."""
    slug = str(article.get("article_slug") or "").strip().strip("/")
    raw_date = raw_edition_date(data)
    if not slug or not isinstance(raw_date, str):
        return str(article.get("url") or "")

    try:
        datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        return str(article.get("url") or "")

    base = f"{SITE_URL}artikelen/{urllib.parse.quote(raw_date)}/{urllib.parse.quote(slug)}/"
    params = {
        "utm_source": "buttondown",
        "utm_medium": "email",
        "utm_campaign": f"editie_{raw_date.replace('-', '_')}",
        "utm_content": slug,
    }
    return f"{base}?{urllib.parse.urlencode(params)}"


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


def article_thumbnail_url(article, data):
    """Use the same resolved image as the website, never a search URL."""
    if not data:
        return ""
    cache_path = Path("data/pixabay-images.json")
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    slug = str(article.get("article_slug") or "").strip().strip("/")
    entry = cache.get(f"{raw_edition_date(data)}/{slug}", {})
    if not isinstance(entry, dict) or entry.get("query") != article.get("image_query"):
        return ""
    path = str(entry.get("image_path") or "").strip()
    if not path:
        return ""
    url = urllib.parse.urljoin(SITE_URL, path)
    parsed = urllib.parse.urlparse(url)
    site = urllib.parse.urlparse(SITE_URL)
    if parsed.scheme != "https" or parsed.netloc != site.netloc:
        return ""
    return url


def article_html(article, data=None, prefer_own_page=False, featured=False):
    title = esc(article.get("email_title") or article.get("title"))
    teaser = esc(article.get("teaser") or article.get("summary"))
    raw_url = buttondown_article_url(data, article) if prefer_own_page and data and article.get("article_slug") else str(article.get("url") or "")
    url = esc(raw_url)
    image_url = article_thumbnail_url(article, data) if prefer_own_page else ""
    meta = " &nbsp;·&nbsp; ".join(esc(part) for part in (article.get("category"), article.get("source"), reading_time_label(article)) if part)
    image_html = ""
    if image_url:
        image_html = f'<a href="{url}" style="text-decoration:none"><img src="{esc(image_url)}" width="660" alt="{esc(article.get("image_alt") or article.get("title"))}" style="display:block;width:100%;height:auto;max-height:{340 if featured else 190}px;object-fit:cover;border:0;border-radius:16px 16px 0 0;"></a>'
    return f"""<div class="story-card" style="margin:0 0 16px;border:1px solid #e1e9e5;border-radius:17px;overflow:hidden;background:#fff;">
      {image_html}<div style="padding:{'24px 26px 28px' if featured else '18px 20px'};">
      <p style="margin:0 0 10px;font:800 10px Arial,Helvetica,sans-serif;text-transform:uppercase;letter-spacing:.08em;color:{GREEN};">{esc(article.get('category') or ('Uitgelicht' if featured else 'Actualiteit'))}</p>
      <h2 style="margin:0 0 12px;font:800 {'34' if featured else '20'}px Arial,Helvetica,sans-serif;line-height:1.18;letter-spacing:-.035em;color:{INK};"><a href="{url}" style="color:{INK} !important;text-decoration:none;">{title}</a></h2>
      {f'<p class="story-intro" style="margin:0 0 12px;font:14px Arial,Helvetica,sans-serif;line-height:1.6;color:{MUTED};">{teaser}</p>' if teaser else ''}
      <p style="margin:0;font:700 11px Arial,Helvetica,sans-serif;line-height:1.5;color:{GREEN};">{meta}</p></div></div>"""


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
    <div style="margin:46px 0 0 0;padding:28px 22px;border:1px solid rgba(23,63,49,.18);text-align:center;background:#f0f5ee;border-radius:17px;">
      <p style="margin:0 0 7px 0;font:700 22px Arial,Helvetica,sans-serif;line-height:1.15;color:{INK};">
        Ken je iemand die ook wel wat positief nieuws kan gebruiken?
      </p>

      <p style="margin:0 0 20px 0;font:14px Arial,Helvetica,sans-serif;line-height:1.5;color:{MUTED};">
        Stuur deze nieuwsbrief gerust door.
      </p>

      <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
        <tr>
          <td style="padding:0 5px 10px 5px;">
            <a href="{whatsapp_share_url}"
               style="display:inline-block;padding:10px 16px;border:1px solid rgba(214,161,58,.65);border-radius:999px;font:800 12px Arial,Helvetica,sans-serif;color:{GREEN_DARK} !important;text-decoration:none;">
              Deel via WhatsApp
            </a>
          </td>
          <td style="padding:0 5px 10px 5px;">
            <a href="{email_share_url}"
               style="display:inline-block;padding:10px 16px;border:1px solid rgba(214,161,58,.65);border-radius:999px;font:800 12px Arial,Helvetica,sans-serif;color:{GREEN_DARK} !important;text-decoration:none;">
              Deel via e-mail
            </a>
          </td>
        </tr>
      </table>

      <p style="margin:6px 0 14px;font:14px Arial,Helvetica,sans-serif;line-height:1.5;color:{MUTED};">Zelf ook twee keer per week positief nieuws ontvangen? <a href="https://positief-nieuws.nl/nieuwsbrief/" style="color:{GREEN_DARK} !important;text-decoration:underline;">Meld je gratis aan.</a></p>

      <p style="margin:8px 0 0 0;font:12px Arial,Helvetica,sans-serif;color:{MUTED};">
        <a href="{newsletter_online_url}" style="color:{GREEN_DARK} !important;text-decoration:underline;text-underline-offset:2px;">
          Lees deze editie online
        </a>
      </p>
    </div>
    """


def homepage_email_order(data, stories):
    stories = list(stories)
    # Same historical editorial override as both homepage renderers.
    if raw_edition_date(data) == "2026-10-08":
        priorities = {"telefoonvrije-school-meer-contact": 0, "berghof-verbindt-limburgse-natuur": 1}
        stories.sort(key=lambda item: priorities.get(item.get("article_slug"), 2))
    return stories


def email_pair(stories, data, own_pages=True):
    cells = ''.join(f'<td class="email-column" width="50%" valign="top" style="width:50%;padding:0 7px;vertical-align:top;">{article_html(item, data, own_pages)}</td>' for item in stories)
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;table-layout:fixed;border-collapse:collapse;"><tr>{cells}</tr></table>'


def build_body(data, nl, international, headlines):
    nl = homepage_email_order(data, nl)
    nl_html = article_html(nl[0], data, True, featured=True) + email_pair(nl[1:3], data)
    nl_html += section_header("Meer goed nieuws uit Nederland", "3 verhalen")
    nl_html += '<div style="height:16px"></div>' + ''.join(article_html(item, data, True) for item in nl[3:])
    world = ''.join(email_pair(international[i:i+2], data) for i in range(0, len(international), 2))
    briefing = ''.join(article_html(item, data) for item in headlines)
    preheader = esc(build_preheader(data, nl))
    return f"""<!-- buttondown-editor-mode: fancy -->
<style>@media(max-width:760px){{.story-intro{{display:none!important}}.email-column{{display:block!important;width:100%!important;padding:0!important}}.email-shell{{padding:20px 16px!important}}.email-title{{font-size:38px!important}}}}</style>
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;font-size:1px;line-height:1px;mso-hide:all;">{preheader}</div>
<div class="email-shell" style="width:100%;max-width:740px;margin:0 auto;box-sizing:border-box;background:{PAPER};padding:28px 28px;color:{INK};font-family:Arial,Helvetica,sans-serif;">
  <div style="padding:0 0 22px;border-bottom:1px solid #e1e9e5;">
    <a href="{esc(buttondown_edition_url(data))}" style="font:800 25px Arial,Helvetica,sans-serif;letter-spacing:-1px;color:{INK} !important;text-decoration:none;"><img src="{SITE_URL}sun-icon-512.png" width="32" height="32" alt="" style="display:inline-block;width:32px;height:32px;vertical-align:middle;margin-right:8px;">Positief nieuws</a>
  </div>
  <div style="padding:30px 0 26px;">
    <p style="margin:0 0 14px;font:700 12px Arial,Helvetica,sans-serif;color:{GREEN};">Editie van {esc(edition_date_text(data))}</p>
    <h1 class="email-title" style="margin:0 0 16px;font:900 52px Arial,Helvetica,sans-serif;line-height:1.04;letter-spacing:-.055em;color:{INK};">Positief <span style="color:#168268;">nieuws</span></h1>
    <p style="margin:0;font:15px Arial,Helvetica,sans-serif;line-height:1.65;color:{MUTED};">Twaalf positieve verhalen uit Nederland en de wereld. Plus drie ontwikkelingen om bij te blijven. Geen eindeloze nieuwsstroom.</p>
    <p style="margin:15px 0 0;font:12px Arial,Helvetica,sans-serif;color:{MUTED};">Elke maandag en donderdag · 6 uit Nederland · 6 uit de wereld · 3 korte actualiteiten</p>
  </div>
  {nl_html}
  <div style="margin-top:36px;">{section_header("Goed nieuws uit de wereld", "6 verhalen")}<div style="height:16px"></div>{world}</div>
  <div style="margin-top:30px;">{section_header("Wat je verder moet weten", "3 korte actualiteiten")}<div style="height:16px"></div>{briefing}</div>
  <div style="padding:32px 15px;margin-top:30px;border-top:1px solid #e1e9e5;text-align:center;">
    <h2 style="margin:0 0 9px;font:800 27px Arial,Helvetica,sans-serif;letter-spacing:-.04em;color:{INK};">Dit was het voor vandaag.<br>Je bent weer bij.</h2><p style="margin:0;font:14px Arial,Helvetica,sans-serif;color:{MUTED};">Geniet van je dag.</p>
  </div>
  {build_share_block(data)}
  <p style="margin:28px 0 0;text-align:center;font:11px Arial,Helvetica,sans-serif;color:{MUTED};">Positief nieuws · Dit gebeurt ook.</p>
  <p style="text-align:center;font:11px Arial,Helvetica,sans-serif;"><a href="{{{{ unsubscribe_url }}}}" style="color:{MUTED};text-decoration:underline;">Afmelden</a></p>
</div>"""


def build_subject(data):
    return f"Dit gebeurt ook · {edition_date_short_text(data)}"


def create_draft(api_key, subject, body, data, preheader):
    payload = {
        "subject": subject,
        "body": body,
        "status": "draft",
        "template": "naked",
        # Canonical blijft bewust zonder UTM-parameters.
        "canonical_url": edition_url(data),
        "description": preheader,
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
        # Gate before any external API mutation, including manual workflow runs.
        from editorial_check import check
        edition = raw_edition_date(data)
        dossier_path = Path("redactie") / f"{edition}.json"
        if not dossier_path.exists():
            raise ValueError("Redactioneel dossier ontbreekt; geen Buttondown-concept gemaakt.")
        selection_path = Path("selectie") / f"{edition}.json"
        pool_path = Path("selectie") / f"{edition}-kandidaten.json"
        selection = json.loads(selection_path.read_text(encoding="utf-8")) if selection_path.exists() else None
        pool = json.loads(pool_path.read_text(encoding="utf-8")) if pool_path.exists() else None
        report = check(data, json.loads(dossier_path.read_text(encoding="utf-8")), selection_review=selection, candidate_pool=pool)
        if not report["ready"]:
            raise ValueError("Redactionele controle: " + "; ".join(report["errors"]))
        subject = build_subject(data)
        preheader = build_preheader(data, nl)
        body = build_body(data, nl, international, headlines)
        draft = create_draft(api_key, subject, body, data, preheader)
    except Exception as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Buttondown-concept aangemaakt.")
    print(f"Onderwerp: {draft.get('subject', subject)}")
    print(f"Preview: {preheader}")
    print(f"ID: {draft.get('id', 'onbekend')}")
    print(f"Status: {draft.get('status', 'onbekend')}")


if __name__ == "__main__":
    main()
