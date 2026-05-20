
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



# UTILS



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



        r"\bTCU\s*\d{4,6}\.\d{1,2}\b",



        r"\bECU\s*\d{4,6}\.\d{1,2}\b",



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



def detect_context(machine, symptoms, dtcs, context, history) -> dict:



    text = f"{machine} {symptoms} {dtcs} {context} {history}".lower()



    detected = {



        "systems": [],



        "conditions": [],



        "facts": [],



        "missing": []



    }



    # Systèmes détectés comme contexte secondaire



    if contains_any(text, ["transmission", "zf", "neutre", "neutral", "embraye", "vitesse", "rapport"]):



        detected["systems"].append("Transmission")



    if contains_any(text, ["hydraulique", "pression", "pompe", "cylindre", "valve", "huile hydraulique"]):



        detected["systems"].append("Hydraulique")



    if contains_any(text, ["moteur", "diesel", "injecteur", "turbo", "egr", "dpf", "fumée", "perte puissance"]):



        detected["systems"].append("Moteur")



    if contains_any(text, ["électrique", "voltage", "batterie", "alternateur", "fusible", "relais", "capteur", "can", "canbus", "faisceau", "courant"]):



        detected["systems"].append("Électrique / commande")



    if contains_any(text, ["frein", "brake", "stationnement", "parking brake", "parking"]):



        detected["systems"].append("Frein")



    if contains_any(text, ["chauffe", "surchauffe", "radiateur", "coolant", "prestone", "thermostat", "fan"]):



        detected["systems"].append("Refroidissement")



    # Conditions



    if contains_any(text, ["intermittent", "parfois", "des fois", "recommence", "revient", "pas toujours"]):



        detected["conditions"].append("Intermittent / revient")



    if contains_any(text, ["constant", "toujours", "tout le temps", "permanent"]):



        detected["conditions"].append("Constant")



    if contains_any(text, ["à chaud", "chaud", "après 15 minutes", "après 20 minutes", "température"]):



        detected["conditions"].append("À chaud / température")



    if contains_any(text, ["à froid", "froid", "démarrage"]):



        detected["conditions"].append("À froid")



    if contains_any(text, ["froid comme à chaud", "froide ou chaude", "à froid comme à chaud"]):



        detected["conditions"].append("Présent froid comme chaud")



    if contains_any(text, ["peu importe la vitesse", "toutes les vitesses", "tous les rapports", "n'importe quelle vitesse"]):



        detected["conditions"].append("Présent dans toutes les vitesses")



    # Faits terrain



    if contains_any(text, ["pas de code", "aucun code", "aucun défaut", "no code", "pas d'erreur"]):



        detected["facts"].append("Aucun code rapporté")



    if contains_any(text, ["lumière témoin", "lumiere temoin", "témoin", "temoin", "voyant", "ne s'allume pas", "ne s allume pas"]):



        detected["facts"].append("Témoin / voyant ne confirme pas l’état")



    if contains_any(text, ["filtre ok", "filtre remplacé", "filtre changé", "filtre neuf"]):



        detected["facts"].append("Filtre déclaré OK")



    if contains_any(text, ["huile ok", "niveau huile ok", "niveau d’huile ok", "qualité huile ok", "huile propre"]):



        detected["facts"].append("Huile / niveau déclaré OK")



    if contains_any(text, ["arrête repart", "redémarre", "reset", "sélecteur au neutre", "remets le sélecteur", "repart normalement"]):



        detected["facts"].append("Reset / arrêt / sélecteur permet de repartir")



    if contains_any(text, ["courant ok", "courant sur", "voltage ok", "alimentation ok"]):



        detected["facts"].append("Courant / alimentation déclaré OK")



    if contains_any(text, ["solénoïde", "solenoide"]):



        detected["facts"].append("Solénoïde mentionné")



    if contains_any(text, ["capteur de pression"]):



        detected["facts"].append("Capteur de pression mentionné")



    # Infos manquantes



    if not extract_dtcs(dtcs + " " + symptoms + " " + context):



        detected["missing"].append("Codes DTC/SPN/FMI exacts ou capture outil diagnostic")



    if not contains_any(text, ["pression", "voltage", "donnée live", "live data", "paramètre", "courant"]):



        detected["missing"].append("Données live : voltage, pression, états d’entrée/sortie module")



    if not contains_any(text, ["connecteur", "faisceau", "wiggle", "masse", "ground"]):



        detected["missing"].append("Inspection connecteurs/faisceau/masses")



    return detected



