#!/usr/bin/env python3

import html
import json
import os
import sys
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

NEWS_FILE = Path("nieuws.json")
KIT_URL = "https://api.kit.com/v4/broadcasts"
GITHUB_API = "https://api.github.com"
LAST_BUTTONDOWN_EDITION = "2026-11-23"
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
    """Inbox-preview: liefst redactioneel uit nieuws.json, anders twee verhalen naast het hoofdverhaal."""
    custom = (
        data.get("meta", {}).get("email_preheader")
        or data.get("edition", {}).get("email_preheader")
        or ""
    )
    custom = " ".join(str(custom).split()).strip()
    if custom:
        return custom[:180]

    titles = []
    for article in homepage_email_order(data, nl)[1:3]:
        title = " ".join(str(article.get("title") or "").split()).strip()
        if title:
            titles.append(title)

    if not titles:
        return "12 positieve verhalen + 3 belangrijke nieuwsitems om bij te blijven."

    preview = "Ook deze editie: " + " · ".join(titles)
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


def newsletter_edition_url(data):
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
        "utm_source": "kit",
        "utm_medium": "email",
        "utm_campaign": f"editie_{raw_date.replace('-', '_')}",
    }

    separator = "&" if "?" in clean_url else "?"
    return f"{clean_url}{separator}{urllib.parse.urlencode(params)}"


def newsletter_article_url(data, article):
    """Eigen artikelpagina met UTM-tracking voor de directe klik vanuit Kit."""
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
        "utm_source": "kit",
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
    raw_url = newsletter_article_url(data, article) if prefer_own_page and data and article.get("article_slug") else str(article.get("url") or "")
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
    # WhatsApp/e-mail binnenkomt niet ten onrechte als Kit toegeschreven.
    share_url = edition_url(data)

    # Alleen de directe klik vanuit deze nieuwsbrief krijgt Kit-UTM's.
    newsletter_online_url = newsletter_edition_url(data)

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
    note = (data.get('meta') or {}).get('personal_note') or {}
    personal_note = ''
    if note.get('text'):
        personal_note = f'<div style="margin:0 0 28px;padding:20px;background:#f0f5ee;border:1px solid #e1e9e5;border-radius:14px"><h2 style="margin:0 0 12px;font:700 22px Arial,Helvetica,sans-serif">{esc(note.get("title", ""))}</h2><p style="margin:0;font:15px/1.65 Arial,Helvetica,sans-serif">{esc(note["text"])}</p><p style="margin:12px 0 0;font:700 14px Arial,Helvetica,sans-serif">Tom</p></div>'
    preheader = esc(build_preheader(data, nl))
    weekday, _, edition_date = edition_date_text(data).partition(" ")
    edition_label = f"{weekday.capitalize()}editie" if edition_date else "Editie"
    intro = (data.get("meta") or {}).get("email_intro")
    if intro:
        intro_paragraphs = [p.strip() for p in intro.split("\n\n") if p.strip()]
    else:
        intro_paragraphs = [
            "Uit Nederland: " + " · ".join(article["title"] for article in nl[1:3]),
            "Uit de wereld: " + " · ".join(article["title"] for article in international[:2]),
        ]
    intro_html = "".join(
        f'<p style="margin:0 0 12px;font:16px/1.6 Arial,Helvetica,sans-serif;color:{INK};">{esc(paragraph)}</p>'
        for paragraph in intro_paragraphs
    )
    return f"""
<style>@media(max-width:760px){{.story-intro{{display:none!important}}.email-column{{display:block!important;width:100%!important;padding:0!important}}.email-shell{{padding:20px 16px!important}}}}</style>
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;font-size:1px;line-height:1px;mso-hide:all;">{preheader}{"&#8204;&nbsp;" * 100}</div>
<div class="email-shell" style="width:100%;max-width:740px;margin:0 auto;box-sizing:border-box;background:{PAPER};padding:28px 28px;color:{INK};font-family:Arial,Helvetica,sans-serif;">
  <div style="background:#ffffff;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-bottom:1px solid #e1e5e3;font:13px/1.5 Arial,Helvetica,sans-serif;color:#111713;">
      <tr>
        <td style="padding:12px 10px 12px 16px;"><strong style="font-size:14px;">{esc(edition_label)}</strong>&nbsp; {esc(edition_date)}</td>
        <td align="right" style="padding:12px 16px 12px 0;">{len(nl) + len(international)} verhalen · {len(headlines)} leestips</td>
      </tr>
    </table>
    <div style="padding:21px 16px 19px;">
      <a href="{esc(newsletter_edition_url(data))}" style="font:800 25px Arial,Helvetica,sans-serif;letter-spacing:-1px;color:{INK} !important;text-decoration:none;"><img src="{SITE_URL}sun-orange.png" width="32" height="32" alt="" style="display:inline-block;width:32px;height:32px;vertical-align:middle;margin-right:8px;">Positief nieuws</a>
      <p style="margin:7px 0 0 40px;font:14px Arial,Helvetica,sans-serif;color:{MUTED};">Dit gebeurt ook</p>
    </div>
  </div>
  <div style="padding:24px 0 17px;">
    {intro_html}
  </div>
  {personal_note}
  {nl_html}
  <div style="margin-top:36px;">{section_header("Goed nieuws uit de wereld", "6 verhalen")}<div style="height:16px"></div>{world}</div>
  <div style="margin-top:30px;">{section_header("Wat je verder moet weten", "3 korte actualiteiten")}<div style="height:16px"></div>{briefing}</div>
  <div style="padding:36px 12px 42px;margin-top:30px;text-align:center;background-color:#ffffff;background-image:radial-gradient(circle at center,#ffffff 0 95px,#f7eddb 96px,#faf7f1 97px 136px,#fcfbf8 137px 170px,#ffffff 171px);">
    <img src="{SITE_URL}sun-orange.png" width="48" height="48" alt="" style="display:block;width:48px;height:48px;margin:0 auto 24px;">
    <h2 style="margin:0 0 22px;font:800 30px/1.08 Arial,Helvetica,sans-serif;letter-spacing:-.04em;color:#111713;">Dit was het voor vandaag.<br>Je bent weer bij.</h2>
    <p style="margin:0;font:16px/1.4 Arial,Helvetica,sans-serif;color:#65756f;">Geniet van je dag.</p>
  </div>
  {build_share_block(data)}
  <p style="margin:28px 0 0;text-align:center;font:11px Arial,Helvetica,sans-serif;color:{MUTED};">Positief nieuws · Dit gebeurt ook.<br>{{{{ address }}}}</p>
  <p style="text-align:center;font:11px Arial,Helvetica,sans-serif;"><a href="{{{{ unsubscribe_url }}}}" style="color:{MUTED};text-decoration:underline;">Afmelden</a></p>
</div>"""


