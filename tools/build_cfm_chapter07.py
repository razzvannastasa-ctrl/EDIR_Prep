"""Build the staged Chapter 7 UEFA CFM football and social responsibility bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "UEFA-HFM-Football-and-social-responsibility.pdf"
OUTPUT = Path("data/cfm_imports/chapter_07_football_and_social_responsibility.json")
QUESTIONS: list[dict] = []


def _positions(number: int, count: int) -> list[int]:
    group = (number - 1) % 5
    return {
        1: [group % 5],
        2: sorted({group % 5, (group + 2) % 5}),
        3: sorted({group % 5, (group + 2) % 5, (group + 4) % 5}),
        4: [position for position in range(5) if position != (group + 1) % 5],
    }[count]


def add(page, category, stem, true, false, explanation):
    number = len(QUESTIONS) + 1
    expected_count = (number - 1) % 4 + 1
    assert len(true) == expected_count, (number, len(true), expected_count)
    positions = _positions(number, len(true))
    assert len(false) == 5 - len(positions), (number, len(false), positions)
    ti, fi = iter(true), iter(false)
    options = [next(ti) if i in positions else next(fi) for i in range(5)]
    QUESTIONS.append({
        "q_number": number,
        "question_text": stem,
        "q_type": "multiple_choice",
        "oral_exam_category": category,
        "options": options,
        "source_locator": {
            "file": SOURCE,
            "pdf_pages": [page],
            "handbook_pages": [196 + 2 * page, 197 + 2 * page],
        },
        "page_crops": [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 200-201: definition, commercialisation and purpose.
add(2, "application", "A national association treats social responsibility as an annual charitable donation. What is the strongest correction?",
    ["Integrate moral, social and environmental concerns into the association's core functions and stakeholder relationships."],
    ["Place philanthropy within the commercial department so its reputational return can be assessed.", "Use donations as the public-facing strand while operational departments manage related risks.", "Link charitable spending to the social issues most visible to the association's supporters.", "Separate community activity from football operations so each can pursue clearer objectives."],
    "An integrative FSR approach places moral, social and environmental concerns inside core structures and processes. Charity can help people, but it is too narrow to define FSR. Stakeholder dialogue should help the association tackle societal issues proactively and create positive impact.")
add(2, "explanation", "Which features distinguish the chapter's integrative definition of FSR?",
    ["Moral, social and environmental concerns enter core organisational functions.", "Stakeholder dialogue supports proactive action on societal issues."],
    ["Community investment is managed as a counterpart to football's commercial activity.", "Reputational protection supplies the principal test for selecting social issues.", "Positive impact is assessed through the benefits returned to the football organisation."],
    "The definition joins responsible internal practice with engagement beyond the organisation. Stakeholder dialogue helps identify and address societal issues rather than merely publicising charitable activity. Positive societal impact is an intended result, not a calculation confined to organisational return.")
add(2, "factual_anchor", "Which elements belong to the chapter's eight-part approach to FSR strategy development?",
    ["Stakeholder management.", "Issue management.", "Monitoring and evaluation."],
    ["Commercial rights management.", "Volunteer workforce planning."],
    "The eight elements are vision and mission, stakeholder management, issue management, the Sustainable Development Goals, a path model, implementation, monitoring and evaluation, and reporting and communication. Commercial rights and volunteer planning may interact with FSR but are not named elements of this framework.")
add(2, "application", "A highly commercialised club faces growing concern about its social impact. Which responses fit the chapter's reasoning?",
    ["Engage the stakeholders affected by the club's activities.", "Adopt decent moral, social and environmental practices.", "Use responsible action to strengthen legitimacy.", "Keep football's wider purpose in view when judging commercial choices."],
    ["Define the response through the issues that offer the clearest competitive return."],
    "Commercialisation increases both football's societal impact and the pressure to legitimise its conduct. Responsible practice and stakeholder engagement can protect reputation and support organisational objectives. The business case is useful, but football's purpose prevents competitive return from becoming the full decision rule.")
add(2, "explanation", "Why is the business case an incomplete foundation for FSR?",
    ["It values responsible conduct through organisational benefit but does not capture football's broader purpose and societal responsibility."],
    ["It concentrates on financial return while the chapter defines FSR through reputational value.", "It applies most clearly to professional clubs while associations require a values-based approach.", "It assesses stakeholder demands after core football objectives have been established.", "It frames social action as risk management while proactive FSR concerns charitable impact."],
    "The business case asks how responsibility can improve reputation, legitimacy or competitive advantage. Those benefits matter, yet FSR also asks what football owes society and what positive difference it should make. Purpose over profit therefore broadens the basis for action.")
add(2, "application", "A proposed sponsorship is profitable but conflicts with the association's sporting values. Which considerations follow the chapter?",
    ["Judge the proposal against football's mission as well as its commercial return.", "Give sporting values precedence when the commercial interest conflicts with purpose."],
    ["Accept the proposal if stakeholder dialogue shows that the reputational risk can be managed.", "Treat the conflict as a social-impact issue after the sponsorship objectives are agreed.", "Balance the values concern against the competitive advantage funded by the partnership."],
    "The chapter presents purpose over profit as a governing idea and cites UEFA's objective that sporting values prevail over commercial interests. Stakeholder and business considerations inform the decision, but they do not neutralise a conflict with mission. The association should therefore apply its values before treating the issue as a communications problem.")
add(2, "explanation", "How are commercialisation and moralisation connected in professional football?",
    ["Greater commercial power increases football organisations' impact on society.", "That impact creates stronger demands for responsible conduct.", "Responsible practice helps organisations maintain legitimacy."],
    ["Moral pressure grows when commercial objectives reduce investment in community programmes.", "Commercial legitimacy depends on demonstrating a direct return from social initiatives."],
    "The chapter describes commercialisation and moralisation as two sides of the same coin. As football organisations resemble influential businesses, society expects them to address moral, social and environmental effects. Responsible practice answers that pressure and can strengthen legitimacy without reducing FSR to a business calculation.")
add(2, "application", "An association is setting the scope of its first FSR strategy. Which choices are well founded?",
    ["Include problematic practices connected with football.", "Include positive practices through which football can benefit society.", "Cover moral, social and environmental concerns.", "Use stakeholder dialogue to identify issues requiring proactive attention."],
    ["Limit the first strategy to issues for which the association controls the social outcome directly."],
    "FSR covers bad practices, good practices and the organisation's wider influence on society. Its scope crosses moral, social and environmental concerns and is informed by affected stakeholders. Direct control is too narrow because football organisations can support solutions through their influence and relationships.")

# PDF page 3 / handbook pages 202-203: charity, reactive and proactive FSR.
add(3, "application", "A club stages a benefit match and presents it as its complete FSR model. How should the activity be classified?",
    ["It is philanthropy that can help people but remains an end-of-pipe conception of FSR."],
    ["It is reactive FSR because the club is responding to an identified social need.", "It is proactive FSR because the activity aims to create a positive societal effect.", "It is integrative FSR because match operations are being used for a social purpose.", "It is responsible profit-seeking because the event joins revenue generation with solidarity."],
    "A benefit match is a clear example of charity or philanthropy. Its value is real, but it is not systematically integrated into the organisation's principal operations or objectives. Integrative FSR asks how revenue is generated and core football activity is conducted, not merely how proceeds are spent.")
add(3, "explanation", "What separates charity from an integrative approach to FSR?",
    ["Charity distributes money, time or skills after resources have been generated.", "Integrative FSR examines how core activities generate revenue and affect society."],
    ["Charity responds to outside-in issues while integrative FSR concentrates on inside-out risks.", "Charity builds social legitimacy while integrative FSR builds organisational legitimacy.", "Charity is appropriate for clubs, while integrative FSR is designed for governing associations."],
    "Charity is philanthropic and tends to sit at the end of the organisational process. Integrative FSR changes the way the core business operates and seeks revenue responsibly. The distinction concerns integration into operations, rather than the governing level or the legitimacy of the cause.")
add(3, "factual_anchor", "Which three conceptions of FSR are distinguished in the chapter?",
    ["FSR as charity.", "Reactive FSR.", "Proactive FSR."],
    ["Regulatory FSR.", "Competitive FSR."],
    "The chapter distinguishes charity, reactive FSR and proactive FSR. Charity is philanthropic, reactive FSR avoids bad practice and proactive FSR integrates good practice while addressing societal problems. Regulatory and competitive effects may influence action but are not separate conceptions in the typology.")
add(3, "application", "An association is addressing corruption risks and a serious local inclusion problem. Which elements form a coherent FSR response?",
    ["Use controls to reduce corruption risk.", "Treat the risk work as an inside-out responsibility.", "Engage with the inclusion problem through an outside-in perspective.", "Keep both strands compliant with the law."],
    ["Present the inclusion programme as the proactive counterpart that replaces further risk analysis."],
    "Reactive FSR addresses organisational bad practices through risk and reputation management. Proactive FSR retains that discipline and also asks how football can help solve pressing societal problems. Legal compliance is required in both, and proactive work supplements rather than replaces risk analysis.")
add(3, "explanation", "What is the defining starting point of reactive FSR?",
    ["Problems and risks arising inside the football organisation."],
    ["Societal issues that football can address through its reach.", "Stakeholder claims with strong moral legitimacy but limited influence.", "Philanthropic opportunities related to the organisation's revenue base.", "Strategic issues that can differentiate the organisation from competitors."],
    "Reactive FSR starts inside the organisation by identifying bad practices and associated risks. Fraud, corruption, match-fixing and doping illustrate this focus. Societal problem-solving and strategic differentiation belong to the proactive extension of FSR.")
add(3, "factual_anchor", "Which characteristics are associated with proactive FSR?",
    ["An outside-in focus on societal problems.", "A strategic orientation linked to the organisation's core activity."],
    ["A philanthropic focus on distributing football-generated revenue.", "A compliance focus that treats responsibility as a cost of doing business.", "A reputation focus that ranks issues by their media visibility."],
    "Proactive FSR considers societal needs from the outside in and connects good practice to core strategy. It still considers organisational risks and legal duties. Philanthropy, compliance and reputation management describe narrower or more reactive approaches.")
add(3, "application", "A club wants to claim a proactive FSR approach. Which evidence would support that claim?",
    ["It manages risks connected with bad practices.", "It integrates good practice into core management.", "It supports a pressing societal issue related to football's capabilities."],
    ["It directs charitable spending towards causes selected by commercial partners.", "It treats legal compliance as evidence that societal expectations have been met."],
    "Proactive FSR goes beyond risk management without abandoning it. The club should integrate responsible practice into its core work and use football-related capabilities to address societal problems. Partner-supported charity and compliance can contribute, but neither demonstrates the full proactive model.")
add(3, "explanation", "In what ways does proactive FSR extend the reactive model?",
    ["It adds good practice to the avoidance of bad practice.", "It examines societal issues as well as organisational risks.", "It seeks strategic differentiation through responsible core activity.", "It asks how football can contribute to changing society."],
    ["It shifts legal compliance into stakeholder dialogue so social priorities can shape the applicable standard."],
    "Proactive FSR keeps the reactive concern with risk and legality, then adds an outside-in and strategic dimension. It connects football's core activity with societal problem-solving and positive practice. Stakeholder dialogue informs priorities, but it does not redefine legal compliance.")

# PDF page 4 / handbook pages 204-205: issue map, diversity and inclusion.
add(4, "application", "A club assigns each social issue to a single department before stakeholder consultation. What is the main weakness in this approach?",
    ["FSR issues overlap across stakeholders and organisational departments, so isolated ownership can miss important connections."],
    ["Departmental ownership gives internal risks more weight than community expectations.", "Consultation is most useful after departments have defined the issues they can influence.", "A single owner makes it harder to rank issues through reputational and operational criteria.", "Issue maps are intended to compare societal themes rather than allocate organisational responsibility."],
    "The issue map shows that concerns such as discrimination, health, human rights and the environment are interconnected. They touch several stakeholder groups and functions, including grassroots, marketing, HR and event management. Clear ownership helps delivery, but strategy needs cross-functional and stakeholder coordination.")
add(4, "explanation", "Why does the chapter present an FSR issues map rather than a fixed checklist?",
    ["It illustrates the breadth and interconnectedness of relevant concerns.", "It prompts each football organisation to identify issues with its own stakeholders and departments."],
    ["It separates inside-out risks from outside-in opportunities before materiality is assessed.", "It ranks concerns according to their proximity to football operations.", "It provides a common reporting structure for associations and clubs."],
    "The map is illustrative and expressly non-exhaustive. Its purpose is to reveal connections between issues, stakeholder claims and organisational functions. Each association or club must still determine which concerns are material in its own context.")
add(4, "factual_anchor", "Which characteristics are examples of deep-level diversity in the chapter?",
    ["Family status.", "Work style.", "Religion."],
    ["Age.", "Gender."],
    "Deep-level diversity concerns less visible characteristics such as family status, work style, religion, personality and work values. Age and gender are presented as surface-level characteristics. The layers can overlap, but the distinction helps managers look beyond readily observed differences.")
add(4, "application", "A football association wants employees and participants to experience genuine inclusion. Which practices fit the chapter's definitions?",
    ["Recognise that individuals have distinct characteristics.", "Reject discrimination across the identified diversity dimensions.", "Provide fair treatment and meaningful involvement.", "Manage behaviours and social norms so people feel welcome."],
    ["Use representation across visible characteristics as the principal evidence that belonging has been achieved."],
    "Diversity concerns uniqueness, while inclusion concerns fair treatment, meaningful involvement and a culture of welcome. Representation can be informative, but visible composition does not show whether people belong. The organisation must manage behaviour and norms as well as access.")
add(4, "explanation", "What is the clearest distinction between diversity and inclusion?",
    ["Diversity describes human differences, while inclusion describes the treatment and norms that create welcome and involvement."],
    ["Diversity concerns workforce composition, while inclusion concerns participation in football activities.", "Diversity is measured through visible traits, while inclusion is assessed through less visible traits.", "Diversity is an internal management issue, while inclusion is a contribution to society.", "Diversity identifies protected groups, while inclusion determines which claims are materially significant."],
    "Diversity asks what makes people unique; inclusion asks how people are treated and involved. Surface and deep characteristics both belong to diversity, while welcome and belonging require inclusive norms. The distinction applies inside football organisations and in society.")
add(4, "application", "A recruitment team considers age and education but overlooks work style and family status. Which conclusions are justified?",
    ["The team is concentrating on surface-level diversity.", "Its assessment misses deep-level characteristics that may shape how people work together."],
    ["The team has captured diversity but still needs an inclusion measure for hidden characteristics.", "The omitted characteristics become relevant after candidates join the organisational culture.", "The surface-level review is sufficient if recruitment decisions apply the same formal criteria."],
    "Age and education are presented at the surface level, whereas work style and family status sit at the deep level. Both layers can affect relationships and organisational experience. Formal equality does not remove the need to understand less visible differences.")
add(4, "explanation", "How should a manager understand the relationship between surface-level and deep-level diversity?",
    ["The layers partly overlap.", "Visible characteristics may correspond with less visible experience or styles.", "Both layers can influence cohesion and inclusion."],
    ["Deep-level characteristics become more reliable once surface-level categories are recorded.", "Surface-level differences are organisational data, while deep-level differences are stakeholder perceptions."],
    "The two layers are analytically useful but not sealed categories. Age may relate to work experience, and education may be reflected in work or communication style. Effective inclusion therefore considers the interaction of visible and less visible characteristics.")
add(4, "application", "A national association is building its first FSR issue inventory. Which actions reflect the issue-map approach?",
    ["Include governance risks such as fraud and questionable contracts.", "Include health, environment and human-rights concerns.", "Examine discrimination and inclusion as connected themes.", "Identify the stakeholders and departments touched by each issue."],
    ["Retain issues that appear in the map before adding concerns raised through local consultation."],
    "The map spans bad practices, social needs and environmental concerns and highlights their overlap. It is a starting point for contextual analysis, not a prescribed catalogue. Local stakeholders and departments should help reveal further concerns and determine relevance.")

# PDF page 5 / handbook pages 206-207: inclusion challenges and climate impact.
add(5, "application", "An association improves disability access for employees but takes no role in access to football in society. How should its inclusion work be assessed?",
    ["It addresses internal inclusion but leaves the association's wider societal inclusion challenge incomplete."],
    ["It addresses the primary diversity layer but needs a deep-level inclusion policy.", "It fulfils the organisational strand and should treat social access as a partner responsibility.", "It manages an infrastructure issue while the FSR challenge concerns equal recruitment and conduct.", "It demonstrates reactive inclusion but requires a separate philanthropic programme for participants."],
    "The chapter describes a twofold challenge: manage diversity and inclusion inside the football organisation and contribute to inclusion in society. Accessible employment infrastructure belongs to the internal strand. Playing opportunities and wider access require a second, outward-facing effort.")
add(5, "explanation", "How do the two inclusion challenges for football organisations differ?",
    ["The internal challenge concerns employment, policy, training and accessible workplaces.", "The societal challenge concerns using football to widen participation and tackle exclusion."],
    ["The internal challenge is driven by regulation, while the societal challenge is driven by stakeholder urgency.", "The internal challenge concerns surface diversity, while the societal challenge concerns deep diversity.", "The internal challenge manages risk, while the societal challenge funds specialist football formats."],
    "Internal inclusion covers the organisation's own recruitment, staff conduct and accessibility. Societal inclusion uses football's reach to address barriers and provide meaningful participation. Regulation may support either strand, but it does not define the distinction.")
add(5, "factual_anchor", "Which practices are listed as part of managing diversity and inclusion inside a football organisation?",
    ["Equal recruitment policy and job opportunities.", "Staff training with corrective action after incidents.", "Accessible infrastructure for disabled employees."],
    ["A hotline for reporting incidents across the national game.", "Playing opportunities adapted to different impairments."],
    "The internal examples concern recruitment, staff policy and an accessible workplace. Reporting hotlines and adapted forms of football illustrate contributions to inclusion in society. Both strands matter, but they operate through different organisational responsibilities.")
add(5, "application", "A club learns that fan travel dominates its matchday carbon footprint. Which management responses fit the evidence presented?",
    ["Measure supporter mobility within the event footprint.", "Engage transport and supporter stakeholders in reduction planning.", "Give material attention to indirect travel emissions.", "Set priorities according to emission significance rather than ease of departmental control."],
    ["Concentrate the initial plan on heating and the vehicle fleet because the club can change those sources directly."],
    "The Wolfsburg example attributes roughly 60% of emissions to fan mobility, showing why indirect effects can dominate. A credible plan measures and manages material sources with relevant partners. Directly controlled energy still matters, but ease of control should not displace the largest source.")
add(5, "explanation", "Why does climate change create a dual responsibility for football organisations?",
    ["Football contributes emissions while its activities and facilities are also exposed to climate-related disruption."],
    ["Football creates matchday emissions while mega-events carry the sector's wider climate exposure.", "Clubs manage operational emissions while governing bodies manage adaptation risks.", "Climate action protects reputation while weather resilience protects competition continuity.", "Professional football drives travel emissions while grassroots football bears the physical consequences."],
    "Football is both a contributor to global warming and a sector affected by it. Travel, events and operations create emissions, while heat, flooding, storms and other conditions can disrupt play. Mitigation and adaptation therefore belong in the same strategic conversation.")
add(5, "factual_anchor", "Which findings are reported in the chapter's football carbon examples?",
    ["An average Bundesliga league game was estimated at about 870 tonnes of CO2 equivalent.", "VfL Wolfsburg attributed about 60% of its emissions to fan mobility."],
    ["A Bundesliga matchday was estimated at about 870 tonnes across the league.", "VfL Wolfsburg identified heating energy as its largest controlled source.", "A season's fan travel was estimated to require about 260,000 trees for offsetting."],
    "The cited study estimated roughly 870 tonnes for one average Bundesliga match and about 260,000 tonnes for a season. Wolfsburg's footprint placed fan mobility near 60%, far above heating or fleet emissions. These figures illustrate scale and priority rather than a universal benchmark.")
add(5, "application", "Repeated extreme weather is disrupting a club's fixtures. Which conclusions should inform its FSR response?",
    ["Treat climate exposure as an operational and economic risk.", "Assess how changing conditions affect pitches, events and participants.", "Combine emission reduction with practical resilience planning."],
    ["Classify cancellations as a facilities issue until a materiality review links them to stakeholder decisions.", "Prioritise compensation for lost fixtures before investing in weather resilience."],
    "The chapter links extreme weather with cancellations, difficult playing conditions and financial harm. Climate action therefore includes understanding football's own exposure as well as reducing its contribution. A cross-functional response is stronger than treating disruption as a narrow facilities matter.")
add(5, "explanation", "Which ideas are demonstrated by the chapter's climate-impact discussion?",
    ["Football activities generate a significant carbon footprint.", "Fan mobility can be the largest emission source.", "Major sports events can create emissions on a very large scale.", "Extreme weather can disrupt several sports and damage football operations."],
    ["The sector's climate priority should be set by the sources measured within venue operations."],
    "The discussion joins footprint evidence with evidence of physical disruption. It shows that emissions extend beyond the venue and that fan mobility can dominate a club's total. It also establishes that climate action is both a responsibility to society and a way to protect the future of sport.")

# PDF page 6 / handbook pages 208-209: climate exposure and Forest Green Rovers.
add(6, "application", "A club wants to reduce the environmental effect of matchday food. Which Forest Green Rovers practice offers the most integrated example?",
    ["Serve plant-based food and send leftover food waste to a nearby composting centre."],
    ["Source beer and wine from local breweries and report their transport footprint.", "Offer plant-based player meals while retaining a broader spectator menu.", "Use food-waste composting as the offset for emissions from catering supply.", "Link the matchday menu to injury and performance indicators for players."],
    "Forest Green Rovers combines a plant-based matchday offer with local composting of leftovers. This addresses both the content of consumption and the waste stream. Local sourcing and player outcomes may support the story, but they are not the integrated practice described here.")
add(6, "explanation", "What makes the Forest Green Rovers example strategically useful rather than a single environmental gesture?",
    ["It applies environmental choices across several core areas of club operation.", "It links facilities, food, travel, equipment and partnerships to a coherent ethos."],
    ["It concentrates environmental decisions in areas visible to supporters and sponsors.", "It combines emission reduction with offsets that establish carbon neutrality.", "It uses commercial partnerships to fund environmental projects beyond football operations."],
    "The example is a portfolio: energy, pitch care, food, plastics, kits, transport and partners reinforce one another. That breadth shows environmental responsibility embedded in the club's operation and identity. Visibility and offsetting contribute, but they do not explain the coherence of the model.")
add(6, "factual_anchor", "Which environmental practices are described for Forest Green Rovers' stadium and pitch?",
    ["Roof-mounted solar panels provide part of the ground's power.", "The remaining electricity comes from a wind- and solar-powered grid.", "Captured rainwater is used to irrigate the pitch."],
    ["Ground heating is supplied by a local biomass network.", "Pitch cuttings are transferred to the nearby food-composting centre."],
    "The club uses roof solar panels, renewable grid electricity and captured rainwater. It also feeds the pitch with seaweed and cuts it using electric and solar-powered equipment. The example shows operational measures rather than a reliance on a single technology.")
add(6, "application", "A club is redesigning team and supporter travel around the Forest Green Rovers example. Which measures are source-grounded?",
    ["Offset fan travel without increasing the match-ticket price.", "Place rapid electric charging in attractive parking locations.", "Use electric vehicles for team and kit transport.", "Reduce travel by keeping training and camps closer to home."],
    ["Use the offset portfolio to defer travel reduction until electric transport can cover the full team schedule."],
    "Forest Green Rovers combines offsets, incentives for electric vehicles, changes to team transport and reduced travel demand. These measures operate at different points in the travel system. Offsetting supports the plan but does not substitute for practical reduction and modal change.")
add(6, "explanation", "What principle governs Forest Green Rovers' selection of commercial partners?",
    ["Partners can differ in their activities, but they must align with the club's people-before-profit ethos."],
    ["Partners should contribute products that replace a higher-impact part of club operations.", "Local partners receive preference when their services reduce transport emissions.", "Environmental partners should provide a measurable benefit to the club's carbon account.", "Sponsors may support separate causes if the partnership revenue advances the club's wider programme."],
    "The club does not require partners to mirror each initiative. It does require alignment with its underlying ethos, which protects strategic coherence. A product, locality or measured saving can be useful, but values fit is the governing criterion in the example.")
add(6, "application", "A kit and concessions review aims to reduce material waste. Which actions follow the chapter's examples?",
    ["Replace single-use water bottles and plastic cups with refill and biodegradable alternatives.", "Trial kit fabrics using lower-impact or recycled materials and incorporate player feedback."],
    ["Retain conventional kit fabric until a replacement delivers a verified carbon saving.", "Use bamboo for supporter merchandise while team kits are evaluated against performance requirements.", "Fund recycling through a levy on bottled drinks and replica kits."],
    "Forest Green Rovers uses refill stations and plant-based biodegradable cups and has tested bamboo and recycled kit materials. Player feedback informed the later fabric decision, showing that environmental and operational criteria can be combined. The approach is iterative rather than dependent on a single certification threshold.")
add(6, "explanation", "What lessons about credible climate action emerge from the Forest Green Rovers case?",
    ["Operational choices should address several material sources.", "Innovation can be tested and revised through practical feedback.", "Partners should reinforce the organisation's environmental values."],
    ["Carbon offsetting provides the common measure that connects operational initiatives.", "Public recognition is needed to turn separate environmental actions into an FSR strategy."],
    "Credibility comes from embedding climate action across daily operations and relationships. The club experiments, learns and chooses partners consistent with its ethos. Offsetting and recognition appear in the case, but the strategic substance lies in the connected operational changes.")
add(6, "application", "A national association wants clubs to learn from the Forest Green Rovers case. Which guidance would preserve the chapter's logic?",
    ["Begin with the material environmental effects of football operations.", "Build a connected portfolio rather than a publicity-led flagship.", "Include supporters, suppliers and partners in the response.", "Adapt measures through operational trials and evidence."],
    ["Use the club's practices as a minimum programme before associations add locally relevant measures."],
    "The case is an example of integrative practice, not a universal checklist. Associations should identify material effects, engage the actors connected to them and combine initiatives coherently. Local adaptation and learning preserve the strategic logic better than copying a fixed package.")

# PDF page 7 / handbook pages 210-211: vision, mission and event stakeholders.
add(7, "application", "An association's FSR statement lists projects but gives no account of purpose or values. What should be added first?",
    ["A vision and mission that act as a moral compass for choices and commitments."],
    ["A materiality ranking that shows why each project deserves organisational resources.", "A stakeholder map that assigns each project to the group most affected by it.", "A set of no-go areas derived from the risks already present in the project portfolio.", "A communications promise linking each project with the association's strategic plan."],
    "Vision and mission define why the organisation exists, what it seeks and the values guiding its conduct. In FSR they provide the moral orientation for stakeholder, issue and implementation choices. Projects, rankings and communications should then flow from that foundation.")
add(7, "explanation", "How do mission and vision differ in the chapter's strategic terminology?",
    ["Mission describes the organisation's reason for being.", "Vision states an intention for a specified period."],
    ["Mission sets moral no-go areas, while vision translates them into strategic objectives.", "Mission addresses internal identity, while vision communicates the promise to society.", "Mission defines enduring values, while vision identifies stakeholder priorities."],
    "Mission explains the organisation's reason for being, whereas vision describes a time-bounded intention. Together they can express values, purpose and commitment. Their FSR value lies in guiding later decisions rather than dividing internal and external communication.")
add(7, "factual_anchor", "Which core values underpin the Football Association of Wales strategic plan shown in the chapter?",
    ["Excellence.", "Family.", "Respect."],
    ["Integrity.", "Inclusion."],
    "The FAW example identifies excellence, family and respect as its three core values. They are described as fundamental beliefs supporting the vision and shaping Welsh football's culture. Integrity and inclusion may fit FSR language but are not the three labels in this example.")
add(7, "application", "A board is preparing an FSR vision-and-mission process. Which uses of the statements are supported by the chapter?",
    ["Define values and the organisation's wider purpose proactively.", "Identify practices that fall within moral no-go areas.", "Orient stakeholder and issue management on moral grounds.", "Express a commitment to staff, stakeholders and society."],
    ["Publish the statements as the strategic narrative after material issues and implementation priorities have been agreed."],
    "Vision and mission come early because they establish the moral compass and promise that guide FSR choices. They help define boundaries, support issue and stakeholder decisions and communicate commitment. Drafting them after priorities are fixed would weaken their orienting role.")
add(7, "explanation", "What is the function of a moral no-go area in an FSR strategy?",
    ["It identifies conduct that conflicts with the organisation's values and should remain outside acceptable practice."],
    ["It marks an issue whose reputational risk exceeds the expected organisational benefit.", "It converts a broad value into a target that can be evaluated through a KPI.", "It separates legal duties from societal issues chosen for proactive action.", "It identifies stakeholder claims that require board approval before engagement."],
    "A no-go area translates the organisation's values into a boundary around unacceptable conduct, such as corruption or human-rights violations. It is grounded in mission rather than a risk-return calculation. Targets and governance can operationalise the boundary later.")
add(7, "factual_anchor", "Which stakeholder descriptions from the 2018 FIFA World Cup example are accurate?",
    ["The workforce includes employees and volunteers.", "The supply chain includes organisations providing products or services for the tournament."],
    ["Participants include ticket holders and organised fan groups.", "The community consists of residents and host-city authorities.", "Regulatory bodies include FIFA member associations and professional-player associations."],
    "The table distinguishes workforce, supply chain, participants, community, attendees, regulators and football-related organisations. Teams belong among participants, fans and ticket holders among attendees, and authorities among regulatory bodies. Precise grouping supports meaningful engagement and responsibility.")
add(7, "application", "A tournament organiser is adapting the FIFA stakeholder inventory. Which distinctions should it preserve?",
    ["Separate the workforce from teams and other event participants.", "Distinguish commercial affiliates from suppliers in the supply chain.", "Recognise residents, media and issue-focused groups within the community."],
    ["Place host authorities with event organisers because they share responsibility for delivery.", "Treat television audiences as media stakeholders because their relationship is indirect."],
    "Stakeholder categories reflect different relationships to the event, not merely operational proximity. Employees, teams, sponsors, suppliers, authorities, communities and attendees have distinct claims and forms of influence. Combining categories too early can hide material issues and engagement needs.")
add(7, "explanation", "Why is a differentiated stakeholder inventory valuable for FSR strategy?",
    ["It reveals how groups affect or are affected by the organisation.", "It clarifies different roles and expectations.", "It helps connect stakeholders with material sustainability issues.", "It supports tailored dialogue and engagement."],
    ["It gives the organiser a defensible order for resolving competing stakeholder claims."],
    "A differentiated inventory makes relationships, claims and issue connections visible. That improves consultation and helps the organisation understand who should be involved in a decision. Classification supports judgement, but it does not itself settle conflicts among stakeholders.")

# PDF page 8 / handbook pages 212-213: strategic and normative stakeholder management.
add(8, "application", "A listed club maps fans, employees, sponsors, neighbours and shareholders. What principle should determine who belongs on the map?",
    ["Include groups that affect the club or are affected by its objectives and activities."],
    ["Include groups with an established relationship that can influence club decisions.", "Include groups whose demands create a reputational or governance consequence.", "Include economic partners and add community groups when a material issue affects them.", "Include primary groups engaged through structured dialogue during the reporting period."],
    "The stakeholder definition is reciprocal: a group may affect the organisation or be affected by it. Borussia Dortmund therefore includes economic and non-economic actors, from shareholders to neighbours. Existing influence, dialogue history and material issues help prioritise engagement but do not define stakeholder status.")
add(8, "explanation", "How did stakeholder thinking extend conventional shareholder-oriented management?",
    ["It added the interests and claims of non-economic parties.", "It recognised reciprocal influence between organisations and affected groups."],
    ["It gave community claims a moral status comparable with investor claims.", "It replaced ownership-based governance with a broader legitimacy model.", "It shifted reputation management from shareholders to primary stakeholder groups."],
    "The stakeholder concept broadens attention beyond shareholders and stockholders. It recognises that many parties influence organisations or experience their effects. This extension does not erase ownership or governance; it adds claims that management must understand.")
add(8, "factual_anchor", "Which attributes form the strategic stakeholder-salience model shown in the chapter?",
    ["Power.", "Legitimacy.", "Urgency."],
    ["Proximity.", "Materiality."],
    "The strategic model balances power, legitimacy and urgency. Their combinations describe different stakeholder types and help managers prioritise reputational risk. Proximity and materiality can inform analysis elsewhere but are not the three axes of this model.")
add(8, "application", "A powerful sponsor favours a decision that harms residents with little influence. Which responses reflect both stakeholder perspectives?",
    ["Assess the sponsor through power, legitimacy and urgency.", "Recognise residents as stakeholders because they are affected.", "Examine the residents' claim on moral grounds despite their limited influence.", "Use mission and values to guide the decision."],
    ["Balance the residents' claim through the urgency it could acquire if public attention increases."],
    "The strategic perspective helps assess influential claims and reputation, while the normative perspective protects those affected even when they lack power. Mission and values provide the moral basis for that judgement. Waiting for a claim to gain urgency would reduce responsibility to strategic risk.")
add(8, "explanation", "What is the main purpose of the strategic stakeholder perspective?",
    ["To manage organisational and reputational risk by assessing stakeholders' power, legitimacy and urgency."],
    ["To identify affected groups whose claims require a moral response.", "To determine which social issues should enter the organisation's materiality matrix.", "To establish a dialogue order among stakeholders connected to the same issue.", "To distinguish primary stakeholders from interested parties with indirect relationships."],
    "Strategic stakeholder management focuses on parties who can affect the organisation. The salience attributes help managers understand risk and prioritise attention. Moral claims by less powerful affected groups belong especially to the normative perspective.")
add(8, "application", "A group affected by a stadium project has low power and moderate urgency. Which considerations support a normative response?",
    ["Being affected gives the group a legitimate moral claim.", "The claim should be considered without making power the deciding criterion."],
    ["Moderate urgency is sufficient when the project creates a direct operational impact.", "The group's legitimacy should be tested through the strategic salience model.", "The response should focus on preventing the claim from becoming a reputational risk."],
    "Normative stakeholder management emphasises the 'is affected by' side of the definition. Affected people can make a legitimate claim even when they cannot influence the organisation. Power and urgency may shape engagement logistics, but they should not decide moral worth.")
add(8, "explanation", "How are stakeholder management and the reactive-proactive FSR distinction connected?",
    ["Strategic stakeholder management supports inside-out reputation and risk management.", "Normative stakeholder management grounds attention to affected people in values.", "Issue management can address outside-in societal problems raised by stakeholders."],
    ["Reactive FSR balances powerful claims, while proactive FSR transfers decision weight to legitimate claims.", "Normative management converts stakeholder concerns into strategic priorities once urgency is established."],
    "The chapter links strategic stakeholder thinking with reactive attention to organisational risk. Normative thinking starts from moral responsibility to those affected, while issue management can extend outward to societal problems. These relationships overlap rather than assigning one stakeholder attribute to each FSR type.")
add(8, "application", "A club is designing stakeholder dialogue for a sensitive human-rights issue. Which practices follow the normative approach?",
    ["Identify people affected by the club's activity.", "Listen to groups whose influence is limited.", "Test choices against the club's stated values.", "Connect dialogue with the wider societal issue, not just reputational exposure."],
    ["Sequence engagement according to power and urgency so the club can stabilise the issue before moral review."],
    "A normative approach gives affected people a voice because their claim has moral significance. Vision and mission orient the judgement, and an outside-in view connects the club with the social problem. Strategic sequencing may be practical, but it should not postpone consideration of less powerful groups.")

# PDF page 9 / handbook pages 214-215: issue management and materiality.
add(9, "application", "An association has a long list of social concerns and needs to identify material priorities. What is the correct use of the materiality matrix?",
    ["Plot issues by the significance of organisational impacts and their influence on stakeholder assessments and decisions."],
    ["Plot stakeholders by their influence and the significance of the issues they advocate.", "Plot objectives by expected social impact and the organisation's ability to deliver them.", "Plot issues by reputational urgency and the legitimacy assigned through consultation.", "Plot initiatives by stakeholder support and the strength of their measurable indicators."],
    "The matrix plots issues, not stakeholders or initiatives. Its horizontal axis concerns the significance of economic, environmental and social impacts, while its vertical axis concerns influence on stakeholder assessments and decisions. The result supports strategic prioritisation and target-setting.")
add(9, "explanation", "What is the relationship between a materiality matrix and stakeholder dialogue?",
    ["The matrix is developed in cooperation with stakeholders.", "Dialogue can test identified issues and reveal further concerns."],
    ["The matrix ranks issues before dialogue determines how stakeholders should be engaged.", "Dialogue supplies the vertical score while management assesses impact significance.", "The matrix converts stakeholder claims into a reporting hierarchy after consultation."],
    "A materiality matrix does not replace dialogue. Issue management is developed with stakeholders, and conversations about issues can refine existing concerns or introduce new ones. Management still evaluates evidence, but the process is collaborative rather than a mechanical division of scoring roles.")
add(9, "factual_anchor", "Which statements correctly describe the materiality matrix in the chapter?",
    ["The horizontal axis represents significance of economic, environmental and social impacts.", "The vertical axis represents influence on stakeholder assessments and decisions.", "The plotted dots represent issues."],
    ["The upper-right area represents stakeholders with definitive salience.", "Distance between dots represents the degree of overlap between issues."],
    "The matrix locates issues against impact significance and stakeholder influence. Dots nearer the high end of both axes warrant greater strategic attention. Stakeholder salience and relationships between issues require separate analysis.")
add(9, "application", "A club is constructing a materiality process for its next FSR strategy. Which steps are appropriate?",
    ["Identify candidate economic, social and environmental issues.", "Discuss those issues with relevant stakeholders.", "Position the issues against both materiality dimensions.", "Link high-priority issues with goals and measurable indicators."],
    ["Publish the completed matrix with the sustainability report before using it to revise corporate objectives."],
    "Materiality begins with issue identification and stakeholder engagement, then evaluates both axes. The resulting priorities should shape goals, practices and indicators. Reporting can explain the outcome, but the matrix is part of strategy development rather than a retrospective appendix.")
add(9, "explanation", "Why is a materiality matrix more than a reporting device?",
    ["It helps prioritise FSR goals and direct practices and indicators towards material issues."],
    ["It validates the issue inventory before the organisation begins stakeholder dialogue.", "It translates the FSR issue map into comparable stakeholder expectations.", "It distinguishes strategic stakeholder risks from normative moral claims.", "It provides the evidence required to integrate SDGs into organisational structures."],
    "The matrix originated in reporting standards, but its management value is strategic. It helps organisations select material topics, set objectives and plan action with valid indicators. Reporting communicates the work after the matrix has already shaped decisions.")
add(9, "factual_anchor", "Which pairings in the chapter's stakeholder-management summary are correct?",
    ["Strategic perspective - groups or individuals who can affect the organisation.", "Normative perspective - groups or individuals affected by the organisation."],
    ["Strategic perspective - issue management aimed at societal problems.", "Normative perspective - reputation management aimed at negative attention.", "Strategic perspective - vision and mission applied as moral boundaries."],
    "The strategic perspective emphasises who can affect the organisation and supports risk and reputation management. The normative perspective emphasises who is affected and uses values to recognise moral claims. Issue management can then connect the organisation with wider societal problems.")
add(9, "application", "A community concern scores high for organisational impact but is raised by stakeholders with little power. Which conclusions fit the chapter?",
    ["The issue can be material because impact significance is a separate dimension.", "Affected stakeholders deserve dialogue on normative grounds.", "The association should consider objectives and indicators for the issue."],
    ["The issue should remain below strategic priorities until stakeholder influence becomes substantive.", "The issue belongs in the matrix after dialogue produces a stronger vertical score."],
    "Materiality is not a vote weighted by stakeholder power. Significant organisational impact can make an issue important, while normative stakeholder thinking supports engagement with affected groups. The association should use the evidence to set an appropriate strategic response.")
add(9, "explanation", "How do stakeholder management and issue management reinforce one another?",
    ["Stakeholders help identify and interpret issues.", "Issues provide the substance for stakeholder dialogue.", "Dialogue can reveal concerns missing from the initial inventory.", "Materiality connects stakeholder assessments with organisational impacts."],
    ["Stakeholder salience provides the common scale used to prioritise issues in the materiality matrix."],
    "Stakeholder dialogue is essentially conversation about issues, and issue management depends on those perspectives. The materiality matrix combines stakeholder influence with evidence about organisational impacts. Salience may shape engagement, but it is not the scoring scale for issue materiality.")

# PDF page 10 / handbook pages 216-217: Sustainable Development Goals.
add(10, "application", "An association wants to use the Sustainable Development Goals as its FSR action plan without further analysis. What correction is needed?",
    ["Use the SDGs as normative orientation, then define material priorities, concrete targets and organisational implementation."],
    ["Select the SDGs closest to existing football programmes and add indicators before implementation.", "Use the SDGs to compare stakeholder priorities with the association's social impact.", "Adopt the SDG targets relevant to football and place them within departmental plans.", "Map current activities to the SDGs before deciding which social issues require further action."],
    "The SDGs provide a blueprint and orientation rather than a ready-made management tool. The association must understand them, define priorities, set concrete targets, integrate them into structures and evaluate and communicate progress. Mapping existing work can help, but it does not replace materiality and planning.")
add(10, "explanation", "What value do the SDGs provide as orientations rather than concrete management tools?",
    ["They provide shared normative direction on major global challenges.", "They can orient priorities and targets that organisations translate into their own structures."],
    ["They supply a common materiality scale for governments, companies and football bodies.", "They convert broad social issues into indicators suitable for organisational reporting.", "They show which stakeholder expectations have international legitimacy."],
    "The SDGs offer a widely recognised blueprint for a better and more sustainable future. Their value is directional: organisations still need to decide what is material and design targets, activities and evaluation. They do not themselves perform stakeholder analysis or supply local indicators.")
add(10, "factual_anchor", "Which global challenges are expressly associated with the SDGs in the chapter?",
    ["Poverty and inequality.", "Climate change and environmental degradation.", "Peace and justice."],
    ["Football governance and competitive balance.", "Public health financing and labour mobility."],
    "The SDGs address poverty, inequality, climate change, environmental degradation, peace and justice among their interconnected concerns. They are global normative standards that can guide football organisations. Football-specific governance and competition questions need to be connected through local materiality work.")
add(10, "application", "A national association is moving from SDG awareness to practical use. Which actions complete the chapter's five-element process?",
    ["Understand how the SDGs can be used in the organisation.", "Define priorities.", "Set concrete targets.", "Integrate the targets into structures and evaluate, report and communicate them."],
    ["Assign each selected goal to the stakeholder group that gave it the highest materiality rating."],
    "The practical sequence moves from understanding to priorities, targets, integration and then evaluation, reporting and communication. This turns normative orientation into managed action. Stakeholders inform priorities, but responsibility remains embedded in the association's structures.")
add(10, "explanation", "What is the main benefit of displaying SDGs within a materiality matrix?",
    ["It links global normative goals with the FSR issues that internal and external stakeholders consider relevant."],
    ["It ranks the SDGs by their expected influence on stakeholder decisions.", "It translates the SDGs into quantitative and qualitative organisational indicators.", "It shows which global goals can be delivered through existing football programmes.", "It separates association priorities from the concerns of external stakeholders."],
    "The Belgian example connects SDGs, material issues and stakeholder perspectives in one strategic view. That helps the association choose relevant global orientations rather than invoking the full agenda abstractly. Targets and indicators still require a later management step.")
add(10, "factual_anchor", "Which targets are cited as examples under SDG 5 on gender equality?",
    ["End discrimination against women and girls.", "Give women equal rights to economic resources through reform."],
    ["Achieve equal representation in organisational leadership.", "Remove gender differences in access to organised sport.", "Require equal investment in women's and men's development programmes."],
    "The chapter cites target 5.1 on ending discrimination and target 5.a on equal rights to economic resources. The other options may be relevant football ambitions, but they are not the examples stated. This distinction matters when an association translates SDG orientation into its own targets.")
add(10, "application", "An association has linked many current projects to SDG icons but cannot explain strategic priorities. Which next steps are appropriate?",
    ["Relate the SDGs to the association's material issues.", "Rank priorities with internal and external stakeholder input.", "Convert selected priorities into concrete organisational targets."],
    ["Retain the broad mapping as evidence of contribution while departments develop measures for their existing projects.", "Choose the goals with the widest international recognition to focus the first reporting cycle."],
    "Icon mapping can show possible connections but does not establish strategic relevance. Materiality, stakeholder input and concrete targets turn the SDGs into guidance for action. Reporting should follow that prioritisation rather than substitute for it.")

# PDF page 11 / handbook pages 218-219: inter/intra perspectives and Zadek's path model.
add(11, "application", "A club is using Zadek's path model to assess a social issue. Which questions should its review answer?",
    ["How mature is the issue in society?", "What organisational learning stage describes the current response?", "Does the combination place the club in a risky or higher-opportunity zone?", "What development in practice would better match the issue's maturity?"],
    ["Which stakeholder has sufficient power and urgency to move the issue along the maturity axis?"],
    "The model joins an inter-organisational judgement about issue maturity with an intra-organisational judgement about the response. Plotting both reveals whether practice lags behind societal expectations and guides development. Stakeholder analysis informs the evidence but does not determine an axis by itself.")
add(11, "explanation", "How do the inter-organisational and intra-organisational FSR perspectives differ?",
    ["The inter-organisational perspective concerns relationships with societal actors, while the intra-organisational perspective concerns internal structures and processes."],
    ["The inter-organisational perspective manages proactive issues, while the intra-organisational perspective manages reactive risks.", "The inter-organisational perspective defines materiality, while the intra-organisational perspective evaluates impact.", "The inter-organisational perspective uses stakeholder claims, while the intra-organisational perspective uses vision and mission.", "The inter-organisational perspective sets strategy, while the intra-organisational perspective reports implementation."],
    "Stakeholder management, issue management and SDGs focus on the organisation's relationship with society. Implementation, monitoring and reporting focus more directly on processes and structures within the organisation. Zadek's model helps link these complementary views.")
add(11, "factual_anchor", "Which stages represent the more mature end of Zadek's issue-maturity axis?",
    ["Consolidating.", "Institutionalised."],
    ["Managerial.", "Strategic.", "Civil."],
    "The issue-maturity axis progresses from latent through emerging and consolidating to institutionalised. Managerial, strategic and civil are organisational learning stages on the other axis. Keeping the axes distinct is essential when interpreting the model.")
add(11, "application", "An institutionalised anti-discrimination issue meets a club response that denies responsibility. Which conclusions follow Zadek's model?",
    ["The issue-response combination lies in the risky red zone.", "The club's learning stage is defensive.", "The response seriously lags behind societal maturity."],
    ["The club should begin with a strategic differentiation project before revising its compliance position.", "The issue should be re-plotted through stakeholder dialogue because institutionalisation concerns legal maturity."],
    "A mature or regulated issue combined with denial creates the clearest red-zone mismatch. The organisation is at the defensive stage and must move through credible responsibility and integration. Strategic positioning cannot substitute for basic compliance and managerial change.")
add(11, "explanation", "Which descriptions correctly distinguish the learning stages in Zadek's model?",
    ["Compliance treats policy adherence as a cost of doing business.", "Managerial practice embeds the issue in core management processes.", "Strategic practice aligns core strategy and innovation with the issue.", "Civil practice promotes broad sector participation and collective action."],
    ["Defensive practice contains the issue through short-term controls while responsibility is assessed."],
    "The learning curve moves from denial to compliance, management integration, strategic alignment and collective civil leadership. Each stage represents a different depth of organisational response and rationale. Defensive practice denies practices, outcomes or responsibilities rather than containing them through accepted controls.")
add(11, "application", "A social issue is still emerging, but an association expects it to matter greatly within five years. What is the best use of the path model?",
    ["Use it to anticipate the issue and develop a proactive response before societal maturity exposes a serious organisational gap."],
    ["Keep the issue under monitoring until consolidation provides clearer stakeholder expectations.", "Move the issue into the strategic stage if early action offers first-mover reputational value.", "Classify it through the materiality matrix and defer the learning-stage assessment until targets exist.", "Engage industry partners so a civil response can establish the issue's maturity."],
    "The path model is expressly forward-looking and can help organisations prepare for issues likely to grow in significance. Early action should be grounded in materiality and organisational capability, not merely first-mover advantage. The aim is a responsible trajectory rather than waiting for pressure.")
add(11, "explanation", "What distinguishes the managerial stage from the strategic stage in Zadek's learning curve?",
    ["The managerial stage embeds the issue in daily management processes.", "The strategic stage aligns the issue with core strategy and process innovation."],
    ["The managerial stage uses indicators, while the strategic stage uses materiality and stakeholder dialogue.", "The managerial stage mitigates litigation risk, while the strategic stage manages reputation risk.", "The managerial stage is intra-organisational, while the strategic stage operates through sector partnerships."],
    "Managerial learning integrates responsible practice into operations to manage risk and generate longer-term gains. Strategic learning goes further by aligning the core business strategy and innovation with the issue. Indicators and stakeholder work may support both stages.")
add(11, "application", "Several clubs face the same mature environmental issue and fear that acting first will create a competitive disadvantage. Which civil-stage actions are appropriate?",
    ["Promote participation across the football sector.", "Develop a collective response to the shared responsibility.", "Use cooperation to reduce first-mover disadvantage."],
    ["Coordinate a common compliance threshold before clubs integrate the issue into core management.", "Ask the governing association to assume implementation while clubs contribute operational data."],
    "At the civil stage, organisations encourage broad industry participation so collective action can deliver long-term value. Cooperation can address the disadvantage faced by an isolated first mover. It should deepen responsibility across participants rather than centralise it away from clubs.")

# PDF page 12 / handbook pages 220-221: implementation, leadership, culture and objectives.
add(12, "application", "An association is building the organisational structure for FSR. Which design choices match the chapter?",
    ["Provide appropriate staffing and an adequate budget.", "Create a qualified FSR unit with direct board reporting.", "Establish a regularly meeting FSR board that connects organisational units.", "Secure visible commitment from the general secretary or CEO."],
    ["Place the FSR function within communications so reporting, training and stakeholder engagement share leadership."],
    "Effective FSR needs resources, expertise, governance links and tone from the top. A separate unit and cross-organisational board help integration across functions. Communications is a partner, but placing the full function there would make implementation too narrow.")
add(12, "explanation", "Why is CEO commitment necessary but insufficient for FSR implementation?",
    ["Tone from the top enables implementation, but responsibility must also be owned by middle managers, staff and bottom-up contributors."],
    ["The CEO sets values, while the FSR board supplies the operational expertise needed across departments.", "The CEO represents the strategic stage, while staff participation provides the managerial stage.", "The CEO secures resources, while the FSR manager determines which societal issues are material.", "The CEO leads internal implementation, while ambassadors manage the organisation's societal relationships."],
    "Senior commitment signals priority and supports resources, but FSR touches many departments and routines. Middle managers, motivated staff and ambassadors help embed it in daily work. The chapter therefore combines top-down leadership with bottom-up participation.")
add(12, "factual_anchor", "Which structural mechanisms are specifically recommended for FSR implementation?",
    ["A qualified FSR unit reporting directly to the board.", "An FSR board that meets regularly and supports cross-unit integration."],
    ["A stakeholder committee reporting through the FSR manager.", "A sustainability lead located in each operational department.", "An external advisory panel chaired by the general secretary or CEO."],
    "The chapter recommends a separate, qualified FSR unit with direct board access and an FSR board supporting integration, ideally including the general secretary or CEO. Departmental enthusiasm and ambassadors also matter, but they are leadership and participation mechanisms rather than the stated structural bodies.")
add(12, "application", "Staff members across several departments are already motivated by climate and equal-opportunity issues. How should the association use this capacity?",
    ["Invite bottom-up participation in implementation.", "Connect motivated staff through an ambassador programme.", "Provide awareness activity and FSR training."],
    ["Ask the FSR unit to select ambassadors after departmental action plans have been approved.", "Use ambassadors mainly to communicate the strategy within their existing teams."],
    "Motivated employees are valuable bottom-up contributors and can be incorporated through an ambassador programme. Awareness and training broaden capability beyond the initial enthusiasts. Their role should influence implementation, not be confined to transmitting a completed plan.")
add(12, "explanation", "Why does organisational culture require explicit attention during FSR implementation?",
    ["FSR introduces new ideas and routines.", "People may prefer familiar practices.", "Leadership behaviour affects acceptance of change.", "Structures can either enable or obstruct participation."],
    ["Cultural alignment should precede consultation so employees evaluate the same vision and mission."],
    "FSR often challenges established habits, so technical structures by themselves are insufficient. Leadership, participation and organisational arrangements shape whether new routines take root. Open consultation helps build the culture; it should not wait for prior alignment.")
add(12, "application", "A CEO asks the FSR manager to draft the vision and mission privately for speed. What is the best response?",
    ["Use open consultation involving employees across the hierarchy so the statements help shape shared culture."],
    ["Draft a board version first, then consult staff on the implementation language.", "Ask departmental ambassadors to consolidate staff values before senior leaders define the mission.", "Use the current strategic values and consult employees when specific FSR no-go areas are proposed.", "Prepare a provisional statement for stakeholder consultation before widening the internal process."],
    "The chapter warns against leaving vision and mission to the CEO or FSR manager. Broad internal participation, interaction and consultation help influence culture and bring the organisation into the FSR process. Speed is less valuable than genuine ownership of the moral compass.")
add(12, "explanation", "What role does management by objectives play in FSR?",
    ["It links goal-setting with monitoring outcomes and adjusting practice.", "It supports the use of KPIs to evaluate whether planned results are being achieved."],
    ["It converts material issues into quantitative targets before departments select activities.", "It separates strategic objectives from qualitative social effects that require later evaluation.", "It makes the FSR board responsible for performance once objectives have been approved."],
    "Management by objectives creates a systematic path from defined goals to evaluation and adjustment. KPIs support that discipline in FSR just as in other management areas. The approach does not require every social effect to become a quantitative target.")
add(12, "application", "An FSR lead wants implementation to reach departments such as events, procurement and grassroots. Which leadership practices are appropriate?",
    ["Encourage middle managers to display responsible leadership.", "Connect departmental work through the deeper FSR strategy.", "Combine senior commitment with staff participation."],
    ["Give the FSR unit approval authority over departmental initiatives that affect material issues.", "Use the FSR board to allocate responsibility for each issue to the department with the strongest expertise."],
    "FSR is everyone's concern and becomes durable when middle managers and staff embed it across their functions. The central strategy and board support coordination, while tone from the top enables the work. Integration is stronger than turning the FSR unit into a parallel approval hierarchy.")

# PDF page 13 / handbook pages 222-223: IOOI, reporting and communication.
add(13, "application", "A grassroots inclusion programme is being evaluated with the IOOI method. Which distinctions should the evaluation preserve?",
    ["Input records the human, financial and material resources invested.", "Output records the activities and immediate products delivered.", "Outcome examines changes among participants and within the organisation.", "Impact examines broader and longer-term changes in society or systems."],
    ["Participant numbers should be reported as impact when they demonstrate sustained programme reach."],
    "IOOI separates what is invested, what is produced, what changes for target groups and what changes more broadly. Participant numbers usually describe output or reach, not societal impact. Preserving the chain prevents activity volume from being mistaken for meaningful change.")
add(13, "explanation", "What is the key difference between output and outcome in the IOOI model?",
    ["Output describes delivered activities and immediate results, while outcome describes changes experienced by target groups or the organisation."],
    ["Output measures participant reach, while outcome measures wider change in the social system.", "Output records the use of resources, while outcome evaluates whether resources were efficient.", "Output concerns quantitative indicators, while outcome uses qualitative evidence.", "Output belongs to project reporting, while outcome belongs to strategic monitoring."],
    "Outputs are the events, media, measures and direct products created by the commitment. Outcomes are changes such as learning, response, attitudes or relationships among participants and the organisation. Wider systemic change belongs to impact.")
add(13, "factual_anchor", "Which measurement tools are paired with later IOOI stages in the chapter?",
    ["Surveys and interviews can assess outcomes.", "Pre-post analysis and time-series studies can assess impact."],
    ["Accounting and resource valuation can assess outputs.", "Participant lists and press clippings can assess impact.", "Project activity reports can assess outcomes."],
    "Outcome evidence can come from surveys, interviews and participant response, while impact may require pre-post analysis, empirical studies or time series. Accounting is associated with input, and activity records support output. The tools become more demanding as evaluation moves towards broader change.")
add(13, "application", "An association is evaluating refugee integration through grassroots football. Which evidence would create a stronger IOOI chain?",
    ["Record staff time and funding as input.", "Record sessions and participant reach as output.", "Assess learning, relationships and participant feedback as outcome."],
    ["Treat continued registration in grassroots clubs as proof of community-level impact.", "Use media coverage to validate the programme's outcome for refugees."],
    "The IOOI chain starts with resources, then delivery, then changes experienced by participants. Continued participation may be valuable outcome evidence, but a claim about community impact needs broader analysis. Media coverage shows visibility rather than integration by itself.")
add(13, "explanation", "Why does the chapter encourage evaluators to look beyond quantitative KPIs?",
    ["Some social effects are difficult to express numerically.", "Qualitative evidence can reveal changes in attitudes, relationships and experience.", "Output counts can overstate success when outcomes remain unclear.", "Impact requires attention to wider changes beyond direct project delivery."],
    ["Qualitative criteria are most useful before an organisation has enough data to establish KPIs."],
    "FSR includes effects such as awareness and integration that may not be captured adequately by counts. Qualitative evidence complements quantitative KPIs and helps explain outcomes and impact. It is a substantive evaluation method, not merely a temporary substitute for data.")
add(13, "application", "A club wants its FSR report to do more than promote successful projects. What should be its central purpose?",
    ["Provide accountable and transparent evidence of action and learning, including what can be improved."],
    ["Demonstrate progress against material topics in a form that strengthens stakeholder confidence.", "Explain performance through the indicators most relevant to the report's audience.", "Use a recognised reporting framework to distinguish verified results from programme narrative.", "Connect project outcomes with the club's stated values and future objectives."],
    "FSR reporting serves governance through accountability and transparency and also supports learning. A credible report reflects on what works, what does not and why. Audience, frameworks and values shape presentation, but the core purpose is open evidence and improvement rather than promotion.")
add(13, "explanation", "Which two broad functions of FSR reporting are emphasised in the chapter?",
    ["Verification through accountability and transparency.", "Improvement through reflection and organisational learning."],
    ["Prioritisation through materiality and stakeholder dialogue.", "Legitimation through evidence of responsible core activity.", "Communication through audience-specific channels and emotional content."],
    "Reporting verifies what the organisation has done and provides open information. It also creates a structured opportunity to learn what worked, where, when, why and how. Materiality and communication support reporting, but they are not the two broad functions highlighted here.")
add(13, "application", "An association is designing communication for a new FSR programme. Which sequence is supported by the chapter?",
    ["Define objectives and the internal or external audience.", "Choose suitable channels and launch in a way that fits the audience.", "Evaluate the communication against the defined objectives."],
    ["Select channels with the communication department before segmenting the stakeholder audience.", "Evaluate response through the programme's FSR indicators so communication and impact use a common measure."],
    "The communication process starts with objectives and audience, then selects channels and an appropriate launch, and finishes with evaluation. Cooperation with the communication department is important throughout. Communication response should be judged against communication objectives rather than assumed to equal programme impact.")

# PDF page 14 / handbook pages 224-225: authenticity and the UEFA FSR Roadmap.
add(14, "application", "A club fears that communicating its FSR work will be dismissed as bluewashing. Which safeguards fit the chapter?",
    ["Communicate authentically.", "Ensure claims reflect substantive action.", "Report shortcomings and progress accurately.", "Use sensitivity because values-based communication can provoke disagreement."],
    ["Delay outward communication until the programme has enough positive evidence to outweigh scepticism."],
    "The risk of bluewashing should make communication careful and truthful, not silent. Claims must be supported by real practice, and the organisation should be transparent about progress and limitations. Authenticity protects long-term reputation better than waiting to present an unqualified success story.")
add(14, "factual_anchor", "Which principle best summarises the chapter's final instruction on FSR communication?",
    ["Communicate authentically and act with sportsmanship."],
    ["Demonstrate measurable progress before amplifying emotional content.", "Use transparency to distinguish FSR communication from football public relations.", "Align external claims with the issues ranked highest by stakeholders.", "Frame organisational learning as evidence that the project is improving."],
    "The chapter's concise instruction is to communicate authentically and act with sportsmanship. This captures the need for truthfulness, substance and sensitivity. Measurement, transparency and learning support that principle but do not replace it.")
add(14, "factual_anchor", "Which monitoring and evaluation actions appear in UEFA's FSR Roadmap?",
    ["Develop KPIs that measure the objective.", "Allocate at least 5% of the project budget to monitoring and evaluation techniques."],
    ["Set qualitative and quantitative indicators for each stakeholder priority.", "Evaluate each material issue through the IOOI method.", "Report progress before revising the project's SMART objectives."],
    "The Roadmap asks organisations to develop objective-linked KPIs and devote at least 5% of project budget to monitoring and evaluation techniques. It reinforces the principle that management requires measurement. IOOI and mixed evidence can help, but they are not stated as mandatory Roadmap actions here.")
add(14, "application", "A national association is beginning the UEFA FSR Roadmap. Which early actions should it take before implementation planning?",
    ["Secure commitment and decision-maker buy-in.", "Pinpoint and rank the association's social and environmental issues.", "Identify key stakeholders and understand their priority issues."],
    ["Draft SMART objectives for the issues already supported by senior leaders.", "Set reporting expectations so stakeholders understand how consultation will influence the final strategy."],
    "The Roadmap begins with commitment, issue management and stakeholder consultation. These steps clarify values, material concerns and the people whose perspectives matter. SMART objectives and implementation activities follow once that foundation is established.")
add(14, "factual_anchor", "Which statements accurately reflect the implementation, reporting and communication stages of UEFA's FSR Roadmap?",
    ["Implementation identifies material issues and formulates SMART objectives.", "Implementation develops activities that support those objectives.", "Reporting demonstrates progress, accountability and learning.", "Communication targets segmented audiences and seeks a response."],
    ["Communication amplifies the programme before reporting tests whether project objectives were achieved."],
    "The Roadmap links material issues to SMART objectives and activities, then uses measurement and reporting for proof and improvement. Communication is planned for a defined, segmented audience and aims to provoke response. It is coordinated with evidence rather than positioned as a stage that precedes evaluation.")


def main() -> None:
    assert len(QUESTIONS) == 100, len(QUESTIONS)
    categories: dict[str, int] = {}
    for question in QUESTIONS:
        category = question["oral_exam_category"]
        categories[category] = categories.get(category, 0) + 1
    assert categories == {
        "application": 45,
        "explanation": 35,
        "factual_anchor": 20,
    }, categories
    payload = {
        "schema_version": 1,
        "library_key": "uefa_cfm",
        "chapter_number": 15,
        "session_title": "Chapter 7 - Football and social responsibility",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
