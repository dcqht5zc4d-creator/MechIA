
import streamlit as st



from datetime import datetime



import hashlib



import json



import re



# =========================================================



# CONFIG



# =========================================================



st.set_page_config(



    page_title="MecaTech IA",



    page_icon="🔧",



    layout="wide"



)



# =========================================================



# STYLE



# =========================================================



st.markdown("""



<style>



    .stApp {



        background-color: #101214;



        color: #f2f2f2;



    }



    h1, h2, h3 {



        color: #f5f5f5;



    }



    .block-container {



        padding-top: 2rem;



        padding-bottom: 3rem;



    }



    .danger-box {



        background: #2a1414;



        border-left: 5px solid #e55353;



        padding: 14px;



        border-radius: 8px;



        margin-bottom: 12px;



    }



    .warning-box {



        background: #2b1d14;



        border-left: 5px solid #c77b30;



        padding: 14px;



        border-radius: 8px;



        margin-bottom: 12px;



    }



    .ok-box {



        background: #14251a;



        border-left: 5px solid #52b788;



        padding: 14px;



        border-radius: 8px;



        margin-bottom: 12px;



    }



    .info-box {



        background: #151a20;



        border-left: 5px solid #4dabf7;



        padding: 14px;



        border-radius: 8px;



        margin-bottom: 12px;



    }



</style>



""", unsafe_allow_html=True)



# =========================================================



# SESSION STATE



# =========================================================



if "cases" not in st.session_state:



    st.session_state.cases = []



if "last_analysis" not in st.session_state:



    st.session_state.last_analysis = None



if "analysis_counter" not in st.session_state:



    st.session_state.analysis_counter = 0



# =========================================================



# OUTILS



# =========================================================



def make_hash(data: dict) -> str:



    raw = json.dumps(data, ensure_ascii=False, sort_keys=True)



    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]



def contains_any(text: str, words: list[str]) -> bool:



    text = text.lower()



    return any(word.lower() in text for word in words)



def extract_dtcs(text: str) -> list[str]:



    if not text:



        return []



    patterns = [



        r"\b[A-Z]{2,5}\s*\d{3,6}\.\d{1,2}\b",



        r"\bSPN\s*\d{3,6}\s*FMI\s*\d{1,2}\b",



        r"\bP\d{4}\b",



        r"\bU\d{4}\b",



        r"\bC\d{4}\b",



        r"\bB\d{4}\b",



    ]



    results = []



    upper_text = text.upper()



    for pattern in patterns:



        results.extend(re.findall(pattern, upper_text))



    return list(dict.fromkeys(results))



def split_lines(text: str) -> list[str]:



    if not text:



        return []



    raw = re.split(r"[\n.;]+", text)



    return [x.strip() for x in raw if x.strip()]



# =========================================================



# MODULES GÉNÉRAUX



# =========================================================