# =========================================================



# ENGINE V0.3.1 — PRIORITÉ AU SYSTÈME CHOISI



# =========================================================



def analyze_case(machine, symptoms, dtcs, context, history, selected_system):



    detected = detect_context(machine, symptoms, dtcs, context, history)



    dtc_list = extract_dtcs(dtcs + " " + symptoms + " " + context)



    systems_detected = detected["systems"]



    facts = detected["facts"]



    conditions = detected["conditions"]



    text = f"{machine} {symptoms} {dtcs} {context} {history}".lower()



    hypotheses = []



    tests = []



    prudence = []



    summary = ""



    severity = "À évaluer"



    risk = "Analyse préliminaire. Validation humaine obligatoire avant réparation ou remise en service."



    # Priorité absolue au choix du mécanicien



    primary_system = selected_system



    if selected_system == "Autre / inconnu":



        primary_system = systems_detected[0] if systems_detected else "Inconnu"



    # Détections spéciales



    parking_brake_problem = contains_any(



        text,



        ["parking brake", "frein de stationnement", "stationnement", "parking"]



    )



    does_not_apply = contains_any(



        text,



        [



            "ne s'applique pas",



            "ne s applique pas",



            "ne s'engage pas",



            "ne s engage pas",



            "pas appliquer",



            "pas appliqué",



            "pas engage",



            "pas engagé"



        ]



    )



    witness_light_problem = contains_any(



        text,



        ["lumière témoin", "lumiere temoin", "témoin", "temoin", "voyant", "ne s'allume pas", "ne s allume pas"]



    )



    current_verified = contains_any(



        text,



        [



            "courant ok",



            "courant sur",



            "voltage ok",



            "alimentation ok",



            "courant solénoïde",



            "courant solenoide",



            "courant capteur",



            "courant sélecteur",



            "courant selecteur"



        ]



    )



    tcu_codes = [code for code in dtc_list if code.upper().startswith("TCU")]



    # -----------------------------------------------------



    # FREIN / PARKING BRAKE



    # -----------------------------------------------------



    if primary_system == "Frein":



        summary = "Le problème décrit concerne principalement le frein ou sa commande."



        if parking_brake_problem:



            summary = "Le problème décrit concerne le parking brake / frein de stationnement : il ne s’applique pas ou sa commande ne confirme pas l’état attendu."



        hypotheses = [



            {



                "title": "Commande logique du parking brake / condition d’autorisation non satisfaite",



                "support": [



                    "Le système principal sélectionné est Frein.",



                    "Le problème touche le parking brake." if parking_brake_problem else "Le type exact de frein doit être confirmé.",



                    "Le témoin ne s’allume pas ou ne confirme pas l’état." if witness_light_problem else "L’état du témoin doit être confirmé.",



                    "Des codes TCU sont présents." if tcu_codes else "Aucun code TCU structuré détecté."



                ],



                "limits": [



                    "Un courant présent à un composant ne confirme pas que le module reçoit ou interprète correctement le signal.",



                    "Il faut valider les entrées/sorties du TCU selon le schéma et le manuel John Deere.",



                    "La description exacte des codes TCU doit être confirmée avec la documentation OEM."



                ]



            },



            {



                "title": "Capteur de pression ou signal de retour mal interprété",



                "support": [



                    "Le capteur de pression est mentionné." if "Capteur de pression mentionné" in facts else "Le capteur de pression doit être validé.",



                    "Le module peut recevoir une valeur incohérente même si l’alimentation est présente.",



                    "Un code TCU peut indiquer un problème d’entrée, signal ou plage de fonctionnement."



                ],



                "limits": [



                    "Mesurer le signal de retour, pas seulement l’alimentation.",



                    "Comparer la lecture réelle du capteur avec ce que le TCU affiche en données live.",



                    "Vérifier alimentation, ground et signal sous charge."



                ]



            },



            {



                "title": "Solénoïde de parking brake alimenté mais non fonctionnel mécaniquement",



                "support": [



                    "Le solénoïde est mentionné." if "Solénoïde mentionné" in facts else "L’état du solénoïde doit être confirmé.",



                    "Courant OK ne veut pas dire que le solénoïde bouge ou que la valve travaille.",



                    "Le frein ne s’applique pas." if does_not_apply else "L’application réelle du frein doit être confirmée."



                ],



                "limits": [



                    "Tester l’activation réelle du solénoïde.",



                    "Écouter/sentir le clic, mesurer résistance, vérifier la commande sous charge.",



                    "Vérifier si la valve est collée ou si le circuit hydraulique/pneumatique réagit."



                ]



            },



            {



                "title": "Circuit hydraulique ou pression de commande du frein de stationnement",



                "support": [



                    "Le frein ne s’applique pas malgré des vérifications électriques.",



                    "Huile/filtre déclarés OK réduisent la piste entretien de base." if ("Huile / niveau déclaré OK" in facts or "Filtre déclaré OK" in facts) else "État huile/filtre à confirmer."



                ],



                "limits": [



                    "Mesurer la pression réelle du circuit de parking brake.",



                    "Vérifier valve, restriction, fuite interne ou blocage mécanique.",



                    "Ne pas conclure électrique seulement si la commande est présente."



                ]



            }



        ]



        tests = [



            "Confirmer la signification exacte des codes TCU dans le manuel John Deere pour 772G 2007.",



            "Lire les données live TCU : commande parking brake demandée, état du sélecteur, état capteur pression, retour témoin.",



            "Vérifier non seulement le courant, mais aussi le signal de retour du capteur de pression.",



            "Tester le solénoïde parking brake sous charge : alimentation, ground, résistance, activation réelle.",



            "Vérifier si le TCU autorise ou bloque l’application du parking brake selon les conditions machine.",



            "Contrôler le circuit hydraulique/pneumatique de parking brake : pression, valve, restriction, fuite interne.",



            "Comparer le schéma électrique : sélecteur, témoin, capteur pression, solénoïde, TCU.",



            "Vérifier si les codes reviennent immédiatement après effacement/redémarrage."



        ]



        severity = "Critique"



        risk = "Frein de stationnement non fonctionnel : ne pas remettre la machine en service tant que l’application réelle du frein n’est pas confirmée."



    # -----------------------------------------------------



    # TRANSMISSION



    # -----------------------------------------------------



    elif primary_system == "Transmission":



        summary = "Le problème décrit concerne principalement la transmission ou sa commande."



        hypotheses = [



            {



                "title": "Commande électrique / logique transmission à vérifier",



                "support": [



                    "Le système principal sélectionné est Transmission.",



                    "Transmission ou commande de rapport mentionnée dans les symptômes.",



                    "Reset ou retour au neutre mentionné." if "Reset / arrêt / sélecteur permet de repartir" in facts else "Comportement après reset à préciser."



                ],



                "limits": [



                    "Sans données live, impossible de confirmer si la transmission reçoit une demande de neutre ou si elle décroche.",



                    "Comparer rapport demandé, rapport engagé et alimentation du module."



                ]



            },



            {



                "title": "Faisceau, connecteur, masse ou alimentation intermittente",



                "support": [



                    "Compatible avec une panne qui revient ou intermittente.",



                    "Peut ne pas toujours générer un code mémorisé."



                ],



                "limits": [



                    "Valider par chute de voltage, wiggle test et inspection des connecteurs.",



                    "Ne pas conclure au module avant d’avoir validé alimentation et masses."



                ]



            },



            {



                "title": "Capteur vitesse / signal CAN / information incohérente",



                "support": [



                    "Une incohérence de vitesse entrée/sortie peut forcer un mode protection."



                ],



                "limits": [



                    "Nécessite lecture live des paramètres.",



                    "Un code peut être absent si l’événement est trop bref ou non mémorisé."



                ]



            }



        ]



        tests = [



            "Lire codes actifs, inactifs et historiques transmission.",



            "Surveiller rapport demandé, rapport engagé, vitesse entrée et vitesse sortie.",



            "Mesurer alimentation et ground du module transmission sous charge.",



            "Faire wiggle test du faisceau, connecteurs et sélecteur.",



            "Vérifier relais, fusibles et connecteurs exposés à eau/sel/vibration.",



            "Tester pression de commande transmission selon procédure OEM si disponible."



        ]



        severity = "Élevé"



        risk = "Transmission qui tombe au neutre en roulant : risque opérationnel important."



    # -----------------------------------------------------



    # HYDRAULIQUE



    # -----------------------------------------------------



    elif primary_system == "Hydraulique":



        summary = "Le problème décrit semble toucher un circuit hydraulique ou une commande hydraulique."



        hypotheses = [



            {



                "title": "Pression hydraulique insuffisante ou instable",



                "support": ["Système principal sélectionné : Hydraulique."],



                "limits": ["Impossible de confirmer sans mesure de pression."]



            },



            {



                "title": "Valve de contrôle qui colle ou fuite interne",



                "support": ["Possible si une fonction ne répond pas correctement."],



                "limits": ["À confirmer par test de pression et temps de cycle."]



            }



        ]



        tests = [



            "Contrôler niveau, qualité et température d’huile hydraulique.",



            "Mesurer pression principale et standby.",



            "Comparer temps de cycle avec spécifications.",



            "Vérifier valve, restriction, fuite interne ou blocage."



        ]



        severity = "Moyen à élevé"



        risk = "Valider pression et sécurité avant usage intensif."



    # -----------------------------------------------------



    # MOTEUR



    # -----------------------------------------------------



    elif primary_system == "Moteur":



        summary = "Le problème décrit semble toucher le moteur ou un système moteur."



        hypotheses = [



            {



                "title": "Restriction air/carburant ou pression insuffisante",



                "support": ["Système principal sélectionné : Moteur."],



                "limits": ["À confirmer avec données live et pression."]



            },



            {



                "title": "EGR / DPF / turbo / capteur moteur",



                "support": ["Possible selon codes et symptômes."],



                "limits": ["Ne pas conclure sans codes et paramètres moteur."]



            }



        ]



        tests = [



            "Lire codes actifs/inactifs moteur.",



            "Vérifier pression carburant, boost, restriction air et EGT.",



            "Comparer données live à froid et à chaud.",



            "Inspecter filtres et connecteurs capteurs."



        ]



        severity = "Moyen"



        risk = "Surveiller température, pression huile et alertes moteur."



    # -----------------------------------------------------



    # ÉLECTRIQUE



    # -----------------------------------------------------



    elif primary_system == "Électrique":



        summary = "Le problème décrit semble lié à une commande électrique, un capteur, un faisceau ou une alimentation."



        hypotheses = [



            {



                "title": "Mauvaise masse ou alimentation instable",



                "support": ["Système principal sélectionné : Électrique."],



                "limits": ["Doit être confirmé par chute de voltage sous charge."]



            },



            {



                "title": "Connecteur oxydé / fil cassé / faisceau intermittent",



                "support": ["Compatible avec vibration, humidité, chaleur ou panne qui revient."],



                "limits": ["Inspection visuelle seule insuffisante : wiggle test recommandé."]



            }



        ]



        tests = [



            "Faire test de chute de voltage sous charge.",



            "Contrôler grounds principaux et secondaires.",



            "Inspecter connecteurs exposés eau/sel/vibration.",



            "Faire wiggle test pendant surveillance live.",



            "Vérifier tension CAN H/CAN L et codes communication."



        ]



        severity = "Moyen à élevé"



        risk = "Panne électrique intermittente : risque de comportement imprévisible."



    # -----------------------------------------------------



    # DEFAULT



    # -----------------------------------------------------



    else:



        summary = "Les informations ne permettent pas encore d’identifier clairement un système principal."



        hypotheses = [



            {



                "title": "Information insuffisante pour orienter le diagnostic",



                "support": ["Le texte ne contient pas assez de détails techniques exploitables."],



                "limits": ["Ajouter système, marque/modèle, symptômes précis, codes et conditions."]



            }



        ]



        tests = [



            "Ajouter marque, modèle, année, moteur/transmission.",



            "Décrire exactement le symptôme et quand il arrive.",



            "Ajouter codes actifs/inactifs ou mentionner qu’il n’y en a pas.",



            "Préciser chaud/froid, vitesse, charge, intermittent/constant.",



            "Ajouter travaux récents et tests déjà faits."



        ]



        severity = "Inconnu"



        risk = "Données insuffisantes. Analyse préliminaire seulement."



    # Prudence commune



    if tcu_codes:



        prudence.append("Codes TCU détectés : utiliser la description OEM exacte avant de conclure. Le code seul ne suffit pas.")



    if current_verified:



        prudence.append("Courant présent ne confirme pas le fonctionnement réel. Vérifier signal de retour, charge, ground et activation mécanique.")



    if "Aucun code rapporté" in facts:



        prudence.append("Aucun code ne veut pas dire aucun problème. Une panne de commande, masse, signal ou hydraulique peut ne pas être mémorisée.")



    if "Filtre déclaré OK" in facts and "Huile / niveau déclaré OK" in facts:



        prudence.append("Filtre OK + huile OK : éviter de rester bloqué sur l’entretien de base; passer aux tests de commande, pression, faisceau et données live.")



    if "Intermittent / revient" in conditions:



        prudence.append("Panne intermittente : prioriser vibration, chaleur, humidité, connecteurs, masses et alimentation.")



    if not dtc_list:



        prudence.append("Aucun DTC structuré détecté dans le texte. Ajouter les codes exacts si disponibles.")



    confidence_label = "Préliminaire"



    if len(facts) >= 3 and len(conditions) >= 1:



        confidence_label = "Moyenne — nécessite tests"



    if dtc_list and len(facts) >= 2:



        confidence_label = "Moyenne+ — codes présents, validation OEM requise"



    systems_output = [primary_system]



    for sys in systems_detected:



        if sys not in systems_output:



            systems_output.append(sys)



    return {



        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),



        "summary": summary,



        "systems": systems_output,



        "conditions": conditions,



        "facts": facts,



        "missing": detected["missing"],



        "dtcs": dtc_list,



        "severity": severity,



        "risk": risk,



        "hypotheses": hypotheses,



        "tests": tests,



        "prudence": prudence,



        "confidence_label": confidence_label



    }



