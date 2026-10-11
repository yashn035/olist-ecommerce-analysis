# Olist E-Commerce Analysis: Data Analyst Interview Preparation Guide

This guide prepares you to speak naturally and authoritatively about this project in technical, behavioral, and case interviews. Every answer uses **real computed metrics**, eliminates buzzwords, flags conversational traps, and prepares you for likely follow-ups.

---

### Q1: "Can you walk me through this project?"
* **Spoken Answer (45s)**:
  > "I analyzed 96,000 delivered orders from Olist, a Brazilian e-commerce marketplace, to understand why gross merchandise value grew 5x while repeat purchases stayed flat at 3%.
  >
  > I built an end-to-end analytics pipeline: cleaned 9 relational tables into SQL, wrote 10 analytical queries on revenue trends, cohort retention, and seller SLAs, and built an interactive Power BI dashboard on a star schema.
  >
  > Three findings stood out:
  > 1. **Repeat purchase rate is stalled at 3.00%**, and Month-1 cohort retention peaks at just **0.48%**—meaning the retention window closes almost entirely within 30 days.
  > 2. **Late delivery cuts review scores from 4.29 to 2.57 stars**, with 1-star reviews surging from 6.6% to 46.2%.
  > 3. **The Pareto rule does not apply**: reaching 80% of revenue requires 45.0% of customers, not 20%.
  >
  > My core recommendation was to prioritize a 30-day post-delivery consumable replenishment trigger over a VIP program, because the data doesn't support an entrenched high-value buyer cohort."
* **Trap to Avoid**: Listing tools instead of business impact. Don't say: *"I used pandas, matplotlib, and seaborn to explore the data."*
* **Follow-up They'll Ask**: *"Why do you think repeat purchases stayed at 3% while GMV grew 5x?"* (Answer: Olist is a marketplace channel integrator for durable goods where consumers rarely realize they are buying through Olist rather than the underlying seller).

---

### Q2: "What was your most surprising finding?"
* **Spoken Answer (45s)**:
  > "My most surprising finding was completely disproving the 80/20 Pareto principle. In retail analytics, stakeholders routinely assume that the top 20% of customers generate 80% of revenue and push for expensive VIP loyalty clubs.
  >
  > When I ran a cumulative revenue percentile query across all 93,104 unique customers, the top 20% generated only 56.61% of total revenue. In fact, reaching 80% of revenue required 45.00% of all customers.
  >
  > That completely reframed our retention strategy: a 'top 20% VIP program' would miss 43.4% of platform revenue. Olist is a high-volume, single-transaction customer acquisition engine with a wide, long tail."
* **Trap to Avoid**: Assuming the 80/20 rule is an immutable natural law. Don't apologize for the data not matching the textbook.
* **Follow-up They'll Ask**: *"How did you verify the ranking wasn't reversed?"* (Answer: I confirmed that rank 1 had the highest spend of R$ 13,440.00 and represented only 0.102% of total platform revenue).

---

### Q3: "How did you define revenue in your analysis?"
* **Spoken Answer (30s)**:
  > "I defined top-line revenue as Gross Merchandise Value (GMV)—the sum of product price plus freight paid by the customer on delivered orders (`SUM(price) + SUM(freight_value)`), which totaled R$ 13.18 million across the clean 20-month window.
  >
  > In product category analyses, I isolated product price alone (`SUM(price)`) to evaluate pure merchandise demand without geographic freight distortions. It's important to clarify that this represents gross platform sales volume, not Olist's net marketplace take-rate commission."
* **Trap to Avoid**: Saying you summed the `payments` table.
* **Follow-up They'll Ask**: *"What happens if you sum payments instead of order items?"* (Answer: If an order has 3 items and 2 payment installments, joining payments to items creates a Cartesian join of 6 rows, double-counting revenue).

---

### Q4: "What is `customer_unique_id`, and why did that matter?"
* **Spoken Answer (30s)**:
  > "The dataset contains two customer identifiers: `customer_id` and `customer_unique_id`. `customer_id` is an order-level proxy generated uniquely per transaction—there are exactly 99,441 rows matching the order table 1:1.
  >
  > `customer_unique_id`, however, identifies the real human individual across multiple orders (96,096 distinct unique customers). If you calculate repeat purchase rate using `customer_id`, your repeat rate calculates as exactly 0%. Grouping by `customer_unique_id` revealed the true 3.00% repeat purchase rate."
* **Trap to Avoid**: Confusing entity grain with data duplication.
* **Follow-up They'll Ask**: *"How would you model this in Power BI?"* (Answer: Keep `Dim_Customers` with `customer_id` as the primary key relating 1-to-many to `Fact_Sales`, while calculating repeat customer measures using `VALUES(Dim_Customers[customer_unique_id])`).

