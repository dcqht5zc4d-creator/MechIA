
import streamlit as st
from datetime import datetime
import hashlib
import json
import re
from typing import Dict, List, Tuple

# =========================================================
# MecaTech IA — Clean MVP v0.1.1
# Based on Claude Design handoff: system + nature + field evidence
# Fix: console form persistence across navigation
# =========================================================

st.set_page_config(
    page_title="MecaTech IA",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLE
# =========================================================
st.markdown(
    """
<style>
    .stApp {
        background: #0d1014;
        color: #e6e8ea;
    }

    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    h1, h2, h3 {
        color: #f4f4f4;
        letter-spacing: -0.02em;
    }

    .small-muted {
        color: #9aa3ad;
        font-size: 0.88rem;
    }

    .mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    .meca-card {
        background: #14181e;
        border: 1px solid #2a323c;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        margin-bottom: 14px;
    }

    .meca-card-strong {
        background: #1b2129;
        border: 1px solid #3a4350;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .risk-critical {
        background: rgba(224,83,61,0.12);
        border-left: 6px solid #e0533d;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 12px 0;
    }

    .risk-warn {
        background: rgba(245,166,35,0.12);
        border-left: 6px solid #f5a623;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 12px 0;
    }

    .risk-ok {
        background: rgba(92,168,92,0.12);
        border-left: 6px solid #5ca85c;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 12px 0;
    }

    .evidence-box {
        background: rgba(91,143,214,0.10);
        border-left: 6px solid #5b8fd6;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 12px 0;
    }

    .scorebar {
        width: 100%;
        height: 9px;
        background: #2a323c;
        border-radius: 99px;
        overflow: hidden;
        margin-top: 6px;
    }

    .scorefill {
        height: 100%;
        background: linear-gradient(90deg, #f5a623, #ff7a1a);
    }

    .tag {
        display: inline-block;
        border: 1px solid #3a4350;
        background: #1b2129;
        color: #d8d8d8;
        border-radius: 999px;
        padding: 4px 10px;
        margin: 3px 5px 3px 0;
        font-size: 0.82rem;
    }

    .tag-orange {
        border-color: #ff7a1a;
        color: #ffb27a;
        background: rgba(255,122,26,0.08);
    }

    .tag-blue {
        border-color: #5b8fd6;
        color: #a9c9f5;
        background: rgba(91,143,214,0.08);
    }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# DATA
# =========================================================

MACHINE_TYPES = [
    "Chargeuse sur roues",
    "Camion lourd",
    "Niveleuse",
    "Excavatrice",
    "Tracteur",
    "Souffleuse",
    "Véhicule municipal",
    "Autre",
]

SYSTEMS = [
    "Transmission",
    "Frein",
    "Hydraulique",
    "Moteur",
    "Électrique",
    "Refroidissement",
    "Direction",
    "PTO / accessoires",
    "Autre / inconnu",
]

FAULT_NATURES = [
    "Inconnue / à déterminer",
    "Mécanique",
    "Électrique / commande",
    "Hydraulique / pression",
    "Capteur / signal",
    "Module / logique",
]

FIELD_TEST_OPTIONS = [
    "Huile / niveau OK",
    "Filtre remplacé ou OK",
    "Courant présent",
    "Ground / masse OK",
    "Pression mesurée",
    "Capteur débranché ou manipulé",
    "Le symptôme change quand le capteur est manipulé",
    "Le symptôme change quand le faisceau est bougé",
    "Alimentation directe active le composant",
    "Alimentation directe ne change rien",
    "Redémarrage / reset change temporairement le comportement",
    "Aucun changement après pièce remplacée",
]

SYSTEM_PROFILES: Dict[str, Dict[str, List[str]]] = {
    "Transmission": {
        "Mécanique": [
            "Embrayage interne, train d’engrenage, arbre ou composant mécanique",
            "Usure ou dommage interne confirmé seulement après tests externes",
            "Défaut mécanique qui affecte la propulsion ou le rapport engagé",
        ],
        "Électrique / commande": [
            "Sélecteur, relais, sortie module, connecteur, alimentation ou ground",
            "Commande électrique qui décroche ou demande le neutre",
            "Faisceau soumis à vibration/eau/sel/chaleur",
        ],
        "Hydraulique / pression": [
            "Pression de commande instable ou insuffisante",
            "Valve, solénoïde hydraulique ou fuite interne",
            "Restriction ou perte de pression sous charge/température",
        ],
        "Capteur / signal": [
            "Capteur vitesse entrée/sortie ou signal de rapport incohérent",
            "Signal de sélecteur ou retour de position mal interprété",
            "Capteur alimenté mais valeur de retour incorrecte",
        ],
        "Module / logique": [
            "Module transmission en protection ou retour au neutre",
            "Condition d’autorisation non satisfaite",
            "État mémorisé qui revient après reset",
        ],
    },
    "Frein": {
        "Mécanique": [
            "Mécanisme de frein collé, usé, mal ajusté ou endommagé",
            "Linkage, piston, ressort, disque ou mouvement physique incomplet",
            "Frein capable de recevoir une commande, mais mouvement réel à confirmer",
        ],
        "Électrique / commande": [
            "Switch, relais, solénoïde, sortie module, alimentation ou ground",
            "Commande présente à vide mais non confirmée sous charge",
            "Faisceau/connecteur qui modifie l’état du frein",
        ],
        "Hydraulique / pression": [
            "Pression air/hydraulique insuffisante ou fuite interne",
            "Valve de frein ou circuit de pression à vérifier",
            "Pression présente à un point mais non transmise au mécanisme",
        ],
        "Capteur / signal": [
            "Capteur de pression, switch ou signal de retour incohérent",
            "Témoin qui ne représente pas l’état réel du frein",
            "Connecteur/faisceau du capteur influence l’état logique",
        ],
        "Module / logique": [
            "Interlock ou condition de sécurité non satisfaite",
            "TCU/ECU interprète mal l’état du frein ou du capteur",
            "Protection module qui bloque l’application ou la confirmation",
        ],
    },
    "Hydraulique": {
        "Mécanique": [
            "Valve collée, cylindre bloqué, fuite interne ou restriction physique",
            "Usure mécanique qui limite la fonction",
            "Mouvement réel incomplet malgré commande présente",
        ],
        "Électrique / commande": [
            "Commande de valve/solénoïde hydraulique instable",
            "Faisceau, connecteur ou sortie module de valve",
            "Autorisation électrique absente ou intermittente",
        ],
        "Hydraulique / pression": [
            "Pression insuffisante ou instable",
            "Pompe faible, cavitation, crépine, filtre ou huile contaminée",
            "Fuite interne ou valve qui bypass",
        ],
        "Capteur / signal": [
            "Capteur de pression différent du manomètre mécanique",
            "Signal capteur incohérent avec la réaction observée",
            "Lecture live qui ne suit pas la pression réelle",
        ],
        "Module / logique": [
            "Commande pilotée limitée par le contrôleur",
            "Condition de sécurité ou état machine qui bloque la fonction",
            "Mode protection hydraulique",
        ],
    },
    "Moteur": {
        "Mécanique": [
            "Compression, timing, restriction mécanique ou usure moteur",
            "Problème interne confirmé par tests de base",
            "Bruit, vibration ou fumée liée à un état mécanique",
        ],
        "Électrique / commande": [
            "Alimentation ECU, relais, injecteur commandé, faisceau ou ground",
            "Commande turbo/EGR/injection instable",
            "Connecteur ou capteur moteur intermittent",
        ],
        "Hydraulique / pression": [
            "Pression carburant/rail, alimentation carburant ou pression d’huile",
            "Restriction carburant ou pompe faible",
            "Pression qui décroche sous charge",
        ],
        "Capteur / signal": [
            "MAP/MAF/température/pression incohérent",
            "Capteur moteur qui provoque derate ou lecture erronée",
            "Signal hors plage sans preuve mécanique",
        ],
        "Module / logique": [
            "ECU en derate / protection",
            "DPF/SCR/EGR/post-traitement limite la puissance",
            "État logique moteur après code actif",
        ],
    },
    "Électrique": {
        "Mécanique": [
            "Composant commandé électriquement bloqué mécaniquement",
            "Actionneur reçoit une commande mais ne bouge pas",
            "Mouvement physique absent malgré commande mesurée",
        ],
        "Électrique / commande": [
            "Mauvaise masse, alimentation instable, relais, fusible ou connecteur",
            "Faisceau frotté, oxydé ou intermittent",
            "Chute de voltage sous charge",
        ],
        "Hydraulique / pression": [
            "Commande électrique correcte, réaction hydraulique absente",
            "Solénoïde actif mais pression aval manquante",
            "Circuit pression commandé électriquement à vérifier",
        ],
        "Capteur / signal": [
            "Capteur alimenté mais signal de retour incohérent",
            "Signal intermittent vers module",
            "Lecture live différente de la mesure terrain",
        ],
        "Module / logique": [
            "Communication CAN/J1939/J1708 ou module qui décroche",
            "Interlock qui bloque une sortie",
            "Module qui protège ou annule la commande",
        ],
    },
    "Refroidissement": {
        "Mécanique": [
            "Pompe à eau, thermostat, bouchon pression, fan ou airflow",
            "Radiateur obstrué ou circulation insuffisante",
            "Restriction mécanique du circuit",
        ],
        "Électrique / commande": [
            "Commande fan, relais, capteur température ou faisceau",
            "Fan non activé malgré condition",
            "Alimentation commande refroidissement",
        ],
        "Hydraulique / pression": [
            "Air dans le système, fuite, pression bouchon ou circulation coolant",
            "Cavitation ou pompe inefficace",
            "Perte de pression du circuit",
        ],
        "Capteur / signal": [
            "Capteur température ou lecture erronée",
            "Écart entre température réelle et donnée live",
            "Signal température instable",
        ],
        "Module / logique": [
            "ECU limite puissance à cause de température",
            "Commande fan ou protection gérée par module",
            "État logique de surchauffe",
        ],
    },
    "Direction": {
        "Mécanique": [
            "Articulation, pivot, bushing, cylindre ou jeu mécanique",
            "Blocage physique ou usure de direction",
            "Réaction gauche/droite asymétrique",
        ],
        "Électrique / commande": [
            "Valve pilotée, commande électrique ou faisceau direction",
            "Alimentation/ground d’une commande assistée",
            "Connecteur sensible aux vibrations",
        ],
        "Hydraulique / pression": [
            "Pression direction insuffisante ou instable",
            "Orbitrol/valve direction, fuite interne ou pompe",
            "Pression change selon régime/température",
        ],
        "Capteur / signal": [
            "Capteur angle/position/pression incohérent",
            "Signal de retour direction mal interprété",
            "Valeur live instable",
        ],
        "Module / logique": [
            "Module limite ou bloque la commande assistée",
            "Interlock ou sécurité direction",
            "Protection liée à vitesse/angle/condition",
        ],
    },
    "PTO / accessoires": {
        "Mécanique": [
            "Clutch, arbre, linkage ou accessoire bloqué",
            "Charge mécanique excessive",
            "Engagement mécanique incomplet",
        ],
        "Électrique / commande": [
            "Switch, relais, solénoïde, faisceau ou autorisation PTO",
            "Commande absente ou intermittente",
            "Sortie module à vérifier",
        ],
        "Hydraulique / pression": [
            "Pression hydraulique/pneumatique d’engagement insuffisante",
            "Valve ou circuit de commande PTO",
            "Fuite interne ou pression aval absente",
        ],
        "Capteur / signal": [
            "Capteur vitesse/position PTO incohérent",
            "Retour engagé/non engagé mal interprété",
            "Signal de rotation absent",
        ],
        "Module / logique": [
            "Interlock de sécurité ou condition d’autorisation PTO",
            "Module bloque l’engagement selon état machine",
            "Protection accessoire",
        ],
    },
}

DEFAULT_TESTS = {
    "Mécanique": [
        "Inspecter physiquement jeu, usure, blocage, ajustement et mouvement réel.",
        "Confirmer que la commande arrive au composant et comparer mouvement demandé vs mouvement réel.",
        "Valider mécaniquement avant de condamner un module.",
    ],
    "Électrique / commande": [
        "Mesurer alimentation et ground sous charge, pas seulement à vide.",
        "Vérifier relais, fusibles, sorties module, connecteurs et continuité.",
        "Faire un wiggle test pendant surveillance live.",
    ],
    "Hydraulique / pression": [
        "Mesurer pression réelle avec manomètre selon procédure.",
        "Comparer pression demandée vs pression réelle.",
        "Vérifier restriction, fuite interne, valve, pompe et retour.",
    ],
    "Capteur / signal": [
        "Mesurer alimentation, ground et signal de retour du capteur.",
        "Comparer la valeur capteur réelle avec les données live du module.",
        "Manipuler connecteur/faisceau du capteur pendant surveillance live.",
    ],
    "Module / logique": [
        "Lire états live du module : demande, autorisation, interlock, protection.",
        "Comparer comportement avant/après reset.",
        "Vérifier les conditions de sécurité qui bloquent la commande.",
    ],
}

# =========================================================
# SESSION STATE
# =========================================================

if "signed_in" not in st.session_state:
    st.session_state.signed_in = True
if "analysis_counter" not in st.session_state:
    st.session_state.analysis_counter = 0
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "history" not in st.session_state:
    st.session_state.history = []
if "validation_log" not in st.session_state:
    st.session_state.validation_log = []

# Persistent console form state.
# Streamlit removes widget state when widgets are not rendered on another page,
# so we keep a permanent copy separate from widget keys.
CONSOLE_DEFAULTS = {
    "machine_type": MACHINE_TYPES[0],
    "brand_model": "",
    "hours_km": "",
    "system": SYSTEMS[0],
    "fault_nature": FAULT_NATURES[0],
    "dtcs": "",
    "field_tests": [],
    "symptoms": "",
    "field_notes": "",
    "history": "",
}

if "console_form" not in st.session_state:
    st.session_state.console_form = CONSOLE_DEFAULTS.copy()

def reset_console_form():
    st.session_state.console_form = CONSOLE_DEFAULTS.copy()

# =========================================================
# HELPERS
# =========================================================

def hash_input(data: Dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()


def split_clean(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"[\n.;•\-]+", text)
    return [p.strip() for p in parts if p.strip()]


def has_any(text: str, words: List[str]) -> bool:
    low = text.lower()
    return any(w.lower() in low for w in words)


def extract_codes(text: str) -> List[str]:
    patterns = [
        r"\b[A-Z]{2,6}\s*\d{3,6}\.\d{1,2}\b",
        r"\bSPN\s*\d{2,6}\s*FMI\s*\d{1,2}\b",
        r"\b[PUBC]\d{4}\b",
    ]
    found = []
    up = text.upper()
    for p in patterns:
        found.extend(re.findall(p, up))
    return list(dict.fromkeys([x.strip() for x in found]))


def infer_nature_from_text(text: str) -> str:
    if has_any(text, ["mécanique", "mecanique", "bloqué", "bloque", "usé", "use", "cassé", "casse", "jeu", "linkage", "ajustement"]):
        return "Mécanique"
    if has_any(text, ["pression", "hydraulique", "air", "valve", "pompe", "manomètre", "manometre"]):
        return "Hydraulique / pression"
    if has_any(text, ["capteur", "signal", "témoin", "temoin", "voyant", "lecture"]):
        return "Capteur / signal"
    if has_any(text, ["module", "tcu", "ecu", "interlock", "autorisation", "reset", "redémarrage", "redemarrage", "protection"]):
        return "Module / logique"
    if has_any(text, ["courant", "voltage", "ground", "masse", "relais", "fusible", "solénoïde", "solenoide", "commande", "connecteur", "faisceau"]):
        return "Électrique / commande"
    return "Inconnue / à déterminer"


def detect_conditions(text: str) -> List[str]:
    conditions = []
    if has_any(text, ["intermittent", "parfois", "des fois", "revient", "recommence", "pas toujours"]):
        conditions.append("Symptôme intermittent / revient")
    if has_any(text, ["constant", "toujours", "tout le temps", "permanent"]):
        conditions.append("Symptôme constant")
    if has_any(text, ["à chaud", "a chaud", "chaud", "après 15", "apres 15", "température"]):
        conditions.append("Condition liée à la chaleur / température")
    if has_any(text, ["à froid", "a froid", "froid", "démarrage", "demarrage"]):
        conditions.append("Condition à froid / démarrage")
    if has_any(text, ["sous charge", "en charge", "pente", "travail fort"]):
        conditions.append("Condition sous charge")
    if has_any(text, ["reset", "redémarre", "redemarre", "arrête repart", "arrete repart"]):
        conditions.append("Reset ou redémarrage change le comportement")
    return conditions


def detect_field_evidence(text: str, selected_tests: List[str]) -> List[Dict[str, str]]:
    evidence = []

    for test in selected_tests:
        evidence.append({
            "title": test,
            "deduction": "Test terrain déclaré par le mécanicien. À utiliser comme preuve de contexte, pas comme conclusion finale.",
            "nature": None,
        })

    if has_any(text, ["capteur", "sensor"]) and has_any(text, ["débranch", "debranch", "démanch", "demanch", "manipul", "bougé", "bouger"]):
        if has_any(text, ["fonctionne", "s'applique", "s applique", "pression sort", "pression est sortie", "témoin allume", "temoin allume", "lumière allume", "lumiere allume"]):
            evidence.append({
                "title": "Action sur capteur → comportement change",
                "deduction": "Une action sur le capteur change le comportement. Prioriser capteur, signal de retour, connecteur, faisceau ou interprétation module.",
                "nature": "Capteur / signal",
            })

    if has_any(text, ["faisceau", "connecteur", "fil", "wiggle"]) and has_any(text, ["change", "revient", "disparaît", "disparait", "fonctionne", "coupe"]):
        evidence.append({
            "title": "Action sur faisceau/connecteur → symptôme change",
            "deduction": "Le changement lié au faisceau augmente la priorité connecteur, continuité, masse, alimentation et vibration.",
            "nature": "Électrique / commande",
        })

    if has_any(text, ["courant direct", "alimenté direct", "alimente direct", "12v direct", "24v direct", "jumper", "shunt"]):
        if has_any(text, ["fonctionne", "marche", "s'applique", "s applique", "s'engage", "s engage", "clic", "bouge"]):
            evidence.append({
                "title": "Alimentation directe active le composant",
                "deduction": "Le composant en aval est probablement capable de fonctionner. Prioriser commande, relais, module, autorisation ou faisceau amont.",
                "nature": "Électrique / commande",
            })
        elif has_any(text, ["rien", "aucun changement", "pas de réaction", "pas de reaction", "ne fonctionne pas"]):
            evidence.append({
                "title": "Alimentation directe ne produit aucune réaction",
                "deduction": "Prioriser actionneur, valve, pression ou mouvement mécanique en aval.",
                "nature": "Mécanique",
            })

    if has_any(text, ["redémarre", "redemarre", "reset", "arrête repart", "arrete repart", "repart la machine"]):
        evidence.append({
            "title": "Redémarrage / reset modifie temporairement le symptôme",
            "deduction": "Prioriser logique module, état mémorisé, interlock, capteur incohérent ou protection temporaire.",
            "nature": "Module / logique",
        })

    if has_any(text, ["aucun changement", "pas changé", "pas changer", "même problème", "meme probleme"]) and has_any(text, ["remplacé", "remplace", "filtre", "huile", "capteur", "solénoïde", "solenoide"]):
        evidence.append({
            "title": "Intervention faite sans changement",
            "deduction": "La piste déjà testée descend en priorité. Chercher mesure objective, commande, signal ou condition non vérifiée.",
            "nature": None,
        })

    # Deduplicate by title
    seen = set()
    deduped = []
    for e in evidence:
        if e["title"] not in seen:
            seen.add(e["title"])
            deduped.append(e)
    return deduped


def detect_facts(text: str, selected_tests: List[str]) -> List[str]:
    facts = []
    codes = extract_codes(text)
    if codes:
        facts.append("Codes détectés : " + ", ".join(codes))
    if has_any(text, ["aucun code", "pas de code", "no code"]):
        facts.append("Aucun code rapporté")
    if has_any(text, ["témoin", "temoin", "voyant", "lumière", "lumiere"]):
        facts.append("Témoin / voyant mentionné")
    if has_any(text, ["ne s'applique pas", "ne s applique pas", "ne s'engage pas", "ne s engage pas"]):
        facts.append("Fonction ne s’applique / ne s’engage pas")
    if has_any(text, ["pression sort", "pression est sortie", "pression sortie"]):
        facts.append("Pression ou réaction observée après manipulation")
    if has_any(text, ["tombe au neutre", "perd la propulsion"]):
        facts.append("Perte de propulsion / tombe au neutre")
    if has_any(text, ["huile ok", "niveau ok", "filtre ok", "ground ok", "masse ok", "courant ok"]):
        facts.append("Vérifications de base déclarées OK")
    for t in selected_tests:
        facts.append("Test coché : " + t)
    return list(dict.fromkeys(facts))


def risk_for(system: str) -> Tuple[str, str]:
    if system == "Frein":
        return "Critique", "Système de frein/immobilisation : ne pas remettre en service sans confirmation du fonctionnement réel."
    if system in ["Transmission", "Direction"]:
        return "Élevé", "Risque opérationnel : valider avant utilisation normale."
    if system == "Refroidissement":
        return "Élevé", "Risque de dommage moteur si surchauffe ou perte de coolant."
    return "Moyen", "Analyse préliminaire. Validation terrain requise avant réparation ou remise en service."


def score_hypotheses(system: str, selected_nature: str, text: str, evidence: List[Dict[str, str]]) -> List[Dict[str, object]]:
    profile = SYSTEM_PROFILES.get(system, SYSTEM_PROFILES["Électrique"])
    inferred = infer_nature_from_text(text)
    active_nature = selected_nature if selected_nature != "Inconnue / à déterminer" else inferred

    # field evidence can override unknown but never overrides explicit mechanic choice
    if selected_nature == "Inconnue / à déterminer":
        for e in evidence:
            if e.get("nature"):
                active_nature = e["nature"]
                break

    order = []
    if active_nature in profile:
        order.append(active_nature)

    for e in evidence:
        n = e.get("nature")
        if n and n in profile and n not in order:
            order.append(n)

    for n in ["Capteur / signal", "Électrique / commande", "Module / logique", "Hydraulique / pression", "Mécanique"]:
        if n in profile and n not in order:
            order.append(n)

    hypotheses = []
    rank_index = 0

    for nature in order:
        for h in profile[nature]:
            base = 55 if nature == active_nature else 38
            if rank_index == 0:
                base += 15
            if any(e.get("nature") == nature for e in evidence):
                base += 15
            if selected_nature == nature:
                base += 10
            if selected_nature != "Inconnue / à déterminer" and nature != selected_nature:
                base -= 5

            score = max(20, min(95, base - rank_index * 3))
            why_parts = [f"Système: {system}", f"Nature: {nature}"]
            if nature == active_nature:
                why_parts.append("priorité active")
            if any(e.get("nature") == nature for e in evidence):
                why_parts.append("appuyé par preuve terrain")

            hypotheses.append({
                "name": h,
                "nature": nature,
                "score": score,
                "why": " · ".join(why_parts),
            })
            rank_index += 1

    return hypotheses[:8], active_nature


def build_next_tests(system: str, active_nature: str, evidence: List[Dict[str, str]]) -> List[str]:
    tests = []

    for e in evidence:
        if "capteur" in e["title"].lower():
            tests += [
                "Mesurer alimentation, ground et signal de retour du capteur.",
                "Comparer la valeur du capteur dans les données live avec l’état réel.",
                "Faire wiggle test du connecteur/faisceau du capteur pendant surveillance live.",
            ]
        elif "faisceau" in e["title"].lower() or "connecteur" in e["title"].lower():
            tests += [
                "Inspecter pins, corrosion, tension des terminaux et frottement du faisceau.",
                "Mesurer chute de voltage sous charge.",
                "Tester continuité/résistance pendant mouvement du faisceau.",
            ]
        elif "alimentation directe" in e["title"].lower():
            tests += [
                "Comparer alimentation directe avec alimentation commandée par le système.",
                "Vérifier relais, sortie module, interlock et conditions d’autorisation.",
            ]
        elif "redémarrage" in e["title"].lower():
            tests += [
                "Lire codes avant et après redémarrage.",
                "Comparer les états live avant/après reset.",
                "Identifier quelle condition revient au défaut.",
            ]

    tests += DEFAULT_TESTS.get(active_nature, [])
    tests += [
        "Lire codes actifs, inactifs et historiques avec l’outil adapté.",
        "Comparer commande demandée vs réaction réelle.",
        "Consulter schéma/procédure OEM avant de condamner une pièce.",
    ]

    return list(dict.fromkeys(tests))[:10]


def missing_info(text: str) -> List[str]:
    missing = []
    if not extract_codes(text) and not has_any(text, ["aucun code", "pas de code"]):
        missing.append("Codes actifs/inactifs ou mention claire qu’il n’y en a pas.")
    if not has_any(text, ["live", "donnée live", "données live", "paramètre", "parametre"]):
        missing.append("Données live pertinentes selon le système.")
    if not has_any(text, ["pression", "voltage", "signal", "ground", "masse", "manomètre", "manometre"]):
        missing.append("Mesure objective : pression, voltage, signal ou ground.")
    if not has_any(text, ["manuel", "oem", "schéma", "schema", "procédure", "procedure"]):
        missing.append("Référence manuel/schéma/procédure OEM.")
    return missing


def run_diagnostic(input_data: Dict) -> Dict:
    st.session_state.analysis_counter += 1

    text = " ".join([
        str(input_data.get("machine_type", "")),
        str(input_data.get("brand_model", "")),
        str(input_data.get("hours_km", "")),
        str(input_data.get("system", "")),
        str(input_data.get("fault_nature", "")),
        str(input_data.get("dtcs", "")),
        str(input_data.get("symptoms", "")),
        str(input_data.get("field_notes", "")),
        str(input_data.get("history", "")),
    ])

    evidence = detect_field_evidence(text, input_data.get("field_tests", []))
    hypotheses, active_nature = score_hypotheses(
        input_data["system"],
        input_data["fault_nature"],
        text,
        evidence,
    )
    severity, risk_message = risk_for(input_data["system"])

    fingerprint = hash_input(input_data)

    return {
        "analysis_no": f"A-{st.session_state.analysis_counter:04d}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fingerprint": fingerprint,
        "system": input_data["system"],
        "selected_nature": input_data["fault_nature"],
        "active_nature": active_nature,
        "severity": severity,
        "risk_message": risk_message,
        "facts": detect_facts(text, input_data.get("field_tests", [])),
        "conditions": detect_conditions(text),
        "evidence": evidence,
        "hypotheses": hypotheses,
        "next_tests": build_next_tests(input_data["system"], active_nature, evidence),
        "missing": missing_info(text),
        "raw_input": input_data,
    }


def export_report(analysis: Dict) -> str:
    lines = [
        "# Rapport MecaTech IA",
        "",
        f"Analyse: {analysis['analysis_no']}",
        f"Date: {analysis['timestamp']}",
        f"Empreinte entrée: {analysis['fingerprint']}",
        "",
        f"Système: {analysis['system']}",
        f"Nature sélectionnée: {analysis['selected_nature']}",
        f"Nature priorisée: {analysis['active_nature']}",
        f"Sévérité: {analysis['severity']}",
        "",
        "## Avertissement",
        analysis["risk_message"],
        "",
        "## Hypothèses priorisées",
    ]

    for i, h in enumerate(analysis["hypotheses"], 1):
        lines.append(f"{i}. {h['name']} — score {h['score']} — {h['why']}")

    lines += ["", "## Preuves terrain"]
    if analysis["evidence"]:
        for e in analysis["evidence"]:
            lines.append(f"- {e['title']}: {e['deduction']}")
    else:
        lines.append("- Aucune preuve terrain structurée détectée.")

    lines += ["", "## Tests recommandés"]
    for i, t in enumerate(analysis["next_tests"], 1):
        lines.append(f"{i}. {t}")

    lines += ["", "## Informations manquantes"]
    for m in analysis["missing"]:
        lines.append(f"- {m}")

    lines += [
        "",
        "## Principe",
        "MecaTech IA structure le diagnostic. La décision finale appartient au mécanicien qualifié.",
    ]
    return "\n".join(lines)


# =========================================================
# UI
# =========================================================

with st.sidebar:
    st.markdown("## 🔧 MecaTech IA")
    st.caption("Clean MVP v0.1.1 · structured diagnostic assistant")
    page = st.radio(
        "Navigation",
        ["Login", "Console", "Résultat", "Validation humaine", "Historique", "Fleet", "Handoff"],
        index=1,
    )
    st.divider()
    st.caption("Principe : aucun diagnostic final sans validation humaine.")

if page == "Login":
    st.title("MecaTech IA")
    st.subheader("Workshop access")
    st.markdown('<div class="meca-card">Accès atelier simulé pour MVP. Le système ne remplace pas un mécanicien qualifié.</div>', unsafe_allow_html=True)
    tech = st.text_input("Technicien", "D. Castonguay")
    shop = st.text_input("Atelier", "Atelier municipal")
    if st.button("Entrer dans MecaTech IA", type="primary"):
        st.session_state.signed_in = True
        st.success(f"Connecté : {tech} — {shop}")

elif page == "Console":
    st.title("Console diagnostic")
    st.caption("Entre ce que tu sais. L’app classe les pistes; elle ne devine pas une cause finale.")

    st.markdown(
        '<div class="meca-card">💾 Les champs de cette console sont maintenant conservés quand tu changes de page. '
        'Tu peux aller voir Résultat, revenir ici, modifier une phrase et relancer l’analyse.</div>',
        unsafe_allow_html=True,
    )

    saved = st.session_state.console_form

    # Buttons outside the form so clearing is intentional and separate from analysis.
    clear_cols = st.columns([0.22, 0.78])
    with clear_cols[0]:
        if st.button("🧹 Effacer le formulaire", use_container_width=True):
            reset_console_form()
            st.session_state.last_analysis = None
            st.rerun()

    with st.form("diagnostic_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            machine_type = st.selectbox(
                "Type de machine",
                MACHINE_TYPES,
                index=MACHINE_TYPES.index(saved.get("machine_type", MACHINE_TYPES[0]))
                if saved.get("machine_type", MACHINE_TYPES[0]) in MACHINE_TYPES else 0,
            )
            brand_model = st.text_input(
                "Marque / modèle / année",
                value=saved.get("brand_model", ""),
                placeholder="Ex: John Deere 772G 2007",
            )
            hours_km = st.text_input(
                "Heures / km",
                value=saved.get("hours_km", ""),
                placeholder="Ex: 12 345 h",
            )

        with c2:
            system = st.selectbox(
                "Système touché",
                SYSTEMS,
                index=SYSTEMS.index(saved.get("system", SYSTEMS[0]))
                if saved.get("system", SYSTEMS[0]) in SYSTEMS else 0,
            )
            fault_nature = st.selectbox(
                "Nature suspectée",
                FAULT_NATURES,
                index=FAULT_NATURES.index(saved.get("fault_nature", FAULT_NATURES[0]))
                if saved.get("fault_nature", FAULT_NATURES[0]) in FAULT_NATURES else 0,
            )
            dtcs = st.text_area(
                "Codes DTC / SPN / FMI",
                value=saved.get("dtcs", ""),
                height=108,
                placeholder="Ex: TCU 522405.5 / aucun code actif",
            )

        with c3:
            st.markdown("##### Preuves terrain cochées")
            default_tests = [x for x in saved.get("field_tests", []) if x in FIELD_TEST_OPTIONS]
            field_tests = st.multiselect(
                "Tests déjà faits",
                FIELD_TEST_OPTIONS,
                default=default_tests,
                label_visibility="collapsed",
            )

        symptoms = st.text_area(
            "Symptômes observés",
            value=saved.get("symptoms", ""),
            height=150,
            placeholder="Décris le symptôme exact : quand, comment, témoins, comportement...",
        )

        field_notes = st.text_area(
            "Notes terrain / essais déjà faits",
            value=saved.get("field_notes", ""),
            height=150,
            placeholder="Ex: en démanchant le capteur de pression, la pression sort, le frein s’applique et le témoin allume...",
        )

        history = st.text_area(
            "Historique machine / travaux récents",
            value=saved.get("history", ""),
            height=95,
            placeholder="Pièces remplacées, problème déjà arrivé, contexte flotte...",
        )

        b1, b2 = st.columns([0.7, 0.3])
        with b1:
            submitted = st.form_submit_button("🔍 Analyser le problème", type="primary", use_container_width=True)
        with b2:
            saved_only = st.form_submit_button("💾 Sauvegarder", use_container_width=True)

    input_data = {
        "machine_type": machine_type,
        "brand_model": brand_model,
        "hours_km": hours_km,
        "system": system,
        "fault_nature": fault_nature,
        "dtcs": dtcs,
        "field_tests": field_tests,
        "symptoms": symptoms,
        "field_notes": field_notes,
        "history": history,
    }

    if submitted or saved_only:
        # Permanent copy survives page changes.
        st.session_state.console_form = input_data.copy()

    if saved_only and not submitted:
        st.success("Formulaire sauvegardé. Tu peux changer de page et revenir sans perdre les textes.")

    if submitted:
        analysis = run_diagnostic(input_data)
        st.session_state.last_analysis = analysis
        st.session_state.history.append(analysis)
        st.success(f"Analyse {analysis['analysis_no']} générée. Va dans l’onglet Résultat.")

elif page == "Résultat":
    st.title("Résultat diagnostic")
    analysis = st.session_state.last_analysis

    if not analysis:
        st.info("Aucune analyse. Va dans Console et lance une analyse.")
    else:
        st.caption(f"{analysis['analysis_no']} · {analysis['timestamp']} · empreinte {analysis['fingerprint']}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Système", analysis["system"])
        m2.metric("Nature priorisée", analysis["active_nature"])
        m3.metric("Sévérité", analysis["severity"])
        m4.metric("Branches", len(analysis["hypotheses"]))

        risk_class = "risk-critical" if analysis["severity"] in ["Critique", "Élevé"] else "risk-warn"
        st.markdown(f'<div class="{risk_class}"><b>Avertissement :</b> {analysis["risk_message"]}</div>', unsafe_allow_html=True)

        st.markdown("## Hypothèses priorisées — aucune cause finale assignée")
        st.caption("Le score sert seulement à ordonner les pistes. Ce n’est pas une probabilité.")

        for i, h in enumerate(analysis["hypotheses"], 1):
            st.markdown('<div class="meca-card-strong">', unsafe_allow_html=True)
            cols = st.columns([0.08, 0.62, 0.18])
            cols[0].markdown(f"### {i:02d}")
            cols[1].markdown(f"**{h['name']}**")
            cols[1].caption(h["why"])
            cols[2].metric("Score", h["score"])
            st.markdown(f'<div class="scorebar"><div class="scorefill" style="width:{h["score"]}%"></div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("## Preuves terrain détectées")
        if analysis["evidence"]:
            for e in analysis["evidence"]:
                st.markdown(f'<div class="evidence-box"><b>{e["title"]}</b><br>{e["deduction"]}</div>', unsafe_allow_html=True)
        else:
            st.write("Aucune preuve terrain structurée détectée.")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("## Faits détectés")
            for f in analysis["facts"] or ["Aucun fait structuré détecté."]:
                st.markdown(f"- {f}")

            st.markdown("## Conditions détectées")
            for c in analysis["conditions"] or ["Aucune condition détectée."]:
                st.markdown(f"- {c}")

        with c2:
            st.markdown("## Informations manquantes")
            for m in analysis["missing"] or ["Aucune information manquante majeure détectée."]:
                st.info(m)

        st.markdown("## Tests recommandés")
        for i, t in enumerate(analysis["next_tests"], 1):
            st.markdown(f"{i}. {t}")

        report = export_report(analysis)
        st.download_button(
            "⬇️ Télécharger rapport Markdown",
            data=report,
            file_name=f"mecatech_ia_{analysis['analysis_no']}.md",
            mime="text/markdown",
        )

elif page == "Validation humaine":
    st.title("Validation humaine obligatoire")
    analysis = st.session_state.last_analysis

    if not analysis:
        st.info("Aucune analyse à valider.")
    else:
        st.markdown('<div class="meca-card">MecaTech IA ne ferme jamais un diagnostic seul. Le mécanicien confirme, corrige ou rejette.</div>', unsafe_allow_html=True)

        st.write("**Analyse :**", analysis["analysis_no"])
        st.write("**Hypothèse #1 :**", analysis["hypotheses"][0]["name"])

        decision = st.radio(
            "Décision du mécanicien",
            ["Non validé", "Confirmé", "Partiellement correct", "Rejeté", "Inconclusif — autres tests requis"],
            horizontal=False,
        )

        final_cause = st.text_area("Cause finale écrite par le mécanicien", placeholder="Ex: capteur de pression parking brake signal intermittent...")
        parts = st.text_input("Pièces / matériel", placeholder="Ex: capteur, connecteur, harnais, aucun...")
        labor = st.text_input("Temps de travail", placeholder="Ex: 1.5 h")
        notes = st.text_area("Notes de validation")

        if st.button("Sauvegarder validation", type="primary"):
            record = {
                "analysis_no": analysis["analysis_no"],
                "decision": decision,
                "final_cause": final_cause,
                "parts": parts,
                "labor": labor,
                "notes": notes,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state.validation_log.append(record)
            st.success("Validation sauvegardée dans cette session.")

elif page == "Historique":
    st.title("Historique de session")

    if not st.session_state.history:
        st.info("Aucune analyse dans cette session.")
    else:
        for a in reversed(st.session_state.history):
            with st.expander(f"{a['analysis_no']} · {a['system']} · {a['active_nature']} · {a['timestamp']}"):
                st.write("**Empreinte :**", a["fingerprint"])
                st.write("**Top hypothèse :**", a["hypotheses"][0]["name"])
                st.write("**Risque :**", a["risk_message"])
                st.write("**Preuves terrain :**", ", ".join([e["title"] for e in a["evidence"]]) or "Aucune")

    st.markdown("## Validations")
    if not st.session_state.validation_log:
        st.caption("Aucune validation encore.")
    else:
        st.json(st.session_state.validation_log)

elif page == "Fleet":
    st.title("Fleet overview")
    st.caption("Vue flotte simulée pour le MVP.")
    rows = [
        {"Unit": "GR-772G", "Type": "Niveleuse", "Health": "À vérifier", "Open DTC": 2, "Status": "Bay 1"},
        {"Unit": "ZW180", "Type": "Chargeuse", "Health": "Critique", "Open DTC": 0, "Status": "Down"},
        {"Unit": "M2-14", "Type": "Camion lourd", "Health": "OK", "Open DTC": 0, "Status": "Route"},
        {"Unit": "D65", "Type": "Souffleuse", "Health": "Maintenance", "Open DTC": 1, "Status": "Shop"},
    ]
    st.dataframe(rows, use_container_width=True)

elif page == "Handoff":
    st.title("Developer handoff — Clean MVP")
    st.markdown(
        """
### Purpose
MecaTech IA is a structured diagnostic assistant for mechanics. It does not replace a mechanic and does not invent a final cause.

### MVP workflow
1. Enter machine, system, suspected fault nature.
2. Enter codes, symptoms, field tests and history.
3. The rules engine extracts facts, field evidence and conditions.
4. Hypotheses are ranked.
5. Mechanic validates or rejects the result.

### Core model
- **System affected**: what part of the machine is involved.
- **Fault nature**: mechanical, command/electrical, hydraulic/pressure, sensor/signal, module/logic.
- **Field evidence**: action → reaction → deduction.
- **Human validation**: mandatory before closure.

### Not included yet
- OEM connector
- scan tool / live J1939 data
- persistent database
- web search
- automatic final cause
- parts ordering / warranty workflow

### Next steps
- Store analyses in a database.
- Add PDF export.
- Add manual/OEM document search.
- Add authenticated users and roles.
- Add fleet history by VIN/unit ID.
"""
    )

st.divider()
st.caption("MecaTech IA Clean MVP v0.1.1 · Read the fault. Find the cause. Fix it — once.")