SYSTEM_MODULES = {



    "Transmission": {



        "risk": "Élevé si la machine perd la propulsion, tombe au neutre ou change de comportement en mouvement.",



        "hypotheses": [



            "Commande électrique / logique de transmission",



            "Sélecteur, faisceau, connecteur, masse ou alimentation intermittente",



            "Capteur de vitesse entrée/sortie ou information incohérente",



            "Pression de commande, valve, solénoïde ou embrayage interne",



            "Défaut mécanique interne à confirmer seulement après tests externes"



        ],



        "tests": [



            "Lire codes actifs, inactifs et historiques avec outil compatible.",



            "Comparer données live : rapport demandé, rapport engagé, vitesse entrée, vitesse sortie.",



            "Mesurer alimentation et ground du module sous charge.",



            "Faire wiggle test du faisceau, connecteurs et sélecteur pendant surveillance live.",



            "Vérifier relais, fusibles, connecteurs exposés eau/sel/vibration.",



            "Mesurer pression de commande selon procédure OEM si disponible.",



            "Confirmer si le problème est présent en marche avant, reculons, toutes vitesses, chaud/froid."



        ]



    },



    "Hydraulique": {



        "risk": "Moyen à élevé selon la fonction touchée, la pression et la possibilité de mouvement incontrôlé.",



        "hypotheses": [



            "Pression hydraulique insuffisante ou instable",



            "Restriction filtre, crépine, huile contaminée ou mauvaise viscosité",



            "Valve de contrôle qui colle, fuite interne ou commande pilotée incorrecte",



            "Capteur de pression ou lecture électronique incohérente",



            "Pompe faible, cavitation ou alimentation d’huile insuffisante"



        ],



        "tests": [



            "Vérifier niveau, qualité, odeur, contamination et température d’huile.",



            "Contrôler filtre, crépine et présence de limaille.",



            "Mesurer pression principale, standby, pilotage et pression de fonction.",



            "Comparer temps de cycle avec spécifications.",



            "Isoler la fonction touchée et vérifier fuite interne possible.",



            "Comparer lecture capteur avec manomètre mécanique.",



            "Vérifier si le problème change avec température, charge ou régime moteur."



        ]



    },



    "Moteur": {



        "risk": "Moyen à élevé si perte de puissance, surchauffe, pression d’huile ou fumée anormale.",



        "hypotheses": [



            "Restriction air, carburant ou échappement",



            "Pression carburant, rail, pompe ou injecteur à vérifier",



            "Turbo, EGR, DPF/SCR ou post-traitement limitant la puissance",



            "Capteur moteur ou faisceau donnant une lecture incohérente",



            "Problème mécanique moteur à confirmer par tests de base"



        ],



        "tests": [



            "Lire codes actifs/inactifs moteur.",



            "Vérifier pression carburant, restriction air, boost, EGT et charge moteur.",



            "Comparer données live à froid et à chaud.",



            "Inspecter filtre air, filtre carburant, lignes et connecteurs capteurs.",



            "Vérifier commande turbo/EGR/DPF/SCR si applicable.",



            "Contrôler pression d’huile, température coolant et restriction échappement.",



            "Confirmer si le problème apparaît sous charge, au ralenti, à chaud ou au démarrage."



        ]



    },



    "Électrique": {



        "risk": "Variable, mais élevé si le défaut provoque arrêt, comportement intermittent ou perte de commande.",



        "hypotheses": [



            "Mauvaise masse ou alimentation instable",



            "Connecteur oxydé, fil cassé, faisceau frotté ou intermittent",



            "Relais, fusible, alimentation module ou circuit sous charge",



            "Capteur alimenté mais signal de retour incohérent",



            "Communication CAN/J1939/J1708 ou module qui décroche"



        ],



        "tests": [



            "Mesurer voltage source et chute de voltage sous charge.",



            "Contrôler grounds principaux et secondaires.",



            "Inspecter connecteurs exposés eau, sel, vibration, chaleur.",



            "Faire wiggle test pendant surveillance live.",



            "Vérifier alimentation, ground et signal de retour des capteurs.",



            "Vérifier codes de communication et état réseau CAN/J1939/J1708.",



            "Comparer le schéma électrique avec les points réellement mesurés."



        ]



    },



    "Frein": {



        "risk": "Critique si frein de service ou stationnement incertain. Immobilisation recommandée jusqu’à validation.",



        "hypotheses": [



            "Commande électrique, logique de sécurité ou condition d’autorisation non satisfaite",



            "Capteur de pression, switch, témoin ou signal de retour incohérent",



            "Solénoïde/valve alimenté mais non fonctionnel mécaniquement",



            "Pression air/hydraulique insuffisante ou fuite interne",



            "Mécanisme de frein collé, usé, mal ajusté ou endommagé"



        ],



        "tests": [



            "Immobiliser la machine si le frein est incertain.",



            "Lire codes actifs/inactifs liés au frein, TCU, ECU ou contrôleur machine.",



            "Vérifier commande demandée vs état réel dans les données live.",



            "Mesurer alimentation, ground et signal de retour capteur/switch.",



            "Tester solénoïde ou valve sous charge, pas seulement présence de courant.",



            "Mesurer pression air/hydraulique du circuit concerné.",



            "Inspecter mécaniquement frein, linkage, ajustement, usure et blocage."



        ]



    },



    "Refroidissement": {



        "risk": "Élevé si surchauffe ou perte de coolant. Risque de dommage moteur.",



        "hypotheses": [



            "Radiateur obstrué, airflow insuffisant ou fan inefficace",



            "Thermostat, pompe à eau ou circulation coolant insuffisante",



            "Air dans le système, bouchon pression ou fuite externe/interne",



            "Capteur température ou lecture erronée",



            "Charge moteur excessive ou problème secondaire causant chaleur"



        ],



        "tests": [



            "Vérifier niveau coolant, concentration, pression et fuite.",



            "Inspecter radiateur, fan, courroie, shroud et obstruction extérieure.",



            "Comparer température entrée/sortie radiateur.",



            "Tester thermostat, bouchon pression et circulation.",



            "Comparer lecture capteur avec température externe fiable.",



            "Vérifier si la surchauffe apparaît au ralenti, sous charge ou en déplacement."



        ]



    },



    "Direction": {



        "risk": "Élevé si perte de contrôle, coups, direction dure ou comportement imprévisible.",



        "hypotheses": [



            "Pression hydraulique de direction insuffisante ou instable",



            "Valve orbitrol/commande direction qui colle ou fuit",



            "Cylindre de direction avec fuite interne ou jeu mécanique",



            "Capteur/commande électronique direction incohérente",



            "Articulation, pivot, bushing ou composant mécanique usé"



        ],



        "tests": [



            "Vérifier niveau/qualité d’huile hydraulique et contamination.",



            "Mesurer pression direction selon procédure.",



            "Comparer réaction gauche/droite, froid/chaud, ralenti/régime.",



            "Inspecter cylindres, pivots, articulation, bushings et jeu.",



            "Vérifier valve direction/orbitrol et fuite interne possible.",



            "Lire codes et données live si direction assistée électroniquement."



        ]



    },



    "PTO / accessoires": {



        "risk": "Variable, élevé si équipement entraîné peut bouger ou engager de façon imprévue.",



        "hypotheses": [



            "Commande électrique/PTO non autorisée ou condition de sécurité absente",



            "Solénoïde, relais, switch ou faisceau PTO intermittent",



            "Pression hydraulique/pneumatique insuffisante pour engagement",



            "Embrayage PTO, arbre, clutch ou composant mécanique usé",



            "Capteur de position/vitesse PTO incohérent"



        ],



        "tests": [



            "Vérifier conditions d’autorisation PTO selon machine.",



            "Lire codes liés à PTO/accessoire.",



            "Mesurer alimentation, ground et commande solénoïde/relais.",



            "Vérifier pression de commande si hydraulique/pneumatique.",



            "Surveiller données live : demande PTO, état engagé, vitesse.",



            "Inspecter mécaniquement arbre, clutch, linkage et sécurité."



        ]



    }



}



