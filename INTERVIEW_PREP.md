# Olist E-Commerce Analysis: Data Analyst Interview Preparation Guide

This guide prepares you to discuss this portfolio project in technical and behavioral data analyst interviews. Every answer incorporates **actual computed figures** from the analysis and outlines common pitfalls ("What NOT to Say").

---

### Question 1: "Can you walk me through this project?"
* **Structure**: Business Problem → Dataset & Grain → Method → Key Finding → Strategic Recommendation.
* **Spoken Answer (45–60s)**:
  > "I analyzed the Olist Brazilian E-Commerce dataset—which covers roughly 100,000 orders between 2016 and 2018—to answer a core growth question: what actually drives revenue and repeat purchases, and where should logistics capital go?
  >
  > I built an end-to-end analytics pipeline: extracting and cleaning 9 relational tables in Python, modeling them in PostgreSQL and SQLite, and building an analytical star schema in Power BI.
  >
  > Two major findings stood out: first, Olist's repeat purchase rate is exceptionally low at 3.00%, with Month 1 cohort retention collapsing to 0.48%. Second, delivery delays inflict massive reputational damage—when deliveries miss the estimated date, customer ratings drop from 4.29 to 2.57 stars, with 1-star reviews surging to 46.15%.
  >
  > My core recommendation was to argue *against* a standard 'VIP Loyalty Program' because the top 20% of buyers drive only 56.6% of revenue, and instead reallocate capital toward automated 30–60 day consumable replenishment triggers and regional micro-fulfillment hubs in the Northeast where transit times currently exceed 24 days."
* **What NOT to Say**:
  * ❌ *"I downloaded some Kaggle data, made some charts in seaborn, and found that Black Friday was big."* (Lacks business problem, methodology, and concrete operational recommendations).

---

### Question 2: "What was your most surprising finding?"
* **Spoken Answer (30–45s)**:
  > "My most surprising finding was completely debunking the traditional 80/20 Pareto principle. In retail analytics, stakeholders routinely assume that the top 20% of customers generate 80% of revenue and push for expensive VIP programs.
  >
  > When I ran a cumulative revenue percentile query across all 93,104 unique customers, the top 20% generated only 56.61% of total revenue. In fact, reaching 80% of revenue required 45.00% of all customers. 
  >
  > This proved that Olist operates as a high-volume, single-transaction customer acquisition engine with a long tail of one-time buyers, rather than a business sustained by an entrenched luxury cohort."
