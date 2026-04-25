import json
from stix2 import MemoryStore, Filter
import streamlit as st

@st.cache_resource
def load_attack_data():
    with open("data/enterprise-attack.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    ms = MemoryStore(stix_data=data["objects"])
    
    # Filter Techniques and Sub-techniques
    techniques = ms.query([
        Filter("type", "=", "attack-pattern")
    ])
    
    documents = []
    for tech in techniques:
        doc = {
            "id": tech.id,
            "technique_id": tech.external_references[0].external_id if tech.external_references else "N/A",
            "name": tech.name,
            "description": tech.description,
            "tactics": [tactic.name for tactic in tech.kill_chain_phases] if hasattr(tech, 'kill_chain_phases') else [],
            "url": f"https://attack.mitre.org/techniques/{tech.external_references[0].external_id.replace('.', '/')}/" if tech.external_references else ""
        }
        # Create rich text for embedding
        content = f"Technique: {doc['name']} ({doc['technique_id']})\n"
        content += f"Tactics: {', '.join(doc['tactics'])}\n"
        content += f"Description: {doc['description']}\n"
        doc["content"] = content
        documents.append(doc)
    
    return documents, ms