# =========================================================



# DÉTECTION GÉNÉRALE



# =========================================================



def detect_general_facts(machine, symptoms, dtcs, context, history) -> dict:



    text = f"{machine} {symptoms} {dtcs} {context} {history}".lower()



    dtc_list = extract_dtcs(text)



    facts = []



    conditions = []



    tests_done = []



    missing = []



    risk_flags = []



    # Conditions



    if contains_any(text, ["intermittent", "parfois", "des fois", "recommence", "revient", "pas toujours"]):



        conditions.append("Intermittent / revient")



    if contains_any(text, ["constant", "toujours", "tout le temps", "permanent"]):



        conditions.append("Constant")



    if contains_any(text, ["à chaud", "chaud", "température", "après 15 minutes", "après 20 minutes"]):



        conditions.append("À chaud / température")



    if contains_any(text, ["à froid", "froid", "démarrage"]):



        conditions.append("À froid / démarrage")



    if contains_any(text, ["froid comme à chaud", "froide ou chaude", "à froid comme à chaud"]):



        conditions.append("Présent froid comme chaud")



    if contains_any(text, ["sous charge", "en charge", "charge", "pente", "travail fort"]):



        conditions.append("Sous charge")



    if contains_any(text, ["ralenti", "idle"]):



        conditions.append("Au ralenti")



    if contains_any(text, ["peu importe la vitesse", "toutes les vitesses", "tous les rapports"]):



        conditions.append("Toutes vitesses / tous rapports")



    # Symptômes / faits



    if contains_any(text, ["pas de code", "aucun code", "aucun défaut", "no code", "pas d'erreur"]):



        facts.append("Aucun code rapporté")



    if dtc_list:



        facts.append("Codes présents")



    if contains_any(text, ["voyant", "témoin", "temoin", "lumière", "lumiere", "warning"]):



        facts.append("Voyant / témoin mentionné")



    if contains_any(text, ["ne s'allume pas", "ne s allume pas", "pas de lumière", "pas de lumiere"]):



        facts.append("Témoin ne s’allume pas")



    if contains_any(text, ["ne fonctionne pas", "fonctionne pas", "ne marche pas", "pas de réaction"]):



        facts.append("Fonction ne répond pas")



    if contains_any(text, ["ne s'applique pas", "ne s applique pas", "ne s'engage pas", "ne s engage pas"]):



        facts.append("Ne s’applique / ne s’engage pas")



    if contains_any(text, ["ne relâche pas", "ne relache pas", "reste engagé", "reste engage"]):



        facts.append("Ne relâche pas / reste engagé")



    if contains_any(text, ["tombe au neutre", "tombe au neutral", "perd la propulsion"]):



        facts.append("Perte de propulsion / tombe au neutre")



    if contains_any(text, ["bruit", "cogne", "claque", "gronde", "siffle", "vibration"]):



        facts.append("Bruit / vibration mentionné")



    if contains_any(text, ["fuite", "coule", "perte d'huile", "perte huile", "leak"]):



        facts.append("Fuite mentionnée")



    if contains_any(text, ["chauffe", "surchauffe", "température haute", "overheat"]):



        facts.append("Surchauffe / température élevée")



    if contains_any(text, ["perte puissance", "manque de force", "boucanne", "fumée", "fumee"]):



        facts.append("Perte de puissance / fumée")



    if contains_any(text, ["reset", "redémarre", "redemarre", "arrête repart", "arrete repart"]):



        facts.append("Reset / redémarrage change le comportement")



    # Tests déjà faits



    if contains_any(text, ["huile ok", "niveau huile ok", "niveau d’huile ok", "qualité huile ok", "huile propre"]):



        tests_done.append("Huile / niveau déclaré OK")



    if contains_any(text, ["filtre ok", "filtre remplacé", "filtre change", "filtre changé", "filtre neuf"]):



        tests_done.append("Filtre déclaré OK/remplacé")



    if contains_any(text, ["courant ok", "voltage ok", "alimentation ok", "courant sur"]):



        tests_done.append("Courant / alimentation déclaré OK")



    if contains_any(text, ["pression ok", "pression bonne"]):



        tests_done.append("Pression déclarée OK")



    if contains_any(text, ["solénoïde", "solenoide"]):



        tests_done.append("Solénoïde mentionné")



    if contains_any(text, ["capteur"]):



        tests_done.append("Capteur mentionné")



    if contains_any(text, ["faisceau", "connecteur", "ground", "masse", "wiggle"]):



        tests_done.append("Faisceau/connecteur/masse mentionné")



    # Risques



    if contains_any(text, ["frein", "brake", "stationnement", "parking brake"]):



        risk_flags.append("Système de freinage ou immobilisation impliqué")



    if contains_any(text, ["tombe au neutre", "perd la propulsion", "direction", "ne freine pas"]):



        risk_flags.append("Risque opérationnel ou sécurité")



    # Manquants



    if not dtc_list and "Aucun code rapporté" not in facts:



        missing.append("Codes actifs/inactifs ou mention claire qu’il n’y en a pas")



    if not contains_any(text, ["année", "202", "201", "200", "modèle", "modele"]):



        missing.append("Année/modèle exact si non indiqué")



    if not contains_any(text, ["heures", "hrs", "km", "h "]):



        missing.append("Heures/km de la machine")



    if not contains_any(text, ["donnée live", "données live", "live data", "paramètre", "parametre"]):



        missing.append("Données live pertinentes selon le système")



    if not contains_any(text, ["schéma", "schema", "manuel", "oem", "procédure", "procedure"]):



        missing.append("Référence manuel/schéma OEM")



    return {



        "dtcs": dtc_list,



        "facts": list(dict.fromkeys(facts)),



        "conditions": list(dict.fromkeys(conditions)),



        "tests_done": list(dict.fromkeys(tests_done)),



        "missing": list(dict.fromkeys(missing)),



        "risk_flags": list(dict.fromkeys(risk_flags)),



        "raw_lines": split_lines(symptoms + "\n" + context + "\n" + history)



    }



