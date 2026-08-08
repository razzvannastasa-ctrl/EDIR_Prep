"""Build the staged Chapter 1 UEFA CFM bank from its reviewed blueprint."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "UEFA-HFM-The-organisation-of-world-football.pdf"
OUTPUT = Path("data/cfm_imports/chapter_01_organisation_of_world_football.json")
QUESTIONS: list[dict] = []


def _positions(number: int, count: int) -> list[int]:
    group = (number - 1) % 5
    return {
        1: [group % 5],
        2: sorted({group % 5, (group + 2) % 5}),
        3: sorted({group % 5, (group + 2) % 5, (group + 4) % 5}),
        4: [position for position in range(5) if position != (group + 1) % 5],
    }[count]


def add(stem, true, false, explanation, pdf_page, handbook_pages, crops=None):
    number = len(QUESTIONS) + 1
    positions = _positions(number, len(true))
    assert len(true) == len(positions), (number, len(true), positions)
    assert len(false) == 5 - len(positions), (number, len(false), positions)
    true_iter, false_iter = iter(true), iter(false)
    options = [
        next(true_iter) if position in positions else next(false_iter)
        for position in range(5)
    ]
    QUESTIONS.append(
        {
            "q_number": number,
            "question_text": stem,
            "q_type": "multiple_choice",
            "options": options,
            "source_locator": {
                "file": SOURCE,
                "pdf_pages": [pdf_page],
                "handbook_pages": handbook_pages,
            },
            "page_crops": crops or [],
            "answer": {
                "correct_options": positions,
                "explanation": explanation,
            },
        }
    )


# PDF page 2 / handbook pages 42-43: ecosystem, pyramid, cooperation and Bosman.
add(
    "A national association is explaining why world football is described as a pyramid. Which statement best captures the handbook's model?",
    ["FIFA sits above recognised regional confederations, whose national associations are also FIFA members."],
    ["The confederations are themselves FIFA member associations.", "Each club reports directly to FIFA without national or regional structures.", "Every country may maintain several FIFA-recognised associations and league pyramids.", "The IFAB sits below domestic leagues and administers their commercial rights."],
    "A strong oral answer should describe a coordinated hierarchy rather than a loose collection of clubs. FIFA is at the apex, while the six confederations organise regional competitions for national associations that also belong to FIFA. The confederations are recognised by FIFA but are not themselves FIFA members.", 2, [42, 43],
)
add(
    "Which features allowed club and national-team competitions to develop in parallel within the football ecosystem?",
    ["Clubs release players to national teams as a form of solidarity.", "Clubs, national associations, confederations and FIFA cooperate for mutual benefit."],
    ["National teams employ all players centrally and loan them to clubs.", "International football developed by separating clubs completely from governing bodies.", "Only commercial broadcasters coordinate the international match calendar."],
    "The system depends on institutional cooperation and the release of club players for national-team duty. That arrangement lets club and national-team competitions coexist instead of competing for an entirely separate player pool. It illustrates the wider interdependence of stakeholders in the football pyramid.", 2, [42, 43],
)
add(
    "A league wants to grow its professional audience without investing in grassroots participation. Which handbook principles challenge that approach?",
    ["Professional competitions need a steady pool of players supported by grassroots participation.", "Grassroots participation also stimulates spectator interest in professional football.", "Elite and mass-participation football are interdependent parts of the same ecosystem."],
    ["Professional demand is independent of participation below elite level.", "Grassroots activity matters only to national teams and not to league football."],
    "The handbook treats grassroots and elite football as mutually reinforcing. Participation supplies players and helps create interest in watching the professional game. An oral answer should therefore reject a strategy that treats the elite product as self-sustaining.", 2, [42, 43],
)
add(
    "Which statements explain why producing a sporting competition requires both rivalry and cooperation?",
    ["Competitors must cooperate sufficiently to stage individual matches.", "League participants need shared arrangements to organise a coherent competition.", "Stakeholders depend on one another for their own success.", "Cooperation helps preserve a stable operating environment for competition."],
    ["Successful leagues remove all common rules so that rivalry is unconstrained."],
    "Sporting opponents compete on the field but jointly produce the contest. Shared rules, calendars and organisational arrangements make meaningful rivalry possible. Purely independent action would undermine the product that every participant relies on.", 2, [42, 43],
)
add(
    "What was the original management purpose of convening the IFAB in 1886?",
    ["To create a uniform international code that enabled football between the four UK home nations."],
    ["To sell global broadcasting rights for national-team competitions.", "To replace the four home-nation associations with a single British association.", "To regulate player agents and international transfers.", "To create the first European club competition."],
    "The IFAB arose from the need for consistent playing rules across the four home nations. A common code made international matches workable without abolishing the participating associations. Its original purpose was regulatory consistency, not commercial or transfer administration.", 2, [42, 43],
)
add(
    "Which benefits does the handbook attribute to the integrated global football pyramid?",
    ["A stable regulatory environment for football development and competitions.", "Coordination of complementary club and national-team calendars."],
    ["Automatic exemption of football from public law.", "A guarantee that commercial revenue is retained only by elite clubs.", "Permission for several competing FIFA-recognised league pyramids in each country."],
    "The pyramid supplies stability and coordination across levels of the game. FIFA's recognition model and international calendar help complementary competitions operate efficiently. It does not remove football from ordinary law or reserve all value for elite participants.", 2, [42, 43],
)
add(
    "A commercial competition generates a large operating surplus. Which uses are consistent with the handbook's solidarity logic?",
    ["Support domestic football development through the national associations.", "Fund grassroots projects from international competition surpluses.", "Use elite competitions to promote participatory as well as spectator interest."],
    ["Distribute every surplus only to the teams that reached the final.", "Treat grassroots football as unrelated to the commercial competition."],
    "Solidarity links commercially successful elite events to the wider football pyramid. Surpluses can support associations and grassroots development, preserving the base on which the elite game depends. A distribution model confined entirely to finalists would miss that ecosystem responsibility.", 2, [42, 43],
)
add(
    "Which consequences followed from the Bosman ruling as presented in the handbook?",
    ["EU institutions became important stakeholders in European football.", "Foreign-player quotas in UEFA and EU domestic competitions ended.", "Out-of-contract players gained mobility between EU countries without a transfer or tribunal fee.", "The professional player labour market internationalised rapidly."],
    ["Football's transfer rules were confirmed to be entirely outside EU labour law."],
    "Bosman showed that football regulation operates within the wider legal environment. The ruling expanded labour mobility, removed the relevant quotas and accelerated market internationalisation. It also forced football managers to recognise EU institutions as stakeholders capable of changing the ecosystem.", 2, [42, 43],
)
add(
    "When a new public regulator begins affecting football, what response follows the chapter's ecosystem approach?",
    ["Map the regulator as a stakeholder and assess how its influence changes the system's equilibrium."],
    ["Ignore it until it becomes a formal FIFA member.", "Assume sporting autonomy prevents it from influencing football.", "Remove existing football stakeholders from the analysis.", "Respond only by changing the Laws of the Game."],
    "The ecosystem is dynamic, so managers must identify emerging stakeholders and evaluate their impact. Bosman illustrates the cost of failing to anticipate an external legal actor. Strategic analysis should precede policies designed to restore or maintain equilibrium.", 2, [42, 43],
)
add(
    "Which statements correctly distinguish a confederation from a FIFA member association?",
    ["A confederation is recognised by FIFA but is not itself a FIFA member.", "A national association within a confederation may also be a FIFA member."],
    ["A confederation has one vote at the FIFA Congress in place of its national associations.", "Only confederations may organise national-team competitions.", "A national association belongs either to FIFA or to a confederation, but never both."],
    "The two memberships should not be conflated. FIFA recognises the six confederations, while the individual national associations hold FIFA membership and participate in their regional structure. That arrangement supports both global and regional governance.", 2, [42, 43],
)
add(
    "Which management assumptions are consistent with the football-ecosystem metaphor?",
    ["The environment changes as new stakeholders emerge.", "The influence of stakeholders requires continuing strategic evaluation.", "Effective policy should respond to changes that threaten system balance."],
    ["The stakeholder map can be fixed permanently once the organisation is founded.", "Commercial success makes cooperation between stakeholders unnecessary."],
    "A biological ecosystem is useful precisely because it evolves and contains interdependent actors. Managers must monitor changes and formulate policy in response. A static map or a purely commercial view would fail to capture that continuing adaptation.", 2, [42, 43],
)
add(
    "Which arrangements reinforce the operational integrity of the global football pyramid?",
    ["Recognition of one national association per country.", "Recognition of one league pyramid per country.", "A coordinated international match calendar.", "Cooperation among FIFA, confederations and national associations."],
    ["Independent international calendars created separately by every professional club."],
    "Integrity depends on recognised authority and coordinated structures. One association and league pyramid per country, combined with a shared international calendar, reduces institutional conflict. Cooperation across governing levels makes club and national-team football complementary.", 2, [42, 43],
)

# PDF page 3 / handbook pages 44-45: stakeholder mapping, IFAB and FIFA purpose.
add(
    "What is the central purpose of stakeholder mapping in football management?",
    ["To monitor internal and external actors and adjust strategy as their influence changes."],
    ["To list only organisations that possess formal voting rights.", "To replace strategic analysis with a one-time organisational chart.", "To exclude public authorities and businesses from football decisions.", "To allocate places in international competitions."],
    "Stakeholder mapping is a continuing strategic discipline, not a static directory. It helps an organisation understand who can affect its objectives and adjust policy as that environment changes. Formal membership is only one possible source of influence.", 3, [44, 45],
    [{"pdf_page": 3, "bbox": {"left": 0.10, "top": 0.30, "right": 0.42, "bottom": 0.73}, "caption": "Figure 1.1: UEFA's stakeholder ecosystem"}],
)
add(
    "Which groups appear in the handbook's broad account of UEFA stakeholders?",
    ["Industry actors such as clubs and leagues.", "External partners such as business and government."],
    ["Only UEFA member associations and no other actors.", "Only organisations based within Switzerland.", "Bodies from individual sports are excluded by definition."],
    "UEFA's map reaches beyond the formal football hierarchy. It includes industry actors, sporting partners and external partners whose decisions affect European football. A useful oral answer should emphasise influence and interdependence rather than legal membership alone.", 3, [44, 45],
)
add(
    "Which factors help explain football's global participation, spectator and commercial appeal according to the IFAB section?",
    ["The playing rules are comparatively easy to understand.", "The Laws of the Game apply universally.", "The game has strong athletic appeal."],
    ["Every market is allowed to rewrite the Laws independently.", "Commercial partners control amendments to the Laws of the Game."],
    "Football combines an accessible game with a universal rule set and strong athletic appeal. That consistency supports participation and spectatorship across different countries, which in turn attracts commercial interest. Local rewriting or commercial control would weaken the universality described in the chapter.", 3, [44, 45],
)
add(
    "Which statements describe the IFAB's authority over the Laws of the Game?",
    ["The Laws of the Game are the preserve of the IFAB.", "Any national association may propose a rule change.", "An amendment requires a three-quarters majority of IFAB members.", "Rule changes have historically been introduced cautiously."],
    ["A simple majority of commercial partners can amend a Law."],
    "The IFAB is the custodian of a universal rule set and changes it conservatively. Proposals are open to national associations, but adoption requires the specified supermajority. Commercial stakeholders may be affected by a change but do not possess amendment authority.", 3, [44, 45],
)
add(
    "Which example illustrates the handbook's principle that sporting imperatives should prevail over commercial interests?",
    ["Football's ban on physical advertising on the field of play under Law 1."],
    ["Allowing sponsors to alter the dimensions of the pitch.", "Giving broadcasters votes on IFAB amendments.", "Replacing promotion and relegation with advertising revenue rankings.", "Permitting on-field advertising whenever a league requests it."],
    "The handbook uses Law 1's restriction on pitch advertising to show that the game itself is treated as primary. UEFA's statutes express the same idea by placing sporting values above commercial interests. Commercial exploitation must therefore operate within sporting constraints.", 3, [44, 45],
)
add(
    "Which changes are cited as examples of the IFAB adapting the game while retaining careful custodianship?",
    ["The 1992 back-pass rule addressed overly defensive play.", "The 2018 introduction of video assistant referees changed officiating support."],
    ["The abolition of national associations followed the back-pass rule.", "VAR transferred control of the Laws to broadcasters.", "The Bosman ruling was an IFAB amendment to Law 1."],
    "The back-pass rule and VAR are examples of deliberate evolution of the Laws of the Game. They responded to sporting needs while leaving the IFAB's custodial role intact. Bosman, by contrast, was a court ruling about labour mobility rather than a change to the playing laws.", 3, [44, 45],
)
add(
    "What features of FIFA membership support equal formal representation at the FIFA Congress?",
    ["FIFA's member associations each have one vote.", "Voting weight does not depend on population size.", "Voting weight does not depend on economic power."],
    ["Regional confederations cast all votes on behalf of their members.", "Broadcast revenue determines the number of Congress votes."],
    "FIFA's Congress applies formal equality among its member associations. Each association receives one vote irrespective of national population or economic strength. That principle concerns representation, not an assessment that every football market is identical.", 3, [44, 45],
)
add(
    "Which statements summarise FIFA's primary strategic purpose as stated in the handbook?",
    ["Continually improve football.", "Promote the game globally.", "Recognise football's unifying, educational, cultural and humanitarian values.", "Place particular emphasis on youth and development programmes."],
    ["Maximise distributions to professional clubs as its sole objective."],
    "FIFA's statutory purpose is broader than running major tournaments. It combines global promotion and improvement of the game with social and developmental values, particularly youth development. Commercial revenue is a means of supporting that mission rather than the sole end.", 3, [44, 45],
)

# PDF page 4 / handbook pages 46-47: competitions, revenue and development.
add(
    "How does the men's Olympic football competition differ from an unrestricted senior World Cup in the handbook's account?",
    ["Most squad members must be under 23, with only three over-age players permitted."],
    ["It is organised outside the Olympic movement.", "Every player must be under 17.", "Only European national associations may enter.", "Clubs rather than national teams represent each country."],
    "FIFA is part of the Olympic movement because football is a recognised Olympic sport. The men's tournament is effectively an under-23 competition with a limited over-age allowance. That age structure distinguishes it from FIFA's unrestricted senior World Cup.", 4, [46, 47],
)
add(
    "Which statements explain how the FIFA World Cup supports FIFA's wider mission?",
    ["Broadcasting and sponsorship rights generate substantial revenue.", "The tournament surplus finances wider FIFA activities between World Cups."],
    ["All World Cup income must remain with the host country.", "The event is disconnected from FIFA's development expenditure.", "FIFA relies mainly on membership fees rather than commercial rights."],
    "The World Cup is both a sporting event and FIFA's principal commercial engine. Its rights income and surplus fund activities across the four-year cycle, including development. An oral answer should connect commercial exploitation to the not-for-profit mission rather than treat them as opposites.", 4, [46, 47],
)
add(
    "A member association requests generic funding with no local diagnosis or accountability. Which FIFA Forward features suggest how the request should be redesigned?",
    ["Support should be tailor-made to the association's development needs.", "The programme takes a 360-degree view of development support.", "Evaluation and auditing accompany increased financial assistance."],
    ["Every association must receive an identical project regardless of context.", "Funding should be exempt from review because FIFA is not-for-profit."],
    "FIFA Forward replaced older programmes with more comprehensive and locally tailored support. Increased funding is paired with stronger evaluation and auditing rather than reduced accountability. The association should therefore present a needs-based programme with measurable oversight.", 4, [46, 47],
)
add(
    "Which statements describe FIFA's wider competition portfolio beyond the senior men's World Cup?",
    ["It includes men's and women's youth World Cups.", "It includes futsal and beach-soccer competitions.", "It includes Olympic football tournaments.", "Many of these competitions are financed as part of FIFA's development role despite operating at a loss."],
    ["FIFA organises no competition unless it generates a direct profit."],
    "FIFA uses competitions as development instruments across age groups, genders and formats. The handbook explicitly notes that almost all competitions outside the flagship World Cup operate at a loss. Their value is therefore assessed against football-development objectives, not only direct profitability.", 4, [46, 47],
)
add(
    "Which expenditure priority best reflects FIFA's not-for-profit development objective in the 2015-18 cycle?",
    ["Football development and education represented its largest single expenditure item after operations and competition costs."],
    ["Dividend payments to private shareholders were the leading programme cost.", "All surplus was reserved for constructing FIFA headquarters.", "Development spending was prohibited from using World Cup revenue.", "Only senior men's competitions could receive programme funding."],
    "The handbook links FIFA's legal form and statutory purpose to material development expenditure. Football development and education were a major use of the organisation's resources after core operating and competition costs. That pattern demonstrates mission-led reinvestment rather than shareholder distribution.", 4, [46, 47],
)
add(
    "Which management conclusions can be drawn from FIFA financing loss-making competitions?",
    ["Direct event profit is not the only measure of strategic value.", "A flagship event can cross-subsidise developmental competitions."],
    ["Every competition should be cancelled once it records a loss.", "Loss-making youth events contradict FIFA's statutory purpose.", "Commercial success removes the need to evaluate development outcomes."],
    "A not-for-profit governing body may deliberately fund events that advance participation, talent and representation. The World Cup's surplus makes that portfolio approach possible. Managers should evaluate mission contribution alongside financial performance rather than applying a single-event profit test.", 4, [46, 47],
)
add(
    "Which elements should appear in an oral explanation of FIFA's dual role as competition organiser and developer?",
    ["It stages commercially powerful flagship competitions.", "It reinvests resources in football development and education.", "It organises other competitions that broaden the game's reach despite their direct losses."],
    ["Its development function is delegated entirely to commercial sponsors.", "Its competition activity is unrelated to its statutory purpose."],
    "FIFA's competition and development functions reinforce one another. Flagship commercial success produces resources, while a broader event and programme portfolio advances global development. Treating the two roles as unrelated would miss the financing logic described in the chapter.", 4, [46, 47],
)
add(
    "Which statements correctly characterise FIFA Forward as presented in the handbook?",
    ["It overhauled the earlier Goal and Financial Assistance programmes.", "It serves both member associations and the six confederations.", "It combines increased financial support with stronger evaluation.", "Its support is intended to be comprehensive and tailored."],
    ["It is limited to financing the senior men's World Cup."],
    "FIFA Forward is a redesign of development assistance rather than a renamed tournament budget. It expands and tailors support while strengthening evaluation and audit. The programme therefore combines resources, local relevance and accountability.", 4, [46, 47],
)

# PDF page 5 / handbook pages 48-49: regulation, overlap and FIFA governance.
add(
    "Which FIFA regulatory responsibility protects the unitary national structure of the global pyramid?",
    ["Ensuring that each member country has one football association and one league structure."],
    ["Allowing rival national associations to compete for recognition every season.", "Delegating recognition entirely to player agents.", "Replacing domestic pyramids with FIFA-run leagues.", "Giving broadcasters authority to approve national associations."],
    "FIFA's recognition rule protects a coherent chain of authority within each country. One association and one league structure reduce competing claims and support the operational integrity of the global pyramid. Commercial or intermediary actors do not determine that recognition.", 5, [48, 49],
)
add(
    "Which activities belong to FIFA's player-market regulatory role?",
    ["Regulating player status and international transfers through the transfer-matching system.", "Regulating player intermediaries or agents."],
    ["Licensing all European coaches on UEFA's behalf.", "Selecting clubs for UEFA competitions.", "Setting domestic ticket prices for member associations."],
    "FIFA regulates the international movement and representation of players through transfer and intermediary rules. Those functions differ from UEFA-specific club licensing or domestic commercial choices. An oral answer should locate the issue at the appropriate governing level.", 5, [48, 49],
)
add(
    "A government attempts to appoint a national association's president directly. Which handbook principles are engaged?",
    ["FIFA seeks to keep football free from government political interference.", "Election interference falls within FIFA's regulatory concern.", "The confederation and national association cooperate with FIFA in protecting autonomy."],
    ["Government appointment is required whenever public funding is involved.", "The issue belongs exclusively to the IFAB because it concerns a president."],
    "FIFA's statutes treat government interference in association elections as a threat to football autonomy. FIFA performs this role with confederations and national associations rather than through the IFAB. The IFAB governs playing laws, not institutional elections.", 5, [48, 49],
)
add(
    "Which statements explain why clubs may be compelled to release fit players for national-team competitions?",
    ["Release protects the health of national-team competitions.", "It operationalises solidarity between club and representative football.", "It supports parallel club and national-team competition structures.", "The obligation is subject to the player's not being injured."],
    ["A club may always refuse release whenever the player is commercially valuable."],
    "Player release is a concrete expression of ecosystem interdependence. Representative competitions need access to players employed by clubs, while injury provides a legitimate limitation. A purely unilateral club veto would undermine the parallel competition model.", 5, [48, 49],
)
add(
    "Under the handbook's allocation of authority, who decides an issue involving national associations from more than one confederation?",
    ["FIFA."],
    ["A single affected national association.", "UEFA regardless of the confederations involved.", "The European Club Association.", "The IFAB's commercial committee."],
    "The territorial scale of an issue determines the governing level. A national association handles national matters, UEFA handles multi-association matters within its territory, and FIFA handles international issues spanning confederations. The question therefore belongs at FIFA level.", 5, [48, 49],
)
add(
    "Which areas are described as overlapping FIFA and UEFA responsibilities?",
    ["Promotion and development of football.", "The fight against doping."],
    ["European club licensing as a FIFA-exclusive function.", "The FIFA World Cup as a UEFA-exclusive competition.", "UEFA coach licensing as an IFAB responsibility."],
    "FIFA and UEFA share several regulatory and development concerns because they govern the same sport and memberships overlap. Doping and football development are examples of shared fields. European club licensing is UEFA-specific, while world-level competitions fall to FIFA.", 5, [48, 49],
)
add(
    "Which subjects are assigned exclusively to FIFA in the handbook's FIFA-UEFA responsibility table?",
    ["The international match calendar.", "The status and transfer of players.", "The relationship with the International Olympic Committee."],
    ["European club licensing and financial fair play.", "European coach licensing."],
    "FIFA's exclusive responsibilities reflect its global scope and Olympic-federation status. Transfers and the international calendar require worldwide coordination, while UEFA has its own European licensing functions. The distinction prevents every regional issue from being treated as global.", 5, [48, 49],
)
add(
    "Which statements accurately describe the FIFA Congress and FIFA Council?",
    ["The Congress is FIFA's supreme legislative body.", "All member associations are represented in the Congress.", "The Congress decides hosts of FIFA World Cup tournaments.", "The Council is a non-executive, supervisory and strategic body that sets FIFA's vision."],
    ["The Council replaced the Congress as the body representing every member association."],
    "The Congress provides the broad legislative and representative foundation of FIFA. The reformed Council supplies strategic supervision rather than replacing the Congress. Their roles are distinct but complementary within the governance structure.", 5, [48, 49],
)
add(
    "Who elects the FIFA president under the governance structure described in the handbook?",
    ["The FIFA Congress."],
    ["The six confederation presidents acting alone.", "The FIFA general secretariat.", "The International Olympic Committee.", "The IFAB."],
    "The FIFA president is elected by the Congress, while the confederations elect 36 of the other Council members. This separates the election of the president from the confederations' allocation of Council seats. Neither the secretariat nor the IFAB performs that electoral role.", 6, [50, 51],
)
add(
    "Which governance safeguards or representation requirements apply to the FIFA Council and presidency in the handbook?",
    ["Each confederation must elect at least one female Council member.", "The FIFA president may serve a maximum of three four-year terms."],
    ["The president holds office for life after a single Congress vote.", "Only UEFA may elect women to the Council.", "The general secretary appoints all 37 Council members."],
    "The reform framework combines regional representation with a minimum female-representation rule. It also limits presidential tenure to three four-year terms. These safeguards constrain office-holding rather than concentrating appointments in the secretariat.", 6, [50, 51],
)
add(
    "Which bodies or officers are responsible for implementing FIFA's high-level decisions?",
    ["The general secretariat implements decisions of the Congress, Council and president.", "The secretary general directs the general secretariat.", "The president exercises substantial day-to-day executive authority."],
    ["Regional broadcasters implement Congress decisions independently.", "The IFAB general assembly manages FIFA's administrative staff."],
    "FIFA separates high-level decisions from administrative implementation. The secretariat, led by the secretary general, carries out the decisions, while the president also has significant executive authority. External commercial actors and the IFAB do not manage FIFA's administration.", 6, [50, 51],
)
add(
    "Which functions belong in a concise oral summary of FIFA's purpose and activities?",
    ["Partnership with the IFAB in organising and policing the rules.", "Global football development through FIFA Forward.", "Organisation of international competitions.", "Regulation in cooperation with confederations and national associations."],
    ["Direct administration of every domestic club's daily operations."],
    "FIFA combines rule custodianship, development, competitions, solidarity financing and regulation. It performs many tasks through partnership across the football pyramid rather than running every club directly. A good oral answer should connect these functions to its global strategic purpose.", 6, [50, 51],
)

# PDF page 6 / handbook pages 50-51: UEFA purpose, political relations and organisation.
add(
    "Which structural feature most clearly distinguishes UEFA's competition experience from FIFA's in the handbook?",
    ["UEFA has decades of experience running several annual, season-long international club competitions."],
    ["UEFA is the world governing body and FIFA is only a regional confederation.", "FIFA runs every European club competition directly.", "UEFA organises no national-team competitions.", "UEFA's only club event is the FIFA Club World Cup."],
    "UEFA's distinctive operational experience lies in its portfolio of recurring European club competitions. FIFA has a global remit but, in the handbook's comparison, only one international club competition. The distinction concerns competition operations, not a reversal of their governing levels.", 6, [50, 51],
)
add(
    "Which principles underpin UEFA's statutory purpose in European football?",
    ["Sporting solidarity redistributes resources from elite football to the grassroots.", "Sporting merit is operationalised through promotion and relegation."],
    ["Closed membership based solely on commercial value.", "Permanent separation of elite clubs from national associations.", "Distribution of all resources only to competition winners."],
    "UEFA's purpose links the sporting pyramid to solidarity and sporting merit. Promotion and relegation express merit, while redistribution connects elite success to grassroots development. A closed, winner-takes-all model conflicts with both principles.", 6, [50, 51],
)
add(
    "Why does UEFA maintain dialogue and cooperation with European political authorities?",
    ["To defend football's interests in policy discussions.", "To safeguard sporting ethics and integrity.", "To promote good governance and obtain support for legitimate football policies."],
    ["To transfer all UEFA rule-making authority to the European Commission.", "To avoid any application of European law to football."],
    "UEFA treats public authorities as influential stakeholders rather than as bodies that can simply be ignored. Cooperation can support policies on integrity, governance, collective rights selling and financial sustainability. Dialogue does not mean surrendering all governing authority or claiming exemption from law.", 6, [50, 51],
)
add(
    "Which UEFA policies are cited as areas where European authorities have provided valuable support?",
    ["Rules on home-grown players.", "Collective selling of television rights.", "Financial fair play.", "Efforts against match-fixing and abusive practices."],
    ["A rule allowing nationality quotas contrary to EU law."],
    "The chapter presents cooperation with European authorities as practical support for integrity and governance policies. Home-grown rules, collective rights selling, financial fair play and anti-match-fixing work are examples. Nationality quotas are specifically problematic under the Bosman framework and should not be confused with locally trained-player rules.", 6, [50, 51],
)
add(
    "What does subsidiarity mean in UEFA's implementation model?",
    ["National associations implement UEFA Congress decisions in a way consistent with local conditions."],
    ["Every local association may disregard Congress decisions entirely.", "UEFA administration replaces national associations in all domestic matters.", "Commercial clubs exercise UEFA's legislative powers.", "FIFA delegates the Laws of the Game to local sponsors."],
    "Subsidiarity combines common direction with locally appropriate implementation. UEFA establishes the framework, while national associations apply decisions in their own contexts. It is not a licence to ignore policy or a mechanism for abolishing the national level.", 6, [50, 51],
)
add(
    "Which electoral functions belong to the UEFA Congress?",
    ["Electing the UEFA president.", "Electing the UEFA Executive Committee."],
    ["Appointing every national association president.", "Selecting all club squads for UEFA competitions.", "Amending the Laws of the Game without the IFAB."],
    "The Congress is the central representative institution in UEFA's governance. It elects the president and Executive Committee and also elects European members of the FIFA Council. Domestic elections, team selection and IFAB law-making fall outside those Congress functions.", 6, [50, 51],
)
add(
    "Which features demonstrate that UEFA operates as a representative democracy?",
    ["The Congress is composed through the member associations.", "Member associations may propose Congress agenda items.", "Congress decisions establish the framework for the president and Executive Committee."],
    ["The president may permanently bypass Congress decisions.", "Commercial partners appoint the Congress directly."],
    "Representative democracy is visible in member-association participation, agenda rights and the authority of Congress decisions. The executive bodies operate within that framework rather than above it. Commercial influence does not replace the statutory representative structure.", 7, [52, 53],
)
add(
    "Which statements accurately describe the composition or role of UEFA's Executive Committee?",
    ["It implements Congress decisions with the president through the UEFA administration.", "It includes members elected by the Congress.", "It includes representatives elected by the European Club Association and European Leagues.", "Stakeholder appointees are ratified by Congress and share the rights and duties of other members."],
    ["It is composed only of broadcasting companies."],
    "The Executive Committee connects representative governance with structured stakeholder participation. Congress-elected members sit alongside ratified club and league representatives, all operating under the same duties. The body implements policy through UEFA's administration rather than serving as a commercial board.", 7, [52, 53],
)

# PDF page 7 / handbook pages 52-53: accountability, justice and stakeholder engagement.
add(
    "Who is UEFA's most senior executive officer according to the governance description?",
    ["The general secretary."],
    ["The chair of the European Club Association.", "The president of the Court of Arbitration for Sport.", "The head of Football Supporters Europe.", "The senior external auditor."],
    "The UEFA president is the public representative, while the general secretary is identified as the most senior executive officer. This distinction helps explain the separation between representation, political leadership and administration. External stakeholders and judicial bodies do not lead UEFA's executive staff.", 7, [52, 53],
)
add(
    "Which statements reflect UEFA's separation-of-powers principle?",
    ["Judicial and executive roles are institutionally separated.", "Dedicated Organs for the Administration of Justice handle disciplinary matters."],
    ["The Executive Committee acts as the final court in every disciplinary appeal.", "Commercial sponsors appoint disciplinary inspectors.", "The principle eliminates any avenue of appeal outside UEFA."],
    "UEFA separates policy execution from disciplinary adjudication through specialised judicial bodies. That architecture supports fair governance and avoids having the executive decide every case. Appeals remain possible, ultimately to the Court of Arbitration for Sport.", 7, [52, 53],
)
add(
    "Which bodies form part of UEFA's Organs for the Administration of Justice?",
    ["The Control, Ethics and Disciplinary Body.", "The Appeals Body.", "The Club Financial Control Body."],
    ["The Professional Football Strategy Council.", "The UEFA Congress's external commercial partners."],
    "UEFA's judicial architecture includes first-instance disciplinary, appeal, inspector and club-financial-control functions. The PFSC is a stakeholder consultation forum, not a judicial organ. Distinguishing consultation from adjudication is important when explaining good governance.", 7, [52, 53],
)
add(
    "Which statements describe the Court of Arbitration for Sport's place in UEFA disciplinary governance?",
    ["It is based in Lausanne.", "It is the ultimate court of appeal for decisions of UEFA disciplinary bodies.", "Its role sits outside UEFA's day-to-day executive administration.", "Its availability reinforces a separation between executive and appellate functions."],
    ["It drafts UEFA competition formats before Congress approval."],
    "CAS provides the ultimate appellate route for UEFA disciplinary decisions. Its external appellate role complements UEFA's internal judicial bodies and supports separation of powers. It does not design competitions or administer UEFA policy.", 7, [52, 53],
)
add(
    "What change prompted UEFA to complement its traditional hierarchy with formal stakeholder engagement?",
    ["Revenue growth and globalised player markets created influential new actors that needed structured consultation."],
    ["National associations ceased to exist.", "The IFAB required leagues to elect the UEFA president.", "European club competitions stopped generating stakeholder interest.", "EU law prohibited UEFA from consulting supporters."],
    "UEFA retained its hierarchy of confederation, associations and clubs but recognised that the ecosystem had become more complex. Revenue growth and globalised labour markets increased the influence of clubs, leagues, players and other groups. Structured engagement was an adaptation, not an abandonment of the statutory hierarchy.", 7, [52, 53],
)
add(
    "Which conditions must a stakeholder group meet to be formally recognised in UEFA consultation?",
    ["It must be organised consistently with UEFA's statutes, regulations and values.", "It must be constituted democratically, openly and transparently."],
    ["It must own broadcasting rights in every UEFA country.", "It must replace the relevant national associations.", "It must be headquartered in the same building as UEFA."],
    "Recognition depends on governance quality and compatibility with UEFA's framework. Democratic, open and transparent constitution provides legitimacy for consultation. Commercial scale, location or substitution for member associations is not the test.", 7, [52, 53],
)
add(
    "Which constituencies are represented in the Professional Football Strategy Council?",
    ["Professional leagues through the European Leagues.", "Clubs through the European Club Association.", "Players through FIFPro Division Europe."],
    ["Only match officials and no member-association representatives.", "The International Olympic Committee as chair."],
    "The PFSC brings together leagues, clubs, players and UEFA member-association representatives under the UEFA president's chairmanship. It is a structured vehicle for dialogue among major professional-football stakeholders. It is not limited to technical officials or chaired by the Olympic movement.", 7, [52, 53],
)
add(
    "Which mechanisms embed club and league stakeholders in UEFA decision-making?",
    ["Two ECA representatives sit on the UEFA Executive Committee.", "One European Leagues representative sits on the Executive Committee.", "Memorandums of understanding formalise relationships with major stakeholder bodies.", "UEFA Club Competitions SA gives club representatives a structured advisory role on strategic business matters."],
    ["Stakeholder bodies can unilaterally enact UEFA regulations without Executive Committee approval."],
    "UEFA combines representation, formal agreements and advisory structures. Stakeholders receive defined channels into consultation and governance, but final statutory approval remains with UEFA bodies. Engagement therefore broadens input without transferring unilateral law-making power.", 7, [52, 53],
)
add(
    "Which organisation is recognised as UEFA's official interlocutor on issues affecting supporters?",
    ["Football Supporters Europe."],
    ["The FIFA Council.", "The European Club Association.", "The Court of Arbitration for Sport.", "UEFA Club Competitions SA."],
    "Football Supporters Europe is the recognised representative interlocutor for fan issues. Its democratic and independent character fits UEFA's stakeholder-recognition criteria. Club, judicial and strategic bodies have different constituencies and purposes.", 7, [52, 53],
)
add(
    "Which supporter-focused functions are associated with SD Europe and CAFE?",
    ["SD Europe helps fan groups participate in club ownership and governance.", "CAFE promotes stadium accessibility for supporters with disabilities."],
    ["Both bodies allocate World Cup hosting rights.", "They regulate international player transfers.", "They replace UEFA's disciplinary bodies."],
    "UEFA's supporter engagement includes both governance participation and accessibility. SD Europe supports supporter involvement in clubs, while CAFE focuses on access for disabled fans. Neither organisation performs global competition, transfer or disciplinary functions.", 7, [52, 53],
)
add(
    "Which statements show that UEFA's supporter strategy extends beyond occasional consultation?",
    ["UEFA recognises an official supporter interlocutor.", "It supports supporter involvement in club ownership and running.", "It works with accessibility specialists to improve stadium access."],
    ["Supporter groups are excluded from all formal stakeholder structures.", "Club licensing contains no supporter liaison or disability access requirements."],
    "The strategy creates ongoing relationships, specialised networks and operational requirements. Supporter liaison and disability access officers connect dialogue to club practice. This is more systematic than asking fans for feedback only when a crisis occurs.", 7, [52, 53],
)
add(
    "Which principles should guide a national association designing its own stakeholder forum from the UEFA example?",
    ["Recognise groups with democratic and transparent governance.", "Give major constituencies stable rather than ad hoc channels.", "Preserve clear statutory responsibility for final decisions.", "Review the forum as the stakeholder environment evolves."],
    ["Allow the best-funded stakeholder to bypass all governing bodies."],
    "The UEFA model combines legitimate representation, continuity and accountable decision rights. Consultation should be structured but should not obscure who is authorised to decide. Because the ecosystem evolves, the engagement design also needs periodic review.", 7, [52, 53],
)

# PDF pages 8-9 / handbook pages 54-57: competitions, solidarity and development.
add(
    "Who has ultimate authority over a club's participation in a UEFA international competition?",
    ["UEFA, after national associations put forward clubs from their countries."],
    ["The club's broadcaster.", "The IFAB acting without UEFA.", "The host city's local authority alone.", "The European Club Association without ratification."],
    "National associations nominate clubs, but UEFA retains final authority over participation in its competitions. This reflects subsidiarity within a common European regulatory framework. Commercial and stakeholder bodies may advise or influence policy but do not replace UEFA's competition authority.", 8, [54, 55],
)
add(
    "Why did UEFA create the Nations League in response to declining interest in friendlies?",
    ["It gives matches a competitive league structure with promotion and relegation.", "It groups more closely matched national teams to improve competitive balance."],
    ["It removes every qualification connection to other tournaments.", "It converts national teams into club franchises.", "It requires each association to sell media rights individually."],
    "The Nations League responds to stakeholder dissatisfaction with low-stakes friendlies by creating meaningful, balanced competition. Its tiered structure and links to qualification increase sporting relevance. Collective media-rights sales also distinguish it from fragmented individual bargaining.", 8, [54, 55],
)
add(
    "Which benefits can collective selling of Nations League media rights provide to participating associations?",
    ["UEFA can bargain for the competition as a coordinated property.", "Many associations receive higher revenues than they could secure individually for friendlies.", "Commercial value is linked to a season-long competitive product."],
    ["Every association is guaranteed identical sporting results.", "Collective selling eliminates UEFA's need to balance stakeholder interests."],
    "Collective selling aggregates rights around a coherent competition and can improve bargaining outcomes for smaller associations. The sporting structure makes the media product more attractive than isolated friendlies. It does not equalise results or remove the need for governance.", 8, [54, 55],
)
add(
    "Which statements illustrate UEFA's use of competitions as both sporting and strategic instruments?",
    ["National-team competitions can be redesigned to improve competitive meaning.", "Club competitions generate resources for participating and non-participating stakeholders.", "Youth, women's and futsal events support development objectives.", "Competition formats can widen representation across member associations."],
    ["A competition has strategic value only when every edition makes a direct profit."],
    "UEFA's portfolio serves several purposes at once: elite competition, commercial generation, representation and development. Some events are deliberately subsidised because they advance the wider mission. A purely direct-profit test would overlook those strategic effects.", 8, [54, 55],
)
add(
    "What does UEFA's distribution to non-participating clubs demonstrate most directly?",
    ["Sporting solidarity redistributes part of elite competition revenue beyond the participants."],
    ["Only competition winners benefit from central revenues.", "Grassroots development is financed solely by governments.", "Non-participating clubs may spend solidarity funds on any unrelated activity.", "UEFA rejects links between youth development and solidarity."],
    "Solidarity payments make the statutory redistribution principle tangible. Revenue generated at the top of the pyramid reaches clubs outside the competitions and is directed toward football development, especially youth. The mechanism therefore broadens benefits without treating the funds as unrestricted windfalls.", 9, [56, 57],
)
add(
    "Which objectives are served by adding a third UEFA club competition in the handbook's account?",
    ["Increase the minimum number of countries represented in group-stage club competition.", "Create a progression route in which the winner qualifies for the Europa League."],
    ["Eliminate the Champions League.", "Restrict group stages to clubs from fewer countries.", "Transfer club-competition authority to FIFA."],
    "The Europa Conference League was designed to widen access and create a sporting pathway into the Europa League. It complements rather than replaces UEFA's existing club competitions. The management logic combines representation with a connected competition hierarchy.", 9, [56, 57],
)
add(
    "Which statements explain why centralised marketing is important to UEFA's solidarity model?",
    ["UEFA sells broadcasting rights collectively on behalf of participating clubs.", "Aggregation helps maximise commercial revenue.", "A portion of the resulting value supports associations, non-participating clubs and development programmes."],
    ["Central marketing requires all revenue to stay with UEFA administration.", "It prevents any distribution to participating clubs."],
    "Centralised marketing pools valuable rights and strengthens UEFA's ability to exploit the property commercially. Most revenue may flow to participants, while part supports solidarity and development obligations. The model therefore links collective commercial power to distribution across the pyramid.", 9, [56, 57],
)
add(
    "Which criteria should a project satisfy to receive HatTrick development funding?",
    ["It should develop football within UEFA's territory.", "It should be of common interest to the football community.", "It should have a clear functional, educational and sporting purpose.", "It should fit a programme financed from UEFA EURO surpluses."],
    ["It must distribute profits to private shareholders as its primary aim."],
    "HatTrick converts EURO surpluses into structured football-development investment. Eligible projects must serve the game broadly and articulate practical, educational and sporting value. A private-profit-first proposal would not fit that programme logic.", 9, [56, 57],
)
add(
    "What is the HatTrick programme's multiplier or snowball effect?",
    ["UEFA funding encourages governments, authorities, sponsors, clubs or FIFA to contribute additional resources."],
    ["Each project automatically doubles the number of professional clubs.", "Funding is repeatedly transferred between the same UEFA accounts.", "Associations are discouraged from seeking co-funding.", "Only broadcast partners may add resources."],
    "The multiplier effect describes how an initial UEFA commitment can unlock further stakeholder investment. It is organisational and financial leverage, not an automatic mathematical doubling. Associations should use the programme to build credible partnerships around development projects.", 9, [56, 57],
)
add(
    "Which statements distinguish UEFA Grow from HatTrick in the chapter?",
    ["UEFA Grow works directly with associations on internal business-development capability.", "HatTrick primarily finances qualifying football-development activity from EURO surpluses."],
    ["UEFA Grow is a judicial appeal body.", "HatTrick regulates the Laws of the Game.", "Both programmes exist solely to finance senior men's transfer fees."],
    "The programmes support development through different levers. HatTrick provides structured project funding, while UEFA Grow strengthens an association's ability to develop its organisation on and off the pitch. Neither is a judicial or playing-law mechanism.", 9, [56, 57],
)

# PDF page 10 / handbook pages 58-59: licensing, sustainability, integrity and social responsibility.
add(
    "Which areas are covered by UEFA club-licensing minimum standards for entry to its competitions?",
    ["Sporting and infrastructure matters.", "Personnel and administration.", "Media and financial matters."],
    ["A guaranteed domestic league position.", "Exemption from all tax and employment obligations."],
    "Club licensing tests whether a club meets a broad organisational baseline, not merely whether its team qualified on the field. Sporting, infrastructure, staffing, administrative, media and financial standards all contribute to readiness. Licensing does not confer legal exemptions or protected league status.", 10, [58, 59],
)
add(
    "Which problems justified adding financial fair play to UEFA's club-licensing framework?",
    ["Large aggregate losses among European top-division clubs.", "Debt-financed spending on salaries and transfers.", "Threats to competition integrity and club survival.", "Cost pressure imposed on better-managed clubs."],
    ["An absence of any financial information from the licensing system."],
    "Licensing gave UEFA visibility of systemic financial instability and excessive debt-funded competition. Those practices endangered clubs, distorted sporting competition and raised costs for prudent organisations. Financial fair play was therefore an extension of an evidence-producing licensing framework, not a response made without data.", 10, [58, 59],
)
add(
    "What does the no-overdue-payables criterion require from a club?",
    ["Proof that debts to clubs, employees and social-security or tax authorities have been settled."],
    ["Proof that the club has never made an operating loss.", "Immediate repayment of every long-term stadium loan regardless of schedule.", "A squad composed only of domestic nationals.", "Approval from the IFAB for each transfer."],
    "The criterion focuses on due obligations to key football, employment and public creditors. UEFA may withhold competition prize money while overdue debts remain unsettled. It is narrower than a rule forbidding every loss or requiring accelerated payment of all long-term finance.", 10, [58, 59],
)
add(
    "Which statements describe the break-even requirement as introduced in the handbook?",
    ["It seeks to prevent clubs spending more than they earn.", "It is assessed for clubs wishing to participate in UEFA club competitions."],
    ["It guarantees that every club earns the same revenue.", "It applies only to national associations and never to clubs.", "It replaces all sporting qualification criteria."],
    "Break-even is a financial-sustainability control attached to UEFA competition participation. It constrains expenditure relative to earnings but does not equalise commercial capacity or replace sporting qualification. It operates alongside the wider club-licensing system.", 10, [58, 59],
)
add(
    "Which UEFA regulatory initiatives address integrity, development or inclusion beyond financial fair play?",
    ["A betting-fraud detection system.", "Rules promoting locally trained players.", "Anti-doping cooperation and education."],
    ["Nationality quotas that disregard EU law.", "A ban on supporter-accessibility officers."],
    "UEFA's wider regulatory portfolio addresses betting integrity, player development and doping. The locally trained-player rule is framed around training rather than nationality, respecting the Bosman context. Inclusion and accessibility are promoted rather than prohibited.", 10, [58, 59],
)
add(
    "Which statements correctly distinguish UEFA's locally trained-player rule from a nationality quota?",
    ["The rule requires a minimum number of locally trained players in the UEFA squad.", "It does not define those players by nationality.", "Its design avoids the nationality restriction found unlawful in the EU context.", "It promotes player development within member associations."],
    ["It requires all 25 squad members to hold the club's national citizenship."],
    "The rule targets where players were trained, not their passports. That distinction allows UEFA to promote local development while avoiding an unlawful nationality quota. It is therefore both a development instrument and a legally informed regulatory design.", 10, [58, 59],
)
add(
    "What is the purpose of UEFA's #EqualGame initiative within the Respect framework?",
    ["To promote inclusion and diversity in football."],
    ["To set transfer fees for locally trained players.", "To select hosts for FIFA competitions.", "To replace anti-doping testing.", "To license player intermediaries."],
    "#EqualGame gives renewed emphasis to inclusion and diversity within UEFA's wider Respect campaign. It is a values and social-impact initiative rather than a transfer, hosting or anti-doping mechanism. A good oral answer should locate it in UEFA's campaigning role.", 10, [58, 59],
)
add(
    "Which aims belong to UEFA's social-responsibility portfolio as described in the handbook?",
    ["Reduce discrimination and increase diversity.", "Foster social integration and reconciliation."],
    ["Limit football participation to elite athletes.", "Replace all public-health partners with commercial sponsors.", "Exclude charitable foundations from football activity."],
    "UEFA uses football's social reach to support inclusion, reconciliation, healthy lifestyles and football for all. Strategic partnerships and foundations extend that work beyond competitions. An elite-only or charity-excluding model would contradict the stated portfolio.", 10, [58, 59],
)

# PDF pages 11-12 / handbook pages 60-62: other confederations, UEFA Assist and conclusion.
add(
    "Which description correctly identifies CONMEBOL in the handbook?",
    ["It is the oldest regional confederation and was founded to organise South America's first national-team competition."],
    ["It governs football in Oceania.", "It was created by merging the two North American confederations.", "It has more member associations than CAF.", "It organises the UEFA Champions League."],
    "CONMEBOL was founded in 1916 around the organisation of the Copa América and is the oldest confederation. Its remit is South America, not Oceania or the CONCACAF region. Its small membership should not be confused with its strong historical sporting influence.", 11, [60, 61],
)
add(
    "Which examples show cooperation between UEFA and other regional confederations?",
    ["Memorandums of understanding provide frameworks for technical and organisational exchange.", "Cooperation can cover coaching, refereeing, competitions, women's football and administration."],
    ["UEFA automatically takes over the other confederation's competitions.", "Cooperation requires the partner to become a UEFA member.", "The agreements prohibit knowledge sharing between associations."],
    "UEFA uses formal agreements to share experience and support development across confederations. The subject matter can be broad, but the partner confederation retains its own identity and authority. Cooperation is therefore capacity-building rather than institutional annexation.", 11, [60, 61],
)
add(
    "Which statements describe the distinctive context of the Oceania Football Confederation?",
    ["It represents the smallest confederation region by total population.", "Many members are small South Pacific island states.", "Most members lack a professional domestic league."],
    ["Australia remains an OFC member in the handbook's account.", "Football is the dominant sport in every OFC member country."],
    "The OFC operates across small and dispersed football markets with limited professional infrastructure. Australia moved to the AFC, and most remaining members are island states where football is not dominant. Development support must therefore reflect a very different operating context from Europe.", 11, [60, 61],
)
add(
    "Which objectives define UEFA Assist?",
    ["Develop managerial capabilities in football and operations.", "Support youth development.", "Support small-scale infrastructure projects.", "Encourage cooperation between UEFA associations and associations in other confederations."],
    ["Finance only European senior club transfers."],
    "UEFA Assist packages external development support around management, youth, infrastructure and cooperation. It formalises earlier ad hoc assistance and spreads support across non-European associations with FIFA and the confederations. The programme is not a transfer-market subsidy.", 12, [62],
)
add(
    "How is UEFA Assist financed according to the chapter?",
    ["It rechannels FIFA Forward funds allocated to UEFA."],
    ["It is financed only from fines paid by players.", "It retains all HatTrick money inside Europe.", "It requires beneficiary associations to surrender FIFA membership.", "It is funded by selling the Laws of the Game."],
    "UEFA Assist uses FIFA Forward resources allocated to UEFA to support development outside Europe. That financing illustrates cooperation between global and regional governing levels. It does not depend on forfeiting membership or commercialising the playing laws.", 12, [62],
)
add(
    "Which management lessons follow from the chapter's concluding ecosystem metaphor?",
    ["New and existing stakeholder influence needs continuous evaluation.", "Strategic analysis should inform effective policy responses."],
    ["A successful structure never needs to adapt.", "Stakeholder complexity is a reason to stop consultation.", "Commercial performance is the only benefit produced by football governance."],
    "The chapter closes by returning to adaptation and equilibrium. Even a system that has served football well needs continuous stakeholder analysis and responsive policy. Its benefits span participation, spectatorship, well-being and business rather than a single commercial measure.", 12, [62],
)
add(
    "Which outcomes does the chapter attribute to effective organisation of football at global, regional and national levels?",
    ["Growth as a spectator sport.", "Growth as a participation sport.", "Contributions to public health and general well-being."],
    ["Elimination of every stakeholder conflict.", "Automatic immunity from external regulation."],
    "The organisational system has supported football's sporting, social and economic reach. Effective management does not make the ecosystem conflict-free or legally autonomous. Its value lies in coordinating complexity so that multiple public and football benefits can emerge.", 12, [62],
)
add(
    "Which statements form a strong final oral summary of how world football is organised?",
    ["Universal playing laws sit alongside a hierarchical governance pyramid.", "FIFA, confederations and national associations have distinct but overlapping roles.", "Commercial competitions help finance development and solidarity.", "Stakeholder engagement and strategic adaptation are necessary as the ecosystem changes."],
    ["The system works because every stakeholder operates independently without shared rules."],
    "World football combines common laws, layered institutions, competitions, regulation and redistributive development. Its actors are interdependent, so commercial and sporting success require cooperation and legitimate stakeholder engagement. The system's durability depends on adapting policy without losing coherent authority.", 12, [62],
)


# Second-pass distractor review: replace weaker alternatives with adjacent,
# source-grounded misconceptions that require genuine conceptual discrimination.
REVISED_DISTRACTORS = {
    1: ["FIFA's six confederations hold membership collectively on behalf of their national associations.", "Confederations supervise clubs directly, while national associations coordinate regional competitions.", "Countries may operate parallel recognised pyramids when each serves a different level of football.", "The IFAB provides the institutional link between domestic leagues and the confederations."],
    2: ["National associations contract senior players for international windows and release them to clubs between fixtures.", "Club and national-team football developed through separate governance structures coordinated by the international calendar.", "Broadcasters' calendar agreements provide the principal mechanism linking club and national-team competitions."],
    3: ["Professional football can sustain spectator demand through competitive quality even when participation declines.", "Grassroots investment supports the player pathway but has limited influence on audiences for elite league football."],
    4: ["Competition organisers need common sporting rules, while commercial and calendar decisions can remain bilateral."],
    6: ["A protected sphere of sporting regulation in areas closely connected to competition organisation.", "Retention of competition income by the organising bodies before discretionary development grants are made.", "Recognition of more than one domestic pyramid where promotion between them is formally coordinated."],
    7: ["Prioritise distributions to participating clubs because their sporting activity generated the surplus.", "Direct the surplus to national-team development because grassroots participation has separate public funding sources."],
    8: ["The ruling preserved football's transfer framework but required proportionate limits on foreign-player quotas."],
    9: ["Monitor the regulator as an external constraint while keeping the existing football stakeholder map unchanged.", "Rely on sporting autonomy until the regulator formally challenges a football rule.", "Rebalance influence among current football stakeholders before adding the regulator to strategic analysis.", "Address the regulator through the football rule-making bodies responsible for competition regulations."],
    10: ["A confederation aggregates its associations' Congress votes on regional matters.", "Confederations hold primary authority for regional national-team football, while FIFA membership concerns club competition.", "Associations participate in FIFA through their confederation rather than holding the two relationships concurrently."],
    11: ["A stakeholder map remains valid for the strategic period unless formal membership changes.", "Commercial growth reduces dependence on non-commercial stakeholders by strengthening football's internal resources."],
    12: ["Club-led calendars reconciled through bilateral release agreements with national associations."],
    13: ["To rank stakeholders according to their formal powers within UEFA's statutes.", "To document the current organisational network before strategic priorities are formulated.", "To distinguish football bodies from external actors that should be managed through public affairs.", "To assign consultation rights in proportion to each stakeholder's operational contribution."],
    14: ["UEFA member associations and the football bodies they formally recognise.", "European institutions and football organisations with a registered European headquarters.", "Cross-sport organisations, with football-specific commercial partners treated as market actors rather than stakeholders."],
    15: ["Consistent core Laws combined with regional discretion over selected playing provisions.", "Commercial investment in competitions, which finances later development of the playing rules."],
    19: ["Confederations allocate Congress representation in proportion to their number of member associations.", "Commercial contribution affects committee representation while Congress voting remains geographically weighted."],
    21: ["It is governed by FIFA as a parallel event rather than as part of the Olympic competition framework.", "Its age restriction applies to the complete squad at under-21 level.", "Entry is allocated through confederation coefficients rather than Olympic qualification.", "Domestic champion clubs represent their associations under national-team regulations."],
    22: ["Host-country revenues finance the event, while FIFA's central income is reserved for development.", "The event's commercial function supports FIFA administration, with development financed through member contributions.", "Membership subscriptions provide the stable base for development while World Cup rights cover competition costs."],
    23: ["Use a standard infrastructure package so funding remains comparable between associations.", "Replace project review with milestone reporting by the recipient association."],
    25: ["Distributions to member associations based on their commercial contribution to FIFA competitions.", "Capital investment in FIFA's central competition-delivery infrastructure.", "Development programmes financed from recurring membership and registration fees.", "Priority funding for senior competitions that generate resources for later development work."],
    26: ["Loss-making competitions should continue when they strengthen FIFA's commercial portfolio over the next cycle.", "Financing youth events is justified primarily when they create a pathway into profitable senior competitions.", "Competition deficits can be accepted as evidence of development commitment without separate outcome evaluation."],
    27: ["FIFA's development role is delivered through confederation programmes financed by commercial partners.", "Competition organisation generates resources but sits outside FIFA's statutory development responsibilities."],
    29: ["Recognising separate associations for professional and amateur football under a shared national framework.", "Using confederation recommendations as the decisive basis for national-association recognition.", "Operating domestic competitions directly where recognition disputes threaten the national pyramid.", "Linking recognition to an association's capacity to commercialise national competitions."],
    30: ["Setting common qualification standards for coaches working in international football.", "Approving club eligibility for confederation competitions through the international transfer system.", "Regulating domestic transfer fees and ticket pricing through member-association directives."],
    31: ["Government nomination is compatible with autonomy where the association receives substantial public funds.", "Presidential appointments concern association governance and are therefore handled through confederation mediation."],
    32: ["A club can decline release when a player's contractual value would be materially exposed by the international fixture."],
    33: ["The complainant association.", "The lead confederation.", "A confederation panel.", "The IFAB."],
    36: ["The Council exercises Congress authority between meetings and therefore represents the member associations in strategic votes."],
    38: ["Presidential continuity is protected by an open-ended mandate subject to periodic confidence votes.", "Women's representation is allocated through confederation policy rather than FIFA Council requirements.", "The Congress elects the president, who then confirms the confederations' Council nominees."],
    40: ["Operational supervision of domestic professional leagues where FIFA regulations affect player status."],
    41: ["UEFA's regional governance remit is broader, while FIFA concentrates on organising global competitions.", "FIFA retains operational responsibility for Europe's principal club competitions through UEFA.", "UEFA's recurring experience is concentrated in club competitions rather than national-team events.", "UEFA's club portfolio is centred on one global-format event complemented by regional qualifiers."],
    42: ["Membership structured around the commercial contribution of professional football stakeholders.", "Separate governance channels for elite clubs and the national associations responsible for development.", "Distribution weighted towards competition performance, with development funded through separate programmes."],
    43: ["To align UEFA regulations with political priorities before they are submitted to football's governing bodies.", "To preserve sporting autonomy by limiting cooperation to areas outside football regulation."],
    45: ["National associations retain discretion over implementation when Congress decisions concern domestic football.", "UEFA intervenes directly where consistent European implementation is more efficient than national delivery.", "Professional stakeholders exercise delegated implementation authority in commercially significant domains.", "Local sponsors may adapt implementation standards where they finance association programmes."],
    46: ["Confirming national-association presidents as Congress delegates.", "Approving club eligibility lists for UEFA competitions.", "Adopting European variations to the playing rules."],
    47: ["The president may act between Congress meetings subject to later Executive Committee ratification.", "Professional stakeholder bodies nominate Congress delegates alongside the member associations."],
    48: ["Its voting membership combines association representatives with delegates from clubs, leagues and broadcasters."],
    49: ["The UEFA president.", "A UEFA vice-president.", "The chair of the Professional Football Strategy Council.", "The director of national-association governance."],
    50: ["The Executive Committee reviews disciplinary appeals involving strategic competition matters.", "Independent disciplinary inspectors are nominated jointly with recognised stakeholder groups.", "CAS review is available after UEFA's administrative bodies confirm the disciplinary decision."],
    53: ["Professional stakeholders gained voting rights that displaced parts of the association-based structure.", "The IFAB's regulatory reforms required leagues and clubs to participate in UEFA governance.", "The growth of club competitions made informal bilateral consultation sufficient for stakeholder management.", "European legal pressure led UEFA to consult public authorities while keeping football stakeholders outside formal structures."],
    54: ["It should demonstrate commercial activity across a representative group of UEFA markets.", "It should represent interests that are not already expressed through member associations.", "It should maintain a staffed liaison office located close to UEFA's administration."],
    55: ["Representatives of clubs, leagues and players, with member associations participating through the Executive Committee.", "A neutral representative of the European sports movement acting as chair."],
    59: ["Supporter dialogue is channelled through recurring forums rather than representation in strategic bodies.", "Club licensing addresses stadium operations, while supporter liaison and accessibility remain consultation topics."],
    60: ["Weight formal influence according to the resources and implementation capacity each stakeholder contributes."],
    61: ["The nominating association's licensing body.", "The domestic league awarding qualification.", "The European Club Association.", "The host association validating the venue."],
    62: ["It separates friendlies from qualification pathways so the new competition can focus on competitive balance.", "It applies club-style league structures to association teams through centrally managed franchises.", "It coordinates fixtures centrally while leaving participating associations to market their media rights."],
    63: ["Collective selling equalises the sporting resources available to the participating national teams.", "Collective selling reduces the need for separate policies on competitive balance and solidarity."],
    64: ["A competition becomes strategically valuable when its commercial return can finance its direct participants."],
    65: ["Central revenues flow principally to participating clubs, with non-participants supported through domestic association programmes.", "Grassroots development is supported through HatTrick rather than club-competition solidarity.", "Non-participating clubs may use solidarity funding for general first-team operating expenditure.", "Youth development is a desirable consequence of solidarity but is not an explicit distribution purpose."],
    66: ["Consolidate the Champions League and Europa League into a wider two-tier competition.", "Reduce group-stage access so qualifying rounds can include more associations.", "Coordinate UEFA's club portfolio with FIFA through shared competition authority."],
    67: ["Central marketing retains a larger competition reserve before development distributions are considered.", "It directs solidarity through associations rather than making distributions to participating clubs."],
    69: ["UEFA funding increases a project's scale through standard matching grants from the association.", "Initial investment is recycled into later HatTrick allocations after projects generate savings.", "Associations are expected to complete projects with programme funding before approaching public partners.", "Commercial partners provide the principal co-financing because the projects use UEFA competition revenues."],
    71: ["A minimum domestic sporting position set consistently across UEFA associations.", "Compliance with financial obligations assessed through national company-law certification."],
    73: ["Evidence that the club's operating result is compatible with its approved break-even forecast.", "Settlement of long-term infrastructure debt before the licensing decision.", "Compliance with the locally trained-player quota for the submitted squad.", "Confirmation that transfer liabilities have been registered through FIFA's systems."],
    74: ["It narrows acceptable revenue differences between clubs through a common spending ceiling.", "It is assessed by national associations as part of their own financial performance.", "It forms part of sporting access by replacing coefficient-based qualification where finances are weak."],
    76: ["It sets a citizenship-based minimum for the players registered in UEFA competition squads."],
    78: ["Direct inclusion funding towards elite player pathways.", "Deliver public-health work through competition sponsors.", "Separate charitable foundations from football-development programmes."],
    79: ["It is the newest confederation, created for South American club football.", "It was created by merging South America's regional associations with CONCACAF.", "It has the largest membership among the six confederations.", "It was founded to organise South America's first international club competition."],
    80: ["UEFA administers agreed development projects within the partner confederation's competition structure.", "The partner confederation participates through an associate relationship with UEFA.", "Cooperation focuses on institutional agreements rather than direct exchange between member associations."],
    81: ["Australia remains part of OFC's development environment while competing through the AFC.", "Football has a strong participation base across OFC despite limited professional league structures."],
    82: ["Support professional-club development projects in emerging European football markets."],
    83: ["It uses disciplinary and competition fines earmarked for international development.", "It reallocates a defined share of HatTrick development funding to projects outside Europe.", "Beneficiary associations contribute a proportion of their FIFA Forward allocation to the programme.", "It is financed through a joint UEFA-IFAB development budget."],
    84: ["The established pyramid should be preserved by managing new stakeholders through existing channels.", "Increasing stakeholder complexity favours selective consultation with actors holding formal responsibilities.", "Commercial and sporting performance provide the principal evidence that governance is producing value."],
    85: ["Greater institutional control over football-related stakeholder disputes.", "Stronger regulatory autonomy for football's governing bodies."],
    86: ["The system is effective because responsibilities are clearly separated between governing levels and stakeholder groups."],
}

for question_number, replacements in REVISED_DISTRACTORS.items():
    question = QUESTIONS[question_number - 1]
    correct = set(question["answer"]["correct_options"])
    false_positions = [index for index in range(5) if index not in correct]
    assert len(false_positions) == len(replacements), question_number
    for position, replacement in zip(false_positions, replacements):
        question["options"][position] = replacement


# Store the reviewed oral-exam blueprint on every item so the planned balance
# is independently auditable rather than living only in an editor's notes.
APPLICATION_QUESTIONS = {
    1, 3, 4, 6, 7, 9, 11, 12, 13, 17, 22, 23, 25, 26, 27, 29, 30, 31,
    32, 33, 34, 39, 40, 43, 45, 53, 54, 56, 59, 60, 62, 63, 64, 65, 66, 67,
    68, 69, 70,
}
FACTUAL_ANCHOR_QUESTIONS = {
    5, 14, 18, 19, 21, 24, 35, 37, 46, 49, 51, 55, 57, 61, 73, 79, 83,
}
assert APPLICATION_QUESTIONS.isdisjoint(FACTUAL_ANCHOR_QUESTIONS)
for question in QUESTIONS:
    number = question["q_number"]
    if number in APPLICATION_QUESTIONS:
        question["oral_exam_category"] = "application"
    elif number in FACTUAL_ANCHOR_QUESTIONS:
        question["oral_exam_category"] = "factual_anchor"
    else:
        question["oral_exam_category"] = "explanation"


def main() -> None:
    assert 80 <= len(QUESTIONS) <= 120, len(QUESTIONS)
    payload = {
        "schema_version": 1,
        "library_key": "uefa_cfm",
        "chapter_number": 15,
        "session_title": "Chapter 1 - The organisation of world football",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
