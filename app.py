import streamlit as st
import pandas as pd
import os

# Mobilvänlig layout och titel
st.set_page_config(page_title="TCF Analyzer v2", layout="centered")

st.title("🧬 The Campbell Formula (TCF)")
st.subheader("Matchanalys & Säsongshistorik | Nacka IBK (Vit)")

# --- FILHANTERING FÖR HISTORIK ---
# En enkel CSV-fil lagrar matcherna lokalt i appen
DB_FILE = "tcf_history.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Match", "Mål_Nacka", "xG_Nacka", "xA_Nacka", "xT_Nacka", "Skott_Nacka", "Slot_Comp", "HDC"])

def save_match(match_name, mål, xg, xa, xt, skott, sc, hdc):
    df = load_data()
    # Undvik dubbletter av samma matchnamn
    if match_name in df["Match"].values:
        df = df[df["Match"] != match_name]
    
    new_row = pd.DataFrame([{
        "Match": match_name, "Mål_Nacka": mål, "xG_Nacka": xg, 
        "xA_Nacka": xa, "xT_Nacka": xt, "Skott_Nacka": skott, 
        "Slot_Comp": sc, "HDC": hdc
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- APPENS STRUKTUR ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Lagstats", "🏃‍♂️ Positionsstats", "📋 Rapport", "📈 Säsongssnitt"])

with tab1:
    st.header("Lagets KPI:er (Bänken)")
    match_title = st.text_input("Matchnamn (t.ex. 'Mora hemma')", "Seriematch 1")
    
    nacka_goals = st.number_input("Faktiska Mål (Nacka)", min_value=0, value=2, step=1)
    nacka_skott = st.number_input("Skott på mål (Nacka)", min_value=0, value=22, step=1)
    slot_completions = st.slider("Lyckade Slot Completions", 0, 40, 14)
    hdc_chances = st.slider("Antal HDC (Slottet/Royal Pass)", 0, 30, 11)
    
    st.markdown("---")
    st.header("🔵 Motståndarna")
    opp_goals = st.number_input("Faktiska Mål (Motståndare)", min_value=0, value=1, step=1)
    opp_skott = st.number_input("Skott på mål (Motståndare)", min_value=0, value=19, step=1)
    opp_slot_completions = st.slider("Motståndarnas Slot Completions", 0, 40, 22)

with tab2:
    st.header("Positionsdata (Nacka Vita)")
    positions = ["Centrar", "Vänsterforwards", "Högerforwards", "Vänsterbackar", "Högerbackar"]
    pos_data = {}
    
    for pos in positions:
        st.markdown(f"### {pos}")
        p_mål = st.number_input(f"Mål - {pos}", min_value=0, value=0, key=f"{pos}_m")
        p_skott = st.number_input(f"Skott på mål - {pos}", min_value=0, value=0, key=f"{pos}_s")
        p_pass = st.number_input(f"Slottspass (A) - {pos}", min_value=0, value=0, key=f"{pos}_p")
        
        pos_data[pos] = {"Mål": p_mål, "xG": round((p_mål * 0.40) + (p_skott * 0.08), 2), "Assist": p_pass, "xA": round(p_pass * 0.15, 2), "xT": round((p_skott * 0.03) + (p_pass * 0.05), 2)}

# Beräkna TCF-värden live
nacka_xG = round((hdc_chances * 0.20) + ((nacka_skott - hdc_chances) * 0.035), 2)
nacka_xA = round(slot_completions * 0.13, 2)
nacka_xT = round((nacka_skott * 0.05) + (slot_completions * 0.06), 2)
opp_xG = round((opp_slot_completions * 0.10) + (opp_skott * 0.02), 2)

with tab3:
    st.header("📋 TCF Matchrapport")
    
    st.markdown("### 📊 STATISTISK JÄMFÖRELSE")
    st.table({
        "Lag": ["Nacka IBK (Vit)", "Motståndarna"],
        "Mål": [nacka_goals, opp_goals],
        "Totalt xG": [nacka_xG, opp_xG],
        "Skott": [nacka_skott, opp_skott]
    })
    
    # KNAPP FÖR ATT SPARA MATCHEN DIREKT FRÅN MOBILEN
    if st.button("💾 Spara match i TCF-historiken", type="primary"):
        save_match(match_title, nacka_goals, nacka_xG, nacka_xA, nacka_xT, nacka_skott, slot_completions, hdc_chances)
        st.success(f"Matchen '{match_title}' har sparats i databasen!")

with tab4:
    st.header("📈 TCF Säsongssnitt & Historik")
    history_df = load_data()
    
    if not history_df.empty:
        # Räkna ut snitt på nyckel-metrics
        snitt_xG = round(history_df["xG_Nacka"].mean(), 2)
        snitt_mål = round(history_df["Mål_Nacka"].mean(), 1)
        snitt_sc = round(history_df["Slot_Comp"].mean(), 1)
        snitt_hdc = round(history_df["HDC"].mean(), 1)
        
        # Visa coola widgetar med snitt
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Vårt snitt xG (Mål: 5.0+)", f"{snitt_xG} xG", delta=round(snitt_xG - 5.0, 2))
            st.metric("Snitt Slot Completions (Mål: 20+)", f"{snitt_sc} st", delta=round(snitt_sc - 20, 1))
        with col2:
            st.metric("Snitt Faktiska Mål", f"{snitt_mål} mål")
            st.metric("Snitt HDC i Slottet (Mål: 15+)", f"{snitt_hdc} st", delta=round(snitt_hdc - 15, 1))
            
        st.markdown("---")
        st.subheader("🗂️ Sparade matcher denna säsong")
        st.dataframe(history_df.set_index("Match"))
        
        if st.button("🗑️ Nollställ all historik"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.experimental_rerun()
    else:
        st.info("Inga matcher sparade ännu. Gå till fliken '📋 TCF Matchrapport' och klicka på sparaknappen efter en match!")
      