def choose_primary_system(selected_system: str, text: str) -> str:



    if selected_system != "Autre / inconnu":



        return selected_system



    t = text.lower()



    system_keywords = {



        "Frein": ["frein", "brake", "stationnement", "parking brake"],



        "Transmission": ["transmission", "zf", "rapport", "neutre", "embraye"],



        "Hydraulique": ["hydraulique", "pompe", "pression", "cylindre", "valve"],



        "Moteur": ["moteur", "diesel", "turbo", "injecteur", "dpf", "egr"],



        "Électrique": ["électrique", "courant", "voltage", "faisceau", "connecteur", "capteur", "can"],



        "Refroidissement": ["radiateur", "coolant", "surchauffe", "thermostat", "fan"],



        "Direction": ["direction", "steering", "articulation", "orbitrol"],



        "PTO / accessoires": ["pto", "prise de force", "accessoire", "souffleuse", "blower"]



    }



    for system, words in system_keywords.items():



        if contains_any(t, words):



            return system



    return "Inconnu"



def build_hypotheses(primary_system: str, detected: dict) -> list[dict]:



    module = SYSTEM_MODULES.get(primary_system)



    if not module:



        return [



            {



                "title": "Information insuffisante pour orienter le diagnostic",



                "support": [



                    "Aucun système clair n’a été sélectionné ou détecté.",



                    "Les symptômes doivent être reliés à un système mécanique précis."



                ],



                "limits": [



                    "Ajouter système principal, codes, conditions, tests déjà faits et comportement exact."



                ]



            }



        ]



    facts = detected["facts"]



    tests_done = detected["tests_done"]



    conditions = detected["conditions"]



    hypotheses = []



    for item in module["hypotheses"]:



        support = [



            f"Système principal : {primary_system}.",



            "Symptôme/faits observés : " + ", ".join(facts) if facts else "Peu de faits confirmés dans l’entrée.",



            "Conditions : " + ", ".join(conditions) if conditions else "Conditions de panne à préciser.",



            "Tests déjà faits : " + ", ".join(tests_done) if tests_done else "Tests déjà faits non précisés."



        ]



        limits = [



            "Hypothèse à vérifier, pas conclusion finale.",



            "Confirmer avec mesures, données live, schéma ou procédure OEM.",



            "Ne pas remplacer de pièce sans test de confirmation."



        ]



        hypotheses.append({



            "title": item,



            "support": support,



            "limits": limits



        })



    return hypotheses



