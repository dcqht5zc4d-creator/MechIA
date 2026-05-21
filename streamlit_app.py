import streamlit as st
from datetime import datetime
import hashlib
import json
import re

st.set_page_config(page_title="MecaTech IA", page_icon="🔧", layout="wide")

# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>
.stApp { background-color:#101214; color:#f2f2f2; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
h1,h2,h3 { color:#f5f5f5; }
[data-testid="stSidebar"] { background:#151719; }
.card { background:#171a1d; border:1px solid #2d3338; border-radius:14px; padding:16px; margin:10px 0; }
.good { border-left:5px solid #52b788; }
.warn { border-left:5px solid #f59f00; }
.danger { border-left:5px solid #ef476f; }
.info { border-left:5px solid #4dabf7; }
.small { color:#b8bec4; font-size:0.92rem; }
.score { font-size:1.4rem; font-weight:700; color:#ff7a1a; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE — persistence console
# =========================================================
DEFAULTS = {
    "machine_type": "Chargeuse sur roues",
    "brand_model": "",
    "hours_km": "",
    "system": "Transmission",
    "fault_nature": "Inconnue / à déterminer",
    "dtcs": "",
    "symptoms": "",
    "field_notes": "",
    "history": "",
    "checked_evidence": [],
    "last_analysis": None,
    "cases": [],
    "analysis_counter": 0,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# DATA
# =========================================================
SYSTEMS = [
    "Transmission", "Frein", "Hydraulique", "Moteur", "Électrique", "Refroidissement", "Direction", "PTO / accessoires", "Autre / inconnu"
]

NATURES = [
    "Inconnue / à déterminer", "Mécanique", "Électrique / commande", "Hydraulique / pression", "Capteur / signal", "Module / logique"
]

EVIDENCE_OPTIONS = [
    "Capteur manipulé/débranché change le symptôme",
    "Bouger le faisceau/connecteur change le symptôme",
    "Alimentation directe active le composant",
    "Alimentation directe ne donne aucune réaction",
    "Redémarrage/reset change temporairement le comportement",
    "Filtre/huile/pièce remplacée sans changement",
    "Pression réelle mesurée ou réaction de pression observée",
    "Fonction mécanique bouge/s’applique après manipulation",
]

BASE_HYPOTHESES = {
    "Frein": {
        "Mécanique": [
            "Mécanisme de frein, linkage, ajustement, usure ou blocage physique",
            "Mouvement réel du frein incomplet malgré une commande présente",
        ],
        "Électrique / commande": [
            "Commande électrique, relais, sortie module, alimentation ou ground du circuit de frein",
            "Solénoïde/valve commandé électriquement mais activation réelle non confirmée",
        ],
        "Hydraulique / pression": [
            "Pression air/hydraulique insuffisante, absente ou non transmise au frein",
            "Valve de commande, fuite interne ou restriction du circuit de frein",
        ],
        "Capteur / signal": [
            "Capteur de pression/switch de frein ou signal de retour incohérent",
            "Connecteur/faisceau du capteur ou témoin interprété incorrectement",
        ],
        "Module / logique": [
            "TCU/ECU/interlock bloque ou autorise mal l’application du frein",
            "État logique/protection qui revient après redémarrage",
        ],
    },
    "Transmission": {
        "Mécanique": [
            "Embrayage interne, arbre, train d’engrenage ou dommage mécanique à confirmer",
            "Usure/blocage interne après exclusion des commandes et pressions",
        ],
        "Électrique / commande": [
            "Sélecteur, faisceau, relais, alimentation ou commande de transmission intermittente",
            "Sortie module ou commande solénoïde instable sous charge",
        ],
        "Hydraulique / pression": [
            "Pression de commande, valve body, solénoïdes hydrauliques ou fuite interne",
            "Réponse hydraulique insuffisante malgré demande de rapport",
        ],
        "Capteur / signal": [
            "Capteur vitesse entrée/sortie, position sélecteur ou retour de rapport incohérent",
            "Signal capteur intermittent causant retour au neutre ou protection",
        ],
        "Module / logique": [
            "Module transmission met le système en protection ou neutre commandé",
            "Condition logique ou interlock qui annule l’engagement",
        ],
    },
    "Hydraulique": {
        "Mécanique": ["Valve qui colle, cylindre, linkage ou composant physique bloqué"],
        "Électrique / commande": ["Commande de valve/solénoïde, sortie module ou faisceau"],
        "Hydraulique / pression": ["Pompe, restriction, fuite interne, pression principale ou pilotage insuffisant"],
        "Capteur / signal": ["Capteur de pression ou lecture différente du manomètre"],
        "Module / logique": ["Commande pilotée limitée par un interlock ou mode protection"],
    },
    "Moteur": {
        "Mécanique": ["Compression, restriction mécanique, usure interne ou distribution"],
        "Électrique / commande": ["Faisceau, alimentation ECU, commande injecteur/turbo/EGR"],
        "Hydraulique / pression": ["Pression carburant/rail, pompe, pression d’huile"],
        "Capteur / signal": ["Capteur MAP/MAF/température/pression incohérent"],
        "Module / logique": ["Derate, mode protection, post-traitement DPF/SCR/EGR"],
    },
    "Électrique": {
        "Mécanique": ["Composant mécanique commandé électriquement bloqué"],
        "Électrique / commande": ["Masse, alimentation, relais, fusible, connecteur, fil cassé"],
        "Hydraulique / pression": ["Commande électrique correcte mais réaction hydraulique absente"],
        "Capteur / signal": ["Signal capteur intermittent ou hors plage"],
        "Module / logique": ["CAN/J1939/J1708, module décroche ou bloque une sortie"],
    },
    "Refroidissement": {
        "Mécanique": ["Pompe à eau, thermostat, fan, radiateur obstrué, circulation"],
        "Électrique / commande": ["Commande fan, relais, capteur température, faisceau"],
        "Hydraulique / pression": ["Pression système, air dans circuit, fuite interne/externe"],
        "Capteur / signal": ["Lecture température incohérente vs température réelle"],
        "Module / logique": ["ECU limite puissance à cause de température lue/réelle"],
    },
    "Direction": {
        "Mécanique": ["Articulation, pivot, bushing, cylindre ou jeu mécanique"],
        "Électrique / commande": ["Commande valve pilotée, capteur angle/position, faisceau"],
        "Hydraulique / pression": ["Pression direction, orbitrol, valve ou pompe"],
        "Capteur / signal": ["Signal angle/position/pression incohérent"],
        "Module / logique": ["Module ou interlock limite l’assistance"],
    },
    "PTO / accessoires": {
        "Mécanique": ["Clutch, arbre, accessoire bloqué, charge mécanique"],
        "Électrique / commande": ["Switch, relais, solénoïde, faisceau PTO"],
        "Hydraulique / pression": ["Pression d’engagement, valve ou circuit piloté"],
        "Capteur / signal": ["Retour position/vitesse PTO incohérent"],
        "Module / logique": ["Interlock ou condition sécurité non satisfaite"],
    },
}

GENERAL_TESTS = {
    "Mécanique": [
        "Confirmer le mouvement physique réel : jeu, blocage, ajustement, usure.",
        "Comparer commande demandée vs mouvement réel observé.",
    ],
    "Électrique / commande": [
        "Mesurer alimentation et ground sous charge, pas seulement à vide.",
        "Vérifier relais, fusibles, connecteurs et continuité pendant wiggle test.",
    ],
    "Hydraulique / pression": [
        "Mesurer pression réelle au manomètre selon procédure OEM.",
        "Comparer pression demandée vs pression réelle et réaction en aval.",
    ],
    "Capteur / signal": [
        "Mesurer alimentation, ground et signal de retour du capteur.",
        "Comparer valeur capteur réelle avec donnée live du module.",
    ],
    "Module / logique": [
        "Lire états live : demande, autorisation, interlock, protection, retour d’état.",
        "Comparer avant/après reset ou redémarrage.",
    ],
}

# =========================================================
# HELPERS
# =========================================================
def combined_text() -> str:
    return "\n".join([
        st.session_state.get("brand_model", ""),
        st.session_state.get("hours_km", ""),
        st.session_state.get("dtcs", ""),
        st.session_state.get("symptoms", ""),
        st.session_state.get("field_notes", ""),
        st.session_state.get("history", ""),
        " ".join(st.session_state.get("checked_evidence", [])),
    ]).lower()


def make_input_snapshot() -> dict:
    return {
        "machine_type": st.session_state.machine_type,
        "brand_model": st.session_state.brand_model,
        "hours_km": st.session_state.hours_km,
        "system": st.session_state.system,
        "fault_nature": st.session_state.fault_nature,
        "dtcs": st.session_state.dtcs,
        "symptoms": st.session_state.symptoms,
        "field_notes": st.session_state.field_notes,
        "history": st.session_state.history,
        "checked_evidence": st.session_state.checked_evidence,
    }


def input_hash(snapshot: dict) -> str:
    raw = json.dumps(snapshot, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def has_any(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)


def extract_codes(text: str) -> list[str]:
    upper = text.upper()
    patterns = [
        r"\b[A-Z]{2,5}\s*\d{3,6}\.\d{1,2}\b",
        r"\bSPN\s*\d{3,6}\s*FMI\s*\d{1,2}\b",
        r"\b[PUCB]\d{4}\b",
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, upper))
    return list(dict.fromkeys(found))


# The visible widgets use _keys. The permanent values use normal keys.
# This prevents Streamlit from deleting the console text when the Console page is not rendered.
FORM_KEYS = [
    "machine_type", "brand_model", "hours_km", "system", "fault_nature",
    "dtcs", "symptoms", "field_notes", "history", "checked_evidence",
]


def init_console_widgets():
    """Rebuild visible widget values from permanent session values when returning to Console."""
    for k in FORM_KEYS:
        wk = "_" + k
        if wk not in st.session_state:
            st.session_state[wk] = st.session_state.get(k, DEFAULTS.get(k, ""))


def sync_console_from_widgets():
    """Copy visible widget values into permanent session storage."""
    for k in FORM_KEYS:
        wk = "_" + k
        if wk in st.session_state:
            st.session_state[k] = st.session_state[wk]


def clear_form():
    reset_values = {
        "machine_type": "Chargeuse sur roues",
        "brand_model": "",
        "hours_km": "",
        "system": "Transmission",
        "fault_nature": "Inconnue / à déterminer",
        "dtcs": "",
        "symptoms": "",
        "field_notes": "",
        "history": "",
        "checked_evidence": [],
    }
    for k, v in reset_values.items():
        st.session_state[k] = v
        st.session_state["_" + k] = v

# =========================================================
# DIAGNOSTIC ENGINE v0.1.2 — evidence weighted
# =========================================================
def detect_facts(text: str, snapshot: dict) -> dict:
    facts = []
    conditions = []
    evidence = []
    missing = []
    deductions = []

    codes = extract_codes(text)
    if codes:
        facts.append("Codes structurés détectés")
    elif "aucun code" in text or "pas de code" in text:
        facts.append("Aucun code rapporté")
    else:
        missing.append("Codes actifs/inactifs ou confirmation qu’il n’y en a pas")

    if has_any(text, ["intermittent", "parfois", "revient", "recommence", "pas toujours"]):
        conditions.append("Intermittent / revient")
    if has_any(text, ["redémarr", "redemarr", "reset", "repart la machine", "après redémarrage", "apres redemarrage"]):
        conditions.append("Comportement influencé par redémarrage/reset")
    if has_any(text, ["à chaud", "a chaud", "chaud"]):
        conditions.append("À chaud")
    if has_any(text, ["à froid", "a froid", "froid"]):
        conditions.append("À froid")

    if has_any(text, ["témoin", "temoin", "voyant", "lumière", "lumiere"]):
        facts.append("Témoin/voyant mentionné")
    if has_any(text, ["ne s’applique", "ne s'applique", "s applique pas", "s’applique pas", "ne s engage", "ne s’engage"]):
        facts.append("Fonction ne s’applique/ne s’engage pas")
    if has_any(text, ["pression sort", "pression est sortie", "pression sortie"]):
        evidence.append("Réaction de pression observée")
    if has_any(text, ["frein s’applique", "frein s'applique", "frein s applique", "brake s’applique", "brake s'applique"]):
        evidence.append("Fonction mécanique s’applique après manipulation")
    if has_any(text, ["huile ok", "filtre ok", "ground", "masse", "fusible ok", "courant"]):
        evidence.append("Tests de base ou électriques mentionnés")

    selected_evidence = snapshot.get("checked_evidence", [])
    evidence.extend(selected_evidence)

    # Deductions — these are intentionally field_notes-weighted by using full text + checked evidence
    if (
        has_any(text, ["capteur", "sensor"])
        and has_any(text, ["démanch", "demanch", "débranch", "debranch", "manipul", "boug"])
        and has_any(text, ["pression sort", "pression est sortie", "s’applique", "s'applique", "s applique", "témoin", "temoin", "allume"])
    ) or "Capteur manipulé/débranché change le symptôme" in selected_evidence:
        deductions.append({
            "nature": "Capteur / signal",
            "title": "Action capteur → réaction du système",
            "text": "Une action sur le capteur change le comportement. Le capteur, son signal, son connecteur, le faisceau ou l’interprétation module doivent monter en priorité.",
            "score_bonus": 45,
            "tests": [
                "Lire la valeur live du capteur pendant commande.",
                "Mesurer alimentation, ground et signal retour du capteur.",
                "Reproduire la manipulation capteur/connecteur en surveillant la donnée live.",
            ],
        })

    if (
        has_any(text, ["faisceau", "connecteur", "wiggle", "bouge le fil", "bougé le fil"])
        and has_any(text, ["change", "revient", "disparaît", "disparait", "fonctionne", "coupe"])
    ) or "Bouger le faisceau/connecteur change le symptôme" in selected_evidence:
        deductions.append({
            "nature": "Électrique / commande",
            "title": "Faisceau/connecteur → panne change",
            "text": "Le comportement change avec le faisceau/connecteur. Priorité au connecteur, pins, continuité, masse et alimentation sous charge.",
            "score_bonus": 40,
            "tests": [
                "Wiggle test contrôlé pendant lecture live.",
                "Chute de voltage sous charge.",
                "Inspection corrosion/tension des pins/frottement.",
            ],
        })

    if "Alimentation directe active le composant" in selected_evidence or (
        has_any(text, ["courant direct", "alimenté direct", "alimente direct", "jumper", "shunt"])
        and has_any(text, ["fonctionne", "marche", "s’applique", "s'applique", "active", "bouge"])
    ):
        deductions.append({
            "nature": "Électrique / commande",
            "title": "Alimentation directe active le composant",
            "text": "Le composant en aval semble capable. Priorité à la commande normale, relais, sortie module, autorisations et faisceau amont.",
            "score_bonus": 35,
            "tests": ["Comparer alimentation directe vs commande normale.", "Vérifier sortie module/relais/interlock."],
        })

    if "Alimentation directe ne donne aucune réaction" in selected_evidence or (
        has_any(text, ["courant direct", "alimenté direct", "alimente direct", "jumper", "shunt"])
        and has_any(text, ["rien", "aucune réaction", "pas de réaction", "ne bouge pas"])
    ):
        deductions.append({
            "nature": "Mécanique",
            "title": "Aucune réaction même en alimentation directe",
            "text": "La priorité se déplace vers l’actionneur, valve, pression ou mouvement mécanique en aval.",
            "score_bonus": 35,
            "tests": ["Mesurer résistance/actionneur.", "Confirmer mouvement mécanique et pression en aval."],
        })

    if "Redémarrage/reset change temporairement le comportement" in selected_evidence or has_any(text, ["redémarr", "redemarr", "reset", "repart la machine"]):
        deductions.append({
            "nature": "Module / logique",
            "title": "Redémarrage/reset influence le symptôme",
            "text": "Un reset qui change le comportement oriente vers module, état logique, interlock, protection ou capteur incohérent.",
            "score_bonus": 30,
            "tests": ["Comparer états live avant/après reset.", "Lire codes avant/après redémarrage.", "Identifier l’interlock ou la condition qui revient."],
        })

    if not snapshot.get("field_notes", "").strip():
        missing.append("Essais déjà faits / preuves terrain")
    if not snapshot.get("history", "").strip():
        missing.append("Historique machine ou réparations récentes")

    return {
        "codes": codes,
        "facts": list(dict.fromkeys(facts)),
        "conditions": list(dict.fromkeys(conditions)),
        "evidence": list(dict.fromkeys(evidence)),
        "missing": list(dict.fromkeys(missing)),
        "deductions": deductions,
    }


def active_nature(snapshot: dict, detected: dict) -> str:
    chosen = snapshot["fault_nature"]
    if chosen != "Inconnue / à déterminer":
        return chosen
    if detected["deductions"]:
        return detected["deductions"][0]["nature"]
    text = combined_text()
    if has_any(text, ["mécanique", "mecanique", "bloqué", "bloque", "usé", "use", "cassé", "casse", "linkage", "ajustement"]):
        return "Mécanique"
    if has_any(text, ["pression", "hydraulique", "valve", "pompe", "air"]):
        return "Hydraulique / pression"
    if has_any(text, ["capteur", "sensor", "signal", "témoin", "temoin", "voyant"]):
        return "Capteur / signal"
    if has_any(text, ["tcu", "ecu", "module", "logic", "interlock", "reset", "redémarr", "redemarr"]):
        return "Module / logique"
    if has_any(text, ["courant", "voltage", "relais", "fusible", "faisceau", "connecteur", "ground"]):
        return "Électrique / commande"
    return "Inconnue / à déterminer"


def analyze() -> dict:
    snapshot = make_input_snapshot()
    text = "\n".join(str(v) for v in snapshot.values() if isinstance(v, (str, list))).lower()
    detected = detect_facts(text, snapshot)
    nature = active_nature(snapshot, detected)
    system = snapshot["system"]

    system_hyp = BASE_HYPOTHESES.get(system, BASE_HYPOTHESES.get("Électrique"))
    scores = {n: 10 for n in ["Mécanique", "Électrique / commande", "Hydraulique / pression", "Capteur / signal", "Module / logique"]}

    # Mechanic choices are authoritative
    scores[nature] = scores.get(nature, 0) + 35

    # Checked evidence + text evidence changes scores strongly
    for d in detected["deductions"]:
        scores[d["nature"]] = scores.get(d["nature"], 0) + d["score_bonus"]

    # Text weighting
    if has_any(text, ["mécanique", "mecanique", "bloqué", "bloque", "cassé", "casse", "usé", "use", "ajustement", "linkage"]):
        scores["Mécanique"] += 18
    if has_any(text, ["pression", "hydraulique", "valve", "pompe", "air"]):
        scores["Hydraulique / pression"] += 18
    if has_any(text, ["capteur", "sensor", "signal"]):
        scores["Capteur / signal"] += 18
    if has_any(text, ["tcu", "ecu", "module", "interlock", "redémarr", "redemarr", "reset"]):
        scores["Module / logique"] += 18
    if has_any(text, ["courant", "voltage", "ground", "masse", "faisceau", "connecteur", "relais", "fusible"]):
        scores["Électrique / commande"] += 14

    # Build prioritized hypotheses
    ranked_natures = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    hypotheses = []
    for n, score in ranked_natures:
        for h in system_hyp.get(n, []):
            hypotheses.append({"nature": n, "title": h, "score": score})

    tests = []
    for d in detected["deductions"]:
        tests.extend(d["tests"])
    for n, _ in ranked_natures[:3]:
        tests.extend(GENERAL_TESTS.get(n, []))
    tests = list(dict.fromkeys(tests))

    severity = "Critique" if system == "Frein" else ("Élevé" if system in ["Transmission", "Direction"] else "Moyen")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_hash": input_hash(snapshot),
        "snapshot": snapshot,
        "system": system,
        "active_nature": nature,
        "severity": severity,
        "detected": detected,
        "scores": scores,
        "hypotheses": hypotheses[:8],
        "tests": tests[:12],
        "summary": f"Analyse centrée sur {system}. Nature priorisée : {nature}. Les preuves terrain modifient maintenant le classement des pistes.",
    }

# =========================================================
# UI
# =========================================================
st.sidebar.title("🔧 MecaTech IA")
st.sidebar.caption("Clean MVP v0.1.3 — Persistent console form")
page = st.sidebar.radio("Navigation", ["Login", "Console", "Résultat", "Validation humaine", "Historique", "Fleet", "Handoff"])
st.sidebar.divider()
st.sidebar.write("Principe : aucun diagnostic final sans validation humaine.")

if page == "Login":
    st.title("MecaTech IA")
    st.subheader("Workshop access")
    st.markdown("""
    <div class='card info'>Prototype MVP. La console sert à structurer un diagnostic terrain sans remplacer le mécanicien.</div>
    """, unsafe_allow_html=True)
    st.text_input("Technicien / ID", placeholder="Ex: garage-st-jérôme")
    st.text_input("PIN", type="password")
    st.button("Entrer", type="primary")

elif page == "Console":
    init_console_widgets()
    st.title("Console diagnostic")
    st.caption("Entre ce que tu sais. L’app classe les pistes; elle ne devine pas une cause finale. Les champs restent conservés pendant la navigation.")

    c1, c2, c3 = st.columns([1.1, 1.1, 1])
    with c1:
        st.selectbox("Type de machine", ["Chargeuse sur roues", "Camion lourd", "Niveleuse", "Excavatrice", "Tracteur", "Souffleuse", "Véhicule municipal", "Autre"], key="_machine_type", on_change=sync_console_from_widgets)
        st.text_input("Marque / modèle / année", placeholder="Ex: John Deere 772G 2007", key="_brand_model", on_change=sync_console_from_widgets)
        st.text_input("Heures / km", placeholder="Ex: 12 345 h", key="_hours_km", on_change=sync_console_from_widgets)
    with c2:
        st.selectbox("Système touché", SYSTEMS, key="_system", on_change=sync_console_from_widgets)
        st.selectbox("Nature suspectée", NATURES, key="_fault_nature", on_change=sync_console_from_widgets)
        st.text_area("Codes DTC / SPN / FMI", placeholder="Ex: TCU 522405.5 / aucun code actif", height=100, key="_dtcs", on_change=sync_console_from_widgets)
    with c3:
        st.multiselect("Preuves terrain cochées", EVIDENCE_OPTIONS, key="_checked_evidence", on_change=sync_console_from_widgets)

    st.text_area("Symptômes observés", placeholder="Décris le symptôme exact : quand, comment, témoins, comportement...", height=130, key="_symptoms", on_change=sync_console_from_widgets)
    st.text_area("Notes terrain / essais déjà faits", placeholder="Ex: en démanchant le capteur de pression, la pression sort, le frein s’applique et le témoin allume...", height=130, key="_field_notes", on_change=sync_console_from_widgets)
    st.text_area("Historique machine / travaux récents", placeholder="Pièces remplacées, problème déjà arrivé, contexte flotte...", height=90, key="_history", on_change=sync_console_from_widgets)

    b1, b2, b3 = st.columns([2, 1, 1])
    with b1:
        if st.button("🔍 Analyser le problème", type="primary", use_container_width=True):
            sync_console_from_widgets()
            st.session_state.analysis_counter += 1
            result = analyze()
            result["run_id"] = st.session_state.analysis_counter
            st.session_state.last_analysis = result
            st.session_state.cases.append(result)
            st.success(f"Analyse #{result['run_id']} générée — {result['input_hash']}")
    with b2:
        if st.button("💾 Sauvegarder", use_container_width=True):
            sync_console_from_widgets()
            st.success("Formulaire conservé dans la session. Tu peux changer de page et revenir à Console.")
    with b3:
        if st.button("🧹 Effacer le formulaire", use_container_width=True):
            clear_form()
            st.rerun()

    st.caption("MecaTech IA Clean MVP v0.1.3 · Read the fault. Find the cause. Fix it — once.")

elif page == "Résultat":
    st.title("Résultat diagnostic")
    result = st.session_state.last_analysis
    if not result:
        st.info("Aucune analyse encore. Va dans Console et clique Analyser.")
    else:
        st.caption(f"Analyse #{result['run_id']} · {result['timestamp']} · empreinte {result['input_hash']}")
        a, b, c = st.columns(3)
        a.metric("Système", result["system"])
        b.metric("Nature priorisée", result["active_nature"])
        c.metric("Sévérité", result["severity"])

        st.markdown(f"<div class='card danger'><b>Résumé :</b> {result['summary']}</div>", unsafe_allow_html=True)

        st.subheader("Déductions terrain")
        deductions = result["detected"]["deductions"]
        if deductions:
            for d in deductions:
                st.markdown(f"<div class='card info'><b>{d['title']}</b><br>{d['text']}</div>", unsafe_allow_html=True)
        else:
            st.warning("Aucune déduction terrain forte détectée. Ajoute des essais déjà faits ou coche une preuve terrain.")

        st.subheader("Hypothèses priorisées")
        for i, h in enumerate(result["hypotheses"], 1):
            st.markdown(f"""
            <div class='card'>
            <b>{i:02d}. {h['title']}</b><br>
            <span class='small'>Catégorie : {h['nature']}</span><br>
            <span class='score'>Score {h['score']}</span>
            </div>
            """, unsafe_allow_html=True)

        st.subheader("Informations détectées")
        c1, c2, c3 = st.columns(3)
        c1.write("**Faits**")
        c1.write(result["detected"]["facts"] or "Non détecté")
        c2.write("**Conditions**")
        c2.write(result["detected"]["conditions"] or "Non détecté")
        c3.write("**Preuves terrain**")
        c3.write(result["detected"]["evidence"] or "Non détecté")

        st.subheader("Tests recommandés")
        for i, t in enumerate(result["tests"], 1):
            st.write(f"{i}. {t}")

        if result["detected"]["missing"]:
            st.subheader("Informations manquantes")
            for m in result["detected"]["missing"]:
                st.info(m)

        st.download_button(
            "Exporter rapport JSON",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"mecatech_rapport_{result['run_id']}_{result['input_hash']}.json",
            mime="application/json",
        )

elif page == "Validation humaine":
    st.title("Validation humaine")
    result = st.session_state.last_analysis
    if not result:
        st.info("Aucune analyse à valider.")
    else:
        st.write(f"Analyse #{result['run_id']} — {result['system']} / {result['active_nature']}")
        verdict = st.radio("Verdict terrain", ["Non validé", "Confirmé", "Partiellement confirmé", "Faux / à corriger", "Inconclusif"])
        cause = st.text_area("Cause réelle trouvée / notes du mécanicien")
        if st.button("Sauvegarder validation", type="primary"):
            result["validation"] = {"verdict": verdict, "cause": cause, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            st.success("Validation sauvegardée dans la session.")

elif page == "Historique":
    st.title("Historique")
    if not st.session_state.cases:
        st.info("Aucune analyse dans cette session.")
    else:
        for r in reversed(st.session_state.cases):
            with st.expander(f"#{r['run_id']} · {r['system']} · {r['active_nature']} · {r['input_hash']}"):
                st.write(r["summary"])
                st.write("Hypothèse #1 :", r["hypotheses"][0]["title"] if r["hypotheses"] else "Aucune")
                st.json(r["snapshot"])

elif page == "Fleet":
    st.title("Fleet overview")
    st.info("Module futur : registre machine, statut, historique, rapports et priorités atelier.")
    st.dataframe([
        {"Unité": "JD-772G", "Système": "Frein", "Statut": "À valider", "Priorité": "Critique"},
        {"Unité": "ZW180", "Système": "Transmission", "Statut": "Analyse", "Priorité": "Élevée"},
        {"Unité": "D65", "Système": "PTO/accessoire", "Statut": "Historique", "Priorité": "Moyenne"},
    ], use_container_width=True)

elif page == "Handoff":
    st.title("Developer handoff")
    st.markdown("""
    ### Objectif
    MecaTech IA structure le raisonnement diagnostic sans assigner de cause finale.

    ### MVP inclus
    - Système touché
    - Nature suspectée
    - Preuves terrain cochées
    - Notes terrain pondérées fortement
    - Hypothèses classées par score
    - Validation humaine
    - Historique session

    ### Correction v0.1.2
    Les informations ajoutées dans **Notes terrain / essais déjà faits** modifient maintenant directement le classement.
    Les preuves terrain ont plus de poids que les simples symptômes.

    ### À ne pas faire
    - Ne pas prétendre remplacer le mécanicien.
    - Ne pas donner de cause finale sans validation humaine.
    - Ne pas laisser les mots-clés écraser le choix du mécanicien.
    """)
