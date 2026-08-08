"""Build the staged Chapter 10 UEFA CFM football law bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "UEFA-HFM-Football-law.pdf"
OUTPUT = Path("data/cfm_imports/chapter_10_football_law.json")
QUESTIONS: list[dict] = []
CATEGORY_CYCLE = [
    "application", "explanation", "factual_anchor", "application", "explanation",
    "application", "factual_anchor", "explanation", "application", "application",
    "explanation", "factual_anchor", "application", "explanation", "application",
    "application", "explanation", "factual_anchor", "application", "explanation",
]


def _positions(number: int, count: int) -> list[int]:
    group = (number - 1) % 5
    return {
        1: [group % 5],
        2: sorted({group % 5, (group + 2) % 5}),
        3: sorted({group % 5, (group + 2) % 5, (group + 4) % 5}),
        4: [position for position in range(5) if position != (group + 1) % 5],
    }[count]


def add(page, stem, true, false, explanation):
    number = len(QUESTIONS) + 1
    assert 1 <= len(true) <= 4, (number, len(true))
    positions = _positions(number, len(true))
    assert len(false) == 5 - len(positions), (number, len(false), positions)
    ti, fi = iter(true), iter(false)
    options = [next(ti) if i in positions else next(fi) for i in range(5)]
    QUESTIONS.append({
        "q_number": number,
        "question_text": stem,
        "q_type": "multiple_choice",
        "oral_exam_category": CATEGORY_CYCLE[(number - 1) % 20],
        "options": options,
        "source_locator": {
            "file": SOURCE,
            "pdf_pages": [page],
            "handbook_pages": [290 + 2 * page, 291 + 2 * page],
        },
        "page_crops": [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 294-295: nature and sources of sports law.
add(2, "A national association assumes that football law is contained in one self-contained code. What is the strongest correction?",
    ["Map the relevant sports regulations together with applicable state law, treaties and jurisprudence."],
    ["Start with FIFA regulations and use national law where the association's statutes expressly incorporate it.", "Separate private football rules from public law before deciding which system governs the issue.", "Use the rules of the highest football body involved, then apply lower-level regulations to procedural gaps.", "Identify the lex sportiva rule first and treat other legal sources as interpretive support."],
    "Sports law is a transversal and transnational field rather than one codified text. A football problem can engage federation rules, domestic law, treaties and case law at the same time. The hierarchy of football bodies matters, but it does not displace other applicable legal sources.")
add(2, "Why is sports law described as both transversal and transnational?",
    ["Different legal disciplines may overlap in one sporting situation.", "Private sporting regulations bind members across national legal systems."],
    ["Transversal rules apply across levels of the football pyramid, while transnational rules apply across confederations.", "State laws fill regulatory gaps, while international treaties provide a uniform procedural code.", "CAS jurisprudence combines domestic and federation rules into a single international system."],
    "Sports law is transversal because contract, employment, disciplinary, corporate and other fields can intersect. It is transnational because sports organisations create rules accepted across borders by their members. That combination is different from a single uniform code or a simple hierarchy of football regulations.")
add(2, "Which sources are presented as elements of sports law?",
    ["The Olympic Charter and its principles of Olympism.", "European law, including movement and competition rules.", "Lex sportiva as the sports community's private legal order."],
    ["National competition regulations as a distinct source from federation rules.", "The Laws of the Game as football's principal public-law source."],
    "The chapter's source map includes the Olympic Charter, European law, anti-doping rules, Swiss law, lex sportiva, and jurisprudence and legal literature. National competition rules may form part of the wider regulatory network, but are not a separately named element in the figure. The Laws of the Game are sporting rules, not a public-law source.")
add(2, "A confederation is regulating continental club finance. Which features of the global football pyramid are relevant?",
    ["FIFA sits above the confederations in the global structure.", "Confederations standardise their continental competitions.", "Confederations may regulate financial organisation involving member associations and clubs.", "National and regional associations connect the international bodies with clubs and participants."],
    ["Continental financial rules derive their authority from the state law of the confederation's headquarters."],
    "The football pyramid runs from FIFA through confederations and associations to clubs and participants. Confederations regulate their competitions and can address the financial organisation of members and clubs, as UEFA does through financial rules. Headquarters law may supplement the framework, but it is not the sole basis described for continental authority.")
add(2, "How does the World Anti-Doping Code operate within sports law?",
    ["It sets the framework with which international federations' anti-doping codes must comply."],
    ["It binds athletes directly once their national association has accepted the Olympic Charter.", "It supplies default rules where a federation's disciplinary code is silent on doping.", "It governs sanctions while federations retain their own definitions of doping offences.", "It applies through national legislation in states that have ratified the Macolin Convention."],
    "The WADA Code regulates doping offences and sanctions at the global framework level. It does not itself apply directly to individual athletes and entourages; federation anti-doping codes implement compliant rules. Its legal route is distinct from the Macolin Convention on competition manipulation.")
add(2, "A football regulation leaves a contractual issue unresolved. Which legal reasoning follows the chapter?",
    ["Check whether the regulation reserves application of state law to fill gaps.", "Identify the state law connected to the governing sports body or agreement."],
    ["Treat CAS case law as the default gap-filler before applying state legislation.", "Apply the national association's law because the affected player is registered there.", "Refer the gap to the next body above in the football pyramid for an authoritative rule."],
    "Sports regulations commonly reserve a role for state law because they cannot anticipate every contingency. The relevant connecting rule may come from statutes, regulations or the parties' agreement, and Swiss law is influential because many federations are based there. CAS jurisprudence can guide interpretation but does not automatically replace the applicable state law.")

# PDF page 3 / handbook pages 296-297: Olympic Charter, Swiss law and Bosman.
add(3, "Which purposes of the Olympic Charter are identified in the chapter?",
    ["Define the fundamental principles and essential values of Olympism.", "Serve as the statutes of the IOC.", "Set reciprocal rights and obligations of the IOC, international federations and NOCs."],
    ["Create a direct disciplinary jurisdiction over members of national Olympic committees.", "Harmonise the eligibility rules used by international federations at the Olympic Games."],
    "The Charter expresses Olympism's principles, functions as the IOC's statutes and allocates core rights and duties among the Olympic Movement's three constituents. It also governs organisation and the conditions for the Games. It is not presented as a direct disciplinary code or a uniform federation eligibility rulebook.")
add(3, "Why is the Olympic Charter important to international federations despite imposing relatively limited obligations on them?",
    ["It requires implementation of the World Anti-Doping Code and the code against competition manipulation.", "It links international federations to governance and integrity duties.", "It recognises their role in preparing and organising the Olympic Games.", "It frames their responsibility to promote and develop their sport worldwide."],
    ["It makes their technical regulations directly enforceable by national Olympic committees."],
    "International federations have specific integrity, governance and development obligations under the Olympic framework and gain a role in Olympic preparation. The Charter therefore connects autonomy with responsibilities. It does not turn NOCs into enforcement bodies for federation technical rules.")
add(3, "A federation based in Switzerland is drafting statutes. Which feature of Swiss association law is most relevant?",
    ["It offers substantial organisational flexibility with relatively few mandatory provisions."],
    ["It requires registration when the association participates in international commercial competitions.", "It gives federation regulations priority over employment law once incorporated into the statutes.", "It permits statutory rules to displace Swiss law in disputes heard by the CAS.", "It subjects associations to a standard governance structure unless the statutes justify deviations."],
    "Swiss association law is deliberately flexible and consists of only 20 Civil Code articles, few of them mandatory. Registration is required in limited circumstances such as commercial activity or an audit requirement. Federation autonomy remains supplemented by applicable Swiss law rather than overriding it.")
add(3, "A FIFA employment rule grants compensation for termination without just cause but leaves the concept undefined. How should the gap be approached?",
    ["Apply the RSTP entitlement together with Swiss employment-law principles.", "Use Swiss law to assess just cause.", "Use Swiss law in calculating compensation where the regulatory framework calls for it.", "Preserve FIFA's jurisdiction over the international football employment dispute."],
    ["Refer the concept to the employment law of the club's national association before FIFA considers the claim."],
    "The RSTP governs the football employment relationship, while FIFA's statutes allow Swiss law to supplement its rules. Swiss employment principles can define just cause and inform compensation without removing FIFA's jurisdiction. The club's local law is not stated as the automatic first reference.")
add(3, "What was the central legal effect of the Bosman ruling described in the handbook?",
    ["It recognised EU freedom of movement for football players and ended post-contract transfer restrictions based on unpaid compensation."],
    ["It treated transfer compensation as incompatible with EU law whenever a player moved between member states.", "It required FIFA to replace transfer fees with training compensation for players under 23.", "It applied EU competition law to the proportionality of sporting rules affecting player mobility.", "It created a right for players to terminate fixed-term contracts when another EU club offered employment."],
    "Bosman stopped a club from withholding release after contract expiry because a new club had not paid compensation. The judgment recognised workers' freedom of movement and drove major reform of FIFA's transfer rules. It did not abolish transfer fees during contracts or create a general early-termination right.")
# PDF page 4 / handbook pages 298-299: European law, anti-doping, case law and lex sportiva.
add(4, "A federation rule restricts club ownership to protect competition integrity. Which Meca-Medina test should guide review?",
    ["Identify a legitimate sporting aim.", "Assess whether the restriction is necessary to achieve that aim.", "Ensure the restriction does not exceed what the aim requires."],
    ["Compare the rule's economic impact with the competitive benefit claimed by the federation.", "Confirm that the restriction is applied consistently across domestic and international competitions."],
    "Meca-Medina asks whether a restrictive sporting rule pursues a legitimate aim and remains necessary and proportionate to it. Integrity can be such an aim, and the test was applied to multiple-club ownership rules. Economic balancing and cross-competition uniformity are not the stated legal criteria.")
add(4, "Why is the World Anti-Doping Code described as unusually autonomous?",
    ["It regulates proof, liability, sanctions, limitation and jurisdiction in substantial detail.", "It is designed for worldwide application through compliant federation rules.", "It leaves limited latitude to national anti-doping bodies.", "Its self-sufficient structure resembles a distinct body of sports law."],
    ["Its decisions are reviewed through a disciplinary structure independent of federation regulations."],
    "The WADA Code anticipates a broad range of substantive and procedural issues, making it comparatively self-contained. International federations implement codes that comply with it, with limited national variation. Its autonomy concerns regulatory completeness, not a separate universal adjudicatory system.")
add(4, "What role does sports case law play in the legal system?",
    ["It promotes consistent interpretation and predictable enforcement of sports regulations."],
    ["It supplies binding precedent to federation bodies when their codes contain comparable provisions.", "It converts recurring federation practice into state-recognised legal rules.", "It gives the CAS authority to revise regulations that produce inconsistent outcomes.", "It resolves conflicts between national law and lex sportiva through a uniform hierarchy."],
    "Decisions of federation bodies, CAS and state courts shape interpretation and crystallise practices. This improves consistency and predictability across disputes. The chapter does not claim a strict common-law precedent system or a universal hierarchy controlled by CAS.")
add(4, "A party believes the CAS applied a sports regulation incorrectly. What is the Swiss Federal Tribunal's role according to the chapter?",
    ["Review limited grounds involving serious procedural defects or fundamental rights.", "Provide public-law oversight of the acceptability of the arbitral process."],
    ["Reconsider the merits when the CAS interpretation conflicts with settled federation case law.", "Correct errors in the application of Swiss law where they affected the award.", "Review whether the sanction is proportionate to the seriousness of the sporting offence."],
    "The SFT exercises narrow control over CAS awards, focusing on fundamental procedural problems rather than the correctness of sports-law application. Its availability provides limited public oversight. It is not a merits appeal on interpretation, proportionality or ordinary legal error.")
add(4, "Which description best captures lex sportiva?",
    ["A coordinated transnational network of private sporting rules, practices and jurisprudence binding the sports community.", "A system that evolves through international federations, the IOC, WADA and CAS.", "A framework whose effects cross borders despite state legal sovereignty."],
    ["A body of customary rules recognised by states when hosting international sporting events.", "A consolidated hierarchy in which international federation statutes prevail over national sports rules."],
    "Lex sportiva is the sports movement's evolving private legal order, formed by statutes, regulations, practices and jurisprudence. Its authority is accepted within the sporting community and can influence public authorities. It is not based on state adoption or a simple rule that international statutes displace every national provision.")
add(4, "A legal team wants more predictable application of a federation's disciplinary rules. Which sources should it examine?",
    ["Decisions of the federation's own judicial bodies.", "CAS jurisprudence reviewing comparable rules.", "Relevant Swiss Federal Tribunal decisions on the arbitral framework.", "Scholarly analysis identifying patterns and shortcomings."],
    ["National association decisions treated as authoritative interpretations of the federation's rule."],
    "Federation decisions, CAS awards, limited SFT jurisprudence and legal literature collectively illuminate interpretation and practice. They can reveal consistent principles and weaknesses in legal reasoning. A national body's locally adapted rule may be informative, but it is not one of the core sources identified for uniform international application.")
add(4, "Why can lex sportiva be called a 'law without the state'?",
    ["Its private rules bind sporting stakeholders internationally without formal enactment by a parliament or state court."],
    ["It is enforced by CAS awards without requiring recognition under national arbitration law.", "It operates where states have delegated regulation of sport to international federations.", "It replaces domestic law for stakeholders who accept membership in the sports movement.", "It derives legal validity from the global consistency of federation practices rather than public authority."],
    "Lex sportiva originates in the private rules and institutions of organised sport rather than state legislation. Its practical reach is powerful because members accept it and sporting bodies apply it worldwide. Domestic law and arbitral enforcement still matter, so the phrase does not mean the state is legally irrelevant.")

# PDF page 5 / handbook pages 300-301: contracts, just cause and consequences.
add(5, "Which features define a professional football employment contract under the RSTP account in the chapter?",
    ["It is written.", "The player receives more than reimbursement of effective football expenses."],
    ["It provides remuneration across at least one playing season.", "It is registered by the national association before sporting services begin.", "It separates football remuneration from image-rights or performance payments."],
    "Professional status depends on a written agreement and payment exceeding actual football expenses. Contract duration is regulated separately, but the definition does not turn on a guaranteed season, registration formality or a particular remuneration structure. These distinctions matter before applying contractual-stability rules.")
add(5, "A club and player are drafting a first professional contract. Which duration limits match the chapter?",
    ["A minimum duration of one year.", "A maximum of three years for a player under 18.", "A maximum of five years for a player over 18."],
    ["A maximum of three seasons when the player turns 18 during the agreed term.", "A minimum duration extending to the end of the registration period in which the contract begins."],
    "The RSTP framework cited sets one year as the minimum and caps under-18 contracts at three years and over-18 contracts at five. The age-based maximum is not described as changing mid-contract. Registration windows do not define the minimum term.")
add(5, "A player has received no salary for two months. Which steps support termination with just cause?",
    ["Confirm that at least two months' salary remains unpaid.", "Put the club on notice and allow at least 15 days.", "Act in good faith after the payment breach remains unresolved.", "Document the serious breach before ending the relationship."],
    ["Give 30 days' notice because termination during the protected period requires a longer opportunity to cure."],
    "Non-payment for at least two months can create just cause if the player first gives the club at least 15 days' notice. Good-faith reliance on a serious unresolved breach is central to just cause. The protected period matters to sanctions for unjustified termination, not to whether an established salary default may be invoked.")
add(5, "A player appeared in 8% of the club's official matches during the season. What special route may be available?",
    ["Termination for sporting just cause within 15 days after the last official match of the season."],
    ["Termination for just cause after giving the club 15 days to provide a sporting opportunity.", "Mutual termination during the next registration period based on insufficient participation.", "A request to suspend the remaining contract until the club offers a defined match role.", "Termination for sporting just cause before the final match if the appearance rate cannot reach 10%."],
    "A player fielded in fewer than 10% of official matches may invoke sporting just cause, but must do so within 15 days of the season's last official match. It is a specific termination ground rather than a right to playing time or suspension. Timing and the completed seasonal percentage are essential.")
add(5, "Which considerations are relevant when calculating compensation for termination without just cause?",
    ["Any contractual penalty or buy-out clause.", "Applicable national law and the specificity of sport."],
    ["The sporting value assigned to the player by the former club at the date of termination.", "The disciplinary sanction expected during the protected period.", "The transfer fee the former club could reasonably have obtained in the next registration window."],
    "Compensation can follow a contractual clause or be calculated using applicable law, the specificity of sport and objective criteria. Those criteria include remuneration, remaining term, amortised fees and the protected period. A speculative market valuation or anticipated disciplinary penalty is not the stated measure.")
add(5, "A player terminates without just cause during the protected period and signs for a new club. Which consequences may follow?",
    ["The player may owe compensation.", "The new club may be jointly and severally liable.", "The player may receive a four- to six-month sporting suspension."],
    ["The new club is sanctioned after the former club proves that it induced the breach.", "The player's suspension runs from the date the employment relationship ended."],
    "An unjustified player termination triggers compensation, shared liability with the new club, and potentially a four- to six-month suspension during the protected period. The new club is presumed to have induced the breach, so the former club need not first prove inducement. The suspension begins when the decision is served and may be postponed during non-playing periods.")
add(5, "A club terminates a player's contract without just cause during the protected period. Which outcome is most directly supported?",
    ["The club may be barred from registering new players for two consecutive registration periods.", "The player may receive residual-value compensation subject to mitigation by a new contract.", "Additional compensation may be available within the stated cap.", "A valid contractual penalty or buy-out clause may govern the financial consequence."],
    ["The player remains registered until the compensation decision becomes final."],
    "The club can face both financial and sporting consequences: compensation and a two-window registration ban. The compensation framework considers residual value and remuneration under a replacement contract, with possible additional compensation. Registration status is not described as continuing until the award.")

# PDF page 6 / handbook pages 302-303: Matuzalem, Mutu and training compensation.
add(6, "Which factors justified the additional specificity-of-sport indemnity in the Matuzalem case?",
    ["He was the team's captain.", "He had recently received a salary increase.", "He left shortly before the club's Champions League campaign."],
    ["The new club obtained his services without paying a transfer fee.", "The contract contained a buy-out figure that exceeded his remaining salary."],
    "CAS considered circumstances showing particular sporting harm: captaincy, the recent raise and the timing before Champions League participation. The €25m buy-out was not used because Shakhtar had received no offers supporting it. The calculation focused on salary difference plus a limited additional indemnity, not simply absence of a transfer fee.")
add(6, "A player leaves without just cause and earns more under the new contract. Which Matuzalem principles guide compensation?",
    ["Compare remuneration under the old and new contracts for the old contract's remaining duration.", "Hold the player and new club jointly and severally liable.", "Consider an additional indemnity when the salary difference is insufficient in the circumstances.", "Limit the additional specificity-of-sport indemnity to a maximum of six months' salary."],
    ["Use the contractual buy-out clause as the minimum compensation unless the former club had accepted a lower offer."],
    "Matuzalem established a salary-difference approach for the remaining term, with shared liability and a possible six-month additional indemnity. A buy-out figure is not automatically the floor; its evidential relevance depends on the circumstances. The method aims at fair compensation for the actual breach.")
add(6, "What distinguished the compensation method in the Mutu case?",
    ["CAS assessed the former club's actual damage, including non-amortised acquisition-related costs."],
    ["CAS compared Mutu's new remuneration with the residual value of his Chelsea contract.", "CAS applied the contractual buy-out clause after adjusting it for the unserved term.", "CAS awarded the replacement cost of a comparable player at the date of termination.", "CAS limited recovery to the salary and sign-on fee outstanding under the old contract."],
    "Mutu used an actual-damage approach rather than the old-versus-new salary comparison. CAS included non-amortised transfer, sign-on, agent and related costs, although it could not award more than Chelsea had requested through confirmation of FIFA's decision. This represents an alternative compensation route for a club harmed by unjustified termination.")
add(6, "A club prepares a claim after a player's unjustified termination. Which lessons emerge from comparing Matuzalem and Mutu?",
    ["Select a calculation method grounded in the evidence of loss.", "Consider salary difference or actual non-amortised damage according to the case facts."],
    ["Claim both methods cumulatively so the adjudicator can remove overlapping amounts.", "Use the player's sporting importance to convert actual damage into a specificity-of-sport award.", "Treat the former transfer fee as the default measure when no reliable new salary is available."],
    "The cases illustrate alternative, evidence-based methods rather than cumulative recovery. Matuzalem centred on remuneration differences and sporting circumstances; Mutu centred on actual non-amortised damage. A claimant must also frame its requested relief carefully because an adjudicator may not award more than sought.")
add(6, "Which clubs may receive FIFA training compensation under the framework described?",
    ["Clubs that actually trained the player between ages 12 and 21.", "Each eligible training club once for its own training period.", "Eligible clubs claiming before the player turns 23."],
    ["Clubs that trained the player after age 21 until the first professional transfer.", "The club holding the player's registration when professional status was first obtained."],
    "Training compensation rewards the clubs that trained the player from 12 to 21, in proportion to their actual training periods, with claims available until age 23. It can be owed to several clubs. Eligibility is not reserved to the club at first professional registration or extended to later training years.")
add(6, "A player signs a first professional contract at 18 after training at several clubs. Which calculation principles apply?",
    ["The new club pays the eligible training clubs.", "The calculation uses standard annual training costs by confederation and club category.", "Years below age 16 are valued using category IV costs.", "The actual training period at each club determines its share."],
    ["The player's former amateur club category sets the annual cost for the full training period."],
    "The new club pays compensation based on FIFA's standard costs, the relevant years and the clubs that provided training. Under-16 training is valued at category IV, while later years generally use the new club's cost category subject to the EU/EEA variation. The former club's category does not set one rate for the whole history.")
add(6, "When is training compensation payable according to the chapter?",
    ["When the player signs the first professional contract."],
    ["At each transfer for a fee until the player reaches age 23.", "When a player first joins a club in a higher training category.", "When the player completes training and begins regular first-team football.", "At each international change of club while the player is under 21."],
    "Training compensation is triggered by the first professional contract and by subsequent changes of club while the relevant training rules still apply. It is distinct from solidarity contribution, which follows fee-paying transfers throughout the career. Professional completion can shorten the compensated training period but is not itself the payment trigger.")
add(6, "A player moved within the EU/EEA from a category III training club to a category I club. Which special rule applies?",
    ["Use the average of the two clubs' category costs for the relevant training years.", "If the move were to a lower category, use the lower category club's costs."],
    ["Use category IV for years spent before the player signed any professional contract.", "Use the new club's category but cap the total at the former club's demonstrated training expenditure.", "Use the former club's category for completed years and the new category for the current season."],
    "Within the EU/EEA, an upward category move uses the average of the old and new club costs, while a downward move uses the lower club's costs. This modifies the general new-club-cost principle. Actual expenditure and split-season category formulas are not the mechanism described.")

# PDF page 7 / handbook pages 304-305: training examples, solidarity and match-fixing definition.
add(7, "A training club failed to offer an eligible player a professional renewal. What risk does it face?",
    ["It may lose its entitlement to training compensation.", "Its actual training contribution remains relevant to solidarity contribution if a later fee-paying transfer occurs.", "The loss turns on the circumstances specified by the training-compensation rules."],
    ["It loses claims under both mechanisms because the pathway ended without a professional offer.", "It retains training compensation if the next club signs the player within the same registration period."],
    "Failure to offer or renew a professional contract can deprive a club of training compensation, as can unjustified termination. Solidarity is a separate redistribution mechanism tied to later transfer fees and training years. The chapter does not make entitlement depend on the timing of the next registration.")
add(7, "Which features distinguish solidarity contribution from training compensation?",
    ["It redistributes 5% of a transfer or loan fee.", "It benefits clubs involved in training from ages 12 to 23.", "It can arise on fee-paying transfers throughout the player's career.", "It is distributed by the buying club after registration."],
    ["It uses the training category of the buying club to allocate each beneficiary's share."],
    "Solidarity contribution allocates 5% of fee-based transfer or loan compensation among training clubs from ages 12 to 23. It can recur through the player's career and the buying club distributes it within 30 days. Club-category training costs belong to the separate training-compensation calculation.")
add(7, "What event most directly triggers solidarity contribution?",
    ["A qualifying transfer or loan for which one club pays compensation to another."],
    ["The player's first professional registration after training in more than one country.", "A change of association before the player reaches the end of the training period.", "A fee-paying transfer to a club in a higher training category.", "A professional transfer occurring before the player's twenty-third birthday."],
    "Solidarity follows a transfer or loan fee, including specified international-dimension cases. It is not confined to a first contract, an upward category move or a young-player transfer. The player's training history determines beneficiaries after the financial trigger occurs.")
add(7, "A foreign-origin player moves for a fee between two clubs in the same country. Which solidarity principles are relevant?",
    ["A national transfer can have the international dimension required for solidarity.", "The buying club should retain and distribute the 5% share."],
    ["Solidarity applies because the player's training clubs belong to more than one association.", "The national association distributes the contribution after verifying the player's passport.", "The selling club deducts solidarity from the fee before issuing the transfer instruction."],
    "The chapter recognises a national transfer or loan with an international dimension when a foreign-origin player moves domestically. The buying club retains 5% and pays eligible training clubs. The mechanism does not shift distribution to the association or selling club.")
add(7, "A player trained at one club from ages 12 to 15 and another from 16 to 19. Which solidarity allocation principles apply?",
    ["Each eligible season from ages 12 to 15 receives a smaller percentage than seasons from 16 onward.", "Both clubs share the 5% according to the years they trained the player.", "The allocation is based on the player's training record rather than the clubs' current categories."],
    ["The later club receives the full contribution if it signed the player's first professional contract.", "The earlier club's share stops accruing once the player completes professional training."],
    "The solidarity schedule allocates 0.25% of the transfer fee for each year from 12 to 15 and 0.5% for each year from 16 to 23, totalling 5%. Each training club receives the amounts attached to its seasons. Professional status and club category do not erase the earlier club's contribution.")
add(7, "A buying club registers a transferred player. Which administrative steps follow for solidarity contribution?",
    ["Retain 5% of the transfer or loan compensation.", "Identify the clubs that trained the player between 12 and 23.", "Allocate shares according to the applicable training years.", "Distribute the amounts within 30 days of registration."],
    ["Pay the 5% to the former association, which settles claims submitted by training clubs."],
    "The buying club is responsible for retaining, calculating and distributing the solidarity share to the training clubs within 30 days. The player passport or equivalent history supports identification and allocation. The chapter does not place the fund with the former association.")
add(7, "How is match-fixing defined in the Macolin and Olympic Movement frameworks?",
    ["An intentional arrangement, act or omission aimed at improperly altering a competition's result or course."],
    ["Conduct that changes a sporting result to obtain a financial benefit for a participant or third party.", "An agreement that removes the unpredictable nature of a match through betting activity.", "An intentional influence on a competition that produces an improper advantage.", "A concealed arrangement between participants that compromises the integrity of the final result."],
    "The definition covers an intentional arrangement, act or omission aimed at an improper alteration of result or course, removing unpredictability to obtain an undue benefit for oneself or others. Actual success, a purely financial benefit and participant collusion are not required by that definition. Its scope reaches attempts and different forms of advantage.")
add(7, "Why should a legal team keep training compensation and solidarity contribution analytically separate?",
    ["They have different triggering events and beneficiary age ranges.", "Training compensation uses standard training costs, while solidarity uses a percentage of a transaction fee."],
    ["Training compensation protects contractual stability, while solidarity compensates clubs for early professionalisation.", "Training compensation applies to international moves, while solidarity governs transfers within one association.", "Training compensation is paid once per player, while solidarity is paid once to each training club."],
    "Training compensation is linked to professional signing and qualifying club changes, using category costs for training mainly from 12 to 21. Solidarity follows fee-paying transfers and loans, allocating 5% across training from 12 to 23 throughout the career. Confusing the mechanisms leads to errors in trigger, rate and beneficiary analysis.")

# PDF page 8 / handbook pages 306-307: match-fixing enforcement and Pobeda.
add(8, "A player passes confidential team information to a relative who bets on the match. Which UEFA integrity concepts are engaged?",
    ["Indirect betting activity connected to a competition.", "Use or disclosure of non-public information obtained through football.", "Potential damage to match or competition integrity."],
    ["Match manipulation if the relative's bet changes the betting market.", "Strict liability of the player's club for the relative's conduct."],
    "UEFA's rules cover direct and indirect betting interests and misuse of inside football information. The integrity offence does not require the bet to move a market or alter the match. Club strict liability concerns specified people connected with the club, not a free-standing rule that makes it answer for any relative.")
add(8, "Which elements can establish a match-integrity violation under the UEFA account?",
    ["Intentional unlawful or undue influence.", "A purpose of gaining an advantage for oneself or another.", "Influence on the course or result of a match or competition.", "Conduct that is likely to produce the prohibited effect even if it fails."],
    ["Proof that the advantage was financial or connected to betting."],
    "The offence focuses on intentional undue influence for an advantage and includes conduct likely to affect the match even without success. Betting is one possible form, not a required element, and the advantage need not be purely financial. This makes attempted manipulation disciplinarily relevant.")
add(8, "A club official learns of an approach to manipulate a match but takes no action. Which duty is most directly breached?",
    ["The duty to report forbidden behaviour to UEFA immediately and voluntarily."],
    ["The duty to cooperate after UEFA opens a disciplinary investigation.", "The duty to protect non-public information obtained through the official's position.", "The duty to prevent members from exposing the club to strict liability.", "The duty to disclose integrity concerns through the national association's disciplinary body."],
    "The UEFA rule expressly makes failure to report forbidden behaviour immediately and voluntarily a breach. That duty arises before a formal cooperation request. It is distinct from confidentiality, preventive club governance and routing a case through a national body.")
add(8, "An association relies on careful supervision as a defence to supporter conduct. How does strict liability affect the argument?",
    ["The association may be responsible for specified connected persons despite proving absence of fault.", "The disciplinary body can sanction the entity without establishing negligence."],
    ["Strict liability applies after the underlying individual has been identified and sanctioned.", "The association remains entitled to avoid liability by proving an effective compliance programme.", "Strict liability concerns match officials and players, while supporter cases require organisational fault."],
    "UEFA and FIFA can hold associations and clubs responsible for members, players, officials, supporters and persons acting on their behalf without proof of entity fault. Due diligence may matter in mitigation but does not defeat the strict-liability basis described. Prior identification or sanction of an individual is not stated as a condition.")
add(8, "Which evidential features supported the finding in the FK Pobeda case?",
    ["Extraordinary betting patterns supported by expert analysis.", "Evidence of serious financial problems.", "Witness evidence implicating the club president."],
    ["The team's poor performance established intentional manipulation when combined with abnormal betting.", "Bookmakers suspended the market after detecting bets linked to club officials."],
    "CAS relied on the expert betting report, the club's financial context and incriminating witness evidence. Bad performance alone was insufficient, although it supported the wider evidential picture and bookmakers' behaviour. The case illustrates cumulative circumstantial proof rather than one decisive match observation.")
add(8, "A disciplinary body is evaluating suspected match-fixing. Which evidence approach follows the chapter?",
    ["Consider different forms of evidence without a closed evidential list.", "Respect human dignity in gathering and using evidence.", "Evaluate the evidence with the body's permitted discretion.", "Allow rebuttal of facts recorded in official UEFA reports."],
    ["Require direct evidence of an agreement when circumstantial evidence includes suspicious betting patterns."],
    "FIFA and UEFA bodies may use varied direct and circumstantial evidence and exercise broad evaluative discretion, while respecting human dignity. Official UEFA reports carry a rebuttable presumption of accuracy. The Pobeda case shows that a coherent circumstantial case can establish manipulation without a recorded agreement.")
add(8, "What is the institutional role of the CAS in FIFA and UEFA disciplinary systems?",
    ["It acts as an independent private tribunal reviewing eligible internal final-instance decisions."],
    ["It supervises federation investigations when sanctions can affect international competitions.", "It replaces internal appeal bodies for integrity offences involving clubs from different associations.", "It enforces federation decisions worldwide through the Swiss arbitral system.", "It provides a public-law appeal where federation procedures do not protect fundamental rights."],
    "CAS is an independent arbitral tribunal of last instance for appeals allowed by the relevant sporting rules and arbitration clause. Its awards are final and binding, subject to very limited SFT challenge. It does not investigate for federations or function as a public court.")
add(8, "A federation is setting limitation rules for match-fixing. Which comparison reflects the handbook?",
    ["UEFA treats match-fixing as not subject to a limitation period.", "FIFA generally applies a ten-year limitation period.", "FIFA identifies a specific exception concerning inducement of certain football actors to breach its rules."],
    ["UEFA's absence of limitation applies to entity liability, while individual prosecutions retain the standard period.", "FIFA's limitation period begins when the disciplinary body receives credible evidence of manipulation."],
    "The chapter contrasts UEFA's no-limitation approach with FIFA's general ten-year period and a stated exception for certain incitement cases. It does not divide UEFA limitation by defendant type or tie FIFA's clock to discovery by the body. The comparison is important when assessing prosecutorial timing.")

# PDF page 9 / handbook pages 308-309: UEFA and FIFA disciplinary structures.
add(9, "Which bodies form the principal internal disciplinary structures described?",
    ["UEFA Control, Ethics and Disciplinary Body.", "UEFA Appeals Body.", "FIFA Disciplinary Committee."],
    ["FIFA Dispute Resolution Chamber for disciplinary and doping offences.", "UEFA Club Financial Control Body as the general ethics appeal body."],
    "UEFA uses the CEDB and Appeals Body for disciplinary and ethical matters, while FIFA uses the Disciplinary Committee and Appeal Committee for disciplinary and doping matters and a separate Ethics Committee. Other specialised bodies may issue important decisions but do not replace this structure. Correct identification determines the proper first instance and appeal route.")
add(9, "A member association failed to prosecute a serious UEFA statutory violation appropriately. Which responses are available?",
    ["The CEDB may prosecute the serious violation.", "The CEDB's jurisdiction can cover both disciplinary and ethical matters.", "An urgent participation issue may be referred directly to the Appeals Body by the CEDB chairperson.", "The competent UEFA body derives its authority from the disciplinary regulations."],
    ["The Appeals Body may assume first-instance jurisdiction when the association's internal remedy has failed."],
    "The CEDB can intervene where a national association or its members fail to prosecute a serious breach of UEFA's statutory objectives. Urgent cases can be referred directly to the Appeals Body by the CEDB chairperson. That is a defined referral power, not a general Appeals Body power to replace national proceedings.")
add(9, "When may the UEFA CEDB chairperson decide as a judge sitting alone?",
    ["In urgent and protest cases, and within specified limits for fines, warnings, reprimands or match suspensions."],
    ["When the ethics and disciplinary inspector and respondent propose the same disciplinary measure.", "When the alleged offence concerns one individual rather than a club or association.", "When the available evidence consists primarily of an official match report.", "When the sanction sought does not affect participation in a future UEFA competition."],
    "The chairperson's single-judge jurisdiction is defined by urgency, protests and stated sanction thresholds, including fines up to CHF 45,000 and suspensions up to three matches. Agreement of the parties is listed in relation to certain Appeals Body decisions, not this CEDB power. Case type and evidential form do not independently create jurisdiction.")
add(9, "A party wants to appeal a CEDB decision. Which institutional steps apply?",
    ["File the appeal with the UEFA Appeals Body.", "Establish that the party is directly affected by the decision."],
    ["Request the CEDB chairperson to certify that the issue is appealable.", "Exhaust a review by the ethics and disciplinary inspector before approaching the Appeals Body.", "Demonstrate that the expected sanction exceeds the CEDB single-judge threshold."],
    "The Appeals Body hears appeals by directly affected parties, subject to exclusions in the regulations. Appealability is not tied to the single-judge threshold or an inspector review. After the internal final decision, an eligible CAS appeal may follow under the separate rules.")
add(9, "Why do the UEFA and FIFA disciplinary codes matter beyond listing offences?",
    ["They define available sanctions.", "They organise and allocate functions among decision-making bodies.", "They regulate the procedures used to determine violations."],
    ["They determine which state law governs enforcement of each sanction.", "They establish the CAS standard of review for appeals from internal bodies."],
    "The codes provide the substantive offences and sanctions as well as institutional jurisdiction and procedure. That makes them the starting point for a disciplinary case. Applicable state law and CAS review arise from wider legal and arbitral frameworks, not solely from the offence code.")
add(9, "A national association is sanctioned in a UEFA case. Which types of measure can the regulatory framework contemplate?",
    ["A financial fine imposed on the association.", "A deduction of points in a current or future competition.", "Full or partial closure of the association's stadium.", "Exclusion from an ongoing or future UEFA competition."],
    ["Suspension of the association's voting rights at UEFA Congress as a disciplinary measure."],
    "UEFA's measures against associations and clubs range from warnings and fines to match, registration, stadium and competition consequences. The precise sanction depends on the offence and proportionality. Congress voting suspension is not included in the measures shown on the cited page.")
add(9, "Which distinction between UEFA and FIFA ethics governance is central at the overview stage?",
    ["UEFA includes ethical provisions within its disciplinary framework, while FIFA has a separate Code and Ethics Committee."],
    ["UEFA's Appeals Body reviews ethics cases, while FIFA ethics decisions proceed directly to CAS.", "UEFA appoints independent inspectors, while FIFA delegates ethics investigation to national associations.", "FIFA's Ethics Committee covers disciplinary offences involving officials, while its Disciplinary Committee covers players and clubs.", "FIFA ethics procedure is governed by the WADA-based disciplinary code rather than its general code."],
    "UEFA's disciplinary structure incorporates ethical matters, whereas FIFA uses a separate Ethics Code and two-chamber Ethics Committee. Appeal routes have specific exceptions and cannot be reduced to a single direct-CAS distinction. The split is by subject matter, not simply by the status of the accused.")

# PDF page 10 / handbook pages 310-311: UEFA investigators, appeals and evidence.
add(10, "Which functions may UEFA ethics and disciplinary inspectors perform?",
    ["Represent UEFA before the CEDB and Appeals Body.", "Initiate disciplinary investigations."],
    ["Issue provisional measures when a case presents a risk of irreparable harm.", "Refer urgent first-instance matters directly to the Appeals Body.", "Request grounds on behalf of a sanctioned party before deciding whether to appeal."],
    "EDIs represent UEFA, may investigate, propose standard measures, appeal CEDB decisions and support UEFA before CAS. Provisional measures and urgent referrals are judicial powers exercised within the procedural structure. A party must manage its own request for grounds and appeal rights.")
add(10, "An individual is involved in UEFA proceedings and needs representation. Which support routes are described?",
    ["Representation by the person's own counsel.", "Representation by another chosen representative.", "Pro bono counsel provided by UEFA."],
    ["Appointment of UEFA counsel when a football-activity ban is possible.", "Representation through the national association that handles procedural communications."],
    "Parties can use their own counsel, another representative or UEFA-provided pro bono counsel, and legal aid can be available. Communication may pass through a club or association, but that does not make it the legal representative. Appointment is not stated as automatic based on sanction severity.")
add(10, "A directly affected club receives a reasoned CEDB decision. Which appeal steps are required?",
    ["File the declaration of appeal within three days.", "Submit grounds within five days after that deadline expires.", "Include facts, evidence, legal requests and prayers for relief.", "Pay the CHF 1,000 fee unless an exemption applies."],
    ["Reserve additional evidence for a reply after UEFA answers the appeal."],
    "The UEFA internal appeal timetable is short and front-loaded. The appellant must put the complete factual, evidential and remedial case forward by the deadline and cannot later add submissions or evidence. The fee exemption is narrow, including specified doping-player and EDI appeals.")
add(10, "Which UEFA first-instance outcome is expressly excluded from internal appeal?",
    ["A warning issued by the competent UEFA disciplinary body."],
    ["A reprimand combined with a procedural-cost order.", "A one-match suspension imposed after a protest proceeding.", "A two-match suspension imposed for a disciplinary offence.", "A fine falling within the CEDB chairperson's single-judge authority."],
    "The express exclusions include a warning, a reprimand and a one-match automatic suspension after dismissal. The listed alternatives add another consequence or concern a different suspension or fine, so appealability must be checked under the ordinary rules. The decision-maker's single-judge authority does not itself remove the right of appeal.")
add(10, "How should official UEFA reports be treated as evidence?",
    ["Their facts are presumed accurate.", "A party may prove that reported facts are inaccurate."],
    ["They prevail over video evidence unless the reporting official corrects the record.", "They shift the burden of proving the offence from UEFA to the respondent.", "They are conclusive on observable conduct but open to challenge on intent."],
    "Official reports receive a rebuttable presumption of accuracy. The party may challenge them with evidence, and the disciplinary body retains discretion over the complete record. The presumption does not make the report conclusive or reverse the ultimate duty to prove the accusation.")
add(10, "A party fears immediate exclusion will cause irreparable harm before the appeal is decided. Which procedural tools are relevant?",
    ["Request provisional measures.", "Explain how the measure supports justice or sporting discipline.", "Show the risk of irreparable harm or a safety and security reason."],
    ["Ask for suspension of the decision upon payment of the appeal fee.", "Request a public hearing so the Appeals Body can assess urgency transparently."],
    "UEFA allows a party to request provisional measures to protect justice, discipline, safety or against irreparable harm. Relief is discretionary rather than an automatic effect of appealing. Hearings are non-public and do not supply the legal basis for interim protection.")
add(10, "What is the normal form of UEFA disciplinary proceedings?",
    ["Written proceedings, with CEDB hearings exceptional and Appeals Body hearings available on request."],
    ["A recorded hearing at first instance when witness credibility is disputed.", "Written proceedings before CEDB followed by an oral appeal if the sanction affects competition participation.", "A private hearing whenever anonymous witness evidence is relied upon.", "An oral procedure when a party has requested reasons for the operative decision."],
    "The default is written procedure. CEDB hearings are exceptional, and Appeals Body hearings may be requested; hearings remain private and recorded. Neither sanction type nor a request for reasons creates an automatic oral phase.")
add(10, "A party receives an unreasoned operative UEFA Appeals Body decision. Which next steps preserve a CAS appeal?",
    ["Request the grounds within five days of receiving the operative part.", "File the CAS appeal within ten days of receiving the reasoned decision."],
    ["File a protective CAS appeal within ten days of the operative part while requesting reasons.", "Ask the EDI to confirm whether the Appeals Body decision is a final internal decision.", "Wait for UEFA to issue reasons because appealable decisions must be reasoned on its own initiative."],
    "UEFA decisions are generally issued without grounds, so the party must request them within five days. The CAS deadline then runs from receipt of the reasoned decision. Assuming reasons will follow or appealing before the stated trigger risks mishandling the procedural sequence.")

# PDF page 11 / handbook pages 312-313: FIFA disciplinary and ethics procedure.
add(11, "Which procedural features distinguish FIFA Disciplinary Committee proceedings from UEFA proceedings?",
    ["Spanish is an additional official language.", "The DC secretariat investigates ex officio under its chairperson."],
    ["FIFA issues reasoned first-instance decisions, while UEFA requires a request.", "FIFA permits public hearings when an offence has an international dimension.", "The DC chairperson refers ethical allegations to the Investigatory Chamber before opening a case."],
    "FIFA adds Spanish and uses its Disciplinary Committee secretariat rather than UEFA-style inspectors for ex officio investigation. Grounds still must be requested, with a ten-day period, and hearings are generally private. Ethics matters are governed separately rather than routed by the DC as part of each disciplinary case.")
add(11, "When may the FIFA Disciplinary Committee's single judge act within the examples given?",
    ["Urgent or protest cases.", "Suspensions up to four matches or three months.", "Fines up to CHF 50,000."],
    ["Cases in which a national body requests worldwide extension of its sanction.", "Cases resolved through a proposed sanction before the investigation is complete."],
    "The single judge has defined jurisdiction by case type and sanction thresholds and can, under conditions, propose a sanction before proceedings commence. Worldwide extension is a chairperson power but not presented as one of the listed single-judge examples. A proposed sanction is a procedural mechanism, not an unfinished investigation shortcut.")
add(11, "A national body imposes a sanction for a serious match-fixing offence. Which extension mechanisms may apply?",
    ["The FIFA DC chairperson may extend its effects worldwide.", "A serious offence is required within the categories described.", "UEFA may extend effects to UEFA competitions on request in qualifying cases.", "Comparable extension can apply to doping sanctions from recognised bodies."],
    ["The CAS must confirm the sanction before it can operate beyond the issuing body's territory."],
    "FIFA and UEFA have mechanisms to extend serious sanctions beyond the original jurisdiction, including match-fixing and doping measures. The requirements and requesting route differ by body. CAS confirmation is not a prerequisite in the process described.")
add(11, "Who may appeal a FIFA Disciplinary Committee decision to the Appeal Committee?",
    ["A party to the proceedings with a legally protected interest."],
    ["A club affected competitively by a sanction imposed on another club.", "A national association where the sanctioned person is one of its registered players.", "Any football body seeking worldwide extension of the disciplinary measure.", "A complainant who supplied the evidence underlying the disciplinary case."],
    "The general test is party status plus a legally protected interest. Associations and clubs also have a specified right to appeal sanctions against their players, officials or members, but mere competitive or evidential interest is insufficient. The procedural connection to the sanctioned person must match the rule.")
add(11, "A club appeals a FIFA disciplinary decision. Which timing and effect rules apply?",
    ["Notify the intention to appeal within three days.", "File the appeal brief and fee within the next five days."],
    ["The appeal suspends sporting sanctions while the chairperson considers any stay request.", "The appeal brief may reserve evidence that was unavailable during the three-day notice period.", "A CHF 1,000 fee is paid after the Appeal Committee confirms admissibility."],
    "The appeal starts with a three-day notice, followed by five more days for the complete brief and CHF 1,000 fee. It generally lacks suspensive effect except for monetary decisions, although the chairperson can grant a stay. The source does not describe a later evidence reservation or admissibility-first payment.")
add(11, "How is a FIFA Ethics Committee case divided between its two chambers?",
    ["The Investigatory Chamber examines the allegation and prepares a final report.", "The Adjudicatory Chamber decides whether to close or adjudicate the case.", "The Investigatory Chamber may conduct preliminary and full investigations."],
    ["The Adjudicatory Chamber approves the opening of investigations involving external complainants.", "The Investigatory Chamber imposes provisional sanctions before referring the final report."],
    "The EIC investigates and submits facts, evidence and possible offences; the EAC independently determines whether to close or proceed to adjudication. Anyone may complain, but the chamber chairperson controls the investigatory threshold. The division separates investigation from judgment.")
add(11, "A FIFA ethics investigation concerns alleged bribery and match manipulation. Which settlement rule applies?",
    ["A plea bargain is unavailable for those accusations.", "The Investigatory Chamber must present the evidence and possible offences in its final report."],
    ["A plea bargain may address bribery if the match-manipulation allegation proceeds to adjudication.", "The EAC can ratify a settlement after narrowing the accusation to a monetary ethics offence.", "The parties may agree facts while leaving sanction to the EAC chairperson under the plea procedure."],
    "The Code account excludes plea bargains for bribery, misappropriation of funds and competition manipulation. The EIC must investigate and report, and the EAC decides the adjudicatory course. Recharacterising or splitting the accusations does not create the settlement route described.")

# PDF page 12 / handbook pages 314-315: adjudication, ethics appeals and standard of proof.
add(12, "A case reaches the FIFA Ethics Committee's Adjudicatory Chamber. Which safeguards and powers apply?",
    ["The concerned party may submit a written position and evidence.", "The party may request a private hearing.", "The EAC may depart from and even extend the EIC's accusation.", "A reasoned written decision must be issued."],
    ["The EIC's recommended sanction limits the maximum measure available to the EAC."],
    "The adjudicatory phase protects the right to be heard and permits a private hearing, while leaving the EAC independent of the EIC's legal characterisation. Decisions are reasoned in writing, with urgent operative parts followed by grounds. The investigating chamber's recommendation does not cap adjudication.")
add(12, "Which FIFA ethics decisions ordinarily go to the Appeal Committee before CAS?",
    ["Decisions concerning manipulation of matches or competitions."],
    ["Decisions extending an EIC accusation during adjudication.", "Decisions imposing a ban on football-related activity.", "Decisions based on a complaint filed by someone outside FIFA.", "Decisions ratifying a plea bargain agreement."],
    "Ethics decisions are generally appealed directly and exclusively to CAS by eligible parties, but match-manipulation decisions may go through the FIFA Appeal Committee. The route depends on subject matter rather than sanction type, complainant identity or how the EAC framed the case.")
add(12, "What does the EAC chairperson have authority to decide alone?",
    ["Specified measures such as monetary sanctions, warnings, reprimands or compliance training.", "Ratification of a plea bargain agreement."],
    ["Closure of a case because the EIC report contains insufficient evidence.", "An extension of the accusation to a more serious ethics offence.", "An appealable match-manipulation sanction within the Disciplinary Committee threshold."],
    "The source gives the chairperson single-person authority for listed lower-level measures and plea-bargain ratification. Decisions on evidential closure or materially reshaping a contested accusation belong to the adjudicatory process. Disciplinary Committee thresholds do not define Ethics Committee jurisdiction.")
add(12, "A disciplinary panel says the evidence is slightly more persuasive than the defence. Why may that be insufficient?",
    ["UEFA and FIFA use comfortable satisfaction rather than a mere balance of probabilities.", "The panel must be convinced that the fact occurred.", "The required satisfaction rises with the gravity of the violation and sanction."],
    ["Comfortable satisfaction requires corroboration when the primary evidence is circumstantial.", "The panel must address reasonable alternative explanations as a separate proof requirement."],
    "Comfortable satisfaction sits above the balance of probabilities and below proof beyond reasonable doubt. Its intensity is flexible: more serious accusations and sanctions demand greater satisfaction. It does not impose fixed corroboration or the criminal-law requirement to eliminate reasonable doubt.")
add(12, "Which statements correctly compare the three proof levels shown?",
    ["Balance of probabilities is the lower threshold.", "Comfortable satisfaction occupies an intermediate position.", "Beyond reasonable doubt is the most demanding of the three.", "Serious disciplinary cases require stronger satisfaction within the intermediate standard."],
    ["Comfortable satisfaction becomes equivalent to beyond reasonable doubt when a lifetime ban is possible."],
    "The framework places comfortable satisfaction between civil balance and criminal beyond-reasonable-doubt proof. Its application becomes more exacting as seriousness increases but does not transform into the criminal standard. The disciplinary body still evaluates the whole evidence with discretion.")
add(12, "What is the central meaning of comfortable satisfaction?",
    ["The disciplinary body is convinced by the evidence that the fact actually occurred."],
    ["The evidence makes the alleged fact materially more likely than competing explanations.", "The evidence meets a percentage threshold adjusted to the proposed sanction.", "The accusation is supported by reliable evidence from more than one source.", "The evidence would satisfy an experienced sports adjudicator despite procedural gaps."],
    "Comfortable satisfaction is a qualitative state of conviction, not a numerical percentage or a source-count rule. It is stricter than mere probability while remaining below criminal proof. The seriousness of the matter affects how much conviction is required.")
add(12, "A federation is designing disciplinary training for investigators and adjudicators. Which distinction should it emphasise?",
    ["Investigators gather and present a case, while adjudicators independently evaluate whether it is proved.", "The standard of proof governs the adjudicator's level of conviction, not the investigator's charging threshold."],
    ["Investigators apply balance of probabilities, while adjudicators apply comfortable satisfaction to the same evidence.", "Adjudicators may rely on the investigating chamber's credibility findings unless rebutted by the party.", "The charging threshold rises to comfortable satisfaction when the proposed sanction is severe."],
    "The FIFA ethics structure separates investigation and adjudication, and the EAC is not bound by the EIC's findings. Comfortable satisfaction governs proof of the offence at decision, whereas a prima facie or sufficient-evidence threshold can initiate and advance investigation. Treating those stages as two fixed proof standards would blur their distinct functions.")

# PDF page 13 / handbook pages 316-317: ICAS, CAS divisions, arbitrators and rules.
add(13, "Which features describe the institutional relationship between ICAS and CAS?",
    ["CAS operates under the aegis of ICAS.", "ICAS is a Swiss foundation.", "ICAS designates arbitrators and mediators on the closed lists."],
    ["CAS itself has legal personality as ICAS's adjudicatory branch.", "ICAS reviews CAS awards before they become enforceable worldwide."],
    "CAS has no legal personality and operates under ICAS, the Swiss foundation responsible for institutional governance and list appointments. CAS panels issue the arbitral awards. ICAS does not serve as an internal merits-review body for those awards.")
add(13, "A dispute must be directed to the appropriate CAS division. Which pairings are correct?",
    ["Appeals Division - challenges to sports-body decisions under a regulatory arbitration clause.", "Ordinary Division - contractual disputes under an arbitration clause or specific agreement.", "Anti-Doping Division - first-instance doping matters delegated by an international federation.", "Ad Hoc Division - disputes arising during major sports events."],
    ["Ordinary Division - review of disciplinary decisions when the federation waives its internal appeal."],
    "The four divisions are distinguished by the source and timing of jurisdiction: appeals, contractual arbitration, delegated doping cases and event-time emergencies. A federation decision remains an appeal-type dispute even if the internal route is structured differently. The arbitration clause, not convenience, determines the division.")
add(13, "What is the purpose of the CAS football list?",
    ["It identifies arbitrators with football relevance within the broader general closed list."],
    ["It restricts football appeals to arbitrators accepted by FIFA and UEFA.", "It supplies mandatory sole arbitrators for lower-value football disputes.", "It separates football contractual cases from disciplinary appeals for appointment purposes.", "It enables parties to appoint specialists outside the general CAS list."],
    "The football list is a voluntary, non-mandatory subset of the general closed list, containing more than 100 football-oriented arbitrators. Parties still appoint within the CAS closed-list framework. It is not a separate compulsory jurisdictional list or a route to external appointments.")
add(13, "How do arbitrator lists differ for the CAS Anti-Doping Division?",
    ["There is a separate closed list of eligible anti-doping arbitrators.", "Some listed arbitrators may be nominated by parties while others are reserved for CAS appointment."],
    ["The anti-doping list is drawn from the general list after parties agree that specialist expertise is needed.", "WADA selects a sub-list for cases involving non-compliance by signatories.", "Anti-doping parties may choose a general-list arbitrator if the division president consents."],
    "The Anti-Doping Division has its own 45-person closed list with appointment roles divided between party nominees and CAS-appointed sole arbitrators or presidents. A further ten-person list handles WADA non-compliance through CAS nomination. These are institutional designations rather than ad hoc party choices from the general list.")
add(13, "Which instruments regulate the different CAS processes?",
    ["The CAS Code contains the ICAS Statutes and general CAS Procedural Rules.", "CAS Mediation Rules govern mediation.", "Separate Anti-Doping Division rules govern that division."],
    ["The Olympic Charter governs Ad Hoc Division procedure during the Olympic Games.", "Federation appeal regulations govern the CAS procedure after jurisdiction is established."],
    "The CAS Code supplies the core institutional and procedural framework, supplemented by mediation, anti-doping and event-specific arbitration rules. The Olympic Games use dedicated CAS arbitration rules, not the Olympic Charter as the procedure. Federation regulations create appeal rights and deadlines but do not replace CAS procedure.")
add(13, "A football contractual dispute might be suitable for mediation. Which conditions follow the chapter?",
    ["The parties must consent.", "A mediator is appointed through the CAS Court Office from a closed list.", "The mediator is designated within the ICAS-controlled institutional framework.", "Mediation is distinct from adjudication by an arbitral panel."],
    ["The Ordinary Division first confirms CAS jurisdiction before referring the parties to mediation."],
    "CAS mediation depends on party consent and uses mediators appointed by the Court Office from an ICAS-designated list. It is a consensual process separate from an arbitral award. The source does not require an Ordinary Division jurisdiction ruling as a preliminary step.")
# PDF page 14 / handbook pages 318-319: CAS jurisdiction, appointments and written phase.
add(14, "A party files at CAS without identifying an arbitration clause. Why is that a fundamental problem?",
    ["CAS jurisdiction depends on a binding arbitration agreement.", "CAS is not a compulsory public tribunal."],
    ["CAS requires the sports body's consent after a dispute arises unless its internal remedies are complete.", "CAS jurisdiction exists through membership of a FIFA-affiliated national association.", "ICAS must confirm that the dispute falls within one of the four CAS divisions."],
    "CAS authority is consensual and must rest on a binding arbitration clause in regulations, a contract or an ad hoc agreement. It does not arise simply from football membership or from classifying the case into a division. Without agreement binding all parties, CAS cannot act like a state court.")
add(14, "Where can a valid CAS arbitration agreement be located?",
    ["In federation statutes or regulations.", "In a contract.", "In an ad hoc agreement concluded before or after the dispute."],
    ["In a national law recognising CAS as the final tribunal for sports disputes.", "In the CAS Code once a party files a statement of appeal."],
    "The consent may be embedded in sporting rules accepted by the parties, negotiated in a contract or given through a specific ad hoc agreement. The CAS Code regulates proceedings but does not create consent by filing. Domestic recognition of arbitration likewise does not itself establish jurisdiction.")
add(14, "Which appointment distinction applies between the CAS Ordinary and Appeals Divisions?",
    ["In both, each party appoints an arbitrator.", "In the Ordinary Division, the party-appointed arbitrators nominate the president.", "In the Appeals Division, the division president nominates the panel president.", "The parties may agree to a sole arbitrator under the applicable process."],
    ["In the Appeals Division, the sports body appoints the president when its decision is under review."],
    "For a three-member panel, party nominations occur in both ordinary and appeal cases, but the source of the president differs. Ordinary co-arbitrators nominate the president, while the Appeals Division president does so in appeals. The respondent sports body receives no special power to chair its own appeal.")
add(14, "A party discovers a possible lack of arbitrator independence. What procedural step is required?",
    ["Challenge the arbitrator within seven days of discovering the reason."],
    ["Ask the appointing party to replace the arbitrator before the written phase closes.", "Notify the panel president and preserve the objection for any SFT appeal.", "Request ICAS to investigate impartiality before the arbitrator accepts appointment.", "File a challenge within seven days of the arbitrator's nomination."],
    "A challenge based on independence or impartiality must be filed within a maximum of seven days after discovery of the reason. The trigger is knowledge of the ground, not necessarily nomination. Preserving the issue without a timely challenge risks losing the procedural remedy.")
add(14, "A party wants CAS proceedings in a language outside English, French and Spanish. Which rules apply?",
    ["The parties may agree on another language.", "The panel and division president must consent."],
    ["The requesting party must fund interpretation and translation before consent is granted.", "The language must be an official language of the sports body whose decision is challenged.", "The division president chooses another language when the parties disagree."],
    "English, French and Spanish are official CAS languages. Another language is possible by agreement with institutional consent; if the parties disagree, the division president decides the language, but not necessarily the requested non-official one. The source does not make cost or federation-language status the legal criterion.")
add(14, "A CAS panel is deciding the merits of a federation dispute. Which legal sequence is supported?",
    ["Apply the sports body's regulations first.", "Apply the law chosen in the contract or regulations in addition.", "Absent a choice, apply the law of the sports body's seat."],
    ["Apply Swiss law first where the federation and CAS are located in Switzerland.", "Use the law most closely connected to the athlete when the parties' choice creates unfairness."],
    "The panel starts with the relevant sports regulations and supplements them with the chosen law. Without a choice, the law of the body's seat applies, often Swiss law for international federations based there. CAS may apply other appropriate rules with reasons, but the basic sequence is not displaced by CAS's own location.")
add(14, "What must a CAS statement of appeal ordinarily contain at the opening stage?",
    ["Identification of the parties and the challenged decision.", "The arbitration clause supporting CAS jurisdiction.", "The nominated arbitrator and prayers for relief.", "Proof of the minimum Court Office fee and any relevant provisional-measures request."],
    ["The complete legal argument and witness evidence on which the appeal will rely."],
    "The statement of appeal establishes the appeal, jurisdiction, requested relief, appointment and fee. The detailed facts, evidence and legal arguments belong to the later appeal brief. Separating the two filings is essential to meeting the non-extendable appeal deadline without confusing it with the brief deadline.")

# PDF page 15 / handbook pages 320-321: CAS procedure, costs, awards and SFT review.
add(15, "Which deadline is expressly non-extendable in CAS appeal proceedings?",
    ["The deadline for filing the appeal itself."],
    ["The ten-day period for filing the appeal brief after the appeal deadline expires.", "The respondent's 20-day period for filing its response.", "The five-day period for appointing the respondent's arbitrator.", "The three-month target for issuing the award after referral to the panel."],
    "The appeal must be filed within the federation's specified deadline or the default 21 days, and that appeal deadline cannot be extended. The appeal-brief period may be extended on request, and other procedural periods operate differently. Missing the jurisdictional appeal deadline is therefore especially serious.")
add(15, "What should the CAS appeal brief add to the statement of appeal?",
    ["A full account of relevant facts.", "Evidence, including documents, experts or witnesses."],
    ["A renewed nomination of the appellant's arbitrator after the respondent has appointed its nominee.", "A response to any anticipated challenge to CAS jurisdiction.", "Proof that internal federation remedies were exhausted through a reasoned final decision."],
    "The appeal brief develops the merits through facts, evidence, legal arguments and the requested disciplinary or monetary relief. The statement already handles the arbitrator nomination and jurisdiction clause. A jurisdiction defence belongs to the respondent's possible response rather than an obligatory speculative rebuttal.")
add(15, "A competition starts before a CAS appeal can be decided. Which provisional measures may address the risk?",
    ["A stay of the challenged decision.", "Permission for an athlete to participate.", "Temporary permission for an official or member to attend a congress or assembly."],
    ["An expedited merits award based on the statement of appeal.", "Suspension of the federation's jurisdiction until the panel is constituted."],
    "CAS can issue conservatory or regulatory measures to avoid irreparable harm and preserve rights while the case proceeds. Examples include staying a decision or temporarily allowing participation. Those measures do not replace the merits proceeding or suspend the sports body's legal authority generally.")
add(15, "Which statements describe the CAS oral phase?",
    ["A hearing may be waived by agreement or by the panel president.", "The panel may decide on written submissions where issues are primarily legal.", "Hearings can occur outside CAS headquarters or by videoconference.", "The sequence can include openings, witness and expert examination, and closing submissions."],
    ["A party is entitled to an oral hearing when witness evidence was included in the appeal brief."],
    "An oral hearing is not inevitable. The panel can proceed on the papers, particularly for legal issues, and any hearing can be physically or remotely organised with the usual adversarial stages. Listing witnesses does not create an absolute entitlement to oral proceedings.")
add(15, "How are CAS arbitration costs handled in the situations described?",
    ["International disciplinary cases are generally free apart from the CHF 1,000 Court Office fee."],
    ["Ordinary cases are free when the sports body's regulations require CAS arbitration.", "The respondent's failure to advance costs causes the appeal to be terminated.", "Each party bears its own legal costs once equal arbitration advances have been paid.", "A sole-arbitrator case uses the same fixed cost as a three-member disciplinary panel."],
    "Qualifying international disciplinary appeals are free beyond the minimum fee. In other cases, equal advances are required; if the respondent does not pay, the appellant must cover the share or the case ends. The final award allocates arbitration costs and may contribute to legal expenses according to outcome.")
add(15, "What powers does a CAS appeals panel have when issuing an award?",
    ["Review both the facts and the law.", "Confirm or annul the challenged decision."],
    ["Increase the sanction when the federation requests broader relief in its response.", "Issue binding guidance for the sports body if the case is referred back.", "Order the sports body to enforce the award under the New York Convention."],
    "The panel has full factual and legal review and may confirm, annul or, in some cases, refer the matter back for a new decision. Enforcement is separate, and referral does not necessarily carry law-making instructions. The scope of any sanction change depends on procedure and relief, not a general power stated on this page.")
add(15, "Which confidentiality distinction applies to CAS awards?",
    ["Ordinary awards are confidential unless the parties publicise them.", "Appeal awards are public unless the parties agree on confidentiality.", "The default therefore differs according to the division."],
    ["Disciplinary appeal awards are public, while contractual appeal awards follow the Ordinary Division rule.", "Awards become public after the three-month issuance period has expired."],
    "Confidentiality follows the proceeding type: ordinary awards default to confidential and appeal awards default to public, subject to party choice in each direction. The subject matter inside an appeal does not create a separate rule. Timing of issuance does not determine publication.")
add(15, "A party considers challenging a CAS award before the Swiss Federal Tribunal. Which grounds are within the limited list?",
    ["Invalid constitution of the panel.", "CAS lack of jurisdiction.", "A ruling beyond or different from the parties' requested relief.", "Violation of equality, the right to be heard or public policy."],
    ["Manifestly incorrect application of the federation's regulations."],
    "SFT review is confined to fundamental arbitral defects: panel constitution, jurisdiction, ultra or extra petita, procedural equality and hearing rights, and public policy. It is not a further sports-law merits appeal. Eligible non-Swiss parties may also expressly waive the right to challenge.")

# PDF page 16 / handbook pages 322-323: enforcement and conclusion.
add(16, "A party refuses to comply with a final CAS award. Which enforcement responses reflect the chapter?",
    ["Seek execution under the New York Convention.", "Use applicable national enforcement procedures.", "Request disciplinary sanctions where federation rules punish non-compliance.", "Recognise that CAS itself does not enforce the award for the parties."],
    ["Return to the CAS panel for an order compelling the federation to execute the award."],
    "CAS issues binding awards but does not carry out enforcement. A successful party may use the New York Convention and domestic execution mechanisms or invoke sporting disciplinary rules, such as FIFA's offence for non-compliance. Enforcement therefore connects private arbitration with both state and sporting systems.")


def main() -> None:
    assert len(QUESTIONS) == 100, len(QUESTIONS)
    category_counts = {
        category: sum(question["oral_exam_category"] == category for question in QUESTIONS)
        for category in {"application", "explanation", "factual_anchor"}
    }
    assert category_counts == {"application": 45, "explanation": 35, "factual_anchor": 20}, category_counts
    payload = {
        "schema_version": 1,
        "library_key": "uefa_cfm",
        "chapter_number": 15,
        "session_title": "Chapter 10 - Football law",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")
    print(category_counts)


if __name__ == "__main__":
    main()
