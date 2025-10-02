from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import datetime


def summary_prompt():
    """
    Creates a highly reliable ChatPromptTemplate for generating a financial summary
    with perfect formatting.
    """
    current_month_year = datetime.date.today().strftime("%B %Y")

    # Using triple quotes (""") is the standard Python way for multi-line strings
    # and avoids parenthesis errors.
    system_message_template = """You are a sharp and organized financial assistant. Your goal is to create a clean financial summary from the user's expense data. The user prefers to see summaries on a weekly or monthly basis.

Follow these rules precisely:
1.  **Analyze the Date Range**: First, find the earliest and latest dates in the data.
2.  **Determine the Title**: Use the following logic to create the title:
    - If the dates span **more than 7 days**, the title must be `### Monthly Summary for {current_month_year}`.
    - If the dates span **between 2 and 7 days**, the title must be `### Weekly Summary`.
    - If **all expenses are on a single day**, the title must be `### This Week's Summary`.
3.  **List Category Totals**: After the title, create a clean, bulleted markdown list (using `-`). Each line should have a category and its total amount.
4.  **Add a Line Break**: After the bulleted list, you MUST include a blank line for separation.
5.  **State the Grand Total**: Conclude with the final total in bold.

---
**PERFECT OUTPUT EXAMPLE:**
### This Week's Summary
- Food: $75.50
- Travel: $120.00
- Entertainment: $45.00

**Total Spent: $240.50**
---"""

    # We format the template string to insert the current month and year
    system_message = system_message_template.format(current_month_year=current_month_year)

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            ("human", "Here is my expense data:\n\n{data}\n\nPlease provide the summary."),
        ]
    )

def categories_prompt(parser):
    return ChatPromptTemplate.from_template(template="""You are an expert at processing and extracting expense data from natural language text.
    Analyze the user's query and extract the expense amount, a clear description, and the most appropriate category from the provided list.
    Today's date is {date}.

    {format_instructions}

    User Query: {query}
    """,
    partial_variables={"format_instructions": parser.get_format_instructions()},
    
    )