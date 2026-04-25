import json
import os
import streamlit as st
from stix2 import MemoryStore, Filter

@st.cache_resource(show_spinner="Loading MITRE ATT&CK chunks and building vector store...")
def load_attack_data():
    data_dir = "data"
    
    # Find all chunk files
    chunk_files = sorted([
        f for f in os.listdir(data_dir) 
        if f.startswith("chunk-") and f.endswith(".json")
    ])
    
    if not chunk_files:
        st.error("❌ No chunk files found in the 'data/' folder. Please make sure your files are named chunk-1.json, chunk-2.json, etc.")
        st.stop()
    
    st.info(f"Found {len(chunk_files)} chunk files. Loading MITRE ATT&CK data...")
    
    all_objects = []
    
    for chunk_file in chunk_files:
        chunk_path = os.path.join(data_dir, chunk_file)
        try:
            with open(chunk_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if isinstance(data, dict) and "objects" in data:
                    all_objects.extend(data["objects"])
                elif isinstance(data, list):
                    all_objects.extend(data)
                else:
                    # If it's a single object
                    all_objects.append(data)
                    
        except Exception as e:
            st.warning(f"⚠️ Could not load {chunk_file}: {e}")
            continue
    
    if not all_objects:
        st.error("❌ No valid objects found in any chunk files.")
        st.stop()
    
    st.success(f"✅ Loaded {len(all_objects):,} MITRE ATT&CK objects from {len(chunk_files)} chunks.")
    
    # Create STIX MemoryStore
    bundle = {
        "type": "bundle",
        "id": "bundle--merged-from-chunks",
        "objects": all_objects
    }
    
    ms = MemoryStore(stix_data=all_objects)
    
    # Extract techniques (attack-patterns)
    techniques = ms.query([Filter("type", "=", "attack-pattern")])
    
    documents = []
    for tech in techniques:
        try:
            ext_id = tech.external_references[0].external_id if tech.external_references else "N/A"
            tactics = [phase.phase_name.replace("-", " ").title() for phase in tech.kill_chain_phases] if hasattr(tech, 'kill_chain_phases') else []
            
            doc = {
                "id": tech.id,
                "technique_id": ext_id,
                "name": tech.name,
                "description": tech.description if hasattr(tech, 'description') else "",
                "tactics": tactics,
                "url": f"https://attack.mitre.org/techniques/{ext_id.replace('.', '/')}/" if ext_id != "N/A" else ""
            }
            
            # Rich content for embedding
            content = f"Technique: {doc['name']} ({doc['technique_id']})\n"
            content += f"Tactics: {', '.join(doc['tactics'])}\n"
            content += f"Description: {doc['description']}\n"
            doc["content"] = content
            
            documents.append(doc)
            
        except Exception:
            continue  # Skip problematic techniques
    
    st.info(f"Extracted {len(documents):,} techniques for RAG.")
    
    return documents, ms
