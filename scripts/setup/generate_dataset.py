"""
FinVox — Industry-Level SME Financial Dataset Generator
Simulates 12 months of realistic cashflow for a Sri Lankan SME (IT Consulting Firm).
"""

import os
import csv
import random
from datetime import datetime, timedelta, date

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample", "sme_cashflow_sample.csv")
YEAR = 2026

# ── Company Profile ──────────────────────────────────────────────────────────
# Fictional SME: "LankaTech Solutions (Pvt) Ltd" — IT Consulting, Colombo
COMPANY_CLIENTS = ["Dialog Axiata PLC", "Softlogic Holdings", "Sampath Bank", "MAS Holdings",
                   "Aitken Spence", "Ceylinco Insurance", "John Keells Holdings", "LOLC Finance",
                   "SLT-Mobitel", "Hayleys PLC", "Local Startup A", "Local Startup B",
                   "Expolanka Holdings", "Access Engineering", "Ceylon Cold Stores",
                   "Commercial Bank", "Hatton National Bank", "Browns & Company",
                   "Dipped Products", "Tokyo Cement"]

SUPPLIERS = ["CloudHosting.lk", "Microsoft Sri Lanka", "Lanka Electricity Board",
             "Sri Lanka Telecom", "Office Mart Colombo", "Lanka Advertising Agency",
             "Mercantile Investments (Loan)", "Bank of Ceylon (Loan)"]

EMPLOYEES = 12  # Fixed headcount
AVG_SALARY = 85000  # LKR per employee per month

# ── Petty Cash & Daily Ops ────────────────────────────────────────────────────
PETTY_CASH_ITEMS = [
    ("Tea/Coffee & Office Refreshments", "Petty Cash", 500, 3000),
    ("Grab / PickMe — Staff Transport", "Transport", 800, 5000),
    ("Printer Ink & Paper Restock", "Office Supplies", 2000, 8000),
    ("Team Lunch — Client Meeting", "Meals & Entertainment", 3000, 12000),
    ("Parking Fee — Colombo Office", "Transport", 200, 800),
    ("Courier — Document Delivery", "Logistics", 350, 1500),
    ("Staff Overtime Meal Allowance", "Meals & Entertainment", 1500, 6000),
    ("Photocopy & Binding — Reports", "Office Supplies", 500, 2500),
]

FREELANCER_NAMES = ["Kasun Perera", "Nimali Fernando", "Ravindu Silva",
                    "Tharushi Jayasinghe", "Malith De Silva", "Shanuki Rathnayake"]

CLIENT_RETAINERS = ["Dialog Axiata PLC", "Sampath Bank", "MAS Holdings", "SLT-Mobitel"]

# ── Seasonal Revenue Multipliers ─────────────────────────────────────────────
# Q1 = slow, Q2 = picking up, Q3 = peak season, Q4 = year-end rush
SEASONAL_MULTIPLIER = {
    1: 0.70, 2: 0.75, 3: 0.85,   # Q1 — Slow
    4: 0.90, 5: 1.00, 6: 1.10,   # Q2 — Growing
    7: 1.20, 8: 1.25, 9: 1.15,   # Q3 — Peak
    10: 1.05, 11: 0.95, 12: 1.30  # Q4 — Year-end rush
}

txn_id = 1
rows = []

def add_txn(txn_date, description, category, amount, txn_type, notes=""):
    global txn_id
    rows.append({
        "transaction_id": f"TXN{txn_id:04d}",
        "date": txn_date.strftime("%Y-%m-%d"),
        "description": description,
        "category": category,
        "amount_lkr": round(amount, 2),
        "transaction_type": txn_type,
        "notes": notes
    })
    txn_id += 1

# ── Helper Functions ─────────────────────────────────────────────────────────
import calendar

def days_in_month(year, month):
    return calendar.monthrange(year, month)[1]

# ════════════════════════════════════════════════════════════════════════════
# MONTHLY TRANSACTION GENERATION
# ════════════════════════════════════════════════════════════════════════════

