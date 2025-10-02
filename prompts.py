from langchain_core.prompts import ChatPromptTemplate

def summary_prompt():
    return ChatPromptTemplate.from_messages(
       [
            (
                "system",
                "You are a sharp and organized financial assistant. Your main goal is to create a clean and simple financial summary from the user's expense data.\n\n"
                "Follow these steps:\n"
                "1.  **Analyze the Dates**: Look at the dates in the provided data to determine if it represents a week, a month, or another period.\n"
                "2.  **Create a Title**: Based on the dates, create a clear Markdown title like `### Weekly Summary` or `### Monthly Summary`.\n"
                "3.  **List Categories**: List each expense category with its total amount in a clean, bulleted list.\n"
                "4.  **State the Total**: Conclude with a clear statement showing the total amount spent for the entire period.\n\n"
                "Make the output neat and easy to read."
            ),
            ("human", "Here is my expense data:\n\n{data}\n\nPlease provide a neat summary."),
        ]
    )