def build_universal_tests(primary_system: str, detected: dict) -> list[str]:



    base_tests = [



        "Sécuriser la machine et confirmer si elle peut être utilisée sans risque.",



        "Reformuler le symptôme exact : ce qui arrive, quand, combien de fois, dans quelles conditions.",



        "Lire codes actifs, inactifs et historiques avec l’outil adapté.",



        "Vérifier les bases : niveaux, qualité fluide, alimentation, grounds, connecteurs visibles.",



        "Reproduire le problème de façon contrôlée si sécuritaire.",



        "Comparer commande demandée vs réaction réelle avec données live si disponibles."



    ]



    module = SYSTEM_MODULES.get(primary_system)



    if module:



        specific_tests = module["tests"]



    else:



        specific_tests = [



            "Identifier le système principal avant de conclure.",



            "Ajouter données live ou mesures objectives.",



            "Comparer avec schéma/manuel OEM."



        ]



    return list(dict.fromkeys(base_tests + specific_tests))



def determine_severity(primary_system: str, detected: dict) -> tuple[str, str]:



    risk_flags = detected["risk_flags"]



    facts = detected["facts"]



    if primary_system == "Frein":



        return (



            "Critique",



            "Frein ou immobilisation impliqué : ne pas remettre en service tant que le fonctionnement réel n’est pas confirmé."



        )



    if "Risque opérationnel ou sécurité" in risk_flags:



        return (



            "Élevé",



            "Risque opérationnel : diagnostic et validation requis avant utilisation normale."



        )



    if primary_system in ["Transmission", "Direction"]:



        return (



            "Élevé",



            SYSTEM_MODULES.get(primary_system, {}).get("risk", "Risque élevé à valider.")



        )



    if "Surchauffe / température élevée" in facts:



        return (



            "Élevé",



            "Surchauffe ou température élevée : risque de dommage si ignoré."



        )



    if primary_system in SYSTEM_MODULES:



        return (



            "Moyen à élevé",



            SYSTEM_MODULES[primary_system]["risk"]



        )



    return (



        "À évaluer",



        "Données insuffisantes. Analyse préliminaire seulement."



    )



def build_prudence(primary_system: str, detected: dict) -> list[str]:



    prudence = []



    if detected["dtcs"]:



        prudence.append("Codes détectés : utiliser la description OEM exacte avant de conclure. Le code seul ne suffit pas.")



    if "Aucun code rapporté" in detected["facts"]:



        prudence.append("Aucun code ne veut pas dire aucun problème. Une panne mécanique, hydraulique ou électrique peut ne pas être mémorisée.")



    if "Courant / alimentation déclaré OK" in detected["tests_done"]:



        prudence.append("Courant présent ne confirme pas le fonctionnement réel : vérifier signal de retour, ground, charge et activation mécanique.")



    if "Filtre déclaré OK/remplacé" in detected["tests_done"] or "Huile / niveau déclaré OK" in detected["tests_done"]:



        prudence.append("Entretien de base déclaré OK : passer aux tests de commande, pression, signal, faisceau et données live.")



    if "Intermittent / revient" in detected["conditions"]:



        prudence.append("Panne intermittente : prioriser vibration, chaleur, humidité, connecteurs, masses et alimentation.")



    if primary_system == "Frein":



        prudence.append("Pour un frein, la validation mécanique réelle prime sur le témoin ou le courant mesuré.")



    prudence.append("MecaTech IA structure le diagnostic; la décision finale appartient au mécanicien qualifié.")



    return list(dict.fromkeys(prudence))