def build_subject(data):
    stories = homepage_email_order(data, data.get("nl", []))
    if stories:
        title = " ".join(str(stories[0].get("title") or "").split())
        if title:
            return title
    return f"Positief nieuws · {edition_date_short_text(data)}"


def request_json(url, method, headers, payload=None):
    request = urllib.request.Request(
        url, method=method, headers={**headers, "Accept": "application/json",
                                     "Content-Type": "application/json"},
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # Response bodies can contain sensitive input. Expose just the status.
        raise RuntimeError(f"{method} {urllib.parse.urlsplit(url).hostname}: HTTP {error.code}") from None


def find_broadcast(api_key, marker):
    headers = {"X-Kit-Api-Key": api_key}
    params = {"slim": "true"}
    seen_cursors = set()
    matches = []
    while True:
        result = request_json(f"{KIT_URL}?{urllib.parse.urlencode(params)}", "GET", headers)
        matches.extend(item for item in result["broadcasts"] if item.get("description") == marker)
        pagination = result["pagination"]
        if not pagination["has_next_page"]:
            break
        cursor = pagination["end_cursor"]
        if not cursor or cursor in seen_cursors:
            raise ValueError("Kit-paginering onvolledig")
        seen_cursors.add(cursor)
        params["after"] = cursor
    if len(matches) > 1:
        raise ValueError(f"Meerdere Kit-broadcasts hebben editie-ID {marker}")
    return matches[0] if matches else None


def claim_edition(marker):
    """Keep a durable claim across reruns, including a crash after the POST."""
    repo = os.environ["GITHUB_REPOSITORY"]
    headers = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
    request_json(f"{GITHUB_API}/repos/{repo}/git/refs", "POST", headers, {
        "ref": f"refs/tags/{marker}",
        "sha": os.environ["PN_DEPLOYED_SHA"],
    })


def draft_payload(subject, body, edition, preheader, marker):
    sender = os.environ["KIT_SENDER_EMAIL"]
    if not sender.lower().endswith("@positief-nieuws.nl"):
        raise ValueError("KIT_SENDER_EMAIL moet een afzender op positief-nieuws.nl zijn")
    if "{{ unsubscribe_url }}" not in body:
        raise ValueError("Kit-afmeldlink ontbreekt")
    payload = {
        "email_address": sender,
        "subject": subject,
        "preview_text": preheader,
        "content": body,
        "description": marker,
        "published_at": f"{edition}T00:00:00+01:00",
        "send_at": None,
        "public": False,
    }
    if os.environ.get("KIT_EMAIL_TEMPLATE_ID"):
        payload["email_template_id"] = int(os.environ["KIT_EMAIL_TEMPLATE_ID"])
        payload["allow_starting_point"] = True
    return payload


def create_draft(api_key, subject, body, data, preheader, *, trial=False):
    edition = raw_edition_date(data)
    marker = f"pn-{edition}" + ("-proef" if trial else "")
    existing = find_broadcast(api_key, marker)
    if existing:
        return existing

    payload = draft_payload(subject, body, edition, preheader, marker)
    if not trial:
        # Only the run that claims this edition may POST. If a claim already
        # exists and Kit has no match, stop for reconciliation rather than retry.
        try:
            claim_edition(marker)
        except RuntimeError:
            existing = find_broadcast(api_key, marker)
            if existing:
                return existing
            raise

    try:
        result = request_json(KIT_URL, "POST", {"X-Kit-Api-Key": api_key}, payload)["broadcast"]
        if not result.get("id") or result.get("status") != "draft" or result.get("public") is not False or result.get("send_at") is not None:
            raise ValueError("Kit bevestigde de conceptstatus niet")
        return result
    except (OSError, RuntimeError, KeyError, ValueError):
        existing = find_broadcast(api_key, marker)
        if existing:
            return existing
        raise RuntimeError(f"Kit-concept voor {marker} niet bevestigd. Controleer Kit en de claim vóór een nieuwe poging.") from None


def is_regular_release(event, current, previous, repository):
    run = event.get("workflow_run", {})
    return (
        event.get("action") == "completed"
        and run.get("conclusion") == "success"
        and run.get("event") in {"dynamic", "push"}
        and run.get("head_branch") == "main"
        and (run.get("head_repository") or {}).get("full_name") == repository
        and current > LAST_BUTTONDOWN_EDITION
        and current != previous
    )


def check_live(data, stories):
    edition = raw_edition_date(data)
    paths = ["", f"edities/{edition}/"] + [
        f"artikelen/{edition}/{item['article_slug']}/" for item in stories
    ]
    if len(set(paths)) != 14:
        raise ValueError("Verwacht 14 verschillende publicatiepagina’s")
    from concurrent.futures import ThreadPoolExecutor

    def verify(path):
        url = SITE_URL + path
        request = urllib.request.Request(
            f"{url}?pn_internal=1&pn_verify={os.environ['PN_DEPLOYED_SHA']}",
            headers={"Cache-Control": "no-cache", "User-Agent": "PositiefNieuws-ReleaseControle/1.0"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            page = response.read().decode("utf-8")
            if response.status != 200 or response.url.split("?")[0] != url or edition not in page:
                raise ValueError(f"Juiste editie ontbreekt op /{path}")
            if path == "" and f"/edities/{edition}/" not in page:
                raise ValueError("Editielink ontbreekt op de homepage")

    def verify_current_data():
        request = urllib.request.Request(
            f"{SITE_URL}nieuws.json?pn_verify={os.environ['PN_DEPLOYED_SHA']}",
            headers={"Cache-Control": "no-cache"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            if json.load(response) != data:
                raise ValueError("De live homepage gebruikt andere editiegegevens")

    with ThreadPoolExecutor(max_workers=7) as pool:
        for attempt in range(8):
            try:
                verify_current_data()
                list(pool.map(verify, paths))
                return
            except (OSError, ValueError) as error:
                if attempt == 7:
                    raise RuntimeError(f"Livecontrole mislukt voor editie {edition}: {type(error).__name__}") from None
                time.sleep(10)


def run_release(event, current, previous, repository):
    data, nl, international, headlines = current
    edition = raw_edition_date(data)
    if not is_regular_release(event, edition, previous, repository):
        print("Geen nieuwe reguliere productie-editie. Kit is niet aangeroepen.")
        return None

    from editorial_check import check
    dossier = json.loads((Path("redactie") / f"{edition}.json").read_text(encoding="utf-8"))
    report = check(data, dossier, require_selection=False)
    if not report["ready"]:
        raise ValueError("Redactionele controle: " + "; ".join(report["errors"]))
    if Path("edities", f"{edition}.json").read_bytes() != NEWS_FILE.read_bytes():
        raise ValueError("Archief en homepage gebruiken verschillende editiebestanden")
    check_live(data, nl + international)
    api_key = os.environ.get("KIT_API_KEY")
    if not api_key:
        raise ValueError("GitHub-secret KIT_API_KEY ontbreekt")
    return create_draft(
        api_key, build_subject(data), build_body(data, nl, international, headlines),
        data, build_preheader(data, nl),
    )


def main():
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        deployed = os.environ["PN_DEPLOYED_SHA"]
        previous = json.loads(subprocess.check_output(
            ["git", "show", f"{deployed}^:nieuws.json"], text=True,
        ))
        draft = run_release(event, load_news(), raw_edition_date(previous), os.environ["GITHUB_REPOSITORY"])
        if draft:
            print(f"Kit-broadcast {int(draft['id'])} aanwezig voor deze editie.")
    except Exception as error:
        print(f"::error::Kit-conceptcontrole mislukt. {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
