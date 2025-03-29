
import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from utils import parse_date  

def build_bills_df(bills):
    """Construct a DataFrame from bills in session state."""
    data = []
    for b in bills:
        if b.date:
            dt = parse_date(b.date)
            year_month = dt.strftime("%Y-%m")
            data.append({
                "year_month": year_month,
                "amount": float(b.amount),  
                "recurring": b.recurring,
                "creditor": b.creditor
            })
    return pd.DataFrame(data)

def render_detailed_monthly_breakdown(df):
    st.subheader("Detailed Monthly Breakdown by Creditor")
    df_monthly = df.groupby(["year_month", "creditor"])["amount"].sum().reset_index()
    pivot_monthly = df_monthly.pivot(index="year_month", columns="creditor", values="amount").fillna(0)
    pivot_monthly["Total"] = pivot_monthly.sum(axis=1)
    st.dataframe(pivot_monthly)

def render_yearly_recurring_table(df):
    st.subheader("Yearly Recurring Table (12× for Recurring)")
    if df.empty or "creditor" not in df.columns:
        st.info("Missing data for yearly recurring table.")
        return
    df_rec = df[df["recurring"] == True]
    df_one = df[df["recurring"] == False]
    df_rec_grouped = df_rec.groupby(["year_month", "creditor"])["amount"].sum().reset_index()
    df_rec_grouped["year"] = df_rec_grouped["year_month"].apply(lambda ym: ym.split("-")[0])
    yearly_map = defaultdict(lambda: defaultdict(float))
    for _, row in df_rec_grouped.iterrows():
        yearly_map[row["year"]][row["creditor"]] += 12 * row["amount"]
    df_one_grouped = df_one.groupby(["year_month", "creditor"])["amount"].sum().reset_index()
    df_one_grouped["year"] = df_one_grouped["year_month"].apply(lambda ym: ym.split("-")[0])
    for _, row in df_one_grouped.iterrows():
        yearly_map[row["year"]][row["creditor"]] += row["amount"]

    years_sorted = sorted(yearly_map.keys())
    all_creds = set()
    for y in years_sorted:
        all_creds.update(yearly_map[y].keys())
    all_creds = sorted(all_creds)

    table_data = []
    for y in years_sorted:
        row_dict = {"year": y}
        for cred in all_creds:
            row_dict[cred] = yearly_map[y][cred]
        table_data.append(row_dict)
    df_yearly = pd.DataFrame(table_data).set_index("year")
    df_yearly["Total"] = df_yearly.sum(axis=1)
    st.dataframe(df_yearly)

def render_monthly_total_spending(df):
    st.subheader("Monthly Total Spending")
    monthly_totals = df.groupby("year_month")["amount"].sum().sort_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x=monthly_totals.index, y=monthly_totals.values)
    plt.title("Total Monthly Spending", fontsize=15)
    plt.xlabel("Year-Month", fontsize=12)
    plt.ylabel("Total kr", fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt.gcf())

def render_monthly_recurring_vs_onetime(df):
    st.subheader("Monthly Spend: Recurring vs One-time")
    monthly_breakdown = df.groupby(["year_month", "recurring"])["amount"].sum().unstack(fill_value=0).sort_index()
    plt.figure(figsize=(10, 6))
    monthly_breakdown.plot(kind="bar", stacked=True)
    plt.title("Recurring vs One-time Spending", fontsize=15)
    plt.xlabel("Year-Month", fontsize=12)
    plt.ylabel("Total kr", fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title="Bill Type", labels=["One-time", "Recurring"])
    plt.tight_layout()
    st.pyplot(plt.gcf())

def render_yearly_total_spending(df):
    st.subheader("Yearly Total Spending")
    df["year"] = df["year_month"].apply(lambda ym: ym.split("-")[0])
    yearly_totals = df.groupby("year")["amount"].sum().sort_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x=yearly_totals.index, y=yearly_totals.values)
    plt.title("Total Yearly Spending", fontsize=15)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Total kr", fontsize=12)
    plt.tight_layout()
    st.pyplot(plt.gcf())

def render_projected_recurring_bills(bills):
    st.subheader("Projected Recurring Bills (Next 12 Months)")
    recurring_bills = [b for b in bills if b.recurring and b.amount]
    if not recurring_bills:
        st.info("No recurring bills to project.")
        return
    df_r = pd.DataFrame([{"creditor": b.creditor, "amount": float(b.amount)} for b in recurring_bills])
    creditor_sums = df_r.groupby("creditor")["amount"].sum()
    start_date = datetime.date.today()
    months = [start_date.replace(day=1) + relativedelta(months=i) for i in range(12)]
    df_projection = pd.DataFrame(
        0,
        index=[m.strftime("%Y-%m") for m in months],
        columns=creditor_sums.index
    )
    for cred, amt in creditor_sums.items():
        df_projection[cred] = amt
    df_projection["Total"] = df_projection.sum(axis=1)
    
    # Line chart
    plt.figure(figsize=(12, 6))
    for column in df_projection.drop(columns="Total").columns:
        plt.plot(df_projection.index, df_projection[column], label=column, marker='o')
    plt.title("Projected Next 12 Months (Line)", fontsize=15)
    plt.xlabel("Year-Month", fontsize=12)
    plt.ylabel("kr", fontsize=12)
    plt.legend(title="Creditors", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt.gcf())
    
    # Area chart
    plt.figure(figsize=(12, 6))
    df_projection.drop(columns="Total").plot.area()
    plt.title("Projected Next 12 Months (Area)", fontsize=15)
    plt.xlabel("Year-Month", fontsize=12)
    plt.ylabel("kr", fontsize=12)
    plt.legend(title="Creditors", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt.gcf())

