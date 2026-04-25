"""
preprocessing.py — ComparaVilles
SAE Outils Décisionnels

Auteurs : Aziz Djerbi, Ismaël Gahlouzi

Ce script extrait et nettoie les données INSEE pour générer le fichier JSON
utilisé par l'application Streamlit ComparaVilles.

Données requises (à placer dans le même dossier que ce script) :
  - ensemble/donnees_communes.csv
      → INSEE Recensement de la Population 2021 (fichier communes)
  - indic-struct-distrib-revenu-2021-COMMUNES_csv/FILO2021_DEC_COM.csv
      → INSEE Filosofi 2021 (revenus fiscaux localisés des ménages)

Usage :
  python3 preprocessing.py
  → génère data/cities_data.json (utilisé par app.py)

Périmètre :
  - Communes de France métropolitaine avec PMUN >= 20 000 habitants
  - Paris, Marseille et Lyon traités via leurs arrondissements
  - 480 villes environ au total
"""

import pandas as pd
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# ────────────────────────────────────────────────────────────
# 1. Chargement des communes (INSEE Recensement 2021)
# ────────────────────────────────────────────────────────────
print("Chargement des communes...")
communes = pd.read_csv(
    os.path.join(BASE, "ensemble", "donnees_communes.csv"),
    sep=";", dtype=str
)
communes["PMUN"] = pd.to_numeric(communes["PMUN"], errors="coerce")

# Gestion spéciale Paris, Marseille, Lyon (découpées en arrondissements)
ARR = {
    "Paris":     (r"^751\d\d$",          "75056", "Île-de-France",               "75", "Paris"),
    "Marseille": (r"^1320\d$|^1321[0-6]$", "13055", "Provence-Alpes-Côte d'Azur", "13", "Bouches-du-Rhône"),
    "Lyon":      (r"^6938[1-9]$",         "69123", "Auvergne-Rhône-Alpes",        "69", "Rhône"),
}
arr_codes = set()
for _, (pat, *_) in ARR.items():
    arr_codes |= set(communes[communes["COM"].str.match(pat, na=False)]["COM"].tolist())

# Sélection des communes > 20 000 hab (hors arrondissements)
big = communes[
    (communes["PMUN"] >= 20000) & ~communes["COM"].isin(arr_codes)
].copy().rename(columns={"COM": "CODGEO", "Région": "region_name"})

print(f"  → {len(big)} communes retenues (hors Paris/Marseille/Lyon arrondissements)")

# ────────────────────────────────────────────────────────────
# 2. Chargement des données Filosofi 2021
#    Source : INSEE — Revenus fiscaux localisés des ménages
# ────────────────────────────────────────────────────────────
print("Chargement Filosofi 2021...")
COLS = [
    "CODGEO",
    "Q221",               # Revenu médian fiscal (€/UC/an)
    "Q121", "Q321",       # 1er quartile (Q1) et 3e quartile (Q3)
    "D121", "D221", "D321", "D421",   # Déciles D1 à D4
    "D621", "D721", "D821", "D921",   # Déciles D6 à D9
    "GI21",               # Coefficient de Gini
    "S80S2021",           # Rapport interdécile S80/S20
    "PACT21",             # Part des foyers avec revenus d'activité (%)
    "PTSA21",             # Part des salaires et traitements dans les revenus (%)
    "PCHO21",             # Part des allocations chômage dans les revenus (%)
    "PBEN21",             # Part des pensions et retraites dans les revenus (%)
    "PPEN21",             # Part des autres pensions dans les revenus (%)
]
filo = pd.read_csv(
    os.path.join(BASE, "indic-struct-distrib-revenu-2021-COMMUNES_csv", "FILO2021_DEC_COM.csv"),
    sep=";", dtype=str, usecols=COLS
)
print(f"  → {len(filo)} communes dans Filosofi")

# ────────────────────────────────────────────────────────────
# 3. Fusion Recensement × Filosofi
# ────────────────────────────────────────────────────────────
df = big.merge(filo, on="CODGEO", how="left")

# Conversion numérique (virgules FR → points, 's' = secret statistique → NaN)
for col in COLS[1:]:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", ".").str.strip(),
            errors="coerce"
        )

# ────────────────────────────────────────────────────────────
# 4. Table de correspondance codes → noms de départements
# ────────────────────────────────────────────────────────────
DEP_NAMES = {
    "01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-de-Haute-Provence","05":"Hautes-Alpes",
    "06":"Alpes-Maritimes","07":"Ardèche","08":"Ardennes","09":"Ariège","10":"Aube",
    "11":"Aude","12":"Aveyron","13":"Bouches-du-Rhône","14":"Calvados","15":"Cantal",
    "16":"Charente","17":"Charente-Maritime","18":"Cher","19":"Corrèze","2A":"Corse-du-Sud",
    "2B":"Haute-Corse","21":"Côte-d'Or","22":"Côtes-d'Armor","23":"Creuse","24":"Dordogne",
    "25":"Doubs","26":"Drôme","27":"Eure","28":"Eure-et-Loir","29":"Finistère","30":"Gard",
    "31":"Haute-Garonne","32":"Gers","33":"Gironde","34":"Hérault","35":"Ille-et-Vilaine",
    "36":"Indre","37":"Indre-et-Loire","38":"Isère","39":"Jura","40":"Landes",
    "41":"Loir-et-Cher","42":"Loire","43":"Haute-Loire","44":"Loire-Atlantique","45":"Loiret",
    "46":"Lot","47":"Lot-et-Garonne","48":"Lozère","49":"Maine-et-Loire","50":"Manche",
    "51":"Marne","52":"Haute-Marne","53":"Mayenne","54":"Meurthe-et-Moselle","55":"Meuse",
    "56":"Morbihan","57":"Moselle","58":"Nièvre","59":"Nord","60":"Oise","61":"Orne",
    "62":"Pas-de-Calais","63":"Puy-de-Dôme","64":"Pyrénées-Atlantiques","65":"Hautes-Pyrénées",
    "66":"Pyrénées-Orientales","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhône","70":"Haute-Saône",
    "71":"Saône-et-Loire","72":"Sarthe","73":"Savoie","74":"Haute-Savoie","75":"Paris",
    "76":"Seine-Maritime","77":"Seine-et-Marne","78":"Yvelines","79":"Deux-Sèvres","80":"Somme",
    "81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendée","86":"Vienne",
    "87":"Haute-Vienne","88":"Vosges","89":"Yonne","90":"Territoire de Belfort","91":"Essonne",
    "92":"Hauts-de-Seine","93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d'Oise",
}

