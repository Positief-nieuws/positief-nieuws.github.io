"""Reproduce the owner-selected, unapproved 5 November editorial concept. No publication/API writes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = '2026-11-05'

def article(slug, candidate, title, basic, teaser, category, url, source, sid, published, paragraphs, query, alt, primary=None):
    return dict(article_slug=slug,candidate_id=candidate,title=title,email_title=title,
                title_alternative=basic,teaser=teaser,category=category,url=url,
                primary_url=primary or url,source=source,source_id=sid,published=published,
                article_body=paragraphs,image_query=query,image_alt=alt)

nl = [
article('gli-afvallen-kwaliteit-van-leven','fda668c35ffe',
 'Leefstijlbegeleiding helpt deelnemers afvallen én beter leven',
 'RIVM: GLI-deelnemers verliezen meer gewicht dan niet-deelnemers',
 'Een nieuwe vergelijking laat extra gewichtsverlies zien. Ook de ervaren kwaliteit van leven verbetert tijdens het tweejarige programma.',
 'Gezondheid','https://www.rivm.nl/nieuws/gli-helpt-bij-afvallen-deelnemers-ervaren-betere-kwaliteit-van-leven','RIVM','rivm','2026-11-03',[
 'Werken aan een gezondere leefstijl met begeleiding levert deelnemers gemiddeld meer gewichtsverlies op dan zonder deelname. Dat concludeert het RIVM in de nieuwe GLI-monitor. GLI staat voor Gecombineerde Leefstijlinterventie, een programma voor mensen met overgewicht of obesitas.',
 'De onderzoekers vergeleken deelnemers met niet-deelnemers van wie de huisarts herhaaldelijk het gewicht had vastgelegd. De GLI-groep verloor gemiddeld 2,5 kilo meer. Na twee jaar meldde de groep ook een betere kwaliteit van leven, zowel met als zonder gewichtsverlagende medicijnen.',
 'De uitkomsten verschillen per persoon. Van de GLI-deelnemers verloor 37 procent minstens vijf procent van het lichaamsgewicht. Bij de combinatie met medicijnen was dat 62 procent. De vergelijking betekent niet dat iedereen hetzelfde resultaat mag verwachten.',
 'Het onderzoek geeft zicht op veranderingen tijdens het traject. Of mensen hun aangepaste leefstijl na afronding volhouden, is nog niet bekend. Wel daalde de uitval: van 49 procent bij de starters uit 2019 naar 35 procent bij de starters uit 2023.'
 ],'id:8830068','Illustratief beeld van bewegen; geen deelnemers aan het RIVM-onderzoek.'),
article('carisia-kees-streekwinkel','afe5ff1fda55',
 'Carisia en Kees bouwen aan een bloeiende streekwinkel',
 'Dove ondernemers openen een grotere streekwinkel in Elst',
 'Bijna tien jaar na hun start hebben de dove ondernemers een nieuwe winkel, vaste klanten en ruimte voor hun volgende plannen.',
 'Mens','https://www.deondernemer.nl/actueel/retail/dove-ondernemers-kees-carisia-t-jong-runnen-succes-winkel~c2b4c48c','De Ondernemer / de Gelderlander','de-ondernemer','2026-11-04',[
 'Carisia en Kees ’t Jong hebben in Elst een nieuwe plek voor hun streekwinkel De Lingegaerdt. Het pand is ruimer en overzichtelijker. Voor het dove ondernemerspaar is dat laatste belangrijk: vanuit hun kantoortje kunnen ze de winkel goed overzien.',
 'Bijna tien jaar geleden verruilden ze hun vaste banen voor de winkel. Inmiddels verkopen ze lokale producten aan een trouwe klantenkring en werken er ook dove en slechthorende vrijwilligers. De verhuizing volgde op een lange periode van vergunningen en voorbereiding.',
 'Communicatie blijft dagelijks aandacht vragen. Bellen kunnen ze niet zelf, en bij gesprekken maakt een gebarentolk veel verschil. Volgens het stel worden te weinig tolkuren vergoed om alle werkdagen te dekken. Daarom plannen ze belangrijke afspraken zoveel mogelijk bij elkaar.',
 'Hun succes betekent dus niet dat alle belemmeringen verdwenen zijn. Wel hebben ze een bedrijf opgebouwd waarin persoonlijk contact een centrale plaats heeft. Klanten worden aangekeken en krijgen de tijd. De grotere winkel biedt bovendien ruimte om verder te ontwikkelen, al zijn een theehuis en belevenistuin voorlopig nog toekomstplannen.'
 ],'id:673184','Illustratieve foto van streekproducten; niet de winkel van Carisia en Kees.'),
article('palingen-veilig-langs-maurik','b36647adfa79',
 'Vissers helpen duizenden palingen veilig langs een waterkrachtcentrale',
 'Ruim 9.000 kilo schieraal overgezet bij Maurik',
 'Bij Maurik is in twee maanden ruim 9.000 kilo volwassen paling vóór de centrale opgevangen en aan de andere kant vrijgelaten.',
 'Natuur & klimaat','https://www.gld.nl/nieuws/8542571/vissers-redden-duizenden-palingen-van-gevaarlijke-hindernis','Omroep Gelderland','omroep-gelderland','2026-11-03',[
 'Ruim 9.000 kilo volwassen paling is de afgelopen twee maanden veilig langs de waterkrachtcentrale bij Maurik geholpen. Beroepsvissers vangen de trekkende dieren vóór de centrale op en zetten ze aan de andere kant terug. Volgens hen is de hoeveelheid een lokaal record.',
 'Deze volwassen paling, schieraal genoemd, trekt vanuit de Nederlandse binnenwateren naar de Sargassozee om zich voort te planten. Onderweg vormen onder meer gemalen, stuwen en turbines hindernissen. De overzetactie voorkomt dat de gevangen dieren door deze centrale hoeven.',
 'Het werk is onderdeel van Paling Over de Dijk, dat sinds 2011 loopt. Met grote fuiken onderscheppen de vissers de aal. Andere gevangen vissoorten gaan terug het water in.',
 'Het record is geen aanwijzing dat de palingstand ineens herstelt. Dit jaar bleef de waterstand relatief laag, waardoor de stuw geen vrije doorgang bood. Er moest daardoor meer worden overgezet. De actie helpt individuele dieren voorbij één obstakel; de volledige route naar zee blijft een grotere opgave.'
 ],'id:8975861','Illustratief beeld van een Nederlandse rivier; niet de overzetactie in Maurik.',primary='https://nos.nl/artikel/2637862-vissers-helpen-duizenden-palingen-veilig-oversteken-bij-waterkrachtcentrale-maurik'),
article('zonvarken-lagere-emissies','ec691c996253',
 'Meer ruimte voor varkens, met minder uitstoot in onderzochte stallen',
 'WUR meet lagere emissies bij drie Zonvarkenbedrijven',
 'Metingen aan het Zonvarken-concept wijzen op lagere ammoniak- en methaanuitstoot. Het onderzoek omvat drie bedrijven.',
 'Natuur & klimaat','https://www.wur.nl/nl/nieuws/zonvarken-meer-aandacht-voor-dierenwelzijn-en-fors-lagere-emissies','Wageningen University & Research','wageningen-university-research','2026-11-03',[
 'Varkens meer leefruimte en een buitenuitloop geven kan samengaan met lagere uitstoot. Onderzoekers van Wageningen University & Research deden metingen op drie bedrijven met het Zonvarken-concept. Dat systeem probeert emissies bij de bron te beperken.',
 'De aanpak scheidt urine en vaste mest en voert mest regelmatig af. Daardoor kunnen minder ammoniak en methaan ontstaan. Op basis van de metingen berekenden de onderzoekers voor een gesloten bedrijf met vijftig zeugen 61 procent minder ammoniak en 89 procent minder methaan dan bij het conventionele vergelijkingssysteem.',
 'Die percentages vragen context. Ze zijn berekend uit een beperkte praktijkstudie, geen garantie voor iedere varkensstal. Ook blijft de buitenuitloop een aandachtspunt: waar dieren op een dichte vloer urineren, kan ammoniak vrijkomen.',
 'WUR wil onder meer mestafvoer, schoonhouden en voeding verder onderzoeken. Ook de meetmethode moet verder worden ontwikkeld en gevalideerd. De huidige uitkomsten bieden daarmee een onderbouwde richting voor verbetering, zonder dat het stalsysteem al als overal bewezen oplossing kan worden beschouwd.'
 ],'id:3386356','Illustratieve foto van varkens; niet een van de drie onderzochte bedrijven.'),
article('dienstenexport-banen-nederland','e345527dae27',
 'Dienstenexport draagt een steeds groter deel van de Nederlandse exportbanen',
 'CBS: diensten leveren ruim drie kwart van groei in exportwerkgelegenheid',
 'Sinds 2010 groeide de werkgelegenheid dankzij export vooral door diensten, zoals ICT en zakelijke ondersteuning.',
 'Economie','https://www.cbs.nl/nl-nl/nieuws/2026/45/export-van-diensten-levert-meer-op-en-creeert-meer-banen','CBS','cbs','2026-11-04',[
 'Nederlandse export draait allang niet alleen om goederen. Nieuwe CBS-cijfers laten zien hoe belangrijk diensten zijn geworden voor de werkgelegenheid. In 2025 hing de uitvoer van goederen en diensten samen met ongeveer 2,6 miljoen voltijdbanen.',
 'Dat waren 760.000 voltijdbanen meer dan in 2010. Ruim drie kwart van die groei kwam voor rekening van dienstenexport. Denk aan ICT, juridisch advies en andere zakelijke diensten. Inmiddels hangt ongeveer de helft van alle exportgerelateerde werkgelegenheid samen met diensten.',
 'Ook per euro uitvoerwaarde blijft bij diensten relatief veel waarde in Nederland: 64 cent in 2025. Voor in Nederland gemaakte goederen was dat 53 cent, voor wederuitvoer 13 cent. Wederuitvoer betreft goederen die grotendeels elders zijn gemaakt en via Nederland verder reizen.',
 'Dit zijn ontwikkelingen over vijftien jaar, geen plotselinge banengroei van deze week. Bovendien bleef het aandeel van de totale exportverdiensten in de economie sinds 2015 redelijk stabiel. De nieuwe cijfers laten vooral zien dat de samenstelling verandert en dat kennis en dienstverlening een grote rol spelen.'
 ],'id:569121','Illustratief beeld van dienstverlening; geen personen uit het CBS-onderzoek.'),
article('levensverhalen-psychische-behandeling','f3db2fc710f2',
 'Het eigen levensverhaal krijgt een plek in psychische behandeling',
 'UT-onderzoek verkent levensverhalen bij persoonlijkheidsstoornissen',
 'Een nieuwe aanpak helpt deelnemers hun ervaringen, kwaliteiten en toekomst te onderzoeken. De eerste evaluaties geven aanknopingspunten.',
 'Gezondheid','https://www.utwente.nl/nl/bms/nieuws/2026/10/1251275/niet-alleen-klachten-behandelen-levensverhalen-helpen-bij-psychisch-herstel','Universiteit Twente','universiteit-twente','2026-10-29',[
 'Wie ben je, wat heeft je gevormd en welke kant wil je op? Zulke vragen krijgen een plaats in een aanpak voor mensen met een persoonlijkheidsstoornis. Promotieonderzoek aan de Universiteit Twente laat zien hoe het levensverhaal de behandeling kan ondersteunen.',
 'Psycholoog en psychotherapeut Silvia Pol ontwikkelde een checklist waarmee behandelaren verhalen systematisch kunnen bekijken. Die geeft aanknopingspunten voor hoe iemand zichzelf, relaties en de toekomst ervaart. Dat kan helpen om behandelkeuzes beter aan te laten sluiten.',
 'Samen met andere deskundigen ontwikkelde Pol ook de groepsinterventie Een sterk verhaal. Deelnemers onderzoeken hun ervaringen, met aandacht voor moeilijke gebeurtenissen én voor eigen kracht en mogelijkheden. De eerste evaluaties wijzen op bruikbaarheid en mogelijke bijdragen aan zelfinzicht en eigen regie.',
 'Het gaat om vroege bevindingen, niet om bewijs dat deze aanpak voor iedereen werkt of andere behandelingen kan vervangen. De waarde ligt in het bredere perspectief: naast klachtenvermindering aandacht geven aan de manier waarop iemand betekenis, richting en samenhang in het eigen leven ervaart.'
 ],'id:849825','Illustratief beeld van schrijven; geen deelnemer aan de onderzochte behandeling.'),
]

world = [
article('corvo-licht-uit-zeevogels','63368e1e7cff',
 'Op Corvo gaat het licht uit zodat jonge zeevogels de oceaan vinden',
 'Corvo dooft straatverlichting tijdens de najaarstrek van jonge zeevogels',
 'Bewoners op het Azoreneiland doven straatlampen en helpen gestrande jonge vogels verder op hun eerste tocht naar zee.',
 'Natuur & klimaat','https://www.goodnewsnetwork.org/islands-near-portugal-turn-off-lights-to-protect-seabird-fledglings-every-oct/','Good News Network','good-news-network','2026-11-01',[
 'Op het Portugese eiland Corvo blijven straatlampen in een kwetsbare periode voor jonge zeevogels meerdere nachten uit. De dieren verlaten in het najaar hun nest en zoeken in het donker de oceaan op. Kunstlicht kan hen daarbij desoriënteren.',
 'De eilandbewoners helpen op twee manieren. Door verlichting te doven beperken ze een bron van verwarring. Daarnaast zoeken vrijwilligers naar jonge vogels die toch op de grond belanden. Die kunnen herstellen voordat ze weer bij zee worden vrijgelaten.',
 'De aanpak is een samenwerking van bewoners, het gemeentebestuur en vogelbeschermers. Het is geen nieuw experiment van deze week: Corvo doet dit al jaren. De actuele berichtgeving laat zien hoe de gemeenschap de jaarlijkse uittocht ook dit najaar begeleidt.',
 'Het vaak genoemde totaal van ruim 30.000 geredde vogels betreft reddingsacties op de Azoren over meerdere jaren. Dat aantal mag niet worden toegeschreven aan alleen het uitschakelen van lampen op Corvo. Wel laat de aanpak zien hoe een dorp zijn verlichting kan aanpassen aan de dieren waarmee het de kust deelt.'
 ],'id:6543041','Illustratief beeld van de zee bij schemering; geen foto van Corvo of de reddingsactie.'),
article('siliconen-grondstof-terugwinnen','7100a6abe994',
 'Van oude siliconen terug naar grondstof voor nieuw materiaal',
 'TU Berlin breekt gebruikte siliconen af tot hun industriële bouwsteen',
 'Onderzoekers winnen in het laboratorium een belangrijke grondstof terug uit gebruikte siliconen. Veilig opschalen is de volgende uitdaging.',
 'Energie & innovatie','https://idw-online.de/en/news879857','TU Berlin via idw','tu-berlin','2026-10-28',[
 'Een versleten siliconenbakvorm bevat materiaal dat hitte en chemische invloeden goed weerstaat. Precies die stevigheid maakt recycling lastig. Een team van de Technische Universität Berlin heeft nu gebruikte siliconen afgebroken tot een belangrijke grondstof voor de productie van nieuwe siliconen.',
 'Het team testte de methode aan alledaagse producten. Bij afzonderlijke materialen werd tot 99 procent van de beoogde grondstof teruggewonnen; bij een mengsel van gebruikte producten was dat 86 procent. Daarmee gaat het om meer dan alleen een theoretische reactie.',
 'De onderzoekers gebruiken een katalysator en een stof die tijdens de reactie fosgeen afgeeft. Dat gas is zeer giftig. Het proces hoort daarom thuis in gecontroleerde chemische installaties, en voor toepassing zijn verdere veiligheids- en zuiveringsstappen nodig.',
 'De publicatie beschrijft laboratoriumonderzoek. Er staat nog geen grootschalige recyclingketen voor afgedankte siliconen. De bereikte stap is dat het materiaal kan worden teruggebracht tot een bruikbare bouwsteen. Of dat ook veilig, betaalbaar en milieugunstig op grote schaal kan, moet verder worden uitgezocht.'
 ],'id:3498584','Illustratief laboratoriumbeeld; niet de installatie uit het Berlijnse onderzoek.'),
article('belfast-robot-complexe-operaties','cd3887213fef',
 'Operatierobot in Belfast al ingezet bij 130 complexe operaties',
 'Belfast gebruikt robotondersteuning bij complexe gynaecologische chirurgie',
 'De techniek is sinds mei in gebruik. De 130 behandelde patiënten vormen een concreet resultaat binnen de gynaecologische zorg.',
 'Gezondheid','https://www.bbc.co.uk/news/articles/c98rz8v5rem0o','BBC','bbc','2026-11-02',[
 'In Belfast City Hospital is robotondersteunde chirurgie inmiddels gebruikt bij 130 patiënten die een complexe gynaecologische operatie nodig hadden. Het Noord-Ierse ministerie van Volksgezondheid bevestigt dat de techniek sinds mei 2026 in gebruik is.',
 'De chirurg bestuurt het systeem. De robot opereert dus niet zelfstandig. De toepassing is onder meer relevant voor ingewikkelde ingrepen in het bekkengebied, zoals bij endometriose. Daarbij groeit weefsel dat op baarmoederslijmvlies lijkt buiten de baarmoeder, met mogelijk ernstige pijn en andere klachten.',
 'Het ministerie kondigde daarnaast 1,95 miljoen pond aan voor endometriosezorg. Dat geld is bestemd voor specialistische centra en lokale ondersteuning. Die investering is een volgende stap; de 130 uitgevoerde operaties zijn het al bereikte resultaat.',
 'De bredere gynaecologische wachtlijsten zijn volgens het ministerie afgenomen. Uit die cijfers volgt niet dat de robot daarvan alleen de oorzaak is: ook extra spreekuren, diagnostiek en behandelcapaciteit spelen mee. Het hoopgevende nieuws is de beschikbaarheid en het daadwerkelijke gebruik van een aanvullende operatietechniek, zonder te suggereren dat de lange wachttijden al verdwenen zijn.'
 ],'id:7839395','Illustratieve foto van een operatiekamer; niet het robotplatform in Belfast.',primary='https://www.health-ni.gov.uk/news/ps195m-investment-endometriosis-services'),
article('china-mangroven-vogelsoorten','a38bcf079551',
 'Waar Chinese mangrovebossen uitbreiden, verschijnen meer vogelsoorten',
 'Onderzoek beschrijft uitbreiding van mangroven en geregistreerde vogeldiversiteit in China',
 'Nieuw beschreven onderzoek over 1998 tot 2020 laat groei van mangrovegebied en een stijging van het aantal geregistreerde vogelsoorten zien.',
 'Natuur & klimaat','https://e360.yale.edu/digest/china-mangrove-restoration-bird-species','Yale Environment 360','yale-environment-360','2026-11-03',[
 'Langs de Chinese kust zijn mangrovebossen uitgebreid na grote verliezen in de vorige eeuw. Onderzoek dat Yale Environment 360 beschrijft, laat zien dat tegelijk meer vogelsoorten in deze gebieden werden geregistreerd.',
 'De vergelijking beslaat 1998 tot 2020. In die periode nam het geregistreerde aantal soorten toe van 148 tot 397. Mangroven groeien op de grens van land en zee. Hun wortels bieden structuur aan het kustgebied, waar allerlei dieren voedsel en beschutting vinden.',
 'Er is geen eenvoudige oorzaak voor de groei van het bosareaal. China plantte mangroven aan en beschermde ze met regelgeving. Ook opwarming speelde mee, doordat bomen zich verder naar het noorden konden verspreiden. Het onderzoek maakt bovendien geen afzonderlijke vergelijking tussen aangeplante en natuurlijke bossen.',
 'De uitkomst mag daarom niet worden gelezen als bewijs dat elke aanplant dezelfde natuurwinst geeft, of dat klimaatverandering gunstig is voor de natuur. Het positieve resultaat is specifieker: na eerdere verliezen kwam er mangrovegebied bij en werd er een grotere verscheidenheid aan vogels waargenomen.'
 ],'id:249830','Illustratief beeld van mangrovewortels; niet een van de Chinese meetlocaties.',primary='https://www.cell.com/the-innovation/fulltext/S2666-6758(26)00147-5'),
article('esk-valley-samen-leven','40f66591d43d',
 'In dit Engelse dorp wonen en werken mensen met en zonder beperking samen',
 'Reportage belicht het dagelijks leven in Esk Valley Camphill Community',
 'Negentien huishoudens delen maaltijden, werk en verantwoordelijkheid. Een nieuwe reportage laat zien hoe die gemeenschap dagelijks functioneert.',
 'Mens','https://www.positive.news/society/what-if-we-stopped-treating-social-care-like-a-service/','Positive News','positive-news','2026-11-03',[
 'Samen eten, werken in de tuin of iets maken in een werkplaats: in Esk Valley Camphill Community horen zulke activiteiten bij het dagelijks leven. Mensen met en zonder verstandelijke beperking delen er huizen en verantwoordelijkheden.',
 'Een nieuwe reportage van Positive News beschrijft de gemeenschap in Noord-Engeland van binnenuit. De schrijver woonde er drie maanden als vrijwilliger. Hij zag hoe bewoners die ondersteuning krijgen ook zelf anderen helpen, bijvoorbeeld door een nieuwkomer wegwijs te maken.',
 'De gemeenschap bestaat uit negentien huishoudens. Ook de eigen website beschrijft een combinatie van samen wonen, begeleiding en werk in onder meer een bakkerij, tuin en houtwerkplaats. Het doel is dat mensen op hun eigen manier bijdragen aan het geheel.',
 'Dit is een inkijk in een bestaande woonvorm, geen bewijs dat deze aanpak voor iedereen beter werkt. De reportage is persoonlijk en de schrijver raakte betrokken bij de gemeenschap. Juist met die beperking erbij is het een interessante leestip: hoe kan ondersteuning ruimte laten voor wederkerigheid, vertrouwde relaties en het gevoel ergens nodig te zijn?'
 ],'id:2247391','Illustratief beeld van samenkomen; niet de bewoners van Esk Valley.',primary='https://www.eskvalleycamphill.org/our-community/'),
article('sensoren-groei-mais','90dfd6722a20',
 'Nieuwe sensoren volgen hoe een maïsplant groeit',
 'Onderzoekers testen rekbare sensoren voor maïsstengels en kolven',
 'In een kas maten sensoren elke tien minuten de groei van stengels en kolven. Veldproeven moeten nog volgen.',
 'Wetenschap','https://phys.org/news/2026-11-sensors-corn-growth.html','South Dakota State University via Phys.org','phys-org','2026-11-03',[
 'Wat doet een maïsplant na bemesting of een andere behandeling? Onderzoekers van South Dakota State University hebben sensoren ontwikkeld die veranderingen in de dikte van stengels en kolven kunnen volgen. Tijdens eerste tests leverden ze iedere tien minuten nieuwe gegevens.',
 'De sensoren gebruiken laserbewerkt grafeen, een elektrisch geleidend materiaal. Dat is bevestigd aan een band van siliconen die met de plant kan meebewegen. Een veermechanisme moet helpen om contact te houden zonder de groei af te knellen.',
 'Het team testte het systeem in een kas. De metingen kunnen onderzoekers helpen om veranderingen preciezer in de tijd te volgen, in plaats van alleen af en toe handmatig te meten. Zo wordt het mogelijk om gerichter te onderzoeken wanneer een plant op ingrepen reageert.',
 'Het bereikte resultaat is een getest meetsysteem. Proeven op het veld en verdere financiering moeten nog volgen. Er is dus nog geen aangetoonde besparing op mest of verbetering van oogsten. Wel hebben onderzoekers een praktisch hulpmiddel om zulke vragen nauwkeuriger te bestuderen.'
 ],'id:3705687','Illustratieve foto van maïs; niet de planten of sensoren uit het experiment.'),
]

note = ('Laatst kwam op straat een moeder schreeuwend en huilend naar me toe. Haar zoontje was kwijt. Hij kon niet praten. '
        'We liepen naar de voetbalclub waar hij mogelijk was. Daar begon iedereen meteen mee te zoeken. Twee minuten later riep zijn moeder: ‘Daar is hij!’ '
        'Een vrouw had zich over hem ontfermd. Al twintig minuten bleef ze bij hem, terwijl zijn moeder hem zocht. '
        'Wat me bijbleef: hoe vanzelfsprekend iedereen hielp. De vrouw die bij het jongetje bleef. De mensen bij de club die direct gingen zoeken. '
        'Dit lees je niet in de krant. Maar het gebeurt wel.')

headlines = [
 dict(title='Democraten behalen meerderheid in Huis en Senaat bij Amerikaanse verkiezingen',url='https://nos.nl/artikel/2637958-amerikaanse-kiezer-rekent-af-met-trump-democratische-meerderheid-in-huis-en-senaat',source='NOS',source_id='nos',published='2026-11-04'),
 dict(title='Nederland draagt Klaas Knot voor als president van de Europese Centrale Bank',url='https://nos.nl/artikel/2637997-nederland-draagt-klaas-knot-voor-als-president-europese-centrale-bank',source='NOS',source_id='nos',published='2026-11-04'),
 dict(title='Inflatie in oktober volgens snelle raming op 3,7 procent',url='https://nos.nl/artikel/2637971-inflatie-stijgt-verder-tot-3-7-procent-in-oktober-boodschappen-iets-goedkoper',source='NOS',source_id='nos',published='2026-11-04'),
]

def main():
    pool=json.loads((ROOT/'selectie'/f'{DATE}-kandidaten.json').read_text())
    byid={x['id']:x for x in pool['all_candidates']}
    order=[]
    for region,articles in [('nl',nl),('int',world)]:
        for rank,item in enumerate(articles,1):
            item.update(region=region,regional_rank=rank,editorial_rank=rank)
            original=byid.get(item['candidate_id'],{})
            if original.get('reading_time_minutes'):item['reading_time_minutes']=original['reading_time_minutes']
            order.append(dict(section=region,article_slug=item['article_slug'],rank=rank))
    data=dict(meta=dict(edition_date=DATE,status='draft',publication_authorized=False,
        selection_confirmed_by='Tom de Haas',selection_confirmed_on='2026-11-04',
        preview_revision='2026-11-05-concept-1',
        email_preheader='Een teruggevonden jongetje, meetbare winst van leefstijlbegeleiding en een eiland dat het licht dooft voor jonge zeevogels.',
        personal_note=dict(title='Dit lees je niet in de krant',text=note),editorial_order=order),
        nl=nl,int=world,headlines=headlines)
    (ROOT/'nieuws.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
