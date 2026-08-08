"""Build the staged Chapter 3 UEFA CFM operational-management bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "Operational-management.pdf"
OUTPUT = Path("data/cfm_imports/chapter_03_operational_management.json")
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
            "handbook_pages": [94 + 2 * page, 95 + 2 * page],
        },
        "page_crops": crops or [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 98-99: operations, Maslow and motivation.
add(2, "application", "A national association has technically capable staff, but service delivery is inconsistent. What should an operational review examine first?",
    ["Whether people are trained, motivated and equipped to perform their roles."],
    ["Whether the strategic plan contains more long-term objectives than the previous cycle.", "Whether stakeholder services can be transferred to the finance department.", "Whether organisational performance can be inferred from senior-team results.", "Whether process documentation can compensate for gaps in staff motivation."],
    "Operational management concerns the people, processes and structures that deliver services day to day. Technical competence alone is insufficient when motivation or tools are weak. The review should therefore connect workforce conditions to the service failure before redesigning strategy or departmental ownership.")
add(2, "explanation", "Which statements distinguish intrinsic motivation from extrinsic motivation?",
    ["Intrinsic motivation arises from passion or pleasure in the activity.", "Extrinsic motivation is driven by economic, social or psychological factors outside the person."],
    ["Intrinsic motivation is created principally through performance bonuses.", "Extrinsic motivation depends on personal enjoyment of football work.", "Intrinsic and extrinsic motivation describe seniority levels in the organisation chart."],
    "Intrinsic motivation comes from within, such as love of football or enjoyment of contributing. Extrinsic motivation comes from outside incentives or pressures, including economic, social and psychological rewards. Effective management recognises both rather than relabelling one as the other.")
add(2, "factual_anchor", "Which needs appear in Maslow's hierarchy as presented in the chapter?",
    ["Physiological needs.", "Belonging and love.", "Esteem."],
    ["Operational autonomy.", "Strategic alignment."],
    "The hierarchy moves from physiological and safety needs through belonging, esteem and self-actualisation. The model suggests that the motivational value of higher needs depends on lower needs being met. Operational autonomy and strategic alignment may matter at work, but they are not named levels in this framework.")
add(2, "application", "Employees feel insecure about their jobs and perceive unfair treatment, while management launches a creativity prize. Which conclusions follow from the motivation framework?",
    ["Unresolved safety and belonging needs may weaken the prize's effect.", "Fair treatment and team membership need management attention.", "A creativity incentive addresses a higher-order need than the reported concerns.", "The association should diagnose employees' position in the needs hierarchy."],
    ["The prize should be increased because economic value determines the level of need being addressed."],
    "The workforce is signalling safety and belonging concerns, while creativity relates more closely to self-actualisation. A prize may have limited effect until security, fairness and team inclusion improve. The framework is diagnostic; it does not say that a larger financial award moves people past unmet needs.")
add(2, "explanation", "Why can a poorly designed extrinsic incentive damage organisational performance?",
    ["It may encourage behaviour that serves the reward rather than the association's interests."],
    ["It converts intrinsic motivation into a formal job description.", "It shifts employees from esteem needs to physiological needs.", "It makes social and psychological incentives unavailable to volunteers.", "It changes the organisation chart before behaviour can respond."],
    "External incentives influence what people optimise, so a badly chosen measure can reward the wrong behaviour. Economic rewards remain useful, but they cover one part of motivation and must support teamwork and fairness. The risk lies in incentive design, not in the existence of job descriptions or organisational structure.")
add(2, "explanation", "How should a football association sustain the motivation of long-serving volunteers?",
    ["Preserve their connection to the sport and community they value.", "Combine appreciation and belonging with well-designed external incentives."],
    ["Convert voluntary roles into target-based bonus schemes as the primary source of commitment.", "Use promotion opportunities to replace passion as service length increases.", "Separate volunteers from staff so social pressure cannot affect motivation."],
    "Volunteers often begin with strong intrinsic motives: love of football, enjoyment and community. Management should keep that passion alive while ensuring recognition, fairness and appropriate support. Treating financial or promotional mechanisms as a substitute for intrinsic meaning misunderstands the source of commitment.")

# PDF page 3 / handbook pages 100-101: job descriptions and structures.
add(3, "application", "A youth coach is unsure about decision authority and how performance will be judged. Which job-description elements should be clarified?",
    ["Reporting and supervisory relationships.", "Resources and decisions within the role.", "Expected results and performance measures."],
    ["The coach's preferred future department.", "The association's complete project portfolio."],
    "A job description establishes accountability, authority, duties, resources, measures and expected results. These elements give the coach a workable role boundary. Career aspirations and the wider project portfolio may inform management discussions but do not resolve the immediate ambiguity.")
add(3, "application", "A motivated employee consistently contributes useful work beyond the formal role. How should a manager interpret this behaviour?",
    ["It is job expansion beyond the documented baseline.", "It may help the association exceed stakeholder expectations.", "It can indicate that motivation and organisational culture are supporting initiative.", "It should be recognised while role priorities remain clear."],
    ["It demonstrates that the job description should be withdrawn from the role."],
    "The chapter describes job expansion as people doing more than the formal description when motivated. The document remains a necessary baseline, while leadership should recognise useful initiative and keep effort aligned. Expansion is not evidence that role clarity has become unnecessary.")
add(3, "explanation", "What is the relationship between a job description and actual performance?",
    ["The description defines a baseline rather than capturing every nuance of work."],
    ["The description predicts whether an employee will be intrinsically motivated.", "The description replaces the need for performance measures once duties are listed.", "The description sets departmental strategy through individual tasks.", "The description should expand whenever an employee exceeds one target."],
    "A job description sets expectations, authority and results, but real behaviour can expand or contract around that baseline. Motivation and culture influence whether people contribute beyond it. The document supports management; it does not determine motivation or replace evaluation.")
add(3, "factual_anchor", "Which information belongs in a well-formed job description?",
    ["The role's duties and responsibilities.", "The resources available to the role."],
    ["The employee's preferred incentive mix.", "The department's external stakeholder map.", "The next strategic plan's project-selection criteria."],
    "The job description specifies reporting lines, supervision, resources, decisions, responsibilities, measures and expected results. It defines the role rather than the employee's personal motivation or the organisation's project portfolio. Those wider tools should remain connected but distinct.")
add(3, "application", "The association is hosting a one-off international tournament involving commercial, technical, competition and media expertise. Which structure is most suitable?",
    ["A temporary project structure drawing specialists from relevant departments.", "Clear coordination around the event's defined period and deliverables.", "Continued departmental accountability for specialist expertise."],
    ["A new standing department that absorbs the specialist teams after the event.", "Separate departmental plans joined during the final reporting stage."],
    "Special events cut across line departments and have a defined life, so a project structure coordinates the required expertise. Specialists retain their functional knowledge while working to common event outcomes. A permanent restructure or late-stage coordination would be disproportionate and operationally risky.")
add(3, "explanation", "Why does the chapter say that organisational structure follows strategy?",
    ["Departments group responsibility around the association's strategic goals.", "Project structures supplement departments when temporary cross-functional work is required.", "The organisation chart should support how services are intended to be delivered.", "Changes in priorities may require different coordination arrangements."],
    ["Strategy is derived from the departments already shown on the organisation chart."],
    "Structure is a means of implementing strategic priorities, not the source of those priorities. Departments support recurring domains, while projects coordinate temporary cross-functional delivery. Managers should therefore test whether the chart and project arrangements enable the intended strategy.")

# PDF page 4 / handbook pages 102-103: HR tools, recruitment and lifecycle.
add(4, "application", "A bonus scheme rewards individual output but has created rivalry and perceptions of favouritism. Which redesign principles follow from the chapter?",
    ["Align incentives with teamwork.", "Make reward criteria transparent and fair.", "Consider how the scheme interacts with intrinsic motivation."],
    ["Replace performance criteria with manager discretion.", "Move the scheme into the risk-management system."],
    "Extrinsic incentives should encourage collective performance and fair treatment. Poorly designed rewards can erode belonging and make intrinsic commitment harder to sustain. Risk rules serve a different purpose: they constrain harmful conduct rather than allocate positive rewards.")
add(4, "application", "A respected employee repeatedly undermines colleagues while still meeting personal targets. Which operational responses are justified?",
    ["Use transparent information to identify the behavioural risk.", "Apply established conduct rules consistently.", "Protect the wider team's motivation and working environment.", "Consider dismissal when serious rule breaches persist."],
    ["Increase the employee's individual incentive so results compensate for the team impact."],
    "Risk-management systems protect the organisation from conduct that damages others or the working environment. Evidence and transparent rules support fair intervention, with dismissal as an ultimate sanction. Strong individual output does not neutralise a sustained negative effect on team motivation.")
add(4, "factual_anchor", "Which activities form the staff lifecycle presented in the chapter?",
    ["Selection."],
    ["Stakeholder mapping.", "Service prototyping.", "Financial reconciliation.", "Project prioritisation."],
    "The lifecycle is selection, growth and offboarding: bringing people in, developing them, and supporting their departure. The other activities belong to market sensing, finance or project design. Career management should therefore cover entry, progression and transition.")
add(4, "application", "Two candidates have similar technical qualifications, but one displays stronger empathy, values and team fit. How should the association decide?",
    ["Assess both hard skills and soft skills against the role profile.", "Give meaningful weight to attitude, values and group fit."],
    ["Select from qualifications first and assess attitude during probation.", "Treat empathy as an intrinsic incentive rather than a selection criterion.", "Use the organisation chart to determine which personality is appropriate."],
    "Knowledge and experience matter, but the final choice may hinge on soft skills because a winning team needs compatible personalities. The profile should make both categories explicit before interviews. Deferring fit assessment transfers avoidable recruitment risk into the working environment.")
add(4, "factual_anchor", "Which work belongs in a thorough staff-selection process?",
    ["Analyse the skills of current staff.", "Agree association-wide HR needs.", "Define the required profile and attitude."],
    ["Set the successful applicant's promotion timetable before interviews.", "Use the incentive scheme as the main applicant-rating method."],
    "Selection begins with the current skill base, compares it with needs, agrees HR priorities and defines the desired profile. A recruitment plan then covers reach, interviews, tests, ratings and the decision. Promotion planning and incentives come later in career management.")
add(4, "explanation", "How do incentives and risk-management systems differ as people-management tools?",
    ["Incentives encourage desired behaviour through rewards.", "Risk systems constrain harmful behaviour through rules, information and sanctions."],
    ["Incentives define role authority while risk systems define expected results.", "Risk systems are designed for career growth while incentives support offboarding.", "Incentives address soft skills while risk systems assess technical competence."],
    "The tools influence behaviour from different directions. Incentives reward contribution, while risk systems identify and sanction conduct that threatens the organisation or its people. Job descriptions, career tools and selection processes cover the other functions suggested by the distractors.")

# PDF page 5 / handbook pages 104-105: performance evaluation and financial foundations.
add(5, "application", "A mid-year review is being used solely to decide bonuses. How should management broaden the conversation?",
    ["Discuss work delivered beyond expectations."],
    ["Limit the discussion to targets linked to the current reward scheme.", "Use peer feedback as a substitute for the line manager's assessment.", "Set training needs after the year-end promotion decision.", "Evaluate personality fit rather than improvement actions."],
    "A performance review should identify strengths, improvement areas, required support and future objectives. A mid-year review can be developmental and need not trigger a reward decision. Bonus linkage is possible, but narrowing the conversation to pay loses the career-management purpose.")
add(5, "application", "An employee needs stronger stakeholder-service skills before taking on a larger role. Which outcomes should follow from evaluation?",
    ["A personal action plan with development objectives.", "Training linked to the capability gap."],
    ["A revised mission statement for the employee's department.", "A project plan that transfers the role to another unit.", "A bonus target based on stakeholder revenue rather than service competence."],
    "Evaluation should translate evidence into a personal action plan and the training needed to achieve it. New responsibilities can follow when capability is ready. Corporate mission or project ownership changes do not address the person's identified development need.")
add(5, "explanation", "What does a 360-degree performance evaluation add to a line-manager review?",
    ["Feedback from people who have working relationships with the employee.", "A broader qualitative view of behaviour across interactions.", "Evidence that can complement quantitative performance measures."],
    ["A replacement for agreed objectives and competence criteria.", "A financial valuation of the employee's future contribution."],
    "A 360-degree process gathers perspectives from colleagues who work with the person, expanding the evidence beyond one manager. It complements quantitative and qualitative criteria. It does not remove the need for objectives, judgement or a development plan.")
add(5, "factual_anchor", "Which three statements are the main financial statements introduced in the chapter?",
    ["The balance sheet.", "The cash flow statement.", "The income statement.", "The profit and loss account as another name for the income statement."],
    ["The stakeholder-satisfaction statement."],
    "The balance sheet, cash flow statement and income statement provide connected but different views. The income statement is also called a profit and loss account. Stakeholder satisfaction may be measured operationally, but it is not one of the three financial statements.")
add(5, "application", "An association wants to know what it owns, what it owes and its residual wealth at year-end. Which financial view is required?",
    ["A balance sheet at the reporting date."],
    ["A cash flow statement for the reporting period.", "An income statement recognising annual revenues and expenses.", "A budgeted cash flow for the coming year.", "A reconciliation of operating profit to operating cash."],
    "The balance sheet is a point-in-time picture of assets, liabilities and equity. Cash flow and income statements explain changes across a period, while a budgeted cash flow looks forward. The requested residual wealth is equity: assets less liabilities.")
add(5, "explanation", "How should accounts receivable and a stadium be distinguished on the balance sheet?",
    ["Receivables are current assets expected to become cash within a year.", "A stadium is normally a non-current tangible asset."],
    ["Receivables are liabilities because customers still control the cash.", "A stadium is current when it hosts fixtures during the reporting year.", "Both are classified by acquisition cost rather than conversion horizon."],
    "Classification reflects the nature and expected conversion of the resource. Receivables usually turn into cash soon, whereas a stadium supports operations for many years and is seldom sold. Customer payment timing does not make the receivable a liability.")

# PDF page 6 / handbook pages 106-107: cash, income and transaction timing.
add(6, "application", "An association forecasts a negative cash balance next year despite a credible sporting plan. What should management conclude?",
    ["The plan requires additional funding or revised cash timing."],
    ["A projected accounting surplus supplies the missing cash at the reporting date.", "Non-current assets can be treated as operating cash for budget purposes.", "The income statement should be used instead because cash forecasts concern wealth.", "The negative balance indicates that equity is already negative."],
    "A budgeted cash flow tests whether planned payments can be met when due. A sound programme may still be infeasible without financing or rescheduling. Profit, assets and equity are related measures, but they do not substitute for cash availability.")
add(6, "application", "The association pays cash for a building that has equivalent value. Which immediate accounting effects are expected?",
    ["Cash decreases while another asset increases.", "The cash flow statement records an investing outflow."],
    ["The purchase price becomes an operating expense at acquisition.", "Equity rises because the association owns more property.", "Revenue is recognised because the building will support future services."],
    "Buying the building exchanges one asset for another, so wealth does not change at acquisition. Cash flow records the payment as investment, while the income statement recognises use over time through depreciation. Ownership alone does not create revenue or equity.")
add(6, "explanation", "Why can sponsorship cash and sponsorship revenue occur at different times?",
    ["Cash follows the payment date.", "Revenue follows delivery of the contracted service.", "Advance payment can precede revenue recognition."],
    ["Revenue is recognised when the contract is signed because rights have future value.", "Cash timing determines the period in which the service is economically delivered."],
    "Financial statements separate the cash transaction from the economic transaction. A three-year sponsorship paid upfront improves cash immediately, while revenue is recognised as the service is delivered. Contract signature and payment do not by themselves complete the economic performance.")
add(6, "factual_anchor", "Which categories structure a cash flow statement?",
    ["Operating activities.", "Investing activities.", "Financing activities."],
    ["Customer activities.", "Equity activities."],
    "Cash movements are classified as operating, investing or financing. The categories distinguish regular operations, non-current asset transactions and funding transactions. Customer receipts may be operating cash, while equity is a balance-sheet concept rather than a cash-flow category.")
add(6, "application", "A marketing agency delivers services in December and is paid in February. How should the association treat the December economics?",
    ["Recognise an expense when the service is used."],
    ["Recognise the expense when February cash leaves the bank.", "Record the service as an intangible asset until payment.", "Treat the unpaid amount as revenue received in advance.", "Classify the service as an investing cash flow in December."],
    "Expense recognition follows consumption of the service rather than payment timing. The unpaid amount creates a liability until cash is paid. It is neither association revenue nor a non-current investment.")
add(6, "explanation", "What does negative equity signal to association management?",
    ["Liabilities exceed the value of assets.", "The organisation may struggle to repay claims as they fall due.", "Management needs to generate value and restore financial resilience.", "Repayment schedules may provide time for corrective action."],
    ["The association necessarily has a negative bank balance on the reporting date."],
    "Negative equity means the balance-sheet value owed exceeds the assets available, which is a serious warning. It is related to solvency rather than being the same as today's cash balance. Staged creditor claims may give management time, but the underlying weakness still requires action.")

# PDF page 7 / handbook pages 108-109: statement analysis and depreciation.
add(7, "factual_anchor", "Which statements correctly classify common cash movements?",
    ["Regular service receipts belong to operating activities.", "Purchasing a stadium is an investing activity.", "Receiving a bank loan is a financing activity."],
    ["Depreciation is a financing cash outflow.", "Recognising sponsorship revenue is an investing cash inflow."],
    "Operating cash comes from regular activity, investment cash from non-current asset transactions, and financing cash from borrowing or repayment. Depreciation has no current cash movement, and revenue recognition follows economic delivery. Classification depends on the transaction's nature rather than its label in another statement.")
add(7, "application", "The association reports a strong operating profit but modest cash generated from operations. Which interpretations are appropriate?",
    ["Profit and operating cash measure different aspects of performance.", "Working-capital movements may explain part of the difference.", "Non-cash expenses may require reconciliation.", "Management should inspect the cash-flow reconciliation before judging liquidity."],
    ["The operating profit figure should be substituted for cash generated in funding decisions."],
    "Operating profit measures economic performance while cash generated reflects cash timing and working capital. Depreciation, debtors and creditors can create a substantial reconciliation. Funding decisions need the cash evidence rather than treating profit as interchangeable with liquidity.")
add(7, "explanation", "Why can two managers reasonably disagree about the value of an asset?",
    ["Some asset values require estimates and judgement."],
    ["Asset value is determined by the cash paid during the current year.", "Current assets are valued by the date they are expected to be sold.", "Liability repayment schedules determine the value assigned to assets.", "Equity supplies a fixed market value for each asset category."],
    "Balance sheets assign monetary values, but some assets lack a simple observable price. Estimation assumptions can therefore produce defensible differences. Cash timing, liability terms and the residual equity equation do not independently fix each asset's value.")
add(7, "application", "A sponsor owes an invoice due in three months, while a bank loan matures in five years. How should they appear on the balance sheet?",
    ["The invoice is a current asset.", "The loan is a long-term liability."],
    ["The invoice is current revenue but absent from assets until paid.", "The loan is equity because repayment is outside the current year.", "Both belong to current assets because they affect future cash."],
    "The receivable is an asset expected to convert to cash within a year. The bank loan finances assets but remains a repayable liability, classified by its maturity. Revenue recognition and balance-sheet classification answer related but separate questions.")
add(7, "application", "The association builds a stadium expected to serve football for decades. Which financial treatments follow the chapter?",
    ["Record the stadium as a non-current tangible asset.", "Recognise its use gradually through depreciation.", "Show the construction payment as an investing cash outflow."],
    ["Recognise construction cost as a single operating expense when the venue opens.", "Classify stadium revenue as a reduction in the asset's carrying value."],
    "The stadium is a long-lived asset rather than a current operating cost. Cash leaves during construction, while depreciation recognises consumption over its useful life. Revenues generated by the venue belong to economic activity, not direct reduction of the asset value.")
add(7, "explanation", "How do liabilities and equity differ as sources financing association assets?",
    ["Liabilities represent funding that must be repaid.", "Equity represents residual organisational wealth.", "Supplier credit and bank borrowing create liabilities.", "Funds received with no repayment obligation can increase equity."],
    ["Equity is the portion of cash reserved for future liability payments."],
    "The right side of the balance sheet explains how assets are financed. Creditors have repayable claims, while equity is the residual after liabilities are deducted from assets. Equity is broader than a cash reserve and changes with economic performance and non-repayable funding.")

# PDF page 8 / handbook pages 110-111: income statement and stakeholder sensing.
add(8, "factual_anchor", "What does an income statement primarily explain?",
    ["Value generated and consumed through revenues and expenses during a period."],
    ["The association's cash receipts and payments classified by activity.", "The assets and claims held at a reporting date.", "The market value of stakeholder relationships at year-end.", "The funding needed for the next strategic cycle."],
    "The income statement reports economic performance over time through revenues and expenses. Cash flow explains cash movement, while the balance sheet is a point-in-time position. Stakeholder value and future funding may influence decisions but are not the statement's direct purpose.")
add(8, "application", "A three-season media-rights contract is paid when signed. Which reporting approach is appropriate?",
    ["Record the cash inflow when payment is received.", "Recognise revenue as the rights service is delivered."],
    ["Recognise the contract value as revenue at signing because cash is secure.", "Spread the cash flow across seasons to match revenue.", "Treat the payment as equity until the final season finishes."],
    "Cash and revenue follow different clocks. The payment enters cash flow when received, while income is earned over the service period. Deferring revenue is not the same as converting the payment into equity or restating cash movement.")
add(8, "application", "The association wants to improve the national-match experience. Which sensing activities provide useful stakeholder evidence?",
    ["Follow a fan's journey through information, ticketing and stadium access.", "Use focus groups to explore expectations.", "Review service processes from the match-goer's perspective."],
    ["Use attendance totals as the definition of fan satisfaction.", "Ask operational departments to infer customer needs from internal efficiency data."],
    "Market sensing requires seeing the service through the stakeholder's eyes. Journey observation, process walkthroughs and focus groups reveal needs and friction that totals may hide. Internal efficiency evidence matters, but it does not substitute for customer perspective.")
add(8, "explanation", "Why is stakeholder satisfaction operationally valuable to a football association?",
    ["Satisfied stakeholders are easier to work with.", "Positive experiences support loyalty and repeat engagement.", "Repeat customers are cheaper to retain than new customers are to acquire.", "Satisfaction helps the association achieve its service goals."],
    ["Satisfaction allows the association to use one service design for its different constituencies."],
    "Good experiences strengthen cooperation, loyalty and repeat use, reducing the effort required to reacquire customers. Football associations serve diverse constituencies, so satisfaction must be understood by stakeholder group. It improves operations without making stakeholder needs uniform.")
add(8, "application", "A department treats colleagues in another unit as people outside its service responsibility. Which correction follows the chapter?",
    ["Recognise colleagues and other departments as internal stakeholders."],
    ["Classify colleagues as external stakeholders when they approve a budget.", "Limit stakeholder analysis to people who purchase a service.", "Treat internal service quality as an HR issue detached from action plans.", "Map departments as resources rather than stakeholders."],
    "Stakeholders include internal colleagues whose work and expectations affect delivery. Their role depends on the objective and action plan, just as external stakeholder relevance does. A financial transaction is not required for a stakeholder relationship.")
add(8, "explanation", "What should an action plan contribute to stakeholder management?",
    ["Identification of stakeholders relevant to the objective.", "Consideration of their expectations and perspective."],
    ["A fixed stakeholder list reused across association objectives.", "A ranking based on each group's commercial contribution.", "A replacement for direct observation of the customer journey."],
    "An action plan links a specific objective to scenarios, milestones and the stakeholders who influence delivery. It should ask what those groups expect and how the plan looks from their perspective. Relevance changes with the objective, so a generic commercial ranking is insufficient.")

# PDF page 9 / handbook pages 112-113: market sensing and insights.
add(9, "factual_anchor", "Which stages form the chapter's market-sensing sequence?",
    ["Map stakeholders.", "Collect information.", "Identify opportunities."],
    ["Approve budgets.", "Evaluate employee incentives."],
    "The five-step sequence maps stakeholders, collects information, identifies opportunities, defines action plans and prioritises them. It translates external sensing into operational choices. Budget approval and people incentives may support implementation but are not stages in this sequence.")
add(9, "application", "A women's-football team maps broadcasters but overlooks OTT platforms, player services and medical organisations. What should it do?",
    ["Expand the map across related stakeholder areas.", "Break broad areas into specific organisations and roles.", "Review the map as technologies and stakeholders change.", "Connect the map to the objective being pursued."],
    ["Keep the map centred on rights buyers because media exposure is the primary value exchange."],
    "The example shows a dense landscape spanning media, players, medical services, data, regulators and marketing. Mapping should become specific enough to support information gathering and action. A broadcaster-centred map would miss organisations shaping participation, welfare and new distribution.")
add(9, "explanation", "Why does the chapter describe market sensing as a team sport?",
    ["The environment is too complex for one person to understand.", "Staff encounter different external signals through their work.", "Shared observations create a richer information base.", "A sensing culture gives employees a delivery role and an intelligence role."],
    ["The marketing department can validate observations after other departments complete their action plans."],
    "Useful intelligence is distributed across the organisation, so each person should act as a sensor. Processes and culture must help observations reach the team and be analysed. Marketing expertise remains useful, but central validation after planning would capture insight too late.")
add(9, "application", "Staff gather useful observations but keep them in personal notes. Which operational changes support opportunity discovery?",
    ["Create routines for sharing observations."],
    ["Ask managers to summarise observations during annual performance reviews.", "Store observations within departmental files until an opportunity is confirmed.", "Commission external research before using staff experience.", "Move responsibility for sensing to the data-analytics supplier."],
    "Internal people are a valuable information source, but their observations need shared processes and habits. A structured repository and periodic discussion turn individual experience into organisational intelligence. Delayed or isolated storage weakens the diversity and timeliness of insight.")
add(9, "factual_anchor", "Which sources of stakeholder information are identified in the market-sensing section?",
    ["People within the association.", "Internet sources."],
    ["The balance sheet as a customer-attitude survey.", "Job descriptions as external market evidence.", "Competition regulations as a measure of sentiment."],
    "The chapter identifies internal observations, internet sources, paid research, market analysts and social-media sentiment analysis. These sources complement each other. Financial and HR documents may support operations but do not directly reveal changing stakeholder attitudes.")
add(9, "application", "A monthly opportunity meeting receives broad observations about drone filming and computer vision. How should the team work with them?",
    ["Develop observations into insights through discussion.", "Explore related uses in scouting, refereeing and coaching.", "Translate promising insights into service opportunities.", "Create and prioritise action plans after refining the idea."],
    ["Select the first technically feasible use before discussing stakeholder value."],
    "Information becomes an insight when the team connects it to changing needs and possible value. Discussion can extend one technology across several services, after which action plans are assessed and prioritised. Technical feasibility alone does not establish stakeholder benefit or strategic fit.")

# PDF page 10 / handbook pages 114-115: opportunity assessment and relationship tools.
add(10, "factual_anchor", "Which dimensions are used to analyse an action plan arising from an opportunity?",
    ["Impact."],
    ["Employee tenure.", "Asset depreciation.", "Congress representation.", "Financial-statement format."],
    "The action-plan assessment covers impact, complexity and timing. Impact may be economic, social, reputational, tactical or strategic; complexity includes stakeholder coordination; timing asks about urgency. The distractors are valid management topics but belong to different tools.")
add(10, "application", "A high-impact digital opportunity requires several powerful external partners who show limited commitment. What should the action plan reflect?",
    ["High coordination complexity.", "The partners' power and commitment."],
    ["Low complexity because the association controls the strategic objective.", "A normal planning timetable based on impact rather than urgency.", "An internal HR response before partner engagement."],
    "Complexity depends on coordination with internal and external stakeholders, especially their power and commitment. Strategic impact does not reduce delivery dependence. Timing must be assessed separately rather than inferred from impact.")
add(10, "explanation", "Why is experimentation useful when designing uncertain services?",
    ["It tests alternative solutions.", "It produces observations about outcomes.", "It reduces uncertainty before wider commitment."],
    ["It converts a strategic opportunity into a routine process before launch.", "It makes comparison with other organisations less useful."],
    "Experimentation creates evidence where outcomes are uncertain. Small tests and observation of peers help managers learn which solution works before scaling. It supports rather than replaces external learning and disciplined planning.")
add(10, "application", "A fan club contacts the association through ticketing, email, events and social media. How should football relationship management support service improvement?",
    ["Record interactions across touchpoints.", "Link product and event history to the stakeholder.", "Analyse behaviour and preferences.", "Use the pattern to improve future service and targeting."],
    ["Maintain separate records for each channel so departments preserve ownership of their data."],
    "Relationship management creates a joined view of interactions, preferences and behaviour. Analysis can reveal patterns and support better service or targeted marketing. Channel silos would fragment the stakeholder picture the tool is intended to organise.")
add(10, "factual_anchor", "What does a driver analysis seek to identify?",
    ["Cause-and-effect relationships behind satisfaction, revenue or cost."],
    ["The legal ownership of stakeholder information.", "The accounting value assigned to customer loyalty.", "The reporting line responsible for each service interaction.", "The timetable for recognising sponsorship revenue."],
    "Driver analysis maps internal factors that influence an outcome such as sponsor satisfaction, revenue or cost. It aims to reveal relationships that might remain hidden. Data ownership, reporting lines and revenue timing are separate operational questions.")
add(10, "application", "Sponsors value media exposure and the experience provided to their guests. Which analysis would best guide improvement?",
    ["Map media exposure and hospitality factors as drivers of sponsor satisfaction.", "Test how changes in those drivers affect the sponsor's perceived value."],
    ["Use the sponsorship fee as the direct measure of satisfaction.", "Assess stadium quality as a financial asset rather than a service driver.", "Separate guest experience from the sponsorship relationship."],
    "A sponsor evaluates both exposure and hospitality, so driver analysis should connect those service dimensions to satisfaction. The fee shows commercial value but does not reveal the experience producing it. Stadium facilities matter here through service quality rather than balance-sheet classification.")

# PDF page 11 / handbook pages 116-117: pricing, maps, scorecards and partners.
add(11, "factual_anchor", "Which factors can affect the value of a match ticket in the chapter's example?",
    ["The opponent.", "The day and time of the match.", "Stadium quality."],
    ["The association's equity balance.", "The depreciation method used for the stadium."],
    "Ticket value changes with the opponent, timing, weather, competing city events and facility quality. Dynamic pricing can respond to those variables. Balance-sheet measures concern financial reporting rather than the fan's perceived value of attendance.")
add(11, "application", "Ticket demand varies by opponent, weather and weekday, but prices are fixed months in advance. Which operational conclusions follow?",
    ["The pricing decision is ignoring changing value drivers.", "Dynamic pricing could incorporate updated demand variables.", "Customer and revenue effects should be monitored.", "Price changes should remain connected to the fan value proposition."],
    ["The association should base prices on stadium book value to create financial consistency."],
    "Fixed pricing can overlook variables that change willingness to pay. A dynamic approach uses current drivers, while monitoring is needed because revenue and customer experience are connected. Stadium accounting value is not a proxy for match-specific fan value.")
add(11, "application", "A manager has a strategy map but lacks evidence about whether its drivers are changing. Which tool should be added?",
    ["A balanced scorecard with measures for the mapped variables."],
    ["A cash-flow reconciliation using the same variables.", "A stakeholder map showing organisations rather than measures.", "A revised organisation chart linking departments to the variables.", "A job-description review for the manager who owns the map."],
    "The strategy map expresses cause-and-effect logic from resources through processes and customers to outcomes. The balanced scorecard adds quantitative measures so those drivers can be tracked. The other tools answer financial, stakeholder or accountability questions rather than measuring the map.")
add(11, "explanation", "How does a strategic map connect operational resources to organisational outcomes?",
    ["Resources support processes.", "Processes shape customer perceptions.", "Customer outcomes influence strategic objectives.", "Cause-and-effect links make operational assumptions explicit."],
    ["Financial objectives determine the resources before customer and process effects are examined."],
    "The map traces a causal chain from resources to process performance, customer value and final objectives. It makes the operating theory of the strategy visible. Reading the chain backwards as a resource-allocation rule would miss its explanatory purpose.")
add(11, "application", "Two partner organisations agree on activities but communicate different promises to the target audience. What should they align?",
    ["The shared message and value proposition."],
    ["Their internal organisation charts.", "Their financial year-end dates.", "Their employee incentive schemes.", "Their asset-valuation methods."],
    "Partner coordination depends on a common understanding of the target market, its needs, the value offered, the message and engagement approach. Activity coordination cannot rescue contradictory promises. Internal structures and accounting policies may differ without undermining a coherent service proposition.")
add(11, "explanation", "Which questions should partners resolve when coordinating a joint service?",
    ["Who is the target market and what does it need?", "What value proposition will satisfy it?", "How will the partners communicate and engage?", "What data and conversion process will support delivery?"],
    ["Which partner will recognise the service revenue first in its income statement?"],
    "Joint delivery starts with agreement on customer, value, message, engagement and the information used to convert interest into participation. These shared choices coordinate intangible service value. Accounting recognition may need agreement later, but it does not define the customer proposition.")

# PDF page 12 / handbook pages 118-119: service design and project structure.
add(12, "factual_anchor", "Which characteristic distinguishes services from physical goods in the chapter?",
    ["Production and consumption occur at the same time."],
    ["Quality is assessed after the customer takes ownership.", "Physical elements dominate perceived service value.", "Customer behaviour has limited influence during delivery.", "Service output can be stored for a later audience."],
    "A service is experienced as it is produced, and much of its value is intangible and interactive. The organisation and other customers influence satisfaction during delivery. Physical ownership and inventory logic therefore fit goods better than a live football experience.")
add(12, "application", "A futsal coaching course provides excellent content but clashes with fixtures and leaves applicants uncertain about admission. Which value dimensions need attention?",
    ["The opportunity cost created by timing.", "The uncertainty surrounding acceptance."],
    ["The accounting value of the course materials.", "The coach's position in the organisation chart.", "The association's financing mix for course delivery."],
    "Perceived value subtracts price, inconvenience and uncertainty from tangible and emotional benefits. Scheduling conflict and unclear acceptance therefore reduce value even when content is strong. Asset values and organisational reporting lines do not represent the applicant's service cost.")
add(12, "explanation", "What are the main stages in designing a new service?",
    ["Understand the target market's needs.", "Design a value proposition superior to alternatives.", "Design operations capable of delivering the service."],
    ["Set the final price before identifying the customer segment.", "Launch the service before testing delivery processes."],
    "Service design starts with customer understanding, defines the value to be offered, and then builds the operating process. Price is one element of value rather than the starting point. Launch should follow process and resource design, especially where delivery is interactive.")
add(12, "application", "Customers see a polished match event, while backstage delivery is fragile. Which capabilities should management strengthen?",
    ["Process design.", "Information and measures for tracking delivery.", "Resources needed to execute the process.", "People with appropriate customer attitudes."],
    ["A broader public value proposition before backstage operations are stabilised."],
    "The service iceberg means the visible experience rests on substantial hidden operations. Reliable processes, information, resources and customer-oriented people create the quality customers perceive. Expanding the promise before stabilising delivery would increase the gap between expectations and experience.")
add(12, "factual_anchor", "Which components contribute to net perceived service value?",
    ["Perceived benefits."],
    ["The provider's asset value.", "The project's internal reporting structure.", "The employee's performance rating.", "The association's accounting surplus."],
    "Net perceived value compares tangible and emotional benefits with price, time inconvenience and uncertainty. It is defined from the customer's perspective. Provider finances and internal controls may shape delivery but are not direct components of the customer's calculation.")
add(12, "application", "Why is a project approach suitable for staging a championship or training camp?",
    ["The service has defined objectives and a changing set of activities.", "The work can be selected, planned, organised, implemented and reviewed."],
    ["The approach converts the event into a recurring line-department process.", "Project status reduces the need for operational measures during delivery.", "A project structure allows objectives to be refined after implementation begins."],
    "Events are finite, distinctive services that benefit from explicit selection, definition, planning, organisation and control. The project cycle also supports monitoring, reporting, review and learning. It creates discipline rather than relaxing measures or scope.")

# PDF page 13 / handbook pages 120-121: project load, definition, planning and learning.
add(13, "factual_anchor", "Which information should a project definition establish?",
    ["Expected deliverables.", "Required performance level.", "Resources and timing."],
    ["The final performance-review ratings of project staff.", "The accounting recognition date for each project benefit."],
    "Definition explains how project value will be delivered through outputs, standards, resources and timing. It aligns stakeholder expectations before detailed activity planning. Staff evaluation and accounting treatment may follow from delivery but do not define the project itself.")
add(13, "explanation", "Why can undertaking too many projects reduce service quality?",
    ["Frequent switching reduces team efficiency.", "Resources become fragmented across competing work.", "Attention available for each project declines.", "Execution quality suffers beyond the useful workload level."],
    ["Project efficiency rises in proportion to the number of initiatives selected."],
    "A modest increase in workload may sharpen organisation, but excessive project volume creates switching and fragmentation. The result is a decline in efficiency and service quality. Selection is therefore an operational capacity decision, not a competition to maximise project count.")
add(13, "application", "Stakeholders keep adding desirable features during tournament delivery. What should the project manager use to control this idea creep?",
    ["The agreed project definition."],
    ["The stakeholder map as authority for adding requested features.", "The annual strategic vision as the detailed scope document.", "The balanced scorecard as the approval mechanism.", "The final review as the point for redefining current deliverables."],
    "A detailed definition establishes deliverables, performance, resources and timing, keeping stakeholders aligned with the original intention. New ideas can be assessed through change control rather than absorbed informally. The other tools inform strategy or measurement but do not provide detailed scope authority.")
add(13, "explanation", "How does project planning differ from project definition?",
    ["Definition specifies value, deliverables and performance expectations.", "Planning assigns activities, timing, information, resources and responsibility."],
    ["Definition selects team members while planning decides the target market.", "Planning establishes the strategic case while definition monitors execution.", "Definition reports results while planning captures lessons from repetition."],
    "Definition sets what the project is expected to deliver and within what broad constraints. Planning explains how, when, with what resources and by whom delivery will occur. Mixing the stages can produce activity before scope and expectations are stable.")
add(13, "application", "A national association is planning a service already delivered successfully by several peers. Which approach improves the plan?",
    ["Benchmark comparable association projects.", "Use UEFA knowledge and contacts.", "Adapt shared good practice to the local context."],
    ["Replicate the peer process before defining local performance expectations.", "Use benchmarking as the final review after operational choices are fixed."],
    "Peer experience can reveal proven activities, resources and risks, while UEFA facilitates exchange. The association still needs a local definition and adaptation because context and stakeholders differ. Benchmarking should inform planning rather than replace it or arrive after decisions are closed.")
add(13, "explanation", "What roles does information play during service delivery and review?",
    ["Monitor delivery against the planned level.", "Keep stakeholders informed through reporting.", "Improve repeated services through review.", "Capture learning from one-off events for future delivery."],
    ["Convert operational results into project scope changes during execution."],
    "Information supports control, communication and learning. Repeated services can improve the same process, while event reviews transfer lessons to future projects. Monitoring may justify corrective action, but informal scope change would recreate idea creep.")

# PDF page 14 / handbook pages 122-123: selection, critical path, risk and measures.
add(14, "explanation", "How should an association choose which service projects to pursue?",
    ["Consider strategic, economic and resource criteria."],
    ["Rank projects by forecast profit and treat resource needs as an implementation issue.", "Use a fixed weighted score as the decisive method for dissimilar projects.", "Select projects that attract the broadest stakeholder group.", "Prioritise projects whose benefits are easiest to measure."],
    "Selection balances contribution to football, financial effects and scarce material and human resources. Weighted models can inform discussion, but unique options and uncertain forecasts limit mechanical ranking. Ease of measurement or audience size does not replace strategic judgement.")
add(14, "application", "A project activity sits on the critical path and begins to slip. Which management responses are appropriate?",
    ["Assess the effect on final delivery timing.", "Protect or reallocate resources to recover the activity."],
    ["Allow the delay if the activity remains within its own departmental budget.", "Move the activity into the post-project review.", "Offset the delay by increasing customer expectations for another service dimension."],
    "A critical-path delay threatens the project's delivery date, so timing and resources require immediate attention. Budget performance in one unit does not neutralise schedule dependence. Review captures learning later; it cannot replace action on a live constraint.")
add(14, "application", "A power cut is a credible match risk. What should a robust contingency plan specify?",
    ["Responses for a failure several hours before kick-off.", "Responses for a failure immediately before or during the match.", "Safe movement of spectators when evacuation is required."],
    ["A single recovery decision applied across the different timing scenarios.", "Transfer of risk responsibility to the electricity supplier after the event."],
    "Contingency planning connects a recognised risk to actions under distinct scenarios. Timing changes whether recovery, postponement or evacuation is appropriate. Supplier responsibility may matter contractually, but the association still needs an operational safety response.")
add(14, "factual_anchor", "Which activity belongs in sound project planning?",
    ["Identify critical activities and resources.", "Estimate project timing.", "Assess costs, benefits and risks.", "Prepare contingency responses."],
    ["Use the project review to define the original work packages."],
    "Planning breaks the project into work packages, estimates resources, timing, costs and benefits, highlights critical elements and prepares for risk. Review occurs after or during delivery to learn and improve. Defining work packages at review would leave execution without a usable plan.")
add(14, "explanation", "What makes a useful service-performance measure?",
    ["It reflects a relevant service dimension."],
    ["It remains stable when service quality changes.", "It requires specialist interpretation by the measurement team.", "It concentrates on dimensions already exceeding expectations.", "It combines customer and employee views into one score."],
    "A good system covers relevant dimensions, responds when service changes and is understandable enough to guide improvement. Measures should expose underperformance as well as strengths. Combining perspectives may hide the distinct causes and audiences represented by each measure.")
add(14, "explanation", "How should a radar chart comparing expected and actual service performance be interpreted?",
    ["An expectation line beyond actual performance indicates underperformance.", "Actual performance beyond expectation indicates overperformance."],
    ["Matching lines show that measurement sensitivity is inadequate.", "A wider actual line indicates higher operating cost rather than service performance.", "Expectation gaps should be prioritised by chart size before considering customer importance."],
    "The chart compares what customers expect with what the service delivers by dimension. Gaps indicate underperformance, overperformance or a match. Management still needs judgement about importance and causes rather than ranking visual gaps mechanically.")

# PDF page 15 / handbook pages 124-125: measurement perspectives, risk and conclusion.
add(15, "application", "A service dashboard contains employee satisfaction, customer satisfaction and call waiting time. How should these measures be classified?",
    ["Employee satisfaction is internal and subjective.", "Customer satisfaction is external and subjective.", "Call waiting time is external and objective."],
    ["Employee satisfaction is objective because it is collected numerically.", "Call waiting time is internal because staff control the answering process."],
    "Perspective concerns whose experience is measured, while objectivity concerns whether the measure is judgement or observable performance. Survey scores remain subjective despite numerical collection. Customer waiting time is an external service outcome even though internal processes influence it.")
add(15, "explanation", "Why should risk assessment continue during project execution?",
    ["Risk conditions can change as the service unfolds.", "Emerging threats may require activation or revision of action plans.", "Continuous monitoring protects service quality and customer experience.", "Execution evidence can refine scenario assumptions."],
    ["The planning-stage assessment transfers operational risk to the project team."],
    "Planning identifies risks and scenarios, but live conditions may change their probability or impact. Monitoring lets managers activate contingencies and adjust responses before service quality is damaged. Responsibility remains with management rather than being discharged by the initial assessment.")
add(15, "explanation", "How do operations relate to strategy in the chapter's conclusion?",
    ["Operations translate strategic intentions into delivered results."],
    ["Operations define the association's mission through recurring service decisions.", "Strategy begins after managers identify operational bottlenecks.", "Operational efficiency determines which stakeholder goals are legitimate.", "Project delivery replaces the need to prioritise strategic initiatives."],
    "Strategy chooses direction and priorities; operations turn them into actual services and experiences. Operational evidence can inform later strategy, but it does not define mission or stakeholder legitimacy. Careful selection, planning, people and measures connect the two levels.")
add(15, "application", "A review finds that a youth event met its budget but disappointed participants. Which follow-up is appropriate?",
    ["Examine customer-facing service dimensions alongside financial performance.", "Capture lessons in the project review for future events."],
    ["Classify the event as successful because budget control is objective.", "Revise the strategic objective before analysing participant experience.", "Transfer evaluation to finance because the event closed within budget."],
    "Budget adherence is one dimension of project performance, not proof of service quality. Participant evidence should identify where expectations were missed, and the review should convert that evidence into learning. Strategy may later change, but operational diagnosis comes first.")
add(15, "explanation", "Which ideas summarise world-class operational management in a football association?",
    ["Motivated, capable people deliver services.", "Financial understanding supports economic resilience.", "Stakeholder sensing reveals opportunities."],
    ["Service quality can be inferred from financial surplus.", "Project selection becomes unnecessary when market sensing is strong."],
    "World-class operations integrate people management, financial literacy, external sensing and disciplined service design. No single indicator captures that system. Surplus can coexist with poor experience, and opportunity discovery still requires project selection and execution capacity.")
add(15, "explanation", "Why are project selection, measurement and learning connected?",
    ["Selection protects scarce capacity for worthwhile projects.", "Measurement supports control during execution.", "Review converts results into learning.", "Learning improves future selection and delivery."],
    ["Measurement compensates for weak selection by proving which overloaded projects should continue."],
    "The operational cycle begins by choosing work that fits strategy and resources, then measures delivery and learns from outcomes. Each stage improves the next cycle. Measurement can reveal a poor choice, but it cannot restore capacity already fragmented by excessive project load.")


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
        "session_title": "Chapter 3 - Operational management",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