# ────────────────────────────────────────────────────────────
# 5. Construction de la liste JSON
# ────────────────────────────────────────────────────────────
def num(val):
    """Convertit une valeur en float arrondi, ou None si manquante."""
    if pd.isna(val):
        return None
    return round(float(val), 2)

def get_filo_row(codgeo):
    """Récupère les indicateurs Filosofi pour une commune (Paris/Marseille/Lyon)."""
    row = filo[filo["CODGEO"] == codgeo]
    if row.empty:
        return {}
    r = row.iloc[0]
    return {
        "rev_med": num(pd.to_numeric(str(r.get("Q221","")).replace(",","."), errors="coerce")),
        "rev_q1":  num(pd.to_numeric(str(r.get("Q121","")).replace(",","."), errors="coerce")),
        "rev_q3":  num(pd.to_numeric(str(r.get("Q321","")).replace(",","."), errors="coerce")),
        "gini":    num(pd.to_numeric(str(r.get("GI21","")).replace(",","."), errors="coerce")),
        "s80s20":  num(pd.to_numeric(str(r.get("S80S2021","")).replace(",","."), errors="coerce")),
        "d1":  num(pd.to_numeric(str(r.get("D121","")).replace(",","."), errors="coerce")),
        "d2":  num(pd.to_numeric(str(r.get("D221","")).replace(",","."), errors="coerce")),
        "d3":  num(pd.to_numeric(str(r.get("D321","")).replace(",","."), errors="coerce")),
        "d4":  num(pd.to_numeric(str(r.get("D421","")).replace(",","."), errors="coerce")),
        "d6":  num(pd.to_numeric(str(r.get("D621","")).replace(",","."), errors="coerce")),
        "d7":  num(pd.to_numeric(str(r.get("D721","")).replace(",","."), errors="coerce")),
        "d8":  num(pd.to_numeric(str(r.get("D821","")).replace(",","."), errors="coerce")),
        "d9":  num(pd.to_numeric(str(r.get("D921","")).replace(",","."), errors="coerce")),
        "pact": num(pd.to_numeric(str(r.get("PACT21","")).replace(",","."), errors="coerce")),
        "ptsa": num(pd.to_numeric(str(r.get("PTSA21","")).replace(",","."), errors="coerce")),
        "pcho": num(pd.to_numeric(str(r.get("PCHO21","")).replace(",","."), errors="coerce")),
        "pben": num(pd.to_numeric(str(r.get("PBEN21","")).replace(",","."), errors="coerce")),
        "paut": num(pd.to_numeric(str(r.get("PPEN21","")).replace(",","."), errors="coerce")),
    }

cities = []
for _, row in df.iterrows():
    dep = str(row["DEP"]).strip()
    entry = {
        "name":     str(row["Commune"]).strip(),
        "dep":      dep,
        "dep_name": DEP_NAMES.get(dep, dep),
        "region":   str(row["region_name"]).strip(),
        "pop":      int(row["PMUN"]),
        "codgeo":   str(row["CODGEO"]).strip(),
    }
    for col in COLS[1:]:
        val = row.get(col)
        entry[col.lower().replace("21","").replace("s80s","s80s20")] = num(val) if pd.notna(val) else None
    cities.append(entry)

# Ajout de Paris, Marseille, Lyon (population agrégée des arrondissements)
for city_name, (pat, codgeo, region, dep, dep_name) in ARR.items():
    pop = int(communes[communes["COM"].str.match(pat, na=False)]["PMUN"].sum())
    entry = {
        "name": city_name, "dep": dep, "dep_name": dep_name,
        "region": region, "pop": pop, "codgeo": codgeo
    }
    entry.update(get_filo_row(codgeo))
    cities.append(entry)

cities.sort(key=lambda x: x["name"])
print(f"\nTotal villes générées : {len(cities)}")

# ────────────────────────────────────────────────────────────
# 6. Export JSON → data/cities_data.json
# ────────────────────────────────────────────────────────────
os.makedirs(os.path.join(BASE, "data"), exist_ok=True)
out_path = os.path.join(BASE, "data", "cities_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(cities, f, ensure_ascii=False, separators=(",", ":"))

size_ko = os.path.getsize(out_path) / 1024
print(f"Fichier généré : {out_path} ({size_ko:.0f} Ko)")
print("Prêt pour l'application Streamlit (app.py).")
