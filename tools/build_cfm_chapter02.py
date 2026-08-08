"""Build the staged Chapter 2 UEFA CFM strategic-management bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "Strategic-Management.pdf"
OUTPUT = Path("data/cfm_imports/chapter_02_strategic_management.json")
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
            "oral_exam_category": category,
            "options": options,
            "source_locator": {
                "file": SOURCE,
                "pdf_pages": [page],
                "handbook_pages": [64 + 2 * page, 65 + 2 * page],
            },
            "page_crops": crops or [],
            "answer": {"correct_options": positions, "explanation": explanation},
        }
    )


# PDF page 2 / handbook pages 68-69: purpose and contributions of strategy.
add(2, "application",
    "A national association is considering a youth academy whose benefits will take years to emerge. What is the sound strategic response?",
    ["Commit adequate resources and allow enough time for the academy to demonstrate results."],
    ["Reallocate the academy budget whenever a short-term result disappoints.", "Treat the decision as routine travel administration.", "Launch it without analysis because sporting projects are reversible.", "Judge the academy only by the next senior match result."],
    "This is a long-term and difficult-to-reverse commitment, so it needs structured analysis, sufficient resources and a coherent direction. The academy must be given time to prove itself. Continual short-term changes would create the zigzagging that strategic management is meant to prevent.")
add(2, "explanation",
    "Which features distinguish strategic management from day-to-day operational management in the handbook?",
    ["It is oriented towards the future.", "It reallocates significant resources."],
    ["It concerns only recurring administrative routines.", "It avoids analysis in favour of instinct.", "It is limited to the association as a whole and cannot support projects."],
    "Strategic management looks ahead, is based on analysis and commits meaningful resources. Operational management handles recurring activities such as travel, competitions and finance. Strategic tools can also be used at departmental, project and individual level.")
add(2, "factual_anchor",
    "Which contributions does strategic management make to an association's prospects of achieving its mission and goals?",
    ["Effective and efficient resource allocation.", "Coordination and decision-making support.", "Employee purpose and motivation."],
    ["Elimination of uncertainty from the external environment.", "Replacement of the executive committee by staff heuristics."],
    "The chapter identifies resource allocation, coordinated decision support and employee purpose as the three principal contributions. Together they connect long-term choices with consistent action. Strategic management improves the chance of success but cannot eliminate uncertainty or governance.")
add(2, "application",
    "A growing association's general secretary is becoming a bottleneck for every decision. Which responses fit the chapter's strategic logic?",
    ["Delegate an appropriate level of decision-making to staff.", "Use a documented strategic plan as a decision guide.", "Align decentralised choices with management's intentions.", "Accept that senior leaders cannot retain the same involvement without losing efficiency."],
    ["Require the general secretary to approve every operational detail indefinitely."],
    "Growth makes complete centralisation inefficient because one leader can no longer know and decide everything. Delegation supported by a clear strategy gives staff useful heuristics for consistent choices. It preserves direction without creating senior-management overload.")
add(2, "explanation",
    "Which statement best defines a strategy in the chapter's terminology?",
    ["A set of planned actions and decisions aimed at achieving a long-term goal."],
    ["A record of every operational transaction completed in a season.", "A prediction that removes the need for contingency planning.", "A mission statement that never contains actions or choices.", "A budget prepared independently of organisational goals."],
    "A strategy connects deliberate actions and decisions to a long-term goal. It may concern the whole association, a department or a project. It is broader than a budget and more actionable than a timeless statement of purpose.")
add(2, "explanation",
    "Why can limited resources make strategic management especially valuable to a national association?",
    ["It helps direct scarce resources towards defined priorities.", "It reduces divergent decisions between competing objectives."],
    ["It guarantees that every desired domain can receive equal funding.", "It turns long-term commitments into easily reversible experiments.", "It makes sporting talent and organisational discipline irrelevant."],
    "Limited resources require choices rather than equal investment everywhere. Strategic management establishes a coherent direction and allocates time, people, infrastructure and money accordingly. It improves the odds of success even when the association lacks superior resources.")

# PDF page 3 / handbook pages 70-71: alignment, motivation and system design.
add(3, "application",
    "Staff in several departments are making locally sensible decisions that conflict with one another. What should management introduce?",
    ["A formal strategic plan that acts as a shared heuristic.", "Clear links between departmental choices and management's intentions.", "Delegated decisions within an agreed organisational direction."],
    ["A separate undocumented strategy for every employee.", "Permanent central approval of every routine choice."],
    "A documented plan provides the common logic that detailed manuals cannot supply. Staff can then decide autonomously while remaining aligned across functions. This addresses inconsistency without recreating the overload caused by total centralisation.")
add(3, "application",
    "Competitions staff pursue commercial growth while grassroots staff pursue participation in ways that undermine each other. Which management conclusions follow?",
    ["The association's commercial and football-development responsibilities can create competing interests.", "Strategic coordination is needed so units pull in the same direction.", "The democratic duty to member entities must be considered alongside business assets.", "Cross-functional consequences should be assessed before initiatives are implemented."],
    ["Each unit should maximise its own objective without reference to the association's mission."],
    "National associations combine commercial assets with duties to develop football and safeguard members. That creates legitimate tensions between units rather than a purely commercial hierarchy. Strategy should coordinate those interests and expose cross-functional consequences.")
add(3, "explanation",
    "How can strategy increase employee purpose and motivation?",
    ["By showing how specific activities contribute to desired results."],
    ["By relying exclusively on financial rewards.", "By concealing why resources were allocated.", "By separating daily work from organisational outcomes.", "By replacing communication with performance sanctions."],
    "People are motivated partly by understanding why their work matters. Strategy links activities and resource choices to desired results, creating a clear sense of purpose. Rewards may still matter, but money alone is not the chapter's account of motivation.")
add(3, "factual_anchor",
    "Whose support is identified as essential when introducing a strategic management system in a national association?",
    ["The executive committee or board.", "The president."],
    ["Only external consultants.", "Only competition sponsors.", "Every service provider before senior management is involved."],
    "A strategic system needs backing from senior management, including the board or executive committee, president and general secretary or CEO. It requires little capital or technical infrastructure. The decisive prerequisite is leadership support rather than outside ownership.")
add(3, "application",
    "An unexpected regulatory change makes the association's original plan unrealistic. How should a mature strategic system respond?",
    ["Recognise that even careful plans cannot foresee every environmental change.", "Activate a contingency response to mitigate the threat.", "Assess whether the change creates an opportunity as well as a risk."],
    ["Treat any short-term target miss as proof that strategy is useless.", "Preserve the original actions regardless of the new environment."],
    "Strategic planning increases preparedness but does not predict every internal or external change. A good system permits contingency action and can exploit new opportunities. Blind adherence to obsolete actions would confuse discipline with rigidity.")
add(3, "explanation",
    "Which elements belong to the handbook's generic strategic management system?",
    ["Monitoring and analysing internal and external conditions.", "Formulating goals, objectives and action plans.", "Allocating resources and responsibilities.", "Controlling performance and updating rolling targets."],
    ["Fixing one permanent plan that is protected from annual review."],
    "The system moves from analysis to goal and action formulation, then to resource allocation, responsibility and control. Annual review keeps three-to-five-year targets current. A permanent plan would fail to adapt to performance and environmental change.")

# PDF page 4 / handbook pages 72-73: annual review and UEFA Grow process.
add(4, "factual_anchor",
    "Which sequence reflects the example annual strategic-planning review cycle?",
    ["Analyse performance and environmental changes before the review meeting."],
    ["Approve budgets before analysing the current situation.", "Begin monitoring only after the next election.", "Draft updates before the review meeting determines guidelines.", "Ask external sponsors to approve the plan instead of the executive committee."],
    "The cycle begins with internal and external analysis based on prior performance. Findings go to a review meeting, proposed updates are then formalised and approved, followed by monitoring and implementation decisions. This order keeps changes evidence-led.")
add(4, "application",
    "At the annual review, the previous year's targets were missed and the external environment has changed. Which actions fit the illustrated process?",
    ["Present the analysis at a strategic planning review meeting.", "Use the discussion to set guidelines for plan updates."],
    ["Skip analysis and repeat the plan unchanged.", "Let each department approve its own corporate strategy.", "Delay performance control until the end of the next three-to-five-year cycle."],
    "The review meeting converts performance evidence and environmental change into agreed update guidelines. Those guidelines are later formalised and presented for executive approval. Repeating the plan without review would break the feedback cycle.")
add(4, "explanation",
    "How do periodic strategy development and annual updating work together?",
    ["A full strategic process may occur every three to five years.", "Annual updates keep medium-term targets relevant.", "The cadence should fit elections, competitions and operational cycles."],
    ["Annual updates require rewriting the association's timeless mission every year.", "A three-to-five-year plan removes the need for monitoring between cycles."],
    "The association can undertake a major formulation cycle every three to five years while reviewing and updating the plan annually. Timing should fit its governance and competition rhythms. Rolling review preserves direction without treating the original plan as immutable.")
add(4, "factual_anchor",
    "Which activities appear in UEFA Grow's eight-step strategy-development process?",
    ["Preparation and a kick-off workshop.", "Analysis of the current situation.", "Drafting followed by review and refinement.", "Implementation and monitoring planning."],
    ["Immediate budget execution before objectives and actions are identified."],
    "UEFA Grow moves from preparation and team mobilisation through analysis, workshops and drafting. Feedback is used to refine and finalise the strategy before implementation and monitoring plans are completed. It is a staged development process, not instant execution.")
add(4, "application",
    "A strategy team is beginning from scratch and wants a productive kick-off. What should it accomplish according to UEFA Grow?",
    ["Excite and inspire the team."],
    ["Approve the final budget before analysing the situation.", "Replace role allocation with informal volunteering.", "Publish a completed strategy during the first meeting.", "Conduct performance control before a strategy exists."],
    "The kick-off workshop is designed to mobilise the team and establish ownership. Preparation has already identified what and who are needed, while the workshop assigns roles and responsibilities. Final strategy and budget decisions come later.")
add(4, "application",
    "Draft strategic objectives are ready for stakeholder testing. Which next steps follow the Grow process?",
    ["Seek feedback to test and improve the draft.", "Refine the strategy before finalisation."],
    ["Move directly to execution and prohibit revisions.", "Return to defining the organisation's legal existence.", "Treat feedback as part of year-end financial reporting only."],
    "Review and refinement deliberately test a draft before it is finalised. Feedback can expose weak assumptions or improve feasibility. Implementation planning should follow a robust finalisation rather than bypassing scrutiny.")

# PDF page 5 / handbook pages 74-75: analytical model and feedback loop.
add(5, "factual_anchor",
    "Which three logical steps structure the chapter's analytical model of strategic management?",
    ["Strategic analysis.", "Strategy formulation through generation and choice.", "Strategic planning, communication and implementation."],
    ["Abolition of performance measurement.", "Permanent separation of goals from resource allocation."],
    "The model begins with analysis, moves to formulation and choice, and ends with planning, communication and implementation. Performance measurement connects implementation back to renewed analysis. The stages are distinct but form a continuing cycle.")
add(5, "application",
    "Elite sporting results have deteriorated sharply. How should this influence the next strategy review?",
    ["Include the shortfall in situation and performance analysis.", "Keep the strategy connected to the association's current context.", "Generate options that address the performance issue.", "Assess the issue before selecting domains and initiatives."],
    ["Exclude past performance so that the vision remains aspirational."],
    "Past and current performance are the starting context for strategy. Ignoring a major elite shortfall would detach formulation from the association's real situation. The issue should inform analysis and the later generation and prioritisation of options.")
add(5, "explanation",
    "Which statements correctly distinguish situation and performance analysis from internal analysis?",
    ["Situation and performance analysis examines results already achieved."],
    ["Internal analysis measures only last season's competition results.", "The two analyses are identical and should be merged.", "Situation analysis ignores organisational problems and challenges.", "Internal analysis excludes resources and staff capabilities."],
    "Performance analysis asks how the association has been doing and what problems define its context. Internal analysis instead appraises resources, capabilities, strengths and weaknesses, so it focuses on potential. Confusing them can hide the difference between poor results and limited capacity.")
add(5, "application",
    "A participation strategy has been drafted without consulting clubs, schools or families. Which analytical corrections are required?",
    ["Identify the relevant external stakeholders and their interests.", "Examine trends, opportunities and threats affecting participation."],
    ["Replace external analysis with financial reporting alone.", "Assume stakeholder preferences are irrelevant once a goal is approved.", "Treat stakeholder mapping as an internal resource audit."],
    "External analysis establishes whose preferences and interests affect a domain and what trends shape it. Participation initiatives cannot work reliably without that knowledge. Internal financial information is useful but does not substitute for understanding stakeholders.")
add(5, "application",
    "An association has identified ten attractive domains but lacks resources to improve all of them. Which formulation choices must it make?",
    ["Choose the domains on which to focus.", "Set domain-specific SMART goals.", "Select initiatives for navigating each chosen domain."],
    ["Allocate identical resources to every domain.", "Postpone all prioritisation until after implementation."],
    "Domain selection determines where scarce resources should be concentrated. Domain navigation then chooses initiatives for achieving goals within each selected area. Equal investment everywhere would avoid the strategic choice the model requires.")
add(5, "explanation",
    "What management value is created by the feedback loop in the strategic-management model?",
    ["It turns performance information into input for renewed analysis.", "It supports yearly or quarterly review and adjustment.", "It tests whether chosen initiatives are producing expected results.", "It helps update strategy when outcomes diverge from expectations."],
    ["It guarantees that environmental change can no longer affect the plan."],
    "Measurement and control close the loop between implementation and the next situation analysis. Managers can learn from results and revise goals or initiatives when needed. The loop creates adaptability, not certainty about the environment.",
    [{"pdf_page": 5, "bbox": {"left": 0.05, "top": 0.11, "right": 0.46, "bottom": 0.37}, "caption": "Figure 2.4: Key elements of a strategic management system"}])

# PDF page 6 / handbook pages 76-77: mission, context and performance.
add(6, "factual_anchor",
    "What is the strategic role of an association's mission and core values?",
    ["They provide the starting reference for assessing mission-related performance."],
    ["They prescribe every departmental action for one season.", "They replace the need for measurable goals.", "They are rewritten whenever a quarterly KPI changes.", "They define only the association's commercial profit target."],
    "Strategy ultimately helps the organisation fulfil its mission, so mission and values frame the initial assessment. They describe purpose and the standards against which relevant performance is judged. They do not replace specific goals or action plans.")
add(6, "application",
    "The association wants to improve football's positioning and reputation. Which approach best defines the organisational context?",
    ["Include relevant functions such as competitions, grassroots, communications and marketing.", "Exclude units that have no immediate bearing on the objective."],
    ["Restrict the analysis automatically to the communications department.", "Involve every unit equally regardless of relevance.", "Define context only after the strategy has been implemented."],
    "Organisational boundaries should capture all functions needed for the objective while removing irrelevant scope. Reputation is cross-functional, so several units contribute. Focused breadth is different from either departmental isolation or indiscriminate inclusion.")
add(6, "explanation",
    "Why should the organisational context be established before strategy formulation?",
    ["It clarifies whether the process covers the whole association or selected units.", "It removes material that is irrelevant to the question.", "It makes cross-functional analysis more focused."],
    ["It guarantees that stakeholders will agree with every resulting priority.", "It fixes the same boundary for all future strategic issues."],
    "Context sets the boundary of the analysis and identifies who and what must be involved. A clear boundary improves focus without assuming every issue has the same organisational reach. It does not eliminate disagreement or the need to revisit scope.")
add(6, "application",
    "A refereeing unit wants to develop its own objectives while remaining within the association's corporate direction. Which statements apply?",
    ["The strategic-management framework can be used at unit level.", "The unit should define a context appropriate to refereeing.", "Unit goals should remain connected to the wider mission.", "Relevant resources and performance indicators should be analysed."],
    ["Only the president and general secretary may use strategic planning tools."],
    "The framework is scalable from the whole association to a unit, project or individual level. Refereeing can therefore define its own context, evidence and goals while remaining aligned with the corporate mission. Unit planning is not a claim of organisational independence.")
add(6, "explanation",
    "Why is performance assessment in a national association more complex than in a profit-maximising company?",
    ["The association's purpose usually extends beyond maximising shareholder value."],
    ["National associations have no measurable outcomes.", "Financial indicators are legally prohibited in football.", "Sporting and stakeholder outcomes cannot be related to a mission.", "Only national-team rankings may be considered."],
    "A company focused on shareholder value can emphasise financial returns, while an association serves a broader mission. Its performance must therefore be judged against sporting, participation, operational and stakeholder goals as well as finances. Complexity does not mean measurement is impossible.")
add(6, "application",
    "Management wants an impartial view of whether the association is meeting its goals efficiently. Which evidence should it use?",
    ["Mission-related key performance indicators.", "Comparisons with targets or previous results."],
    ["Only anecdotal views from the senior team.", "Only the size of the association's cash balance.", "Indicators selected without reference to organisational purpose."],
    "KPIs translate mission and goals into evidence that can be compared over time or against targets. Benchmarking similar organisations can add a relative perspective. Financial data alone cannot represent a multi-purpose football association.")

# PDF page 7 / handbook pages 78-79: KPIs, urgent challenges and time horizons.
add(7, "factual_anchor",
    "Which categories organise the handbook's example performance indicators for national associations?",
    ["Financial performance.", "Operational performance.", "Stakeholder satisfaction."],
    ["Astrological forecasting.", "Personal preferences of a single executive."],
    "The example groups indicators into financial, operational, internal and stakeholder-satisfaction categories. That arrangement gives management a broader picture than one headline measure. Categories should reflect the association's mission and operating context.")
add(7, "application",
    "A recession causes sponsors to withdraw urgently from grassroots programmes. How should this affect strategy formulation?",
    ["Treat the loss as a priority problem requiring a focused response.", "Consider an ad hoc process for the overriding issue.", "Shorten the action horizon where the crisis demands it.", "Allow the urgent challenge to shape the scope of the wider review."],
    ["Preserve every original funding initiative regardless of feasibility."],
    "A severe funding shock may override the normal planning rhythm and require rapid action. The association should define the urgent issue, timeframe and response while considering its effect on the broader strategy. Rigidity would leave the plan detached from available resources.")
add(7, "explanation",
    "What determines an appropriate time horizon for a strategic plan?",
    ["The nature and urgency of the problems being addressed."],
    ["A universal rule that every plan must last exactly one season.", "The preference to avoid external and internal analysis.", "The number of pages in the public strategy document.", "The assumption that every objective changes at the same speed."],
    "The horizon must fit the issue: urgent shocks may require months, normal plans often cover three to five years, and structural goals may need a decade or more. A clear horizon also determines suitable evidence and tools. One duration cannot serve every challenge.")
add(7, "application",
    "An association is preparing a 12-year participation strategy. Which analytical choices are appropriate?",
    ["Examine long-term demographic trends.", "Examine long-term economic and technological trends."],
    ["Base the entire strategy only on this month's registrations.", "Use the same assumptions as a three-month crisis plan.", "Avoid stating a time horizon until implementation is complete."],
    "A long-range participation strategy should assess structural forces likely to change demand and delivery over time. Demographic, economic and technological trends are therefore especially relevant. Current data remain useful, but cannot be the only basis for a 12-year direction.")
add(7, "application",
    "A board wants a balanced UEFA Grow performance dashboard. Which choices demonstrate the intended breadth?",
    ["Include participation and performance measures.", "Include facilities and revenue measures.", "Include governance, women's football and enabling-capacity measures."],
    ["Measure only senior men's national-team ranking.", "Exclude engagement because it is outside association performance."],
    "UEFA Grow proposes eight complementary areas rather than a single sporting or financial measure. Performance, participation, facilities, revenue, engagement, governance and regulation, women's football and enablers create a rounded assessment. A narrow elite result would miss organisational capacity and wider mission outcomes.")
add(7, "explanation",
    "How do context, performance and problems combine to define the scope of a strategy review?",
    ["Context establishes the organisational boundary.", "Performance evidence shows how the association is doing.", "Problems identify issues requiring action.", "Urgency and scale help establish the time horizon."],
    ["Scope is fixed entirely by the previous strategy's title."],
    "The review scope emerges from who and what is included, the evidence of current results and the challenges to resolve. Their importance and urgency also shape duration and priorities. A previous document may inform the process but cannot define it alone.")

# PDF page 8 / handbook pages 80-81: external analysis and domain mapping.
add(8, "factual_anchor",
    "What does the chapter mean by a national association domain?",
    ["An activity area involving an exchange with a defined stakeholder group."],
    ["Any department shown on the payroll.", "Only an activity that generates commercial profit.", "A geographical confederation recognised by FIFA.", "A temporary committee with no stakeholder exchange."],
    "A domain is defined through an activity and an exchange of goods, services or money with identifiable stakeholders. It is not simply an organisational box or commercial market. The concept helps map the association's diverse external environment.")
add(8, "application",
    "When mapping the sponsorship domain, which elements should the strategy team identify?",
    ["The controlled advertising space or rights offered by the association.", "The sponsor as a customer exchanging money for a defined service."],
    ["Only the internal staff member who signs invoices.", "Youth players as the sole stakeholders in every sponsorship exchange.", "An assumption that rights and obligations need no definition."],
    "Sponsorship is a comparatively clear domain because the service, stakeholder and exchange can be specified. The association offers controlled rights and the customer supplies money under defined obligations. Mapping should make that value exchange explicit.")
add(8, "application",
    "A youth-development review identifies only young players as stakeholders. Which additions are supported by the handbook?",
    ["Clubs that deliver membership and training.", "Parents who influence participation and safety perceptions.", "Schools and local government that shape access and development."],
    ["Commercial broadcasters as the only remaining stakeholder.", "No additions, because the player is the only party to the exchange."],
    "Youth development involves a network rather than a simple buyer-seller exchange. Clubs, parents, schools and local government can all influence participation and value creation. Excluding them would weaken both external analysis and later action design.")
add(8, "explanation",
    "Why can a relatively small national association still require complex domain analysis?",
    ["It may operate across many sporting, social, regulatory and commercial areas.", "Its democratic and political structure adds internal complexity.", "Its stakeholders exchange different forms of value.", "Its activity set can be broader than that of a similarly sized company."],
    ["Employee count determines that every activity has the same market dynamics."],
    "A staff of 30 to 70 may still support a dozen or more very different areas. The association combines democratic governance with diverse exchanges and stakeholders. Organisational size therefore understates strategic complexity.")
add(8, "application",
    "A strategy team has an unstructured list of hundreds of activities. What is a useful first step in external analysis?",
    ["Group activity into a manageable map of principal domains and subdomains."],
    ["Treat every task as an equally important strategic domain.", "Copy another association's map without adapting it.", "Begin allocating budgets before identifying stakeholders.", "Limit the map to areas that collect commercial revenue."],
    "Domain mapping organises a complex environment into principal areas of activity and related subdomains. The handbook suggests that associations often identify roughly 8 to 15 main areas, without prescribing a universal template. The map must reflect the association's own exchanges and mission.")
add(8, "explanation",
    "Why does the chapter prefer the term 'domain' to 'business unit' for many association activities?",
    ["Some activities create non-commercial value for stakeholders.", "Many relevant exchanges are not conventional markets."],
    ["National associations are prohibited from generating revenue.", "A domain can never contain a commercial subdomain.", "The term removes the need to identify services and stakeholders."],
    "National associations operate in areas such as youth development, refereeing and participation where value is broader than profit. Domain is therefore a more flexible label for stakeholder exchanges. Commercial activity can still form a domain or subdomain.")

# PDF page 9 / handbook pages 82-83: focus, KSFs and PEST.
add(9, "factual_anchor",
    "Which questions are used to identify key success factors within a domain?",
    ["What drives stakeholder behaviour?", "How can the association meet stakeholder expectations?", "How might it meet those expectations better than alternatives?"],
    ["Which unit has the largest historical budget?", "How can stakeholder preferences be avoided?"],
    "KSF analysis begins with the determinants of stakeholder behaviour and satisfaction. It then asks how the association can meet those expectations, potentially better than other organisations. Historical budget size does not by itself identify what makes a domain successful.")
add(9, "application",
    "Parents report that youth football feels unsafe and poorly communicated. Which actions follow the KSF example?",
    ["Improve clubs' communication with parents.", "Set standards for the atmosphere in youth teams.", "Train and communicate with youth coaches.", "Address access and confidence through clubs, schools and local authorities."],
    ["Concentrate exclusively on elite national-team branding."],
    "The KSF approach converts drivers of stakeholder satisfaction into conditions for success. Safety, communication, atmosphere and access require action with clubs, coaches, schools and authorities. Elite branding would not address the identified youth-domain expectations.")
add(9, "explanation",
    "How does domain mapping support later strategy formulation?",
    ["It creates the structure within which domain-specific goals and initiatives can be developed."],
    ["It determines one identical strategy for every domain.", "It removes the need to compare expected results and costs.", "It guarantees that all domains receive priority.", "It replaces analysis when domain dynamics remain unclear."],
    "The domain map defines coherent areas for goals, evidence and action. Management can then compare expected results, costs, investment and revenue when choosing focus. Unclear domains may still require KSF or PEST analysis.")
add(9, "application",
    "Managers understand who participates in a new recreational-football domain but cannot explain what drives success. Which analysis should they undertake?",
    ["Identify what determines stakeholder behaviour and satisfaction.", "Translate those expectations into key success factors."],
    ["Move directly to a final public strategy without further analysis.", "Use the association's overall profit as the only success factor.", "Assume success factors are identical across every country and domain."],
    "KSF analysis is designed for a domain whose success dynamics are uncertain. It links stakeholder motives to what the association must do well. The resulting insight makes initiatives easier to formulate and more likely to be effective.")
add(9, "factual_anchor",
    "Which dimensions form the PEST framework used in external analysis?",
    ["Political trends.", "Economic trends.", "Social trends."],
    ["Tactical match formations.", "Employee personality types."],
    "PEST covers political, economic, social and technological trends. It provides a disciplined scan of external forces affecting a particular domain. Match tactics and personality assessment belong to different analytical questions.")
add(9, "application",
    "An ageing population and rapid growth of new social platforms are changing youth participation. Which responses fit PEST analysis?",
    ["Reassess how social trends affect stakeholder expectations.", "Examine how technological change alters communication.", "Review the domain's key success factors.", "Adapt participation and parent-engagement initiatives accordingly."],
    ["Preserve the existing approach because success factors never change."],
    "PEST analysis is useful because external trends can change the conditions for success. Demography may alter participation needs while technology changes how clubs communicate with families. The association should update KSFs and actions rather than freeze them.")

# PDF page 10 / handbook pages 84-85: implications and internal resources.
add(10, "factual_anchor",
    "How should the scope of a PEST analysis normally be defined?",
    ["Around a specific domain and its relevant geography."],
    ["As one global list applied unchanged to every domain.", "Only around factors controlled by the association.", "By excluding trends that vary between countries.", "By the structure of the finance department alone."],
    "PEST factors have meaning in relation to a domain and place. Immigration, economic disparity or technology may be crucial in one country or activity and minor in another. A generic global list can therefore obscure strategic relevance.")
add(10, "application",
    "External analysis reveals a new public-funding opportunity and a threat from falling lottery contributions. What should analysts do next?",
    ["Record potential actions for exploiting the opportunity.", "Record potential responses to the threat."],
    ["Discard ideas until after the final strategy is approved.", "Treat opportunities as internal capabilities.", "Assume every recorded idea must automatically be funded."],
    "Analysis should generate preliminary implications, issues and options while the evidence is fresh. These ideas enter a repository for later comparison and prioritisation. Recording an option does not mean that it has already been selected.")
add(10, "explanation",
    "What is the main purpose of internal strategic analysis?",
    ["Appraise resources the association can access or control.", "Assess staff and organisational capabilities.", "Identify strengths and weaknesses that affect execution."],
    ["Predict every political trend outside the association.", "Measure past results without considering future potential."],
    "Internal analysis asks whether the association has the resources and capabilities to execute its goals. It identifies strengths to leverage and weaknesses to address. External trends and past performance are related but distinct analytical tasks.")
add(10, "application",
    "A board adopts an ambitious stadium strategy without checking funding, land or delivery expertise. Which risks should management recognise?",
    ["The goals may be disconnected from controllable resources.", "Execution may fail because required capabilities are absent.", "Stakeholders may lose confidence in unrealistic commitments.", "The project could consume goodwill and resources without producing results."],
    ["A well-worded goal makes resource appraisal unnecessary."],
    "Goals must be grounded in financial, tangible and human capability. Unrealistic commitments can damage results and stakeholder trust, not merely miss a target. An internal appraisal should precede final commitment.")
add(10, "factual_anchor",
    "Which item is one of the four resource categories used for a national association's internal analysis?",
    ["Intangible assets."],
    ["Political trends.", "Stakeholder satisfaction drivers.", "Competition results as a complete category of resources.", "External threats controlled by another organisation."],
    "The four categories are financial resources, tangible assets, intangible assets and human resources. Intangibles include brands, reputation, know-how and databases. Political trends and stakeholder drivers belong to external analysis.")
add(10, "application",
    "The association is cataloguing its fan database, reputation, training centre and staff expertise. How should these resources be classified?",
    ["The database and reputation are intangible assets.", "The training centre is a tangible asset."],
    ["All four are financial resources because they may have value.", "Staff expertise is an external political trend.", "The training centre is a stakeholder preference rather than a resource."],
    "Classification clarifies what the association controls and how it can be measured or developed. Data and reputation are intangible, facilities are tangible, and staff expertise belongs to human resources. Potential financial value does not collapse these distinctions.")

# PDF page 11 / handbook pages 86-87: scoring and strengths/weaknesses grid.
add(11, "factual_anchor",
    "Which statements describe the scoring dimensions in the strengths and weaknesses analysis?",
    ["Importance reflects a resource's value for success.", "Relative strength reflects how well the association performs in that resource.", "Relative strength can use comparable measurable indicators."],
    ["Importance is always produced by a scientific formula.", "A score of five on a ten-point relative-strength scale means unique superiority."],
    "The grid uses strategic importance and relative strength as separate dimensions. Importance often relies on informed judgement linked to KSFs, while relative strength can be benchmarked objectively. An average score indicates ordinary rather than exceptional capability.")
add(11, "application",
    "Senior managers disagree sharply about how important the fan database is to strategic success. Which assessment practices are appropriate?",
    ["Ask more than one person to score importance.", "Relate importance to the domain's key success factors.", "Use a mathematical average or seek an agreed score.", "Separate importance from the current quality of the database."],
    ["Let the database owner set both scores without challenge."],
    "Importance is judgemental, so multiple perspectives reduce individual bias. The discussion should connect the resource to the relevant KSFs and distinguish value from current relative strength. Ownership alone is not an objective scoring method.")
add(11, "application",
    "An association wants to score its relative strength in training methods. What evidence is most useful?",
    ["Comparable indicators from similar national associations."],
    ["The personal confidence of one coach only.", "The resource's strategic importance score copied into the strength column.", "A PEST list of national currency trends.", "The age of the strategic plan document."],
    "Relative strength concerns comparative performance in a resource or capability. Where measures exist, equivalent data from similar associations provide a sound basis. Strategic importance and external trends answer different questions.")
add(11, "explanation",
    "How should the four quadrants of the strengths and weaknesses grid be interpreted?",
    ["High-importance strong resources are key strengths.", "High-importance weak resources are key weaknesses."],
    ["Every low-importance weakness requires first priority.", "A strong but irrelevant resource is automatically a strategic priority.", "Relative strength alone determines strategic value."],
    "The grid combines value for success with comparative capability. High-importance areas deserve attention as strengths to leverage or weaknesses to repair. Low-importance resources may be superfluous strengths or irrelevant weaknesses rather than priorities.")
add(11, "application",
    "Facilities are crucial to the strategy but score very poorly in relative strength. Which conclusions are justified?",
    ["Facilities constitute a key weakness.", "A strategy dependent on current facilities carries execution risk.", "Capability-building or an alternative delivery route should be considered."],
    ["Facilities should be ignored because weakness implies low importance.", "The association should label them a superfluous strength."],
    "High importance combined with low relative strength defines a key weakness. Management should either strengthen the capability, source it differently or reconsider a strategy that relies on it. Ignoring the gap would reduce strategic robustness.")
add(11, "explanation",
    "Why does strengths-and-weaknesses analysis improve assessment of strategy robustness?",
    ["It tests whether proposed initiatives rely on capabilities the association actually possesses.", "It highlights important weaknesses that may block execution.", "It identifies valuable strengths that can support success.", "It distinguishes strategically relevant gaps from low-value deficiencies."],
    ["It proves that every strategy based on a current weakness must be abandoned permanently."],
    "Robustness depends on matching ambition to the association's real capability profile. The grid shows where execution is supported, exposed or distracted by irrelevant resources. A weakness may be developed or outsourced rather than making action permanently impossible.")

# PDF page 12 / handbook pages 88-89: development choices, vision and SMART goals.
add(12, "factual_anchor",
    "What broad choices does the chapter give for addressing an important internal weakness?",
    ["Build the capability internally."],
    ["Ignore it while continuing to depend on it.", "Redefine it automatically as a strength.", "Transfer the association's mission to a supplier.", "Remove performance control from the strategy."],
    "An association can develop the capability itself or outsource the relevant task when appropriate. The decision depends on core competence and how feasibly internal capacity can be built. Relabelling or ignoring a key weakness leaves the execution risk unchanged.")
add(12, "application",
    "Travel logistics are a key weakness and specialist expertise lies outside the association's core competence. Which responses are sensible?",
    ["Evaluate outsourcing to a qualified travel agency.", "Retain clear responsibility for how the outsourced service supports strategic goals."],
    ["Build an internal travel company regardless of cost or expertise.", "Assume outsourcing removes the need to manage performance.", "Abandon every goal involving travel."],
    "Outsourcing is appropriate when external expertise is stronger and internal capability is difficult or inefficient to build. The association still needs standards, accountability and alignment with its goals. Outsourcing transfers delivery, not strategic responsibility.")
add(12, "explanation",
    "Which steps form the structured approach to strategy formulation after analysis?",
    ["Formulate a vision and SMART goals.", "Generate ideas for achieving the goals.", "Prioritise goals and actions."],
    ["Implement every idea before comparing it.", "Replace goals with a list of available resources."],
    "Formulation converts analytical insight into direction, possible action and explicit choices. A vision and SMART goals establish outcomes, idea generation produces routes, and prioritisation selects among them. Implementation comes after these choices.")
add(12, "application",
    "A workshop is confusing the association's mission, five-year vision and annual goals. Which distinctions should the facilitator establish?",
    ["Mission describes the organisation's enduring purpose and activity.", "Vision states intended achievement for a defined period.", "Detailed goals give operational direction within the vision.", "SMART goals make desired results specific and assessable."],
    ["Mission, vision and goals are interchangeable labels for the annual budget."],
    "Mission answers why the association exists, vision describes a time-bound destination, and goals specify what must be achieved. SMART formulation makes goals measurable and actionable. Treating the concepts as synonyms weakens both communication and planning.")
add(12, "factual_anchor",
    "Which quality belongs to a SMART goal in the chapter?",
    ["It is measurable."],
    ["It is deliberately open-ended.", "It avoids a time reference.", "It is unrelated to the association's mission.", "It is impossible with current or developable resources."],
    "SMART goals are specific, measurable, attainable, relevant and time-bound. In simpler terms they should be ambitious but realistic, measurable and aligned with mission and strategy. Open-ended aspirations are insufficient for an action plan.")
add(12, "application",
    "A committee proposes the goal 'develop youth participation'. How should it improve the goal?",
    ["Specify the target population and desired result.", "Add a measurable target and deadline."],
    ["Remove all numbers so the goal remains flexible.", "Replace relevance with a list of unrelated activities.", "State a result beyond any plausible resource capacity."],
    "The generic aspiration does not tell managers what success looks like or when it should be achieved. A defined population, measurable result and deadline create a basis for initiatives and control. The target should remain ambitious, relevant and attainable.")

# PDF page 13 / handbook pages 90-91: coordinated planning, ideas and prioritisation.
add(13, "factual_anchor",
    "Which features characterised the Danish association's coordinated planning framework described in the chapter?",
    ["A four-year planning cycle.", "Goals organised around main domains.", "Common templates based on SMART goals."],
    ["Untracked working groups created whenever any committee wished.", "Plans containing actions but no targets or measures."],
    "The DBU replaced a proliferation of hard-to-coordinate groups with a common cycle, domain structure and SMART template. Committees specified objectives, measures, yearly targets and actions. Standardisation supported coordination without requiring every plan to be written centrally.")
add(13, "explanation",
    "How should a time-bound organisational vision relate to domain-specific strategic issues?",
    ["The vision should provide an overall direction for the planning period.", "Domain goals should translate that direction into specific outcomes.", "The vision should take account of important issues revealed by analysis.", "The vision may serve as the heading for a three-to-five-year strategic plan."],
    ["Every domain issue must be copied word-for-word into the vision statement."],
    "Vision is broader than the issues arising in individual domains, but it cannot ignore them. It supplies a shared destination while domain-specific goals and actions provide precision. This is why a vision often names a planning period yet still needs SMART goals beneath it.")
add(13, "application",
    "The association enters a new esports-related domain where internal experience is limited. What is the most suitable idea-generation response?",
    ["Use experience and benchmarks from other organisations."],
    ["Rely only on staff who have never worked in the domain.", "Skip external analysis and copy the first visible initiative.", "Fund every idea before assessing impact.", "Treat a lack of internal knowledge as evidence that no strategy is possible."],
    "A new domain may exceed internal expertise, making external benchmarks, peer learning and consultants useful. Those inputs should still be tested against the association's analysis and goals. Outside experience informs judgement rather than replacing it.")
add(13, "explanation",
    "Which sources can be used to generate actions for achieving SMART goals?",
    ["Experience within the association.", "Experience from other organisations and external specialists."],
    ["Random action without a defined goal.", "Only initiatives already funded in the current budget.", "A rule prohibiting workshops, sprints or design thinking."],
    "The chapter presents internal expertise, external experience and dedicated idea-generation methods as three routes. The right route depends on the novelty and complexity of the domain. Ideas are generated broadly before being compared and prioritised.")
add(13, "application",
    "Supporters report a poor national-stadium experience, but the causes are unclear. Which design-thinking actions fit the handbook example?",
    ["Map the supporters' journey to and through the stadium.", "Identify pains that should be removed.", "Identify gains that could improve the experience."],
    ["Begin with a predetermined solution and avoid user experience evidence.", "Restrict analysis to the final score of the match."],
    "Journey mapping makes the experience visible from the supporter's perspective. Pains identify problems while gains suggest value-creating additions. This method broadens action generation beyond internal assumptions or sporting results.")
add(13, "explanation",
    "Which statements distinguish domain selection from domain navigation?",
    ["Domain selection chooses the areas on which the association will focus.", "Domain navigation chooses initiatives within a selected area.", "Both are necessary because resources are limited.", "Both domains and initiatives should be prioritised."],
    ["Navigation means distributing identical initiatives across every domain."],
    "Selection answers where the association will concentrate its effort, while navigation answers how it will pursue goals there. Scarcity requires both levels of choice. Equal activity across all domains would avoid rather than perform prioritisation.")

# PDF page 14 / handbook pages 92-93: matrix and implementation supports.
add(14, "explanation",
    "What question is the impact/complexity matrix designed to help management answer?",
    ["Which domains or initiatives deserve priority given expected value and delivery difficulty."],
    ["Which stakeholder has formal voting rights at Congress.", "How to calculate national-team rankings.", "Whether the association needs a mission.", "Which employee should receive every operational decision."],
    "The matrix compares potential impact with complexity, cost, effort or risk. It supports prioritisation after ideas have been generated. It is a decision aid for strategic focus rather than a governance or competition-ranking tool.",
    [{"pdf_page": 13, "bbox": {"left": 0.59, "top": 0.53, "right": 0.92, "bottom": 0.79}, "caption": "Figure 2.6: Impact/complexity matrix"}])
add(14, "application",
    "An initiative has high impact and low complexity. How should the association normally treat it?",
    ["Prioritise it as a quick win.", "Check that its impact genuinely supports mission, vision or goals."],
    ["Reject it because low complexity implies low value.", "Delay it until every high-complexity project is complete.", "Evaluate it only by historical budget size."],
    "High-impact, low-complexity initiatives are the matrix's low-hanging fruit. They normally deserve priority, provided the impact assessment is aligned with strategic outcomes. Ease alone is insufficient if the initiative does not advance the mission.")
add(14, "application",
    "A proposed national training centre has high expected impact and high complexity. Which next steps fit the chapter?",
    ["Investigate and plan the project further.", "Develop a business case or business plan.", "Assess feasibility before committing major resources."],
    ["Classify it automatically as a quick win.", "Reject it solely because it is complex."],
    "High-impact, high-complexity projects may be strategically important but require deeper investigation. A business plan can test cost, risk and feasibility before commitment. Complexity calls for evidence, not automatic rejection or instant execution.")
add(14, "factual_anchor",
    "Which factors are identified as common obstacles to strategy implementation?",
    ["Limited understanding of the strategy.", "Resistance to change.", "Unclear expectations or inadequate experience.", "Weak motivation, control or follow-up."],
    ["The mere existence of written goals and an approved budget."],
    "Implementation fails when the people responsible do not understand, accept, know how to perform or remain accountable for the strategy. These are human and organisational conditions. A written plan helps, but cannot execute itself.")
add(14, "explanation",
    "Why may an association prepare different versions of its written strategic plan?",
    ["Internal users often need deadlines, deliverables and operational detail."],
    ["Public versions must disclose every confidential operational dependency.", "Different audiences require contradictory missions.", "A public document replaces internal implementation planning.", "The plan should remain unwritten until all initiatives are complete."],
    "Writing the strategy is the starting point for communication, but audiences need different levels of detail. Internal versions can support delivery, while public versions may explain direction more generally. The core strategy should remain coherent across versions.")
add(14, "explanation",
    "How should organisational structure respond to strategic priorities?",
    ["Priority domains should have a clear place in line functions or appropriate units.", "Major strategic change may justify revising the organisation chart."],
    ["The structure should remain fixed regardless of strategy.", "Every temporary initiative requires an independent legal association.", "Line functions should contain unrelated activities to prevent specialisation."],
    "Structure should support rather than obstruct the chosen strategy. Clear line functions improve focus, coordination and control, and new priorities may justify new units. Reorganisation should follow genuine strategic needs rather than every minor action.")

# PDF page 15 / handbook pages 94-95: control, MBO and conclusion.
add(15, "application",
    "A quarterly report shows that a strategic participation programme is behind schedule and overspending. What should management do?",
    ["Investigate the deviation early.", "Take corrective action before year-end.", "Report progress against both budget and strategic objectives."],
    ["Wait for consolidated annual accounts before discussing it.", "Remove the objective from the strategy without analysis."],
    "Structured reporting creates an early-warning mechanism for both financial and strategic performance. Managers can diagnose the deviation and agree corrective action while recovery remains possible. Waiting until year-end sacrifices that principal advantage.")
add(15, "explanation",
    "What trade-off should be considered when designing reporting and control systems?",
    ["Frequent structured reporting can reveal problems early.", "Corrective action becomes possible before deviations grow.", "A formal system requires additional time and resources.", "Controls can cover strategic goals as well as financial measures."],
    ["The cheapest system is always the most strategically effective."],
    "Formal reporting improves visibility and timely intervention but costs more to operate. The association should choose a cadence and scope proportionate to its needs. Control is broader than finance and can monitor progress against strategic objectives.")
add(15, "explanation",
    "What is management by objectives in the chapter's implementation framework?",
    ["Translation of organisational goals into individual objectives and responsibilities."],
    ["Replacement of strategic goals with personal preferences.", "A method for eliminating manager-employee progress discussions.", "A reporting system limited to consolidated year-end accounts.", "A rule that objectives cannot influence incentives."],
    "MBO links the strategy of a unit to the annual objectives of managers and employees. Progress can be reviewed with line managers and corrective action taken. Incentives may be connected to results, but alignment and accountability are the central purpose.")
add(15, "application",
    "A department's strategic goal is to increase licensed coaches, but employee objectives concern unrelated media activity. Which corrections follow MBO?",
    ["Translate the department goal into relevant individual objectives.", "Review progress periodically with line managers."],
    ["Keep the unrelated objectives because individual plans need no strategic link.", "Measure progress only after the strategic period ends.", "Assign responsibility without clarifying expected results."],
    "Individual work should contribute visibly to the unit's strategic objectives. Relevant annual targets and periodic discussion create accountability and permit correction. Unrelated objectives weaken the link between organisation and execution.")
add(15, "explanation",
    "Why should an association adapt strategic-management formats and timing to its own context?",
    ["Associations differ in structure and operating cycles.", "Governance elections and major competitions may shape timing.", "A fitted system is more likely to be usable and sustained."],
    ["The fundamental need for analysis disappears in some associations.", "Adaptation means omitting goals and implementation."],
    "The methodology is transferable, but processes must fit the association's structure, culture and calendar. A system may take time to mature around elections or competitions. Adaptation concerns practical design, not abandonment of analytical fundamentals.")
add(15, "explanation",
    "Which principles form a strong oral summary of effective strategic management?",
    ["Understand the internal and external environment deeply.", "Appraise resources and capabilities objectively.", "Formulate clear goals and a path to achieve them.", "Allocate sustained effort to implementation and control."],
    ["Assume that a well-written strategy will implement itself."],
    "Effective strategy combines evidence, realistic self-assessment, clear choices and disciplined execution. Each element supports the next and performance feedback renews the cycle. A document alone cannot substitute for people, resources, communication and follow-up.")


# Second-pass distractor review: these replace weaker alternatives with nearby,
# source-grounded misconceptions that avoid lexical giveaways and absurd claims.
REVISED_DISTRACTORS = {
    1: ["Commit the full academy budget before defining success measures.", "Use the next competition cycle as the decisive evaluation period.", "Fund facilities first and postpone staffing and analytical work.", "Rotate resources between the academy and senior team as results fluctuate."],
    2: ["It concentrates on optimising established operating procedures.", "It commits resources after senior management has selected an initiative intuitively.", "It is formulated at corporate level and translated operationally without departmental strategy."],
    3: ["Faster approval of routine operational expenditure.", "Greater central control of departmental work by the executive committee."],
    4: ["Retain central approval for cross-departmental decisions while delegating routine administration."],
    5: ["A portfolio of departmental objectives compiled for the annual budget.", "A forecast describing the environment in which a long-term goal may be pursued.", "A statement of organisational purpose supported by broad aspirations.", "A resource plan showing how approved activities will be financed."],
    6: ["It spreads resources evenly so each domain maintains a minimum activity level.", "It favours reversible short-term initiatives until additional resources become available.", "It compensates for resource constraints by narrowing analysis to financial measures."],
    7: ["Departmental plans negotiated separately and reconciled during annual budgeting.", "Central review of decisions that exceed each unit's delegated financial authority."],
    9: ["By linking motivation primarily to performance-related pay.", "By communicating resource allocations while leaving their strategic rationale with managers.", "By defining departmental outputs without linking them to mission-level outcomes.", "By using performance controls as the principal explanation for strategic priorities."],
    10: ["The retained strategy consultant.", "The association's principal commercial partners.", "The department heads responsible for implementation."],
    11: ["Classify the target miss as an implementation problem before reassessing the environment.", "Maintain the approved initiatives while adjusting their delivery timetable."],
    12: ["A three-to-five-year plan reviewed when its final targets become due."],
    13: ["Set provisional budgets before reviewing internal and external changes.", "Begin formal monitoring after proposed updates receive executive approval.", "Draft detailed updates before the review meeting and use the meeting to ratify them.", "Ask principal funding partners to approve changes before executive review."],
    15: ["Use annual reviews to revise the vision while retaining fixed operational targets.", "Concentrate monitoring in the final year so interim variation does not destabilise direction."],
    18: ["Begin implementation of low-risk elements while the draft is being reviewed.", "Return the draft to senior management for approval before wider feedback.", "Collect feedback as part of the first implementation report."],
    19: ["Strategic budgeting, operational delivery and retrospective evaluation.", "Independent cycles for goal setting, resource allocation and performance reporting."],
    21: ["Internal analysis compares recent results with targets to identify underperformance.", "The two analyses use the same evidence but report it to different governing bodies.", "Situation analysis establishes the future capabilities available for implementation.", "Internal analysis concentrates on achieved results while performance analysis estimates potential."],
    23: ["Maintain baseline investment across the ten domains and prioritise within each one.", "Pilot initiatives in several domains before deciding which domains deserve focus."],
    24: ["It confirms the original strategic assumptions once implementation data are available."],
    25: ["They translate purpose into detailed instructions for the current planning cycle.", "They provide a broad substitute for measurable departmental objectives.", "They are revised when performance indicators reveal a significant target gap.", "They frame the association's sporting and commercial ambitions for the planning period."],
    26: ["Define the context around communications because that unit owns reputation management.", "Include the leadership team and each unit affected by the resulting resource allocation.", "Use the draft initiatives to determine which organisational units belong in the analysis."],
    27: ["It secures early agreement from the stakeholders included in the process.", "It creates a stable corporate boundary that can be reused for subsequent reviews."],
    28: ["The unit should contribute evidence and actions while corporate leaders retain responsibility for setting its objectives."],
    29: ["Associations rely mainly on qualitative outcomes that cannot support systematic measurement.", "Financial indicators provide the neutral baseline against which sporting outcomes should be converted.", "Mission-related sporting outcomes are assessed separately from organisational performance.", "Senior national-team and club results provide a sufficient proxy for the wider mission."],
    30: ["A structured consensus assessment produced by the senior team.", "Financial results compared with budget and previous seasons.", "Indicators selected from common association practice before checking their link to purpose."],
    31: ["Public and media visibility.", "Board and committee satisfaction."],
    32: ["Protect the approved grassroots portfolio and meet the shortfall through temporary reserves."],
    33: ["The association's presidential term and competition calendar.", "The availability of reliable external and internal data.", "The publication cycle for the association's annual report.", "The time needed for departments to absorb planned expenditure."],
    34: ["Extrapolate recent registration growth across the planning period.", "Use the assumptions prepared for the association's short-term financial contingency plan.", "Choose the horizon after preferred participation initiatives have been costed."],
    35: ["Use sporting performance as the headline measure and treat organisational capacity as explanatory data.", "Combine engagement and participation because both measure public involvement."],
    36: ["The previous plan's focus areas and duration establish the default scope for the next cycle."],
    37: ["An organisational function responsible for delivering a strategic objective.", "An activity area with a measurable financial return for the association.", "A group of related activities serving stakeholders within a defined territory.", "A programme governed by a standing committee and funded through the strategic plan."],
    38: ["The commercial department as provider and sponsors as recipients of brand exposure.", "Spectators as the principal stakeholder because sponsors purchase access to their attention.", "The inventory of rights, leaving contractual obligations to the later implementation plan."],
    39: ["Commercial partners that can finance club delivery and player recruitment.", "Clubs as delivery partners, with families and public bodies treated as contextual influences rather than stakeholders."],
    40: ["A smaller workforce reduces internal complexity but makes external domains more dependent on shared processes."],
    41: ["Group tasks according to the department currently responsible for them.", "Use UEFA Grow's example domain map as the initial structure and preserve its categories for benchmarking.", "Estimate budgets for activity clusters before defining their stakeholder exchanges.", "Prioritise revenue-producing clusters and map development activities during formulation."],
    42: ["Association activities combine commercial and regulatory functions within the same organisational unit.", "Commercial activity is better described as a business unit, while development activity forms a domain.", "The term emphasises strategic responsibility rather than the exchange of value with stakeholders."],
    44: ["Use a national youth-football image campaign to strengthen parental confidence before changing club practices."],
    45: ["It provides a standard strategic approach that can be adapted across the mapped domains.", "It supplies enough environmental structure to rank domains from stakeholder size alone.", "It establishes the domain portfolio that should receive baseline strategic attention.", "It identifies where external analysis can be replaced by internal capability assessment."],
    46: ["Draft several initiatives from staff experience and use stakeholder research to refine them.", "Use financial sustainability as the first KSF, then add stakeholder factors.", "Transfer KSFs from a comparable participation domain before testing local differences."],
    47: ["Participation trends.", "Strategic capability trends."],
    48: ["Adjust communications to the new platforms while retaining the existing participation offer and KSFs."],
    49: ["Use a national PEST scan and apply the same priority trends within each domain.", "Concentrate on trends that the association can influence through its strategy.", "Exclude geographically uneven trends until reliable national data are available.", "Define the scope around the association's principal organisational functions."],
    50: ["Hold the ideas outside the option repository until their financial impact is quantified.", "Treat the funding opportunity as an additional financial resource in the internal analysis.", "Advance both responses to formulation because they arose from validated external analysis."],
    51: ["Estimate how external political changes will affect the association's resources.", "Explain past performance through the resources used during the previous cycle."],
    53: ["External opportunities.", "Stakeholder satisfaction.", "Competition performance.", "Regulatory exposure."],
    54: ["Record the database, reputation and facility as assets, while treating expertise as an operating cost.", "Classify staff expertise with intangible know-how because neither is a physical asset.", "Treat the training centre as a capability because it enables programme delivery."],
    55: ["Importance is derived from measurable performance relative to peer associations.", "A midpoint relative-strength score indicates that the resource makes an average contribution to strategic success."],
    57: ["A panel assessment by experienced technical staff within the association.", "The resource's KSF-based importance score adjusted for recent performance.", "National trends in coach education participation and employment.", "The development budget allocated to training-method research."],
    58: ["A low-importance weakness becomes a priority when its relative-strength score is especially poor.", "A strong resource merits strategic investment even when its contribution to KSFs is limited.", "Relative strength determines the quadrant, while importance is used later for initiative ranking."],
    60: ["It identifies current capability gaps that should be excluded from the strategic plan."],
    61: ["Reduce strategic dependence on the capability.", "Reclassify the weakness as non-core.", "Transfer strategic accountability to a supplier.", "Manage the exposure through tighter control."],
    62: ["Build a small internal travel unit so the association retains direct control of a strategically important service.", "Use a specialist supplier and rely on its service standards in place of association-level controls.", "Redesign travel-dependent activities to reduce the need for specialist logistics."],
    63: ["Pilot promising ideas before formalising the vision and goals.", "Prioritise available resources first and formulate goals that fit the resulting allocation."],
    65: ["It is directionally aspirational.", "It is measurable but undated.", "It captures a valuable opportunity.", "It requires future capabilities."],
    66: ["Specify a range of acceptable participation growth without fixing a target date.", "Define the activities the committee will deliver and use completion as the success measure.", "Set a stretch target based on the leading association's participation rate before assessing attainability."],
    68: ["The vision should summarise the highest-priority issue from each strategic domain."],
    69: ["Use internal staff to preserve ownership, supplementing their experience after ideas are drafted.", "Adapt a highly visible initiative from a leading association as the initial strategy.", "Fund small pilots across the idea portfolio and compare their early results.", "Delay action generation until the association has recruited in-house domain specialists."],
    70: ["Actions proposed during analysis before a SMART goal has been selected.", "Initiatives with identified funding because feasibility is part of idea generation.", "Structured benchmarking sessions focused on replicating peer-association practice."],
    72: ["Navigation allocates a common package of initiatives across the selected domains."],
    73: ["Which stakeholders should participate in deciding strategic priorities.", "How alternative initiatives compare on expected financial return.", "Whether the proposed initiative is consistent with the association's stated mission.", "Which department has the authority and capacity to sponsor an initiative."],
    74: ["Investigate it further because low complexity may indicate that its impact has been overstated.", "Schedule it after high-complexity projects so early resources support structural change.", "Prioritise it when a similar initiative performed well in the previous planning cycle."],
    75: ["Treat it as a quick win if sufficient funding is currently available.", "Place it behind lower-impact initiatives until implementation capability improves."],
    77: ["Use the public version to disclose deliverables while keeping strategic rationale internal.", "Adapt mission and vision wording to the interests of each audience.", "Use the public plan for stakeholder communication and maintain implementation detail in departmental budgets.", "Publish the plan after initial implementation has confirmed that its goals are feasible."],
    78: ["Retain the existing structure and coordinate new priorities through cross-functional projects.", "Create a project unit for each strategic initiative so line functions remain operationally focused.", "Combine related and unrelated activities in larger line functions to reduce management layers."],
    80: ["A light reporting system is strategically preferable because it protects staff time for implementation."],
    81: ["Assignment of individual targets based on professional-development needs rather than unit goals.", "A periodic performance discussion focused on employee capability and conduct.", "A year-end reporting process that attributes unit outcomes to responsible managers.", "A bonus framework linked to departmental results without negotiated individual objectives."],
    82: ["Retain the media objectives but add a departmental participation KPI to each employee review.", "Review progress when the annual departmental result is available.", "Assign coach-development tasks and allow employees to define the expected results during delivery."],
}

for question_number, replacements in REVISED_DISTRACTORS.items():
    question = QUESTIONS[question_number - 1]
    correct = set(question["answer"]["correct_options"])
    false_positions = [index for index in range(5) if index not in correct]
    assert len(false_positions) == len(replacements), question_number
    for position, replacement in zip(false_positions, replacements):
        question["options"][position] = replacement


def main() -> None:
    assert len(QUESTIONS) == 84, len(QUESTIONS)
    categories: dict[str, int] = {}
    for question in QUESTIONS:
        category = question["oral_exam_category"]
        categories[category] = categories.get(category, 0) + 1
    assert categories == {
        "application": 38,
        "explanation": 29,
        "factual_anchor": 17,
    }, categories
    payload = {
        "schema_version": 1,
        "library_key": "uefa_cfm",
        "chapter_number": 15,
        "session_title": "Chapter 2 - Strategic management",
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
