"""Build the staged Chapter 5 UEFA CFM communications bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "Communication-the-media-and-public-relations.pdf"
OUTPUT = Path("data/cfm_imports/chapter_05_communication_media_pr.json")
QUESTIONS: list[dict] = []


def _positions(number: int, count: int) -> list[int]:
    group = (number - 1) % 5
    return {
        1: [group % 5],
        2: sorted({group % 5, (group + 2) % 5}),
        3: sorted({group % 5, (group + 2) % 5, (group + 4) % 5}),
        4: [position for position in range(5) if position != (group + 1) % 5],
    }[count]


def add(page, category, stem, true, false, explanation, crops=None):
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
            "handbook_pages": [146 + 2 * page, 147 + 2 * page],
        },
        "page_crops": crops or [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 150-151: stakeholder communication flows and consistency.
add(2, "application", "External stakeholders are receiving conflicting messages from several association departments. What should the communications review examine first?",
    ["Whether internal objectives, plans and messages are coherent across the association."],
    ["Whether external media coverage can be increased before internal differences are discussed.", "Whether each department can tailor the strategic objective to its stakeholder group.", "Whether two-way channels should be replaced by centrally issued publications.", "Whether stakeholder expectations can be managed through a larger number of channels."],
    "External consistency depends on a coherent internal communications environment. Departments need shared clarity about objectives, plans and core messages before adapting communication to audiences. More coverage or channels would amplify rather than resolve an internal contradiction.")
add(2, "explanation", "How does the chapter distinguish internal and external stakeholders of a national association?",
    ["Internal stakeholders include leaders, staff and volunteers within the association.", "External stakeholders include governing bodies, leagues, clubs, players, media, fans and sponsors."],
    ["Professional players become internal stakeholders when selected for a national team.", "Broadcast-rights holders are internal stakeholders during contracted competitions.", "Amateur clubs are internal stakeholders because they operate under association rules."],
    "The distinction concerns whether the stakeholder sits within the association's organisation or in its environment. Presidents, executives, boards, staff and volunteers are internal; football bodies, participants, media and commercial groups outside it are external. Selection, regulation or contract does not move an external party into the organisation.")
add(2, "factual_anchor", "Which interaction types appear in the chapter's communication-channel model?",
    ["Inside-outside communication.", "Outside-inside communication.", "Two-way communication."],
    ["Vertical communication.", "Rights-holder communication."],
    "The model identifies flows from the association outward, flows from external stakeholders inward and reciprocal two-way exchanges. Channels such as publications, third-party reports, email and social media serve these different directions. Organisational hierarchy and contractual status are not separate interaction types in the model.")
add(2, "application", "Which examples are correctly matched to the direction of communication?",
    ["A press conference is inside-outside.", "A third-party report is outside-inside.", "An interactive website can support two-way exchange.", "Personal contact can support two-way exchange."],
    ["A television report commissioned by a broadcaster is inside-outside because it concerns the association."],
    "Direction depends on who initiates and exchanges the communication. Association events and publications project outward, third-party media can bring external perspectives inward, and interactive or personal channels permit dialogue. Subject matter alone does not turn independent coverage into association-originated communication.")
add(2, "explanation", "Why is each stakeholder interaction described as a 'moment of truth'?",
    ["The interaction tests whether the association's promises match the stakeholder's experience."],
    ["The interaction establishes which department owns the stakeholder relationship.", "The interaction tests whether the audience understood the intended message.", "The interaction measures whether the selected channel reached its planned audience.", "The interaction records feedback for the programme's later communication assessment."],
    "A moment of truth is a point at which conduct and communication are experienced and judged. Repeated interactions can build credibility or expose inconsistency across people and departments. Channel reach and ownership matter operationally, but they do not define this test of promises.")
add(2, "application", "A board member and the media department give different accounts of the same initiative. Which risks follow from the chapter?",
    ["Stakeholders may question the association's coherence.", "Credibility may weaken across later moments of truth."],
    ["The media department gains priority because it owns the external channel.", "The board account should be treated as outside-inside feedback.", "The difference can be resolved by sending each account to a separate audience."],
    "Inconsistent accounts reveal a lack of shared objectives or priorities and can damage credibility. The organisational position should be aligned internally before further external communication. Channel ownership or audience separation does not reconcile the underlying contradiction.")
add(2, "factual_anchor", "Which elements contribute to communication coherence as defined in the chapter?",
    ["Clarity about collective objectives.", "Clarity about organisational aims.", "Clarity about current plans."],
    ["Uniform use of one communication channel.", "Central approval of each stakeholder response."],
    "Coherence means that the organisation and its people understand their collective objectives, aims and latest plans. It supports consistent messages while allowing appropriate channels and delegated interaction. It does not require a single channel or central clearance of each exchange.")
add(2, "application", "A national association is mapping communication around a policy change. Which stakeholders should be included in the system?",
    ["The board and staff who must understand the policy.", "Leagues and clubs affected by implementation.", "Players, fans and media who may react publicly.", "Governing and commercial partners whose interests are engaged."],
    ["Stakeholders selected after the announcement according to the volume of coverage generated."],
    "The stakeholder system extends across internal decision-makers and external football, public and commercial groups. Mapping them before communication helps identify direction, channel and consistency needs. Waiting for coverage makes the process reactive and overlooks quieter but influential relationships.")
add(2, "explanation", "What is the main communications implication of a converging digital media environment?",
    ["Associations need an adaptable strategy for faster, wider and changing information consumption."],
    ["Associations should prioritise the fastest channel when stakeholder preferences differ.", "Digital convergence makes internal communication less important than external monitoring.", "Changing search behaviour makes formal planning less reliable than real-time response.", "Wider reach allows one message format to serve internal and external audiences."],
    "Information now circulates quickly and widely while consumption and search behaviours evolve. This creates opportunity and risk, requiring strategic adaptation rather than reflexive choice of the fastest platform. Internal coherence remains the basis for credible communication across the converged environment.")
add(2, "explanation", "Why does the chapter begin with internal communication before external communication and PR?",
    ["External credibility depends on shared understanding inside the association.", "Internal alignment reduces inconsistent messages across external moments of truth."],
    ["Internal communication determines which external stakeholders have decision authority.", "External PR begins after internal channels have produced measurable media coverage.", "Internal alignment permits external communication to proceed without stakeholder dialogue."],
    "Communication follows an inside-outside logic: people within the association need common objectives, plans and messages before speaking externally. That alignment reduces inconsistency and supports credibility. It does not replace two-way stakeholder engagement or depend on media results.")

# PDF page 3 / handbook pages 152-153: internal communication and the foundation of PR.
add(3, "factual_anchor", "Which activities are key aspects of internal communication in Figure 5.3?",
    ["Organising a communications strategy.", "Developing identity and ownership.", "Assessing success and failure."],
    ["Segmenting external media audiences.", "Negotiating access with rights holders."],
    "The figure links strategy, identity and ownership, tools, assessment, and staff connection and training. These activities make internal communication a managed process. External media segmentation and rights negotiations belong elsewhere in the communications remit.")
add(3, "application", "A national association wants staff to feel valued and connected to its direction. Which measures fit the chapter?",
    ["Explain strategic decisions before they become public.", "Give staff opportunities to express views on vision and policy.", "Provide internal communication tools and face-to-face exchanges.", "Offer training and development that reinforce organisational belonging."],
    ["Use external campaign performance as the principal measure of staff ownership."],
    "Ownership grows when staff receive timely information, can contribute views and have practical ways to connect and develop. This supports a common language, motivation and acceptance of strategy. External campaign results do not demonstrate whether staff feel involved.")
add(3, "explanation", "What organisational condition makes internal communication effective even without a dedicated department?",
    ["A management-backed strategy that operates across organisational units."],
    ["A communications subsection within each operational department.", "A direct reporting line from each unit to the external PR team.", "A shared intranet used as the main source of strategic decisions.", "A central newsletter that standardises horizontal coordination."],
    "A dedicated department is not essential if management supports a coherent strategy that works across the organisation. The aim is horizontal coordination rather than fragmented ownership in departmental subsections. Tools such as intranets or newsletters support the strategy but do not create it.")
add(3, "application", "Management plans to announce a major restructuring. Which internal steps should precede the public announcement?",
    ["Inform staff about the decision and its rationale.", "Provide a channel for questions and views."],
    ["Ask external media to explain the change so staff receive an independent account.", "Limit advance communication to managers who will speak publicly.", "Delay staff consultation until the external narrative has stabilised."],
    "Staff should be informed and involved before major decisions become public, which protects morale and ownership. A two-way internal channel helps management understand expectations and prepare consistent explanations. Learning through the media or postponing dialogue leaves employees out of the process.")
add(3, "factual_anchor", "Which tools can support information sharing inside a national association?",
    ["An intranet.", "Internal newsletters.", "Face-to-face exchanges."],
    ["Third-party media reports.", "Public-affairs lobbying."],
    "The chapter names newsletters, intranet, social media and face-to-face exchanges as internal tools. Their purpose is to make operational information obtainable and shared across units. Third-party reports and lobbying connect the association with its external environment.")
add(3, "application", "A rapidly growing association has added several specialised departments. Which responses address the communication risk?",
    ["Create horizontal communication across the departments.", "Schedule face-to-face time between managers and staff.", "Ensure operational information is obtainable across units.", "Keep the communications strategy backed by senior management."],
    ["Allow each specialist department to define the association message for its own operational area."],
    "Growth increases the effort needed to connect units and preserve shared objectives. Horizontal coordination, accessible information, management support and direct interaction counter silos. Departmental expertise should shape details, but separate corporate messages would weaken coherence.")
add(3, "explanation", "Why is internal communication a prerequisite for successful external communication?",
    ["It creates in-house understanding and acceptance of the association's vision."],
    ["It assigns external channel responsibility to the staff closest to each issue.", "It provides external audiences with evidence that staff were consulted.", "It converts operational information into a public-relations objective.", "It reduces the need to adapt messages for different external stakeholders."],
    "Internal communication aligns people around corporate vision, strategic goals and operational information. That shared base supports consistent and credible external behaviour. It does not determine channel ownership or remove the need for audience-specific communication.")
add(3, "application", "Which elements should be linked in an internally established communications platform?",
    ["Objectives and target audiences.", "Channels, actions and resources."],
    ["Media coverage and staff approval as the starting conditions.", "Departmental messages and independent assessment plans.", "External publicity and internal training as separate strategies."],
    "The chapter calls for a consistent platform linking objectives, channels, actions, targets, planning, assessment and resources. These elements should form one strategic process before external targeting. Coverage, training and departmental input may contribute, but they should not fragment the platform.")
add(3, "explanation", "Which principles distinguish sound PR from image-making detached from reality?",
    ["PR communicates the association's actual aims and evolving work.", "Reputation depends on alignment between the projected image and stakeholder experience.", "Internal employees as well as external audiences form part of the reputation relationship."],
    ["PR should lead stakeholder expectations while operations catch up with the projected identity.", "PR credibility is protected when aspirational messages are framed as strategic objectives."],
    "PR should communicate real aims and practices in a way that strengthens reputation across employees and external stakeholders. A gap between projection and lived experience creates reputational damage. Labelling a claim as aspirational does not remove the need for authenticity.")
add(3, "application", "Staff morale is falling because employees learn about association initiatives through the press. Which corrective actions follow the chapter?",
    ["Give staff earlier access to major decisions.", "Create opportunities for staff to raise concerns.", "Clarify the association's objectives across departments.", "Use regular internal channels supported by management."],
    ["Increase external briefing detail so employees can rely on a more complete public account."],
    "Employees who feel out of the loop may lose motivation and support for the association. Earlier internal information, dialogue and cross-unit clarity rebuild ownership. Improving the public briefing would leave the internal failure unresolved.")

# PDF page 4 / handbook pages 154-155: strategic PR, media relations and management functions.
add(4, "explanation", "Why should PR be integrated into the association's wider communications strategy?",
    ["It manages reputation and relationships across a complex stakeholder environment."],
    ["It provides the paid-media reach needed to make corporate messages credible.", "It coordinates external messaging after strategic decisions have been finalised elsewhere.", "It protects reputation by separating difficult media stories from strategic work.", "It centralises external contact in the PR team to maintain communication consistency."],
    "PR affects how the association understands audiences, advises decisions and builds trust across many relationships. It therefore belongs within management and communication rather than as a publicity add-on. Paid reach, journalistic promotion and isolation from operations misunderstand its role.")
add(4, "application", "A difficult governance story is circulating among journalists. How should the association approach the media relationship?",
    ["Keep channels open and help journalists obtain accurate information.", "Recognise that journalists have an independent agenda rather than a promotional duty."],
    ["Restrict contact until the association has favourable news to balance the story.", "Ask sports journalists to apply the same agenda as general-news reporters.", "Prioritise rebuttal before establishing which claims are inaccurate or unfair."],
    "Journalists are not there to promote the association, and different media sectors may have different agendas. Open channels and accurate assistance make the relationship more workable during good and difficult stories. Rebuttal is appropriate for unfair claims after the facts and perceptions have been assessed.")
add(4, "factual_anchor", "Which responsibilities belong to PR as a management function?",
    ["Anticipating and interpreting public opinion and emerging issues.", "Advising management on public consequences of decisions.", "Researching and evaluating communication programmes."],
    ["Assigning journalists to association campaigns.", "Approving the commercial terms of media-rights distribution."],
    "PR scans the external environment, advises internal decision-makers and continually researches, conducts and evaluates programmes. These responsibilities connect public understanding with organisational aims. Editorial assignments and rights sales remain responsibilities of media organisations and commercial functions.")
add(4, "application", "An association has no designated PR capability while criticism is growing online. Which risks should management address?",
    ["Core messages may be communicated inconsistently.", "Distorted perceptions may become established.", "The association may become reactive and defensive.", "Reputational damage may accumulate across international digital audiences."],
    ["Stakeholders may interpret the lack of a PR team as a decision to use direct communication."],
    "Without coordinated PR, rapid social communication can amplify inconsistent messages and entrenched perceptions. The organisation risks responding to other agendas instead of setting its own through credible relationships. Direct channels remain useful, but their existence does not explain or solve the coordination gap.")
add(4, "factual_anchor", "Which PR area cultivates transparent relationships with political and cultural elites around football governance?",
    ["Public affairs."],
    ["Publicity.", "Media relations.", "Advertising.", "Direct selling."],
    "Public affairs addresses governance issues and relationships with political and cultural elites. Publicity and media relations support visibility and media relationships, while advertising and selling have distinct commercial purposes. The audience and policy context identify the public-affairs function.")
add(4, "explanation", "How does football PR differ from advertising and marketing in Table 5.1?",
    ["PR advocates the association, its remit and strategic goals rather than buying product-sales messages.", "Marketing focuses on getting products or services to customers, whereas PR focuses on relationships and reputation."],
    ["PR uses unpaid channels, whereas advertising and marketing depend on paid channels.", "PR communicates with public bodies, whereas marketing communicates with fans and sponsors.", "PR addresses corporate goals, whereas marketing operates outside the association's strategy."],
    "PR includes promotion of the association, publicity, media relations and public affairs. Advertising is chiefly paid product or service communication, while marketing connects offers with customers. Channel payment or audience type alone does not create the distinction, and each function should support strategy.")
add(4, "application", "Stakeholder experience contradicts the association's public claims. Which PR responses are appropriate?",
    ["Investigate the operational reality behind the criticism.", "Correct inaccurate claims with evidence.", "Advise management on changes needed to align conduct and message."],
    ["Strengthen the projected image before discussing the underlying experience.", "Treat criticism as a media-relations problem once the message has been issued consistently."],
    "PR seeks accurate and fair perceptions, but credibility depends on reality matching communication. The team should distinguish unfair claims from genuine operational shortcomings and advise correction on both fronts. Repeating a coherent message cannot repair a credible experience gap.")
add(4, "explanation", "What characterises a proactive rather than reactive PR posture?",
    ["Monitor public opinion and emerging issues.", "Maintain relationships before crises arise.", "Communicate core mission consistently across levels.", "Set constructive agendas across traditional and social media."],
    ["Delay public engagement until an issue has a stable media interpretation."],
    "Proactive PR scans, advises, communicates and builds trust before pressure peaks. This gives the association relationships and credibility with which to address difficult periods. Waiting for a settled external narrative leaves the organisation defensive and allows perceptions to harden.")
add(4, "application", "Why should an association invest in media trust before an inevitable crisis occurs?",
    ["Established mutual understanding gives later communication greater credibility."],
    ["Trusted outlets will adopt the association's interpretation before reporting the issue.", "Long-standing relationships allow difficult stories to be deferred until facts are complete.", "Prior goodwill shifts responsibility for correcting public perceptions to journalists.", "Media trust reduces the need for internal agreement during a fast-moving crisis."],
    "PR relationships operate as a foundation of credibility and mutual understanding when a crisis tests the association. Trust does not remove journalistic independence or permit delay and inconsistency. It makes accurate, open communication more likely to be heard and understood.")
add(4, "explanation", "Why should players and coaches be included in communications planning?",
    ["They communicate through the media and therefore affect the association's relationships.", "Their practical needs should be considered when communication activity is planned."],
    ["Their media visibility means their needs should determine timing before organisational objectives are set.", "Their participation allows the PR team to transfer media responsibility to the team.", "Their needs should define the communication objectives before stakeholder research."],
    "Players and coaches are visible communicators and important participants in media operations. Planning should account for their needs while aligning their contribution with association objectives. Inclusion does not give them strategic control or relieve the PR function of coordination.")

# PDF page 5 / handbook pages 156-157: PR objectives, techniques and stakeholder targeting.
add(5, "factual_anchor", "Which outcomes are listed as key objectives of football PR?",
    ["Raise awareness.", "Inform and educate stakeholders.", "Build trust."],
    ["Secure paid-media inventory.", "Increase the licensing value of the association's marks."],
    "Football PR aims to raise awareness, inform, educate, build trust and goodwill, encourage team support and generate support for strategy and policy. Paid advertising space and licensing valuation belong to other functions. The PR outcomes concern understanding and relationships.")
add(5, "application", "A national association wants public support for a new grassroots strategy. Which PR techniques could form a coherent programme?",
    ["Explain the strategy through clear B2B and B2C communication.", "Use dialogue with supporters to understand concerns.", "Build media relationships that support accurate coverage.", "Open relevant venues or activities to community participation."],
    ["Select a publicity format before defining what stakeholder response the strategy requires."],
    "The chapter presents communication, dialogue, media relations, community access and other techniques as tools serving researched objectives. Used together, they can inform, listen and demonstrate the strategy in practice. Choosing a visible tool before defining the desired response reverses the planning sequence.")
add(5, "explanation", "Why are PR techniques insufficient when used without research and strategic planning?",
    ["They are visible delivery tools rather than the complete PR management process."],
    ["Using several techniques supplies strategic breadth when audience barriers remain unclear.", "The reach produced by a technique defines the objective it can credibly support.", "A coordinated delivery timetable turns the selected tools into a communication strategy.", "Stakeholder dialogue can refine the programme purpose after implementation has begun."],
    "Techniques such as publicity, dialogue, sponsorship and lobbying are the visible execution of PR. Research and planning first establish audiences, barriers, objectives and desired action, after which tools can be selected and evaluated. Visibility does not make a technique strategically self-sufficient.")
add(5, "application", "Which objectives would be informative goals for an association campaign?",
    ["Increase awareness of a programme.", "Improve how stakeholders perceive its quality."],
    ["Create emotional attachment to the association's mission.", "Motivate supporters to volunteer for the programme.", "Prompt advocates to promote the programme among peers."],
    "Informative goals concern attention, representation, image and perceived quality. Emotional attachment forms a separate objective type, while volunteering and advocacy are behavioural responses. Clear classification helps the association choose appropriate measures.")
add(5, "factual_anchor", "Which three objective types organise the chapter's discussion of PR effects?",
    ["Informative objectives.", "Emotional objectives.", "Behavioural objectives."],
    ["Commercial objectives.", "Editorial objectives."],
    "PR seeks effects on perceptions, emotions and behaviours, expressed as informative, emotional and behavioural goals. A programme may also support commercial or editorial interests, but those are not the three objective classes presented. The categories help connect communication with measurable stakeholder change.")
add(5, "application", "Which outcomes are behavioural PR objectives?",
    ["Stakeholders volunteer for a programme.", "Stakeholders contact the association for information.", "Supporters advocate the programme to peers.", "The target group participates in the requested activity."],
    ["Stakeholders report a stronger emotional attachment without changing their actions."],
    "Behavioural objectives ask the audience to do something, including volunteering, seeking information, advocacy or participation. Emotional attachment may support later behaviour but is a distinct outcome. Evaluation should therefore match the action requested.")
add(5, "explanation", "Which result represents an emotional rather than informative or behavioural objective?",
    ["A stronger emotional attachment to the association and its mission."],
    ["Higher awareness of the programme among the target group.", "A more favourable rating of the association's perceived quality.", "More enquiries requesting programme information.", "More supporters promoting the programme to friends."],
    "Emotional objectives seek attachment to the association and its mission. Awareness and perceived quality are informative effects, while enquiries and advocacy are behaviours. Separating the categories supports precise campaign assessment.")
add(5, "application", "The Moldova association finds that a stakeholder group views it as closed and out of touch. What should happen before channel selection?",
    ["Identify the specific barriers behind that perception.", "Clarify what the group should know and do."],
    ["Select social media because the barrier concerns transparency.", "Use emotional connectors as the campaign's final assessment measures.", "Begin with a high-frequency channel to demonstrate responsiveness."],
    "The Moldova example starts with stakeholders and barriers, then defines emotional connectors, knowledge, desired behaviour and channels. A transparency problem does not by itself identify the right platform or measure. Channel choice follows diagnosis and objectives.")
add(5, "explanation", "What does the Moldova example show about matching stakeholders to communications?",
    ["Different groups face different barriers.", "Emotional connectors can make the message relevant.", "Desired knowledge and action should guide channel selection."],
    ["A shared reputation objective requires the same message emphasis across groups.", "Channel accessibility is a sufficient basis for selecting stakeholder actions."],
    "Employees, regional associations and fans have distinct barriers, motives, desired actions and accessible channels. The strategy can share an overall reputation aim while adapting content and delivery. Easy access to a channel matters, but it does not define the behaviour being sought.")
add(5, "application", "A stadium project requires political support and stronger community acceptance. Which PR actions fit the techniques framework?",
    ["Use lobbying to explain the association's position to relevant political elites.", "Open facilities or project activities to meaningful community use.", "Engage supporters and local groups in two-way dialogue.", "Prepare media relationships to communicate the project's strategic purpose."],
    ["Treat sponsorship coverage as evidence that political and community concerns have been resolved."],
    "The framework combines lobbying, venue access, supporter engagement and media relations around strategic objectives. Each technique addresses a different relationship and should generate feedback as well as visibility. Sponsor coverage cannot substitute for political understanding or community experience.")

# PDF page 6 / handbook pages 158-159: communication processes and #WePlayStrong strategy.
add(6, "factual_anchor", "How should a communication programme be organised according to the chapter?",
    ["As a defined process with a start point and an end point."],
    ["As a continuing set of channels reviewed when media coverage changes.", "As a sequence beginning with audience selection and ending with action delivery.", "As a campaign cycle whose end point is the strategic objective.", "As a collection of PR techniques managed by their responsible departments."],
    "A programme should have a defined beginning and end and connect recommended techniques to strategic and communication objectives. Audience, channels, actions and assessment sit within that process. A continuing communications function may contain many programmes, but each programme needs boundaries for planning and evaluation.")
add(6, "application", "A campaign aims to strengthen the legitimacy of a domestic league structure. Which objective links are appropriate?",
    ["Connect the strategic legitimacy goal to a communication objective about awareness and negative perceptions.", "Select audiences, channels and actions in relation to those linked objectives."],
    ["Use media coverage as the strategic objective and league legitimacy as the assessment measure.", "Set separate communication objectives for each channel before defining the audience.", "Treat positive awareness as sufficient evidence that the league structure is legitimate."],
    "Table 5.4 links the corporate goal with a specific communication effect, then defines audiences, channels, actions and assessment. Awareness contributes to legitimacy but does not prove it by itself. Channels execute the communication objective rather than generating separate objectives first.")
add(6, "explanation", "Which components make the communication process in Table 5.4 assessable?",
    ["A defined strategic and communication objective.", "Specified audiences and channels.", "Planned actions and assessment methods."],
    ["A common message used across audiences and channels.", "A publicity target separated from the association's strategic plan."],
    "The table creates a chain from strategy through communication objective, audience, channel and action to assessment. This makes the intended effect and evidence explicit. Message adaptation may be needed, and publicity should remain connected to corporate strategy.")
add(6, "application", "Employees report silos, limited long-term planning and weak awareness of association activity. Which responses follow the Moldova example?",
    ["Use regular cross-unit meetings and event debriefs.", "Gather staff feedback through surveys.", "Create accessible shared calendars and internal channels.", "Encourage employees to promote association activity through their networks."],
    ["Begin with an external reputation campaign so staff see the association's intended image."],
    "The Moldova plan combines face-to-face communication, feedback, shared information and staff advocacy to address silos and trust. These actions build internal awareness and participation before asking employees to spread the message. An external campaign would repeat the inside-outside error.")
add(6, "factual_anchor", "Which audience problem prompted the original #WePlayStrong campaign objective?",
    ["Many girls stopped playing football as they entered their teenage years."],
    ["Teenage players had limited awareness of elite women's competitions.", "Member associations lacked a shared visual identity for women's football.", "Young supporters viewed football content as inaccessible on mobile platforms.", "Female players lacked routes to appear in mainstream football media."],
    "UEFA research identified teenage drop-out from participation as a major development challenge. The campaign aimed to raise awareness of health and growth, change perceptions and make football feel relevant and attractive to girls. Media and identity choices served that objective rather than defining the initial problem.")
add(6, "application", "Why were Instagram and YouTube appropriate early channels for #WePlayStrong?",
    ["They were used by the teenage target audience.", "They supported visual stories about fun, confidence and health."],
    ["They gave member associations editorial control over external media coverage.", "They reached the target through the same content format as traditional television.", "They allowed campaign assessment to focus on views rather than participation attitudes."],
    "Channel choice followed the audience and message: social and video platforms could reach teenage girls with engaging, peer-relevant content. Member associations could customise supporting material, but the platforms did not confer editorial control over wider media. Reach metrics were useful alongside perception and participation evidence.")
add(6, "explanation", "What makes #WePlayStrong a long-term PR strategy rather than a short publicity burst?",
    ["The campaign evolved through successive stages.", "Content and partners were refreshed around changing opportunities.", "The core awareness and perception objectives remained connected over time."],
    ["The campaign retained its original platform mix to build consistent exposure.", "The campaign treated each major tournament as a separate objective cycle."],
    "The initiative adapted content, influencers and platforms while preserving a long-term aim around participation and perceptions. Major events became opportunities within the strategy rather than isolated campaigns. Longevity came from purposeful evolution, not an unchanged channel plan.")
add(6, "application", "How should UEFA assess whether the #WePlayStrong programme is advancing its objectives?",
    ["Measure awareness and reach among the intended audience.", "Track changes in perceptions of girls' and women's football.", "Examine stated interest or action related to participation.", "Use feedback to adapt content, partners and platforms."],
    ["Use total social-media views as the common measure for informative, emotional and behavioural objectives."],
    "The campaign seeks informative, emotional and behavioural change, so assessment should include reach, perception and participation-related evidence. Feedback also informs adaptation across campaign stages. A view count measures exposure but cannot represent attachment or behaviour by itself.")
add(6, "explanation", "Why did the campaign toolkit add strategic value for UEFA member associations?",
    ["It allowed a shared campaign to be adapted to local audiences while preserving the core purpose."],
    ["It enabled member associations to replace UEFA's target audience with their existing fan segments.", "It transferred campaign assessment responsibility from UEFA to local media partners.", "It standardised content so associations could avoid local stakeholder research.", "It gave local associations freedom to redefine the campaign's behavioural objective."],
    "The toolkit supported localisation within a common strategic campaign, helping associations speak directly to girls and young women in their countries. Adaptation concerned delivery and relevance, not abandonment of the target or objectives. Local insight remained necessary to use the toolkit well.")
add(6, "explanation", "What does the stakeholder table show about emotional connectors and desired actions?",
    ["Connectors translate stakeholder motives into a relevant communication approach.", "Desired actions should reflect the barriers and relationship being addressed."],
    ["Emotional connectors are campaign outcomes that replace behavioural assessment.", "Desired actions should be common across groups when the reputation objective is shared.", "Connectors determine channel choice before the association defines what stakeholders should know."],
    "Emotional connectors such as belonging, appreciation or enjoyment help the message resonate with a particular group. The requested behaviour should then answer the diagnosed barrier and communication goal. Connectors guide relevance but are not outcome measures or substitutes for knowledge objectives.")

# PDF page 7 / handbook pages 160-161: campaign evolution and strategic media operations.
add(7, "application", "How did the Women's World Cup provide a strategic opportunity for #WePlayStrong?",
    ["It supplied a relevant moment to amplify the campaign's existing objectives.", "It enabled stories linking historical and current female players.", "It attracted mainstream and social-media attention to the campaign."],
    ["It shifted the campaign from teenage participation towards tournament promotion.", "It made influencer activity less important because event coverage supplied sufficient reach."],
    "The tournament was used as a platform within the existing perception and participation strategy. Historical stories, players, influencers and media relations connected the campaign to a major public moment. The event expanded reach without replacing the core target or the need for creative partners.")
add(7, "explanation", "Which lessons emerge from the reported development of #WePlayStrong?",
    ["Major events can extend a long-term campaign.", "Creative partners and influencers can open new forms of engagement.", "Platform choices should evolve with audience behaviour.", "Local customisation can preserve relevance across member associations."],
    ["A campaign should retain its strongest platform once awareness begins to grow."],
    "The case links longevity with adaptation: the campaign used events, influencers, changing platforms and a customisable toolkit. Its strategic purpose stayed stable while delivery evolved. Continued growth did not justify freezing the media mix.")
add(7, "factual_anchor", "What does it mean to describe journalists and broadcasters as cultural intermediaries?",
    ["They mediate information between sources and audiences."],
    ["They translate association strategy into messages approved for public use.", "They distribute football content while remaining separate from audience perception.", "They act as neutral channels whose agendas are set by information sources.", "They represent football organisations when public debates concern the game."],
    "Media professionals select and shape information between sources and audiences and are influenced by the organisations in which they work. They are therefore active intermediaries rather than neutral pipes or association representatives. Understanding this role is central to strategic media relations.")
add(7, "application", "A media officer is planning access for print, radio and television journalists. Which considerations are appropriate?",
    ["Understand the different deadlines and production needs of each sector.", "Adapt practical access while preserving clear relationship boundaries."],
    ["Provide the same access timetable to demonstrate equal treatment across media.", "Prioritise broadcast needs because their audience reach is likely to be larger.", "Let each outlet determine access arrangements after the event schedule is fixed."],
    "Media sectors work to different deadlines and formats, so effective planning accommodates genuine needs. Fairness does not require an identical timetable, and boundaries remain necessary. The officer should coordinate access rather than cede logistics to the outlets.")
add(7, "explanation", "Which steps form the chapter's relationship-management process for media operations?",
    ["Identify the relationships to develop.", "Evaluate their current importance and value.", "Design policies to improve them through dialogue."],
    ["Assign each relationship to a fixed priority category for the strategic cycle.", "Select media channels before deciding which relationships the association needs."],
    "The process moves from identification and evaluation to policy design and implementation. Relationship priorities can change, and two-way dialogue reveals what each media public needs and what the association can provide. Channel planning follows the relationship and objective rather than preceding them.")
add(7, "application", "An association is implementing new media-access guidelines. Which practices balance policy and the human relationship?",
    ["State clear boundaries for media interaction.", "Explain the purpose of the guidelines to journalists and staff.", "Use dialogue to understand practical media needs.", "Apply interpersonal skill when resolving exceptions or tension."],
    ["Let strong personal relationships determine when written boundaries apply."],
    "Guidelines establish predictable boundaries, while dialogue and interpersonal communication make them workable in real situations. The human element complements policy but does not displace it. Exceptions should be reasoned within the strategy rather than granted through personal influence.")
add(7, "factual_anchor", "What is the first step in the chapter's process for successful media relationships?",
    ["Identify the journalists and organisations with which relationships exist or should be developed."],
    ["Evaluate which current relationships have run their course.", "Design policies for the most influential outlets.", "Set media-performance targets for each relationship.", "Implement boundaries for access and information."],
    "The process begins by identifying the relevant journalists and media organisations. Evaluation, policy design and implementation follow once the relationship map exists. Media goals are aligned at the planning level rather than replacing this first diagnostic step.")
add(7, "application", "How should an association set media goals for an event?",
    ["Define what the event, players and organisation should achieve through media activity.", "Align those goals directly with the association's strategic plan."],
    ["Begin with the coverage volume available from key outlets and derive the event goal.", "Let player visibility determine the organisational objective for the event.", "Separate media performance from corporate strategy so editorial results remain independent."],
    "Media planning starts with goals for the event, participants and organisation, tied to overall vision and objectives. Coverage opportunities influence tactics, not the strategic purpose. Editorial independence does not require the association to detach its own media goals from strategy.")
add(7, "explanation", "Why is football PR described as a dynamic process rather than an optional add-on?",
    ["Media relationships and technologies evolve over time.", "Reputation and stakeholder relationships affect core management decisions.", "People across the organisation contribute to communication outcomes."],
    ["PR becomes strategic when a campaign generates sufficient external coverage.", "Media relations can be isolated from PR once access policies are implemented."],
    "PR continually identifies, evaluates and develops relationships in a changing environment. Its consequences reach policy, reputation and organisational behaviour, and many staff contribute to moments of truth. Coverage and access policies are outputs within the process, not conditions that make PR strategic.")
add(7, "application", "Media coverage is amplifying a governance dispute and shaping public opinion. Which responses fit the chapter?",
    ["Analyse how different outlets are framing the issue.", "Engage the most relevant media relationships with accurate information.", "Use dialogue to understand the questions and constraints of those outlets.", "Keep the response aligned with the association's strategic goals and agreed policy."],
    ["Concentrate on the outlet with the largest audience before evaluating relationship importance."],
    "Media can set agendas, form opinions and amplify or distort debate, so the association needs analysis and prioritised relationships. Accurate information, dialogue and policy alignment support a credible response. Audience size matters, but influence and relationship relevance require evaluation first.")

# PDF page 8 / handbook pages 162-163: media-officer skills, social media and platform strategy.
add(8, "factual_anchor", "Which media-officer skill means being polite while remaining firm with competing parties?",
    ["Diplomacy."],
    ["Mediation.", "Negotiation.", "Organisation.", "Relationship evaluation."],
    "Diplomacy balances courtesy with firmness when coaches, players and journalists want different things. Mediation solves practical or interpersonal conflict, negotiation seeks behavioural compromise, and organisation manages logistics. The skills overlap in practice but have distinct emphasis in the chapter.")
add(8, "application", "A live press conference risks being dominated because journalists cannot reach the microphones easily. Which responses are appropriate?",
    ["Redesign the practical layout and access before the event.", "Retain discreet operational control while the conference is live."],
    ["Use diplomacy with journalists after the conference to restore the planned format.", "Ask the coach to mediate access because sporting staff control the event narrative.", "Reduce the number of attending outlets before testing a better logistical arrangement."],
    "The media officer's organisational role includes planning microphone access and other logistics that preserve a smooth, fair conference. During a live event, control should be discreet but active. Post-event diplomacy or restricting attendance would address symptoms after a preventable layout failure.")
add(8, "explanation", "Which principles support productive day-to-day relationships with journalists?",
    ["Understand the deadlines and constraints of different media.", "Be flexible where practical while maintaining boundaries.", "Nurture the relationship continuously rather than around favourable stories."],
    ["Offer comparable access by using the same arrangements for print, radio and television.", "Allow established journalists broader boundaries because their constraints are well understood."],
    "Positive media relations depend on understanding sector needs, accommodating them where possible and being firm about limits. Relationships need continuous attention across easy and difficult periods. Fairness is compatible with tailored logistics, and familiarity does not justify looser boundaries.")
add(8, "application", "Credible evidence confirms an embarrassing association failure that is spreading online. How should media relations respond?",
    ["Acknowledge the issue.", "Provide accurate information about what happened.", "Explain the actions being taken to move forward.", "Prepare spokespeople to communicate consistently across platforms."],
    ["Defend the existing position until the online story has reached a stable interpretation."],
    "In an instant media environment, the story is likely to emerge through some route. The media function should not defend the indefensible; acknowledgment, accuracy and forward action protect credibility better. Waiting for the narrative to settle leaves other actors to define it.")
add(8, "factual_anchor", "What is a platform media economy?",
    ["An environment in which content moves across multiple media platforms and devices."],
    ["A rights market in which streaming services distribute content through licensed intermediaries.", "A social-media model in which audiences create the association's public message.", "A communications structure in which one website coordinates the association's channels.", "A digital marketplace in which mobile access replaces fixed-device consumption."],
    "The platform economy spans traditional television, internet streaming and other services consumed through fixed and mobile devices. It features convergence, interconnectivity, mobility and real-time interaction. It is broader than a rights route, a website architecture or a mobile-only market.")
add(8, "application", "Many-to-many communication is weakening the association's control of a developing story. Which responses fit the chapter?",
    ["Develop a clear message for the specific audience.", "Cultivate credible messengers and gatekeeper relationships."],
    ["Return to one-way publication channels until the association regains narrative control.", "Use the same spokesperson across audiences to reduce message variation.", "Prioritise message frequency over dialogue with mediators and online communities."],
    "Interactive communication gives many actors the ability to create and relay information. The association therefore needs audience-specific messages and trusted messengers, supported by relationship management. One-way volume cannot restore the influence lost through weak dialogue and mediation.")
add(8, "explanation", "What should a sports information professional align when communicating in the digital age?",
    ["The message with a specific audience.", "The messenger with the relationships needed to deliver it.", "The storytelling form with the requirements of the platform."],
    ["The association's core message with a common format across media.", "The messenger's personal following with authority over the communication objective."],
    "Fundamental communication principles remain, but message, audience, messenger and form must fit the platform and relationship context. Gatekeepers and mediators still matter even in direct channels. Consistency concerns meaning, not reuse of one format or transfer of strategic authority to a popular messenger.")
add(8, "application", "An association is adapting one story for television, a mobile video service and social media. Which practices are appropriate?",
    ["Preserve the core meaning across formats.", "Adapt length and storytelling technique to each medium.", "Design opportunities for sharing and interaction on social platforms.", "Check that the chosen messenger suits each audience."],
    ["Use the television version as the reference format and shorten it for the other platforms."],
    "Basic communication rules and core meaning should remain coherent, while form reflects each platform's peculiarities. Social media adds sharing and interaction, and messenger choice affects credibility. Merely trimming a television product underuses the distinct consumption pattern of mobile and social media.")
add(8, "explanation", "Why does the chapter emphasise the social use of digital technologies rather than the devices alone?",
    ["Communities and communication practices form through how people use the platforms."],
    ["The device determines reach, while social use determines the communication objective.", "Online communities arise when the association provides a common content schedule.", "Technical interconnectivity is more important for fixed devices than mobile platforms.", "Social usage turns outside-inside communication into an association-controlled channel."],
    "Fans and other groups create practices, relationships and online communities around technologies. The strategic meaning therefore lies in social behaviour as well as technical capability. Devices enable exchange, but they do not determine objectives or give the association control over the resulting community.")
add(8, "explanation", "How should Objectives, Strategy and Tactics relate in a digital media plan?",
    ["Objectives define what communication should achieve.", "Strategy and tactics select how appropriate media will deliver that purpose."],
    ["Tactics identify the audience before objectives are finalised.", "Strategy is the choice of platform, while tactics define the association's overall direction.", "Objectives are revised to match the strongest response available from the selected platform."],
    "OST begins with clear objectives, followed by a strategy and tactics or action plans that deliver them. Platform selection belongs within this chain and should serve the intended communication effect. Starting from a tactic or platform risks reshaping purpose around available tools.")

# PDF page 9 / handbook pages 164-165: social-media good practice, monitoring and conclusion.
add(9, "application", "A national association is launching a social-media initiative from an established website. Which implementation steps fit the chapter?",
    ["Integrate the initiative with the current web strategy.", "Link relevant websites to support traffic and implementation.", "Monitor performance against short- and medium-term goals."],
    ["Build a separate audience so social dialogue can be assessed independently of website traffic.", "Choose the dominant social platform before analysing its relationship with traditional media."],
    "The guidance recommends building from existing website traffic, connecting sites and integrating social and traditional media. Clear goals and monitoring define success and guide review. Creating an isolated audience or choosing a platform first would fragment the strategy.")
add(9, "application", "Which practices make an association's social-media presence strategically credible?",
    ["State why the association is using each platform.", "Match platforms to their functions and audiences.", "Listen and engage rather than push messages.", "Commit to distinctive content and sustained dialogue."],
    ["Use a common promotional objective so followers recognise the association across platforms."],
    "Good practice begins with purpose, audience fit, conversation and continued commitment. Fans may reject a presence treated as a promotional feed, and each platform can play a different role. Identity may stay coherent while objectives and content adapt.")
add(9, "factual_anchor", "Which principle should guide the selection of different social-media platforms?",
    ["Platforms serve different functions and reach different demographic audiences."],
    ["Platforms with the largest current audience should carry the association's strategic content.", "Platforms used by journalists should lead the association's supporter strategy.", "Platforms should be grouped by whether communication is personal or organisational.", "Platforms with strong video tools should receive the association's distinctive content."],
    "Platform choice should reflect function, demographic profile and communication objective. Size, journalistic use and technical features are relevant inputs but do not establish strategic fit by themselves. The association should understand each audience and purpose.")
add(9, "application", "Journalists are using social media as a news feed about officials, players and fans. How should the association respond?",
    ["Monitor and participate in the relevant conversation.", "Build relationships by following key people and developing its own audience."],
    ["Issue formal corrections through the association website before engaging on the platform.", "Limit player and official accounts so journalists depend on the corporate feed.", "Treat journalistic monitoring as outside-inside communication requiring no association response."],
    "Journalists monitor social platforms for stories, so the association needs situational awareness and active relationships within that space. Its own participation can supply context and credible information. Website statements and account governance may help, but withdrawal leaves the conversation to others.")
add(9, "explanation", "What does it mean to treat social media as a conversation?",
    ["Listen to audience responses.", "Engage with participants rather than simply broadcasting.", "Use creative, distinctive content that invites sharing and feedback."],
    ["Let audience reaction determine the association's strategic position.", "Respond to high-engagement topics before checking rights-holder constraints."],
    "Conversation involves listening, participation and content that gives audiences a reason to engage. It remains governed by strategy, rights and organisational boundaries. Audience response informs implementation but does not replace the association's objectives or obligations.")
add(9, "application", "Which governance measures should accompany staff and player use of association-related social media?",
    ["Clarify who is authorised to speak for the association.", "Distinguish personal posts from organisational statements.", "Train players and officials on acceptable language and tone.", "Moderate discussion on association-owned profiles."],
    ["Let each team set posting boundaries according to its current media relationships."],
    "Clear authority, capacity, tone, training and moderation protect both the organisation and the game. Guidelines should circulate across the association and online. Team circumstances may affect implementation, but fragmented boundaries would undermine coherence.")
add(9, "factual_anchor", "Which tournament subject does the chapter identify as inappropriate for player social-media posts?",
    ["Team news and injuries."],
    ["Personal reflections on the host city.", "Approved behind-the-scenes content.", "Messages supporting the national team.", "Posts identifying a personal rather than official capacity."],
    "During tournaments, players may use social media but should avoid team news, injuries, referees and incidents in the training camp. The guidance protects sporting and organisational information while permitting responsible participation. Other content remains subject to tone, authority and rights considerations.")
add(9, "application", "An association's social account begins a two-way initiative but then falls silent. Which corrective actions fit the guidance?",
    ["Re-establish sustained responsibility for listening and response.", "Review performance and audience feedback against the stated goal."],
    ["Return to scheduled one-way posts until follower numbers recover.", "Move the initiative to a newer platform before examining the implementation failure.", "Redefine success around the content already published rather than the planned dialogue."],
    "A dialogue that lapses into silence damages credibility and reflects weak implementation commitment. The association should restore ownership, assess feedback and adjust the plan against its definition of success. Platform switching or retroactive measures avoid the operational cause.")
add(9, "explanation", "Why does reduced control over web-based information increase the importance of monitoring?",
    ["Media may rely on sources the association did not create.", "Many actors can spread and reshape information quickly.", "Monitoring allows earlier identification of issues and perceptions."],
    ["Monitoring restores editorial authority over third-party sources.", "Monitoring reduces the need for trusted messengers when inaccurate claims appear."],
    "Digital sources outside the association increasingly influence media coverage and public understanding. Monitoring cannot control them, but it can detect narratives, support timely advice and guide credible response. Editorial power and trusted relationships remain external constraints to manage.")
add(9, "explanation", "Which priorities summarise the chapter's conclusion on communications management?",
    ["Address internal and external communication as linked strategic concerns.", "Use PR to build practical stakeholder relationships.", "Give media operations dedicated and specialised attention.", "Keep platform strategy broad and flexible as technology changes."],
    ["Concentrate resources on the current dominant platform while it defines audience behaviour."],
    "The conclusion integrates internal alignment, external relationships, PR and professional media operations. Because platforms and behaviours change quickly, the strategy needs a clear purpose with enough breadth and flexibility to adapt. Current market dominance is not a reliable long-term basis for concentrating the communications remit.")


def main() -> None:
    assert len(QUESTIONS) == 80, len(QUESTIONS)
    categories: dict[str, int] = {}
    for question in QUESTIONS:
        category = question["oral_exam_category"]
        categories[category] = categories.get(category, 0) + 1
    assert categories == {
        "application": 36,
        "explanation": 28,
        "factual_anchor": 16,
    }, categories
    payload = {
        "schema_version": 1,
        "library_key": "uefa_cfm",
        "chapter_number": 15,
        "session_title": "Chapter 5 - Communication, the media and public relations",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
