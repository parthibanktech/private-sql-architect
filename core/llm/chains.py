import chainlit as cl
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from operator import itemgetter
import os

from core.llm.prompts import QA_PROMPT, ROUTE_PROMPT, CHAT_PROMPT

async def update_chain(dialect="SQLite", model="qwen2.5-coder:7b", kb_mode="Standard"):
    if model == "gpt-4o-mini":
        llm = ChatOpenAI(model="gpt-4o-mini")
    else:
        llm = ChatOllama(model=model)

    retriever = cl.user_session.get("retriever")

    intent_chain = (
        PromptTemplate.from_template(ROUTE_PROMPT)
        | llm
        | StrOutputParser()
    )
    cl.user_session.set("intent_chain", intent_chain)

    chat_chain = (
        PromptTemplate.from_template(CHAT_PROMPT)
        | llm
        | StrOutputParser()
    )
    cl.user_session.set("chat_chain", chat_chain)

    qa_prompt = PromptTemplate.from_template(
        QA_PROMPT + f"\n\nGenerate SQL for this Dialect: {dialect}."
    )
    
    def format_docs(docs):
        if not docs: return "No schema context available."
        return "\n\n".join(doc.page_content for doc in docs)

    def extract_context(inputs):
        return inputs["context"]

    if retriever:
        rag_chain = (
            {"context": itemgetter("question") | retriever | format_docs, "question": itemgetter("question"), "history": itemgetter("history")}
            | qa_prompt
            | llm
            | StrOutputParser()
        )
    else:
        rag_chain = (
            {"context": lambda x: "", "question": itemgetter("question"), "history": itemgetter("history")}
            | qa_prompt
            | llm
            | StrOutputParser()
        )
    
    cl.user_session.set("rag_chain", rag_chain)
    cl.user_session.set("current_dialect", dialect)