for month in range(1, 13):
    multiplier = SEASONAL_MULTIPLIER[month]
    month_start = date(YEAR, month, 1)

    # ── 1. CLIENT INVOICE PAYMENTS (Major Revenue) ───────────────────────
    # 3–6 client payments per month, paid between 5th and 28th
    num_clients = random.randint(3, 6)
    selected_clients = random.sample(COMPANY_CLIENTS, num_clients)
    for client in selected_clients:
        pay_day = random.randint(5, 28)
        pay_date = date(YEAR, month, pay_day)
        base = random.uniform(150000, 600000) * multiplier
        add_txn(pay_date,
                f"Invoice Payment — {client}",
                "Sales Revenue",
                base,
                "Credit",
                f"Project milestone payment from {client}")

    # ── 2. SALARIES (Fixed, 25th of every month) ─────────────────────────
    salary_date = date(YEAR, month, 25)
    total_salary = EMPLOYEES * AVG_SALARY * random.uniform(0.97, 1.03)  # slight variation
    add_txn(salary_date,
            f"Staff Salaries — {EMPLOYEES} Employees",
            "Salaries",
            -total_salary,
            "Debit",
            "Monthly payroll run")

    # ── 3. RENT (Fixed, 1st of every month) ──────────────────────────────
    rent_date = date(YEAR, month, 1)
    rent_amount = 120000 * random.uniform(0.98, 1.02)  # almost fixed
    add_txn(rent_date,
            "Office Rent — Colombo 3, Level 4",
            "Rent",
            -rent_amount,
            "Debit",
            "Monthly office lease payment")

    # ── 4. ELECTRICITY BILL (10th of every month) ────────────────────────
    elec_date = date(YEAR, month, 10)
    elec_amount = random.uniform(18000, 45000) * (1.1 if month in [6, 7, 8] else 1.0)  # summer peak
    add_txn(elec_date,
            "Lanka Electricity Board — Office Bill",
            "Electricity Bill",
            -elec_amount,
            "Debit",
            "Monthly electricity consumption")

    # ── 5. INTERNET & CLOUD HOSTING ──────────────────────────────────────
    internet_date = date(YEAR, month, 12)
    add_txn(internet_date,
            "SLT Fiber — Office Broadband (1Gbps)",
            "Internet Bill",
            -random.uniform(8500, 12000),
            "Debit",
            "Monthly ISP subscription")

    cloud_date = date(YEAR, month, random.randint(14, 18))
    add_txn(cloud_date,
            "CloudHosting.lk — Server & Hosting",
            "Cloud & Software",
            -random.uniform(25000, 85000),
            "Debit",
            "Monthly cloud infrastructure")

    # ── 6. MARKETING SPEND (Variable — heavier in Q3/Q4) ─────────────────
    if random.random() < 0.75:  # Not every month
        mkt_date = date(YEAR, month, random.randint(8, 20))
        mkt_amount = random.uniform(20000, 120000) * multiplier
        add_txn(mkt_date,
                "Lanka Advertising Agency — Digital Campaign",
                "Marketing",
                -mkt_amount,
                "Debit",
                f"Online ads & social media campaign — month {month}")

    # ── 7. OFFICE SUPPLIES (Occasional) ──────────────────────────────────
    if random.random() < 0.50:
        supply_date = date(YEAR, month, random.randint(5, 25))
        add_txn(supply_date,
                "Office Mart Colombo — Stationery & Equipment",
                "Office Supplies",
                -random.uniform(5000, 35000),
                "Debit",
                "Office consumables and equipment")

    # ── 8. QUARTERLY TAX PAYMENT (March, June, September, December) ───────
    if month in [3, 6, 9, 12]:
        tax_date = date(YEAR, month, 20)
        tax_amount = random.uniform(80000, 250000)
        add_txn(tax_date,
                f"Inland Revenue — Quarterly Tax Payment Q{month // 3}",
                "Tax",
                -tax_amount,
                "Debit",
                "Corporate income tax installment")

    # ── 9. LOAN REPAYMENT (Monthly EMI) ──────────────────────────────────
    if month >= 2:  # Loan taken in Jan, repayment starts Feb
        emi_date = date(YEAR, month, 5)
        add_txn(emi_date,
                "Bank of Ceylon — Business Loan EMI",
                "Loan Repayment",
                -75000,
                "Debit",
                "Monthly EMI for LKR 3.6M business loan")

    # ── 10. ONE-TIME / IRREGULAR EVENTS ──────────────────────────────────
    # January: Bank loan received
    if month == 1:
        add_txn(date(YEAR, 1, 15),
                "Bank of Ceylon — Business Loan Disbursement",
                "Bank Loan",
                3600000,
                "Credit",
                "3-year business expansion loan @ 14% p.a.")

    # March: Annual Software License renewal
    if month == 3:
        add_txn(date(YEAR, 3, 5),
                "Microsoft Sri Lanka — Office 365 Annual License",
                "Software License",
                -180000,
                "Debit",
                "Annual Microsoft 365 Business license — 12 seats")

    # June: Staff Training & Development
    if month == 6:
        add_txn(date(YEAR, 6, 18),
                "ICTA Sri Lanka — Staff Training Program",
                "Training & Development",
                -95000,
                "Debit",
                "Cloud computing certification for 3 engineers")

    # August: Investment return (FD matured)
    if month == 8:
        add_txn(date(YEAR, 8, 22),
                "Sampath Bank — Fixed Deposit Maturity",
                "Investment Return",
                480000,
                "Credit",
                "12-month FD matured with 10.5% interest")

    # October: Laptop purchase for new hire
    if month == 10:
        add_txn(date(YEAR, 10, 5),
                "Abans PLC — 3x Dell Latitude Laptops",
                "Equipment Purchase",
                -520000,
                "Debit",
                "New employee onboarding equipment")

    # December: Year-end performance bonus
    if month == 12:
        bonus_amount = EMPLOYEES * random.uniform(20000, 50000)
        add_txn(date(YEAR, 12, 20),
                "Year-End Performance Bonus — All Staff",
                "Salaries",
                -bonus_amount,
                "Debit",
                "Annual performance bonus payout")

    # ── 11. PETTY CASH — Daily micro-transactions (32–42 per month) ────
    num_petty = random.randint(32, 42)
    for _ in range(num_petty):
        item = random.choice(PETTY_CASH_ITEMS)
        desc, cat, min_amt, max_amt = item
        p_day = random.randint(1, days_in_month(YEAR, month))
        p_date = date(YEAR, month, p_day)
        add_txn(p_date, desc, cat, -random.uniform(min_amt, max_amt), "Debit", "Petty cash expense")

    # ── 12. FREELANCER PAYMENTS (5–8 per month) ────────────────────
    num_freelancers = random.randint(5, 8)
    for _ in range(num_freelancers):
        fl_name = random.choice(FREELANCER_NAMES)
        fl_day = random.randint(10, 28)
        fl_date = date(YEAR, month, fl_day)
        fl_amt = random.uniform(25000, 120000)
        add_txn(fl_date,
                f"Freelancer Payment — {fl_name}",
                "Freelancer Fees",
                -fl_amt,
                "Debit",
                f"Contract work — {fl_name}")

    # ── 13. CLIENT RETAINER FEES (Fixed monthly, 1st of month) ───────────
    for retainer_client in CLIENT_RETAINERS:
        r_amt = random.uniform(50000, 150000)
        r_date = date(YEAR, month, 1)
        add_txn(r_date,
                f"Monthly Retainer — {retainer_client}",
                "Retainer Fee",
                r_amt,
                "Credit",
                f"Fixed monthly support retainer from {retainer_client}")

    # ── 14. BANK CHARGES & FEES (Monthly) ────────────────────────────────
    bank_date = date(YEAR, month, random.randint(15, 28))
    add_txn(bank_date,
            "Sampath Bank — Monthly Account Maintenance",
            "Bank Charges",
            -random.uniform(500, 2500),
            "Debit",
            "Monthly bank service charge")

    # ── 15. ATM/CASH WITHDRAWALS (Petty cash replenishment) ──────────────
    for _ in range(random.randint(5, 9)):
        atm_day = random.randint(1, days_in_month(YEAR, month))
        atm_date = date(YEAR, month, atm_day)
        add_txn(atm_date,
                "ATM Withdrawal — Petty Cash Fund",
                "Cash Withdrawal",
                -random.uniform(5000, 25000),
                "Debit",
                "Petty cash fund replenishment")

    # ── 16. MISCELLANEOUS INCOME (Rebates, refunds) ───────────────────────
    if random.random() < 0.35:
        misc_day = random.randint(5, 28)
        misc_date = date(YEAR, month, misc_day)
        misc_sources = [
            ("Tax Refund — IRD Sri Lanka", "Tax Refund", 45000, 180000),
            ("Insurance Claim Reimbursement", "Insurance", 12000, 85000),
            ("Vendor Rebate — CloudHosting.lk", "Rebates", 5000, 30000),
            ("Overpayment Refund — SLT", "Refunds", 2000, 8000),
        ]
        src = random.choice(misc_sources)
        add_txn(misc_date, src[0], src[1], random.uniform(src[2], src[3]), "Credit", "Miscellaneous income")

    # ── 17. INSURANCE PREMIUM (Quarterly: Jan, Apr, Jul, Oct) ────────────
    if month in [1, 4, 7, 10]:
        ins_date = date(YEAR, month, 7)
        add_txn(ins_date,
                "Ceylinco Insurance — Business Property & Liability",
                "Insurance",
                -random.uniform(18000, 55000),
                "Debit",
                "Quarterly business insurance premium")

    # ── 18. VEHICLE FUEL & MAINTENANCE (Monthly) ─────────────────────────
    for _ in range(random.randint(6, 12)):
        fuel_day = random.randint(1, days_in_month(YEAR, month))
        fuel_date = date(YEAR, month, fuel_day)
        add_txn(fuel_date,
                "Fuel — Company Vehicle",
                "Transport",
                -random.uniform(3000, 12000),
                "Debit",
                "Company vehicle fuel top-up")

    # ── 19. VENDOR INVOICE PAYMENTS (2–3 per month) ───────────────────────
    vendors = [
        ("Abans PLC — IT Equipment Maintenance", "Equipment Maintenance", 15000, 60000),
        ("Dialog — Mobile Bills (Staff)", "Telephone", 8000, 25000),
        ("Printcare PLC — Stationery Order", "Office Supplies", 10000, 40000),
        ("Keells Super — Office Pantry", "Petty Cash", 3000, 15000),
        ("DIMO — Vehicle Service", "Transport", 15000, 55000),
    ]
    for _ in range(random.randint(4, 7)):
        v = random.choice(vendors)
        v_day = random.randint(5, 28)
        v_date = date(YEAR, month, v_day)
        add_txn(v_date, v[0], v[1], -random.uniform(v[2], v[3]), "Debit", "Vendor invoice payment")



# ── WRITE TO CSV ──────────────────────────────────────────────────────────────
fieldnames = ["transaction_id", "date", "description", "category", "amount_lkr",
              "transaction_type", "notes"]

# Sort by date for realism
rows.sort(key=lambda x: x["date"])

with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
total_in = sum(r["amount_lkr"] for r in rows if r["amount_lkr"] > 0)
total_out = sum(r["amount_lkr"] for r in rows if r["amount_lkr"] < 0)
net = total_in + total_out

print(f"[OK] Dataset generated: '{OUTPUT_FILE}'")
print(f"   Total Transactions : {len(rows)}")
print(f"   Total Inflow       : LKR {total_in:,.2f}")
print(f"   Total Outflow      : LKR {abs(total_out):,.2f}")
print(f"   Net Cash Flow      : LKR {net:,.2f} ({'SURPLUS' if net > 0 else 'DEFICIT'})")
