import streamlit as st
from src.data_loader import load_attack_data
from src.rag_pipeline import build_vector_store, get_rag_chain
from src.visualization import create_attack_heatmap
import time

st.set_page_config(
    page_title="MITRE ATT&CK AI Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .chat-message { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ MITRE ATT&CK AI Cybersecurity Assistant")
st.markdown("**Retrieval-Augmented Generation** powered by MITRE ATT&CK Enterprise Matrix")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    st.divider()
    st.subheader("Example Questions")
    examples = [
        "How do adversaries perform credential dumping?",
        "What techniques are used in initial access via phishing?",
        "Explain Defense Evasion tactics and common techniques",
        "How to detect process injection (T1055)?",
        "What are the most common tactics in ransomware attacks?"
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.query = ex

    if st.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vectorstore" not in st.session_state:
    with st.spinner("Loading MITRE ATT&CK dataset and building vector store... (first run may take 30-60s)"):
        documents, _ = load_attack_data()
        st.session_state.vectorstore = build_vector_store(documents)
        st.session_state.documents = documents

# Main Chat Area
col1, col2 = st.columns([2, 1])

with col1:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask about any MITRE ATT&CK technique or tactic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving relevant techniques and generating response..."):
                rag_chain, retriever = get_rag_chain(st.session_state.vectorstore)
                
                # Retrieve for visualization
                retrieved_docs = retriever.invoke(prompt)
                
                # Generate answer
                response = rag_chain.invoke(prompt)
                
                st.markdown(response)
                
                # Show heatmap below answer
                st.divider()
                st.subheader("Relevant Techniques Heatmap")
                heatmap_fig = create_attack_heatmap(retrieved_docs)
                if heatmap_fig:
                    st.plotly_chart(heatmap_fig, use_container_width=True)
                else:
                    st.info("No strong matches for heatmap visualization.")
                
                # Store in history
                st.session_state.messages.append({"role": "assistant", "content": response})

with col2:
    st.subheader("How it Works")
    st.markdown("""
    1. **RAG Pipeline**: MITRE ATT&CK techniques are embedded using OpenAI embeddings.
    2. **Retrieval**: Top relevant techniques are fetched via semantic search (FAISS).
    3. **Generation**: GPT-4o-mini generates structured, cited answers.
    4. **Visualization**: Interactive heatmap highlights tactics vs techniques by relevance.
    """)
    
    st.caption("Built for SOC analysts, red teamers, and cybersecurity enthusiasts.")

# Footer
st.caption("MITRE ATT&CK® is a registered trademark of The MITRE Corporation. Data sourced from official STIX bundles.")