# =========================================================



# HEADER



# =========================================================



st.title("🔧 MecaTech IA")



st.caption("Prototype MVP v0.3.1 — priorité au système choisi, moteur prudent, validation humaine obligatoire")



col1, col2, col3, col4 = st.columns(4)



with col1:



    st.metric("Version", "v0.3.1")



with col2:



    st.metric("Mode", "MVP terrain")



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



    Cette version priorise le système choisi par le mécanicien.



    Les mots-clés servent de contexte secondaire, pas de décision principale.



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



            placeholder="Ex: John Deere 772G 2007",



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



                "Autre / inconnu"



            ],



            key="system"



        )



        dtcs = st.text_area(



            "Codes DTC / SPN / FMI",



            placeholder="Ex: TCU 522405.5 / TCU 523754.3",



            height=120,



            key="dtcs"



        )



    symptoms = st.text_area(



        "Symptômes observés",



        placeholder="Décris le problème : quand ça arrive, témoin, comportement, conditions...",



        height=170,



        key="symptoms"



    )



    context = st.text_area(



        "Contexte terrain / tests déjà faits",



        placeholder="Ex: filtre OK, huile OK, courant au sélecteur OK, courant au solénoïde OK...",



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



            st.metric("Sévérité", analysis["severity"])



        with b:



            st.metric("Niveau de certitude", analysis["confidence_label"])



        with c:



            st.metric("DTC détectés", len(analysis["dtcs"]))



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



            st.write("**Systèmes :**")



            st.write(analysis["systems"] if analysis["systems"] else "Non détecté")



        with col_b:



            st.write("**Conditions :**")



            st.write(analysis["conditions"] if analysis["conditions"] else "Non détecté")



        with col_c:



            st.write("**Faits terrain :**")



            st.write(analysis["facts"] if analysis["facts"] else "Non détecté")



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



                f"Analyse #{analysis['run_id']} — {case['machine']} — {analysis['timestamp']}"



            ):



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



    st.header("À propos de MecaTech IA v0.3.1")



    st.write("""



    Cette version corrige une lacune importante :



    Le système principal choisi par le mécanicien est maintenant prioritaire.



    Exemple :



    Si le mécanicien choisit Frein, l’analyse reste centrée sur le frein/parking brake,



    même si le texte contient les mots “sélecteur de vitesse”, “huile” ou “courant”.



    Ce qu’elle fait :



    - relance une nouvelle analyse à chaque clic;



    - garde un historique de session;



    - priorise le système choisi;



    - détecte les codes TCU;



    - structure les symptômes;



    - propose des hypothèses à vérifier;



    - affiche les limites et informations manquantes;



    - garde une validation humaine.



    Principe :



    MecaTech IA doit aider à raisonner, pas inventer une certitude.



    """)



st.divider()



st.caption("MecaTech IA v0.3.1 — Read the fault. Find the cause. Fix it — once.")

