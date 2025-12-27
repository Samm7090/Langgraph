from urllib import response
from dotenv import load_dotenv
load_dotenv()

#---Define llm
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0
)

#-- Response cleaning
import re

def remove_think_blocks(text: str) -> str:
    # Remove <think>...</think> including multiline
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


#---Generate mail automatically throught llm

# from langchain_core.tools import tool

# @tool
# def generate_email_body(purpose:str) -> str:
#     """Generate an email body based on the given purpose."""

#     prompt=f""" write a professional and humble email for the following purpose: {purpose} Tone: Humble and Polite
#                 IMPORTANT:
#                 - Do NOT include explanations
#                 - Do NOT include reasoning
#                 - Do NOT include <tool_call> tags
#                 - Output ONLY the final email text"""

#     response=llm.invoke(prompt)
#     clean_text = remove_think_blocks(response.content)
#     return clean_text



#tools

from langchain_core.tools import tool

@tool
def draft_email(to: str, subject:str, body:str) -> str:
    """Draft an email."""
    return f"To: {to}\nSubject: {subject}\n\n{body}:"


from dotenv import load_dotenv
import os

load_dotenv()

@tool
def send_gmail(to: str, subject: str, body: str) -> str:
    """
    Send email using Gmail SMTP
    """
    import smtplib
    from email.mime.text import MIMEText

    sender = "sammedh8nale@gmail.com"
    password = os.getenv("APP_PASSWORD")  # Gmail App Password

    msg = MIMEText(body)
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

    return "Email sent successfully"

#---List of tools
tools=[draft_email, send_gmail]



#---Combine tools with llm
llm_with_tools=llm.bind_tools(tools=tools)

#---Workflow
# State Schema
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from typing import Annotated
from langgraph.graph.message import add_messages

class EmailStateSchema(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

from IPython.display import display, Image
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

#Node Definition
from langchain_core.messages import AIMessage

def tool_calling_llm(state: EmailStateSchema):
    response=llm_with_tools.invoke(state['messages'])

    clean = remove_think_blocks(response.content)

    new_response = AIMessage(
        content=clean,
        tool_calls=response.tool_calls,
        additional_kwargs=response.additional_kwargs
    )

    return {"messages": [new_response]}


# Human inloop

    
# from langchain_core.messages import AIMessage

# def confirm_node(state: EmailStateSchema):
#     email_text = state["messages"][-1].content
#     return {
#         "messages": [
#             AIMessage(
#                 content=f"""
#     Please confirm before sending email:

# {email_text}

# Reply YES to send or NO to cancel.
# """
#             )
#         ]
#     }

# Build Graph

builder= StateGraph(EmailStateSchema)


builder.add_node("llm", tool_calling_llm)
builder.add_node("tools", ToolNode(tools))
# builder.add_node("confirm", confirm_node)

# Edges



builder.add_edge(START, "llm")
builder.add_conditional_edges("llm",tools_condition,{"tools":"tools", END:END})
# builder.add_edge("tools", "confirm")
# builder.add_edge("confirm", END)
builder.add_edge("tools", END)

# Compile Graph
graph=builder.compile()

# Visualize Graph
# display(Image(graph.get_graph().draw_mermaid_png()))

from langchain_core.messages import HumanMessage

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="draft a email as let's have a call am tomorrow morning 7am to mukhtar.shaikh3108@gmail.com  that and mention at the end of mail that this ai generated email on new line"
            )
        ]
    }
)

print(result["messages"][-1].content)


#-- Function to extract subject and body

import re

def extract_subject_and_body(text):
    match = re.search(r"Subject:\s*(.*)", text)
    subject = match.group(1).strip() if match else "No Subject"

    # body = everything after the first blank line
    parts = text.split("\n\n", 1)
    body = parts[1] if len(parts) > 1 else text

    return subject, body

#-- User Confirmation and Send Email
user_reply = input("Type YES or NO: ").strip().lower()  # simulate input

if user_reply.lower() == "yes":
    
    #call extract function
    subject, body = extract_subject_and_body(result["messages"][-2].content)
    
    send_result = send_gmail.invoke({
        "to": "sammedh.cs19101@mmcc.edu.in",
        "subject": subject,
        "body": body
    })
    print(send_result)
else:
    print("Email cancelled")
