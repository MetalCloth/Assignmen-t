import streamlit as st
import pandas as pd
import datetime
from typing import Literal, Optional
from prompts import summary_prompt
from fpdf import FPDF

from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Expense Tracker",
    layout="wide"
)


def generate_ai_summary(expenses_df: pd.DataFrame):
    """Generates a summary using the AI chain."""
    llm=ChatOllama(model="llama3", temperature=0)
    prompt=summary_prompt()
    chain=prompt | llm 
    data=expenses_df.to_string(index=False, columns=["Date", "Category", "Amount", "Description"])
    try:
        summary = chain.invoke({"data": data})
        return summary.content
    except Exception as e:
        st.error("Could not connect to the AI model. Please ensure Ollama is running.")
        return None

def create_pdf_summary(summary_text: str):
    """Creates a PDF file in memory from the summary text."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    lines = summary_text.split('\n')
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('### '):
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, stripped_line.replace('###', ''), ln=True, align='C')
            pdf.set_font("Helvetica", size=12)
            pdf.ln(5)  
        elif stripped_line.startswith('* ') or stripped_line.startswith('- '):
            pdf.cell(5) 
            clean_line = stripped_line.lstrip('*- ').replace('**', '')
            pdf.multi_cell(0, 7, f"- {clean_line}")
        elif stripped_line:  
            pdf.multi_cell(0, 7, stripped_line)
        else:
            pdf.ln(5)  

    return pdf.output(dest='S').encode('latin-1')


st.title("AI Expense Tracker")

### initialise session state for storing expenses
if 'expenses' not in st.session_state:
    st.session_state.expenses = []

# --- Input Form ---
st.subheader("Add a New Expense")
CATEGORIES = ["Food", "Rent", "Travel", "Entertainment", "Utilities", "Other"]

with st.form("expense_form", clear_on_submit=True):
    col_form1, col_form2, col_form3 = st.columns(3)
    with col_form1:
        description = st.text_input("Description", placeholder="Groceries")
    with col_form2:
        category = st.selectbox("Category",CATEGORIES)
    with col_form3:
        amount = st.number_input("Amount",min_value=0.01,format="%.2f")

    submitted = st.form_submit_button("Add Expense", type="primary")

if submitted:
    new_expense = {
        "Date": datetime.date.today(),
        "Description": description if description else " ",
        "Category": category,
        "Amount": amount,
    }
    st.session_state.expenses.append(new_expense)
    st.success(f"Logged: ${amount:.2f} for {category}")


st.divider()

# --- Display Expenses and Summaries ---
if st.session_state.expenses:
    expenses_df = pd.DataFrame(st.session_state.expenses)
    expenses_df['Date'] = pd.to_datetime(expenses_df['Date'])

    col1, col2 = st.columns([3,2])

    with col1:
        st.subheader("Recent Expenses")
        st.dataframe(
            expenses_df.sort_values(by="Date", ascending=False).style.format({"Amount": "${:.2f}"}),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("Expense Summary")
        
        summary_df=expenses_df.groupby('Category')['Amount'].sum().reset_index()
        summary_df=summary_df.sort_values(by="Amount",ascending=False)
        st.bar_chart(summary_df.set_index('Category')['Amount'])
        total_expenses=expenses_df['Amount'].sum()
        st.metric(label="Total Expenses",value=f"${total_expenses:,.2f}")
        
        if st.button("Generate My Spending Summary", type="secondary"):
            with st.spinner("The AI is analyzing your spending..."):
                ai_summary = generate_ai_summary(expenses_df)
                if ai_summary:
                    st.write(ai_summary)
                    
                    # Generate PDF in memory
                    pdf_bytes = create_pdf_summary(ai_summary)
                    
                    # Add download button
                    st.download_button(
                        label="Download as PDF",
                        data=pdf_bytes,
                        file_name="expense_summary.pdf",
                        mime="application/pdf"
                    )

else:
    st.info("Your expense list is empty. Add an expense above to get started.")

