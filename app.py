import streamlit as st
import json
import requests
import time
import plotly.graph_objects as go
import pandas as pd

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ComparaVilles",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS minimal
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    h1 { font-size: 2rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; padding: 0.5rem 1.2rem; }
    div[data-testid="metric-container"] { background:#FEFCF8; border:1px solid #E0DAD0;
        border-radius:8px; padding:0.6rem 1rem; }
    .source-note { font-size:0.72rem; color:#999; margin-top:0.5rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# DONNÉES
# ─────────────────────────────────────────────────────────────
@st.cache_data
def load_cities():
    with open("data/cities_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

cities      = load_cities()
city_index  = {c["name"]: c for c in cities}
names       = sorted(city_index.keys())

# ─────────────────────────────────────────────────────────────
# EN-TÊTE
# ─────────────────────────────────────────────────────────────
st.title("🏙️ ComparaVilles")
st.caption("Comparateur de villes françaises (+20 000 hab.) · Données INSEE Filosofi 2021 · SAE Outils Décisionnels")
st.divider()

# ─────────────────────────────────────────────────────────────
# SÉLECTION DES VILLES
# ─────────────────────────────────────────────────────────────
col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    name_a = st.selectbox("🔴 Ville A", names, index=names.index("Lyon") if "Lyon" in names else 0)
with col_sel2:
    other  = [n for n in names if n != name_a]
    name_b = st.selectbox("🔵 Ville B", other, index=other.index("Bordeaux") if "Bordeaux" in other else 0)

ca = city_index[name_a]
cb = city_index[name_b]
COLOR_A = "#C85A1E"
COLOR_B = "#1B5EA0"

st.divider()

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def fmt_pop(n):
    if n >= 1_000_000: return f"{n/1_000_000:.2f} M"
    if n >= 1_000:     return f"{n/1_000:.0f} k"
    return str(n)

def fmt_eur(v):
    if v is None: return "—"
    return f"{int(v):,} €".replace(",", " ")

def val(city, key):
    return city.get(key)

def bar_chart(title, labels, vals_a, vals_b, unit="", note=""):
    """Graphique barres côte à côte Plotly."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name=name_a, x=labels, y=vals_a,
                         marker_color=COLOR_A, text=[f"{v}{unit}" if v else "—" for v in vals_a],
                         textposition="outside"))
    fig.add_trace(go.Bar(name=name_b, x=labels, y=vals_b,
                         marker_color=COLOR_B, text=[f"{v}{unit}" if v else "—" for v in vals_b],
                         textposition="outside"))
    fig.update_layout(
        title=title, barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=40, r=20),
        yaxis_title=unit, plot_bgcolor="#FEFCF8", paper_bgcolor="#FEFCF8",
        height=350,
    )
    if note:
        fig.add_annotation(text=note, xref="paper", yref="paper", x=0, y=-0.12,
                           showarrow=False, font=dict(size=10, color="#999"), align="left")
    return fig

def horiz_compare(label, va, vb, unit="", lower_is_better=False, fmt_fn=None):
    """Ligne de comparaison horizontale avec barres proportionnelles."""
    if va is None and vb is None:
        return
    va = va or 0; vb = vb or 0
    max_val = max(va, vb) or 1
    pct_a = va / max_val * 100
    pct_b = vb / max_val * 100
    win_a = (va <= vb) if lower_is_better else (va >= vb)
    color_a_win = COLOR_A if (win_a and va != vb) else "#999"
    color_b_win = COLOR_B if (not win_a and va != vb) else "#999"
    fw_a = "bold" if (win_a and va != vb) else "normal"
    fw_b = "bold" if (not win_a and va != vb) else "normal"
    disp_a = fmt_fn(va) if fmt_fn else f"{va}{unit}"
    disp_b = fmt_fn(vb) if fmt_fn else f"{vb}{unit}"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #EAE6DF">
      <div style="width:180px;font-size:.88rem;color:#666">{label}</div>
      <div style="flex:1">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
          <div style="flex:1;height:6px;background:#EAE6DF;border-radius:3px;overflow:hidden">
            <div style="width:{pct_a:.0f}%;height:100%;background:{COLOR_A};border-radius:3px"></div>
          </div>
          <div style="width:100px;text-align:right;font-size:.82rem;color:{color_a_win};font-weight:{fw_a}">{disp_a}</div>
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <div style="flex:1;height:6px;background:#EAE6DF;border-radius:3px;overflow:hidden">
            <div style="width:{pct_b:.0f}%;height:100%;background:{COLOR_B};border-radius:3px"></div>
          </div>
          <div style="width:100px;text-align:right;font-size:.82rem;color:{color_b_win};font-weight:{fw_b}">{disp_b}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ONGLETS
# ─────────────────────────────────────────────────────────────
tab_gen, tab_emp, tab_rev, tab_met = st.tabs(
    ["📊 Général", "💼 Emploi", "💰 Revenus", "🌤️ Météo"]
)

# ══════════════════════════════════════════════════════════════
# ONGLET 1 — GÉNÉRAL
# ══════════════════════════════════════════════════════════════
with tab_gen:
    # Cartes héros
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### 🔴 {ca['name']}")
        st.caption(f"{ca['dep_name']} · {ca['region']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Population", fmt_pop(ca["pop"]))
        m2.metric("Revenu médian/UC", fmt_eur(val(ca,"rev_med")))
        m3.metric("Gini", f"{val(ca,'gini'):.3f}" if val(ca,"gini") else "—")
    with c2:
        st.markdown(f"#### 🔵 {cb['name']}")
        st.caption(f"{cb['dep_name']} · {cb['region']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Population", fmt_pop(cb["pop"]))
        m2.metric("Revenu médian/UC", fmt_eur(val(cb,"rev_med")))
        m3.metric("Gini", f"{val(cb,'gini'):.3f}" if val(cb,"gini") else "—")

    # Explication Gini
    with st.expander("ℹ️ Comprendre le coefficient de Gini"):
        st.markdown("""
        Le **coefficient de Gini** mesure les **inégalités de revenus** dans une ville.

        | Valeur | Interprétation |
        |--------|---------------|
        | **< 0.35** | Faibles inégalités (villes ouvrières, revenus homogènes) |
        | **0.35 – 0.45** | Inégalités modérées (villes françaises moyennes) |
        | **> 0.45** | Fortes inégalités (grandes métropoles : Paris 0.53, Lyon 0.42) |

        Plus le coefficient est **élevé**, plus les écarts de revenus entre les habitants sont importants.
        """)

    st.divider()

    # Graphique population
    fig_pop = go.Figure(go.Bar(
        x=[ca["name"], cb["name"]],
        y=[ca["pop"], cb["pop"]],
        marker_color=[COLOR_A, COLOR_B],
        text=[fmt_pop(ca["pop"]), fmt_pop(cb["pop"])],
        textposition="outside",
    ))
    fig_pop.update_layout(
        title="Population comparée", showlegend=False,
        yaxis_title="Habitants", plot_bgcolor="#FEFCF8", paper_bgcolor="#FEFCF8",
        margin=dict(t=50, b=30), height=320,
    )
    st.plotly_chart(fig_pop, use_container_width=True)

    # Comparaison barres
    st.subheader("Comparaison des indicateurs")
    horiz_compare("Population", ca["pop"], cb["pop"], fmt_fn=lambda v: f"{v:,}".replace(",", " "))
    horiz_compare("Revenu médian (€/UC/an)", val(ca,"rev_med"), val(cb,"rev_med"),
                  fmt_fn=fmt_eur)
    horiz_compare("1er quartile (Q1)", val(ca,"rev_q1"), val(cb,"rev_q1"), fmt_fn=fmt_eur)
    horiz_compare("3e quartile (Q3)", val(ca,"rev_q3"), val(cb,"rev_q3"), fmt_fn=fmt_eur)
    horiz_compare("Gini (↓ = moins d'inégalités)", val(ca,"gini"), val(cb,"gini"),
                  lower_is_better=True, fmt_fn=lambda v: f"{v:.3f}")
    horiz_compare("Rapport S80/S20 (↓ = moins d'inégalités)", val(ca,"s80s20"), val(cb,"s80s20"),
                  lower_is_better=True, fmt_fn=lambda v: f"{v:.1f}x")

    st.markdown('<p class="source-note">Sources : INSEE — Recensement 2021, Filosofi 2021 (revenus fiscaux localisés par commune)</p>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ONGLET 2 — EMPLOI
# ══════════════════════════════════════════════════════════════
with tab_emp:
    st.info("""
    **Note de lecture** : les indicateurs ci-dessous sont issus du fichier Filosofi (INSEE 2021).
    Ils représentent la **part de chaque type de revenu dans le revenu fiscal de référence total** des ménages,
    et non des taux d'emploi ou de chômage au sens du BIT.
    """)

    with st.expander("ℹ️ Pourquoi les salaires ne représentent que ~60 % ?"):
        st.markdown("""
        Le revenu fiscal de référence d'un ménage se compose de **plusieurs sources** :

        - 🏢 **Salaires et traitements** (~55–70 % selon les villes) — revenus du travail salarié
        - 👴 **Pensions et retraites** (~20–30 %) — revenus des retraités (part importante dans les villes âgées)
        - 📉 **Allocations chômage** (~2–5 %) — indemnités chômage perçues par les ménages
        - 💼 **Revenus d'indépendants** (~5–10 %) — BNC, BIC, etc.
        - 🏠 **Revenus du patrimoine** (~5 %) — loyers, dividendes, intérêts

        Ainsi, même dans une ville dynamique, les salaires ne représentent qu'une fraction du revenu total
        parce qu'une partie significative de la population est retraitée, indépendante ou propriétaire.
        """)

    c1, c2 = st.columns(2)
    with c1:
        fig_cho = bar_chart(
            "Poids des allocations chômage dans les revenus des ménages (%)",
            [ca["name"], cb["name"]],
            [val(ca,"pcho")], [val(cb,"pcho")],
            unit=" %",
            note="% des allocations chômage dans le revenu fiscal de référence (source : INSEE Filosofi 2021)"
        )
        # Recréer avec 1 seul groupe par ville
        fig_cho = go.Figure()
        fig_cho.add_trace(go.Bar(name=ca["name"], x=[ca["name"]], y=[val(ca,"pcho")],
                                  marker_color=COLOR_A,
                                  text=[f"{val(ca,'pcho')} %" if val(ca,'pcho') else "—"],
                                  textposition="outside"))
        fig_cho.add_trace(go.Bar(name=cb["name"], x=[cb["name"]], y=[val(cb,"pcho")],
                                  marker_color=COLOR_B,
                                  text=[f"{val(cb,'pcho')} %" if val(cb,'pcho') else "—"],
                                  textposition="outside"))
        fig_cho.update_layout(title="Part allocations chômage dans le revenu total",
                               showlegend=False, yaxis_title="% du revenu fiscal",
                               plot_bgcolor="#FEFCF8", paper_bgcolor="#FEFCF8",
                               height=320, margin=dict(t=60,b=30))
        st.plotly_chart(fig_cho, use_container_width=True)

    with c2:
        fig_tsa = go.Figure()
        fig_tsa.add_trace(go.Bar(name=ca["name"], x=[ca["name"]], y=[val(ca,"ptsa")],
                                  marker_color=COLOR_A,
                                  text=[f"{val(ca,'ptsa')} %" if val(ca,'ptsa') else "—"],
                                  textposition="outside"))
        fig_tsa.add_trace(go.Bar(name=cb["name"], x=[cb["name"]], y=[val(cb,"ptsa")],
                                  marker_color=COLOR_B,
                                  text=[f"{val(cb,'ptsa')} %" if val(cb,'ptsa') else "—"],
                                  textposition="outside"))
        fig_tsa.update_layout(title="Poids des salaires dans les revenus des ménages (%)",
                               showlegend=False, yaxis_title="% du revenu fiscal",
                               plot_bgcolor="#FEFCF8", paper_bgcolor="#FEFCF8",
                               height=320, margin=dict(t=60,b=30))
        st.plotly_chart(fig_tsa, use_container_width=True)

    st.divider()
    st.subheader("Composition des revenus — comparaison détaillée")

    horiz_compare("% foyers avec rev. d'activité",
                  val(ca,"pact"), val(cb,"pact"), fmt_fn=lambda v: f"{v:.1f} %")
    horiz_compare("Part salaires et traitements",
                  val(ca,"ptsa"), val(cb,"ptsa"), fmt_fn=lambda v: f"{v:.1f} %")
    horiz_compare("Part alloc. chômage (↓ = moins de chômage)",
                  val(ca,"pcho"), val(cb,"pcho"),
                  lower_is_better=True, fmt_fn=lambda v: f"{v:.1f} %")
    horiz_compare("Part pensions et retraites",
                  val(ca,"pben"), val(cb,"pben"), fmt_fn=lambda v: f"{v:.1f} %")

    # Graphique radar structure
    st.divider()
    cats = ["Salaires", "Activité", "Moins chômage", "Moins retraites", "Revenus", "Égalité"]
    max_tsa  = max(val(ca,"ptsa") or 0, val(cb,"ptsa") or 0) or 1
    max_act  = max(val(ca,"pact") or 0, val(cb,"pact") or 0) or 1
    max_cho  = max(val(ca,"pcho") or 0, val(cb,"pcho") or 0) or 1
    max_ben  = max(val(ca,"pben") or 0, val(cb,"pben") or 0) or 1
    max_rev  = max(val(ca,"rev_med") or 0, val(cb,"rev_med") or 0) or 1
    max_gini = max(val(ca,"gini") or 0, val(cb,"gini") or 0) or 1

    def radar_vals(c):
        return [
            (val(c,"ptsa") or 0) / max_tsa * 100,
            (val(c,"pact") or 0) / max_act * 100,
            100 - (val(c,"pcho") or 0) / max_cho * 100,
            100 - (val(c,"pben") or 0) / max_ben * 100,
            (val(c,"rev_med") or 0) / max_rev * 100,
            100 - (val(c,"gini") or 0) / max_gini * 100,
        ]

    fig_radar = go.Figure()
    for city, color, rvals in [(ca, COLOR_A, radar_vals(ca)), (cb, COLOR_B, radar_vals(cb))]:
        fig_radar.add_trace(go.Scatterpolar(
            r=rvals + [rvals[0]], theta=cats + [cats[0]],
            fill="toself", name=city["name"],
            line_color=color,
            fillcolor=color.replace("#", "rgba(").replace("C8","200,").replace("5A","90,")
                            .replace("1E","30,").replace("1B","27,").replace("5E","94,")
                            .replace("A0","160,") + "0.15)" if "#" in color else color
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, title="Vue radar — structure économique",
        height=400, paper_bgcolor="#FEFCF8",
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown('<p class="source-note">Sources : INSEE Filosofi 2021 — revenus fiscaux localisés par commune</p>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ONGLET 3 — REVENUS
# ══════════════════════════════════════════════════════════════
with tab_rev:
    st.markdown("""
    Distribution des **revenus fiscaux de référence par unité de consommation** (€/an).
    Les déciles et quartiles sont classés par rang de percentile croissant.
    """)

    with st.expander("ℹ️ Comment lire ce graphique ?"):
        st.markdown("""
        | Indicateur | Percentile | Signification |
        |------------|-----------|---------------|
        | D1 | 10 % | 10 % des ménages ont un revenu **inférieur** à cette valeur |
        | D2 | 20 % | 20 % des ménages ont un revenu inférieur |
        | Q1 | 25 % | 25 % des ménages sont en dessous (1er quartile) |
        | D3 | 30 % | … |
        | D4 | 40 % | … |
        | Médiane | 50 % | La moitié des ménages est en dessous (revenu "typique") |
        | D6 | 60 % | … |
        | D7 | 70 % | … |
        | Q3 | 75 % | 75 % des ménages sont en dessous (3e quartile) |
        | D8 | 80 % | … |
        | D9 | 90 % | Seuil à partir duquel on est dans les 10 % les plus aisés |
        """)

    # Ordre correct par percentile croissant
    decile_labels = ["D1\n(10%)", "D2\n(20%)", "Q1\n(25%)", "D3\n(30%)", "D4\n(40%)",
                     "Médiane\n(50%)", "D6\n(60%)", "D7\n(70%)", "Q3\n(75%)", "D8\n(80%)", "D9\n(90%)"]
    keys_a = [val(ca,k) for k in ["d1","d2","rev_q1","d3","d4","rev_med","d6","d7","rev_q3","d8","d9"]]
    keys_b = [val(cb,k) for k in ["d1","d2","rev_q1","d3","d4","rev_med","d6","d7","rev_q3","d8","d9"]]

    fig_dec = go.Figure()
    fig_dec.add_trace(go.Scatter(
        x=decile_labels, y=keys_a, name=ca["name"],
        mode="lines+markers", line=dict(color=COLOR_A, width=2.5),
        marker=dict(size=8, color=COLOR_A),
        hovertemplate="%{x}<br>" + ca["name"] + " : %{y:,.0f} €<extra></extra>"
    ))
    fig_dec.add_trace(go.Scatter(
        x=decile_labels, y=keys_b, name=cb["name"],
        mode="lines+markers", line=dict(color=COLOR_B, width=2.5),
        marker=dict(size=8, color=COLOR_B),
        hovertemplate="%{x}<br>" + cb["name"] + " : %{y:,.0f} €<extra></extra>"
    ))
    fig_dec.update_layout(
        title="Distribution des revenus fiscaux (déciles + quartiles, par percentile croissant)",
        yaxis_title="Revenus fiscaux (€/an/UC)",
        yaxis_tickformat=",.0f",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FEFCF8", paper_bgcolor="#FEFCF8",
        height=420, margin=dict(t=60, b=50, l=60, r=20),
        xaxis=dict(tickangle=0),
    )
    st.plotly_chart(fig_dec, use_container_width=True)

    # Tableau comparatif
    st.divider()
    st.subheader("Tableau comparatif")
    rows = []
    for label, ka, kb in zip(
        ["D1 (10%)", "D2 (20%)", "Q1 (25%)", "D3 (30%)", "D4 (40%)",
         "Médiane (50%)", "D6 (60%)", "D7 (70%)", "Q3 (75%)", "D8 (80%)", "D9 (90%)"],
        ["d1","d2","rev_q1","d3","d4","rev_med","d6","d7","rev_q3","d8","d9"],
        ["d1","d2","rev_q1","d3","d4","rev_med","d6","d7","rev_q3","d8","d9"]
    ):
        va, vb = val(ca, ka), val(cb, kb)
        ecart = int(va - vb) if va and vb else None
        rows.append({
            "Indicateur": label,
            ca["name"]: fmt_eur(va),
            cb["name"]: fmt_eur(vb),
            "Écart": (f"+{ecart:,} €".replace(",", " ") if ecart and ecart > 0
                      else f"{ecart:,} €".replace(",", " ") if ecart else "—"),
        })
    df_table = pd.DataFrame(rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

    st.markdown('<p class="source-note">Sources : INSEE Filosofi 2021 — revenus fiscaux de référence par UC et par commune</p>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ONGLET 4 — MÉTÉO
# ══════════════════════════════════════════════════════════════
with tab_met:
    JOURS = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"]

    def wicon(code):
        if code <= 1:  return "☀️"
        if code <= 3:  return "⛅"
        if code <= 48: return "🌫️"
        if code <= 57: return "🌧️"
        if code <= 67: return "🌧️"
        if code <= 77: return "❄️"
        if code <= 82: return "🌦️"
        return "⛈️"

    def wdesc(code):
        if code <= 1:  return "Ensoleillé"
        if code <= 3:  return "Nuageux"
        if code <= 48: return "Brumeux"
        if code <= 57: return "Bruine"
        if code <= 67: return "Pluie"
        if code <= 77: return "Neige"
        if code <= 82: return "Averses"
        return "Orage"

    @st.cache_data(ttl=3600)
    def geocode(city_name):
        url = "https://nominatim.openstreetmap.org/search"
        r = requests.get(url, params={"city": city_name, "country": "France",
                                       "format": "json", "limit": 1},
                          headers={"Accept-Language": "fr", "User-Agent": "ComparaVilles-SAE"})
        data = r.json()
        if not data:
            raise ValueError(f"Ville introuvable : {city_name}")
        return float(data[0]["lat"]), float(data[0]["lon"])

    @st.cache_data(ttl=3600)
    def fetch_weather(lat, lon):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weathercode",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "forecast_days": 7, "timezone": "Europe/Paris"
        }
        return requests.get(url, params=params).json()

    with st.spinner("Récupération des données météo…"):
        try:
            lat_a, lon_a = geocode(ca["name"])
            time.sleep(1.1)  # Nominatim rate limit
            lat_b, lon_b = geocode(cb["name"])
            wa = fetch_weather(lat_a, lon_a)
            wb = fetch_weather(lat_b, lon_b)

            # Météo actuelle
            c1, c2 = st.columns(2)
            for col, city, w, color in [(c1, ca, wa, "🔴"), (c2, cb, wb, "🔵")]:
                with col:
                    cur = w["current"]
                    st.markdown(f"### {color} {city['name']}")
                    icon = wicon(cur["weathercode"])
                    desc = wdesc(cur["weathercode"])
                    st.markdown(f"## {icon} {round(cur['temperature_2m'])}°C — {desc}")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Humidité", f"{cur['relative_humidity_2m']} %")
                    m2.metric("Vent", f"{round(cur['wind_speed_10m'])} km/h")
                    m3.metric("Précip.", f"{cur['precipitation']} mm")
                    m4.metric("Ressenti", f"{round(cur['temperature_2m'] - cur['wind_speed_10m']*0.07)}°C")

                    # Prévisions 7 jours
                    st.markdown("**Prévisions 7 jours :**")
                    d = w["daily"]
                    fc_cols = st.columns(7)
                    for i in range(7):
                        from datetime import datetime
                        date = datetime.strptime(d["time"][i], "%Y-%m-%d")
                        with fc_cols[i]:
                            st.markdown(f"""
                            <div style="text-align:center;background:#F0ECE4;border-radius:8px;padding:6px 2px">
                              <div style="font-size:.7rem;color:#999">{JOURS[date.weekday()+1 if date.weekday()<6 else 0]}</div>
                              <div style="font-size:1.3rem">{wicon(d['weathercode'][i])}</div>
                              <div style="font-size:.78rem;font-weight:bold">{round(d['temperature_2m_max'][i])}°</div>
                              <div style="font-size:.75rem;color:#888">{round(d['temperature_2m_min'][i])}°</div>
                            </div>
                            """, unsafe_allow_html=True)

            # Graphique températures
            st.divider()
            from datetime import datetime
            d_a, d_b = wa["daily"], wb["daily"]
            labels = [datetime.strptime(t, "%Y-%m-%d").strftime("%a %d/%m") for t in d_a["time"][:7]]

            fig_clim = go.Figure()
            for name_c, d, color in [(ca["name"], d_a, COLOR_A), (cb["name"], d_b, COLOR_B)]:
                fig_clim.add_trace(go.Scatter(
                    x=labels, y=[round(v) for v in d["temperature_2m_max"][:7]],
                    name=f"{name_c} max", line=dict(color=color, width=2.5),
                    mode="lines+markers"
                ))
                fig_clim.add_trace(go.Scatter(
                    x=labels, y=[round(v) for v in d["temperature_2m_min"][:7]],
                    name=f"{name_c} min", line=dict(color=color, width=1.5, dash="dot"),
                    mode="lines+markers", marker=dict(size=6)
                ))
            fig_clim.update_layout(
                title="Températures prévues — 7 jours",
                yaxis_title="°C",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor="#FEFCF8", paper_bgcolor="#FEFCF8",
                height=350, margin=dict(t=60, b=30),
            )
            st.plotly_chart(fig_clim, use_container_width=True)
            st.markdown('<p class="source-note">Sources : Nominatim (OpenStreetMap) — géocodage · Open-Meteo API (ECMWF) — météo gratuite sans clé</p>',
                        unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Impossible de charger la météo. Vérifiez votre connexion internet. ({e})")
