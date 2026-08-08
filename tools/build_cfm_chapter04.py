"""Build the staged Chapter 4 UEFA CFM football-marketing bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = "UEFA-HFM-Football-Marketing.pdf"
OUTPUT = Path("data/cfm_imports/chapter_04_football_marketing.json")
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
            "handbook_pages": [124 + 2 * page, 125 + 2 * page],
        },
        "page_crops": crops or [],
        "answer": {"correct_options": positions, "explanation": explanation},
    })


# PDF page 2 / handbook pages 128-129: sports marketing, uncertainty and distinctive features.
add(2, "application", "A well-balanced international match is attracting little attention despite its sporting appeal. What should the association examine first?",
    ["Whether target spectators know about the contest and can access it."],
    ["Whether hospitality packages should be expanded before audience reach is measured.", "Whether sponsor activation provides a sufficient proxy for spectator awareness.", "Whether past attendance demonstrates access to the current contest.", "Whether result-focused promotion is more urgent than removing distribution barriers."],
    "Football's uncertain outcome creates appeal, but marketing must make prospective spectators aware of the contest and able to consume it. Sponsor activity can extend value, yet it does not repair weak audience access. The match result and the Laws of the Game are not substitutes for diagnosing reach and availability.")
add(2, "explanation", "Why is uncertainty of outcome central to the chapter's definition of sports marketing?",
    ["It creates excitement and expectation around the contest.", "It supports direct and indirect objectives for several stakeholder groups."],
    ["It makes prediction of the likely winner the main source of audience tension.", "It reduces the need to research motives once competitive balance is established.", "It places indirect stakeholder objectives after the needs of attending spectators."],
    "Uncertainty generates the tension and drama that draw people to football. Staging and communicating that contest creates opportunities for fans, businesses and related organisations to pursue different objectives. Marketing heightens awareness and access; it does not control the sporting result or narrow value to stadium attendance.")
add(2, "factual_anchor", "Which domains form part of the chapter's overview of football marketing?",
    ["The nature of the sports product.", "Brand and marketing communications.", "Licensing, ticketing and hospitality."],
    ["Stakeholder sensing and operational service design.", "Competition governance and member representation."],
    "The chapter covers the sports product, brand and marketing communications, licensing, ticketing and hospitality, and media rights. These domains connect market understanding with product development and distribution. Refereeing and transfer adjudication belong to different management and legal functions.")
add(2, "application", "A sponsor activates in a tournament fan zone. Which outcomes are consistent with the chapter?",
    ["Raise awareness of the sponsor's products and brand.", "Engage in public-relations activity.", "Transfer desirable football attributes to the sponsor's image.", "Create promotional interactions around the event."],
    ["Treat association with the event as sufficient evidence that each activation objective was achieved."],
    "Fan zones give partners a setting for promotions, PR, engagement and image transfer. The association between sponsor and football can build awareness and favourable meaning. Activation rights do not confer control over competition rules or format.")
add(2, "explanation", "What does it mean to describe sport as product-led?",
    ["The contest on the field gives the football product its fundamental strength."],
    ["The surrounding service experience gives the contest its primary product strength.", "Customer preferences should determine the sporting features before access is designed.", "Marketing communications define the core product that the teams subsequently deliver.", "Product leadership means prioritising team performance over market understanding."],
    "In sport, the on-field contest is the core source of product strength. Customer needs remain important for surrounding services and access, but marketers face limits in changing the sporting product itself. Hospitality, communications and research add value around the contest rather than creating it.")
add(2, "application", "A stadium has good teams but a subdued atmosphere. How should marketers apply the idea of supporters as 'prosumers'?",
    ["Treat crowd participation as part of the value created during the match.", "Develop attendance and engagement measures that strengthen the live atmosphere."],
    ["Treat atmosphere as an event-staff output that spectators subsequently consume.", "Evaluate crowd contribution through ticket revenue as the most comparable measure.", "Prioritise broadcast presentation because live engagement follows from media exposure."],
    "Supporters consume the match while also helping produce its atmosphere, excitement and tension. Marketers should therefore consider both attendance and active engagement in the live experience. Revenue records consumption, but it does not capture the crowd's productive role.")
add(2, "explanation", "Which considerations explain why football marketers operate within parameters outside their control?",
    ["Core rules constrain changes to the spectacle.", "A national association depends on the relevant governing authority for changes to the Laws.", "Marketing must work creatively around the protected sporting contest."],
    ["Strong customer evidence permits a national association to trial preferred rules as a marketing measure.", "Commercial demand should determine whether rule changes enter product planning before governance review."],
    "Football marketers cannot redesign the core game as freely as a conventional producer might redesign a product. Changes to the Laws sit with the authorised governing structure, so associations must improve access, presentation and surrounding services within those constraints. Customer evidence informs marketing choices but does not transfer rule-making authority.")
add(2, "application", "A board reviews a national team's season using revenue growth and sporting results. Which principles should guide the discussion?",
    ["Recognise that football uses sporting and financial performance measures.", "Consider that fans may value competition results more than profit.", "Explain tensions between commercial and sporting objectives.", "Assess how the two types of performance affect stakeholder perceptions."],
    ["Convert sporting performance into revenue so the board can use a single measure."],
    "Football organisations face a dual performance logic: economic outcomes matter, while fans and other stakeholders may prioritise league or cup performance. The measures interact but are not interchangeable. A sound review makes the tension visible instead of forcing the sporting result into a financial proxy.")
add(2, "factual_anchor", "How does the chapter characterise the relationship between sport and the media?",
    ["It is symbiotic: sport supplies attractive content and media supplies exposure."],
    ["It is a distribution relationship in which football gains exposure while media demand remains independent of sport.", "It is a content relationship whose value runs from football to media rather than back through promotion.", "It is a commercial-rights relationship whose significance depends chiefly on broadcast revenue.", "It is a promotional relationship that becomes less reciprocal as clubs create their own social content."],
    "Sport gives media outlets popular, ready-made content, while media coverage markets and promotes the sports product. Each side can help or hinder the other's objectives, which makes the relationship strategically important. The relationship is broader than a specific licence, promotion or direct-marketing transaction.")
add(2, "explanation", "A national association is considering an unfamiliar overseas market. What should market research establish before product development?",
    ["Who the prospective customers are and where they are located.", "Which products they may value and what they may pay."],
    ["Which domestic product can be transferred with the smallest operational change.", "Which sponsor already has the strongest relationship with the national team.", "Which competition result would create immediate demand in that territory."],
    "Market research systematically gathers and analyses data to inform decisions. Before designing an offer, the association needs evidence about customers, location, product appeal and willingness to pay. Internal convenience, sponsorship strength or a favourable result may influence execution, but they do not replace market understanding.")

# PDF page 3 / handbook pages 130-131: market research, product dimensions, goods and services.
add(3, "explanation", "Which statements correctly distinguish dimensions of a football product?",
    ["The uncertain contest is the core product.", "Add-on attractions belong to the augmented product.", "Expectations about what a match might become describe the potential product."],
    ["The tangible product is the physical setting in which the core contest takes place.", "The potential product describes expected benefits from the current augmented offer."],
    "The core is the functional or psychological basis, represented by the uncertain contest. The tangible dimension gives that core a marketable form, the augmented dimension adds attractions, and the potential dimension highlights what it might become. Tangibility here is a product layer, not a synonym for merchandise.")
add(3, "application", "A marketing team is defining what can count as a product in its portfolio. Which items fit the chapter's concept?",
    ["A new corporate hospitality service.", "A line of branded merchandise.", "An overseas national-team tour.", "A prominent player presented to a market."],
    ["A customer segment before any offer is made to it."],
    "A product is anything offered in a marketplace for purchase, consumption or awareness, including physical items, services, people and experiences. Hospitality, merchandise, tours and star players can therefore be managed as products. A segment identifies a group of customers; it is not itself the market offering.")
add(3, "factual_anchor", "Which characteristic makes an unsold seat at a completed match a lost service opportunity?",
    ["Perishability."],
    ["Non-standardisation.", "Inseparability.", "Intangibility.", "Augmentation."],
    "A match service is perishable because the same experience cannot be stored and sold after it has occurred. Inseparability concerns simultaneous production and consumption, while intangibility and non-standardisation describe other service properties. Augmentation is a product dimension rather than a service characteristic.")
add(3, "explanation", "How does a branded scarf differ from a football match as a market offering?",
    ["The scarf can be standardised and stored, whereas the match varies and perishes.", "The scarf is separable from its consumer, whereas the match is experienced as it is produced."],
    ["The scarf is an augmented service, whereas the match is a tangible core product.", "The scarf derives value from uncertainty, whereas the match derives value from physical ownership.", "The match can be inventoried when demand falls, whereas scarf production must follow attendance."],
    "The scarf is a tangible, standardised, separable and non-perishable good. A match is intangible, non-standardised, inseparable and perishable as a service experience. The distinction affects inventory, capacity and delivery decisions rather than reversing the sources of value.")
add(3, "application", "Research suggests demand for a new overseas hospitality offer. Which steps follow the chapter's marketing logic?",
    ["Define the customer group and its needs.", "Test product appeal and willingness to pay.", "Develop an offer that reflects the evidence."],
    ["Set the package around existing facilities before testing customer expectations.", "Use a famous player as the principal evidence that the market is viable."],
    "The association should move from systematic market insight to a product designed around identified needs and price expectations. Existing resources and player appeal may shape the offer, but neither demonstrates demand by itself. Product development follows evidence rather than preceding it.")
add(3, "explanation", "What makes market research useful to a football organisation?",
    ["It gathers data systematically.", "It analyses evidence for decision-making.", "It keeps the organisation outward-facing.", "It supports customer-focused product choices."],
    ["It fixes the product decision once the initial customer evidence has been analysed."],
    "Market research is systematic and ongoing, connecting data collection and analysis to decisions. Its purpose is to understand the operating environment and customers so products meet marketplace needs. Managers still interpret the evidence; a survey result is not a substitute for judgement.")
add(3, "application", "How should marketers classify the phrase 'the championship-deciding match' within the four product dimensions?",
    ["As a tangible presentation of the core contest."],
    ["As an augmented add-on to the stadium experience.", "As a potential version of a future competition.", "As the underlying psychological need served by football.", "As a non-perishable good created from the match."],
    "Calling a fixture the championship-deciding match emphasises and promotes the core contest, so it is the tangible product layer in this framework. The augmented layer adds benefits, while the potential layer imagines future possibilities. The phrase does not change the service into a physical good.")
add(3, "explanation", "How should a marketer distinguish an augmented football product from a potential product?",
    ["Augmentation adds current features that make the offer more attractive.", "Potential positioning highlights what the offer may become or deliver in the future."],
    ["Augmentation defines the uncertain contest, while potential positioning packages it for sale.", "Augmentation concerns physical goods, while potential positioning concerns services.", "Potential positioning records customer benefits that have already been consumed."],
    "An augmented product adds present benefits, such as a prestigious venue or associated experience. The potential product stimulates expectations about a future possibility, such as a predicted classic. They are distinct from the core contest and from the goods-services classification.")
add(3, "factual_anchor", "Which characteristics belong to goods in the chapter's comparison?",
    ["A physical form that customers can handle.", "Production in repeatable standard units.", "Separation of one item from another."],
    ["Consumption as the service is produced.", "Capacity that expires after delivery."],
    "Goods are described as tangible, standardised, separable and non-perishable. Simultaneous production and consumption reflects inseparability, while lost capacity reflects perishability, both associated with services. These characteristics explain why merchandise and matches require different marketing decisions.")
add(3, "application", "What can a national association learn from the Swedish hospitality example?",
    ["Different packages can address distinct customer needs.", "Concept, target group and facility location can be coordinated.", "Product names can connect hospitality with football heritage.", "Tiered experiences can support clearer market positioning."],
    ["A common service design is preferable when customer groups share the same event."],
    "The example uses three differentiated hospitality concepts, each with a defined audience, experience and location. Football heritage also helps package and name the offers. Shared attendance at one match does not mean that business customers value the same proposition.")

# PDF page 4 / handbook pages 132-133: consumption motives and competition product management.
add(4, "factual_anchor", "Which consumption motive is illustrated by supporting a team because its style of play is stimulating?",
    ["Stimulation."],
    ["Convenience.", "Self-improvement.", "Demography.", "Family predisposition."],
    "Stimulation describes consumption prompted by the excitement or style of the sporting experience. Convenience and self-improvement are separate motives, while demography and family relationships are influences on behaviour. The distinction helps marketers identify the value a supporter is seeking.")
add(4, "application", "A supporter follows the national team after moving abroad because their parents supported it and it expresses where they were born. Which influences are present?",
    ["A demographic connection to place of birth.", "A sociocultural influence through family relationships."],
    ["Convenience created by proximity to home matches.", "Self-improvement through association with the strongest team.", "A licensing influence created by access to branded products."],
    "Place of birth is a demographic influence, while parental support is a sociocultural influence. These factors can sustain allegiance despite relocation. The scenario does not establish convenience, status-seeking or a licensing relationship.")
add(4, "explanation", "Why should marketers distinguish general motives from demographic and sociocultural influences?",
    ["Motives describe benefits such as belonging, convenience or stimulation.", "Demographic factors help explain who may be predisposed to consume.", "Sociocultural factors show how peers and family shape behaviour."],
    ["Demographic analysis identifies the benefit a supporter seeks from the product.", "Sociocultural patterns establish segment demand before willingness to pay is tested."],
    "General motives explain what a person may seek from sport, whereas demographic and sociocultural factors help explain patterns of predisposition and influence. Used together, they improve segmentation and product design. They do not classify the product or remove the need for wider market research.")
add(4, "application", "A hospitality manager is matching three differentiated lounges to customer groups. Which decisions follow the Swedish example?",
    ["Reserve the most exclusive business-club setting for key partners.", "Match dining format to the expectations of each group.", "Use facility location as part of the proposition.", "Offer a less exclusive mingling format to a broader business audience."],
    ["Allocate customers by guest capacity before considering the experience they value."],
    "The Swedish example aligns concept, target group and location rather than treating capacity as the defining criterion. Different degrees of exclusivity and interaction create distinct propositions. Capacity matters operationally, but customer fit determines how the products are positioned.")
add(4, "factual_anchor", "Which format change characterised the European Cup's transition to the Champions League in the case study?",
    ["A hybrid of group and knockout stages."],
    ["A round-robin league culminating in a title table.", "A knockout competition with seeded second legs.", "A group stage followed by regional leagues.", "A finals tournament hosted by one member association."],
    "The 1992 redesign combined group and knockout stages. It responded to commercial and sporting concerns surrounding the risk of prominent clubs disappearing after one tie. The other structures do not describe the case study's hybrid format.")
add(4, "explanation", "Why did the development of television strengthen the case for redesigning the European Cup?",
    ["Broadcasters wanted a greater number of dependable fixtures.", "Early knockout elimination threatened the continued presence of popular clubs."],
    ["Broadcaster demand justified preserving the knockout format while expanding surrounding programming.", "Revenue growth made scheduling inventory more important than the sporting structure of the product.", "Popular-club participation could be protected through seeding rather than a broader product redesign."],
    "Satellite and pay television increased the revenues at stake and the value of reliable content. A pure knockout format could remove prominent clubs after one tie, reducing attractive inventory for clubs and broadcasters. UEFA responded by reconsidering commercial and sporting aspects while retaining governing control.")
add(4, "application", "After a successful competition redesign, what should UEFA continue to do according to the case study?",
    ["Monitor what fans want.", "Consult relevant football stakeholders.", "Assess whether commercial and sporting features remain attractive."],
    ["Preserve the launch format as the benchmark for future market decisions.", "Use broadcast revenue as the principal evidence of supporter satisfaction."],
    "Successful product management remains responsive to fans and stakeholders. Commercial prosperity is important, but the competition must also retain sporting appeal and relevance. Past success and broadcast income therefore support, rather than conclude, the monitoring process.")
add(4, "application", "A competition has strong football quality but little distinctiveness in a crowded market. Which branding actions fit the chapter's example?",
    ["Develop recognisable visual symbols.", "Use a distinctive sound or anthem.", "Create consistent words and images around the competition.", "Link those assets to a clear identity in consumer memory."],
    ["Change the match format before establishing how consumers perceive the current identity."],
    "The Champions League example shows how words, sounds, images, symbols and logos make a competition recognisable and distinctive. Consistent assets help consumers identify and remember the product. Format may require review for product reasons, but weak identity is first a branding problem.")

# PDF page 5 / handbook pages 134-135: branding, brand equity and sponsorship.
add(5, "explanation", "What is the primary marketing value of a strong football brand?",
    ["It differentiates the product and makes consumer choice easier."],
    ["It standardises consumer expectations across different football markets.", "It allows the association to infer loyalty from awareness.", "It shifts product development from customer evidence towards identity consistency.", "It makes competition performance secondary when promotional recognition is strong."],
    "Branding helps a football product stand out, builds trust and reduces the difficulty of choosing among alternatives. This can encourage loyalty and repeat consumption, but awareness is not the same as loyalty. A brand supports the underlying product rather than changing its service characteristics or replacing customer insight.")
add(5, "application", "The Icelandic association wants a contemporary identity rooted in national culture. Which actions align with the case study?",
    ["Translate authentic cultural symbols into a new visual identity.", "Apply the identity consistently across team activities and merchandise."],
    ["Base the identity on the team's recent ranking rather than longer cultural meaning.", "Separate the new logo from kit and merchandising activity to protect sporting credibility.", "Use the branding agency's international style in place of locally recognisable elements."],
    "Iceland's rebrand drew on folklore and traditional design while updating the national teams' image. Consistent use across activities, kit and merchandise reinforced the identity. Recent performance created attention, but authenticity and integrated application gave the brand its meaning.")
add(5, "factual_anchor", "Which outcomes contribute to brand equity as described in the chapter?",
    ["Enhanced perceived quality.", "Positive brand associations.", "Increased customer loyalty."],
    ["Control over media distribution channels.", "Reduced dependence on the sporting product."],
    "Brand equity captures the benefits produced by the brand name compared with an unbranded equivalent. It can raise awareness and perceived quality, create favourable associations and strengthen loyalty. Distribution control and the quality of the sporting contest remain separate management issues.")
add(5, "explanation", "How can football organisations build brand equity?",
    ["Through the nature and calibre of players.", "Through the organisation's treatment of customers.", "Through fans' access to prominent players.", "Through market campaigns that convey a chosen association."],
    ["Through visual consistency without reference to team, organisation or market factors."],
    "The chapter groups brand-equity drivers around team, organisation and market factors. Players, customer care, access and campaign choices can each add meaning and perceived value. Visual consistency helps recognition, but equity requires substantive experiences and associations as well.")
add(5, "application", "A well-known competition has high awareness but declining repeat attendance. What should its brand review prioritise?",
    ["Examine whether perceived quality and loyalty are weakening."],
    ["Increase logo exposure because awareness establishes repeat behaviour.", "Replace customer research with a more distinctive typeface.", "Treat the attendance decline as a licensing-control problem.", "Position the brand around a future product before assessing the current experience."],
    "Brand equity extends beyond recognition to perceived quality, associations and loyalty. High awareness can coexist with a disappointing experience and weak repeat behaviour. The review should diagnose those equity components before changing visual assets or licensing arrangements.")
add(5, "explanation", "Why are elements of the marketing communications mix often combined?",
    ["Different techniques perform complementary communication roles.", "Integration can improve the effectiveness of reaching and influencing customers."],
    ["Combination converts promotional activity into a single sponsorship contract.", "Integration makes target-market selection less important for channel choice.", "Using several techniques protects a weak product from unfavourable customer experience."],
    "Sponsorship, sales promotion, direct marketing, PR and advertising can each be used separately, but they serve different roles. Combining them coherently can reinforce awareness, meaning and response across the target market. Integration does not remove the need for segmentation or a credible product.")
add(5, "factual_anchor", "Which arrangements are forms of sponsorship identified in the chapter?",
    ["Naming rights.", "Endorsement contracts.", "Technical partnerships."],
    ["Retail distribution agreements.", "Ticket-bundle discounts."],
    "Sponsorship includes naming rights, endorsements, shirt deals and technical partnerships. Distribution agreements concern access to markets, while ticket-bundle discounts are sales promotions. The contractual purpose and value exchange distinguish the tools.")
add(5, "application", "A company sponsors a national team. Which objectives are consistent with the chapter?",
    ["Raise awareness and recall.", "Enhance the sponsor's brand image.", "Build positive associations with football.", "Develop business links with the property and its customers."],
    ["Acquire a licence to place the team's marks on unrelated retail products."],
    "Sponsorship can create awareness, recall, image benefits, favourable associations and business relationships. A licence to use protected marks is a separate contractual right. The sponsorship should therefore be evaluated against communication and relationship objectives, not assumed merchandising permissions.")
add(5, "application", "UEFA wants to communicate support for an anti-racism initiative. Which arrangement demonstrates that a rights holder can also become a sponsor?",
    ["UEFA can act as a sponsor to associate its resources with the initiative and its message."],
    ["UEFA can require an existing commercial sponsor to carry the message as its own activation.", "UEFA can licence the campaign identity to a partner and treat the licence fee as sponsorship.", "UEFA can sell naming rights to the initiative and retain the role of sponsored property.", "UEFA can target previous ticket purchasers and classify their response as sponsorship reach."],
    "A sports organisation that receives sponsorship can also become a sponsor to communicate a chosen message. Supporting an anti-racism initiative is the chapter's example of that broader role. Sales promotion, licensing, naming rights and transaction-based direct marketing describe different mechanisms.")
add(5, "explanation", "How does sponsorship differ from sales promotion in its typical purpose and timing?",
    ["Sponsorship builds promotional associations and business relationships.", "Sales promotion uses a short-term added benefit to stimulate purchase."],
    ["Sponsorship is defined by a price reduction, while sales promotion transfers brand image.", "Sales promotion grants continuing rights to use the sponsored property's identity.", "Sponsorship targets previous purchasers, while sales promotion addresses prospective customers."],
    "Sponsorship exchanges finance or resources for promotional and relationship benefits, often building image and associations. Sales promotion adds a temporary cash or in-kind incentive to prompt purchase or move stock. Neither tool is defined by whether the customer is new or returning.")

# PDF page 6 / handbook pages 136-137: promotional mix, direct marketing, PR and AIDA.
add(6, "explanation", "Which statements capture the value and risks of sales promotion?",
    ["An added benefit can stimulate short-term purchasing.", "Discounting can help clear stock before a new product cycle.", "Frequent price reductions can weaken perceived brand value."],
    ["A sales promotion builds customer profiles from transaction data.", "A promotion stabilises future demand by encouraging customers to buy ahead."],
    "Sales promotion uses a temporary cash or in-kind benefit to generate sales or reduce unwanted stock. Heavy discounting may damage brand status, and stockpiling may distort later demand. Customer profiling belongs to direct marketing rather than defining the promotion itself.")
add(6, "application", "A new national-team kit launches after a tournament, while substantial old stock remains. Which actions and cautions fit the chapter?",
    ["Use a time-limited price reduction on the outgoing kit.", "Frame the offer as a stock-clearance sales promotion.", "Monitor whether customers bring future purchases forward.", "Protect the perceived value of the new brand cycle."],
    ["Maintain the discounted price into the new cycle to convert the promotion into standard pricing."],
    "A short-term discount can reduce the risk of obsolete inventory before the new kit arrives. Management should watch brand dilution and demand displacement caused by stockpiling. Extending the reduction into the new cycle would blur the promotion and weaken the intended positioning.")
add(6, "factual_anchor", "Which description best defines direct marketing in the chapter?",
    ["Communication targeted to individual customers using relevant data."],
    ["Public communication designed to build mutual stakeholder understanding.", "Paid communication intended to move a broad audience through AIDA.", "A temporary benefit offered to increase sales volume.", "Resources provided to a football property for promotional association."],
    "Direct marketing is described as one-to-one marketing because it uses customer data to tailor communication. PR, advertising, sales promotion and sponsorship have different audiences and value exchanges. Transaction histories make the direct approach increasingly precise.")
add(6, "application", "A database identifies a group of lapsed season-ticket holders. Which responses reflect football relationship management?",
    ["Use their previous transaction history to define the lapsed group.", "Send a relevant re-engagement offer based on that evidence."],
    ["Place the same awareness advert across mass media before examining renewal behaviour.", "Treat non-renewal as proof that the match product lacks sporting quality.", "Remove lapsed customers from the database to improve the reported retention rate."],
    "Transaction data allows the club to identify lapsed purchasers and communicate with them directly. A tailored incentive, such as a free ticket, can test whether they can be re-engaged. Broad advertising or assumptions about sporting quality are less diagnostic than the observed relationship data.")
add(6, "explanation", "Which features distinguish public relations as a marketing communication tool?",
    ["It is deliberate, planned and sustained.", "It seeks mutual understanding with stakeholders.", "It manages information to shape reputation and relationships."],
    ["It relies on a temporary purchasing incentive to demonstrate value.", "It is measured by the royalties earned from third-party brand use."],
    "PR manages information over time to establish mutual understanding and support reputation, profile, messages and relationships. Its credibility can make it influential and cost-effective. Purchase incentives and royalties belong to sales promotion and licensing respectively.")
add(6, "application", "A national association launches a football-development scheme in a disadvantaged community. Which PR considerations are relevant?",
    ["The activity can demonstrate care for the community.", "Credible coverage can strengthen organisational reputation.", "Communication should connect the project with stakeholder understanding.", "The project itself should substantiate the public message."],
    ["The association should judge PR success from favourable coverage before assessing the community experience."],
    "A genuine social project can generate credible PR because conduct supports the association's message and reputation. Communication should explain the relationship with the community rather than detach publicity from delivery. Pricing the scheme as a promotion confuses social impact and sales stimulation.")
add(6, "factual_anchor", "In the AIDA model, which stage follows Interest?",
    ["Desire."],
    ["Recall.", "Engagement.", "Persuasion.", "Purchase."],
    "AIDA progresses from Attention or Awareness to Interest, Desire and Action. The model characterises how advertising is intended to move an audience towards a response. Recall, engagement, persuasion and purchase may be measured in campaigns, but they are not the named next stage.")
add(6, "explanation", "How should advertising be used within football marketing communications?",
    ["To attract attention and inform or persuade the target audience.", "Through media selected for the audience and desired response."],
    ["To create individual offers from a purchaser's transaction record.", "To establish mutual understanding through stakeholder dialogue.", "To provide a contractual association with a football property."],
    "Advertising catches attention, informs, persuades and reinforces purchase decisions, often described through AIDA. Its channel should fit the target audience and campaign purpose. Data-led individual offers, sustained stakeholder understanding and contractual association belong to direct marketing, PR and sponsorship.")
add(6, "application", "An association wants to generate match interest among 18-to-24-year-olds. Which planning decisions are supported by the chapter?",
    ["Define the benefits and features to communicate.", "Choose media platforms used by the target group.", "Set a budget consistent with the chosen communication method."],
    ["Select the most prestigious channel before clarifying the target message.", "Use the same media pattern that reached older season-ticket holders."],
    "The marketer should begin with the target group, decide what it should know, select a suitable channel and establish the budget. Platform relevance matters more than prestige, and evidence about another segment cannot be transferred without analysis. Implementation follows these choices.")
add(6, "explanation", "Which decisions form a coherent marketing-communications strategy?",
    ["Identify the target market.", "Specify the message and product benefits.", "Choose how the message will be conveyed.", "Establish the available budget."],
    ["Commit to internal delivery before choosing the communication channel."],
    "A coherent strategy aligns audience, message, medium and budget. The organisation then decides how to implement it, including whether to use internal resources or an agency. Choosing the delivery arrangement prematurely risks misalignment with the channel and expertise required.")

# PDF page 7 / handbook pages 138-139: fan segments and the introduction to licensing.
add(7, "factual_anchor", "Which fan segment follows football partly for social currency without identifying as a highly committed fan?",
    ["FOMO followers."],
    ["Club loyalists.", "Football fanatics.", "Icon imitators.", "Main eventers."],
    "FOMO followers are moderate fans who claim close interest but use football partly for social currency. Club loyalists and football fanatics have stronger emotional commitment, while icon imitators focus on players and participation. Main eventers become more engaged around prominent matches or tournaments.")
add(7, "application", "A campaign targets main eventers and icon imitators. Which distinctions should shape the content?",
    ["Emphasise major fixtures and tournament moments for main eventers.", "Use player-led and participation-oriented content for icon imitators."],
    ["Use club-identity messaging for main eventers because they are long-term loyalists.", "Treat icon imitators as low-engagement followers led by friends and family.", "Build both messages around community belonging associated with football fanatics."],
    "Main eventers keep up with news and intensify their engagement around big occasions. Icon imitators follow particular players and prefer playing to watching, so player and participation themes fit them better. The alternative descriptions belong to club loyalists, tag alongs and football fanatics.")
add(7, "explanation", "Why is fan segmentation useful for a national association's communications?",
    ["Groups differ in emotional engagement and consumption behaviour.", "Segments respond to different content and channels.", "A differentiated approach can make communication more relevant."],
    ["Segment size determines the brand equity created by each campaign.", "Segmentation removes the need to understand motives within a group."],
    "The six groups vary in commitment, social motivation, viewing patterns and interest in players or events. Recognising these differences helps marketers select appropriate messages, platforms and programmes. Segment percentages guide scale, but they do not measure campaign equity or explain each person completely.")
add(7, "application", "How could an association communicate differently across the fan segments described in the chapter?",
    ["Use major-event campaigns for followers whose engagement peaks around tournaments.", "Use player-created social content for fans who imitate icons.", "Use community-oriented messages for deeply engaged football fanatics.", "Use accessible introductory content for tag alongs influenced by friends or family."],
    ["Use one loyalty message because the segments belong to the same football market."],
    "Segmentation is valuable when it changes communication choices. Event prominence, player access, community meaning and socially accessible content address different motives described in the groups. A common football interest does not imply a common level or source of engagement.")
add(7, "factual_anchor", "What is a sports licensing agreement?",
    ["A contract permitting another entity to use specified brand assets in return for a fee or royalties."],
    ["A sponsorship contract transferring the sporting property's identity to the sponsor.", "A distribution contract appointing a retailer to reach a foreign market.", "A direct-marketing permission based on a fan's transaction history.", "A hospitality contract granting special access to players and facilities."],
    "Licensing grants defined use of names, marks, trademarks, logos or trade names for compensation. It may support a new product or association with an existing one. Sponsorship, distribution, direct marketing and hospitality involve different rights and purposes.")
add(7, "explanation", "How can a licensee use a football organisation's intellectual property?",
    ["To develop a new product incorporating authorised brand assets.", "To associate an existing product with the sports property."],
    ["To determine the sports organisation's future brand positioning.", "To resell the sporting rights through a media distribution channel.", "To convert the licence fee into ownership of the underlying trademark."],
    "A licensing agreement may enable product development or add an authorised football association to an existing offer. The scope is contractual and does not transfer ownership or strategic control of the brand. Media resale rights would require a different grant.")
add(7, "application", "A game developer wants to include tournament teams, players, logos and images. Which elements should the agreement address?",
    ["Permission from the relevant rights holders.", "The intellectual-property assets covered.", "The fee or royalty exchanged for use."],
    ["Permission from the game's distributor as the route to the tournament assets.", "Access to later brand assets under the current contract cycle."],
    "The developer needs a licence from the organisations controlling the relevant teams and tournament IP. The agreement should define the assets and compensation, as the Konami example illustrates. Sporting-format control and later-created assets do not arise without express contractual scope.")
add(7, "application", "Why might a football organisation expand its licensing activity?",
    ["To realise commercial value from owned properties.", "To respond to consumer demand for branded products.", "To use gaming and social platforms as new product opportunities.", "To reach customers in increasingly global markets."],
    ["To reduce the need for monitoring how third parties use the brand."],
    "Changed business models, consumer tastes, technology and globalisation have expanded licensing opportunities. These forces can create revenue and new forms of engagement. Growth increases rather than reduces the need for careful control of licensed products.")

# PDF page 8 / handbook pages 140-141: licensing benefits, risks and management.
add(8, "factual_anchor", "Which party is the licensor in a football licensing agreement?",
    ["The organisation granting the right to use its protected brand assets."],
    ["The company purchasing products from the licensed retailer.", "The intermediary distributing the finished products to the market.", "The sponsor providing finance for promotional association.", "The agency measuring the brand equity created by the products."],
    "The licensor owns or controls the relevant property and grants defined usage rights. The licensee acquires those rights, while retailers and other intermediaries may later distribute the product. Sponsorship and brand measurement are separate relationships.")
add(8, "explanation", "What strategic benefits can licensing provide to a football rights holder?",
    ["Revenue from the granted rights.", "Reach into new geographic or demographic markets."],
    ["Direct control of the licensee's retail customer relationships.", "Protection from reputational effects caused by the licensed product.", "Ownership of the licensee's new product and distribution network."],
    "Licensing can create income, market reach, awareness, brand equity and goodwill. Because another organisation develops or sells the product, the licensor may not control the customer relationship or execution directly. That distance creates management and reputation risks rather than ownership of the licensee's operations.")
add(8, "application", "A national association is licensing its crest for a new product category. Which controls should it prioritise?",
    ["Define acceptable product use of the crest.", "Monitor product quality and brand association.", "Provide remedies for use that damages the association."],
    ["Let the retailer set brand standards because it has closer customer contact.", "Assess the deal from projected royalties without considering control costs."],
    "A licensor must manage how its name and marks appear, because poor execution can undermine the organisation and require costly repair. Clear scope, quality oversight and remedies protect the brand. Retail knowledge and royalty projections are relevant, but they do not replace rights-holder control.")
add(8, "application", "A small manufacturer becomes a licensee of a prestigious football competition. Which benefits may support its business case?",
    ["Develop new products around an established brand.", "Use existing brand equity to accelerate market acceptance.", "Build relationships with retailers and other intermediaries.", "Support premium pricing through the prestigious association."],
    ["Extend the association into adjacent product categories under the existing category licence."],
    "The licensee can draw on established brand equity, save brand-building time and open product, retail and pricing opportunities. The association may also strengthen revenue streams. Sporting or disciplinary authority remains with the football bodies and represents a potential external reputation risk.")
add(8, "explanation", "Why can a prestigious football licence save a licensee time and money when launching a product?",
    ["The product can draw on brand equity already established by the football property."],
    ["The licensor assumes the licensee's product-development expenditure.", "Retail relationships established by the licensor transfer with the brand rights.", "Premium pricing follows from the licence before product quality is assessed.", "The licence fee substitutes for investment in positioning the licensee's offer."],
    "The licensee can associate its offer with awareness, quality perceptions and associations the football brand has already built. That can accelerate acceptance and intermediary relationships. The licensee still carries its own development, positioning and quality responsibilities, and premium pricing remains a market outcome rather than a contractual benefit.")
add(8, "application", "An association's licensing portfolio is growing faster than its management capacity. Which response fits the chapter?",
    ["Prioritise active oversight of licensees and products.", "Assess whether expected revenue and brand reach justify the workload."],
    ["Broaden the categories further so monitoring costs are spread across more agreements.", "Delegate brand standards to licensees with the highest projected sales.", "Replace product oversight with an annual brand-awareness survey."],
    "Licensing is complex, time-consuming and capable of harming the brand when weakly managed. The association should match portfolio scale to oversight capacity and total strategic value. More categories, delegated standards or awareness data do not control individual product execution.")
add(8, "explanation", "Why can licensing remain valuable when its revenue is smaller than media and commercial-rights income?",
    ["It keeps consumers connected with the brand between major events.", "It extends the brand into products and customer occasions.", "It can support awareness and goodwill in additional markets."],
    ["It gives the licensor direct access to transactions made by each retailer's customers.", "It reduces the strategic importance of managing brand associations."],
    "Licensing has engagement and reach value beyond its share of revenue. Branded games, merchandise and other products can keep the football property present throughout the year and introduce it to new groups. Those benefits still require careful management and do not guarantee access to retailer data.")
add(8, "application", "A rights team is designing a tender for several licensing categories. Which practices are supported by the UEFA example?",
    ["Define distinct product categories and competition rights.", "Use a transparent invitation-to-tender process.", "Coordinate the rights cycle with the competitions covered.", "Consider online, on-site and physical retail routes."],
    ["Bundle product categories without distinguishing how the brand will reach consumers."],
    "The UEFA case defines categories, covered competitions, cycle and retail routes before selecting partners. This makes scope and market access clearer for bidders and the rights holder. An undifferentiated bundle would weaken control and obscure the capabilities needed for each category.")

# PDF page 9 / handbook pages 142-143: ticket strategy, hospitality and changing media rights.
add(9, "factual_anchor", "What is the central capacity objective identified for match-ticket marketing?",
    ["Maximise use of the available stadium capacity."],
    ["Maximise the average ticket price across customer groups.", "Increase the proportion of hospitality seats within the stadium.", "Prioritise repeat purchasers in the initial sales window.", "Minimise discounted bundles across a match series."],
    "Ticket marketers seek to fill the stadium because attendance supports atmosphere, commercial partners and revenue. Price, priority windows and bundles are tools within the strategy rather than the central capacity objective. The appropriate mix depends on customer evidence and match conditions.")
add(9, "application", "An association is preparing a ticket-sales plan. Which customer groups should its database distinguish?",
    ["Current and prospective match-goers.", "Repeat purchasers and lapsed match-goers."],
    ["High- and low-spend purchasers before separating current from lapsed status.", "Supporters grouped by preferred package before purchase behaviour is established.", "Current purchasers and hospitality guests while prospective demand is assessed separately."],
    "The chapter begins with actual, potential, repeat and lapsed purchasers so communication and packages can respond to behaviour. Hospitality and sponsorship may require related data, but media intermediaries are not ticket customers. A single result or sponsor association does not provide the same relationship insight.")
add(9, "explanation", "Why does fuller stadium capacity create value beyond ticket revenue?",
    ["A larger crowd strengthens match atmosphere.", "Atmosphere supports the experience expected by sponsors and broadcasters.", "Attendance can reinforce engagement with the football product."],
    ["Capacity use converts the match from a perishable service into an inventory asset.", "A sell-out demonstrates that ticket packages delivered equal value to each customer group."],
    "Attendance helps produce the tension and atmosphere of the live product, which also matters to partners and media audiences. It can therefore create experiential and commercial value alongside gate income. A sell-out does not change service perishability or prove that different customers received equal value.")
add(9, "application", "A ticket team wants higher sales and stronger long-term loyalty. Which actions fit the chapter's strategy?",
    ["Use purchase data to identify behavioural trends.", "Target communication to defined customer groups.", "Create packages that add benefits for those groups.", "Track and retain customers with significant lifetime value."],
    ["Use discounted bundles as the standard offer before identifying who values them."],
    "A coherent ticket strategy moves from customer identification to targeted communication and suitable packages. Retaining high-lifetime-value customers can improve long-term profitability and loyalty. Bundles can be useful, but they should answer a diagnosed need rather than precede segmentation.")
add(9, "application", "What should an association do before sending direct ticket offers to supporters?",
    ["Interpret purchase data to identify which features and benefits are relevant to the recipient."],
    ["Select a discount level from the unsold capacity before reviewing customer history.", "Classify repeat buying as evidence that the existing package needs no refinement.", "Use match importance as a substitute for analysing fan data.", "Send the same product description to current and lapsed purchasers."],
    "Direct mailing becomes more effective when fan data informs the offer and message. Purchase history can reveal behaviour, value and potential needs across current, prospective and lapsed groups. Unsold capacity and match prominence matter, but they do not determine customer relevance by themselves.")
add(9, "explanation", "What distinguishes a compelling hospitality proposition from a general match ticket?",
    ["It offers memorable benefits or access unavailable in the general experience.", "It builds identification and affinity through a distinctive service."],
    ["It is defined by a higher price and a larger catering allocation.", "It serves commercial partners without requiring customer segmentation.", "It derives exclusivity from limiting communication about the facilities."],
    "Hospitality adds distinctive access, facilities, catering, viewing or networking benefits that create a memorable relationship with the organisation. Price and catering may be components, but neither defines the proposition. The offer still requires a target group, positioning and clear communication.")
add(9, "application", "A venue is considering entering the corporate-hospitality market. Which questions should be resolved first?",
    ["What outcomes the hospitality activity should achieve.", "Which customers and position the product will target.", "Whether facilities and resources can deliver added value."],
    ["Which external caterer offers the lowest unit cost before the proposition is defined.", "Which ticket segment can be upgraded without changing the service design."],
    "The organisation should clarify purpose, market position, target customers and delivery capability before setting the detailed mix. Outsourcing, price and service nature follow from that strategy. Starting with supplier cost or easy upgrades risks creating an offer without a distinctive customer benefit.")
add(9, "explanation", "Which developments have transformed the market for football media rights?",
    ["A proliferation of media outlets and content.", "Consumer creation of information through social media.", "Technology convergence on handheld devices.", "Fragmentation into products such as live, highlights, overseas and internet rights."],
    ["A return to a linear media product chosen by the broadcaster for the audience."],
    "Media rights now span many outlets, formats and territories, while fans can consume and create content across converged devices. Fragmentation gives consumers more influence over bundles and timing. This is the opposite of a single linear product imposed by one broadcaster.")

# PDF page 10 / handbook pages 144-145: media distribution and intermediaries.
add(10, "factual_anchor", "Which distribution route sends media products from a football organisation to consumers through its own website or mobile service?",
    ["Direct contact distribution."],
    ["Indirect contact distribution.", "Wholesale licensing.", "Retail sponsorship.", "Promotional syndication."],
    "Direct contact distribution connects the organisation with consumers through channels such as websites or mobile phones. Indirect distribution inserts an agent, broker, distributor or other intermediary. The remaining terms are not the chapter's classification of this route.")
add(10, "application", "A European association plans to enter a media market with distinct local rules and consumer habits. Which preparations are appropriate?",
    ["Research who the customers are and how they consume content.", "Assess local norms and licensed access requirements."],
    ["Transfer the domestic rights bundle before examining local demand.", "Select the highest-revenue broadcaster before comparing market-access routes.", "Use global brand awareness as evidence that the domestic format will fit."],
    "Market entry requires insight into customers, timing, preferences and local conventions. Regulatory or licensing conditions may make a local agent necessary, so channel design must follow the market context. Brand strength and revenue forecasts do not establish route suitability by themselves.")
add(10, "explanation", "How should a rights holder compare direct and indirect media distribution?",
    ["Direct distribution can preserve control of customer relationships.", "Indirect distribution can add local expertise and market access.", "Direct distribution requires resources to provide an effective service."],
    ["Indirect distribution gives the rights holder closer transaction data than its own platform.", "Direct distribution transfers logistical responsibility to a wholesaler."],
    "Direct contact supports control and proximity but requires internal technology, service and selling capability. An intermediary can reduce those burdens and open markets through expertise and relationships. The trade-off is greater distance and possible loss of control, not closer data ownership.")
add(10, "application", "A national association lacks overseas sales expertise but wants broad market reach. Which benefits could justify using an intermediary?",
    ["Specialist administrative and selling skills.", "Local logistical support and market access.", "Creation of useful product bundles and assortments.", "Transfer of some stock and liquidity exposure."],
    ["Closer direct control of the end-customer relationship."],
    "Intermediaries may contribute expertise, logistics, sales capability, bundling and assumption of stock-related risk. These services can extend reach when internal capacity is limited. The association pays through cost, margin and reduced proximity to the market.")
add(10, "factual_anchor", "Which intermediary is used in the chapter's example to simplify and extend the supply network for overseas television rights?",
    ["A wholesaler."],
    ["A locally licensed agent.", "A high-street retailer.", "A specialist distributor.", "A media-rights broker."],
    "The chapter uses a wholesaler as the example for extending the supply network and selling overseas television rights. A retailer example concerns selling subscriptions to consumers. Franchisees and agents may be intermediaries, but they are not the specific example described.")
add(10, "explanation", "What are the main strategic risks of relying on intermediaries for media-rights distribution?",
    ["The rights holder may lose market control and customer proximity.", "Costs, coordination problems or weak partner selection may erode value."],
    ["The rights holder must build the intermediary's consumer platform from its own resources.", "The intermediary makes local market knowledge less available to the rights holder.", "The arrangement converts media rights into a direct-contact channel."],
    "Indirect distribution can add expertise but also reduces margins, increases distance and creates coordination and reputation exposure. Poor selection may weaken market position, while overdependence can reduce control. These are governance trade-offs within an indirect channel, not features of direct distribution.")
add(10, "application", "Which factors should shape a media-rights distribution strategy?",
    ["Customer location and ease of access.", "Costs and revenues of reaching the market.", "Emerging technologies and influential platforms."],
    ["The number of intermediaries already used in the domestic market.", "The visual identity of the competition before consumer access is assessed."],
    "A distribution strategy should connect target-market location and access with economics and changing technology. Domestic arrangements may offer evidence, but they do not determine a different market's optimal channel. Branding matters to demand, while the distribution decision focuses on reaching and serving that demand.")
add(10, "application", "Fans increasingly shape how football content is consumed. How should a rights strategy respond?",
    ["Study how consumers use each platform.", "Design formats suited to conventional and emerging consumption patterns.", "Consider consumer-created and interactive behaviour.", "Review channel choices as technology and access habits evolve."],
    ["Preserve the linear broadcast bundle as the reference product for digital channels."],
    "Consumers now choose timing, bundles and platforms and can influence the experience through social media. Rights strategy must therefore examine behaviour and adapt formats and routes across established and emerging channels. Treating digital distribution as a copy of linear broadcasting misses that shift in control.")

# PDF page 11 / handbook pages 146-147: social-media case study and conclusion.
add(11, "application", "A women's national team wants to bring players and supporters closer through digital media. Which approach best reflects the English FA case?",
    ["Give selected players a supported role in creating authentic off-field content."],
    ["Centralise player communication in the association's corporate account to maintain a uniform voice.", "Prioritise edited match highlights before testing live or behind-the-scenes material.", "Base player selection on follower totals rather than their ability to connect teams and fans.", "Use celebrity messages as the recurring format for routine training coverage."],
    "The Digital Ambassador programme made players the digital faces of their clubs and enabled them to create off-field insight. This authenticity was intended to reduce distance and inspire future players. Central control, highlights and celebrity support may contribute, but they do not reproduce the core mechanism.")
add(11, "explanation", "Why did the English FA's social-media approach support growth in women's football?",
    ["Live and behind-the-scenes content increased access to players and teams.", "A broad platform mix created repeated opportunities for engagement around matches."],
    ["The campaign depended on licensing match footage to player-managed retail channels.", "Digital ambassadors replaced the need for dedicated media teams at clubs.", "Social content was designed around ticket discounts for existing supporters."],
    "The case combines live training and match content, player-led insight and coordinated use of several social platforms. This brought teams and fans closer and extended visibility around matchdays. The approach required content capability and relationship-building rather than retail licensing or a narrow sales promotion.")
add(11, "factual_anchor", "Which practices appear in the English FA women's-football case study?",
    ["Live video from training sessions.", "Club players acting as digital ambassadors.", "Match and highlight content distributed through social platforms."],
    ["Celebrity greetings used as the recurring source of player-led content.", "Paid promotion used as the principal source of club match highlights."],
    "The case identifies live training content, a broad platform presence, player digital ambassadors, live-streamed matches and club-produced highlights. Teams retained media capability and used different channels for complementary content. It was not described as a centralisation or licensing programme.")
add(11, "application", "A national association is reviewing its overall marketing capability. Which priorities follow the chapter's conclusion?",
    ["Reconcile marketplace demands with organisational resources and skills.", "Build an outward-looking and customer-focused internal culture.", "Remain responsive to trends while creating new opportunities.", "Use marketing insight across competition, product and rights decisions."],
    ["Treat marketing as a communications department once the sporting product is defined."],
    "Marketing underpins choices about competitions, consumers, merchandise and media rights. A national association must connect external demand with internal capability while encouraging innovation and responsiveness. That requires a market-led culture across operations, not a communications function added after product decisions.")


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
        "session_title": "Chapter 4 - Football marketing",
        "source_pdf": SOURCE,
        "questions": QUESTIONS,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(QUESTIONS)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