def render_last_year_step_function_chart(df):
    st.subheader("Last Year Step-Function Chart")
    df_rec = df[df["recurring"] == True].copy()
    if df_rec.empty:
        st.info("No recurring bills to plot.")
        return
    df_rec["date"] = df_rec["year_month"].apply(lambda ym: datetime.datetime.strptime(ym, "%Y-%m"))
    creditors = df_rec["creditor"].unique()
    global_earliest = df_rec["date"].min()
    months_back = 12
    start_date = global_earliest - relativedelta(months=months_back)
    end_date = df_rec["date"].max()

    monthly_range = []
    cur = start_date
    while cur <= end_date:
        monthly_range.append(cur)
        cur += relativedelta(months=1)

    df_projection = pd.DataFrame(index=[m.strftime("%Y-%m") for m in monthly_range])
    for cred in creditors:
        cdf = df_rec[df_rec["creditor"] == cred].copy()
        cdf = cdf.groupby("date")["amount"].sum().reset_index().sort_values("date")
        known_points = list(zip(cdf["date"], cdf["amount"]))
        costs = []
        for m_date in monthly_range:
            if m_date < known_points[0][0]:
                cost = known_points[0][1]
            else:
                relevant = [amt for (dt, amt) in known_points if dt <= m_date]
                cost = relevant[-1] if relevant else known_points[0][1]
            costs.append(cost)
        df_projection[cred] = costs

    df_projection["Total"] = df_projection.sum(axis=1)
    
    plt.figure(figsize=(12, 6))
    for column in df_projection.drop(columns="Total").columns:
        plt.plot(df_projection.index, df_projection[column], label=column, marker='o')
    plt.title("Last Year Step-Function: Earliest Price for Prior Months", fontsize=15)
    plt.xlabel("Year-Month", fontsize=12)
    plt.ylabel("kr", fontsize=12)
    plt.legend(title="Creditors", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt.gcf())
    st.caption("Each creditor uses its earliest known bill cost for prior months, updating with new bills.")


def render_statement_spending_chart(transactions):
    if not transactions:
        st.info("No transaction data available.")
        return

    df = pd.DataFrame(transactions)

    df['trans_date'] = pd.to_datetime(df['trans_date'])
    df['month'] = df['trans_date'].dt.to_period('M').dt.to_timestamp()
    monthly_totals = df.groupby('month', as_index=False)['amount'].sum()

    st.subheader("Monthly Total Spending (Bank Statement)")
    plt.figure(figsize=(10, 6))
    sns.barplot(data=monthly_totals, x='month', y='amount', color='skyblue')
    plt.title("Monthly Total Spending")
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.xticks(rotation=45)

    st.pyplot(plt.gcf())
    
def render_spending_by_creditor(transactions):
    if not transactions:
        st.info("No transaction data available.")
        return
    
    df = pd.DataFrame(transactions)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    creditor_totals = df.groupby('creditor', as_index=False)['amount'].sum()
    
    st.subheader("Total Spending by Creditor")
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=creditor_totals, 
        x='creditor', 
        y='amount', 
        hue='creditor', 
        palette='viridis', 
        dodge=False
    )
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()

    
    plt.title("Spending Grouped by Creditor")
    plt.xlabel("Creditor")
    plt.ylabel("Total Amount")
    plt.xticks(rotation=45, ha='right')
    
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
    for container in ax.containers:
        ax.bar_label(container, fmt=lambda x: format(x, ',.0f').replace(',', '.'))
    
    st.pyplot(plt.gcf())

    
    
def render_costs_by_category(transactions):
    if not transactions:
        st.info("No transaction data available.")
        return
    
    df = pd.DataFrame(transactions)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    cost_df = df[df['amount'] < 0].copy()
    if cost_df.empty:
        st.info("No cost data available (all amounts are positive).")
        return
    
    # Group by category and sum costs (taking absolute values)
    cost_by_category = cost_df.groupby('category', as_index=False)['amount'].sum()
    cost_by_category['total_cost'] = cost_by_category['amount'].abs()
    
    st.subheader("Costs Grouped by Category")
    
    plt.figure(figsize=(10, 6))
    # Use hue='category' so that palette can be mapped correctly, then remove the legend.
    ax = sns.barplot(
        data=cost_by_category, 
        x='category', 
        y='total_cost', 
        hue='category', 
        palette='magma', 
        dodge=False
    )
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()

    plt.title("Total Costs by Category")
    plt.xlabel("Category")
    plt.ylabel("Cost (absolute value)")
    plt.xticks(rotation=45, ha='right')
    
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
    for container in ax.containers:
        ax.bar_label(container, fmt=lambda x: format(x, ',.0f').replace(',', '.'))
    
    st.pyplot(plt.gcf())
