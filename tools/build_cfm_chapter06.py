"""Build the staged Chapter 6 UEFA CFM event-and-volunteer bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "Event-and-volunteer.pdf"
OUTPUT = Path("data/cfm_imports/chapter_06_event_and_volunteer_management.json")
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
            "handbook_pages": [164 + 2 * page, 165 + 2 * page],
        },
        "page_crops": crops or [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 168-169: event goals, stakeholders and four phases.
add(2, "application", "A host association is defining success for a one-off international event. What should be its primary management goal?",
    ["Deliver the expected-quality experience to stakeholders while strengthening shared emotion, brand and reputation."],
    ["Maximise the territorial legacy before confirming the event-time service standard.", "Give the rights holder's requirements priority over stakeholder experience.", "Use event size as the principal indicator of brand and reputational value.", "Treat operational delivery and social impact as separate projects with different leadership."],
    "The primary goal is successful stakeholder delivery at the expected quality, combined with emotion, brand profile and organiser reputation. Sustainable impact and legacy form an important secondary goal that should be integrated, not allowed to displace delivery. Size and rights-holder compliance are inputs rather than complete definitions of success.")
add(2, "explanation", "How do one-off and recurrent football events differ in organisational terms?",
    ["A one-off event may have a different organiser and host territory on each occasion.", "A recurrent event may require structures that support longer-term development."],
    ["A one-off event has a smaller territorial impact than a recurrent event.", "A recurrent event uses a temporary organising structure for each delivery cycle.", "A one-off event involves international bodies, whereas recurrent events are national."],
    "One-off status concerns the temporary event and host configuration, while recurrence creates a continuing development context. Territorial scale and governing level do not define the distinction. The organising structure should therefore reflect the event's duration and future.")
add(2, "factual_anchor", "Which phases form the chapter's generic football-event model?",
    ["Concept.", "Preparation.", "Event-time operations."],
    ["Rights acquisition.", "Commercial exploitation."],
    "The four phases are concept, preparation, event-time operations, and closure and legacy. Their duration varies with event size and nature. Rights and commercial work occur within the phases rather than constituting separate phases.")
add(2, "application", "A local organising structure is bringing together partners that have never worked together. Which practices reflect the stakeholder approach?",
    ["Identify the relevant public, private, football and civil-society actors.", "Understand their expectations and different approaches.", "Coordinate them through an event-specific structure.", "Build collaboration around the quality and legacy goals."],
    ["Assign stakeholder priority according to the resources each partner commits."],
    "The stakeholder approach manages a network of parties whose expectations and methods differ. The local structure coordinates them around common event outcomes. Resource contribution matters, but stakeholder priority cannot be reduced to funding or assets.")
add(2, "explanation", "Why is an ad hoc local organising structure needed for many major events?",
    ["It coordinates a temporary and complex stakeholder network for the specific event."],
    ["It places partner bodies within a single event-governance hierarchy.", "It gives public partners a common legal identity for the event.", "It transfers delivery risk away from established football bodies.", "It brings partner expertise into functions controlled directly by the event organiser."],
    "The temporary structure gives the event a focal point for coordination, responsibilities and stakeholder expectations. It cooperates with permanent bodies rather than replacing them. Volunteer management remains an HR responsibility, and reputational effects extend beyond the structure's life.")
add(2, "application", "A host wants its event to leave economic, environmental and social benefits. Which planning choices follow the chapter?",
    ["Define the intended sustainable impact during the concept phase.", "Carry sustainability through delivery, closure and legacy planning."],
    ["Assess sustainability after operational quality has been demonstrated.", "Use ISO 20121 as a certification of the event's eventual legacy.", "Assign legacy to local authorities because benefits arise in the host territory."],
    "Sustainable impact should be designed from the outset and managed across the event lifecycle. ISO 20121 offers a management framework for economic, environmental and social responsibility, but it does not certify a future legacy. The host territory and organisers need collaborative ownership.")
add(2, "explanation", "Why does the chapter use volunteer management to illustrate each event phase?",
    ["Volunteers contribute to event delivery.", "Their programme demonstrates HR processes across the lifecycle.", "Their involvement can create social impact and legacy."],
    ["Volunteer programmes define the governance model for the local organising structure.", "Volunteer numbers provide a common quality measure across functional areas."],
    "Volunteer management spans strategy, planning, recruitment, training, operations, celebration and legacy. It therefore illustrates the phases while showing how human capital can benefit the community. Governance and quality still require wider event-management measures.")

# PDF page 3 / handbook pages 170-171: local organising structure and project activation.
add(3, "application", "A one-off event is setting up its local organising structure. Which design decisions are essential?",
    ["Choose an appropriate legal status.", "Define governance arrangements.", "Allocate core functions to managers.", "Connect the temporary structure with permanent partner bodies."],
    ["Base the structure on the organisation chart used for the host's recurrent competitions."],
    "The LOS should be tailored to the event's requirements, legal context, governance and functional responsibilities. It must also cooperate with permanent partners despite its short life. An existing chart may inform design, but copying it would ignore the one-off mission and stakeholder network.")
add(3, "explanation", "Why is an operational organisation chart important when setting the event in motion?",
    ["It gives visible form to responsibilities and relationships in the event project."],
    ["It fixes the structure so later phases can focus on delivery rather than governance.", "It ranks functional areas according to their event-time authority.", "It converts stakeholder agreements into individual action plans.", "It shows the rights holder which functions the host can manage independently."],
    "The chart makes the temporary organisation and allocation of responsibility visible. It supports discussion, coordination and later action planning but does not freeze the project or replace agreements. Authority and independence still depend on governance and the event's contracts.")
add(3, "factual_anchor", "Which bodies may be represented as external parties on an event steering group?",
    ["Police.", "City authorities."],
    ["Match spectators.", "Competing team captains.", "Merchandise customers."],
    "A steering group may include external operational partners such as police, city authorities, hotels and transport representatives. They contribute expertise and coordination needed to keep the project on track. Spectators, captains and customers are stakeholders but are not the examples given for steering-group membership.")
add(3, "application", "Several event partners use different terminology and interpret responsibilities differently. Which steps should occur before detailed action plans?",
    ["Bring the interested parties together.", "Agree shared concepts and language.", "Allocate responsibilities within a joint vision."],
    ["Let functional areas retain their own terminology until operational manuals are drafted.", "Ask the steering group to assign tasks before partners discuss the event concept."],
    "A common vision and language allow partners to understand their contribution and responsibility. Collective and individual action plans follow that alignment. Drafting tasks or manuals first would embed different interpretations in the project.")
add(3, "explanation", "What should distinguish a structure for a recurrent event from one for a one-off event?",
    ["It should account for long-term organisational development.", "It should retain learning across delivery cycles.", "It should still allocate event-specific functions clearly.", "It should connect recurring responsibilities with permanent bodies."],
    ["It should preserve the first cycle's governance because partner continuity reduces structural risk."],
    "Recurrence creates a future beyond the immediate delivery, so structure and learning need a longer horizon. Event-specific accountability remains necessary, while links with permanent organisations become especially valuable. Continuity does not remove the need to review governance as the event develops.")
add(3, "application", "The organiser wants the steering group to keep the project on track. What should the group do?",
    ["Meet regularly to review direction and coordination."],
    ["Manage the daily work schedules of functional-area teams.", "Approve operational exceptions during event-time delivery.", "Replace bilateral coordination with decisions taken at board meetings.", "Take ownership of functions shared between the rights holder and the LOS."],
    "The steering group provides regular oversight and cross-party coordination. Daily execution remains with project and functional managers under allocated responsibilities. Oversight should reinforce rather than absorb operational ownership.")
add(3, "explanation", "What is the value of showing phased responsibility in an operational organisation chart?",
    ["It clarifies how roles shift from strategy and planning into delivery.", "It identifies where the rights holder and local structure share or separate responsibility."],
    ["It makes responsibility stable across phases so the project needs fewer handovers.", "It assigns authority according to how early a function appears in the timeline.", "It allows the steering group to resolve role conflicts after implementation begins."],
    "A phased chart makes transitions, shared ownership and handovers explicit over the project timeline. Responsibility may change as the event moves towards on-site delivery. Early visibility reduces, rather than postpones, role conflicts.")

# PDF page 4 / handbook pages 172-173: business plan and project dimensions.
add(4, "application", "Which contents should a robust event business plan address?",
    ["The LOS vision, concept and goals.", "Legacy and sustainability.", "Stakeholder responsibilities and contractual context."],
    ["Detailed event-time briefings for each operational post.", "Final stakeholder satisfaction results used to justify the original assumptions."],
    "The business plan explains the goals, why they are achievable and how the project will deliver them. It covers governance, context, risks, resources, budget, milestones and major functional plans. Event-time briefings and final results belong to later operational and closure documents.")
add(4, "explanation", "Why is a sports event a project in the chapter's framework?",
    ["It pursues a fixed objective.", "It operates within a defined time frame.", "It mobilises limited resources.", "It must provide an established service level."],
    ["It uses a temporary workforce whose responsibilities end after closure."],
    "Fixed purpose, deadline, limited resources and expected service make an event a project. A temporary workforce is common but does not define project status, and recurrent events can still use project methods. The framework focuses on constraints and deliverables.")
add(4, "factual_anchor", "Which project dimension describes the specified deliverables and services?",
    ["Scope."],
    ["Quality.", "Resources.", "Time.", "Governance."],
    "Scope defines the product to be delivered, including services and deliverables. Quality concerns the level provided to stakeholders, resources are limited inputs, and time defines start and end. Governance shapes control but is not one of the four dimensions in Figure 6.6.")
add(4, "application", "A proposed service enhancement would improve quality but require more budget and threaten the deadline. Which project logic applies?",
    ["Assess the change across quality, resources and time.", "Confirm that the enhanced service remains within the agreed scope."],
    ["Prioritise quality because it is the stakeholder-facing project dimension.", "Use the business plan's contingency allowance as evidence that the deadline remains feasible.", "Treat the enhancement as a new deliverable after operational preparation begins."],
    "The four dimensions are interconnected, so a quality change affects resources, time and possibly scope. Contingency does not prove feasibility, and adding a deliverable without change control can destabilise the project. The decision requires an explicit trade-off against the fixed objective.")
add(4, "explanation", "Which event features increase the need for disciplined project management?",
    ["A temporary organisation in an unfamiliar environment.", "Irreversible decisions in a one-off process.", "Uncontrollable variables and high uncertainty."],
    ["Positive cash flow before the main delivery period.", "A critical path that shortens when more functions work in parallel."],
    "Events combine novelty, temporary structures, irreversible choices, uncertainty, early investment and a critical path. Cash flow is commonly negative before returns, and parallel activity does not remove dependencies on the longest path. Discipline helps manage this leap into the unknown.")
add(4, "application", "The organiser must invest heavily before event income arrives. Which response follows the event-project analysis?",
    ["Plan financing and cash flow as a core project constraint.", "Sequence commitments against available income and deadline risk.", "Include financial assumptions and mitigation in the business plan.", "Monitor how borrowing costs affect the budget."],
    ["Delay project commitments until revenue is received so financial exposure remains within budget."],
    "Events often have negative early cash flow, yet waiting for income can create technical delay. The organiser must balance financing, timing and risk in the business plan. Blanket postponement would protect cash while endangering the non-negotiable delivery date.")
add(4, "explanation", "What makes the four project dimensions interconnected?",
    ["A decision in one dimension changes the feasible balance of the others."],
    ["Scope determines quality, while time and resources remain planning constraints.", "Quality can be adjusted during delivery without changing the project definition.", "Resources determine the service level after the deadline has been fixed.", "Time becomes independent once the critical path has been approved."],
    "Scope, time, quality and resources form one project balance. A new deliverable, reduced budget or delayed task can change the attainable service and schedule. Approval of a plan does not make any dimension independent of later change.")

# PDF page 5 / handbook pages 174-175: operational planning, gates and temporal tools.
add(5, "application", "A functional-area plan lists activities but leaves accountability and location unclear. Which additions are required?",
    ["Specify who performs each activity.", "Specify where and how it will be done."],
    ["Add the expected legacy of each activity before assigning responsibility.", "Replace activity dates with project gates shared by the functional areas.", "Assign the work to the steering group until the operational structure is complete."],
    "An operational plan should answer what, who, when, where and how. Missing ownership and execution context prevents coordinated action even if activities are listed. Gates and legacy may inform the plan but do not replace task-level accountability.")
add(5, "explanation", "What is the purpose of the event master plan?",
    ["Establish the long-term planning framework.", "Set milestones for the event.", "Give the project coherence as an evolving whole."],
    ["Freeze the project definition before functional managers are appointed.", "Translate each deliverable into an event-time operations manual."],
    "The master plan is the LOS's first management tool and evolves as the project develops. It organises milestones and the route towards delivery while preserving overall coherence. Detailed operations manuals and frozen deliverables come later within that framework.")
add(5, "factual_anchor", "Which statements correctly describe roadmap terms used in the chapter?",
    ["A gate is a synchronisation and decision point.", "A deliverable is an agreed tangible product.", "A main task may involve several projects.", "A main task closes with a gate."],
    ["A working visit is the point at which a deliverable becomes part of project scope."],
    "Gates align projects and decisions, deliverables are agreed outputs, and a main task coordinates work that closes at a gate. Working visits may support review and audit but do not define when an output enters scope. The distinctions make roadmap status auditable.")
add(5, "application", "A venue layout must be agreed by several projects before detailed infrastructure work proceeds. Which management device is most appropriate?",
    ["Create a shared gate at which the layout deliverable is reviewed and frozen."],
    ["Place the layout on the Gantt chart after infrastructure work starts so actual constraints are visible.", "Let each project approve its own layout component before the steering review.", "Treat the layout as a main task whose deliverable is defined at event-time operations.", "Use the working visit as the formal decision point without a separate project gate."],
    "A gate synchronises related projects around an agreed deliverable and authorises the next work. Separate approvals risk incompatible assumptions, while late definition would create rework. A visit may provide evidence but the gate carries the coordinated decision.")
add(5, "explanation", "How does a Gantt chart support event preparation?",
    ["It places tasks and responsibilities against the project timeline.", "It makes sequence, overlap and progress visible."],
    ["It defines the quality standard attached to each project deliverable.", "It replaces the master plan once functional tasks have start dates.", "It prioritises risks according to the duration of the affected task."],
    "A Gantt chart is a temporal model showing the functional structure and path towards the deadline. It supports coordination, progress review and deadline decisions. Quality, risk priority and the overall master framework still require their own analysis.")
add(5, "application", "A pandemic disrupts the established event roadmap. Which planning responses follow the chapter?",
    ["Update milestones and gates around the revised delivery date.", "Re-sequence recruitment, training and operational preparation.", "Preserve a coherent view of dependencies across functional areas."],
    ["Retain frozen deliverables because a postponement changes timing rather than scope.", "Create a separate recovery schedule so the approved master plan remains the formal reference."],
    "A master plan is evolving and should reflect material changes in timing, dependencies and assumptions. Postponement may affect deliverables and resource needs as well as dates. A disconnected recovery plan would leave competing sources of project truth.")
add(5, "explanation", "Why are summary temporal tools useful even for less complex events?",
    ["They show the route to the overall deadline.", "They consolidate established planning points.", "They help teams view work in relation to time.", "They support identification of upcoming decisions."],
    ["They make detailed functional plans unnecessary when the event duration is short."],
    "Every event benefits from a visible path to its deadline, scaled to its complexity. A summary chart links milestones and tasks so teams can coordinate and prioritise. It complements rather than replaces detailed plans.")

# PDF page 6 / handbook pages 176-177: time, risk, quality, finance and functional areas.
add(6, "application", "A volunteer-programme task on the critical path is slipping. What should management do?",
    ["Assess the effect on dependent tasks and the fixed event deadline."],
    ["Use available budget contingency before revising the volunteer schedule.", "Move assessment activity into closure so recruitment dates remain unchanged.", "Ask the functional manager to recover time within the quality standard already set.", "Treat the delay as a local issue until it changes an event gate."],
    "Time tools reveal dependencies and allow managers to prioritise decisions before a delay reaches the event. The response should examine downstream tasks, resources, quality and gates together. Waiting for a milestone failure or assuming local recovery understates critical-path risk.")
add(6, "explanation", "Why must event risk management continue through post-event wrap-up?",
    ["New risks can emerge as the project evolves.", "Monitoring and contingency action remain necessary until closure."],
    ["Risk ownership transfers from the LOS to functional managers during delivery.", "Post-event risks concern financial reporting rather than the operational plan.", "A business-plan risk register remains sufficient once implementation begins."],
    "Event uncertainty changes across planning, delivery and closure, so risks need tracking, analysis and contingencies throughout. Both business and operational plans should reflect the live process. Initial registers and ownership structures need updating rather than passive retention.")
add(6, "factual_anchor", "Which outcomes are purposes of a quality management system?",
    ["Increase efficiency.", "Reduce unnecessary costs.", "Increase stakeholder satisfaction."],
    ["Set the event's taxation status.", "Rank functional areas by strategic importance."],
    "Quality management coordinates processes and resources to achieve expected results and service levels. It supports efficiency, cost control, satisfaction and continuous improvement. Taxation and functional hierarchy are separate finance and design matters.")
add(6, "application", "An event receives public funding and private investment. Which financial controls are appropriate?",
    ["Establish taxation and legal accounting obligations early.", "Maintain transparent detailed accounts.", "Prepare for funders to review annual accounts.", "Allow audit rights where required by funding agreements."],
    ["Draw the first budget before confirming taxation status so funding assumptions can be tested."],
    "The organiser needs legal compliance, a clear taxation position and transparent records before reliable budgeting. Public and private funders may require detailed accounts and audits. Testing assumptions does not justify building a budget on unresolved tax treatment.")
add(6, "explanation", "What is the management value of dividing an event into functional areas?",
    ["It creates an expertise-based, tangible and hierarchical description of the project."],
    ["It gives each area an independent project scope and stakeholder set.", "It fixes the same functional structure for events of different sizes.", "It transfers cross-area integration to the steering group.", "It ranks deliverables according to the expertise needed to produce them."],
    "Functional decomposition makes the complex event understandable and manageable by expertise. Areas and sub-functions can be added or omitted for the particular event, while integration remains a project-management task. The structure describes the whole rather than creating independent projects.")
add(6, "application", "A city-based event includes fan zones that are absent from the standard functional-area list. What should the organiser do?",
    ["Add a suitable functional area or sub-function.", "Define its links with safety, mobility, catering and communications."],
    ["Place fan-zone work within cultural programming because the standard list is hierarchical.", "Treat it as a supplier package outside the LOS functional structure.", "Wait for the operations manual before deciding whether the activity needs separate management."],
    "The list is adaptable: organisers may remove irrelevant areas or add activities such as fan zones and city operations. The new scope should be integrated with connected functions. Outsourcing or late documentation does not remove the need for clear ownership.")
add(6, "explanation", "How do ISO 9001 and ISO 20121 differ in the chapter?",
    ["ISO 9001 specifies a quality management system.", "ISO 20121 guides improvement of event sustainability.", "ISO 20121 spans financial, social and environmental performance."],
    ["ISO 9001 defines the stakeholder service level for football events.", "ISO 20121 measures whether a promised event legacy has been achieved."],
    "ISO 9001 addresses the quality system, whereas ISO 20121 supports sustainable event management across economic, social and environmental dimensions. The standards guide systems rather than prescribing a football service level or proving long-term legacy. Organisers still define objectives and measures.")

# PDF page 7 / handbook pages 178-179: strategic notes and volunteer concept planning.
add(7, "factual_anchor", "Which elements belong in a functional-area strategic note?",
    ["Relevant obligations and assumptions.", "Milestones and main risks.", "Minimum service level and required resources.", "Costs and financing arrangements."],
    ["Daily event schedules approved by each team leader."],
    "The strategic note defines scope and objectives, regulatory context, difficulties, milestones, risks, service, resources, costs and local recommendations. It guides the area from the beginning of the project. Daily schedules are later operational tools.")
add(7, "application", "A volunteer programme is being designed within the event strategy. What should the LOS define first?",
    ["The desired social impact and legacy for the host territory."],
    ["The number of volunteers available through partner organisations.", "The training format that functional managers prefer.", "The recognition event that will retain volunteers after closure.", "The recruitment channel with the broadest local reach."],
    "Volunteer strategy sits within the project strategy and expresses the social dimension of sustainability. Desired impact and legacy guide needs, roles, recruitment, training and follow-up. Starting from available people or channels risks building activity without purpose.")
add(7, "explanation", "How should paid staff and volunteers be understood within event HR management?",
    ["Both are selected for expertise and complementary ability.", "Together they form the event workforce."],
    ["Paid staff carry leadership responsibility while volunteers provide supplementary capacity.", "Volunteer assessment belongs to functional areas rather than HR.", "Corporate culture applies to contracted staff because volunteer commitment is temporary."],
    "HR recruits, trains, assesses and rewards the whole workforce while supporting leadership and culture. Paid or unpaid status does not remove the need for expertise, motivation and complementary roles. Functional managers contribute, but HR provides the overarching process.")
add(7, "factual_anchor", "Which sequence appears in the revised EURO 2020 volunteer timeline?",
    ["Applications and interviews.", "Volunteer reconfirmation.", "Training and activation."],
    ["Legacy assessment before the thank-you event.", "Job-specific training before volunteer reconfirmation."],
    "The revised timeline moves through applications, interviews, reconfirmation, training, activation and a thank-you event. Reconfirmation was important after postponement and preceded renewed preparation. Legacy work follows delivery rather than preceding recognition.")
add(7, "application", "How should a volunteer programme translate its strategy into a workable plan?",
    ["Define phases, timings and locations.", "Specify human, financial and material resources.", "Analyse needs for successive and overlapping operations.", "Keep the plan within the established event budget."],
    ["Set volunteer numbers from partner availability before identifying posts and tasks."],
    "Planning turns desired impact into timed, resourced and budgeted activities. Needs analysis identifies real posts and the phases that may run successively or together. Available volunteers do not determine legitimate workforce demand.")
add(7, "explanation", "Why is the concept phase decisive for later event performance?",
    ["It establishes the LOS, project definition, business plan, budget and functional structure."],
    ["It completes operational detail so preparation can concentrate on implementation.", "It transfers project risks into functional strategic notes.", "It fixes volunteer assignments before recruitment begins.", "It confirms stakeholder satisfaction standards through test events."],
    "The concept phase creates the governance and planning foundations on which preparation acts. It defines direction, structure, risk, quality, budget and legacy without pretending every operational detail is settled. Flexibility and later needs analysis remain necessary.")
add(7, "application", "During preparation, a project change is agreed after new information emerges. Which actions are required?",
    ["Document the decision and update the plan.", "Communicate and report the revised status."],
    ["Implement the change within the affected functional area before updating cross-project agreements.", "Preserve the original result record so later debriefing can compare it with the change.", "Ask the steering group to revise the vision because an agreed plan has changed."],
    "Preparation requires action against the plan, complete records, status reporting and implementation of agreed changes in revised plans and agreements. A local change can affect other areas and should not outrun formal coordination. The vision need not change simply because execution adapts.")

# PDF page 8 / handbook pages 180-181: preparation steering and risk process.
add(8, "factual_anchor", "Which areas form the preparation-phase project-management framework in Figure 6.10?",
    ["Budget management.", "Time management and project steering.", "Risk management."],
    ["Media-rights management.", "Legacy communication."],
    "The figure combines budget, time and steering, functional-area management, and risk management. Together they control the main preparation constraints. Rights and legacy activity may appear within functions but are not the four framework areas.")
add(8, "application", "Cash receipts are delayed, but postponing procurement threatens technical readiness. Which approach fits the chapter?",
    ["Assess the financial cost of acting early.", "Assess the technical risk of waiting for income.", "Sequence tasks using both cash-flow and project-status information.", "Escalate the trade-off through the project steering mechanism."],
    ["Use the fixed event deadline to justify early procurement before financing consequences are assessed."],
    "Doing tasks after cash arrives may create technical delay, while acting early may create borrowing costs and financial risk. Steering should balance both constraints against the fixed deadline and available resources. The deadline creates urgency but does not erase financing effects.")
add(8, "explanation", "Why is a steering mechanism essential during event preparation?",
    ["It helps supervision respond to uncertainty while preserving the project's agreed principles."],
    ["It transfers deadline decisions from functional managers to the project owner.", "It converts the master plan into a series of budget approvals.", "It stabilises project status so risks can be reviewed at formal gates.", "It allows resource decisions to follow cash flow rather than technical readiness."],
    "Preparation contains inevitable uncertainty, so managers need a control device that compares status with plan and supports timely decisions. Steering coordinates rather than removes functional responsibility. It monitors cash, technical progress and risk continuously, not just at gates.")
add(8, "application", "Which steps should a project team use when analysing a newly identified event risk?",
    ["Identify and evaluate the risk and its vulnerability.", "Define preventive or corrective actions and assess residual exposure."],
    ["Allocate contingency resources before comparing possible actions.", "Set the action priority from the current risk trend before estimating consequences.", "Close the risk once its initial rating is lower than the functional-area threshold."],
    "The process identifies and evaluates risk, defines actions, then evaluates those actions and residual exposure. Resource allocation follows an informed response choice, and low-rated risks may still need monitoring. The cycle is repeated as planning evolves.")
add(8, "factual_anchor", "Which risk trends are shown in the event risk-management chart?",
    ["An increasing risk trend.", "A stable risk trend.", "A decreasing risk trend."],
    ["A resolved risk status.", "A transferred risk status."],
    "The chart uses upward, horizontal and downward trends and distinguishes satisfactory or resolved status from major issues. It connects trend, current status and decisions. Transfer may be a response but is not a displayed trend category.")
add(8, "application", "A vulnerability cannot be removed through operational design. What should the contingency process do?",
    ["Define measures that reduce the incident's impact.", "Assess the residual risk after those measures.", "Prepare recovery actions if the threat materialises.", "Repeat the analysis as project conditions change."],
    ["Accept the vulnerability once preventive solutions have been exhausted."],
    "Risk cannot be eliminated in full, so contingency planning includes mitigation, recovery and explicit residual exposure. Conditions and action effectiveness need periodic review. Exhausting prevention does not end management responsibility.")
add(8, "explanation", "What balance should project steering maintain during preparation?",
    ["A continuing balance between usable resources, qualitative results and deadlines."],
    ["A balance between budget authority and functional autonomy.", "A balance between preventive and corrective actions for each risk.", "A balance between rights-holder standards and local stakeholder expectations.", "A balance between stable risks and issues escalated to project meetings."],
    "Steering coordinates collective and individual action so resources, quality and time remain compatible. Other tensions may require management, but the chapter identifies this three-way operational balance. Risk charts and meetings provide evidence for maintaining it.")

# PDF page 9 / handbook pages 182-183: project control, functional manuals, budget and volunteer needs.
add(9, "application", "A project review shows a widening gap between the master plan and actual preparation. Which actions belong in the meeting?",
    ["Assess and prioritise the associated risks.", "Decide preventive or corrective actions."],
    ["Revise the master plan after functional managers implement local recovery measures.", "Move unresolved items into the operations manual so event-time teams can manage them.", "Use current status as the new baseline before assessing why the gap arose."],
    "Review meetings compare plan and reality, assess risk, make decisions and update roadmaps. Corrective action should be coordinated before local implementation changes the baseline. An operations manual is not a repository for unresolved preparation gaps.")
add(9, "explanation", "What is distinctive about the project manager's oversight role?",
    ["Maintain technical, financial and temporal objectives.", "Monitor political, social and media developments.", "Connect external events with implementation risk."],
    ["Take operational ownership when a functional area misses its objectives.", "Limit reporting to dimensions the LOS can control directly."],
    "The project manager integrates core delivery constraints with the wider environment that may help or harm implementation. Functional managers retain ownership of their areas while the project manager steers the whole. Uncontrollable developments still require monitoring and response.")
add(9, "application", "A complex event has slow information flow through several management layers. Which design responses fit the chapter?",
    ["Clarify decision-making and reporting channels.", "Use a flatter hierarchy.", "Maintain links through meetings, reports and site visits.", "Integrate administrative, technical and financial information."],
    ["Route cross-functional decisions through the steering group to preserve consistency."],
    "Effective information systems and a flat hierarchy help teams mobilise and decide while preserving coherence. Meetings, reporting and site visits keep dispersed functions connected. The steering group provides oversight but should not become the route for routine cross-functional decisions.")
add(9, "factual_anchor", "Which document describes the processes and actions to be used during event delivery?",
    ["The operations manual."],
    ["The business plan.", "The functional strategic note.", "The master debrief report.", "The project charter."],
    "Functional planning leads to an operations manual that formalises event-time processes and actions. The business plan and strategic note define earlier goals and scope, while the master debrief records learning after delivery. The documents are connected but serve different stages.")
add(9, "explanation", "How should a functional-area manager translate deliverables into team organisation?",
    ["Distribute tasks and responsibilities around the deliverables.", "Establish coordination mechanisms and procedures."],
    ["Define a separate stakeholder strategy for the function.", "Wait for the operations manual before ranking priority issues.", "Set cost and time expectations after team roles are allocated."],
    "Deliverables are time-sensitive parts of the manager's job and should drive task allocation, coordination, rules and procedures. Priority issues and expectations for time, cost and quality need early definition. The function contributes to one project and should not detach its stakeholder strategy.")
add(9, "application", "The organiser wants stronger control of event expenditure. Which measures are supported by the chapter?",
    ["Assign budget authority by area and expense level.", "Use contracts after competitive requests for proposals.", "Track expenses through cost centres."],
    ["Allocate reimbursement responsibility to the central budget holder rather than functional areas.", "Review cash flow after annual reports confirm the grant income received."],
    "Budget authority, tendering, contracts and cost centres make responsibility and expenditure traceable. Reporting provides opportunities to revise budgets and cash flow during the project. Centralising reimbursement or waiting for annual confirmation would reduce timely control.")
add(9, "factual_anchor", "Which budget-management measures help address early negative cash flow and event materials?",
    ["Value-in-kind support.", "Inventory control.", "Cash-flow analysis.", "Cost-centre tracking."],
    ["Budget authority deferred pending event income."],
    "Value in kind can reduce cash expense, while inventory, cost centres and cash-flow review improve control. These measures make early commitments and materials visible. Delaying authority would obstruct necessary preparation rather than manage it.")

# PDF page 10 / handbook pages 184-185: volunteer recruitment and assignment.
add(10, "explanation", "Why must volunteer recruitment begin with a detailed needs analysis?",
    ["It identifies real tasks, locations and required volunteer categories."],
    ["It estimates the applicant pool needed to sustain the selection ratio.", "It determines which recruitment partners can supply the largest workforce.", "It fixes assignment before functional managers assess field performance.", "It allows organisers to recruit early while job descriptions are refined."],
    "Needs analysis establishes the actual posts, numbers, categories, venues and functional demands. Recruitment and assignment quality depends directly on that evidence. Applicant supply and early timing should serve defined work rather than create roles after people are recruited.")
add(10, "application", "A large volunteer campaign has many applicants but poor role fit. Which changes follow the chapter?",
    ["Use job descriptions as selection criteria.", "Train reliable selectors to assess applicants."],
    ["Increase early recruitment so functional managers have more candidates to reassign.", "Let the volunteer manager finalise assignments before integration to preserve consistency.", "Use automated screening as the decisive assessment for specialist posts."],
    "Recruitment quality comes from needs, job descriptions and capable selectors, not application volume. Face-to-face assessment supports reciprocal commitment and role fit. Final composition benefits from functional evaluation after integration and training.")
add(10, "factual_anchor", "Which stages may appear in the volunteer application and assignment process?",
    ["Online registration.", "Initial selection.", "Video or face-to-face interview."],
    ["Operational briefing before assignment review.", "Legacy commitment assessment before rejection decisions."],
    "The process moves from registration through screening and interviews towards possible assignment, with communication at each decision point. Briefing follows recruitment and integration, while legacy involvement is considered later. The exact process can scale without losing these core stages.")
add(10, "application", "How should the organiser communicate with a large pool of volunteer applicants?",
    ["Use a specialist database linked to applications.", "Send timely status messages at decision points.", "Organise contact groups for targeted communication.", "Coordinate the event website and application forms with the database."],
    ["Keep applicant communication within the recruiting partner's platform until interviews begin."],
    "Targeted logistics and an integrated database support accuracy, scale and timely communication. System messages should accompany progression and rejection decisions. Leaving data and communication fragmented with partners weakens control of the candidate relationship.")
add(10, "explanation", "What does the rule 'recruit early to recruit less' mean?",
    ["Early, needs-based recruitment improves selection and reduces later over-recruitment."],
    ["Early recruitment allows roles to be combined before functional needs are finalised.", "Early applicants are more likely to accept reciprocal commitment with the organiser.", "An early campaign reduces the number of interview stages needed for assignment.", "Recruiting before other events improves retention through reduced competition."],
    "Starting early creates time for targeted recruitment, careful selection and reliable confirmation against real needs. It does not mean recruiting before roles exist or shortening assessment. The purpose is a better-fit workforce rather than a larger safety margin.")
add(10, "application", "A volunteer has passed interviews and is awaiting first experience in the event environment. How should assignment be handled?",
    ["Treat the volunteer manager's placement as a pre-assignment.", "Use integration, training and field evaluation before finalising the role."],
    ["Confirm the assignment from the interview evidence so training can be role-specific.", "Let the functional manager change the role during event delivery after observing performance.", "Keep the applicant unassigned until a test event creates a vacant post."],
    "The volunteer manager commonly pre-assigns, while functional managers evaluate people in the field. Final assignment follows integration, training and evaluation, preferably at test events. Premature confirmation or event-time improvisation increases mismatch risk.")
add(10, "factual_anchor", "Which principle explains why volunteer assignment requires cooperation with functional areas?",
    ["Functional managers assess operational fit before the final team composition.", "HR provides the recruitment and volunteer-management process.", "Assignments depend on the tasks identified in each function."],
    ["Functional managers take control of applicant communication after initial selection.", "HR transfers legal responsibility for volunteers once pre-assignment is complete."],
    "HR and volunteer management provide the process, while functional areas define work and assess fit in practice. Final teams therefore emerge through cooperation. Communication and legal support remain coordinated centrally rather than transferring with a placement.")

# PDF page 11 / handbook pages 186-187: event schedule, delegated decisions and incidents.
add(11, "application", "Which details should an event schedule contain for each activity?",
    ["Date and time.", "Description and location.", "People involved.", "Person responsible."],
    ["Contingency budget for the activity."],
    "The activity plan makes event-time work executable by specifying what, when, where, who participates and who is responsible. Budget contingencies belong to control and escalation arrangements rather than each schedule line. The schedule is then used for briefing, rehearsal and delivery.")
add(11, "explanation", "Why must event-time decision powers be transferred during preparation?",
    ["The event director cannot make each reactive decision quickly enough during delivery."],
    ["Functional managers have greater authority over stakeholder objectives during the event.", "Delegation reduces the need for coordination between functional areas.", "Staff and volunteers need discretion before their roles and responsibilities are finalised.", "Preparation decisions become less relevant once event-time conditions are known."],
    "Delivery is fast and reactive, so defined powers must sit with functional managers, staff and volunteers closest to the issue. Delegation is prepared alongside roles, responsibilities and coordination. It distributes timely authority without fragmenting the event's objectives.")
add(11, "application", "A test rehearsal reveals that staff hesitate over routine venue decisions. Which corrections are appropriate?",
    ["Clarify decision rights at venue and functional-area level.", "Rehearse the schedule with those responsibilities in place."],
    ["Reserve uncertain decisions for the event director until staff gain live experience.", "Add further approval steps so functional managers can document the decision path.", "Let team leaders infer authority from the tasks assigned in the operations manual."],
    "Roles and decision powers should be explicit and tested before the event. Rehearsal exposes gaps in briefing, authority and coordination while there is time to correct them. Live experience is too late to discover who may act.")
add(11, "factual_anchor", "Which incident categories does the chapter distinguish during event delivery?",
    ["Incidents the organiser can manage directly.", "Incidents manageable with a service provider.", "Incidents requiring external emergency services."],
    ["Incidents managed by the rights holder because they affect the competition.", "Incidents transferred to the steering group because they cross functional areas."],
    "Unexpected events differ according to whether the organiser, a provider or external emergency authorities are required. The category determines escalation and control. Competition relevance or cross-functional scope does not by itself transfer incident command.")
add(11, "application", "A bomb threat requires immediate evacuation. Which actions follow the illustrated procedure?",
    ["Notify emergency services and the police commander.", "Inform the facility and matchday safety leadership.", "Broadcast instructions and deploy stewards to critical areas.", "Clear evacuation, assembly and emergency-access routes."],
    ["Keep venue control with the event controller while the police manage the external response."],
    "The event controller initiates the procedure, informs the relevant authorities and coordinates immediate safety actions. Control of the venue is then formally transferred to the police commander managing the incident. Splitting internal and external command at that point would create ambiguity.")
add(11, "explanation", "What is the role of functional-area managers during event delivery?",
    ["Implement formalised processes at the required quality and time."],
    ["Translate emerging stakeholder requests into revised event objectives.", "Escalate cross-functional problems before making a local operational adjustment.", "Apply the formal process until the event director authorises adaptation.", "Prioritise contracted service levels when stakeholder objectives compete for time."],
    "Functional managers sit at the centre of delivery, executing planned processes and responding within delegated authority. Decisions should serve event stakeholder objectives and integrate with other functions. Problems require action and controlled communication rather than isolated optimisation or concealment.")
add(11, "factual_anchor", "Which stakeholders receive particular priority in functional-area implementation?",
    ["Participating teams.", "Athletes."],
    ["Commercial partners.", "Host-city authorities.", "Media-rights holders."],
    "The chapter identifies participating teams and athletes as the most important stakeholders during implementation. Other partners remain significant and have defined requirements. Operational priority reflects the sporting event's core purpose rather than commercial or governmental status.")

# PDF page 12 / handbook pages 188-189: volunteer integration, training and operations.
add(12, "application", "A volunteer cohort is arriving for a medium-sized event. Which integration outcomes should the programme pursue?",
    ["Make volunteers feel welcomed.", "Build a common event identity.", "Strengthen commitment to their mission."],
    ["Confirm final assignments before general training begins.", "Focus onboarding on technical competence because belonging develops through team work."],
    "Integration welcomes volunteers into the organisation and creates identity, belonging and commitment. Technical and job-specific preparation follows within a balanced programme. Assignment and competence matter, but they do not replace the social purpose of onboarding.")
add(12, "explanation", "Why should onboarding, general training and job-specific training receive equal importance?",
    ["Onboarding creates welcome and client focus.", "General training builds shared spirit and ambassador skills.", "Job-specific training develops technical effectiveness.", "Together they prepare both commitment and performance."],
    ["Job-specific training should take priority when volunteers already identify with football."],
    "The three elements address different requirements: belonging, common understanding and role competence. Existing enthusiasm for football does not prove familiarity with the event or its service standards. Balanced preparation makes volunteers committed and effective.")
add(12, "factual_anchor", "Which item is directly assessed alongside the volunteer training plan itself?",
    ["Evaluation of participants."],
    ["Evaluation of the recruitment campaign.", "Evaluation of functional-area staffing ratios.", "Evaluation of the rights-holder service level.", "Evaluation of volunteer legacy before activation."],
    "The chapter calls for assessment and certification and states that both participants and the training plan should be evaluated. Recruitment, staffing and legacy have separate assessments. The training evaluation asks whether people and preparation are ready for their roles.")
add(12, "application", "A functional manager discovers that a trained volunteer is unsuitable for a live role. Which response fits the operating model?",
    ["Coordinate replacement with the volunteer department.", "Maintain support and information for the affected team."],
    ["Reassign the volunteer directly because operational responsibility sits with the functional manager.", "Wait for the daily debrief so replacement does not interrupt execution.", "Ask the overall project manager to approve the individual staffing change."],
    "Functional managers direct volunteers day to day, while the volunteer department remains available for additional people or replacement. Coordination protects records, welfare and team coverage. Operational responsibility does not make staffing support disappear.")
add(12, "explanation", "How are responsibilities divided in operational volunteer management?",
    ["The project manager holds overall operational responsibility.", "Functional-area managers supervise volunteers in their areas.", "The volunteer department supplies schedules, contacts and support."],
    ["Volunteer coordinators direct each functional process during execution.", "Functional managers transfer daily motivation and communication to the central team."],
    "Overall event control remains with the project manager, local supervision with functional managers, and central support with volunteer management. The arrangement combines line responsibility and specialist support. Motivation and communication remain active responsibilities within each volunteer team.")
add(12, "application", "Which elements should a functional manager include in the daily volunteer operating cycle?",
    ["An operational briefing.", "Execution of assigned work.", "An operational debriefing.", "Ongoing motivation, communication and support."],
    ["Certification of each volunteer before the next day's assignment."],
    "The three-step cycle is briefing, execution and debriefing, supported by information, logistics, motivation and loyalty-building. Certification belongs to the wider training process rather than a daily requirement. The cycle converts plans into learning and next-day improvement.")

# PDF page 13 / handbook pages 190-191: event-time learning, closure and debriefing.
add(13, "application", "What is the immediate management value of a daily volunteer-team debrief?",
    ["Identify strengths and changes needed before the next day's activities."],
    ["Create the formal evidence required for the master event report.", "Evaluate each volunteer's contribution to the programme legacy.", "Confirm whether functional objectives should be revised for the next event.", "Transfer unresolved operational issues to the closure-phase review."],
    "Daily debriefing captures live learning and enables next-day correction while the event continues. It can later inform the master report, but its immediate purpose is operational improvement. Legacy and future-event objectives need broader post-event assessment.")
add(13, "explanation", "Why is event-time delivery more demanding than the longer planning phases?",
    ["Activities occur within much tighter timing constraints.", "Unexpected situations require rapid coordinated decisions."],
    ["The event director assumes more decisions as stakeholder visibility increases.", "Functional areas can prioritise execution because quality was defined during preparation.", "The operations manual reduces the need to communicate across areas during delivery."],
    "Years of preparation culminate in a short, hectic delivery period where seconds matter and conditions change. People need clear duties, delegated authority and coordination to respond. Prior planning enables action but does not remove live quality or communication demands.")
add(13, "factual_anchor", "Which tasks belong to the closure and legacy phase?",
    ["Draft a complete event report.", "Assess stakeholder-perceived quality.", "Transfer knowledge for future events."],
    ["Freeze the event business plan against actual results.", "Reassign remaining operational risks to long-term partner organisations."],
    "Closure includes reporting, perceived-quality assessment, knowledge transfer, impact and legacy assessment, and evidence-based corporate communication. The aim is learning, accountability and leverage. Plans are compared with results rather than frozen, and residual issues require explicit resolution.")
add(13, "application", "How should an organiser design its post-event debriefing process?",
    ["Define the process before the event.", "Collect notes during delivery.", "Use functional, team and individual debrief levels.", "Relate positive and negative points to original objectives."],
    ["Delay the first debrief until participants can assess the event with greater objectivity."],
    "Predefinition and contemporaneous notes improve the reliability of debriefing while facts are fresh. Multiple levels provide complementary perspectives tied to objectives. Later reflection may add objectivity, but postponing initial capture risks lost evidence.")
add(13, "explanation", "What is the main trade-off in conducting debriefs immediately after the event?",
    ["Memories are fresh, but participants may lack objectivity."],
    ["Operational facts are complete, but financial information is unavailable.", "Stakeholders are accessible, but team leaders have lost decision authority.", "Recommendations are timely, but future organisers cannot yet be identified.", "The master plan is comparable, but stakeholder expectations have changed."],
    "Immediate assessment benefits from vivid factual recall but can be shaped by emotion and proximity to the event. A planned process, notes and combined evidence help manage that weakness. The trade-off is about recall and objectivity rather than authority or document availability.")
add(13, "application", "A master debrief report will be shared publicly. Which handling choices are appropriate?",
    ["Create one clear record combining individual and functional evidence.", "Present shortcomings carefully while preserving useful learning."],
    ["Remove operational weaknesses that cannot be linked to a missed objective.", "Publish team debriefs separately so stakeholder perspectives remain transparent.", "Focus the public version on positive impact and keep recommendations within the LOS."],
    "The master report should consolidate facts, objectives, roles, results, accounts and recommendations for future use. Wider distribution requires thoughtful presentation, not suppression of material learning. Fragmented or purely promotional reporting weakens the report's reference value.")

# PDF page 14 / handbook pages 192-193: quality, knowledge, impact, legacy and communication.
add(14, "application", "How should an organiser assess stakeholder-perceived event quality?",
    ["Prioritise stakeholders according to event characteristics.", "Ask them to identify and rank expectations.", "Measure satisfaction against each important expectation."],
    ["Use a common quality score so stakeholder groups can be compared directly.", "Assess superiority against competing events before examining intended purpose."],
    "Perceived quality is stakeholder judgement of the event against purpose, expectations and alternatives. Interviews and questionnaires should capture both importance and satisfaction for prioritised groups. A single cross-group score may hide different expectations and service gaps.")
add(14, "explanation", "Which knowledge losses should an event knowledge-management system address?",
    ["Individual expertise lost through turnover.", "Collective capability lost when project teams dissolve.", "Past failures or rejected solutions that are forgotten.", "Skills that remain undiscovered or poorly shared."],
    ["Operational knowledge superseded by a revised event concept."],
    "Event learning is vulnerable when people leave, teams disband, experience is forgotten or skills are invisible across units. A knowledge system captures and transfers that strategic resource so organisations can adapt and improve. Revised concepts may change use, but they do not make earlier reasoning valueless.")
add(14, "factual_anchor", "What does leveraging an event legacy mean?",
    ["Taking deliberate post-event action to obtain desired medium- and long-term territorial results."],
    ["Measuring the economic, social and environmental effects produced during the event.", "Communicating positive impact to justify the original hosting investment.", "Maintaining the LOS until expected legacy indicators are achieved.", "Transferring event knowledge to the next organising structure."],
    "Impact describes effects related to the event, while legacy concerns effects in later years. Leveraging is the action by interested parties to turn event-created dynamics into desired longer-term results. Measurement, communication and knowledge transfer can support leverage but are not the definition.")
add(14, "application", "A host faces criticism that a major event is too costly and environmentally damaging. Which responses fit sustainable event management?",
    ["Assess economic, social and environmental impacts.", "Integrate responsible decisions into planning and implementation."],
    ["Use the expected legacy to offset weak short-term environmental performance.", "Limit impact assessment to priorities controlled directly by the LOS.", "Apply ISO 20121 after the event to determine whether the investment was justified."],
    "Sustainability requires responsible decisions and impact control across economic, social and environmental dimensions. Legacy aspirations do not cancel harmful delivery, and shared territorial effects still require assessment. ISO 20121 guides management throughout the lifecycle rather than serving as a retrospective investment test.")
add(14, "explanation", "What principles should guide corporate communication about event legacy?",
    ["Begin the communication strategy in the concept phase.", "Maintain consistency across stakeholders and phases.", "Support closure messages with facts and figures."],
    ["Frame unresolved negative impacts as areas for future legacy leverage.", "Concentrate legacy communication after the LOS has completed its assessment."],
    "Corporate communication should run across the event lifecycle and reinforce coherent, credible messages with evidence. Closure provides facts, but the strategy and stakeholder relationships begin much earlier. Reframing weaknesses without transparent assessment would damage credibility.")
add(14, "application", "Which objectives should shape the volunteer programme after the final whistle?",
    ["Celebrate volunteer contribution.", "Evaluate programme quality and impact.", "Capitalise on acquired skills and experience.", "Connect volunteers and partners to longer-term social initiatives."],
    ["Retain the event volunteer structure until the next LOS can absorb its trained teams."],
    "Closure moves from celebration and assessment to leveraging skills and networks for social legacy. The event structure may dissolve, so long-term value depends on links with permanent associations, clubs and community partners. Retaining a temporary structure is not the same as creating a sustainable programme.")

# PDF page 15 / handbook pages 194-195: volunteer celebration, evaluation and social legacy.
add(15, "application", "What should a volunteer celebration communicate after the event?",
    ["That volunteers were integral contributors to event and community success."],
    ["That recognition closes the organiser's reciprocal obligation to volunteers.", "That celebration is the programme's principal retention intervention.", "That contribution is valued through priority for future event roles.", "That collective thanks should precede individual programme assessment."],
    "Celebration acknowledges volunteers as champions of the event and community. It is part of an ongoing reciprocal relationship in which people also gained skills, confidence and involvement. Recognition supports, but does not complete, evaluation, follow-up or retention.")
add(15, "explanation", "Why is volunteering described as a reciprocal relationship?",
    ["The event and community receive volunteer effort.", "Volunteers gain satisfaction, skills, confidence and experience."],
    ["The LOS provides recognition in return for unpaid operational labour.", "Functional managers receive flexibility in exchange for volunteer commitment.", "The community provides future opportunities in return for the event's social impact."],
    "Reciprocity is broader than a direct transaction: organisations and communities benefit from contribution, while individuals gain development, belonging and satisfaction. Recognition is important but is one part of that value. Future opportunity should be cultivated rather than assumed as repayment.")
add(15, "application", "How should the LOS evaluate the volunteer programme's perceived quality and social impact?",
    ["Interview volunteers and programme managers.", "Include recruiters, coaches and functional-area managers.", "Review process strengths and weaknesses from management and volunteer perspectives."],
    ["Use commitment and event-image ratings as the overall social-impact measure.", "Let the volunteer department aggregate feedback before functional managers identify process weaknesses."],
    "Evaluation needs perspectives from the people who designed, recruited, trained, managed and experienced the programme. Management review and volunteer questionnaires reveal different strengths, shortcomings and perceived services. A narrow rating or prematurely aggregated view would obscure causes.")
add(15, "factual_anchor", "Which examples represent the four areas of social value in Figure 6.17?",
    ["Pride and well-being.", "Collective identity and social inclusion.", "Health literacy and human capital.", "Social capital and community capacity-building."],
    ["Financial resilience and operational service quality."],
    "The framework crosses individual and collective value with mode of being and capabilities. It includes pride, psychic income, identity and unity, health literacy and human capital, and social capital and capacity. Finance and service quality are event-management outcomes rather than categories in this social-value figure.")
add(15, "application", "A national association wants event volunteers to remain involved in football afterwards. Which initiative fits the FA Football Workforce example?",
    ["Build a programme that recruits, retains, develops and recognises volunteers across football."],
    ["Transfer event volunteers into clubs that report immediate staffing gaps.", "Retain the event database as the main channel for future voluntary assignments.", "Reward experienced volunteers with responsibility for recruiting the next event cohort.", "Use club placement as evidence that the event's social legacy has been achieved."],
    "The Football Workforce aims to recruit more volunteers, retain them, help them work smarter and recognise their contribution. Events can be an entry point into clubs and community development, but placement needs a coherent programme and partnership. Database retention or immediate vacancies do not define long-term human-capital development.")
add(15, "explanation", "How can a one-off event avoid losing the social connections created by its volunteer programme?",
    ["Link volunteers with permanent clubs, associations and community partners.", "Create an ongoing collaborative volunteer strategy beyond the LOS."],
    ["Keep volunteer teams intact until a future event provides comparable roles.", "Assign legacy responsibility to the national association after the LOS dissolves.", "Focus follow-up on volunteers who received event-specific technical training."],
    "A temporary LOS may disappear, so enduring value needs relationships with permanent organisations and continued collaborative activity. The national association can lead but should work with regional bodies, clubs, authorities, universities and sponsors. Preserving event teams or selecting technical specialists is narrower than social legacy.")

# PDF page 16 / handbook pages 196-197: sustainable-event conclusions and global volunteer strategy.
add(16, "application", "Which wider outcomes can a football event create for its host area?",
    ["A stronger shared identity.", "Solidarity and belonging.", "Long-term social and territorial development."],
    ["A legacy proportional to the years spent preparing the event.", "Community cohesion that follows from delivering the expected sporting quality."],
    "Events can bring people together and create identity, solidarity, belonging and development that outlast the competition. These outcomes need intentional leverage and do not arise in proportion to preparation time or operational quality. Delivery creates opportunity, while partners shape the legacy.")
add(16, "explanation", "What does the 'DNA of a sustainable sporting event' illustrate?",
    ["Event organisation and sustainability are intertwined strands.", "Both strands run through concept, preparation, operations and closure.", "Sustainability should influence event design and delivery decisions.", "Closure and legacy remain part of the organising lifecycle."],
    ["Sustainability becomes the leading strand once operational delivery is secured."],
    "The DNA image rejects a separate sustainability workstream added around delivery. Organisation and sustainability wind together through each phase from design to legacy. Neither strand waits for the other to be secured.")
add(16, "factual_anchor", "What is the 'puzzle approach' to resourcing a major event?",
    ["Activate public and local partnerships to combine existing services, expertise and resources."],
    ["Divide the event into self-contained functional pieces managed by specialist partners.", "Use temporary facilities to fill gaps between the rights-holder specification and local capacity.", "Prioritise human-scale services whose costs fit the confirmed event income.", "Transfer dedicated-facility risk to partners with established local operations."],
    "The puzzle approach assembles services, trained people and financial resources through public and local partnerships. It can avoid building dedicated facilities by using existing capacity. Functional division and risk transfer may occur, but the core idea is coordinated activation of complementary partners.")
add(16, "application", "A host lacks specialised staff and facilities for several event services. Which responses follow the human-scale approach?",
    ["Identify partners that already possess suitable services and expertise.", "Build agreements that integrate those resources into the LOS project."],
    ["Reduce the service scope until the host can deliver it through its own structure.", "Create dedicated facilities so rights-holder standards remain under direct control.", "Assign partner-managed services to the steering group because they sit outside LOS capability."],
    "A human-scale event uses partnerships to access existing facilities, trained people and funding while keeping the project coherent. Direct ownership is not the measure of professional delivery. Agreements and project controls integrate partner resources without moving routine management to the steering group.")
add(16, "explanation", "Why do inexperienced organisers still need professional project-management capability?",
    ["They must comply with rights-holder specifications.", "They must respect public and private partner interests.", "They must control quality and budget across a complex system."],
    ["Event-specific methods compensate for limited local knowledge of stakeholders.", "Professional tools transfer delivery risk to the people assigned each functional process."],
    "The LOS faces severe constraints, interdependent stakeholders and fixed standards even when its people have not delivered the event before. Project knowledge and tools structure scope, phases, quality, budget and accountability. They support local judgement rather than replacing it or transferring risk away from leadership.")
add(16, "application", "Which actions would turn event volunteering into a broader human-capital strategy?",
    ["Give volunteers clearly defined and meaningful roles.", "Capture and develop the skills gained through the event.", "Connect trained volunteers with future football and community initiatives.", "Coordinate a national volunteer strategy with permanent partners."],
    ["Preserve the event assignment structure so skills remain comparable across future initiatives."],
    "Volunteers can continue contributing when their event skills, networks and motivation are recognised and linked to future programmes. A national strategy can develop this human capital beyond one LOS. Future initiatives need adapted roles rather than preservation of the event chart.")


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
        "session_title": "Chapter 6 - Event and volunteer management",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
