"""Build the staged Chapter 8 UEFA CFM women's football bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "UEFA-HFM-Womens-football.pdf"
OUTPUT = Path("data/cfm_imports/chapter_08_womens_football.json")
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
            "handbook_pages": [226 + 2 * page, 227 + 2 * page],
        },
        "page_crops": [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 230-231: change model and historical context.
add(2, "application", "An association defines a participation target before examining the environment around women's football. Which part of Pettigrew's model is missing?",
    ["Context: the external trends, opportunities and threats surrounding the change."],
    ["Content: the specific development goals and intended purpose of the initiative.", "Process: the methods through which the participation target will be delivered.", "Governance: the stakeholders responsible for approving and resourcing the target.", "Evaluation: the indicators used to judge whether participation has become sustainable."],
    "Pettigrew's context asks what surrounds and shapes the proposed change before goals and delivery are finalised. Content concerns what will change, while process concerns how it will happen. A sound participation strategy therefore begins with the political, economic, social and institutional setting.")
add(2, "explanation", "Which descriptions correctly distinguish context, content and process in Pettigrew's change model?",
    ["Context concerns the surrounding trends, opportunities and threats.", "Content concerns what is changing and the goals of that change."],
    ["Process concerns the stakeholders whose support gives the change legitimacy.", "Context concerns the historical baseline used to measure future development.", "Content concerns the resources and structures through which implementation is controlled."],
    "Context describes the environment, content specifies the intended change and purpose, and process describes how change will be achieved. Stakeholders, history and resources can inform those elements, but they do not replace their definitions. The model keeps diagnosis, ambition and delivery logically connected.")
add(2, "factual_anchor", "Which developments appear on the chapter's timeline of women's football?",
    ["The first recorded women's international match in 1881.", "A UEFA resolution on national-association responsibility in 1971.", "The first FIFA Women's World Cup in 1991."],
    ["The first UEFA women's club competition in 1982.", "The first global women's football strategy in 2001."],
    "The timeline marks the 1881 international, UEFA's 1971 resolution and the 1991 FIFA Women's World Cup. The UEFA European women's championship began in 1982, while UEFA launched its women's club competition in 2001. FIFA's first dedicated global strategy came much later.")
add(2, "application", "A country lifted a historic ban on women's football but participation remains weak. Which responses reflect the chapter's historical analysis?",
    ["Rebuild access to suitable pitches and facilities.", "Restore funding and organisational infrastructure.", "Address social assumptions that survived the formal ban.", "Treat the setback as a long-term development issue rather than a legal change alone."],
    ["Prioritise elite competition so public success can compensate for the historical loss of grassroots structures."],
    "Historic bans denied women's football venues, funding and infrastructure and pushed activity outside official systems. Lifting a ban removes a legal barrier but does not recreate the lost pathway or change entrenched norms. Recovery therefore requires coordinated grassroots, facility, cultural and governance work.")
add(2, "explanation", "Why did restrictions on official pitches have effects beyond the wording of the bans?",
    ["They removed the venues and infrastructure needed for organised development, setting the game back even where informal play continued."],
    ["They shifted women's football into community settings where national associations could not regulate it.", "They interrupted international fixtures while domestic teams retained local competition.", "They reduced spectator income that had previously financed women's football development.", "They converted women's teams into unofficial clubs without access to men's competition calendars."],
    "Access to recognised pitches was fundamental to organised teams, competitions and visibility. Removing that access effectively dismantled the game's infrastructure and support, even if women continued to play informally. The consequence was developmental regression, not merely a temporary reduction in fixtures.")
add(2, "factual_anchor", "Which historical events demonstrate institutional influence on women's football development?",
    ["National-association bans blocked access to official football infrastructure.", "UEFA's 1971 resolution asked associations to take responsibility for the women's game."],
    ["The First World War placed women's teams under national-association control.", "The 1881 international established a recognised European competition pathway.", "The 1920 international fixtures secured regular access to men's club grounds."],
    "The bans show how institutions could constrain the game, while the 1971 UEFA resolution helped move responsibility back into national associations. Wartime social change encouraged teams but did not create governing control. Early matches demonstrated demand without establishing durable structures.")
add(2, "application", "A strategy team is using the chapter's history as part of a context review. Which questions should it ask?",
    ["Which past restrictions shaped current access to facilities?", "Which social norms still affect participation?", "Which institutional decisions changed responsibility for the game?"],
    ["Which historical attendance milestones provide a benchmark for current commercial targets?", "Which early teams offer a model for the present national competition structure?"],
    "Historical context explains why today's starting position is uneven and why formal opportunity may not equal practical access. Facilities, norms and institutional ownership are lasting mechanisms. Attendance stories are informative, but they are not a sufficient basis for current commercial targets or structures.")
add(2, "explanation", "How do content and process interact in a women's football development strategy?",
    ["Content specifies goals such as participation and sustainability.", "Process identifies how those goals will be achieved.", "The chosen process should respond to the diagnosed context.", "Progress can fail when ambitious content is detached from delivery conditions."],
    ["Process should be fixed first so realistic content can be selected from the available delivery methods."],
    "Pettigrew's elements are distinct but connected. Content says what the association wants to change, while process turns that ambition into action in a particular context. Starting with a fixed delivery method can constrain diagnosis and encourage the wrong goal.")
add(2, "application", "An association wants to copy another country's women's football initiative because it produced rapid growth. What is the best first step?",
    ["Compare the political, social, economic, legal and football context before adapting the initiative."],
    ["Replicate the initiative's goals and adjust its delivery process to the available domestic resources.", "Map the initiative's stakeholders and secure equivalent organisations in the domestic system.", "Use the other country's growth rate to set a locally credible participation objective.", "Pilot the initiative in the strongest region before assessing wider contextual differences."],
    "A programme that worked elsewhere sits within a particular context. The association should first understand whether the same opportunities, threats, norms and structures apply, then adapt content and process. A pilot can be valuable later, but it should not bypass contextual analysis.")
add(2, "application", "A development plan seeks to repair the legacy of exclusion from official football. Which paired priorities are justified?",
    ["Create accessible playing opportunities and rebuild recognised development pathways.", "Challenge the social norms that once legitimised exclusion."],
    ["Use national-team visibility to restore participation before investing in local infrastructure.", "Create separate governance arrangements so historical men's structures do not shape the women's game.", "Measure recovery through the return of attendance levels recorded before the bans."],
    "The historical damage was both structural and cultural. Rebuilding venues, pathways and official support must be accompanied by work on attitudes and legitimacy. Elite visibility may help, but it cannot replace local access or provide a reliable historical recovery benchmark.")

# PDF page 3 / handbook pages 232-233: renewed development, strategies, competitions and futsal.
add(3, "factual_anchor", "Which goals are included in FIFA's first global strategy for women's football?",
    ["Develop and grow on and off the pitch.", "Showcase the game.", "Govern and lead."],
    ["Standardise professional leagues.", "Integrate women's and men's commercial rights."],
    "FIFA's five goals are develop and grow, showcase, communicate and commercialise, govern and lead, and educate and empower. Professional league design and rights integration may be policy choices, but they are not goal headings in the strategy.")
add(3, "application", "A national association is aligning its plan with UEFA's #TimeForAction strategy. Which ambitions belong in that alignment?",
    ["Increase the number of women and girls playing.", "Change perceptions of women's football.", "Increase the reach and value of major women's competitions.", "Improve player standards and female representation in UEFA bodies."],
    ["Create a senior women's futsal team before expanding the grassroots football pathway."],
    "UEFA's strategy combines participation, perception, competition value, sporting standards and representation. This is a portfolio rather than a single commercial or performance target. Futsal development can contribute, but the strategy does not prescribe that sequence.")
add(3, "explanation", "Why was UEFA's 1971 resolution a pivotal governance development?",
    ["It formally asked national associations to take responsibility for women's football, helping reverse institutional exclusion."],
    ["It transferred women's international competitions from informal organisers to UEFA.", "It linked the lifting of national bans to the creation of domestic women's leagues.", "It made gender equality a condition of national-association membership.", "It established a common European pathway for clubs and representative teams."],
    "The resolution placed formal responsibility for the women's game with national associations. Bans were then lifted across countries and official international development accelerated. It did not itself create a complete competition system or a membership condition.")
add(3, "factual_anchor", "Which competition developments are accurately described in the chapter?",
    ["UEFA established a European women's representative-team competition in 1982.", "UEFA launched the women's club competition that became the Women's Champions League in 2001."],
    ["The representative-team competition was relaunched as Women's EURO in 1982.", "The Women's Champions League introduced centralised rights when it launched.", "The first UEFA women's futsal competition preceded the women's club competition."],
    "The representative competition began in 1982 and was relaunched under the European Women's Championship name in 1990. The women's club competition followed in 2001. Centralised rights and a group stage were later planned changes, while Women's Futsal EURO began in 2019.")
add(3, "application", "A country has no registered female futsal players but wants to enter a future UEFA competition. Which actions follow the inaugural Women's Futsal EURO experience?",
    ["Use the new competition as a development catalyst.", "Run talent identification across women's football and futsal.", "Build a national team alongside conditions for continued domestic growth."],
    ["Recruit senior football players first so the association can meet competition entry requirements.", "Postpone domestic programmes until an international event creates enough participant demand."],
    "The inaugural competition prompted many associations to identify talent and create teams from a very low base. A national side can showcase the pathway, but sustainable progress also requires better conditions and further competitions. The example supports parallel development rather than a temporary selection exercise.")
add(3, "explanation", "How can major women's competitions contribute to wider development?",
    ["They create visible role models.", "They stimulate technical and tactical progress.", "They attract public and commercial interest.", "They provide milestones that reinforce participation and investment."],
    ["They create a commercial return that can finance grassroots growth without separate development funding."],
    "Competitions showcase quality, produce role models and attract audiences and partners. Those effects can strengthen the broader development environment. They do not remove the need for deliberate grassroots, governance and funding work.")
add(3, "application", "A governing body is revising the Women's Champions League format and commercial approach. Which chapter-backed intervention is most coherent?",
    ["Combine a more competitive group stage with centralised rights to improve visibility."],
    ["Expand knockout rounds while leaving rights with clubs to preserve local commercial incentives.", "Centralise sponsorship while retaining club control of broadcast rights and match production.", "Increase the number of entrants before changing the format so participation drives visibility.", "Bundle rights with men's competitions until women's audiences are commercially mature."],
    "The chapter describes the planned addition of a group stage alongside centralised rights as a way to improve competitiveness and visibility. The two measures reinforce sporting and commercial development. Continued bundling would work against the later strategy of giving women's properties distinct value.")
add(3, "explanation", "How did Title IX create a step change for women's football in the United States?",
    ["It made gender equality mandatory in federally supported education.", "That legal change expanded teams, scholarships and funding in schools and colleges."],
    ["It required national sports bodies to provide equal competition structures.", "It shifted elite player development from clubs to educational institutions.", "It linked public funding to equal professional opportunities after college."],
    "Title IX altered the legal environment of education, including college sport. The resulting access to teams, scholarships and funding rapidly expanded the player base. Its mechanism was educational equality, not the direct regulation of professional football.")
add(3, "application", "An association wants one plan to reflect FIFA and UEFA strategic priorities. Which combined actions are well supported?",
    ["Grow participation and player standards.", "Showcase and commercialise the game.", "Strengthen governance, leadership and female representation."],
    ["Use competition reach as the principal measure of progress across the two strategies.", "Sequence empowerment after the playing pathway has achieved sustainable growth."],
    "Both strategies link on-pitch growth with visibility, commercial development and leadership. An integrated plan should therefore balance participation, performance, governance and market development. Competition reach is important, but it is not a complete measure and empowerment is not a later-stage add-on.")

# PDF page 4 / handbook pages 234-235: PESTEL and grassroots participation.
add(4, "application", "A national association is conducting a PESTEL review of women's football. Which issues are correctly classified?",
    ["School-sport policy as political.", "Disposable income and recession as economic.", "Broadcast infrastructure as technological.", "Equality legislation as legal."],
    ["Changing-room availability as social because it affects participant inclusion."],
    "PESTEL separates policy, economic capacity, socio-cultural conditions, technology, environment and law. Facilities and changing rooms are treated within the environmental dimension in this chapter. Classification helps the association examine different mechanisms without losing their interaction.")
add(4, "explanation", "What is the main value of using PESTEL for women's football development?",
    ["It exposes external opportunities and threats that shape feasible goals and delivery choices."],
    ["It ranks national constraints before stakeholders decide which issues they can influence.", "It distinguishes structural barriers from cultural barriers within grassroots participation.", "It converts historical context into six categories suitable for strategy monitoring.", "It identifies which development initiatives should be led by government rather than football bodies."],
    "PESTEL is a structured context scan. It helps leaders see how policy, wealth, culture, technology, geography, facilities and law can enable or inhibit the women's game. It informs strategy but does not itself rank priorities or allocate responsibility.")
add(4, "factual_anchor", "Which technological opportunities are identified for women's football?",
    ["Deals with over-the-top digital broadcasters.", "National associations creating their own direct platforms."],
    ["Centralised production reducing the cost of targeting advertising audiences.", "Digital rights being bundled with men's properties to increase initial reach.", "Pay-per-view replacing free access as the preferred early-market model."],
    "OTT providers and association-owned platforms can widen availability and engagement. The chapter also notes uncertainty over rights value because digital economics and free access may reduce revenue. Technology creates options rather than one prescribed commercial model.")
add(4, "application", "An association plans a free digital channel for women's matches. Which expectations are realistic?",
    ["It can increase coverage and audience engagement.", "It may support interest and participation.", "It may generate limited direct revenue while access remains free."],
    ["It should raise rights value by creating competition among digital broadcasters.", "It should replace television partnerships until viewing figures establish a paid market."],
    "A direct channel can solve an exposure problem and help build the market. Free access, however, may not monetise rights and can affect how external broadcasters value them. The association should treat reach and revenue as related but distinct objectives.")
add(4, "explanation", "How does greater gender equality support women's football development according to the chapter?",
    ["It encourages investment in women's sport.", "It expands opportunities to participate.", "Participation can improve the player skill base.", "It is positively associated with international performance."],
    ["It reduces the effect of cultural heritage once equal-opportunity legislation is in place."],
    "Gender equality affects resources, access and the conditions in which skills develop. The chapter reports positive associations with participation and elite performance. Cultural and religious factors can persist, so legal or workforce equality does not erase every barrier.")
add(4, "factual_anchor", "Who is the PlayMakers grassroots programme designed to reach?",
    ["Girls aged five to eight who have not previously played football."],
    ["Primary-school girls who are at risk of dropping out of organised sport.", "Girls aged five to eight who prefer non-competitive football formats.", "Young players who need fundamental movement skills before joining a club.", "Girls entering football through schools without a recognised local pathway."],
    "PlayMakers targets five- to eight-year-old girls who have never played football. Disney stories and imaginative play provide a safe, welcoming entry point. The programme develops movement, life and football skills, but those needs do not define eligibility.")
add(4, "application", "A hot-climate country with limited pitches is designing a women's football plan. Which conclusions follow the environmental analysis?",
    ["Adapt training formats and schedules to climatic constraints.", "Treat suitable facilities and changing rooms as development infrastructure."],
    ["Focus indoor provision on futsal before expanding the outdoor player pathway.", "Use the larger national talent pool to offset irregular access to training.", "Classify facility investment as an economic intervention because climate cannot be changed."],
    "Climate can make regular outdoor training harder, while physical infrastructure can expand opportunity. Strategy should adapt the playing environment and invest in practical access. Futsal may help, but the chapter does not prescribe it as the required sequence or redefine facilities as purely economic.")
add(4, "explanation", "How should leaders distinguish legal and social influences on women's football?",
    ["Law can create enforceable equality in defined settings.", "Social norms shape whether opportunities are accepted and used.", "The two influences can reinforce one another but operate through different mechanisms."],
    ["Legal change is most effective after social participation has demonstrated demand.", "Social equality is the main route through which legislation improves elite performance."],
    "Title IX illustrates a legal rule changing educational opportunity, while gender norms, religion and cultural heritage shape behaviour and investment more broadly. Legal and social forces interact, yet compliance does not automatically change attitudes. Development plans need both access rights and cultural engagement.")
add(4, "application", "An association wants grassroots growth to strengthen the whole women's game. Which benefits should its plan connect?",
    ["More girls experiencing football.", "Greater interest among participants and their networks.", "A wider talent pipeline for elite football.", "A stronger base for the future health of the game."],
    ["Earlier identification of talented players so grassroots resources can be concentrated on retention."],
    "Participation is valuable both in itself and as the foundation of the football ecosystem. It creates players, interest and future elite talent. Concentrating grassroots resources on early talent selection would narrow the programme and weaken the wider participation purpose.")

# PDF page 5 / handbook pages 236-237: participation barriers and dropout.
add(5, "application", "A beginner programme gives girls one short session per week while boys have several informal playing opportunities. Which barrier is most directly illustrated?",
    ["Time: girls have less opportunity to practise movement and game-playing skills."],
    ["Infrastructure: the formal programme provides less club access than boys receive.", "Competitive setting: limited contact increases pressure to perform during each session.", "Gender stereotyping: the schedule reflects assumptions about girls' interest in football.", "Individual difference: a common timetable overlooks variation in girls' prior experience."],
    "The chapter identifies reduced time in sport as a direct barrier to learning and practising fundamental skills. The situation may reflect wider structural or cultural choices, but the immediate mechanism is unequal exposure. Programme design should increase safe, enjoyable opportunities to play.")
add(5, "explanation", "Why should grassroots organisers offer both mixed and girl-only environments?",
    ["Some girls enjoy practising with boys.", "Others feel more comfortable and confident in girl-only settings."],
    ["Mixed settings develop competitive resilience, while single-sex settings develop basic skills.", "Mixed settings suit experienced players, while single-sex settings suit first-time participants.", "Mixed settings improve access, while single-sex settings reduce gender stereotyping."],
    "Girls are not a homogeneous group, and preferences for the social environment differ. Choice helps programmes fit participants rather than impose one pathway. The distinction is about comfort, enjoyment and experience, not a fixed link to skill or competitiveness.")
add(5, "factual_anchor", "Which barriers to girls' participation are identified in the chapter?",
    ["Gender-related stereotypes.", "Limited infrastructure and club access.", "Difficulty navigating some conflict-resolution styles."],
    ["Insufficient visibility of elite competitions.", "Limited access to paid coaching before adolescence."],
    "The barrier list includes time, environment and competition, stereotypes, infrastructure, individual differences and conflict management. Elite visibility and cost appear in the later discussion of adolescent dropout, but not as labels in this initial six-part list.")
add(5, "application", "A club is redesigning its introductory offer after girls report feeling judged in competitive sessions. Which changes follow the evidence?",
    ["Make fun and enjoyment explicit programme priorities.", "Reduce premature performance pressure.", "Offer a setting in which mistakes feel safe.", "Ask participants which social environment they prefer."],
    ["Delay formal competition until participants demonstrate confidence in fundamental movement skills."],
    "Traditional competitive environments can make girls feel judged and undermine confidence when fun is displaced. A responsive programme changes climate and offers participant choice. The chapter supports flexible design rather than a universal readiness threshold for competition.")
add(5, "explanation", "Why must programme design account for individual differences among girls?",
    ["Treating girls as a uniform group obscures differences in circumstances, experience and preference that shape participation."],
    ["Individual assessment identifies which barriers should be addressed through the club and which require partners.", "Different experiences determine whether mixed or single-sex football is the more inclusive format.", "Personal circumstances explain why some girls respond more strongly to social stigma during adolescence.", "Individualised programmes prevent infrastructure limits from affecting already active girls."],
    "The chapter explicitly rejects the idea that girls form a homogeneous group. Effective design considers differences within and between groups and the uniqueness of each person. Those differences inform choice, but they do not map each participant to one fixed barrier or format.")
add(5, "factual_anchor", "Which patterns are highlighted in the discussion of girls leaving football?",
    ["Many players stop when moving from girls' to women's football after age 18.", "Around age 14, girls' dropout can be about twice the rate for boys."],
    ["Dropout rises when competitive performance becomes part of girls' self-worth after age 18.", "Registered participation falls mainly because adult amateur opportunities are less visible.", "Peer influence becomes weaker as girls develop a clearer sense of athletic competence."],
    "The chapter identifies two important transition risks: adolescence and the move into adult football. At around 14, peer pressure, body image and perceived competence matter; after 18, the pathway into women's football loses many players. Retention therefore needs age-specific responses.")
add(5, "application", "A national association is designing a retention plan for teenage girls. Which actions address the cited dropout mechanisms?",
    ["Provide good facilities and coaching at suitable times.", "Address safety and transport barriers.", "Use strong female athletic role models."],
    ["Separate body-image support from football delivery so coaches can focus on athletic competence.", "Subsidise club fees after girls have shown sustained commitment to organised football."],
    "Teenage retention is affected by access, safety, cost, peers, body image and role models. A coherent programme brings those considerations into delivery and partnerships. Waiting for sustained commitment or separating identity concerns from the football environment would miss the mechanism of dropout.")
add(5, "explanation", "How do stereotypes and infrastructure reinforce one another as participation barriers?",
    ["Masculine stereotypes can reduce institutional priority for girls' football.", "Lower priority can produce weaker access to clubs, pitches and school provision.", "Poor access then makes girls' participation appear less normal.", "That apparent lack of demand can reproduce the original stereotype."],
    ["Infrastructure investment should precede stereotype work because visible participation provides the evidence needed to change attitudes."],
    "Cultural assumptions influence where opportunity and resources are placed, while weak provision makes exclusion seem natural. Breaking the cycle requires both practical access and communication with parents and society. One strand should not be postponed until the other has succeeded.")
add(5, "application", "Young players avoid speaking up when conflict occurs during training. What is the most appropriate development response?",
    ["Teach and practise skills for navigating conflict within a supportive football environment."],
    ["Use single-sex groups until players become comfortable with competitive disagreement.", "Ask coaches to adopt less masculine resolution styles during the introductory phase.", "Provide an escalation route so players can avoid direct conflict while confidence develops.", "Treat conflict competence as a life-skill outcome after regular participation is established."],
    "Conflict is unavoidable in football, so avoiding it does not prepare players for the game or wider life. The chapter recommends helping girls develop the skills to navigate and manage it. Coaching style and escalation routes may support safety, but they do not replace capability-building.")
add(5, "application", "Girls in a low-income area have poor facilities and must pay for football outside school. Which combined response is best supported?",
    ["Improve access to suitable provision through schools or partner facilities.", "Reduce the cost barrier through association, government or stakeholder support."],
    ["Prioritise transport support because facility quality affects retention after participation begins.", "Create a free introductory programme and move retained players into the existing paid pathway.", "Concentrate coaching resources at the strongest local club so quality compensates for travel and fees."],
    "The chapter links dropout to inferior facilities, suboptimal times, transport and cost, especially when school opportunities are absent. Partnerships and funding should improve both access and affordability. A short free entry point or a distant high-quality hub leaves the structural barrier in place.")

# PDF page 6 / handbook pages 238-239: participation opportunities, PlayMakers and governance.
add(6, "explanation", "Which wider benefits provide a case for increasing girls' participation in football?",
    ["Development of athletic and movement skills.", "Physical and mental well-being across the life course.", "Educational attainment and transferable life skills."],
    ["Earlier sporting specialisation that strengthens elite pathways.", "Greater employment access through qualifications gained in organised sport."],
    "Participation can support physical competence, health, continued activity, education and skills such as cooperation, leadership and communication. These effects strengthen the social and football case for access. The chapter does not present early specialisation or direct qualifications as the mechanism.")
add(6, "application", "A PlayMakers-style session is being designed for girls new to football. Which features fit the model?",
    ["Use familiar stories and characters to stimulate imaginative play.", "Create a positive learning environment in which mistakes feel safe.", "Develop life, movement, game and basic football skills.", "Match delivery to five- to eight-year-old beginners."],
    ["Use story outcomes as progressive performance goals before introducing football techniques."],
    "PlayMakers uses Disney-inspired storytelling as the delivery approach for young beginners. Its context combines safety, welcome and play with life, movement and football goals. The story supports exploration rather than becoming a disguised performance curriculum.")
add(6, "factual_anchor", "What is the central design logic shown in the PlayMakers framework?",
    ["Align who the programme serves, what it delivers and how it delivers within a positive context."],
    ["Move from life skills to movement skills and then to football basics within each story.", "Use the self-confidence goal to connect imaginative play with regular activity.", "Balance the Disney narrative with a club pathway suited to beginner players.", "Define the learning environment before selecting the age group and football goals."],
    "The framework connects who, what and how around goals, context and self. It is aimed at young beginners, develops several kinds of skill and uses a positive PlayMakers approach. The components are aligned rather than arranged as a fixed teaching sequence.")
add(6, "application", "A club wants its recruitment message to reach girls who are new to football. Which communication choices are source-grounded?",
    ["Advertise in places the target audience already uses.", "Use inclusive images and explain health and social benefits."],
    ["Lead with competitive opportunities so interested girls can identify an appropriate standard.", "Use social media as the main channel and ask existing players to validate the message.", "Place the campaign around football venues so parents can see the available infrastructure."],
    "Communication should meet girls and women in schools, colleges, gyms, cafes and their networks. Inclusive imagery, benefits, social media, word of mouth and bring-a-friend activity broaden reach. A competition-led or venue-centred message may reproduce the barriers facing newcomers.")
add(6, "explanation", "Why should current players be given a voice when participation opportunities are redesigned?",
    ["They can identify practical changes that would improve their experience.", "Their preferences help tailor venue, format and delivery.", "Participation in design can reveal barriers that managers have overlooked."],
    ["Player input provides evidence of demand before resources are committed.", "Consultation is most useful after partners have defined the formats they can support."],
    "Players experience the pathway directly and can reveal how provision fits or fails. Their input supports tailored, participant-centred design and can be gathered through tools such as an online forum. It should shape choices early rather than merely validate a feasible offer.")
add(6, "application", "A national association has a participation idea but lacks venues and delivery funding. Which actions follow the chapter's guidance?",
    ["Partner with schools and colleges.", "Explore facilities linked to boys' and men's clubs.", "Seek FIFA, UEFA, government and commercial resources.", "Coordinate partners around the shared participation goal."],
    ["Reduce the initial target group so existing association facilities can support a consistent programme."],
    "Participation growth often depends on partners that hold facilities, reach or funding. Schools, clubs, governing bodies, government and commercial organisations can contribute complementary resources. Narrowing the audience to fit internal capacity would leave the access problem unresolved.")
add(6, "explanation", "Why is storytelling useful in an introductory football programme?",
    ["It encourages creativity and original thinking while reducing fear of mistakes."],
    ["It makes football techniques meaningful before girls enter competitive play.", "It creates a shared social identity that supports retention beyond the sessions.", "It allows mixed-ability players to progress without formal skill assessment.", "It connects health benefits with characters that parents and children recognise."],
    "Storytelling creates an imaginative and psychologically safe way to move and play. That can make football more attractive and support experimentation among beginners. The chapter does not claim that it substitutes for progression, assessment or retention planning.")
add(6, "application", "Girls say the existing league venue and format are a poor fit for how they want to play. Which response is appropriate?",
    ["Offer participation formats and indoor or outdoor venues shaped by participant preferences.", "Use player feedback to test and refine the redesigned opportunity."],
    ["Retain the league format and change session length so the pathway remains connected to competition.", "Move the programme into local communities before asking players which format they prefer.", "Offer a single-sex version first because venue concerns may reflect discomfort in mixed settings."],
    "The guidance is to tailor opportunities to girls and women, including venue, format and local context, and to give players a voice. Consultation should inform the design rather than follow a predetermined solution. A league, community or girl-only format may work, but none is the default answer.")
add(6, "explanation", "How can a participation programme support both football development and broader social outcomes?",
    ["It builds movement and football capability.", "It can improve health and continued activity.", "It develops cooperation, leadership and communication skills."],
    ["It turns social benefits into recruitment messages that strengthen the elite talent pathway.", "It makes educational outcomes part of the association's performance framework for grassroots coaches."],
    "Participation creates football capability and can also support well-being, education and life skills. These outcomes reinforce one another without reducing the programme to talent production. Communication may explain the benefits, but the social value should be embedded in the experience itself.")

# PDF page 7 / handbook pages 240-241: governance, stakeholder mapping and power.
add(7, "application", "A women's football board is reviewing whether its governance environment supports growth. Which positive conditions should it look for?",
    ["Evidence of interventions that work.", "Knowledge-sharing among stakeholders.", "Visible leadership support.", "Commitment to equality and sustainable commercial progress."],
    ["A single accountable funder that can coordinate the transition from dependency to sustainability."],
    "The chapter identifies evidence, shared learning, leadership, a climate for change, steps towards sustainability and equality commitments as opportunities. These conditions can be distributed across the ecosystem. Sustainability does not depend on finding one funder to own the transition.")
add(7, "explanation", "Why is unclear ownership a serious threat to sustainable women's football development?",
    ["It weakens accountability for coordinating resources, decisions and long-term outcomes across the stakeholder system."],
    ["It prevents national associations from distinguishing governance duties from commercial responsibilities.", "It leaves development funding dependent on stakeholders with unequal domestic resources.", "It makes good practice difficult to transfer between clubs, leagues and governing bodies.", "It allows calendar and regulatory differences to persist without a recognised competition authority."],
    "Women's football involves many organisations, so unclear ownership can leave essential work uncoordinated and nobody answerable for sustainability. Funding inequality and structural differences worsen that risk but are separate threats. Effective governance clarifies who leads, contributes and reports.")
add(7, "factual_anchor", "Which statements reflect the chapter's stakeholder concept and mapping approach?",
    ["A stakeholder can affect or be affected by organisational objectives.", "Stakeholders can be mapped by power and support."],
    ["Stakeholder status depends on a recognised economic, political or legitimate form of power.", "Mapping begins with organisations that control resources for women's football.", "Support measures whether a stakeholder's objectives align with the national association's strategy."],
    "Stakeholder status comes from affecting or being affected by the organisation, not from possessing a particular kind of power. Mapping then examines dimensions such as power, support, legitimacy, urgency and interest. Support is contextual and should not be reduced to formal strategic alignment.")
add(7, "application", "A national association is mapping stakeholders for a new women's league. Which steps are appropriate?",
    ["Identify bodies and groups that affect or experience the league's decisions.", "Assess the nature and strength of their power.", "Evaluate their support and interests."],
    ["Exclude service providers whose influence is contractual rather than strategic.", "Map national government within political context before treating it as a football stakeholder."],
    "The map should include governing bodies, clubs, players, partners, government, NGOs, broadcasters and providers where relevant. Power, support and interests help explain how to engage them. Contractual or public-sector status does not remove stakeholder relevance.")
add(7, "explanation", "Which examples correctly illustrate the chapter's four forms of stakeholder power?",
    ["Financial input can create economic power.", "Election or organised backing can create political power.", "An assigned decision-making role can create legitimate power.", "Charisma and respected leadership can create referent power."],
    ["A stakeholder deeply affected by a decision has legitimate power through the moral basis of the claim."],
    "Economic, political, legitimate and referent power describe different sources of influence. Being affected can create a strong normative claim, but it is not the chapter's definition of legitimate power in this four-part list. That distinction prevents moral standing and formal authority from being conflated.")
add(7, "factual_anchor", "How does the chapter contrast an individual fan with an organised fan group?",
    ["An organised group can aggregate voices and use media and matchday channels to gain substantial influence."],
    ["An organised group gains political power because it represents a recognised supporter constituency.", "An individual fan has economic power through ticket purchases but limited legitimate power.", "A fan group moves from low to high support when its objection attracts wider media attention.", "An individual fan becomes strategically important when digital engagement can be measured."],
    "One fan may have little influence, but a coordinated group can make its voice heard through social media, broadcasts and chanting. The change is the aggregation and exercise of influence, not a formal transfer of political or legitimate authority. Support and power remain separate dimensions.")
add(7, "application", "A low-power player group is deeply affected by a proposed calendar change. Which responses are justified?",
    ["Recognise the group as a stakeholder because it is affected.", "Consider the moral legitimacy of its claim as well as its strategic influence."],
    ["Increase the group's mapped support score so the effect is visible in prioritisation.", "Consult the group after powerful competition stakeholders have identified feasible options.", "Treat player unions as the representative stakeholder if the players lack direct decision power."],
    "The stakeholder definition and normative approach require attention to affected groups even when power is low. Strategic mapping can inform engagement, but it should not erase moral significance. Representation may help, yet direct effects still deserve a voice.")
add(7, "explanation", "How should power and support be interpreted together in stakeholder mapping?",
    ["Power estimates a stakeholder's capacity to influence decisions.", "Support indicates the stakeholder's current orientation towards the organisation or goal.", "A powerful but weakly supportive stakeholder needs a different engagement strategy from a powerful ally."],
    ["High support increases the legitimacy of a stakeholder's power.", "Low support reduces strategic priority unless the stakeholder's concerns are urgent."],
    "Power and support answer different questions and create a more useful map when read together. A high-power ally can help delivery, while a high-power sceptic may require understanding and engagement. Support does not confer legitimacy or cancel the influence of opposition.")
add(7, "application", "A league initiative has leadership backing but lacks data, resources and clear accountability. Which governance response follows the threat analysis?",
    ["Define ownership and reporting responsibility.", "Improve the evidence base.", "Secure dedicated resources.", "Coordinate regulatory and calendar issues across stakeholders."],
    ["Launch a pilot while the governance model is negotiated."],
    "Leadership support is an opportunity, but it does not neutralise missing data, ownership, resources or structural coordination. Those gaps should be addressed explicitly so the initiative can become sustainable. A pilot without clear responsibility can reproduce the same governance weakness.")

# PDF page 8 / handbook pages 242-243: stakeholder management, leagues and club structures.
add(8, "application", "A stakeholder map has been completed for a women's football strategy. What is its most important next use?",
    ["Design engagement and collaboration that move stakeholders towards shared development goals."],
    ["Rank stakeholder needs so scarce development resources can be distributed transparently.", "Identify which powerful stakeholders should own each strategic objective.", "Test whether a win-win outcome is possible before the strategy is approved.", "Separate strategic stakeholders from groups whose claims are mainly normative."],
    "Mapping is useful because it informs what the organisation should do with and about stakeholders. It supports tailored engagement, priority and collaboration around shared goals. It should not turn power into ownership or remove affected groups from the strategy.")
add(8, "explanation", "Why must strategic and normative stakeholder perspectives be used together?",
    ["The strategic view recognises influence and implementation risk.", "The normative view protects the claims of people deeply affected despite limited power."],
    ["The strategic view prioritises shared goals, while the normative view resolves conflicts through compromise.", "The strategic view applies to organisations, while the normative view applies to players and communities.", "The strategic view maps power and support, while the normative view maps legitimacy and urgency."],
    "Strategic analysis helps leaders work with stakeholders capable of enabling or obstructing change. Normative analysis prevents low-power affected groups from being ignored. The perspectives are ethical and managerial lenses, not separate maps for different stakeholder types.")
add(8, "factual_anchor", "Which tasks are identified as requirements for effective women's football development?",
    ["Identify stakeholders specific to the women's game.", "Evaluate their interests and relative power.", "Use the evaluation to seek shared goals and win-win outcomes."],
    ["Assign sustainable-development accountability to the strongest governing stakeholder.", "Standardise stakeholder categories across national and regional contexts."],
    "The chapter sets out identification, evaluation and collaborative use of that evaluation as the core sequence. Context determines which stakeholders matter and what power they have. Accountability should be clarified, but it is not assigned mechanically to the strongest body.")
add(8, "application", "A youth coach and first-team coach want the same small development budget for different purposes. Which responses fit effective stakeholder management?",
    ["Clarify each party's objective and underlying interest.", "Explore whether cooperation can create a different win-win solution.", "Consider a transparent compromise if joint value cannot be created.", "Recognise the longer-term relationship cost if one party simply wins."],
    ["Give priority to the first-team request if elite performance is a stated strategic goal."],
    "A win-win result is desirable but may not be feasible when resources are fixed. Dialogue can uncover alternatives, and compromise may be preferable to an imposed win that damages later cooperation. Strategic importance informs judgement but does not settle the conflict by itself.")
add(8, "explanation", "Which statement best captures the structural focus of a stand-alone women's club in the chapter?",
    ["Its identity, resources and promotion can remain centred on the women's team without dependence on a men's club."],
    ["Its specialist staff divide their time between women's sporting and commercial roles.", "It keeps a separate identity while remaining inside a men's club reporting perimeter.", "It is insulated from calendar and regulatory differences affecting integrated clubs.", "It depends on women's football revenues rather than parent-club contributions."],
    "A stand-alone club can forge its own identity and devote organisational attention to the women's team. Specialist expertise and independence from a men's team's fortunes can follow. That structure does not guarantee commercial self-sufficiency or freedom from wider league constraints.")
add(8, "factual_anchor", "Which facts describe the European women's league landscape in the chapter?",
    ["The benchmarking report counted 52 leagues involving 485 clubs.", "A minority of leagues were professional while most were amateur."],
    ["Professional leagues were concentrated in countries where women's clubs were integrated with men's clubs.", "League format differences mainly reflected whether players were local or international.", "Calendar variation was presented as a domestic issue rather than a European competition concern."],
    "European leagues differ in professionalism, format, timing and national context. Those differences affect player quality, recruitment and the development of European competitions. The chapter does not reduce the pattern to club integration or recruitment geography.")
add(8, "application", "A women's team is considering integration with a major men's club. Which benefits are supported?",
    ["Shared training and stadium infrastructure.", "Bundled sponsorship opportunities.", "Access to specialist marketing and technical staff."],
    ["Protection from reduced investment if the men's first team is relegated.", "A separate reporting perimeter that gives the women's team independent control of shared staff."],
    "Integration can unlock infrastructure, brand, sponsorship and specialist expertise. It also creates a risk that shared staff and resources favour the men's side or that men's-team problems affect the women. A separate operating entity can clarify responsibility but does not create full control over shared assets.")
add(8, "explanation", "Which considerations support a balanced comparison of stand-alone and integrated women's clubs?",
    ["Stand-alone clubs can build a distinct identity.", "Stand-alone resources remain focused on the women's team.", "Integrated clubs can share infrastructure and expertise.", "Integrated clubs can benefit from a recognised parent brand and commercial bundling."],
    ["The preferred structure depends mainly on whether the domestic women's league is professional or amateur."],
    "Each structure has advantages and risks, and cultural and national context affect the choice. Stand-alone models offer focus and autonomy, while integration offers assets, expertise and reach. League status matters but does not determine the organisational answer.")
add(8, "application", "A national association is assessing where women's football sits within its own organisation. What should the review establish first?",
    ["Its current structure, headcount, funding and responsibility for participation and talent pathways."],
    ["Whether a dedicated department would provide clearer ownership than staff distributed across divisions.", "Whether the women's committee has authority over league and club development.", "Which domestic stakeholders can supplement UEFA and FIFA funding.", "How the current structure compares with associations whose leagues are professional."],
    "The chapter stresses understanding the current state and status of women's football inside the association. Structure, staffing, resources and development responsibilities reveal barriers and opportunities. Comparison and redesign come after that diagnosis rather than defining it.")
add(8, "explanation", "What does a realistic win-win approach require in stakeholder management?",
    ["Search for ways to create shared value before accepting a zero-sum allocation.", "Recognise when compromise or a difficult trade-off remains necessary."],
    ["Give each stakeholder a benefit proportional to its mapped power and support.", "Use normative claims to protect low-power groups when strategic goals conflict.", "Set shared goals first and defer distributional conflicts to implementation."],
    "Win-win thinking encourages creativity and cooperation, but the chapter accepts that fixed resources can prevent everyone receiving the preferred outcome. Transparent compromise or choice may then be required. Mapping supports engagement rather than supplying a formula for benefits.")

# PDF page 9 / handbook pages 244-245: professionalisation, fans, broadcasting and sponsors.
add(9, "application", "A league is moving more players onto professional contracts. Which safeguards should accompany the transition?",
    ["Plan for education and careers beyond short playing lives.", "Prepare players for increased media scrutiny.", "Assess whether salaries provide realistic financial security."],
    ["Prioritise full-time contracts for players whose performance gains can increase league visibility.", "Use club licensing to align professional salaries with the support available after retirement."],
    "Professionalisation can raise sporting quality by allowing full-time focus, but it also increases dependence on contracts and public pressure. Careers are short and pay may not secure the future. Player welfare and transition support therefore belong alongside sporting and commercial planning.")
add(9, "explanation", "Which benefits and risks of player professionalisation are identified?",
    ["Full-time commitment can improve playing quality.", "Players become more dependent on contract income.", "Short careers and lower salaries create post-playing financial risk.", "Greater media scrutiny creates additional pressure."],
    ["Professionalisation widens the gap between international players and those in amateur domestic leagues."],
    "The chapter presents professionalisation as a genuine sporting opportunity with material personal risks. Full-time work can improve standards, yet financial security and scrutiny become more acute. The comparison with amateur leagues does not establish the extra gap described in the distractor.")
add(9, "factual_anchor", "What commercial role do fans play in the chapter's model?",
    ["Larger audiences can increase ticket income and make the property more valuable to sponsors and broadcasters."],
    ["Stadium attendance provides advertisers with the audience evidence needed to value broadcast rights.", "Digital viewers create sponsor value when they can be converted into ticket-buying supporters.", "Showcase-event audiences establish the commercial trend used to price regular league rights.", "Fan growth raises club income before it affects sponsorship and broadcasting demand."],
    "Fans create direct ticket value and indirect leverage with broadcasters and sponsors. Traditional models often use audience size as a driver, although later sections challenge attendance as the required starting point. Digital and stadium audiences can both matter without following one conversion sequence.")
add(9, "application", "A national association launches a free streaming channel for domestic women's matches. Which outcomes should it monitor separately?",
    ["Growth in reach and engagement.", "Direct and indirect commercial revenue."],
    ["The rights value created by moving viewers from free streams to broadcast partners.", "The sponsorship value generated by average live-stream audiences.", "The proportion of digital viewers who later attend showcase matches."],
    "Free digital coverage can expand awareness and engagement while producing little direct income. The association should therefore distinguish audience-building from monetisation and assess broader sponsor or rights effects carefully. A particular conversion path is possible but is not guaranteed by the source.")
add(9, "explanation", "Why did unbundling women's competition sponsorship rights represent a development opportunity?",
    ["It allowed women's competitions to be valued and marketed as distinct properties.", "It enabled partners to associate directly with the values of the women's game.", "It created packages spanning elite competitions and grassroots initiatives."],
    ["It separated women's rights from the attendance assumptions used to price men's properties.", "It gave UEFA control of club sponsorship categories needed for centralised broadcasting."],
    "Unbundling created a clear women's football proposition for internationally recognised brands. It connected competition and grassroots assets and enabled direct image transfer. The move challenged inherited packaging, but it did not remove the need to demonstrate value or establish broadcast control.")
add(9, "application", "A sponsor is considering a women's league with modest but growing audiences. Which value case is most credible?",
    ["Present audience growth and engagement.", "Show the fit between the sponsor's brand and positive values in women's football.", "Explain the digital communities through which image transfer can occur.", "Define how the partnership will activate both awareness and association."],
    ["Price the rights against the larger future market that digital reach is expected to create."],
    "Women's football sponsorship can offer awareness and valuable image transfer even before audiences match mature properties. Digital platforms make associations visible across broad communities. A credible case uses evidence and activation rather than capitalising anticipated growth into the present price.")
add(9, "factual_anchor", "What did the cited 2018/19 live-stream data suggest about club structure and digital audiences?",
    ["Integrated clubs reported much larger average digital audiences than stand-alone clubs."],
    ["Integrated clubs converted the parent men's audience into higher sponsorship income.", "Stand-alone clubs relied more heavily on free streams to build visibility.", "Integrated clubs generated average audiences comparable with major tournament broadcasts.", "Stand-alone audiences grew more consistently because the women's identity was distinct."],
    "The cited averages were about 72,101 per game for integrated clubs and 4,511 for stand-alone clubs. The chapter suggests that association with a high-profile men's club may help attract viewers. It does not establish the proposed revenue, platform or growth mechanisms.")
add(9, "explanation", "How does the chapter qualify the traditional link between audience size and sponsorship value?",
    ["Audience reach remains important.", "Image transfer can create value through association with the game's positive qualities."],
    ["Digital targeting makes sponsor fit more reliable than mass audience awareness.", "Naming rights create greater value when competition audiences are unstable.", "Shared values matter mainly when rights have been unbundled from men's football."],
    "Traditional sponsorship thinking begins with awareness and audience size, but women's football also offers image and values association. Digital communities can expand that opportunity. The chapter adds a second value route rather than declaring audience reach obsolete.")
add(9, "application", "A club relies heavily on its parent team and governing-body grants. Which steps would strengthen financial resilience?",
    ["Develop sponsor relationships based on audience and values fit.", "Explore broadcast and digital revenue while building reach.", "Broaden the mix of earned and external funding."],
    ["Reduce parent-club contributions once commercial income covers the women's first-team budget.", "Prioritise ticketing because matchday revenue demonstrates progress towards self-sustainability."],
    "The funding chart and discussion show considerable dependence on founders, parent clubs and grants. Sustainability requires a broader commercial model, but external support may still help development. No single revenue line, including ticketing, is a sufficient test of resilience.")

# PDF page 10 / handbook pages 246-247: sustainability and change processes.
add(10, "application", "A league describes itself as sustainable because its parent clubs and governing bodies have committed funding for five years. Which conclusions are appropriate?",
    ["The funding provides valuable development support.", "Dependence on a small set of contributors remains a sustainability risk.", "Commercial income streams should be developed alongside the support.", "The model should be reviewed against participation, governance and competition goals."],
    ["Five-year certainty is sufficient for sustainability while audiences and sponsor value are still developing."],
    "The chapter says European women's football was not self-sustaining and relied substantially on parent clubs and grants. Stable support can start and protect development, but resilience requires a wider model and progress across the football ecosystem. Funding duration alone does not establish sustainability.")
add(10, "explanation", "Why is current dependence on founders, parent clubs and grants strategically important?",
    ["It exposes women's football to decisions and resources outside its own earned-income model, making long-term development vulnerable."],
    ["It places commercial development behind the priorities of organisations that also fund men's football.", "It prevents clubs from using sponsorship and broadcasting income to professionalise players.", "It makes national associations accountable for club sustainability without control of league revenues.", "It means commercial initiatives should replace development grants before the game can grow independently."],
    "External contributions are important but create dependency when the game cannot sustain itself through a broader resource base. The risk is vulnerability, not a rule that funders necessarily neglect the women's game. Strategy should diversify and develop income without withdrawing useful investment prematurely.")
add(10, "factual_anchor", "Which statements describe Lewin's force field model as used in the chapter?",
    ["Identify and weight forces that support change.", "Identify and weight forces that restrain change."],
    ["Classify each force by context, content or process before assigning influence.", "Multiply the strongest driving force by the number of opposing forces.", "Treat equal totals as evidence that gradual change remains feasible."],
    "Force field analysis identifies driving and restraining forces and assigns weights to their influence. Change is expected when the driving total exceeds the restraining total. The model is contextual but does not use Pettigrew categories as its scoring method.")
add(10, "application", "An association's force field shows strong strategy and participation initiatives but weak resources and severe calendar problems. Which actions follow the model?",
    ["Preserve and build on the positive strategic forces.", "Mitigate the resource constraint.", "Resolve calendar obstacles with relevant stakeholders."],
    ["Increase the weight assigned to participation initiatives after early delivery evidence is available.", "Launch the strategy while the driving total is close to the restraining total and reassess after one cycle."],
    "Force field analysis is used to act on the balance, not merely describe it. The association should strengthen drivers and remove or reduce specific restraints such as resources and calendars. Reweighting should reflect changed reality, and implementation should not be used to wish away an unfavourable balance.")
add(10, "explanation", "Why must force field weights be determined in the association's own context?",
    ["The same factor can have different influence across countries and organisations.", "Available resources and stakeholder relationships vary.", "Competition and calendar structures vary.", "Locally grounded weights reveal which obstacles and drivers deserve action."],
    ["Common weights are useful after associations agree a shared European development objective."],
    "Lewin's model is deliberately situational. Funding, participation, strategy, leagues, resources and calendars do not exert the same force everywhere. A common objective can aid coordination, but it does not make local influence comparable without analysis.")
add(10, "factual_anchor", "Which example is presented as a force against the development of women's football?",
    ["A lack of dedicated resources."],
    ["Dependence on grants from governing bodies.", "Unequal access to domestic stakeholder funding.", "Variation in national-association structures.", "Limited commercial value from digital rights."],
    "The example model lists lack of leagues and competitions, lack of dedicated resources and calendar problems as restraining forces. The other issues may be wider threats or contextual concerns, but they are not the labelled forces in Figure 8.6.")
add(10, "application", "A participation objective is ambitious while its delivery resources remain undefined. Which next steps are justified?",
    ["Assess strengths and weaknesses relevant to the goal.", "Identify funding, partners and best-practice initiatives that can support delivery."],
    ["Reduce the target until internal association resources can meet the full delivery requirement.", "Adopt the UEFA doubling ambition so external partners understand the intended scale.", "Begin with the strongest existing programme and measure whether it can be expanded nationally."],
    "Goals can be ambitious or more modest, but they need an honest delivery analysis. Resources, partners, strengths, weaknesses and transferable practice help convert ambition into a process. The UEFA target provides inspiration rather than a mandatory local scale.")
add(10, "explanation", "How do Pettigrew's process perspective and Lewin's force field analysis complement one another?",
    ["Pettigrew asks how the intended change will be achieved.", "Force field analysis identifies drivers and restraints affecting that delivery.", "The analysis helps select actions that strengthen or mitigate specific forces."],
    ["Pettigrew establishes the change goal, while Lewin tests whether stakeholder support is sufficient.", "Force field totals determine whether the content of change should be revised before implementation."],
    "Pettigrew provides the broad context-content-process logic, while Lewin offers a practical way to analyse the conditions surrounding implementation. The force field can shape actions within the process. It informs but does not mechanically redefine the goal or reduce feasibility to stakeholder support.")
add(10, "application", "A national association is reviewing governance before launching a women's football strategy. Which questions should it address?",
    ["Where does women's football sit in the organisation?", "Is ownership concentrated or distributed across departments?", "Are there dedicated committee and strategy arrangements?", "Which stakeholders must participate in delivering priority goals?"],
    ["Which organisational model among UEFA's associations should be adopted as the reference structure?"],
    "The chapter encourages associations to diagnose their structure, leadership, strategy and stakeholder system. Several structural models exist, so the aim is to understand fitness for local goals rather than copy one reference design. Ownership and involvement should be explicit before delivery.")

# PDF page 11 / handbook pages 248-249: structures and the commercial sustainability cycle.
add(11, "application", "Women's football specialists are scattered across an association and no unit owns the strategy. What is the first governance priority?",
    ["Clarify responsibility, coordination and decision rights for the strategy within the existing structure."],
    ["Create a dedicated women's football department so specialist headcount is brought under one leader.", "Establish a women's football committee before reallocating responsibility across divisions.", "Appoint a strategy lead who reports across the departments containing specialist staff.", "Benchmark the structure against associations with comparable participation and league status."],
    "The chapter presents several organisational forms and asks leaders to understand their own arrangement. The immediate need is clear ownership and coordination aligned with goals. A department, committee or cross-functional lead may be suitable later, but structure should follow diagnosis rather than assumption.")
add(11, "explanation", "Why should organisational structure be assessed together with strategy and resources?",
    ["Structure determines where responsibility and expertise sit.", "Strategy and resources determine whether that arrangement can deliver the chosen goals."],
    ["Structure provides accountability, while strategy provides stakeholder legitimacy.", "Resources determine which of the four association structures is viable.", "Strategy should be finalised before structure so roles can be assigned without duplication."],
    "A chart alone says little about effectiveness. Leaders need to know who owns the work, what the priorities are and whether staffing and funding match them. Strategy and structure should be aligned iteratively rather than in a rigid sequence.")
add(11, "factual_anchor", "Which assumptions form part of the traditional commercial cycle described in the chapter?",
    ["Large attendances attract broadcasters.", "Large global audiences attract sponsors.", "Commercial revenue supports professionalisation and sporting quality."],
    ["Professionalisation leads clubs to unbundle women's commercial rights.", "Sporting quality converts digital viewers into regular match-going fans."],
    "The traditional cycle links attendance, broadcasting, sponsorship, revenue, professionalisation, quality and renewed audience growth. Rights structure and digital conversion can influence the cycle but are not assumptions listed in it. The chapter later challenges the idea that attendance must be the entry point.")
add(11, "application", "A women's league has limited stadium attendance but a strong values-based sponsor and growing digital reach. Which interventions can advance the sustainability cycle?",
    ["Use sponsorship income to improve resources and professionalisation.", "Use digital reach to strengthen broadcast and partner value.", "Invest in product quality and audience engagement.", "Treat progress at either commercial point as capable of feeding the circular process."],
    ["Direct sponsor activation towards attendance growth before allocating funds to professionalisation."],
    "The cycle is circular, so sponsorship, broadcasting, investment, quality or audiences can provide an entry point. The league should connect its existing strengths so gains reinforce other stages. It need not force sponsorship through attendance before improving the product.")
add(11, "explanation", "What is the key implication of viewing the commercial model as a circular process?",
    ["Progress can begin at different stages, so weak attendance need not prevent interventions through sponsorship, broadcasting or investment."],
    ["Each stage should be strengthened until it can generate resources for the next stage.", "External funding is most useful at the professionalisation stage because it raises product quality.", "A break in one stage can be bypassed temporarily while the rest of the cycle develops.", "The cycle becomes virtuous once commercial revenue exceeds external contributions."],
    "A circle has no mandatory first step. Gains in sponsorship, media reach, investment, professionalisation or product quality can stimulate the other elements. The implication is strategic flexibility, not a fixed sequence or a single threshold for virtue.")
add(11, "factual_anchor", "Which sources can provide initial investment to start the sustainability cycle?",
    ["Parent clubs or private investors.", "National associations or governing-body programmes."],
    ["Broadcasters through free production and distribution.", "Sponsors through image-transfer rights packages.", "Supporters through membership and academy fees."],
    "The chapter explicitly identifies parent clubs, angel investors, national associations and governing bodies such as UEFA as sources that can kick-start development. Other stakeholders may later generate income, but they are not grouped as initial external funding in this passage.")
add(11, "application", "A sponsor chooses a women's league for its equality values rather than its current audience size. Which strategy should the league follow?",
    ["Build a partnership around credible values fit.", "Use the investment to strengthen sustainability and professionalisation.", "Connect sponsor activation with audience and product development."],
    ["Treat image transfer as a temporary entry route until attendance can support awareness-led sponsorship.", "Separate the equality message from league operations so sporting quality remains the commercial product."],
    "Values-based sponsorship can itself be a meaningful entry point into the commercial cycle. Credible activation and reinvestment can improve the football product and audience relationship. Image transfer is not merely a bridge to a supposedly superior attendance model.")
add(11, "explanation", "How can the traditional model appear as either a virtuous or vicious circle?",
    ["Audience growth can attract commercial partners.", "Commercial revenue can support quality and professionalisation.", "A better product can stimulate further audience growth.", "Weak attendance can seem to block the commercial stages when it is treated as the required starting point."],
    ["The circle becomes vicious when external funding supports quality without producing a proportional audience increase."],
    "The same feedback structure can reinforce growth or appear to trap an immature property. The chapter's response is that the cycle can be entered elsewhere rather than accepting attendance as the gatekeeper. External investment may be a solution, not evidence of failure.")
add(11, "application", "A league's attendance campaign has stalled, but an OTT platform offers investment and distribution. What is the strongest strategic interpretation?",
    ["Use the media intervention as an alternative entry point that can build reach, revenue and later demand elsewhere in the cycle."],
    ["Accept distribution while protecting the attendance campaign as the primary route to sustainable revenue.", "Use the platform to establish audience data before negotiating sponsor packages.", "Treat the offer as external funding until viewers begin generating rights income.", "Delay professionalisation spending until digital engagement shows a link with product demand."],
    "Digital broadcasting can begin movement in the circular model without waiting for stadium growth. It can build reach, commercial evidence and resources that improve the product and attract partners. The league should integrate the opportunity rather than subordinate it to the old first-step assumption.")

# PDF page 12 / handbook pages 250-251: image transfer, revised commercial logic and conclusion.
add(12, "explanation", "How do awareness and image transfer differ as sponsorship objectives?",
    ["Awareness seeks exposure to an audience.", "Image transfer seeks association with the property's values and emotional meaning."],
    ["Awareness is achieved through attendance, while image transfer is achieved through digital engagement.", "Awareness is a base-level objective, while image transfer requires the sponsor to finance sporting development.", "Awareness values audience size, while image transfer values growth potential rather than current reach."],
    "Awareness concerns being seen, whereas image transfer concerns what qualities attach to the sponsor through the relationship. Women's football can offer both, including values such as equality and a fast-growing identity. Platform and investment choices support activation but do not define the two objectives.")
add(12, "application", "A sponsor values equality and the growth story of women's football. Which partnership design is most defensible?",
    ["Demonstrate a genuine fit between the sponsor and the football property.", "Create activation that expresses the shared values.", "Measure both audience effects and the intended brand association."],
    ["Emphasise the future market size so the values fit can be converted into an awareness target.", "Use the equality objective for community activation while commercial messaging focuses on sporting growth."],
    "Image transfer depends on credible similarity between sponsor aims and the football property's values. Activation should make that relationship visible, and evaluation should examine awareness and association. Separating equality from the commercial story would weaken the reason the sponsor chose the property.")
add(12, "explanation", "Which developments challenge the assumption that fan-base growth must begin the sustainability process?",
    ["Increasing value in women's broadcast rights.", "The rise of association-, league- and club-controlled OTT platforms.", "Major sponsorship deals based on fit and shared values.", "External investment that can improve resources and professionalisation."],
    ["The growth of showcase audiences that gives commercial partners evidence beyond domestic attendance."],
    "Broadcast change, digital distribution, values-based sponsorship and external investment offer several alternative starting points. They can drive reach, revenue and quality before regular attendance is mature. Showcase audiences help the case, but the chapter's challenge rests on new market mechanisms rather than event evidence alone.")
add(12, "factual_anchor", "Which principle best captures the chapter's conclusion on development models?",
    ["No perfect model exists; associations should use contextual analysis, shared learning and adaptable tools to move the women's game forward."],
    ["Associations should combine the strongest participation, governance and commercial practices from comparable countries.", "Sustainability requires locally selected entry points into a common European development cycle.", "Stakeholder analysis should determine which development model has the broadest win-win potential.", "Context should shape implementation while UEFA and FIFA strategies provide the common content."],
    "The chapter repeatedly emphasises variation in national context, structures, barriers and opportunities. Tools and useful initiatives can be shared, but there is no universal solution. Strategy requires informed adaptation rather than selecting a model through one criterion.")
add(12, "application", "A strategy produces commercial growth but players and grassroots groups say they were excluded from decisions. Which response follows the conclusion?",
    ["Reassess who is affected and improve stakeholder engagement.", "Seek win-win adjustments that preserve progress while addressing legitimate participation and player concerns."],
    ["Use the commercial gains to fund the missing grassroots priorities before reopening the strategy.", "Add player and grassroots indicators so future reviews capture their outcomes.", "Protect the current strategy until the new revenue model has demonstrated sustainability."],
    "Successful development depends on understanding and working with stakeholders, including those affected by decisions. Commercial progress does not remove the normative need for engagement. Funding and indicators may help, but they should follow renewed dialogue rather than substitute for it.")
add(12, "explanation", "How does Pettigrew's context-content-process model organise the chapter's final strategic message?",
    ["Context explains national history, PESTEL forces and governance conditions.", "Content covers participation, empowerment and sustainable commercial development.", "Process uses stakeholder work and change tools to achieve those aims."],
    ["Context determines which global goals are feasible, while content and process adapt the FIFA and UEFA strategies.", "Process begins when force field analysis shows that drivers exceed restraints."],
    "The chapter uses context to diagnose, content to define the development agenda and process to plan action. FIFA and UEFA goals inform the agenda but do not replace local choice. Force field analysis can support process planning even when the initial balance shows difficult restraints.")
add(12, "application", "A national association is preparing an integrated plan for the next cycle of women's football. Which workstreams reflect the chapter's conclusion?",
    ["Grow and retain grassroots participation.", "Strengthen governance, leadership and stakeholder engagement.", "Use communication and commercial innovation to build sustainability.", "Adapt delivery to the country's context and identified forces for and against change."],
    ["Use elite competition growth as the connecting measure across participation, governance and commercial workstreams."],
    "The conclusion joins participation, empowerment, governance and sustainable commercial development within local context. Stakeholder analysis and change models connect the workstreams and guide delivery. Elite competition matters, but it cannot serve as the common measure for this broader system.")


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
        "session_title": "Chapter 8 - Women's football",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
