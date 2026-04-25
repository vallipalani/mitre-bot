import pandas as pd
import plotly.express as px
import streamlit as st

def create_attack_heatmap(relevant_docs):
    if not relevant_docs:
        return None
    
    # Extract tactics and techniques with scores
    tactics = []
    techniques = []
    scores = []
    tech_ids = []
    names = []
    
    for i, doc in enumerate(relevant_docs[:15]):  # Limit for readability
        meta = doc.metadata
        for tactic in meta.get("tactics", ["Unknown"]):
            tactics.append(tactic)
            techniques.append(meta.get("technique_id", "N/A"))
            names.append(meta.get("name", "Unknown"))
            scores.append(1.0 - (i * 0.05))  # Simulated relevance decay
            tech_ids.append(meta.get("technique_id", "N/A"))
    
    if not tactics:
        return None
    
    df = pd.DataFrame({
        "Tactic": tactics,
        "Technique": techniques,
        "Relevance": scores,
        "Name": names,
        "ID": tech_ids
    })
    
    # Pivot for heatmap
    pivot_df = df.pivot_table(index="Technique", columns="Tactic", values="Relevance", fill_value=0)
    
    fig = px.imshow(
        pivot_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdYlBu_r",
        title="MITRE ATT&CK Relevance Heatmap"
    )
    
    fig.update_traces(
        hovertemplate="<b>Technique:</b> %{y}<br>" +
                      "<b>Tactic:</b> %{x}<br>" +
                      "<b>Relevance:</b> %{z:.2f}<br>" +
                      "<b>Name:</b> %{customdata[0]}",
        customdata=df[["Name"]].values.reshape(-1, 1)  # Simplified
    )
    
    fig.update_layout(
        height=600,
        xaxis_title="Tactics",
        yaxis_title="Techniques",
        coloraxis_colorbar_title="Relevance Score"
    )
    
    return fig