---

### Q5: "Is a 3% repeat purchase rate bad? How do you interpret that?"
* **Spoken Answer (45s)**:
  > "In isolation, 3.00% sounds low compared to mature D2C e-commerce benchmarks of 20–30%. But the curve shape matters far more than the raw number.
  >
  > When I examined monthly cohorts, repeat behavior is effectively a single-month phenomenon. Month-1 retention is 0.48%, which is the highest point of the post-purchase curve—and also effectively a floor. It drops to 0.26% in Month 2 and asymptotes to noise after Month 3.
  >
  > If a customer doesn't return within 30 days of delivery, the probability they ever return drops below 0.3%. There is no slow-burn retention to harvest. That collapses the recommendation into a specific, testable action: reactivate customers within a strict 30-to-45-day window for repeat categories like *Health & Beauty* (the #1 category at R$ 532.8k), or not at all."
* **Trap to Avoid**: Calling 0.48% a 'strong peak'. It's an operational ceiling and a floor.
* **Follow-up They'll Ask**: *"What kind of intervention would you run in that 30-day window?"* (Answer: Automated replenishment triggers with personalized discounts on consumable items 25–30 days after marked delivery date).

---

### Q6: "You said late delivery hurts review scores. How do you know that's causal?"
* **Spoken Answer (60s)**:
  > "In the exploratory data, it's strictly correlational: on-time deliveries average 4.29 stars with only 6.6% 1-star reviews, whereas late deliveries plunge to 2.57 stars with 46.2% 1-star reviews.
  >
  > However, distance, remote geography, and product defect rates are natural confounds. To test this, I engineered a matched-pair analysis in SQL: for each late order, I identified on-time orders in the exact same state, purchasing the exact same product ID, within 10% of the same order value.
  >
  > Across 3,309 unique matched late orders and 32,710 comparison pairs, the review score penalty persisted at **-1.59 stars** (4.19 ★ on-time vs. 2.61 ★ late). This confirms that delivery delay exerts an independent, direct penalty on customer satisfaction that cannot be explained away by product quality or geographic distance."
* **Trap to Avoid**: Claiming pure causality without unprompted acknowledgement of confounding variables.
* **Follow-up They'll Ask**: *"What would it take to prove 100% causality?"* (Answer: A randomized A/B test—for example, subsidizing expedited express carrier logistics for a random 50% sample in delayed regions and measuring the review delta against the control group).

---

### Q7: "How did you handle truncated or incomplete months?"
* **Spoken Answer (30s)**:
  > "I audited the date distribution in SQL and found that raw timestamps spanned September 2016 to October 2018. However, 2016 only had ~329 pilot orders, while September and October 2018 contained truncated records after data logging ceased.
  >
  > If left uncleaned, a time-series line chart shows misleading 90% revenue crashes at both ends. I strictly bounded the analytical window between January 1, 2017 and August 31, 2018—yielding exactly 20 complete, contiguous monthly periods."
* **Trap to Avoid**: Filtering arbitrarily without citing the data volume rationale.
* **Follow-up They'll Ask**: *"Did you exclude 2016 from cohort retention as well?"* (Answer: Yes, because single-order pilot cohorts in late 2016 produce misleading 100% or 0% retention artifacts).

---

### Q8: "Why did your Pareto curve deviate from the 80/20 rule?"
* **Spoken Answer (30s)**:
  > "The 80/20 rule is an empirical heuristic, not a mathematical law. It holds true in businesses with power-law retention—like B2B SaaS, mobile gaming with 'whales', or luxury travel.
  >
  > On Olist, the customer spend distribution has low variance because 97% of buyers make exactly one purchase with an Average Order Value of R$ 137.00. Because few buyers make 5 or 10 purchases, cumulative revenue scales almost linearly with customer count. The top 20% generate 56.61%, and reaching 80% requires 45.00% of shoppers."
* **Trap to Avoid**: Saying your code had a bug or apologizing for the empirical result.
* **Follow-up They'll Ask**: *"Does Pareto hold on the seller side?"* (Answer: Yes! Seller volume is heavily concentrated, with a small fraction of sellers driving the vast majority of orders, which is typical for marketplace aggregators).

---

### Q9: "What would you do if you had more data?"
* **Spoken Answer (45s)**:
  > "Three specific datasets would unlock deeper strategic insights:
  > 1. **Marketing Spend & CAC**: Knowing acquisition costs by channel would let me calculate true Customer Lifetime Value to CAC (LTV:CAC) ratios and evaluate whether single-purchase customers are even profitable.
  > 2. **Session & Cart Abandonment Telemetry**: Web traffic data would help evaluate whether high freight in remote states (50–60% of item price in RO and MA) is suppressing checkout conversion rates.
  > 3. **Carrier & Package Dimensions**: Package cubic weight would isolate whether seller dispatch delays or carrier transit bottlenecks drive the 24–30 day delivery times in the North."
