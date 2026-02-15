import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re

# 1. Pagina configuratie
st.set_page_config(page_title="Indeed Job Analyzer PRO", layout="wide")

st.title("📋 Vacature-Analyzer (NL/EN)")
st.markdown("""
Dit dashboard analyseert vacatureteksten op basis van het **Job Demands-Resources (JD-R) model**. 
Het helpt bij het identificeren van psychologische factoren zoals werkdruk en beschikbare steun.
""")

# 2. Bestand uploaden
uploaded_file = 'dataset_indeed_2.csv'

if uploaded_file:
    # Inladen en direct opschonen van lege waarden om 'TypeError' te voorkomen
    df = pd.read_csv(uploaded_file)
    df = df.fillna("") # Vervangt alle NaN door een lege string
    
    st.success(f"Bestand geladen! {len(df)} vacatures gevonden.")

    # 3. Sidebar: Kolom Mapping
    st.sidebar.header("⚙️ Kolom Instellingen")
    col_options = df.columns.tolist()
    
    # Automatische detectie of handmatige selectie
    desc_col = st.sidebar.selectbox("Vacaturetekst (Description)", col_options, 
                                   index=col_options.index('description') if 'description' in col_options else 0)
    company_col = st.sidebar.selectbox("Bedrijfsnaam (Company)", col_options, 
                                      index=col_options.index('company') if 'company' in col_options else 0)
    rating_col = st.sidebar.selectbox("Bedrijfsrating", col_options, 
                                     index=col_options.index('companyInfo/rating') if 'companyInfo/rating' in col_options else 0)
    pos_col = st.sidebar.selectbox("Functietitel", col_options, 
                                  index=col_options.index('positionName') if 'positionName' in col_options else 0)

    # 4. Filters (Gecorrigeerd voor sorting error)
    # We zorgen dat we alleen unieke, niet-lege namen sorteren
    bedrijven = sorted([str(b) for b in df[company_col].unique() if b != ""])
    
    if bedrijven:
        geselecteerd_bedrijf = st.multiselect(
            "Selecteer één of meerdere bedrijven:", 
            options=bedrijven, 
            default=[bedrijven[0]]
        )
        
        df_filtered = df[df[company_col].isin(geselecteerd_bedrijf)]
    else:
        st.error("Geen bedrijfsnamen gevonden.")
        st.stop()

    # 5. Psychologische Analyse: NL + EN Termen (JD-R Model)
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚖️ Job Demands (Eisen)")
        # Woordgroepen voor eisen (Rood)
        demands = {
            'Werkdruk/Stress': ['stress', 'druk', 'pressure', 'deadlines', 'tempo', 'pace', 'targets'],
            'Flexibiliteit': ['flexibel', 'flexible', 'no 9-to-5', 'geen 9-tot-5', 'avonden', 'weekends', 'shift'],
            'Complexiteit': ['dynamisch', 'dynamic', 'fast-paced', 'uitdagend', 'challenging', 'complex']
        }
        
        d_results = {}
        for label, keywords in demands.items():
            pattern = '|'.join(keywords)
            # We tellen in hoeveel vacatures minstens één van de woorden voorkomt
            count = df_filtered[desc_col].str.contains(pattern, case=False, na=False).sum()
            d_results[label] = count
            
        fig_demands = px.bar(x=list(d_results.keys()), y=list(d_results.values()), 
                             labels={'x': 'Type Eis', 'y': 'Aantal vacatures'},
                             color_discrete_sequence=['#E74C3C'], title="Gevonden 'Demands'")
        st.plotly_chart(fig_demands, use_container_width=True)

    with col2:
        st.subheader("🌱 Job Resources (Steun)")
        # Woordgroepen voor resources (Groen)
        resources = {
            'Ontwikkeling': ['opleiding', 'training', 'development', 'ontwikkeling', 'coaching', 'learning', 'groei'],
            'Balans': ['balans', 'balance', 'thuiswerk', 'remote', 'home office', 'flex-time', 'glijdende'],
            'Ondersteuning': ['team', 'sfeer', 'vrijheid', 'freedom', 'autonomie', 'autonomy', 'collega', 'support']
        }
        
        r_results = {}
        for label, keywords in resources.items():
            pattern = '|'.join(keywords)
            count = df_filtered[desc_col].str.contains(pattern, case=False, na=False).sum()
            r_results[label] = count
            
        fig_res = px.bar(x=list(r_results.keys()), y=list(r_results.values()), 
                         labels={'x': 'Type Steun', 'y': 'Aantal vacatures'},
                         color_discrete_sequence=['#27AE60'], title="Gevonden 'Resources'")
        st.plotly_chart(fig_res, use_container_width=True)

    # 6. Top Keywords Analyse (Bilinguale 'Wordcloud' vervanger)
    st.divider()
    st.subheader(f"🔤 Meest gebruikte termen")
    
    # Tekst samenvoegen en opschonen
    combined_text = " ".join(df_filtered[desc_col].astype(str)).lower()
    all_words = re.findall(r'\w+', combined_text)
    
    # Stopwoorden filter (NL + EN)
    stop_words = set([
        'en', 'de', 'het', 'een', 'voor', 'met', 'van', 'is', 'op', 'te', 'worden', 'we', 'are', 
        'with', 'for', 'you', 'will', 'your', 'that', 'this', 'have', 'been', 'over', 'niet', 'aan'
    ])
    
    # Alleen woorden langer dan 4 letters die niet in stopwoordenlijst staan
    meaningful_words = [w for w in all_words if len(w) > 4 and w not in stop_words]
    
    word_counts = Counter(meaningful_words).most_common(15)
    
    if word_counts:
        word_df = pd.DataFrame(word_counts, columns=['Woord', 'Frequentie'])
        fig_word_freq = px.bar(word_df, x='Frequentie', y='Woord', orientation='h', 
                               color='Frequentie', color_continuous_scale='Viridis')
        fig_word_freq.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_word_freq, use_container_width=True)
    else:
        st.info("Niet genoeg tekst gevonden voor een trefwoorden-analyse.")

    # 7. Detail Overzicht
    with st.expander("📝 Bekijk de volledige vacatureteksten"):
        st.dataframe(df_filtered[[company_col, pos_col, desc_col]])

else:
    st.info("Upload je vacatures-CSV (Indeed export) om de analyse te starten.")
    # Voorbeeld voor portfolio
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/JD-R_Model.png/640px-JD-R_Model.png", caption="Het Job Demands-Resources model als basis voor deze analyse.")