import json
import os
import streamlit as st
from stix2 import MemoryStore, Filter

@st.cache_resource(show_spinner="Loading MITRE ATT&CK chunks...")
def load_attack_data():
    data_dir = "data"
    
    # Find all chunk files
    chunk_files = sorted([
        f for f in os.listdir(data_dir) 
        if f.startswith("chunk-") and f.endswith(".json")
    ])
    
    if not chunk_files:
        st.error("❌ No chunk files found in the 'data/' folder.\nMake sure your files are named chunk-1.json, chunk-2.json, ..., chunk-10.json")
        st.stop()
    
    st.info(f"Found {len(chunk_files)} chunk files. Loading data...")
    
    all_objects = []
    
    progress_bar = st.progress(0)
    
    for i, chunk_file in enumerate(chunk_files):
        chunk_path = os.path.join(data_dir, chunk_file)
        try:
            with open(chunk_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if isinstance(data, dict) and "objects" in data:
                    all_objects.extend(data["objects"])
                elif isinstance(data, list):
                    all_objects.extend(data)
                else:
                    all_objects.append(data)
                    
        except Exception as e:
            st.warning(f"⚠️ Failed to load {chunk_file}: {e}")
        
        # Update progress
        progress_bar.progress((i + 1) / len(chunk_files))
    
    progress_bar.empty()
    
    if not all_objects:
        st.error("❌ No valid objects could be loaded from chunks.")
        st.stop()
    
    st.success(f"✅ Successfully loaded {len(all_objects):,} objects from {len(chunk_files)} chunks.")
    
    # Build STIX MemoryStore
    ms = MemoryStore(stix_data=all_objects)
    
    # Get only techniques (attack-pattern)
    techniques = ms.query([Filter("type", "=", "attack-pattern")])
    
    documents = []
    for tech in techniques:
        try:
            ext_ref = tech.external_references[0] if tech.external_references else None
            technique_id = ext_ref.external_id if ext_ref else "N/A"
            
            tactics = []
            if hasattr(tech, 'kill_chain_phases'):
                tactics = [phase.phase_name.replace("-", " ").title() 
                          for phase in tech.kill_chain_phases]
            
            doc = {
                "id": str(tech.id),
                "technique_id": technique_id,
                "name": tech.name,
                "description": getattr(tech, 'description', ''),
                "tactics": tactics,
                "url": f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}/" if technique_id != "N/A" else ""
            }
            
            content = f"Technique: {doc['name']} ({doc['technique_id']})\n"
            content += f"Tactics: {', '.join(doc['tactics'])}\n"
            content += f"Description: {doc['description']}\n"
            
            doc["content"] = content
            documents.append(doc)
            
        except:
            continue
    
    st.info(f"✅ Extracted {len(documents):,} techniques ready for RAG.")
    
    return documents, ms
