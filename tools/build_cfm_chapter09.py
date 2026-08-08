"""Build the staged Chapter 9 UEFA CFM football development bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "UEFA-HFM-Football-Development.pdf"
OUTPUT = Path("data/cfm_imports/chapter_09_football_development.json")
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
            "handbook_pages": [252 + 2 * page, 253 + 2 * page],
        },
        "page_crops": [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 256-257: four development areas and the future game.
add(2, "application", "A national association treats football development as a series of annual operational projects. What is the strongest correction?",
    ["Anchor development in a long-term strategic vision for the future game."],
    ["Create a multi-year operational programme before selecting the national playing philosophy.", "Use UEFA's long-term vision as the association's development direction and localise annual actions.", "Let grassroots, coaching and elite departments define separate plans before agreeing common outcomes.", "Build the strategy around the areas where the association has direct delivery responsibility."],
    "Football development needs a long-term direction and is therefore closely linked to strategic management. Operational projects should implement a clear national vision rather than substitute for it. UEFA offers inspiration, while each association must decide how it will shape its own future game.")
add(2, "explanation", "Why is football development more closely associated with strategic than operational management?",
    ["It concerns the future direction of the game over several years.", "It requires a shared vision that coordinates multiple development areas."],
    ["It is governed through national objectives rather than competition delivery processes.", "It depends on stakeholder commitments that extend beyond association planning cycles.", "It measures success through player pathways rather than short-term operational outputs."],
    "Strategic management establishes direction, priorities and a long-term picture of the game. Football development connects grassroots, coaches, elite players and the wider football culture over time. Operational management remains necessary for delivery, but it does not define the destination.")
add(2, "factual_anchor", "Which areas are among the four key pillars of football development in the chapter?",
    ["Grassroots football.", "Coach education.", "Elite player development."],
    ["Competition development.", "Technical leadership."],
    "The four areas are the future game, grassroots football, coach education and elite player development. Competition and technical leadership support those areas but are not separate pillars in Figure 9.1. The framework emphasises a connected national development system.")
add(2, "application", "A board is drafting its national football-development plan. Which choices follow the chapter?",
    ["Define the desired style, philosophy and values of the future game.", "Expand safe, quality-controlled opportunities to play.", "Raise coaching standards across grassroots and elite football.", "Improve elite youth development for top-level demands."],
    ["Use national-team performance to determine which pillar receives priority in the first cycle."],
    "The plan should express a future-game vision and translate it across participation, coaching and elite development. The four areas reinforce one another and protect the long-term health of the game. Current national-team results are evidence, not a sound rule for prioritising one pillar over the system.")
add(2, "explanation", "What does UEFA's instruction to keep football first imply for development strategy?",
    ["Decisions should protect, grow, innovate and promote the game's ecosystem in line with its mission and future needs."],
    ["Football objectives should be set before trust, competitiveness and prosperity are considered.", "Development projects should prioritise playing outcomes over institutional and commercial outcomes.", "The national playing philosophy should guide stakeholder interests when they conflict.", "Innovation should be introduced where it preserves enjoyment for players and supporters."],
    "Keeping football first means using the game's long-term health and enjoyment as the central reference. UEFA's mission includes being played, trusted, competitive and engaging, supported by football, trust, competitiveness and prosperity. The pillars work together rather than establishing football as a narrow sporting priority over the rest.")
add(2, "application", "An association has drafted a future-game philosophy internally. Which next steps are necessary?",
    ["Identify the stakeholders who shape the national game.", "Engage them so the vision is shared and embraced."],
    ["Ask technical stakeholders to approve the playing philosophy before consulting delivery partners.", "Translate the philosophy into grassroots standards before engaging clubs and schools.", "Use the vision as an association mandate and seek stakeholder commitment during implementation."],
    "A national vision succeeds when the actors who influence the game help define and own it. Clubs, coaches, schools, government and other stakeholders need genuine involvement rather than late endorsement. Technical clarity is important, but shared ownership is part of the strategy itself.")
add(2, "explanation", "How do the four football-development areas reinforce one another?",
    ["Grassroots creates access and the foundation of the game.", "Coach education improves the people who shape learning environments.", "Elite development prepares talented players within the national vision."],
    ["The future-game pillar converts progress in the other areas into a unified playing identity.", "Elite success supplies the visibility and resources needed to sustain grassroots and coach education."],
    "The future-game vision gives direction, grassroots provides breadth, coach education improves quality and elite development supports top-level progression. Their effects are reciprocal and should be planned holistically. A national identity is defined up front and refined through the system, rather than produced after the other areas succeed.")

# PDF page 3 / handbook pages 258-259: interconnected sectors and dual pyramids.
add(3, "application", "A development strategy has strong elite academies but weak grassroots provision and coach education. Which responses fit the chapter?",
    ["Improve the grassroots learning and playing environment.", "Develop the coaching workforce.", "Connect both areas to the elite pathway.", "Retain a shared future-game vision across the three sectors."],
    ["Protect academy investment until the participation and coaching systems can provide players of comparable quality."],
    "Elite development cannot be isolated from the breadth and quality of grassroots football or the coaches who influence players. The three sectors supplement one another within the national vision. Protecting one strong component while waiting for the rest would preserve the imbalance.")
add(3, "explanation", "What is the main distinction between participation sport and performance sport?",
    ["Participation emphasises involvement and enjoyment, while performance emphasises competition and results."],
    ["Participation develops lifelong players, while performance develops national-team players.", "Participation is organised through grassroots clubs, while performance is organised through academies.", "Participation prioritises quantity, while performance prioritises quality.", "Participation covers children and adults, while performance begins with adolescent athletes."],
    "The two trajectories differ in their primary orientation, not in a rigid institutional or age boundary. They coexist and interact, and players may move between them according to age, ability and identity. Both require attention to quantity and quality.")
add(3, "factual_anchor", "Which levels belong to the participation and performance trajectories?",
    ["Children and teenagers in participation sport.", "Emerging and performance athletes in performance sport."],
    ["Adults in the performance trajectory after elite competition.", "Academy players as a separate bridge level between the trajectories.", "High-performance athletes as the final level of both trajectories."],
    "Participation sport includes children, teenagers and adults, while performance sport includes emerging, performance and high-performance athletes. The categories describe engagement, not specific institutions. Movement between environments means the trajectories interact without sharing the same final level.")
add(3, "application", "A talented teenager is struggling in an elite academy and is considering returning to community football. Which pathway principles apply?",
    ["Guide the player towards the environment that fits their identity and needs.", "Keep movement between participation and performance pathways possible.", "Treat retention in football as a central outcome."],
    ["Maintain the academy place while adjusting competitive exposure so the player retains elite potential.", "Use chronological age and current ability to identify the more suitable pyramid."],
    "The overlapping pyramids recognise that players can move between grassroots and elite environments. The association and clubs should support the environment that fits the individual while keeping the person in the game. Retention matters more than preserving a status that no longer suits the player.")
add(3, "explanation", "How can a national coach-education philosophy create a national football culture?",
    ["It links a shared playing style to coach development.", "It influences coaches and players in grassroots and elite environments.", "It aligns individual and team development with the future game.", "It connects actors around a common direction."],
    ["It standardises coaching practice so players can move between the two pyramids without changing learning methods."],
    "A shared philosophy spreads the national vision through the people who teach and play the game. It can align environments while allowing age, ability and context to shape practice. Culture comes from connected direction, not uniform sessions across every pathway.")
add(3, "factual_anchor", "Which statement best describes the relationship of grassroots football to the performance pyramid?",
    ["Grassroots forms its foundation and can lead into regional youth competition and academy development."],
    ["Grassroots supplies players to the performance pathway after regional competition identifies talent.", "Grassroots and performance overlap at the academy stage where participation becomes selective.", "Grassroots is the entry layer of performance for children with competitive potential.", "Grassroots supports performance while remaining a separate lifelong-football pyramid."],
    "The chapter depicts grassroots at the base of the performance pyramid as well as within lifelong football. Regional competition and academies can then provide more performance-focused environments. The pathways remain distinct in purpose but overlap and influence one another.")
add(3, "application", "An association wants to reduce player loss between grassroots and elite environments. Which actions are supported?",
    ["Prepare both environments for player movement.", "Use individual guidance to match players with a suitable pathway."],
    ["Create a formal return route from academies to regional youth competition for released players.", "Delay pathway decisions until players reach the performance-athlete phase.", "Use the national playing style as the common selection standard in both environments."],
    "Retention improves when pathways are connected and players are guided to environments that fit their development and identity. Formal routes may help, but the principle is broader than one transition mechanism. A shared style can connect learning without becoming a universal selection test.")

# PDF page 4 / handbook pages 260-261: Belgian football DNA and player-centred development.
add(4, "application", "A poor international result triggers a national development review. Which features of the Belgian response are transferable?",
    ["Bring the relevant football stakeholders together.", "Audit the youth-development approach.", "Shift attention from youth results towards individual learning."],
    ["Select a national formation before reviewing how coaches develop young players.", "Use the senior ranking as the baseline measure for the development reform."],
    "Belgium used a crisis as a moment for collective diagnosis and a player-centred change in youth development. The playing identity and coach education then carried that direction through the system. The result prompted reform but was not itself the reform's performance measure.")
add(4, "explanation", "Which principles define the Belgian player-centred paradigm?",
    ["The individual player is the main actor.", "Youth learning takes priority over team results.", "Formats match players' developmental characteristics.", "Coach education spreads the shared approach."],
    ["The team remains the main performance unit once players enter organised small-sided competition."],
    "Belgium changed the youth mindset from winning to developing the individual within the team. Age-appropriate formats, a clear playing identity and coach education supported the shift. The player-centred principle continues across organised competition rather than ending when team play begins.")
add(4, "factual_anchor", "What playing identity did the Belgian FA adopt in the example?",
    ["Possession-based football in a 4-3-3, emphasising creativity, positioning and comfort on the ball."],
    ["Positioning-based football in a 4-3-3, emphasising control before creative risk.", "Possession football built around technical dominance in one-against-one situations.", "A common 4-3-3 structure with freedom for coaches to define the national playing style.", "A ball-centred curriculum that used possession as the main youth performance indicator."],
    "The Belgian identity used a 4-3-3 and sought control through effective possession and quality positioning, with creativity and ball comfort. The formation served a wider learning philosophy. It was not a narrow tactical or performance metric.")
add(4, "application", "Coaches are introducing football to five- and six-year-olds. Which practices follow Belgium's developmental logic?",
    ["Use one-against-one play with goalkeepers to maximise touches and scoring.", "Focus on the relationship between the child and the ball before demanding passing patterns."],
    ["Introduce three-against-three so the triangle becomes the first collective reference.", "Rotate children between duos after each goal to vary opponents and decisions.", "Use dribbling outcomes to identify children ready for the next playing format."],
    "At that age, Belgium matched the format to egocentric development through 'me and the ball'. Short one-against-one games created touches, dribbles and goals in a fun setting. Triangles and more collective concepts were introduced at the next stage rather than used as readiness tests.")
add(4, "explanation", "How does the Belgian progression adapt football to child development?",
    ["It begins with individual exploration of the ball.", "It introduces triangles through three- and five-a-side football.", "It expands playing range through eight-a-side before the adult game."],
    ["It increases team size when children demonstrate collective decision-making.", "It keeps each format until players have mastered its technical objectives."],
    "The pathway progresses by developmental stage from individual play to increasingly complex collective structures. Formats are adapted to player characteristics and age. Progression is not described as a mastery test controlled by competition outcomes.")
add(4, "application", "An association is creating a national football DNA. Which stakeholders should be involved according to the chapter?",
    ["The association's technical department and national-team staff.", "Professional and grassroots clubs.", "Coach educators and coaches at different levels.", "Regional bodies, schools and relevant public partners."],
    ["Limit final design authority to technical stakeholders so the national identity remains coherent."],
    "A national football DNA should connect the whole development ecosystem from grassroots to elite. Broad involvement builds a shared vision and makes implementation more credible. Technical leadership is essential, but coherence should not be achieved by excluding delivery stakeholders.")
add(4, "explanation", "What made Belgium's association proactive rather than reactive?",
    ["It defined its desired future and adjusted its pathway deliberately instead of copying or waiting for others."],
    ["It used regular monitoring to respond early to changes in world football.", "It converted a poor tournament into a long-term technical reform.", "It made the national playing identity the reference for stakeholder decisions.", "It reviewed its course against ambitions before external results required change."],
    "A proactive association chooses a direction, builds stakeholder ownership and shapes its own future. Monitoring and adjustment support that stance, but the defining feature is intentional authorship of the national plan. Reaction to one result was the starting opportunity, not the continuing mode.")

# PDF page 5 / handbook pages 262-263: Multimove, small-sided games and the Belgian process.
add(5, "factual_anchor", "Which two categories of movement skill are developed through Multimove?",
    ["Locomotion involving coordinated body movement.", "Object control involving skills such as catching, throwing, kicking and rolling."],
    ["Balance involving static and dynamic body control.", "Perception involving eye-hand and eye-foot coordination.", "Manipulation involving bat, ball and partner activities."],
    "Multimove groups its twelve skills into locomotion and object control. Coordination supports successful performance, but it is not a third category. The programme develops broad movement capability before narrow football specialisation.")
add(5, "application", "A preschool programme spends most of its time on dribbling and passing drills. Which changes reflect Multimove?",
    ["Add varied locomotor experiences.", "Add catching, throwing, hitting, kicking and rolling activities.", "Reduce premature concentration on football technique."],
    ["Use football-themed movement stations so object control remains relevant to later participation.", "Assess eye-hand and eye-foot coordination before choosing the movement mix."],
    "Multimove offers a broad, fun movement base for young children and avoids premature specialisation. Locomotion and diverse object-control tasks develop essential motor skills. Football themes can be used, but the programme should not narrow the movement purpose around later selection.")
add(5, "explanation", "Why did Belgium remove league tables for younger age groups?",
    ["It reduced coaches' focus on trophies.", "It encouraged development rather than short-term selection.", "It protected late developers from being displaced by stronger children.", "It supported age-appropriate small-sided learning."],
    ["It allowed coaches to evaluate progress through individual technical outcomes instead of team results."],
    "League tables can push coaches towards players who deliver immediate wins, especially physically advanced children. Removing them supports playing time, learning and individual development. The reform changes the purpose of competition rather than replacing results with another narrow measure.")
add(5, "factual_anchor", "At what stage does Belgium's example introduce the adult eleven-a-side format?",
    ["From around age 13, after progression through smaller formats."],
    ["At under-14 level, when league tables also begin.", "After four years of eight-a-side football in a double diamond.", "When players enter medium-range collective football.", "At the transition from regional youth competition to academies."],
    "The pathway moves from dribbling play to three-, five- and eight-a-side formats before eleven-a-side begins around age 13. Some milestones occur near the same age, but the format is defined by the developmental progression rather than league-table or academy status.")
add(5, "application", "A national association wants coach education to drive its playing identity. Which design is supported by Belgium's master-plan process?",
    ["Define the shared national vision first.", "Use coach education to spread the playing style and player-development approach."],
    ["Pilot the identity through national youth teams before changing grassroots courses.", "Begin with elite coach educators so the approach gains technical credibility.", "Tie course completion to coaches demonstrating the national formation in competition."],
    "Belgium established a common vision and then improved coach education to carry it across grassroots and elite settings. Youth teams and elite schools provided useful test platforms, but implementation was not postponed until those pilots succeeded. Education communicates principles rather than certifying formation compliance.")
add(5, "explanation", "How did the Belgian development chain connect vision with senior-team performance?",
    ["A shared vision informed better coach education.", "Better education improved coaches across levels.", "Better coaches improved youth-player and youth-team development."],
    ["National youth-team results validated the player-centred pathway before senior performance improved.", "Elite schools translated the vision into selection standards used by clubs."],
    "Figure 9.5 presents a chain from shared vision through education and coaching to youth development, youth teams and the senior side. It illustrates systemic influence rather than a single causal test. The pathway was built for development, not to use youth results as a gate before senior progress.")
add(5, "application", "A youth coach is selecting bigger players to win a league while late developers remain on the bench. Which responses fit the chapter?",
    ["Reduce incentives tied to youth standings.", "Prioritise playing time and individual development.", "Use age-appropriate small-sided formats.", "Evaluate coaching against learning rather than trophies."],
    ["Create separate competitive groups so physically mature players and late developers receive suitable challenge."],
    "Belgium's reform addresses the selection distortion caused by a winning-first environment. Smaller formats, no early tables and development-centred coaching give more children meaningful experience. Separating players by current maturity risks reinforcing the same bias.")

# PDF page 6 / handbook pages 264-265: England DNA and grassroots quality.
add(6, "application", "A national team programme has a playing style but inconsistent coaching and support. Which framework best addresses the gap?",
    ["Use the England DNA elements to align identity, play, player profile, coaching and support."],
    ["Translate the style into a four-corners player profile before redesigning coaching.", "Create a common training methodology and let support teams adapt to each squad.", "Define technical and tactical targets across national teams before adding heritage and identity.", "Use analysis and sports medicine to standardise player preparation across age groups."],
    "England DNA is a connected framework: who we are, how we play, the future player, how we coach and how we support. A playing style by itself leaves the learning and performance system incomplete. The elements should be aligned rather than introduced as a technical sequence.")
add(6, "explanation", "Which statements correctly distinguish elements of England's footballing DNA?",
    ["'Who we are' concerns identity, pride and heritage.", "'How we play' concerns playing style and philosophy."],
    ["'How we coach' defines the technical and tactical attributes of the future player.", "'How we support' sets the planning and review standards for training.", "'The future England player' describes the analysis and sports-science support profile."],
    "The first two elements establish national identity and playing philosophy. The future-player element uses the four corners, coaching concerns consistent session delivery and review, and support includes analysis, medicine, psychology and nutrition. The distinctions create complementary responsibilities.")
add(6, "factual_anchor", "Which dimensions form the four-corners profile of the future England player?",
    ["Technical and tactical abilities.", "Physical attributes.", "Psychological and social characteristics."],
    ["Decision-making under intensity.", "National identity and heritage."],
    "The four corners are technical, tactical, physical, and psychological/social, with the first and last expressed as paired aspects in the passage. Decision-making is a desired quality but not a separate corner. Identity belongs to the wider 'who we are' element.")
add(6, "application", "An association wants consistent national-team coaching without making sessions rigid. Which practices fit England DNA?",
    ["Use a shared coaching approach across teams.", "Plan sessions against player needs and the playing philosophy.", "Review delivery and learning.", "Coordinate coaching with performance-support disciplines."],
    ["Prescribe common exercises so technical development remains comparable across age groups."],
    "Consistency concerns planning, delivery, review and alignment with the philosophy, not identical exercises. Support functions strengthen performance around the player. Coaches still need to adapt practice to age, stage and individual need.")
add(6, "explanation", "What is the defining feature of grassroots football in the chapter?",
    ["It is non-professional, non-elite football driven primarily by participation and love of the game."],
    ["It is organised football below the performance pathway and includes school, amateur and disability formats.", "It is community football designed to create lifelong participation and social value.", "It is the broad base from which regional youth and academy players emerge.", "It includes age- and ability-based formats that remain outside licensed competition."],
    "Grassroots is defined by its non-elite nature and its participation motive. It includes many formats and populations, from children and schools to veterans and disability football. Its pathway value and social effects are important but do not replace the definition.")
add(6, "application", "Registered-player numbers are rising, but many participants report unsafe or poor-quality experiences. Which priorities follow UEFA's grassroots vision?",
    ["Improve the safety and quality control of the environment.", "Treat retention and participant experience alongside growth."],
    ["Pause recruitment campaigns until existing clubs meet the Grassroots Charter standard.", "Direct education funding to the coaches in programmes with the highest dropout rates.", "Use fair-play compliance as the threshold for continued growth investment."],
    "UEFA's vision combines access for everybody, everywhere with a safe, quality-controlled environment. Growth without quality may fail to retain players or deliver the game's benefits. Standards and education should improve the system without turning growth into a sequential reward.")
add(6, "explanation", "Why should grassroots policy preserve local and regional football identities?",
    ["Grassroots is the mass foundation of the game.", "Local societies shape how football is experienced.", "Development should adapt the product to future community needs."],
    ["A national playing identity should influence elite pathways while grassroots retains local variation.", "Preserving identity protects participation from excessive standardisation by UEFA criteria."],
    "Football is played in diverse communities, and its strength comes from that broad social base. National associations should refine and adapt the game while respecting local, regional and national identity. This is not a formal separation between national elite philosophy and grassroots practice.")

# PDF page 7 / handbook pages 266-267: Grassroots Charter and Football in Schools evidence.
add(7, "application", "A national association wants to improve its UEFA Grassroots Charter level. Which areas should its plan address?",
    ["Growth in registered participation.", "Retention and lifelong involvement.", "Education across the grassroots game.", "Fair play as a cross-cutting quality principle."],
    ["Competition terms as the measure connecting participation, education and retention."],
    "The Charter criteria include growth, retention, education, terms and fair play, with fair play influencing the other dimensions. The system recognises both numbers and quality. Competition conditions can contribute but are not the cross-cutting principle described.")
add(7, "explanation", "Why does the Grassroots Charter place special emphasis on retaining teenagers?",
    ["Teenagers who stay in the game can become tomorrow's adult players and volunteers, supporting lifelong football."],
    ["Teenage retention protects the transition from school football into registered club programmes.", "It preserves the age group most likely to enter regional youth competition and coaching.", "It improves registered-player data used for Charter assessment and HatTrick funding.", "It creates a pool for the UEFA C diploma and Grassroots Leader pathway."],
    "Retention supports a healthy lifelong game and the future volunteer workforce, not merely player statistics. Teenagers who remain connected can contribute in many later roles. Funding and education may support retention, but they are not its core rationale here.")
add(7, "factual_anchor", "Which features are connected with UEFA Grassroots Charter recognition?",
    ["Gold, silver and bronze levels.", "Registered-player information as a prerequisite."],
    ["A national playing philosophy linked to school programmes.", "UEFA C-qualified coaches in each nationwide project.", "Fair-play indicators reported separately from the other criteria."],
    "The Charter uses three recognition levels and requires player data. Nationwide school or education programmes are also needed at higher levels, while fair play influences the whole model. The chapter does not make a national style or coach qualification the stated prerequisite.")
add(7, "application", "An association wants government support for Football in Schools. Which evidence should it use?",
    ["Schools provide crucial access to physical activity.", "Football can support pupil development and community goals.", "Inactivity creates substantial health and economic costs."],
    ["Registered school participants can strengthen the association's Grassroots Charter assessment.", "Football provides a specialist alternative where physical education teachers feel unprepared."],
    "The evidence base connects school access, youth and community benefits, and the social cost of inactivity. It is intended to help associations build partnerships with government and education authorities. The programme should support high-quality education rather than position football as a substitute for teachers.")
add(7, "explanation", "Which conclusions are supported by the physical-activity evidence presented?",
    ["A large share of EU citizens are inactive.", "Activity declines as children age.", "Girls are less active than boys.", "School physical education is a crucial source of activity for many children."],
    ["The evidence shows that football should be the principal extracurricular response to inactivity."],
    "The evidence describes a serious participation and health problem and the central reach of schools. UEFA Football in Schools can help within that context. The data support intervention, but they do not establish football as the single or principal policy response.")
add(7, "application", "A Football in Schools proposal focuses on talent identification. What is the strongest redesign?",
    ["Reframe it around broad access, pupil development and community benefit."],
    ["Add a participation strand before selecting pupils for local club pathways.", "Use teachers and parents to identify children whose interest can be sustained outside school.", "Measure educational and social outcomes alongside the talent pathway.", "Connect talent identification with the association's elite youth development programme."],
    "Football in Schools is a grassroots, educational and social initiative, not primarily a selection mechanism. It can introduce children to football and support multiple pupil and community goals. Club links may follow, but talent identification should not organise the programme.")

# PDF page 8 / handbook pages 268-269: school environments and child-centred grassroots coaching.
add(8, "application", "Physical education is underfunded and often taught by non-specialists. Which football-association responses are appropriate?",
    ["Partner with schools to expand high-quality opportunities.", "Support teachers and coaches with age-appropriate resources."],
    ["Deliver extracurricular football through association staff until teachers gain specialist confidence.", "Prioritise schools where physical education is the main source of activity for most pupils.", "Use club coaches to provide the technical content while teachers manage inclusion and welfare."],
    "Football can help schools address limited provision, but quality depends on partnership and capable adults. Resources and education should strengthen the environment rather than replace teachers with a parallel football system. Need and reach inform prioritisation without narrowing responsibility.")
add(8, "explanation", "Which types of benefit can high-quality school football generate?",
    ["Psychosocial and personal development.", "Physical fitness and motor development.", "Community cohesion and social inclusion."],
    ["Earlier transition into structured club participation.", "Improved competitive behaviour through team goal-setting."],
    "The evidence covers psychosocial, physical and community benefits, including learning, leadership, health and inclusion. Club participation and competition may occur, but they are not the benefit categories identified. Quality of experience is what enables the broader outcomes.")
add(8, "factual_anchor", "Which principles appear in the iCoachKids pledge?",
    ["Be child-centred.", "Make sport fun and safe.", "Engage parents positively.", "Use competition developmentally."],
    ["Introduce sport-specific learning before performance targets."],
    "The ten rules include child-centred, holistic and inclusive practice, fun and safety, love of sport, foundational skills, parents, progression, varied methods and developmental competition. The pledge prioritises love for sport above learning the sport, reversing the distractor's sequence.")
add(8, "application", "A school football programme rewards the strongest teams and gives less playing time to beginners. What climate should replace this approach?",
    ["A mastery climate focused on effort, personal improvement and individual needs."],
    ["A participation climate that rewards attendance and cooperative behaviour.", "A child-centred climate that groups pupils by stage before competition.", "An inclusive climate that uses mixed ability until foundational skills develop.", "A learning climate that assesses progress through age-appropriate football tasks."],
    "High-quality school football needs a safe, caring and inclusive mastery climate. Effort and personal improvement should shape motivation, with activities appropriate to age and need. Grouping or assessment can support learning but does not define the climate.")
add(8, "explanation", "Why are grassroots coaches central to both participation and social development?",
    ["They shape first experiences that influence continued involvement.", "They support players as people as well as performers."],
    ["They connect school access with club retention pathways.", "They deliver the social objectives attached to association grassroots funding.", "They provide the specialist technical knowledge missing from children's physical education."],
    "Coaches affect enjoyment, learning, belonging, health and the likelihood that young people stay active. Their role includes teams and communities, not just technique. Pathways and policy may support that work, but the central mechanism is the quality of daily coaching.")
add(8, "application", "A generic coach course prepares adults for senior amateur teams and children's teams together. Which changes follow the chapter?",
    ["Create content specific to coaching children.", "Train coaches to adapt to age, ability and playing format.", "Develop grassroots specialists."],
    ["Keep a common qualification and add supervised practice in children's settings.", "Use the UEFA C syllabus for novice coaches and the generic course for experienced coaches."],
    "Many coaches work with children, yet few programmes are designed for that sector. Education should address child development, diverse participants and the grassroots environment. Supervised practice helps, but it cannot compensate for content built around a different coaching role.")
add(8, "explanation", "What philosophy unites the iCoachKids rules?",
    ["Children's sport should be fun and safe.", "Development should be holistic and inclusive.", "Learning and competition should suit age and stage.", "Love of sport and broad participation should be protected."],
    ["Foundational skills should be secured before children choose a performance pathway."],
    "The pledge creates positive, child-centred experiences through safety, inclusion, progression and suitable challenge. It values foundational skills but does not turn them into a gate for pathway choice. The child's long-term relationship with sport remains central.")

# PDF page 9 / handbook pages 270-271: grassroots qualification and European Coaching Framework.
add(9, "application", "A national association wants to strengthen its grassroots coach pathway at scale. Which first intervention is best supported?",
    ["Combine the UEFA C diploma with accessible child-centred learning resources adapted to football."],
    ["Use the UEFA C diploma as the qualification and reserve online courses for volunteer coaches.", "Make the iCoachKids course a prerequisite before candidates enter the UEFA coaching pyramid.", "Replace local grassroots courses with UEFA's free online programme during the transition.", "Focus UEFA C delivery on coaches working in registered youth competitions."],
    "The UEFA C diploma provides the formal foundation, while adapted iCoachKids courses supplement it and broaden access. They serve complementary functions in the grassroots pathway. Neither resource is limited to a secondary category of coach or used to replace national delivery.")
add(9, "explanation", "What is the role of the UEFA C diploma in the coaching pathway?",
    ["It focuses on the grassroots coach profile.", "It forms the mandatory first step and foundation for Convention signatories."],
    ["It certifies coaches for children's football before they progress to amateur teams.", "It connects the Grassroots Leader course with the UEFA B diploma.", "It provides the common qualification for participation-pathway coaches across age groups."],
    "UEFA C addresses the specific grassroots environment and sits at the base of the coaching pyramid. National associations signed to the Convention must provide it. It is a foundation, not a statement that every grassroots role is identical or confined to children.")
add(9, "factual_anchor", "Which qualifications are shown below the UEFA A diploma in the coaching pyramid?",
    ["UEFA B diploma.", "UEFA Youth B diploma.", "UEFA C diploma."],
    ["UEFA Elite Youth B diploma.", "UEFA Grassroots diploma."],
    "The pyramid places UEFA B and its youth, goalkeeper and futsal specialist versions above UEFA C. Elite Youth is an A-level specialist diploma, while grassroots is the profile served by UEFA C rather than a separately named diploma.")
add(9, "application", "A federation is auditing its coach-education system against the ESCF. Which dimensions should it examine?",
    ["Whether the system is athlete-centred.", "How coaching practice is defined.", "How expertise and development pathways are supported.", "How certification and recognition operate."],
    ["Whether the same competence language is used at each qualification level."],
    "The ESCF has five drivers: athlete-centred vision, practice, expertise, development, and certification and recognition. A shared language supports comparison, but competence demands should vary by role and level. The audit should examine the whole system rather than wording consistency alone.")
add(9, "explanation", "What problem is the European Sport Coaching Framework designed to solve?",
    ["It provides shared principles, reference points and terminology to improve coach learning, mobility, employability and system quality across Europe."],
    ["It aligns national qualifications so coaches can move between sports and countries.", "It sets European minimum standards before sport-specific bodies design certificates.", "It converts the international framework into a common coach curriculum for the EU.", "It gives governing bodies a research-based model for recognising coaching as a profession."],
    "The ESCF is a shared framework, not a single curriculum or licence. It helps systems analyse and improve learning, mobility, employability and quality while applying principles in specific contexts. Sport governing bodies retain responsibility for role-specific standards.")
add(9, "application", "A national coaching framework covers practice and qualifications but lacks a coherent development pathway. Which ESCF drivers should be strengthened?",
    ["Coaching expertise, to define progression towards increasingly effective performance.", "Coach development, to connect learning opportunities across a long-term pathway."],
    ["Athlete-centred vision, because progression should begin with participant needs.", "Certification and recognition, because pathway stages need formal status.", "Coaching practice, because functions provide the competence sequence."],
    "Expertise describes levels and aspirations, while coach development concerns how people learn and progress. Certification can recognise stages, but it does not create the learning pathway. The ESCF drivers should be connected without confusing recognition with development.")

# PDF page 10 / handbook pages 272-273: athlete-centred vision and participation trajectories.
add(10, "application", "An elite coach values results but gives little attention to athlete welfare. Which athlete-centred corrections are supported?",
    ["Clarify values and beliefs around doing well for athletes.", "Match coaching to participant needs and stage.", "Optimise well-being alongside performance."],
    ["Use athlete feedback to decide which performance demands can be adjusted.", "Prioritise welfare during sampling and specialising before performance investment begins."],
    "Athlete-centred coaching joins performance with well-being and a genuine desire to serve participants. Values, philosophy and capability must fit the athlete's changing stage. Welfare is not a concession negotiated against performance or limited to early phases.")
add(10, "explanation", "How do the two engagement trajectories and their phases relate?",
    ["Participation includes children, adolescents and adults.", "Performance progresses through emerging, performance and high-performance athletes.", "The trajectories coexist within the wider sports-participation map.", "Coach education should match the needs of each cohort."],
    ["Athletes move from participation to performance after the specialising phase."],
    "The map contains parallel participation and performance trajectories with three cohorts in each. Sampling, specialising and investment describe the performance journey, while participation can continue across life. Movement is possible, but the model does not prescribe one crossover point.")
add(10, "factual_anchor", "What defines the investment phase in the developmental model of sports participation?",
    ["The athlete commits to pursuing high performance in a specific sport."],
    ["The athlete selects one preferred sport while retaining complementary activities.", "The athlete enters a performance environment with specialist coaching.", "The athlete increases training time and competitive exposure in the chosen sport.", "The athlete joins the high-performance cohort after mastering foundational skills."],
    "The investment phase is defined by commitment to high performance in one sport. Increased training, specialist coaching and competition may follow, but they are not the defining wording. Earlier sampling and specialising prepare the trajectory without setting a mastery threshold.")
add(10, "application", "A national association is matching diplomas to coaching roles. Which pairings follow the chapter?",
    ["UEFA C for the grassroots game.", "UEFA Pro for the professional game."],
    ["UEFA B for the top amateur senior game.", "UEFA A for elite youth and academy football.", "UEFA Youth B for emerging athletes in national development programmes."],
    "The pathway maps UEFA C to grassroots and UEFA Pro to the professional game. UEFA A sits just below professional football for the top amateur senior game, with Elite Youth A serving elite youth. Specialist diplomas add role focus without replacing the core mapping.")
add(10, "explanation", "Why does each diploma level need a specific coach profile?",
    ["Different participant cohorts have different needs.", "Coaching functions become more demanding with role and expertise.", "Competence standards should fit the environment."],
    ["A profile lets qualifications recognise prior experience before course entry.", "A profile ensures coaches remain within the trajectory covered by their licence."],
    "Profiles connect the participant cohort, coaching role and required competence. This makes education relevant from grassroots to elite football. A licence recognises preparedness for a role but does not confine a coach permanently to one trajectory.")
add(10, "application", "A course for emerging-athlete coaches copies the professional-game curriculum at lower intensity. Which changes are appropriate?",
    ["Start from the cohort's developmental needs.", "Define the relevant coaching functions.", "Set competence demands for the role.", "Choose learning activities suited to that context."],
    ["Retain professional tactical content so coaches understand the destination of the pathway."],
    "Coach education should be athlete-centred and role-specific rather than a diluted version of the highest licence. Functions and competencies must match emerging athletes and the development environment. Understanding the destination can help, but it should not organise the curriculum.")
add(10, "factual_anchor", "Which UEFA diploma is positioned for the top amateur senior game just below professional football?",
    ["UEFA A."],
    ["UEFA Elite Youth A.", "UEFA B.", "UEFA Youth B.", "UEFA Pro."],
    "Figure 9.13 places UEFA A at the top amateur senior level below the professional game. Elite Youth A is the specialist route for elite youth, while UEFA Pro serves professional football. The distinction links the qualification to the coaching role.")

# PDF page 11 / handbook pages 274-275: primary coaching functions and competence.
add(11, "application", "A coach has a clear strategy but weak athlete relationships and an unstable programme environment. Which functions need immediate attention?",
    ["Shape the environment so the programme conditions support athlete objectives.", "Build relationships that reconnect athletes, staff and the wider programme."],
    ["Read and react, because instability requires situational decision-making.", "Reflect and learn, because the strategy should be reviewed before implementation continues.", "Organise practice and competition, because shared activity can repair trust."],
    "The six functions are interdependent, and this scenario points directly to environment and relationships. Reading events and reflection support improvement, but they do not replace the foundational relational and programme work. The coach should act while keeping the whole cycle connected.")
add(11, "explanation", "Why are the six primary coaching functions described as cyclical and interdependent?",
    ["Action in one function affects the others.", "Coaches move through planning, implementation, review and adjustment.", "Continuous learning improves the programme over time."],
    ["The cycle returns to vision-setting after each competition phase.", "Interdependence allows coaches to compensate for weaker functions through experience."],
    "Vision, environment, relationships, practice, response and reflection form a connected process. Coaches repeatedly plan, act, observe and adjust rather than complete the functions once. Experience helps development but cannot make one function optional.")
add(11, "factual_anchor", "Which activities are primary functions of a coach in the ESCF?",
    ["Set vision and strategy.", "Build relationships.", "Read and react to events.", "Reflect and learn."],
    ["Certify athlete readiness for competition."],
    "The six functions also include shaping the environment and conducting practice and competition. Certification of athlete readiness is not listed as a separate function. The framework defines the daily work from vision through continual reflection.")
add(11, "application", "Unexpected off-field events affect a squad during a tournament. Which coaching function is central?",
    ["Read the situation and respond through effective decision-making."],
    ["Shape the environment so the event has less influence on athlete objectives.", "Build relationships with the external people involved in the programme.", "Review the event after competition and update the programme strategy.", "Adjust practice and competition plans to protect the targeted learning outcomes."],
    "Reading and reacting explicitly covers on-field and off-field events and requires sound decisions in the moment. Other functions may support prevention and follow-up. The central demand in the scenario is an appropriate live response.")
add(11, "explanation", "How does a competence-based approach use the six coaching functions?",
    ["The functions define the work coaches must perform.", "Task-related competences then become the basis for course content and minimum standards."],
    ["Competences are assessed through the function most relevant to each diploma level.", "Functions provide a common syllabus while competence standards distinguish coaching roles.", "Course content begins with the functions athletes need at their engagement stage."],
    "The functions describe the job, and corresponding competencies describe what capable performance requires. UEFA can then set minimum standards appropriate to each level. The same functional framework supports different roles without imposing one syllabus or one assessment per function.")
add(11, "application", "A coach plans excellent sessions but athletes feel detached from the programme goals. Which integrated response follows the framework?",
    ["Co-create a clearer vision with the athletes.", "Strengthen positive relationships.", "Connect practice design to individual and team objectives."],
    ["Use reflection sessions so athletes understand how activities contribute to improvement.", "Make competition targets the shared reference until programme trust improves."],
    "Vision should be created in partnership with athletes and translated through relationships and practice. Reflection may support understanding, but the disconnection requires more than explanation after sessions. Competition targets should not replace shared developmental purpose.")

# PDF page 12 / handbook pages 276-277: expertise, knowledge, LTCD and certification.
add(12, "application", "A coach-development programme focuses on tactics and session design. Which additions are needed for integrated expertise?",
    ["Subject and teaching knowledge.", "Relationship-building knowledge.", "Self-awareness and personal philosophy.", "Reflection that connects knowledge with practice."],
    ["A formal expertise assessment before coaches choose their development pathway."],
    "Effective coaches integrate professional, interpersonal and intrapersonal knowledge. Reflection helps them apply and develop those forms of knowledge in real work. An expertise assessment may guide planning, but it is not a substitute for this integrated content.")
add(12, "explanation", "What is the value of the novice-expert continuum?",
    ["It helps coaches locate their current development and see a possible progression towards expertise."],
    ["It determines which qualification level a coach should enter based on demonstrated proficiency.", "It separates underperforming coaches from beginners who need foundational education.", "It gives systems a common scale for comparing expertise across coaching roles.", "It identifies when practising proficiency is sufficient for independent coaching."],
    "The continuum is a developmental reference from beginner through competence and proficiency to expert performance. It supports individual aspiration and system pathway design. It is not presented as a licensing threshold or a cross-role ranking instrument.")
add(12, "factual_anchor", "Which pairings correctly describe coaching knowledge types?",
    ["Professional knowledge - subject matter and how to teach it.", "Interpersonal knowledge - connecting with people and building relationships."],
    ["Intrapersonal knowledge - evaluating programme effectiveness through reflection.", "Professional knowledge - applying the six coaching functions in practice.", "Interpersonal knowledge - understanding athlete-centred values and beliefs."],
    "Professional knowledge concerns the sport and pedagogy, interpersonal knowledge concerns relationships, and intrapersonal knowledge concerns self, philosophy, experience and reflection. The types overlap in practice but retain distinct centres. Programme evaluation and functions are broader coaching activities.")
add(12, "application", "An experienced player begins coaching and is placed directly on an advanced course. Which LTCD principles should guide a better decision?",
    ["Assess the person's coaching stage and experience.", "Understand how the person learns.", "Consider the participants and role they will coach."],
    ["Credit playing expertise within professional knowledge and focus the course on relationships.", "Use the novice-expert continuum to place the candidate at cultivating competence."],
    "Playing experience does not determine coaching expertise. Long-term coach development is tailored to stage, learning needs and participant context. The continuum can support reflection, but placement requires a fuller profile rather than a preset label.")
add(12, "explanation", "Which principles justify a structured system of coach certification?",
    ["It protects minimum workforce quality.", "It benefits athletes and participants.", "It recognises coaches as qualified professionals.", "It aligns competence demands with coaching roles and expertise."],
    ["It ensures licence holders have comparable competence across sports and national systems."],
    "Certification and licensing establish acceptable competence and raise recognition of coaching. Levels should match real roles, functions and expertise demands. Shared minimums improve quality without claiming that competence is interchangeable across sports and contexts.")
add(12, "application", "A federation has one certificate for grassroots assistants and senior head coaches. What is the primary redesign?",
    ["Create role- and expertise-aligned levels with progressively demanding functions and competences."],
    ["Keep one certificate and add specialist endorsements for grassroots and senior football.", "Use continuing education hours to distinguish assistants, coaches and head coaches.", "Map the certificate to UEFA B and require experience for higher responsibilities.", "Separate professional and amateur certificates before defining the coaching roles."],
    "The chapter links assistant, coach, advanced and master roles with increasing expertise and demands. UEFA likewise uses C, B, A and Pro levels with defined profiles. The redesign should begin with roles and competence, not administrative endorsements or sector labels.")

# PDF page 13 / handbook pages 278-279: Jira Panel, Coaching Convention and learning design.
add(13, "application", "A federation wants to understand why capable coaches are leaving the profession. Which use of the Jira Panel best fits the chapter?",
    ["Examine demands, constraints and support across coaches' personal, professional and contextual circumstances.", "Use the findings to shape a pathway that reflects coaches' real working lives."],
    ["Compare coaches' technical knowledge with the competences prescribed for their licence level.", "Audit whether courses reproduce the six primary coaching functions in equal proportions.", "Classify departures by the participation or performance trajectory of the athletes coached."],
    "The Jira Panel is a holistic way of viewing a coach's life, including personal, professional and contextual influences. It helps a system understand development and retention in the realities coaches face. It is broader than a technical audit, course-content check or athlete-pathway classification.")
add(13, "explanation", "What are important benefits of the UEFA Coaching Convention?",
    ["It establishes minimum standards for coach education and qualifications.", "It supports mutual recognition and greater freedom for qualified coaches to work.", "It strengthens the status and credibility of the coaching profession."],
    ["It standardises national course delivery so licence holders receive comparable learning activities.", "It transfers responsibility for advanced coach assessment from associations to UEFA."],
    "The Convention raises and harmonises minimum quality, supports recognition of qualifications and promotes coaching as a profession. Associations retain responsibility for delivering their programmes within the framework. Comparable standards do not require identical learning activities or central UEFA assessment.")
add(13, "application", "A UEFA A course is dominated by lectures delivered away from clubs. Which redesign follows the chapter's reality-based approach?",
    ["Connect learning tasks to the coaches' actual teams and roles.", "Use practical experience as material for reflection and conceptualisation.", "Let coaches test new approaches in their own environments.", "Ask coach educators to facilitate learning rather than merely transmit information."],
    ["Assess each learning cycle through a match-based demonstration before returning to theory."],
    "Reality-based education begins with what coaches do in their own contexts and cycles between experience, reflection, concepts and experimentation. Coach educators facilitate that process. A match demonstration can be useful, but prescribing it as the assessment for every cycle is not the model described.")
add(13, "factual_anchor", "Which sequence best represents Kolb's experiential learning cycle as presented in the chapter?",
    ["Concrete experience, reflective observation, abstract conceptualisation, active experimentation."],
    ["Concrete experience, active experimentation, reflective observation, abstract conceptualisation.", "Reflective observation, concrete experience, active experimentation, abstract conceptualisation.", "Abstract conceptualisation, reflective observation, concrete experience, active experimentation.", "Active experimentation, abstract conceptualisation, concrete experience, reflective observation."],
    "Kolb's cycle moves from concrete experience to reflection, then to conceptual understanding and active experimentation. The experimentation creates further experience and restarts the cycle. The order matters because reflection and concepts mediate between experience and the next trial.")
add(13, "explanation", "What makes coach education learner-centric in the chapter?",
    ["It starts from the coach's needs, experience and working context.", "It makes the coach an active participant in constructing and applying learning."],
    ["It permits each coach to define the competence standards against which progress is assessed.", "It organises content around problems nominated by the course group rather than licence profiles.", "It gives individual practice greater weight than collaborative learning with peers."],
    "Learner-centric education recognises coaches as adults with experience, needs and real contexts. They actively reflect, collaborate, solve problems and apply ideas rather than receive content passively. Standards and role profiles still frame the programme, and peer learning can be an important part of it.")
add(13, "application", "A federation is selecting and developing coach educators. Which qualities deserve particular attention?",
    ["Credibility grounded in coaching and coach-development experience.", "Skill in facilitating reflection, interaction and applied learning.", "Capacity to model the learner-centred methods expected on courses."],
    ["Recent competitive success at the licence level taught.", "Expertise in delivering a consistent presentation of the national curriculum."],
    "Coach educators need relevant expertise and the ability to create effective adult learning, not merely subject knowledge or presentation consistency. Their behaviour should model facilitation, reflection and connection to practice. Competitive status can add credibility but is not the defining qualification.")
add(13, "explanation", "Why should qualified coaches and coach educators continue learning after certification?",
    ["Football and the demands of coaching continue to evolve.", "Competence develops through experience, reflection and renewed experimentation.", "Different roles and contexts create new learning needs.", "Continued development helps qualifications translate into sustained practice quality."],
    ["Licence recognition depends on completing equivalent learning cycles in each national system."],
    "Certification marks a competence threshold, not the end of development. Coaches and educators work in changing environments and improve by repeatedly connecting experience with reflection and new action. Ongoing learning helps formal standards remain meaningful in practice.")

# PDF page 14 / handbook pages 280-281: UEFA support and individual player pathways.
add(14, "application", "A national association has a sound coach-education strategy but lacks expertise to implement it. Which UEFA support is most directly relevant?",
    ["Use HatTrick funding, technical-development services and UEFA's coach-education networks to build delivery capacity."],
    ["Ask UEFA Share to certify the association's tutors before national courses begin.", "Use UEFA development tournaments as the principal training environment for coach educators.", "Adopt course material from a more established association through the Coaching Convention.", "Request UEFA instructors to assume responsibility for delivering the national licence pathway."],
    "UEFA facilitates development through HatTrick, expert support, conferences, instructors, reports and knowledge exchange. These mechanisms help associations strengthen their own systems. They do not transfer national responsibility to UEFA or make another association's curriculum a required template.")
add(14, "explanation", "What is the main value of UEFA Share to football development?",
    ["It enables national associations to exchange expertise and practical experience.", "It helps useful solutions travel between associations while remaining adaptable to local context."],
    ["It provides a common repository from which associations select approved national curricula.", "It coordinates joint delivery of programmes when associations lack specialist staff.", "It compares national projects against common performance indicators funded through HatTrick."],
    "UEFA Share is a knowledge-exchange platform: associations learn from one another's experience and expertise. Good ideas can inform local solutions without being copied mechanically. It is not described as a curriculum approval, shared delivery or performance-ranking system.")
add(14, "factual_anchor", "Which responsibilities belong to national associations and clubs in player development?",
    ["The association defines the national vision and player-development framework.", "Clubs provide the daily development environment.", "The two levels collaborate so individual pathways connect with the national direction."],
    ["The association assigns players to the club environment most suited to their maturation stage.", "Clubs determine how the national curriculum is adapted for each regional talent pool."],
    "The association gives strategic direction through a national curriculum or framework, while clubs do most day-to-day development. Collaboration connects the system and supports individual players. The chapter does not assign the association placement control or clubs regional curriculum authority.")
add(14, "application", "An association and its clubs are building an elite-player plan. Which features create the strongest pathway?",
    ["Agree a clear national playing and development philosophy.", "Define complementary association and club responsibilities.", "Track individual needs rather than treating age groups as homogeneous.", "Create communication and transition points across club and national-team environments."],
    ["Use national-team selection as the common benchmark for judging club development quality."],
    "The chapter stresses an aligned vision, collaboration and individualised pathways. Players move through club and association environments, so communication and clear responsibilities matter. Selection is one event in development and is too narrow to serve as the common quality benchmark.")
add(14, "explanation", "Why must elite-player development be individualised?",
    ["Players differ in biological maturation, experience, needs and development rate."],
    ["Individual planning allows coaches to preserve a common curriculum while varying the competition level.", "It prevents position-specific development from narrowing the national playing philosophy.", "It aligns player objectives with the stage of the national-team pathway they have reached.", "It gives clubs a consistent basis for comparing players who enter the pathway at different ages."],
    "Chronological age does not capture the considerable differences between developing players. Individual plans should respond to biological, psychological, technical and contextual needs. The purpose is development fit, not simply curriculum variation, pathway alignment or comparison.")
add(14, "factual_anchor", "Which two forms of maturation are specifically distinguished in the chapter's player-development discussion?",
    ["Chronological maturation reflected by calendar age.", "Biological maturation reflected by physical development."],
    ["Psychological maturation reflected by decision-making independence.", "Technical maturation reflected by skill stability under pressure.", "Social maturation reflected by adaptation to senior-team relationships."],
    "The chapter contrasts chronological age with biological maturation to explain why same-age players may differ substantially in size and development. Psychological and social development remain important, but they are not the named two-part distinction here. Technical proficiency is a performance characteristic rather than a form of maturation.")
add(14, "application", "A selection group favours physically advanced twelve-year-olds. Which actions protect the development of later-maturing players?",
    ["Assess biological maturity alongside current performance.", "Offer meaningful development opportunities to a broad pool.", "Review selections over time rather than treating early advantage as stable potential."],
    ["Group players by maturity status through the full age phase to reduce physical mismatches.", "Use technical testing to separate maturation effects from underlying football potential."],
    "Physical advantage can distort current performance and hide longer-term potential. Maturity-aware assessment, repeated review and broad opportunity reduce premature loss. Permanent grouping and a single technical test oversimplify a dynamic, multidimensional process.")

# PDF page 15 / handbook pages 282-283: relative age effect and talent-development principles.
add(15, "application", "A youth national team contains many players born early in the selection year. Which response best addresses the relative age effect?",
    ["Audit birth-date distributions across age groups and selection stages.", "Train scouts to distinguish current performance from future potential.", "Maintain access for later-born and later-maturing players.", "Reassess players repeatedly as maturation advantages change."],
    ["Balance each intake by birth quarter so the pathway represents the eligible population."],
    "The relative age effect calls for awareness, broader opportunity and repeated assessment, because temporary advantages can influence selection. A forced quarterly quota may change representation but does not itself improve evaluation of potential. The chapter favours delaying definitive judgements and offering the best environment to many players.")
add(15, "explanation", "Why is current youth performance an unreliable substitute for long-term potential?",
    ["Current performance is influenced by temporary advantages such as relative age and biological maturity."],
    ["Performance measures the player's present role, whereas potential predicts suitability for senior positions.", "Potential depends mainly on the rate at which a player responds to elite training.", "Performance becomes informative after physical development has been standardised within an age group.", "Potential can be assessed more reliably through longitudinal technical benchmarks than match observation."],
    "Youth performance reflects the player and the present environment, including age and maturation advantages. Those advantages can fade, while less prominent players may develop further. Potential therefore requires patient, multidimensional and repeated judgement rather than a different single metric.")
add(15, "factual_anchor", "Which figures illustrate the relative age effect in the European youth data cited?",
    ["About 47% of selected players were born in the first quarter.", "About 6% were born in the fourth quarter."],
    ["Around 57% were born between January and March.", "Around 3% of selected players were born in December across the analysed age groups.", "First-quarter selection was approximately four times fourth-quarter selection."],
    "The chart reports 47% in quarter one and 6% in quarter four. It also gives month examples of 57 January-born players and 3 December-born players, not percentages. The two quarter figures represent a much larger than fourfold difference.")
add(15, "application", "A federation loses many previously selected players before senior level. Which strategy follows the chapter?",
    ["Delay definitive talent decisions where possible.", "Provide strong learning environments to more players for longer.", "Use theory, system design and the learning environment together to support development."],
    ["Concentrate specialist resources on players whose potential remains stable across consecutive selections.", "Move deselected players to participation pathways so elite environments can preserve progression intensity."],
    "Many youth selections do not translate to senior careers, so the system should avoid early final judgements. Wider, longer access and coherent development environments give potential time to emerge. Stable selection history is still influenced by the system, and movement out of a squad need not end a performance pathway.")
add(15, "explanation", "What makes talent identification and development a complex system rather than a single selection exercise?",
    ["Potential emerges through interaction between the player and the environment.", "Development is nonlinear and differs between individuals.", "Selection decisions can themselves change access to learning opportunities.", "Theory, pathway structures and coaching environments must work together."],
    ["Reliable identification requires a common model of senior performance before pathway design begins."],
    "Talent is not a fixed quality revealed at one trial. It develops through changing player characteristics, opportunities, coaching and system decisions. A senior-performance model can guide a pathway, but it does not remove uncertainty or make identification a sequential technical exercise.")

# PDF page 16 / handbook pages 284-285: good practice, futsal and UEFA's elite scheme.
add(16, "application", "A federation has a talent pathway on paper, but club environments vary widely in quality. What is the strongest system-level priority?",
    ["Translate the pathway principles into consistently high-quality daily learning environments."],
    ["Centralise the most influential age groups so the national association can control the curriculum.", "Accredit clubs according to the number of players progressing to national teams.", "Use national development camps to compensate for variation in club practice.", "Specify a common weekly training structure for each stage of the pathway."],
    "The player experiences development primarily through the daily environment, so pathway theory must become quality practice in clubs. Centralisation, output-based accreditation, camps and prescribed schedules may affect provision but do not directly ensure an effective learning climate. Good systems align principles, support and local delivery.")
add(16, "explanation", "Why can futsal contribute to football-player development?",
    ["Frequent involvement with the ball and tight spaces demand rapid perception, technique and decisions.", "Transitions and repeated attacking-defending situations expose players to transferable game problems."],
    ["Its smaller teams let coaches isolate technical development while retaining competitive pressure.", "Its indoor setting allows the football curriculum to continue when outdoor competition is unavailable.", "Its laws create a more predictable tactical environment for learning positional play."],
    "Futsal creates dense, realistic interactions: players receive, decide and transition frequently under pressure. Those experiences can transfer to football. Indoor access is practically useful, but the developmental argument is broader than continuity, isolation or tactical predictability.")
add(16, "factual_anchor", "Which characteristics of futsal are highlighted in the chapter?",
    ["It is played five against five.", "It uses a smaller, low-bounce ball.", "It produces frequent transitions between attack and defence."],
    ["It restricts ball contact to encourage decisions before possession.", "It uses rolling substitutions primarily to sustain technical intensity."],
    "The chapter highlights the five-a-side format, smaller low-bounce ball, tight area, frequent touches, quick decisions and repeated transitions. Contact restrictions are not part of the stated case. Rolling substitutions may be a rule of futsal, but that causal claim is not presented in the source.")
add(16, "application", "An association is deciding how to use futsal in its development programme. Which choices are supported?",
    ["Use it as a complementary environment for developing transferable skills.", "Integrate it at stages where frequent touches and decisions serve player needs.", "Consider it as a winter or indoor competition opportunity.", "Prepare coaches to connect futsal experiences with the wider player pathway."],
    ["Replace small-sided football with futsal during the sampling years to create a consistent technical base."],
    "Futsal can enrich, not replace, the football pathway. Its technical, perceptual and practical benefits should be deliberately connected to player needs and coaching. Substituting it wholesale for other small-sided experiences would narrow the varied development environment advocated in the chapter.")
add(16, "factual_anchor", "Which statement correctly summarises UEFA's elite youth player-development scheme?",
    ["It is organised around the pillars support, share and improve."],
    ["It links academy accreditation, development tournaments and the Youth League into one competition pathway.", "It funds association projects that strengthen the transition from elite youth to senior national teams.", "It benchmarks national player pathways through club and association development outcomes.", "It provides technical tools primarily for coaches working in UEFA youth competitions."],
    "The diagram names support, share and improve as the scheme's three pillars. The surrounding chapter describes several initiatives and tools, but not as one competition pathway, funding condition, benchmarking regime or restricted service. The scheme helps associations improve elite youth development more broadly.")

# PDF page 17 / handbook pages 286-287: academies, tournaments, Youth League and conclusion.
add(17, "application", "A federation wants youth internationals to learn rather than be judged mainly by results. Which uses of UEFA development tournaments fit that aim?",
    ["Expose players to international matches in a development-focused setting.", "Use the events to give players and staff learning experiences before higher-stakes competition."],
    ["Select balanced squads so each tournament provides reliable comparison with peer associations.", "Rotate players across positions to broaden the evidence available for future selection.", "Align tournament objectives with the UEFA Youth League so players encounter one elite-game model."],
    "Development tournaments provide valuable international experience with learning as the priority. They prepare players, coaches and referees for future demands without turning the event into a ranking exercise. Squad balance, positional rotation and alignment with club competition may be local choices, but they are not the source's central purposes.")
add(17, "explanation", "How does the UEFA Youth League support elite-player development?",
    ["It gives leading academy players meaningful international club competition.", "It exposes players to different football cultures and styles.", "It creates demanding experiences that can bridge academy and senior football."],
    ["It standardises the competitive calendar for academies linked to senior UEFA competitions.", "It allows associations to compare the output of their academy systems through club results."],
    "The Youth League raises the quality and variety of competitive experience for elite young players. International opponents and contexts add challenges beyond domestic academy football and can support transition. Its developmental value does not depend on calendar standardisation or using results to rank national systems.")
add(17, "application", "A national association is reviewing its entire football-development strategy. Which final principles from the chapter should guide the review?",
    ["Keep grassroots, coach education and elite-player development connected by a long-term vision.", "Make player and participant needs central to pathway design.", "Support clubs and coaches in creating high-quality daily environments.", "Treat development as an evolving process that requires collaboration, reflection and improvement."],
    ["Use senior international performance as the shared outcome that aligns participation and performance programmes."],
    "The chapter presents development as an interconnected, long-term system centred on people and learning. Associations provide direction and support, while clubs and coaches shape everyday experience. Senior performance matters, but it cannot serve as the single outcome for a system that also seeks participation, retention and lifelong involvement.")


def main() -> None:
    assert len(QUESTIONS) == 100
    category_counts = {
        category: sum(question["oral_exam_category"] == category for question in QUESTIONS)
        for category in {"application", "explanation", "factual_anchor"}
    }
    assert category_counts == {"application": 45, "explanation": 35, "factual_anchor": 20}, category_counts
    payload = {
        "schema_version": 1,
        "library_key": "uefa_cfm",
        "chapter_number": 15,
        "session_title": "Chapter 9 - Football development",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")
    print(category_counts)


if __name__ == "__main__":
    main()
