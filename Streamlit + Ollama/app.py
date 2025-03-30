import streamlit as st
import seaborn as sns

from utils import *

from db import (
    initialize_db,
    save_bill,
    get_bills,
    update_bill_recurring_status,
    delete_bill,
    get_transactions,
    import_statement_xlsx,
)

from analytics import (
    build_bills_df,
    render_detailed_monthly_breakdown,
    render_yearly_recurring_table,
    render_monthly_total_spending,
    render_monthly_recurring_vs_onetime,
    render_yearly_total_spending,
    render_projected_recurring_bills,
    render_last_year_step_function_chart,
    render_statement_spending_chart,
    render_spending_by_creditor,
    render_costs_by_category
)


def load_bills():
    """Load bills into session state if not already loaded."""
    if "bills" not in st.session_state:
        st.session_state.bills = get_bills()
        
def load_transactions():
    """Load transactions into session state if not already loaded."""
    if "transactions" not in st.session_state:
        transactions = get_transactions()
        st.session_state.transactions = [t.to_dict() for t in transactions]



def main():
    st.title("Financial Analyzer")
    initialize_db()
    load_bills()
    load_transactions()
    
    injected_prompt = create_financial_prompt_injection(
        st.session_state.bills, st.session_state.transactions
    )

    # Set color palette
    sns.set_palette("deep")
    sns.set_style("whitegrid")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Bills", "📑 Existing Bills", "📊 Analytics", "🤖 AI Assistant"
    ])

    # --- Tab 1: Upload Bills ---
    with tab1:
        st.subheader("Upload Bills & Bank Statements")
        files = st.file_uploader("Upload your bills or bank statements here", accept_multiple_files=True)
        if files:
            for file in files:
                if file.type == "application/pdf":
                    text = extract_text_from_pdf(file)
                    bill = extract_info(text)
                    if any(b.id == bill.id for b in st.session_state.bills):
                        st.warning(f"{file.name} already exists.")
                        continue
                    save_bill(bill)
                    st.session_state.bills.append(bill)
                    st.success(f"Saved {file.name}")
                    st.markdown(f"**Amount:** {int(bill.amount)} kr")
                    st.markdown(f"**Creditor:** {bill.creditor}")
                    st.markdown(f"**Date:** {bill.date}")
                    st.write("---")
                elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    import_statement_xlsx(file)
                    st.success(f"Imported transactions from {file.name}")
                else:
                    st.warning(f"Unsupported file type: {file.type}. Please upload a PDF or XLSX.")
            
            transactions = get_transactions()
            st.session_state.transactions = [t.to_dict() for t in transactions]

            st.subheader("Transactions Imported")
            st.dataframe(st.session_state.transactions)
            
           


        st.subheader("Add a Bill or Subscription Manually")
        with st.form("manual_bill_form"):
            creditor_input = st.text_input("Creditor")
            date_input = st.date_input("Date")  
            amount_input = st.number_input("Amount (kr)", min_value=0, value=0)
            recurring_input = st.checkbox("Recurring?")
            submitted = st.form_submit_button("Add Bill")
            if submitted:
                date_str = date_input.strftime("%d.%m.%Y")
                manual_bill = Bill(creditor_input, date_str, str(amount_input), recurring_input)
                if any(b.id == manual_bill.id for b in st.session_state.bills):
                    st.warning("This bill already exists in the database.")
                else:
                    save_bill(manual_bill)
                    st.session_state.bills.append(manual_bill)
                    st.success(f"Added bill for {creditor_input} on {date_str}")

    # --- Tab 2: Existing Bills ---
    with tab2:
        if not st.session_state.bills:
            st.write("No existing bills found.")            

        creditors = sorted({b.creditor for b in st.session_state.bills})
        selected_creditor = st.selectbox("Filter by Creditor", ["All"] + creditors)
        filtered_bills = [
            b for b in st.session_state.bills
            if selected_creditor == "All" or b.creditor == selected_creditor
        ]

        recurring_filter = st.selectbox("Filter by Recurring status", ["All", "Recurring", "One-time"])
        if recurring_filter != "All":
            want_recurring = (recurring_filter == "Recurring")
            filtered_bills = [b for b in filtered_bills if b.recurring == want_recurring]

        sort_option = st.selectbox("Sort by:", [
            "Date (Newest First)", "Date (Oldest First)", "Creditor (A-Z)", "Creditor (Z-A)"
        ])
        if sort_option == "Date (Newest First)":
            filtered_bills.sort(key=lambda x: parse_date(x.date), reverse=True)
        elif sort_option == "Date (Oldest First)":
            filtered_bills.sort(key=lambda x: parse_date(x.date))
        elif sort_option == "Creditor (A-Z)":
            filtered_bills.sort(key=lambda x: x.creditor.lower())
        elif sort_option == "Creditor (Z-A)":
            filtered_bills.sort(key=lambda x: x.creditor.lower(), reverse=True)

        if not filtered_bills:
            st.write("No bills match your current filter.")
        else:
            for bill in filtered_bills:
                info = bill.to_dict()
                st.markdown(f"### {info['creditor']} - {int(info['amount'])} kr")
                st.write(f"**Date:** {info['date']}")
                cb_key = f"recurring_{info['id']}"
                if cb_key not in st.session_state:
                    st.session_state[cb_key] = info["recurring"]
                new_status = st.checkbox("Recurring bill", key=cb_key, value=st.session_state[cb_key])
                if new_status != info["recurring"]:
                    update_bill_recurring_status(info["id"], new_status)
                    for i, existing in enumerate(st.session_state.bills):
                        if existing.id == info["id"]:
                            st.session_state.bills[i].recurring = new_status
                            break
                    st.success(f"Updated to {'Recurring' if new_status else 'One-time'}")
                if st.button("❌ Delete Bill", key=f"delete_{info['id']}"):
                    delete_bill(info["id"])
                    st.session_state.bills = [x for x in st.session_state.bills if x.id != info["id"]]
                    st.warning(f"Deleted bill {info['amount']} kr")
                st.write("---")

    # --- Tab 3: Analytics ---
    with tab3:
        st.header("Analytics")

        if not st.session_state.bills and not st.session_state.transactions:
            st.write("No data to analyze.")
        else:
            if st.session_state.bills:
                # Build a DataFrame from bills
                df = build_bills_df(st.session_state.bills)
                
                render_detailed_monthly_breakdown(df)
                render_yearly_recurring_table(df)
                render_monthly_total_spending(df)
                render_monthly_recurring_vs_onetime(df)
                render_yearly_total_spending(df)
                render_projected_recurring_bills(st.session_state.bills)
                render_last_year_step_function_chart(df)
            
            if st.session_state.transactions:
                st.subheader("Bank Statement Analytics")
                render_statement_spending_chart(st.session_state.transactions)
                render_spending_by_creditor(st.session_state.transactions)
                render_costs_by_category(st.session_state.transactions)

            
        # --- Tab 4: AI Assistant ---
    with tab4:
        st.header("AI Assistant (Local Ollama)")
        if "ollama_history" not in st.session_state:
            st.session_state["ollama_history"] = []
        if "clear_input" not in st.session_state:
            st.session_state["clear_input"] = False
        if st.session_state["clear_input"]:
            st.session_state["chat_input"] = ""
            st.session_state["clear_input"] = False

        with st.form("ollama_chat_form"):
            user_input = st.text_input("Ask the AI something:", key="chat_input")
            submit_button = st.form_submit_button("Send")

        if submit_button and user_input:
            st.session_state["ollama_history"].append({"role": "user", "content": user_input})
            with st.spinner("Thinking..."):
                answer = ask_ollama(st.session_state["ollama_history"], injected_prompt)
            st.session_state["ollama_history"].append({"role": "assistant", "content": answer})
            st.session_state["clear_input"] = True
            st.rerun()

        for msg in reversed(st.session_state["ollama_history"]):
            role_label = "You" if msg["role"] == "user" else "Assistant"
            st.write(f"**{role_label}:** {msg['content']}")


if __name__ == "__main__":
    main()
