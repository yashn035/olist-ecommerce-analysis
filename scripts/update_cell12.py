import json
from pathlib import Path

nb_path = Path("notebooks/eda.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

new_src = [
    "# Cell 12: EXECUTIVE SUMMARY & KEY FINDINGS\n",
    'print("=" * 80)\n',
    'print("                      EXECUTIVE PORTFOLIO FINDINGS")\n',
    'print("=" * 80)\n',
    'print("1. REVENUE GROWTH & SEASONALITY:")\n',
    'print("   Gross marketplace sales expanded rapidly throughout 2017 and peaked in November 2017")\n',
    'print("   at R$ 987,765.37 across 7,289 orders (+52.37% MoM), before stabilizing around R$ 902k/mo in 2018.")\n',
    'print("")\n',
    'print("2. CUSTOMER RETENTION DEFICIT:")\n',
    'print("   The marketplace operates almost entirely on single-transaction customer acquisitions;")\n',
    'print("   repeat purchase rate is 3.00% (2,789 repeat buyers) with Month 1 cohort retention")\n',
    'print("   averaging just 0.48% across all monthly cohorts.")\n',
    'print("")\n',
    'print("3. SEVERE LOGISTICS REPUTATIONAL RISK:")\n',
    'print("   Late delivery inflicts massive reputational damage, dropping average customer review scores")\n',
    'print("   from 4.29 to 2.57 stars (-1.72 drop), with 1-star reviews surging from 6.58% to 46.15%.")\n',
    'print("")\n',
    'print("4. GEOGRAPHIC LOGISTICS FRICTION:")\n',
    'print("   Logistics delays are concentrated in remote Northern and Northeastern states, where transit")\n',
    'print("   times reach 24.52 to 29.91 days with late rates in Alagoas (AL) reaching 23.99%.")\n',
    'print("")\n',
    'print("5. DISPROPORTIONATE FREIGHT BURDEN:")\n',
    'print("   Shipping fees represent 51.53% to 59.58% of product value for remote consumers (e.g. RO, MA, PB),")\n',
    'print("   compared to 26.51% in Sao Paulo, creating steep regional friction.")\n',
    'print("")\n',
    'print("6. THE PARETO MISCONCEPTION:")\n',
    'print("   The customer revenue distribution does not exhibit an 80/20 rule: the top 20% of customers")\n',
    'print("   generate only 56.61% of revenue, and it takes 45.00% of customers to reach 80% of revenue.")\n',
    'print("   Growth depends on customer acquisition volume rather than an entrenched VIP luxury cohort.")\n',
    'print("=" * 80)\n'
]

nb["cells"][-1]["source"] = new_src

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Updated Cell 12 in eda.ipynb")