def confidence_label(detected: dict) -> str:



    score = 0



    if detected["dtcs"]:



        score += 2



    if detected["facts"]:



        score += 1



    if detected["conditions"]:



        score += 1



    if detected["tests_done"]:



        score += 1



    if len(detected["raw_lines"]) >= 3:



        score += 1



    if score <= 1:



        return "Préliminaire — données limitées"



    if score <= 3:



        return "Structurée — nécessite tests"



    return "Moyenne — validation terrain/OEM requise"



# =========================================================



# MOTEUR GÉNÉRAL V0.4



# =========================================================



def analyze_case(machine, symptoms, dtcs, context, history, selected_system):



    text = f"{machine} {symptoms} {dtcs} {context} {history}"



    primary_system = choose_primary_system(selected_system, text)



    detected = detect_general_facts(machine, symptoms, dtcs, context, history)



    severity, risk = determine_severity(primary_system, detected)



    hypotheses = build_hypotheses(primary_system, detected)



    tests = build_universal_tests(primary_system, detected)



    prudence = build_prudence(primary_system, detected)



    if primary_system == "Inconnu":



        summary = "Les informations ne permettent pas encore d’identifier clairement le système principal."



    else:



        summary = (



            f"Analyse générale centrée sur le système : {primary_system}. "



            "Le moteur ne conclut pas à une pièce défectueuse; il structure les pistes et les tests à effectuer."



        )



    return {



        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),



        "version": "v0.4",



        "primary_system": primary_system,



        "summary": summary,



        "dtcs": detected["dtcs"],



        "facts": detected["facts"],



        "conditions": detected["conditions"],



        "tests_done": detected["tests_done"],



        "missing": detected["missing"],



        "risk_flags": detected["risk_flags"],



        "severity": severity,



        "risk": risk,



        "hypotheses": hypotheses,



        "tests": tests,



        "prudence": prudence,



        "confidence_label": confidence_label(detected),



    }



# =========================================================



# HEADER



# =========================================================



st.title("🔧 MecaTech IA")



st.caption("Prototype MVP v0.4 — moteur général modulaire de diagnostic")



col1, col2, col3, col4 = st.columns(4)



with col1:



    st.metric("Version", "v0.4")



with col2:



    st.metric("Mode", "Moteur général")



with col3:



    st.metric("Analyses", st.session_state.analysis_counter)



with col4:



    st.metric("Décision finale", "Mécanicien")



st.divider()



# =========================================================



# SIDEBAR



# =========================================================



st.sidebar.title("Navigation")



page = st.sidebar.radio(



    "Menu",



    ["Diagnostic", "Historique", "Validation humaine", "À propos"]



)



# =========================================================



# PAGE DIAGNOSTIC



# =========================================================



