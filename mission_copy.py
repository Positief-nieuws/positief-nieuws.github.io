"""Mission copy shared by existing pages and future site builds.

Only presentation copy changes; newsletter POSTs and editorial content stay intact.
"""
from pathlib import Path
import re

MISSION = 'Positief nieuws wil het nieuwslandschap meer in balans brengen door ook oplossingen, vooruitgang en hoopvolle ontwikkelingen zichtbaar te maken.'
PERSONAL = 'Ik ben Tom, de initiatiefnemer van Positief nieuws. Met deze site wil ik meer ruimte geven aan wat er óók goed gaat, naast het nieuws over problemen en crises.'
INVITE = 'Ken je iemand die dit ook wil lezen? Deel dit verhaal via WhatsApp, e-mail of de link hieronder. Zo help je oplossingen en vooruitgang meer mensen in Nederland te bereiken.'
SHARE = 'Deel Positief nieuws met iemand die een breder nieuwsbeeld waardeert. Zo help je oplossingen, vooruitgang en hoopvolle ontwikkelingen meer mensen in Nederland te bereiken.'


def enhance(markup, path):
    path = Path(path)
    if path == Path('index.html'):
        markup = markup.replace('Vandaag weer twaalf positieve verhalen uit Nederland en de wereld, plus drie ontwikkelingen om bij te blijven. Veel leesplezier en daarna weer lekker verder met je dag.', 'Ook oplossingen en vooruitgang verdienen aandacht. Lees twaalf positieve verhalen uit Nederland en de wereld, plus drie ontwikkelingen om bij te blijven. Met bronnen en nuance, in een paar minuten.')
        markup = markup.replace('Bij ieder verhaal vind je bronnen om verder te lezen. Zo zie je wat er goed gaat, met ruimte voor nuance en zonder eindeloze nieuwsstroom.', MISSION + ' Bij ieder verhaal vind je bronnen en nuance. Problemen blijven in beeld; hoopvolle ontwikkelingen krijgen ook de ruimte.')
        markup = markup.replace('Het nieuws bestaat niet alleen uit oorlog, politieke ruzie, ongelukken en crises. Iedere dag gaan er ook dingen vooruit: in wetenschap, gezondheid, natuur, technologie en gewoon tussen mensen. Alleen krijgen die verhalen vaak minder aandacht.', MISSION + ' We ontkennen problemen niet en maken ontwikkelingen niet mooier dan ze zijn.</p><p>' + PERSONAL)
        pending_copy = """<p>Dank je voor je belangstelling voor Positief nieuws.</p>
          <p><strong>Check nu je inbox en bevestig je e-mailadres via de link in de mail.</strong></p>
          <p>Daarna ben je helemaal klaar en kun je twee keer per week genieten van oplossingen en vooruitgang in je mail.</p>
          <p>Krijg je geen mail? Kijk in je spamfolder. Nog steeds niets? <a href="/nieuwsbrief/">Probeer opnieuw met een geldig e-mailadres.</a></p>
          <!-- mission:pending --><p>Wil je ons helpen? <a href="/nieuwsbrief/">Deel de inschrijfpagina</a> met iemand die dit nieuws ook waardeert.</p>"""
        markup = re.sub(
            r'(<div class="signup-pending-copy">).*?(<div class="signup-pending-actions">)',
            lambda match: match[1] + '\n          ' + pending_copy + '\n        </div>\n\n        ' + match[2],
            markup, count=1, flags=re.S,
        )
        if '<!-- mission:confirmed -->' not in markup:
            markup = markup.replace('<h1 class="page-title">Bedankt voor het bevestigen</h1>', '<h1 class="page-title">Bedankt voor het bevestigen</h1><!-- mission:confirmed --><p>Fijn dat je belangstelling hebt voor een breder nieuwsbeeld. Wil je oplossingen en vooruitgang verder helpen? <a href="/nieuwsbrief/">Deel de inschrijfpagina</a> met iemand die dit ook waardeert.</p>')
        confirmed_share = '<!-- mission:confirmed-share --><p>Wil je ons helpen? <a href="/nieuwsbrief/">Deel de inschrijfpagina</a> met iemand die dit nieuws ook waardeert.</p>'
        def add_confirmed_share(match):
            section = match[0]
            if '<!-- mission:confirmed-share -->' not in section:
                section = section.replace('<div class="signup-pending-actions">', confirmed_share + '\n        <div class="signup-pending-actions">', 1)
            return section
        markup = re.sub(r'<section id="signup-confirmed-view".*?</section>', add_confirmed_share, markup, count=1, flags=re.S)
    elif path == Path('over/index.html'):
        markup = markup.replace('Positief nieuws laat zien wat er óók gebeurt, zonder het belangrijke nieuws weg te laten. Een compacte selectie om in een paar minuten bij te zijn en daarna weer verder te gaan.', MISSION)
        if '<!-- mission:tom -->' not in markup:
            markup = markup.replace('<h2>Waarom Positief nieuws bestaat</h2>', '<!-- mission:tom --><h2>Waarom ik Positief nieuws maak</h2><p>' + PERSONAL + '</p>')
        if '<!-- mission:contribute -->' not in markup:
            markup = markup.replace('<h2>Correcties en contact</h2>', '<!-- mission:contribute --><h2>Help dit nieuws verder</h2><p>' + SHARE + ' Stuur bijvoorbeeld de link naar een verhaal dat je raakte naar een vriend, familielid of collega.</p><p>Zie je een hoopvolle ontwikkeling die aandacht verdient? <a href="/tip/">Tip de redactie</a>. Ik bekijk graag of het verhaal bij de selectie past.</p><h2>Correcties en contact</h2>')
        markup = markup.replace('Lees hoe Positief nieuws verhalen selecteert, bronnen gebruikt en een compacte mix maakt van positief nieuws en drie belangrijke onderwerpen.', 'Lees waarom Tom Positief nieuws maakt: meer balans in het nieuws, met oplossingen, vooruitgang, betrouwbare bronnen en ruimte voor nuance.')
    elif path == Path('nieuwsbrief/index.html'):
        markup = markup.replace('Er gaat meer goed dan je denkt. Ontvang twee keer per week een rustige selectie nieuws uit Nederland en de wereld. In een paar minuten ben je weer bij.', 'Geef ook oplossingen en vooruitgang een plek in je nieuwsbeeld. Ontvang twee keer per week een rustige selectie uit Nederland en de wereld. Met bronnen en nuance, zonder problemen uit het oog te verliezen.')
    if path.parts[0] == 'artikelen':
        markup = markup.replace('Ken je iemand die dit ook wil lezen? Deel dit verhaal.', INVITE)
    if path == Path('index.html') and '<!-- mission:about-share -->' not in markup:
        markup = markup.replace('<p><a href="#nieuwsbrief" id="about-newsletter-link">', '<!-- mission:about-share --><p>' + SHARE + ' Een nieuwstip? <a href="/tip/">Laat het weten</a>.</p><p><a href="#nieuwsbrief" id="about-newsletter-link">')
    return markup
