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



    .box {



        background: #171b1f;



        border: 1px solid #343a40;



        padding: 16px;



        border-radius: 12px;



        margin-bottom: 12px;



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



    # Systèmes



    if contains_any(text, ["transmission", "zf", "neutre", "neutral", "embraye", "vitesse", "rapport"]):



        detected["systems"].append("Transmission")



    if contains_any(text, ["hydraulique", "pression", "pompe", "cylindre", "valve", "huile hydraulique"]):



        detected["systems"].append("Hydraulique")



    if contains_any(text, ["moteur", "diesel", "injecteur", "turbo", "egr", "dpf", "fumée", "perte puissance"]):



        detected["systems"].append("Moteur")



    if contains_any(text, ["électrique", "voltage", "batterie", "alternateur", "fusible", "relais", "capteur", "can", "canbus", "faisceau"]):



        detected["systems"].append("Électrique / commande")



    if contains_any(text, ["frein", "brake", "stationnement", "parking brake"]):



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



    if contains_any(text, ["lumière transmission", "voyant transmission", "lumière trans", "trans light"]):



        detected["facts"].append("Voyant transmission allume")



    if contains_any(text, ["filtre remplacé", "filtre changé", "filtre neuf"]):



        detected["facts"].append("Filtre remplacé")



    if contains_any(text, ["huile ok", "niveau huile ok", "niveau d’huile ok", "qualité huile ok", "huile propre"]):



        detected["facts"].append("Huile / niveau déclaré OK")



    if contains_any(text, ["arrête repart", "redémarre", "reset", "sélecteur au neutre", "remets le sélecteur", "repart normalement"]):



        detected["facts"].append("Reset / arrêt / sélecteur permet de repartir")



    if contains_any(text, ["avant et reculons", "marche avant", "reculons", "avant ou reculons"]):



        detected["facts"].append("Avant / reculons mentionnés")



    # Infos manquantes utiles



    if not extract_dtcs(dtcs + " " + symptoms):



        detected["missing"].append("Codes DTC/SPN/FMI exacts ou capture outil diagnostic")



    if not contains_any(text, ["heures", "km", "h"]):



        detected["missing"].append("Heures/km de la machine")



    if not contains_any(text, ["pression", "voltage", "donnée live", "live data", "paramètre"]):



        detected["missing"].append("Données live : voltage, pression, rapport demandé/engagé, vitesses capteurs")



    if not contains_any(text, ["connecteur", "faisceau", "wiggle", "masse", "ground"]):



        detected["missing"].append("Inspection connecteurs/faisceau/masses")



    return detected



# =========================================================



# ENGINE V0.3 — PRUDENT



# =========================================================



def analyze_case(machine, symptoms, dtcs, context, history):



    detected = detect_context(machine, symptoms, dtcs, context, history)



    dtc_list = extract_dtcs(dtcs + " " + symptoms)



    systems = detected["systems"]



    facts = detected["facts"]



    conditions = detected["conditions"]



    hypotheses = []



    tests = []



    prudence = []



    summary = ""



    severity = "À évaluer"



    risk = "Analyse préliminaire. Validation humaine obligatoire avant réparation ou remise en service."



    # -----------------------------------------------------



    # TRANSMISSION



    # -----------------------------------------------------



    if "Transmission" in systems:



        summary = "Le problème décrit concerne principalement la transmission ou sa commande."



        hypotheses = [



            {



                "title": "Commande électrique / logique transmission à vérifier",



                "support": [



                    "Transmission tombe au neutre.",



                    "Le reset ou le retour au neutre permet de repartir." if "Reset / arrêt / sélecteur permet de repartir" in facts else "Le comportement de reset n’est pas encore confirmé.",



                    "Absence de code rapportée." if "Aucun code rapporté" in facts else "Les codes exacts ne sont pas confirmés."



                ],



                "limits": [



                    "Sans données live, impossible de confirmer si la transmission reçoit une demande de neutre ou si elle décroche.",



                    "Il faut comparer rapport demandé, rapport engagé et alimentation du module."



                ]



            },



            {



                "title": "Faisceau, connecteur, masse ou alimentation intermittente",



                "support": [



                    "Panne qui revient/intermittente." if "Intermittent / revient" in conditions else "Intermittence à confirmer.",



                    "Présent dans plusieurs vitesses." if "Présent dans toutes les vitesses" in conditions else "Impact selon les vitesses à préciser.",



                    "Aucun code peut arriver avec une coupure momentanée non enregistrée." if "Aucun code rapporté" in facts else "Historique de codes à vérifier."



                ],



                "limits": [



                    "Doit être validé par chute de voltage, wiggle test et inspection des connecteurs.",



                    "Ne pas conclure au module avant d’avoir validé alimentation et masses."



                ]



            },



            {



                "title": "Capteur vitesse / signal CAN / information incohérente",



                "support": [



                    "Une incohérence de vitesse entrée/sortie peut forcer un mode protection.",



                    "Voyant transmission mentionné." if "Voyant transmission allume" in facts else "Voyant ou message au tableau à confirmer."



                ],



                "limits": [



                    "Nécessite lecture live des paramètres.",



                    "Un code peut être absent si l’événement est trop bref ou non mémorisé."



                ]



            },



            {



                "title": "Pression de commande ou solénoïde transmission",



                "support": [



                    "La transmission décroche au neutre.",



                    "Filtre et huile OK réduisent la piste d’entretien de base." if ("Filtre remplacé" in facts and "Huile / niveau déclaré OK" in facts) else "État huile/filtre à confirmer."



                ],



                "limits": [



                    "La pression doit être mesurée selon procédure OEM.",



                    "Ne pas remplacer solénoïde ou module sans test de commande."



                ]



            }



        ]



        tests = [



            "Lire les codes actifs, inactifs et historiques avec outil compatible machine/transmission.",



            "Surveiller en données live : rapport demandé, rapport engagé, vitesse entrée, vitesse sortie, état du sélecteur.",



            "Mesurer alimentation et ground du module transmission sous charge.",



            "Faire wiggle test du faisceau, connecteurs, sélecteur et alimentation pendant surveillance live.",



            "Vérifier relais, fusibles, connecteurs exposés à eau/sel/vibration/chaleur.",



            "Confirmer si la lumière transmission allume exactement au moment où elle tombe au neutre.",



            "Tester pression de commande transmission selon procédure OEM si disponible.",



            "Documenter si le problème arrive en marche avant, reculons, toutes vitesses, charge, pente, chaud/froid."



        ]



        severity = "Élevé"



        risk = "Transmission qui tombe au neutre en roulant : risque opérationnel important. Ne pas remettre en service normal sans validation."



    # -----------------------------------------------------



    # HYDRAULIQUE



    # -----------------------------------------------------



    elif "Hydraulique" in systems:



        summary = "Le problème décrit semble toucher un circuit hydraulique ou une commande hydraulique."



        hypotheses = [



            {



                "title": "Pression hydraulique insuffisante ou instable",



                "support": ["Symptômes liés à pression/pompe/valve."],



                "limits": ["Impossible de confirmer sans manomètre ou données live."]



            },



            {



                "title": "Restriction filtre / huile / crépine",



                "support": ["Piste de base à éliminer en premier."],



                "limits": ["Si filtre et huile sont déjà confirmés OK, cette piste descend en priorité."]



            },



            {



                "title": "Valve de contrôle qui colle ou fuite interne",



                "support": ["Peut causer perte de fonction ou réaction lente."],



                "limits": ["Doit être confirmé par test de pression et temps de cycle."]



            }



        ]



        tests = [



            "Vérifier niveau, qualité et température d’huile hydraulique.",



            "Contrôler filtres, crépine et présence de limaille.",



            "Mesurer pression principale et standby.",



            "Comparer temps de cycle avec les spécifications.",



            "Isoler la fonction affectée et vérifier fuite interne possible."



        ]



        severity = "Moyen à élevé"



        risk = "Valider pression et sécurité avant usage intensif."



    # -----------------------------------------------------



    # MOTEUR



    # -----------------------------------------------------



    elif "Moteur" in systems:



        summary = "Le problème décrit semble toucher le moteur ou un système moteur."



        hypotheses = [



            {



                "title": "Restriction air/carburant ou pression insuffisante",



                "support": ["Piste fréquente en perte de puissance ou fonctionnement anormal."],



                "limits": ["À confirmer avec données live et pression."]



            },



            {



                "title": "EGR / DPF / turbo / capteur moteur",



                "support": ["Possible selon codes et symptômes."],



                "limits": ["Ne pas conclure sans codes et paramètres moteur."]



            },



            {



                "title": "Faisceau / capteur / alimentation module",



                "support": ["Possible surtout si intermittent."],



                "limits": ["Doit être validé par inspection et mesures électriques."]



            }



        ]



        tests = [



            "Lire codes actifs/inactifs moteur.",



            "Vérifier pression carburant, boost, restriction air et EGT.",



            "Comparer données live à froid et à chaud.",



            "Inspecter filtre air, filtre carburant et connecteurs capteurs.",



            "Valider alimentation et grounds du module moteur."



        ]



        severity = "Moyen"



        risk = "Surveiller température, pression huile et alertes moteur."



    # -----------------------------------------------------



    # FREIN



    # -----------------------------------------------------



    elif "Frein" in systems:



        summary = "Le problème décrit implique un système de freinage."



        hypotheses = [



            {



                "title": "Commande électrique / solénoïde / switch de frein",



                "support": ["Piste fréquente si frein de stationnement ou commande ne répond pas."],



                "limits": ["À confirmer par mesure électrique et schéma."]



            },



            {



                "title": "Pression air/hydraulique insuffisante",



                "support": ["Selon type de système."],



                "limits": ["Doit être mesuré avant conclusion."]



            },



            {



                "title": "Mécanisme de frein collé ou usé",



                "support": ["Possible si commande fonctionne mais réaction mécanique anormale."],



                "limits": ["Inspection physique requise."]



            }



        ]



        tests = [



            "Immobiliser la machine si le frein est incertain.",



            "Vérifier alimentation, solénoïde, switchs et capteurs.",



            "Mesurer pression air/hydraulique selon système.",



            "Inspecter mécaniquement le frein.",



            "Valider la logique de sécurité dans le manuel OEM."



        ]



        severity = "Critique"



        risk = "Système de freinage impliqué : ne pas utiliser si comportement anormal."



    # -----------------------------------------------------



    # ÉLECTRIQUE



    # -----------------------------------------------------



    elif "Électrique / commande" in systems:



        summary = "Le problème décrit semble lié à une commande électrique, un capteur, un faisceau ou une alimentation."



        hypotheses = [



            {



                "title": "Mauvaise masse ou alimentation instable",



                "support": ["Très probable dans les pannes intermittentes."],



                "limits": ["Doit être confirmé par chute de voltage sous charge."]



            },



            {



                "title": "Connecteur oxydé / fil cassé / faisceau intermittent",



                "support": ["Compatible avec vibration, humidité, chaleur ou panne qui revient."],



                "limits": ["Inspection visuelle seule insuffisante : wiggle test recommandé."]



            },



            {



                "title": "Communication CAN ou module qui décroche",



                "support": ["Possible si perte de communication ou comportement logique anormal."],



                "limits": ["Nécessite lecture réseau et codes communication."]



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



    if "Aucun code rapporté" in facts:



        prudence.append("Aucun code ne veut pas dire aucun problème. Une panne de commande, masse, signal ou hydraulique peut ne pas être mémorisée.")



    if "Filtre remplacé" in facts and "Huile / niveau déclaré OK" in facts:



        prudence.append("Filtre remplacé + huile OK : éviter de rester bloqué sur l’entretien de base; passer aux tests de commande, pression, faisceau et données live.")



    if "Intermittent / revient" in conditions:



        prudence.append("Panne intermittente : prioriser vibration, chaleur, humidité, connecteurs, masses et alimentation.")



    if not dtc_list:



        prudence.append("Aucun DTC structuré détecté dans le texte. Ajouter les codes exacts si disponibles.")



    confidence_label = "Préliminaire"



    if len(facts) >= 3 and len(conditions) >= 2 and len(systems) >= 1:



        confidence_label = "Moyenne — nécessite tests"



    if dtc_list and len(facts) >= 3:



        confidence_label = "Moyenne+ — avec codes, mais validation requise"



    return {



        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),



        "summary": summary,



        "systems": systems,



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



st.caption("Prototype MVP v0.3 — moteur prudent, relance directe, validation humaine obligatoire")



col1, col2, col3, col4 = st.columns(4)



with col1:



    st.metric("Version", "v0.3")



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



    Cette version ne prétend pas confirmer une panne. Elle structure le raisonnement mécanique,



    classe les pistes à vérifier et indique les informations manquantes.



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



            placeholder="Ex: Hitachi ZW180 2020 transmission ZF",



            key="brand_model"



        )



        hours_km = st.text_input(



            "Heures / km",



            placeholder="Ex: 14 822 h ou inconnu",



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



            placeholder="Ex: Aucun code actif ou inactif / SPN xxxx FMI xx",



            height=120,



            key="dtcs"



        )



    symptoms = st.text_area(



        "Symptômes observés",



        placeholder="Décris le problème : quand ça arrive, chaud/froid, vitesse, charge, bruit, comportement...",



        height=170,



        key="symptoms"



    )



    context = st.text_area(



        "Contexte terrain / tests déjà faits",



        placeholder="Ex: filtre remplacé, huile OK, problème froid comme chaud, repart après arrêt, etc.",



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



            history=history



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



    # AFFICHAGE RÉSULTAT



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



    st.write(



        "Le mécanicien garde la décision finale. Cette section sert à noter si l’analyse était utile ou non."



    )



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



    st.header("À propos de MecaTech IA v0.3")



    st.write("""



    Cette version est un MVP fonctionnel très simple.



    Ce qu’elle fait :



    - relance une nouvelle analyse à chaque clic;



    - garde un historique de session;



    - structure les symptômes;



    - détecte les faits importants;



    - propose des hypothèses à vérifier;



    - donne une séquence de tests;



    - affiche les informations manquantes;



    - garde une validation humaine.



    Ce qu’elle ne fait pas encore :



    - elle ne remplace pas le mécanicien;



    - elle ne remplace pas les manuels OEM;



    - elle ne lit pas encore les données live;



    - elle ne se connecte pas encore aux outils JPRO/OEM;



    - elle n’utilise pas encore une vraie API IA;



    - elle ne sauvegarde pas encore dans une vraie base de données.



    Principe :



    MecaTech IA doit aider à raisonner, pas inventer une certitude.



    """)



st.divider()



st.caption("MecaTech IA v0.3 — Read the fault. Find the cause. Fix it — once.")