if page == "Diagnostic":



    st.header("Console diagnostic atelier")



    st.markdown("""



    <div class="info-box">



    Version v0.4 : moteur général modulaire. Le système choisi par le mécanicien reste prioritaire.



    L’app structure le raisonnement au lieu de deviner une pièce.



    </div>



    """, unsafe_allow_html=True)



    c1, c2 = st.columns(2)



    with c1:



        machine_type = st.selectbox(



            "Type de machine",



            [



                "Chargeuse sur roues",



                "Camion lourd",



                "Niveleuse",



                "Excavatrice",



                "Tracteur",



                "Souffleuse",



                "Véhicule municipal",



                "Autre"



            ],



            key="machine_type"



        )



        brand_model = st.text_input(



            "Marque / modèle / année",



            placeholder="Ex: John Deere 772G 2007, Hitachi ZW180 2020",



            key="brand_model"



        )



        hours_km = st.text_input(



            "Heures / km",



            placeholder="Ex: 12 908 h ou inconnu",



            key="hours_km"



        )



    with c2:



        system = st.selectbox(



            "Système principal",



            [



                "Transmission",



                "Hydraulique",



                "Moteur",



                "Électrique",



                "Frein",



                "Refroidissement",



                "Direction",



                "PTO / accessoires",



                "Autre / inconnu"



            ],



            key="system"



        )



        dtcs = st.text_area(



            "Codes DTC / SPN / FMI",



            placeholder="Ex: TCU 522405.5 / SPN 3719 FMI 16 / aucun code actif",



            height=120,



            key="dtcs"



        )



    symptoms = st.text_area(



        "Symptômes observés",



        placeholder="Décris le problème : ce qui arrive, quand, conditions, bruit, témoin, comportement...",



        height=170,



        key="symptoms"



    )



    context = st.text_area(



        "Contexte terrain / tests déjà faits",



        placeholder="Ex: huile OK, filtre remplacé, courant au solénoïde OK, pression non testée, problème chaud/froid...",



        height=140,



        key="context"



    )



    history = st.text_area(



        "Historique machine connu",



        placeholder="Travaux récents, pièces remplacées, problème déjà arrivé, notes du technicien...",



        height=110,



        key="history"



    )



    st.divider()



    if st.button("🔍 Analyser le problème", type="primary", use_container_width=True):



        st.session_state.analysis_counter += 1



        machine = f"{machine_type} | {brand_model} | {hours_km} | {system}"



        input_snapshot = {



            "machine_type": machine_type,



            "brand_model": brand_model,



            "hours_km": hours_km,



            "system": system,



            "dtcs": dtcs,



            "symptoms": symptoms,



            "context": context,



            "history": history,



        }



        input_hash = make_hash(input_snapshot)



        analysis = analyze_case(



            machine=machine,



            symptoms=symptoms,



            dtcs=dtcs,



            context=context,



            history=history,



            selected_system=system



        )



        analysis["run_id"] = st.session_state.analysis_counter



        analysis["input_hash"] = input_hash



        analysis["input_snapshot"] = input_snapshot



        case = {



            "machine": machine,



            "analysis": analysis,



            "symptoms": symptoms,



            "context": context,



            "dtcs": dtcs,



            "history": history,



            "human_validation": "Non validé",



            "real_cause": ""



        }



        st.session_state.last_analysis = case



        st.session_state.cases.append(case)



        st.success(f"Nouvelle analyse #{analysis['run_id']} générée à {analysis['timestamp']}")



    if st.session_state.last_analysis:



        case = st.session_state.last_analysis



        analysis = case["analysis"]



        st.subheader("Résultat diagnostic")



        st.caption(



            f"Analyse #{analysis['run_id']} — {analysis['timestamp']} — empreinte entrée : {analysis['input_hash']}"



        )



        a, b, c = st.columns(3)



        with a:



            st.metric("Système principal", analysis["primary_system"])



        with b:



            st.metric("Sévérité", analysis["severity"])



        with c:



            st.metric("Certitude", analysis["confidence_label"])



        if analysis["severity"] in ["Critique", "Élevé"]:



            st.markdown(f"<div class='danger-box'><b>Risque :</b> {analysis['risk']}</div>", unsafe_allow_html=True)



        elif analysis["severity"] in ["Moyen", "Moyen à élevé"]:



            st.markdown(f"<div class='warning-box'><b>Risque :</b> {analysis['risk']}</div>", unsafe_allow_html=True)



        else:



            st.markdown(f"<div class='ok-box'><b>Risque :</b> {analysis['risk']}</div>", unsafe_allow_html=True)



        st.markdown("### Résumé")



        st.write(analysis["summary"])



        st.markdown("### Informations détectées")



        col_a, col_b, col_c = st.columns(3)



        with col_a:



            st.write("**Faits observés :**")



            st.write(analysis["facts"] if analysis["facts"] else "Non détecté")



        with col_b:



            st.write("**Conditions :**")



            st.write(analysis["conditions"] if analysis["conditions"] else "Non détecté")



        with col_c:



            st.write("**Tests déjà faits :**")



            st.write(analysis["tests_done"] if analysis["tests_done"] else "Non détecté")



        st.markdown("### Codes détectés")



        st.write(analysis["dtcs"] if analysis["dtcs"] else "Aucun code structuré détecté")



        st.markdown("### Hypothèses à vérifier")



        for i, h in enumerate(analysis["hypotheses"], start=1):



            with st.expander(f"{i}. {h['title']}", expanded=(i == 1)):



                st.write("**Ce qui appuie cette piste :**")



                for item in h["support"]:



                    st.write(f"- {item}")



                st.write("**Limites / ce qui manque :**")



                for item in h["limits"]:



                    st.write(f"- {item}")



        st.markdown("### Tests recommandés dans l’ordre")



        for i, test in enumerate(analysis["tests"], start=1):



            st.write(f"{i}. {test}")



        if analysis["prudence"]:



            st.markdown("### Points de prudence")



            for item in analysis["prudence"]:



                st.warning(item)



        if analysis["missing"]:



            st.markdown("### Informations manquantes utiles")



            for item in analysis["missing"]:



                st.info(item)



        with st.expander("Voir l’entrée exacte analysée"):



            st.json(analysis["input_snapshot"])



        report = {



            "machine": case["machine"],



            "analysis": analysis



        }



        st.download_button(



            "Télécharger le rapport JSON",



            data=json.dumps(report, ensure_ascii=False, indent=2),



            file_name=f"rapport_mecatech_ia_analyse_{analysis['run_id']}.json",



            mime="application/json"



        )



