from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource(show_spinner="Building vector database...")
def build_vector_store(documents):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.create_documents(
        [doc["content"] for doc in documents], 
        metadatas=documents
    )
    
    # Use Chroma (persistent in-memory for Streamlit)
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        collection_name="mitre_attack",
        persist_directory=None  # in-memory
    )
    return vectorstore

def get_rag_chain(vectorstore):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    
    template = """You are a senior cybersecurity analyst specializing in MITRE ATT&CK.
Use the following context to answer the user's question.

Context:
{context}

Question: {question}

Answer in this structured format:
- **Summary**: Brief overview
- **Relevant Techniques**: Bullet list with IDs, names, and short explanation
- **Tactics Involved**: List of tactics
- **Recommendations**: Defensive recommendations
- **Sources**: MITRE ATT&CK citations with links

Be precise, professional, and always include technique IDs.
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain, retriever
