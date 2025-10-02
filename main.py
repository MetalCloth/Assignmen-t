import streamlit as st
import pandas as pd
import datetime
from typing import Literal, Optional
from prompts import summary_prompt
from prompts import cprompt
from langchain.output_parsers import PydanticOutputParser
from fpdf import FPDF

from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
# import dotenv
# from dotenv import load_dotenv
# load_dotenv()

# import os
# os.environ['GOOGLE_API_KEY']=os.getenv('GOOGLE_API_KEY')

# --- Page Configuration ---
CATEGORIES = ["Food", "Travel", "Entertainment", "Utilities", "Rent", "Other"]
CategoryLiteral = Literal["Food", "Travel", "Entertainment", "Utilities", "Rent", "Other"]

class Expense(BaseModel):
    """Represents a single expense with its amount, description, and category."""
    amount: float = Field(description="The numerical amount of the expense.")
    description: str = Field(description="A detailed description of what the expense was for.")
    category: CategoryLiteral = Field(description=f"The category of the expense. Must be one of {', '.join(CATEGORIES)}")





def parse_expense_query(query: str) -> Expense | None:
    """
    Parses a natural language query to extract expense details (amount, description, category).
    """
    parser = PydanticOutputParser(pydantic_object=Expense)
    


    prompt=cprompt(parser=parser)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    chain = prompt | llm | parser

    try:
        parsed_result = chain.invoke({
            "query": query,
            "date": datetime.date.today().strftime("%Y-%m-%d")
        })
        return parsed_result
    except Exception as e:
        st.error(f"Failed to parse your request. Please try again. Error: {e}")
        return None


st.set_page_config(
    page_title="AI Expense Tracker",
    layout="wide"
)





def generate_ai_summary(expenses_df: pd.DataFrame):
    """Generates a summary using the AI chain."""
    # llm=ChatOllama(model="llama3", temperature=0)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
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

### Initialise session state for storing expenses
if 'expenses' not in st.session_state:
    st.session_state.expenses = []

# --- Input Form for Conversational Input ---
st.subheader("Log a New Expense")

with st.form("expense_form", clear_on_submit=True):
    query = st.text_input("Enter your expense", placeholder="e.g., '$7 Uber Eats for team dinner on client visit'")
    submitted = st.form_submit_button("Log Expense", type="primary", use_container_width=True)

# --- Form Submission Logic ---
if submitted and query:
    with st.spinner("AI is processing your expense..."):
        parsed_expense = parse_expense_query(query)
    
    if parsed_expense:
        new_expense = {
            "Date": datetime.date.today(),
            "Description": parsed_expense.description.capitalize(),
            "Category": parsed_expense.category,
            "Amount": parsed_expense.amount,
        }
        st.session_state.expenses.append(new_expense)
        st.success(f"Logged: ${parsed_expense.amount:.2f} for '{parsed_expense.description.capitalize()}' ")
elif submitted and not query:
    st.warning("Enter your expense details.")

st.divider()

# --- Display Expenses and Summaries ---
if st.session_state.expenses:
    expenses_df = pd.DataFrame(st.session_state.expenses)
    expenses_df['Date'] = pd.to_datetime(expenses_df['Date'])

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Recent Expenses")
        st.dataframe(
            expenses_df.sort_values(by="Date", ascending=False).style.format({"Amount":"${:.2f}"}),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("Expense Summary")
        
        summary_df=expenses_df.groupby('Category')['Amount'].sum().reset_index()
        summary_df=summary_df.sort_values(by="Amount", ascending=False)
        st.bar_chart(summary_df.set_index('Category')['Amount'])
        total_expenses = expenses_df['Amount'].sum()
        st.metric(label="Total Expenses", value=f"${total_expenses:,.2f}")
        
        if st.button("Generate My Spending Summary", type="secondary"):
            with st.spinner("The AI is analyzing your spending..."):
                try:
                    ai_summary = generate_ai_summary(expenses_df)
                    if ai_summary:
                        st.markdown(ai_summary)
                        pdf_bytes = create_pdf_summary(ai_summary)
                        st.download_button(
                            label="Download as PDF",
                            data=pdf_bytes,
                            file_name="expense_summary.pdf",
                            mime="application/pdf"
                        )
                except NameError:
                    st.error("The `summary_prompt` function is not defined. Please ensure `prompts.py` exists.")
else:
    st.info("Your expense list is empty. Add an expense above to get started.")