# =========================================================



# HISTORIQUE



# =========================================================



elif page == "Historique":



    st.header("Historique des diagnostics de cette session")



    if not st.session_state.cases:



        st.info("Aucun diagnostic dans cette session.")



    else:



        st.write(f"Nombre de diagnostics : {len(st.session_state.cases)}")



        for case in reversed(st.session_state.cases):



            analysis = case["analysis"]



            with st.expander(



                f"Analyse #{analysis['run_id']} — {analysis['primary_system']} — {analysis['timestamp']}"



            ):



                st.write("**Machine :**", case["machine"])



                st.write("**Résumé :**", analysis["summary"])



                st.write("**Sévérité :**", analysis["severity"])



                st.write("**Certitude :**", analysis["confidence_label"])



                st.write("**Empreinte entrée :**", analysis["input_hash"])



                if analysis["hypotheses"]:



                    st.write("**Hypothèse principale :**", analysis["hypotheses"][0]["title"])



                st.write("**Validation humaine :**", case.get("human_validation", "Non validé"))



# =========================================================



# VALIDATION HUMAINE



# =========================================================



elif page == "Validation humaine":



    st.header("Validation humaine")



    st.write("Le mécanicien garde la décision finale. Cette section sert à noter si l’analyse était utile ou non.")



    if not st.session_state.last_analysis:



        st.info("Aucune analyse récente à valider.")



    else:



        case = st.session_state.last_analysis



        analysis = case["analysis"]



        st.write("**Analyse :**", f"#{analysis['run_id']}")



        st.write("**Machine :**", case["machine"])



        st.write("**Système principal :**", analysis["primary_system"])



        st.write("**Hypothèse principale :**", analysis["hypotheses"][0]["title"])



        validation_options = [



            "Non validé",



            "Confirmé",



            "Partiellement confirmé",



            "Faux diagnostic",



            "À vérifier plus tard"



        ]



        validation = st.radio(



            "Résultat terrain",



            validation_options,



            index=validation_options.index(case.get("human_validation", "Non validé"))



        )



        real_cause = st.text_area(



            "Cause réelle trouvée / notes du technicien",



            value=case.get("real_cause", ""),



            height=140



        )



        if st.button("Sauvegarder validation", type="primary"):



            case["human_validation"] = validation



            case["real_cause"] = real_cause



            st.success("Validation sauvegardée pour cette session.")



# =========================================================



# À PROPOS



# =========================================================



elif page == "À propos":



    st.header("À propos de MecaTech IA v0.4")



    st.write("""



    Cette version introduit un moteur général modulaire.



    Principe :



    - le système choisi par le mécanicien est prioritaire;



    - l’app extrait les faits, conditions, tests déjà faits et codes;



    - elle propose des hypothèses générales adaptées au système;



    - elle donne une séquence de tests;



    - elle affiche les limites et informations manquantes;



    - elle ne conclut pas à une pièce sans preuve.



    Différence avec les versions précédentes :



    - moins de logique codée pour un cas précis;



    - plus de raisonnement général par système;



    - meilleure base pour tester plusieurs problèmes mécaniques différents.



    Limites actuelles :



    - pas encore de vraie API IA;



    - pas encore de base de données persistante;



    - pas encore de recherche web;



    - pas encore de documentation OEM;



    - pas encore de données live J1939/J1708.



    Objectif :



    aider le mécanicien à structurer son diagnostic, sans remplacer son jugement.



    """)



st.divider()



st.caption("MecaTech IA v0.4 — Moteur général modulaire | Read the fault. Find the cause. Fix it — once.")