* **What NOT to Say**:
  * ❌ *"Everything pretty much followed the 80/20 rule like textbooks say."* (Shows you didn't check the data or calculated rank percentiles backwards).

---

### Question 3: "How did you define revenue in your analysis?"
* **Spoken Answer (30–45s)**:
  > "I defined top-line revenue as Gross Merchandise Value (GMV)—the sum of product item price plus freight paid by the customer on delivered orders (`SUM(price) + SUM(freight_value)`), which totaled R$ 13.18 million across the clean 20-month window.
  >
  > In product category analyses, I isolated product price alone (`SUM(price)`) to evaluate pure merchandise demand without geographic freight distortions. It's important to clarify that this represents gross platform sales volume, not Olist's net marketplace take-rate commission."
* **What NOT to Say**:
  * ❌ *"I just summed the payment table."* (Red flag: summing payments across multi-item orders without grain awareness leads to catastrophic double-counting).

---

### Question 4: "What is `customer_unique_id`, and why did that matter?"
* **Spoken Answer (30–45s)**:
  > "The dataset contains two customer identifiers: `customer_id` and `customer_unique_id`. `customer_id` is actually an order-level proxy generated uniquely per transaction—there are exactly 99,441 rows matching the order table 1:1.
  >
  > `customer_unique_id`, however, identifies the real human individual across multiple orders. There are 96,096 distinct unique customers. If you evaluate repeat purchase behavior using `customer_id`, your repeat rate will calculate as exactly 0%. Grouping by `customer_unique_id` revealed the true 3.00% repeat purchase rate."
* **What NOT to Say**:
  * ❌ *"They were basically duplicates in the customer table, so I just used customer_id."* (Shows failure to understand relational grain).

---

### Question 5: "Is a 3% repeat purchase rate bad? How do you interpret that?"
* **Spoken Answer (45–60s)**:
  > "In isolation, 3.00% sounds alarmingly low compared to mature D2C e-commerce benchmarks of 20–30%. However, the context and curve shape matter more than the raw number.
  >
  > Olist is an aggregation marketplace for third-party merchants selling durable, high-ticket, one-off items like furniture, tools, and auto parts. Customers often don't realize they are buying through 'Olist'—they buy via Mercado Livre or B2W where Olist is just the backend integrator.
  >
  > When I examined the cohort curve, Month 1 is the peak return period at only 0.48%, quickly decaying to 0.17%. This indicates Olist functions as a top-of-funnel acquisition channel. The opportunity isn't building a generic loyalty program; it's cross-selling into repeat consumable categories like *Health & Beauty* (the #1 category at R$ 532.8k)."
* **What NOT to Say**:
  * ❌ *"Yes, 3% is terrible, the company is failing."* (Lacks business model context and domain understanding of marketplace integrators).

---

### Question 6: "You said late delivery hurts review scores. How do you know that's causal?"
* **Spoken Answer (45–60s)**:
  > "To be strictly honest, I don't—and that's an important analytical distinction. The data shows a strong correlation: on-time deliveries average 4.29 stars with only 6.58% 1-star reviews, whereas late deliveries plunge to 2.57 stars with 46.15% 1-star reviews.
  >
  > However, there are significant confounding variables: remote geographic distance, seller product defect rates, fragile packaging, and carrier handling. For example, remote Northern states like Alagoas have higher late rates (23.99%) but also higher transit times (24.5 days) and freight costs (51–59%).
  >
  > To prove causality, we would need an A/B test or an instrumental variable approach—such as carrier hub strikes that delay shipping exogenously while keeping product quality and seller behavior constant."
* **What NOT to Say**:
  * ❌ *"The p-value was tiny, so late delivery definitely causes bad reviews."* (Fails the senior-analyst test on correlation vs. causation).

---

### Question 7: "How did you handle truncated or incomplete months?"
* **Spoken Answer (30–45s)**:
  > "I audited the date distribution in SQL and found that raw timestamps spanned September 2016 to October 2018. However, 2016 only had ~329 pilot orders, while September and October 2018 contained truncated records after data logging ceased.
  >
  > If left uncleaned, a time-series line chart shows misleading 90% revenue crashes at both ends. I strictly bounded the analytical window between January 1, 2017 and August 31, 2018—yielding exactly 20 complete, contiguous monthly periods."
* **What NOT to Say**:
  * ❌ *"I just plotted all dates in the table."* (Shows lack of basic data quality profiling).

---

### Question 8: "Why did your Pareto curve deviate from the 80/20 rule?"
* **Spoken Answer (30–45s)**:
  > "The 80/20 rule is an empirical heuristic, not a mathematical law. It holds true in businesses with power-law retention—like B2B SaaS, mobile gaming with 'whales', or luxury travel.
  >
  > On Olist, the customer spend distribution has low variance because 97% of buyers make exactly one purchase with an Average Order Value of R$ 137.00. Because few buyers make 5 or 10 purchases, cumulative revenue scales almost linearly with customer count. The top 20% generate 56.61%, and reaching 80% requires 45.00% of shoppers."
* **What NOT to Say**:
  * ❌ *"My SQL code must have had a bug because it didn't equal 80/20."* (Shows lack of confidence in real empirical analysis).

---

### Question 9: "What would you do if you had more data?"
* **Spoken Answer (30–45s)**:
  > "Three specific datasets would unlock deeper strategic insights:
  > 1. **Marketing Spend & CAC**: Knowing customer acquisition costs by channel would let me calculate true Customer Lifetime Value to CAC (LTV:CAC) ratios.
  > 2. **Session & Cart Abandonment Telemetry**: Web traffic data would help evaluate whether high freight in remote states (50–60% of item price in RO and MA) is suppressing checkout conversion rates.
  > 3. **Carrier & Package Dimensions**: Package cubic weight would isolate whether seller dispatch delays or carrier transit bottlenecks drive the 24–30 day delivery times in the North."
* **What NOT to Say**:
  * ❌ *"I'd train a complex deep learning neural network on the text reviews."* (Premature complexity without business justification).

---

### Question 10: "If you had to move one metric by 10%, which one would you pick and why?"
* **Spoken Answer (45–60s)**:
  > "I would target a 10% reduction in the **Late Delivery Rate** (reducing it from 8.01% down to ~7.2%).
  >
  > Here's why: Late deliveries are the single biggest lever damaging customer goodwill. Reducing late orders directly rescues customers from the 2.57-star rating cliff and cuts the 46.15% 1-star surge.
  >
  > Operationally, I can achieve this without building new warehouses: SQL query Q10 identified chronic sellers with over 50 completed orders who maintain late rates exceeding 30% and average delays of 28–40 days. Simply enforcing seller dispatch SLAs, deprioritizing chronic late sellers in the Buy Box, and subsidizing regional consolidation in the Northeast would quickly hit that 10% target."
* **What NOT to Say**:
  * ❌ *"I would increase total revenue by 10% by running a huge discount promo."* (Ignores operational constraints and profitability).
