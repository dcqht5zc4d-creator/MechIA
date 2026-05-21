import json
import re
from datetime import datetime
import hashlib

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_VERSION = "MecaTech IA Clean MVP v0.2.0 — API IA encadrée"

st.set_page_config(page_title="MecaTech IA", page_icon="🔧", layout="wide")

st.markdown(
    """
<style>
.stApp { background:#101214; color:#f2f2f2; }
section[data-testid="stSidebar"] { background:#151719; }
h1,h2,h3 { color:#f5f5f5; }
.block-container { padding-top:2rem; padding-bottom:3rem; }
.card { background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.11); border-radius: 14px; padding: 16px; margin: 10px 0; }
.warning { background:#2b1d14; border-left:5px solid #f59e0b; padding:14px; border-radius:8px; }
.danger { background:#2a1414; border-left:5px solid #ef4444; padding:14px; border-radius:8px; }
.ok { background:#14251a; border-left:5px solid #22c55e; padding:14px; border-radius:8px; }
.info { background:#111827; border-left:5px solid #38bdf8; padding:14px; border-radius:8px; }
.small { opacity:.82; font-size:.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

DEFAULT_FORM = {
    "machine_type": "Chargeuse sur roues",
    "brand_model": "",
    "hours_km": "",
    "system_affected": "Transmission",
    "fault_nature": "Inconnue / à déterminer",
    "dtcs": "",
    "symptoms": "",
    "field_evidence_checked": [],
    "field_notes": "",
    "history": "",
}

for k, v in DEFAULT_FORM.items():
    st.session_state.setdefault(f"console_{k}", v)

st.session_state.setdefault("analysis_counter", 0)
st.session_state.setdefault("last_analysis", None)
st.session_state.setdefault("case_history", [])
st.session_state.setdefault("human_validation", {})
st.session_state.setdefault("saved_form_at", None)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def snapshot_form() -> dict:
    return {k: st.session_state.get(f"console_{k}", v) for k, v in DEFAULT_FORM.items()}


def input_hash(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def clear_form():
    for k, v in DEFAULT_FORM.items():
        st.session_state[f"console_{k}"] = v
    st.session_state.saved_form_at = now_str()


def save_form():
    st.session_state.saved_form_at = now_str()


def extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Réponse API vide.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.I).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if not match:
        raise ValueError("Aucun JSON détecté dans la réponse API.")
    return json.loads(match.group(0))


def get_api_key():
    try:
        return st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return ""


def get_model():
    try:
        return st.secrets.get("OPENAI_MODEL", "gpt-4.1-mini")
    except Exception:
        return "gpt-4.1-mini"


FIELD_EVIDENCE_OPTIONS = [
    "Commande électrique présente",
    "Courant/voltage OK sous charge",
    "Ground/masse OK",
    "Faisceau/connecteurs vérifiés",
    "Bouger faisceau/connecteur change le symptôme",
    "Capteur manipulé/débranché change le symptôme",
    "Pression présente avant valve mais absente après valve",
    "Pression sort après manipulation",
    "Fonction marche avec courant direct",
    "Fonction ne marche pas avec courant direct",
    "Redémarrage/reset change temporairement le comportement",
    "Huile/niveau OK",
    "Filtre remplacé/OK",
    "Symptôme présent froid comme chaud",
    "Symptôme seulement à chaud",
    "Aucun code actif",
]

SYSTEMS = ["Transmission", "Frein", "Hydraulique", "Moteur", "Électrique", "Refroidissement", "Direction", "PTO / accessoires", "Autre / inconnu"]
FAULT_NATURES = ["Inconnue / à déterminer", "Mécanique", "Électrique / commande", "Hydraulique / pression", "Capteur / signal", "Module / logique", "Valve / solénoïde mécanique-hydraulique"]


def local_fallback_analysis(case: dict) -> dict:
    text = " ".join([
        str(case.get("system_affected", "")),
        str(case.get("fault_nature", "")),
        str(case.get("dtcs", "")),
        str(case.get("symptoms", "")),
        " ".join(case.get("field_evidence_checked", []) or []),
        str(case.get("field_notes", "")),
        str(case.get("history", "")),
    ]).lower()

    system = case.get("system_affected", "Autre / inconnu")
    selected_nature = case.get("fault_nature", "Inconnue / à déterminer")
    hypotheses = []
    evidence_used = []

    def add_h(title, nature, reason, score):
        hypotheses.append({
            "title": title,
            "nature": nature,
            "score": score,
            "reason": reason,
            "confirming_tests": [],
            "why_not_final": "Piste à confirmer par mesure terrain/OEM; aucune cause finale assignée.",
        })

    command_present = any(w in text for w in ["commande électrique présente", "courant", "voltage", "alimenté", "alimentation", "ground"])
    pressure_not_passing = any(w in text for w in ["pression ne passe", "ne laisse pas passer", "pression absente après", "absente apres", "valve", "solénoïde", "solenoide"])

    if command_present and pressure_not_passing:
        evidence_used.append("Commande électrique mentionnée + pression/réaction non transmise.")
        add_h("Solénoïde/valve alimenté mais bloqué mécaniquement ou hydrauliquement", "Valve / solénoïde mécanique-hydraulique", "Électricité présente ne confirme pas que la valve laisse passer la pression.", 95)
        add_h("Restriction, spool collé, obstruction ou fuite interne dans le circuit de commande", "Hydraulique / pression", "Le symptôme indique une réaction hydraulique absente ou non transmise.", 88)

    if any(w in text for w in ["capteur manipulé", "débranch", "debranch", "démanch", "demanch", "pression sort", "frein s’applique", "frein s'applique", "témoin allume"]):
        evidence_used.append("Manipulation capteur/connecteur modifie le comportement.")
        add_h("Capteur/signal/connecteur ou interprétation module influençant l’autorisation", "Capteur / signal", "Une action sur capteur/connecteur qui modifie le symptôme devient une preuve terrain importante.", 82)

    if "redémarrage" in text or "redemarrage" in text or "reset" in text or "repart" in text:
        evidence_used.append("Redémarrage/reset change ou ramène le comportement.")
        add_h("État logique module, interlock, protection ou défaut mémorisé", "Module / logique", "Un reset qui change le comportement oriente vers logique module/interlock ou état capteur.", 78)

    if selected_nature == "Mécanique":
        add_h(f"Inspection mécanique du système {system}", "Mécanique", "Le mécanicien a priorisé une nature mécanique; l’analyse ne doit pas être détournée par les mots courant/capteur seuls.", 75)

    if selected_nature != "Inconnue / à déterminer" and selected_nature not in [h["nature"] for h in hypotheses]:
        add_h(f"Piste priorisée par le mécanicien : {selected_nature}", selected_nature, "La nature suspectée choisie par le mécanicien doit orienter le classement.", 72)

    if not hypotheses:
        add_h(f"Diagnostic structuré du système {system}", selected_nature, "Données insuffisantes pour une orientation forte; garder une analyse méthodique.", 50)

    tests = [
        "Sécuriser la machine avant essai si frein/direction/propulsion impliqués.",
        "Comparer commande demandée vs réaction réelle.",
        "Mesurer alimentation et ground sous charge, pas seulement à vide.",
        "Mesurer pression avant/après valve ou solénoïde selon procédure OEM.",
        "Comparer données live : demande, autorisation, état capteur, état sortie module.",
        "Faire wiggle test connecteur/faisceau si une manipulation change le symptôme.",
        "Ne remplacer aucune pièce sans test de confirmation.",
    ]

    return {
        "analysis_mode": "fallback_local_no_api",
        "summary": "Analyse locale structurée. API IA non utilisée ou indisponible. Aucune cause finale assignée.",
        "system_affected": system,
        "fault_nature_interpreted": selected_nature,
        "risk_level": "Critique" if system == "Frein" else "À évaluer",
        "safety_warning": "Validation humaine obligatoire avant remise en service.",
        "detected_facts": evidence_used or ["Données lues, mais aucune preuve terrain forte détectée."],
        "field_evidence_used": case.get("field_evidence_checked", []) or [],
        "hypotheses": sorted(hypotheses, key=lambda h: h["score"], reverse=True)[:5],
        "contradictions_or_cautions": ["Présence de courant ≠ fonction mécanique/hydraulique confirmée.", "Code ou témoin seul ≠ cause finale."],
        "missing_information": ["Données live du module / scan tool", "Schéma ou procédure OEM", "Mesures objectives avant/après commande"],
        "recommended_next_tests": tests,
        "human_validation_required": True,
    }


SYSTEM_PROMPT = """
Tu es MecaTech IA, assistant de diagnostic mécanique pour équipements lourds.
Tu ne donnes jamais une cause finale certaine. Tu classes des hypothèses à vérifier.
Tu tiens compte des preuves terrain cochées et des notes terrain autant ou plus que les symptômes.

Règles mécaniques générales:
- Commande électrique présente + pression/mouvement absent = priorité après la commande: valve, solénoïde bloqué mécaniquement/hydrauliquement, restriction, obstruction, actionneur ou mécanisme.
- Électricité présente ne confirme pas le fonctionnement hydraulique/mécanique.
- Capteur manipulé/débranché + symptôme change = capteur, signal retour, connecteur, faisceau ou interprétation module monte en priorité.
- Courant direct active composant = composant aval probablement capable; vérifier commande, relais, module, interlock, faisceau amont.
- Courant direct n'active pas composant = actionneur, valve, pression, mécanique aval monte en priorité.
- Pression présente avant valve mais absente après valve = valve/spool/solénoïde/restriction monte en priorité.
- Reset/redémarrage change temporairement le comportement = logique module, interlock, défaut mémorisé ou état capteur à vérifier.
- Frein de stationnement incertain = risque critique.

Réponds seulement en JSON valide, sans markdown, selon cette structure:
{
  "analysis_mode": "api_ai",
  "summary": "string",
  "system_affected": "string",
  "fault_nature_interpreted": "string",
  "risk_level": "Faible|Moyen|Élevé|Critique|À évaluer",
  "safety_warning": "string",
  "detected_facts": ["string"],
  "field_evidence_used": ["string"],
  "hypotheses": [{"title":"string","nature":"string","score":0,"reason":"string","confirming_tests":["string"],"why_not_final":"string"}],
  "contradictions_or_cautions": ["string"],
  "missing_information": ["string"],
  "recommended_next_tests": ["string"],
  "human_validation_required": true
}
"""


def call_openai_analysis(case: dict) -> dict:
    api_key = get_api_key()
    model = get_model()
    if not api_key:
        result = local_fallback_analysis(case)
        result["summary"] = "Clé API absente. " + result["summary"]
        return result
    if OpenAI is None:
        result = local_fallback_analysis(case)
        result["summary"] = "Librairie openai absente dans requirements.txt. " + result["summary"]
        return result

    client = OpenAI(api_key=api_key)
    user_payload = {"case": case, "required_behavior": ["Analyse toutes les sections, surtout preuves terrain et notes terrain.", "Classe selon preuves terrain + choix du mécanicien.", "Ne donne aucune cause finale certaine."]}

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        temperature=0.2,
    )

    text = getattr(response, "output_text", None)
    if not text:
        try:
            text = response.output[0].content[0].text
        except Exception:
            text = str(response)

    parsed = extract_json(text)
    parsed.setdefault("analysis_mode", "api_ai")
    parsed.setdefault("human_validation_required", True)
    parsed.setdefault("hypotheses", [])
    parsed.setdefault("recommended_next_tests", [])
    return parsed


st.sidebar.title("🔧 MecaTech IA")
st.sidebar.caption("Clean MVP + API IA")
page = st.sidebar.radio("Navigation", ["Login", "Console", "Résultat", "Validation humaine", "Historique", "Fleet", "Handoff"])
st.sidebar.markdown("---")
st.sidebar.caption(f"API OpenAI : {'connectée' if get_api_key() else 'absente'}")
st.sidebar.caption("Principe : aucune cause finale sans validation humaine.")


if page == "Login":
    st.title("MecaTech IA")
    st.subheader("Workshop access")
    st.markdown("""<div class="card"><b>Objectif :</b> assistant de diagnostic mécanique structuré.<br><b>Rôle :</b> classer les pistes, pas remplacer le mécanicien.<br><b>Mode v0.2 :</b> analyse IA encadrée par API OpenAI + fallback local si l'API manque.</div>""", unsafe_allow_html=True)
    st.info("Va dans Console pour entrer un cas.")

elif page == "Console":
    st.title("Console diagnostic")
    st.caption("Entre ce que tu sais. L'app classe les pistes; elle ne devine pas une cause finale.")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.selectbox("Type de machine", ["Chargeuse sur roues", "Niveleuse", "Camion lourd", "Excavatrice", "Tracteur", "Souffleuse", "Véhicule municipal", "Autre"], key="console_machine_type")
        st.text_input("Marque / modèle / année", placeholder="Ex: John Deere 772G 2007", key="console_brand_model")
        st.text_input("Heures / km", placeholder="Ex: 12 345 h", key="console_hours_km")
    with col2:
        st.selectbox("Système touché", SYSTEMS, key="console_system_affected")
        st.selectbox("Nature suspectée", FAULT_NATURES, key="console_fault_nature")
        st.text_area("Codes DTC / SPN / FMI", placeholder="Ex: TCU 522405.5 / aucun code actif", height=100, key="console_dtcs")
    with col3:
        st.multiselect("Preuves terrain cochées", FIELD_EVIDENCE_OPTIONS, key="console_field_evidence_checked")
        st.markdown("""<div class="info small">Les preuves terrain ont un poids fort dans l'analyse.<br>Ex: commande présente + pression absente après valve ≠ panne électrique simple.</div>""", unsafe_allow_html=True)

    st.text_area("Symptômes observés", placeholder="Décris le symptôme exact : quand, comment, témoins, comportement...", height=130, key="console_symptoms")
    st.text_area("Notes terrain / essais déjà faits", placeholder="Ex: solénoïde alimenté mais ne laisse pas passer la pression; pression avant valve OK; frein reste appliqué...", height=140, key="console_field_notes")
    st.text_area("Historique machine / travaux récents", placeholder="Pièces remplacées, problème déjà arrivé, contexte flotte...", height=90, key="console_history")

    b1, b2, b3 = st.columns([2, 1, 1])
    with b1:
        if st.button("🔍 Analyser le problème", type="primary", use_container_width=True):
            save_form()
            st.session_state.analysis_counter += 1
            case = snapshot_form()
            case["analysis_number"] = st.session_state.analysis_counter
            case["timestamp"] = now_str()
            case["input_hash"] = input_hash(case)
            with st.spinner("Analyse IA encadrée en cours..."):
                try:
                    analysis = call_openai_analysis(case)
                except Exception as e:
                    analysis = local_fallback_analysis(case)
                    analysis["summary"] = f"Erreur API, fallback local utilisé : {e}"
            package = {"case": case, "analysis": analysis, "created_at": now_str()}
            st.session_state.last_analysis = package
            st.session_state.case_history.append(package)
            st.success(f"Analyse #{case['analysis_number']} générée. Va dans Résultat.")
    with b2:
        if st.button("💾 Sauvegarder", use_container_width=True):
            save_form()
            st.success(f"Formulaire sauvegardé à {st.session_state.saved_form_at}")
    with b3:
        if st.button("🧹 Effacer", use_container_width=True):
            clear_form()
            st.rerun()
    if st.session_state.saved_form_at:
        st.caption(f"Dernière sauvegarde du formulaire : {st.session_state.saved_form_at}")

elif page == "Résultat":
    st.title("Résultat diagnostic")
    package = st.session_state.last_analysis
    if not package:
        st.info("Aucune analyse. Va dans Console et clique Analyser.")
    else:
        case = package["case"]
        analysis = package["analysis"]
        st.caption(f"Analyse #{case.get('analysis_number')} — {case.get('timestamp')} — empreinte {case.get('input_hash')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Système", analysis.get("system_affected", case.get("system_affected", "")))
        c2.metric("Nature interprétée", analysis.get("fault_nature_interpreted", case.get("fault_nature", "")))
        c3.metric("Risque", analysis.get("risk_level", "À évaluer"))
        risk = str(analysis.get("risk_level", "")).lower()
        box_class = "danger" if "critique" in risk or "élevé" in risk else "warning" if "moyen" in risk or "évaluer" in risk else "ok"
        st.markdown(f"<div class='{box_class}'><b>Sécurité :</b> {analysis.get('safety_warning','Validation humaine obligatoire.')}</div>", unsafe_allow_html=True)
        st.markdown("### Résumé")
        st.write(analysis.get("summary", ""))
        st.markdown("### Faits et preuves utilisés")
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Faits détectés**")
            for x in analysis.get("detected_facts", []) or []:
                st.write(f"- {x}")
        with col_b:
            st.write("**Preuves terrain prises en compte**")
            for x in analysis.get("field_evidence_used", []) or []:
                st.write(f"- {x}")
        st.markdown("### Hypothèses priorisées — aucune cause finale assignée")
        for i, h in enumerate(analysis.get("hypotheses", []) or [], start=1):
            with st.expander(f"{i:02d}. {h.get('title','Hypothèse')} — {h.get('nature','')} — Score {h.get('score','?')}", expanded=(i == 1)):
                st.write("**Pourquoi cette piste :**")
                st.write(h.get("reason", ""))
                tests = h.get("confirming_tests", []) or []
                if tests:
                    st.write("**Tests de confirmation :**")
                    for t in tests:
                        st.write(f"- {t}")
                st.write("**Pourquoi ce n'est pas final :**")
                st.write(h.get("why_not_final", "Validation terrain requise."))
        st.markdown("### Prudences / contradictions")
        for x in analysis.get("contradictions_or_cautions", []) or []:
            st.warning(x)
        st.markdown("### Informations manquantes")
        for x in analysis.get("missing_information", []) or []:
            st.info(x)
        st.markdown("### Prochains tests recommandés")
        for i, t in enumerate(analysis.get("recommended_next_tests", []) or [], start=1):
            st.write(f"{i}. {t}")
        with st.expander("Voir l'entrée exacte analysée"):
            st.json(case)
        st.download_button("⬇️ Export rapport JSON", data=json.dumps(package, ensure_ascii=False, indent=2), file_name=f"mecatech_analysis_{case.get('analysis_number','x')}.json", mime="application/json")

elif page == "Validation humaine":
    st.title("Validation humaine")
    package = st.session_state.last_analysis
    if not package:
        st.info("Aucune analyse à valider.")
    else:
        case = package["case"]
        analysis = package["analysis"]
        key = case["input_hash"]
        st.write(f"Analyse #{case.get('analysis_number')} — {analysis.get('system_affected', case.get('system_affected'))}")
        st.write("**Hypothèse principale :**", (analysis.get("hypotheses") or [{}])[0].get("title", "—"))
        status = st.radio("Résultat terrain", ["Non validé", "Confirmé", "Partiellement confirmé", "Faux diagnostic", "Inconclusif"], key=f"validation_status_{key}")
        notes = st.text_area("Cause réelle trouvée / notes du mécanicien", key=f"validation_notes_{key}")
        if st.button("Sauvegarder validation", type="primary"):
            st.session_state.human_validation[key] = {"status": status, "notes": notes, "saved_at": now_str()}
            st.success("Validation sauvegardée dans la session.")

elif page == "Historique":
    st.title("Historique de session")
    if not st.session_state.case_history:
        st.info("Aucun historique pour cette session.")
    else:
        for package in reversed(st.session_state.case_history):
            case = package["case"]
            analysis = package["analysis"]
            with st.expander(f"#{case.get('analysis_number')} — {case.get('system_affected')} — {case.get('timestamp')} — {case.get('input_hash')}"):
                st.write("**Résumé :**", analysis.get("summary", ""))
                st.write("**Risque :**", analysis.get("risk_level", ""))
                st.write("**Hypothèse principale :**", (analysis.get("hypotheses") or [{}])[0].get("title", "—"))
                st.json(case)

elif page == "Fleet":
    st.title("Fleet")
    st.info("MVP : section visuelle seulement. Future version : machines, historique par numéro de série, work orders, coûts, rapports.")

elif page == "Handoff":
    st.title("Developer handoff")
    st.markdown("""
### MecaTech IA v0.2 — API IA encadrée

**Inclus**
- Console avec champs persistants.
- API IA pour analyse structurée.
- Fallback local si clé/API absente.
- Résultat structuré : système, nature, preuves, hypothèses, tests, prudences.
- Validation humaine.
- Historique de session.

**Règles essentielles**
- Pas de cause finale sans validation humaine.
- Les notes terrain et preuves cochées ont un poids fort.
- Commande électrique présente + pression/mouvement absent = vérifier valve/solénoïde mécanique-hydraulique, restriction, pression, actionneur.
- Web live non inclus dans v0.2.

**Prochaine version**
- v0.3 : bouton séparé de recherche web publique avec classement des sources A/B/C.
- v0.4 : documentation PDF/OEM autorisée + historique flotte.
""")

st.divider()
st.caption(APP_VERSION + " | Read the fault. Find the cause. Fix it — once.")