* **Trap to Avoid**: Suggesting complex machine learning models that don't solve the core business problem.
* **Follow-up They'll Ask**: *"If marketing data showed CAC exceeded LTV on first purchase, what would you recommend?"* (Answer: Shift marketing acquisition budget to high-AOV or consumable categories with higher repeat probability, like Health & Beauty).

---

### Q10: "If you had to move one metric by 10%, which one would you pick and why?"
* **Spoken Answer (45s)**:
  > "I would target a 10% reduction in the **Late Delivery Rate** (reducing it from 8.01% down to ~7.2%).
  >
  > Here's why: Late deliveries are the single biggest operational lever damaging customer goodwill. Reducing late orders directly rescues customers from the 2.57-star rating cliff and cuts the 46.15% 1-star surge.
  >
  > Operationally, I can achieve this without building new warehouses: SQL query Q10 identified chronic sellers with over 50 completed orders who maintain late rates exceeding 30% and average delays of 28–40 days. Simply enforcing seller dispatch SLAs, deprioritizing chronic late sellers in the Buy Box, and subsidizing regional consolidation in the Northeast would quickly hit that 10% target."
* **Trap to Avoid**: Choosing top-line revenue without considering profitability or operational capacity.
* **Follow-up They'll Ask**: *"What pushback would you expect from merchants if you enforced those SLAs?"* (Answer: Merchants might threaten to leave the marketplace, so SLA enforcement must pair with logistics assistance, such as scheduled carrier pick-ups).

---

### Q11: "What was the weakest part of your analysis?"
* **Spoken Answer (45s)**:
  > "The biggest analytical blind spot was the total absence of marketing acquisition spend and margin data.
  >
  > Because I only had gross revenue, I could identify that 97% of shoppers are one-time buyers, but I couldn't evaluate whether that model is actually broken. If customer acquisition cost is R$ 10 and gross margin on an R$ 137 basket is R$ 25, a single-purchase acquisition engine is perfectly viable. If CAC is R$ 40, the business is bleeding cash.
  >
  > Without CAC and unit margins, I had to stop at behavioral retention conclusions rather than full unit economic profitability."
* **Trap to Avoid**: Claiming your analysis was perfect, or citing a trivial typo. Confessing a substantive data boundary is a mark of seniority.
* **Follow-up They'll Ask**: *"How would you approximate CAC if marketing spend wasn't provided?"* (Answer: You can't safely invent it, but you could benchmark against publicly traded Brazilian e-commerce comparables like Magazine Luiza or B2W during 2017–2018).

---

### Q12: "How did you decide when to stop analyzing?"
* **Spoken Answer (30s)**:
  > "I stopped once each business question had an unambiguous operational recommendation that withstood scrutiny.
  >
  > For instance, once the Pareto curve showed that reaching 80% of revenue required 45.0% of customers, I didn't need to segment the customer base into 15 micro-deciles. The core strategic hypothesis—whether to launch a VIP tier—was already decisively answered with a 'no'.
  >
  > Good analysis knows when additional granularity produces diminishing marginal business value."
* **Trap to Avoid**: Saying you stopped because you ran out of time or didn't know what else to query.
* **Follow-up They'll Ask**: *"What's an example of an analytical rabbit hole you avoided?"* (Answer: Doing natural language processing topic modeling on 100,000 Portuguese text reviews when the quantitative 1-star vs 5-star rating correlation already gave the operational answer).

---

### Q13: "If you had one week to extend this project, what would you do?"
* **Spoken Answer (45s)**:
  > "I would do two things:
  > 1. **Complete the Causal Investigation**: I already built a matched-pair query controlling for product, state, and price (which showed a -1.59 star penalty). Next, I would build a logistic regression model controlling for seller tenure and delivery distance to calculate the marginal probability of a 1-star review per extra day of delay.
  > 2. **Build an Interactive Stakeholder App**: I would wrap the processed SQL datasets into a self-service dashboard (like Streamlit or Power BI Service) with scenario modeling sliders—allowing logistics managers to simulate review score recovery under different SLA thresholds."
* **Trap to Avoid**: Proposing extensions unrelated to the core business objectives.
* **Follow-up They'll Ask**: *"Why Streamlit or Power BI over static notebooks?"* (Answer: Static notebooks are for analysts to do math; interactive dashboards empower non-technical operations leads to self-serve insights without writing SQL).
