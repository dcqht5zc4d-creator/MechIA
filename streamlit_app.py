
import streamlit as st



from datetime import datetime



import hashlib



import json



import re



st.set_page_config(



    page_title="MecaTech IA",



    page_icon="🔧",



    layout="wide"



)



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



if "cases" not in st.session_state:



    st.session_state.cases = []



if "last_analysis" not in st.session_state:



    st.session_state.last_analysis = None



if "analysis_counter" not in st.session_state:



    st.session_state.analysis_counter = 0



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



SYSTEM_MODULES = {



    "Transmission": {



        "risk": "Élevé si la machine perd la propulsion, tombe au neutre ou change de comportement en mouvement.",



        "hypotheses": {



            "Mécanique": [



                "Embrayage interne, composant mécanique, arbre ou train d’engrenage à vérifier",



                "Défaut mécanique interne à confirmer seulement après tests externes",



                "Usure, blocage ou dommage interne affectant le rapport ou la propulsion",



            ],



            "Électrique / commande": [



                "Commande électrique / logique de transmission",



                "Sélecteur, faisceau, connecteur, masse ou alimentation intermittente",



                "Relais, fusible, sortie module ou alimentation de commande instable",



            ],



            "Hydraulique / pression": [



                "Pression de commande transmission insuffisante ou instable",



                "Valve, solénoïde hydraulique ou circuit de commande à vérifier",



                "Restriction, fuite interne ou perte de pression sous condition",



            ],



            "Capteur / signal": [



                "Capteur de vitesse entrée/sortie ou information incohérente",



                "Signal de sélecteur ou retour de position incohérent",



                "Capteur alimenté mais signal de retour incorrect",



            ],



            "Module / logique": [



                "Module qui demande une protection ou un retour au neutre",



                "Autorisation de commande ou condition logique non satisfaite",



                "État mémorisé / protection temporaire après défaut",



            ],



        },



        "tests": [



            "Lire codes actifs, inactifs et historiques avec outil compatible.",



            "Comparer données live : rapport demandé, rapport engagé, vitesse entrée, vitesse sortie.",



            "Mesurer alimentation et ground du module sous charge.",



            "Faire wiggle test du faisceau, connecteurs et sélecteur pendant surveillance live.",



            "Mesurer pression de commande selon procédure OEM si disponible.",



            "Confirmer si le problème est présent en marche avant, reculons, toutes vitesses, chaud/froid.",



        ],



    },



    "Frein": {



        "risk": "Critique si frein de service ou stationnement incertain. Immobilisation recommandée jusqu’à validation.",



        "hypotheses": {



            "Mécanique": [



                "Mécanisme de frein collé, usé, mal ajusté ou endommagé",



                "Linkage, ajustement, disque, ressort, piston ou composant physique à inspecter",



                "Frein capable de recevoir une commande mais mouvement mécanique bloqué ou incomplet",



            ],



            "Électrique / commande": [



                "Commande électrique, switch, relais, solénoïde ou sortie module à vérifier",



                "Alimentation présente mais commande réelle sous charge non confirmée",



                "Faisceau, connecteur, ground ou alimentation de commande instable",



            ],



            "Hydraulique / pression": [



                "Pression air/hydraulique insuffisante ou fuite interne",



                "Valve de commande du frein ou circuit de pression à vérifier",



                "Pression présente à un endroit mais non transmise correctement au frein",



            ],



            "Capteur / signal": [



                "Capteur de pression, switch, témoin ou signal de retour incohérent",



                "Capteur alimenté mais valeur retournée au module incorrecte",



                "Connecteur/faisceau du capteur modifie l’état logique du frein",



            ],



            "Module / logique": [



                "Logique de sécurité ou condition d’autorisation non satisfaite",



                "TCU/ECU interprète mal l’état du frein ou du capteur",



                "Interlock ou protection empêche l’application ou la confirmation du frein",



            ],



        },



        "tests": [



            "Immobiliser la machine si le frein est incertain.",



            "Lire codes actifs/inactifs liés au frein, TCU, ECU ou contrôleur machine.",



            "Vérifier commande demandée vs état réel dans les données live.",



            "Mesurer alimentation, ground et signal de retour capteur/switch.",



            "Tester solénoïde ou valve sous charge, pas seulement présence de courant.",



            "Mesurer pression air/hydraulique du circuit concerné.",



            "Inspecter mécaniquement frein, linkage, ajustement, usure et blocage.",



        ],



    },



    "Hydraulique": {



        "risk": "Moyen à élevé selon la fonction touchée, la pression et la possibilité de mouvement incontrôlé.",



        "hypotheses": {



            "Mécanique": [



                "Valve qui colle, fuite interne, cylindre ou composant mécanique bloqué",



                "Usure mécanique ou restriction physique dans le circuit",



            ],



            "Électrique / commande": [



                "Commande électrique de valve ou solénoïde hydraulique à vérifier",



                "Faisceau, connecteur ou sortie module de commande hydraulique instable",



            ],



            "Hydraulique / pression": [



                "Pression hydraulique insuffisante ou instable",



                "Restriction filtre, crépine, huile contaminée ou mauvaise viscosité",



                "Pompe faible, cavitation ou alimentation d’huile insuffisante",



            ],



            "Capteur / signal": [



                "Capteur de pression ou lecture électronique incohérente",



                "Signal capteur différent de la pression mesurée mécaniquement",



            ],



            "Module / logique": [



                "Commande pilotée ou autorisation hydraulique bloquée par le module",



                "État logique qui limite la fonction hydraulique",



            ],



        },



        "tests": [



            "Vérifier niveau, qualité, odeur, contamination et température d’huile.",



            "Contrôler filtre, crépine et présence de limaille.",



            "Mesurer pression principale, standby, pilotage et pression de fonction.",



            "Comparer temps de cycle avec spécifications.",



            "Comparer lecture capteur avec manomètre mécanique.",



            "Vérifier si le problème change avec température, charge ou régime moteur.",



        ],



    },



    "Moteur": {



        "risk": "Moyen à élevé si perte de puissance, surchauffe, pression d’huile ou fumée anormale.",



        "hypotheses": {



            "Mécanique": [



                "Compression, distribution, restriction mécanique ou usure moteur à vérifier",



                "Problème mécanique interne à confirmer par tests de base",



            ],



            "Électrique / commande": [



                "Faisceau, alimentation module, relais ou capteur moteur instable",



                "Commande électrique d’injecteur, turbo, EGR ou système moteur à vérifier",



            ],



            "Hydraulique / pression": [



                "Pression carburant, rail, pompe ou alimentation carburant à vérifier",



                "Pression d’huile ou alimentation fluide moteur anormale",



            ],



            "Capteur / signal": [



                "Capteur moteur donnant une lecture incohérente",



                "Signal MAF/MAP/température/pression incompatible avec le symptôme",



            ],



            "Module / logique": [



                "ECU en mode protection ou derate",



                "Post-traitement, DPF/SCR/EGR limitant la puissance par logique",



            ],



        },



        "tests": [



            "Lire codes actifs/inactifs moteur.",



            "Vérifier pression carburant, restriction air, boost, EGT et charge moteur.",



            "Comparer données live à froid et à chaud.",



            "Inspecter filtre air, filtre carburant, lignes et connecteurs capteurs.",



            "Contrôler pression d’huile, température coolant et restriction échappement.",



        ],



    },



    "Électrique": {



        "risk": "Variable, mais élevé si le défaut provoque arrêt, comportement intermittent ou perte de commande.",



        "hypotheses": {



            "Mécanique": [



                "Composant mécanique commandé électriquement bloqué ou usé",



                "Actionneur reçoit une commande mais ne produit pas le mouvement attendu",



            ],



            "Électrique / commande": [



                "Mauvaise masse ou alimentation instable",



                "Connecteur oxydé, fil cassé, faisceau frotté ou intermittent",



                "Relais, fusible, alimentation module ou circuit sous charge",



            ],



            "Hydraulique / pression": [



                "Commande électrique correcte mais pression/réaction hydraulique absente",



                "Solénoïde activé mais circuit de pression en aval à vérifier",



            ],



            "Capteur / signal": [



                "Capteur alimenté mais signal de retour incohérent",



                "Signal intermittent ou hors plage vers module",



            ],



            "Module / logique": [



                "Communication CAN/J1939/J1708 ou module qui décroche",



                "Module bloque une sortie à cause d’un interlock ou état logique",



            ],



        },



        "tests": [



            "Mesurer voltage source et chute de voltage sous charge.",



            "Contrôler grounds principaux et secondaires.",



            "Inspecter connecteurs exposés eau, sel, vibration, chaleur.",



            "Faire wiggle test pendant surveillance live.",



            "Vérifier alimentation, ground et signal de retour des capteurs.",



            "Vérifier codes de communication et état réseau CAN/J1939/J1708.",



        ],



    },



    "Refroidissement": {



        "risk": "Élevé si surchauffe ou perte de coolant. Risque de dommage moteur.",



        "hypotheses": {



            "Mécanique": [



                "Pompe à eau, thermostat, bouchon pression ou circulation mécanique à vérifier",



                "Obstruction radiateur, fan, courroie ou airflow insuffisant",



            ],



            "Électrique / commande": [



                "Commande fan, relais, capteur température ou faisceau à vérifier",



                "Fan commandé électriquement mais non activé sous condition",



            ],



            "Hydraulique / pression": [



                "Pression système coolant, air dans le circuit ou fuite interne/externe",



                "Circulation insuffisante ou cavitation pompe",



            ],



            "Capteur / signal": [



                "Capteur température ou lecture erronée",



                "Différence entre lecture module et température réelle",



            ],



            "Module / logique": [



                "Commande fan ou protection moteur gérée par module",



                "ECU limite puissance à cause de température lue ou réelle",



            ],



        },



        "tests": [



            "Vérifier niveau coolant, concentration, pression et fuite.",



            "Inspecter radiateur, fan, courroie, shroud et obstruction extérieure.",



            "Comparer température entrée/sortie radiateur.",



            "Tester thermostat, bouchon pression et circulation.",



            "Comparer lecture capteur avec température externe fiable.",



        ],



    },



    "Direction": {



        "risk": "Élevé si perte de contrôle, coups, direction dure ou comportement imprévisible.",



        "hypotheses": {



            "Mécanique": [



                "Articulation, pivot, bushing, cylindre ou composant mécanique usé",



                "Jeu mécanique ou blocage physique dans la direction",



            ],



            "Électrique / commande": [



                "Commande électrique, valve pilotée ou capteur de direction à vérifier",



                "Faisceau ou alimentation de commande direction instable",



            ],



            "Hydraulique / pression": [



                "Pression hydraulique de direction insuffisante ou instable",



                "Valve orbitrol/commande direction qui colle ou fuit",



            ],



            "Capteur / signal": [



                "Capteur position/angle/pression direction incohérent",



                "Signal de retour direction mal interprété",



            ],



            "Module / logique": [



                "Module limite ou bloque une commande de direction assistée",



                "Interlock ou logique de sécurité direction à vérifier",



            ],



        },



        "tests": [



            "Vérifier niveau/qualité d’huile hydraulique et contamination.",



            "Mesurer pression direction selon procédure.",



            "Comparer réaction gauche/droite, froid/chaud, ralenti/régime.",



            "Inspecter cylindres, pivots, articulation, bushings et jeu.",



            "Lire codes et données live si direction assistée électroniquement.",



        ],



    },



    "PTO / accessoires": {



        "risk": "Variable, élevé si équipement entraîné peut bouger ou engager de façon imprévue.",



        "hypotheses": {



            "Mécanique": [



                "Embrayage PTO, arbre, clutch ou composant mécanique usé",



                "Accessoire entraîné bloqué ou charge mécanique excessive",



            ],



            "Électrique / commande": [



                "Solénoïde, relais, switch ou faisceau PTO intermittent",



                "Commande électrique/PTO non autorisée ou condition de sécurité absente",



            ],



            "Hydraulique / pression": [



                "Pression hydraulique/pneumatique insuffisante pour engagement",



                "Valve ou circuit de commande PTO à vérifier",



            ],



            "Capteur / signal": [



                "Capteur de position/vitesse PTO incohérent",



                "Retour d’état engagé/non engagé mal interprété",



            ],



            "Module / logique": [



                "Interlock de sécurité ou condition d’autorisation PTO non satisfaite",



                "Module bloque l’engagement à cause d’un état machine",



            ],



        },



        "tests": [



            "Vérifier conditions d’autorisation PTO selon machine.",



            "Lire codes liés à PTO/accessoire.",



            "Mesurer alimentation, ground et commande solénoïde/relais.",



            "Vérifier pression de commande si hydraulique/pneumatique.",



            "Surveiller données live : demande PTO, état engagé, vitesse.",



            "Inspecter mécaniquement arbre, clutch, linkage et sécurité.",



        ],



    },



}



def normalize_fault_nature(selected_nature: str, text: str) -> str:



    if selected_nature != "Inconnue / à déterminer":



        return selected_nature



    t = text.lower()



    if contains_any(t, ["mécanique", "bloqué", "usé", "cassé", "linkage", "jeu", "ajustement"]):



        return "Mécanique"



    if contains_any(t, ["courant", "voltage", "relais", "fusible", "solénoïde", "solenoide", "commande"]):



        return "Électrique / commande"



    if contains_any(t, ["pression", "hydraulique", "air", "valve", "pompe"]):



        return "Hydraulique / pression"



    if contains_any(t, ["capteur", "signal", "témoin", "temoin", "voyant"]):



        return "Capteur / signal"



    if contains_any(t, ["module", "tcu", "ecu", "interlock", "autorisation", "logique", "reset"]):



        return "Module / logique"



    return "Inconnue / à déterminer"



def detect_general_facts(machine, symptoms, dtcs, context, history) -> dict:



    text = f"{machine} {symptoms} {dtcs} {context} {history}".lower()



    dtc_list = extract_dtcs(text)



    facts = []



    conditions = []



    tests_done = []



    missing = []



    risk_flags = []



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



    if contains_any(text, ["reset", "redémarre", "redemarre", "arrête repart", "arrete repart", "redémarrage"]):



        facts.append("Reset / redémarrage change le comportement")



    if contains_any(text, ["pression sort", "pression est sortie", "pression sortie"]):



        facts.append("Pression/réaction observée après manipulation")



    if contains_any(text, ["frein s'applique", "frein s applique", "parking brake s'applique", "parking brake s applique"]):



        facts.append("Frein s’applique après manipulation")



    if contains_any(text, ["huile ok", "niveau huile ok", "niveau d’huile ok", "qualité huile ok", "huile propre"]):



        tests_done.append("Huile / niveau déclaré OK")



    if contains_any(text, ["filtre ok", "filtre remplacé", "filtre changé", "filtre neuf"]):



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



    if contains_any(text, ["frein", "brake", "stationnement", "parking brake"]):



        risk_flags.append("Système de freinage ou immobilisation impliqué")



    if contains_any(text, ["tombe au neutre", "perd la propulsion", "direction", "ne freine pas"]):



        risk_flags.append("Risque opérationnel ou sécurité")



    if not dtc_list and "Aucun code rapporté" not in facts:



        missing.append("Codes actifs/inactifs ou mention claire qu’il n’y en a pas")



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



        "raw_lines": split_lines(symptoms + "\n" + context + "\n" + history),



    }



def detect_field_deductions(machine, symptoms, dtcs, context, history) -> list[dict]:



    text = f"{machine} {symptoms} {dtcs} {context} {history}".lower()



    deductions = []



    sensor_action = contains_any(text, [



        "débranch", "debranch", "démanch", "demanch", "déconnect", "deconnect",



        "manipul", "bougé le capteur", "bouger le capteur", "capteur"



    ])



    positive_reaction = contains_any(text, [



        "fonctionne", "se remet", "revient", "s'applique", "s applique",



        "s'engage", "s engage", "pression sort", "pression est sortie",



        "témoin allume", "temoin allume", "lumière allume", "lumiere allume"



    ])



    if sensor_action and positive_reaction:



        deductions.append({



            "title": "Une action sur un capteur modifie le comportement du système",



            "deduction": (



                "Le fait qu’une action sur un capteur change le comportement indique que le circuit en aval "



                "peut probablement fonctionner. Il faut prioriser le capteur, son signal de retour, son connecteur, "



                "son faisceau ou l’interprétation du signal par le module."



            ),



            "priority_shift": [



                "Augmenter priorité : capteur / signal retour / connecteur / faisceau / module",



                "Réduire priorité : panne purement mécanique en aval, tant que la réaction positive est reproductible",



            ],



            "next_tests": [



                "Comparer alimentation, ground et signal de retour du capteur.",



                "Lire la valeur du capteur en données live pendant la commande.",



                "Bouger le connecteur/faisceau du capteur pendant surveillance live.",



                "Confirmer si la réaction est reproductible à chaque manipulation du capteur.",



            ],



            "preferred_nature": "Capteur / signal",



        })



    harness_action = contains_any(text, [



        "bouge le faisceau", "bougé le faisceau", "wiggle", "brasse le fil",



        "bouge le fil", "connecteur", "faisceau", "fil cassé", "fil coupé"



    ])



    symptom_changes = contains_any(text, [



        "apparaît", "apparait", "disparaît", "disparait", "revient",



        "arrête", "arrete", "repart", "fonctionne", "coupe"



    ])



    if harness_action and symptom_changes:



        deductions.append({



            "title": "Une action sur le faisceau/connecteur modifie la panne",



            "deduction": (



                "Si bouger un faisceau ou un connecteur fait apparaître ou disparaître la panne, "



                "la priorité devient connecteur, fil cassé, masse, alimentation ou mauvaise continuité."



            ),



            "priority_shift": [



                "Augmenter priorité : faisceau / connecteur / masse / alimentation / continuité",



                "Réduire priorité : remplacement de module ou pièce mécanique sans preuve",



            ],



            "next_tests": [



                "Faire un wiggle test contrôlé pendant lecture des données live.",



                "Mesurer chute de voltage sous charge.",



                "Inspecter pins, corrosion, tension des terminaux et frottement du faisceau.",



                "Tester continuité et résistance du fil pendant mouvement.",



            ],



            "preferred_nature": "Électrique / commande",



        })



    direct_power = contains_any(text, [



        "courant direct", "alimenté direct", "alimente direct", "power direct",



        "12v direct", "24v direct", "jumper", "shunt"



    ])



    function_works = contains_any(text, [



        "fonctionne", "marche", "s'applique", "s applique", "s'engage", "s engage",



        "active", "bouge", "clic", "clique"



    ])



    function_not_works = contains_any(text, [



        "ne fonctionne pas", "fonctionne pas", "ne marche pas", "rien ne bouge",



        "pas de clic", "pas de réaction", "pas de reaction"



    ])



    if direct_power and function_works:



        deductions.append({



            "title": "La fonction marche avec alimentation directe",



            "deduction": (



                "Si la fonction marche avec une alimentation directe, l’actionneur ou le circuit en aval "



                "est probablement capable de fonctionner. La priorité devient la commande, le relais, le module, "



                "l’autorisation logique, le faisceau ou l’alimentation normale."



            ),



            "priority_shift": [



                "Augmenter priorité : commande / relais / module / autorisation / faisceau amont",



                "Réduire priorité : actionneur complètement mort ou mécanique bloquée",



            ],



            "next_tests": [



                "Comparer alimentation directe vs alimentation commandée par le système.",



                "Vérifier relais, sortie module, conditions d’autorisation et sécurité.",



                "Mesurer voltage sous charge au connecteur pendant commande normale.",



                "Vérifier si le module demande réellement l’activation.",



            ],



            "preferred_nature": "Électrique / commande",



        })



    if direct_power and function_not_works:



        deductions.append({



            "title": "La fonction ne marche pas même avec alimentation directe",



            "deduction": (



                "Si l’alimentation directe ne produit aucune réaction, la priorité devient l’actionneur, "



                "la valve, le circuit hydraulique/pneumatique ou le mécanisme en aval."



            ),



            "priority_shift": [



                "Augmenter priorité : actionneur / solénoïde / valve / pression / mécanique",



                "Réduire priorité : commande amont seulement",



            ],



            "next_tests": [



                "Mesurer résistance de l’actionneur ou solénoïde.",



                "Confirmer ground et courant sous charge.",



                "Vérifier activation mécanique réelle.",



                "Mesurer pression ou mouvement en aval.",



            ],



            "preferred_nature": "Mécanique",



        })



    reset_changes = contains_any(text, [



        "redémarre", "redemarre", "reset", "arrête repart", "arrete repart",



        "après redémarrage", "apres redemarrage", "repart la machine"



    ])



    if reset_changes:



        deductions.append({



            "title": "Le redémarrage/reset change temporairement le comportement",



            "deduction": (



                "Si un redémarrage ou reset change le comportement, la priorité augmente pour la logique module, "



                "l’état mémorisé, l’autorisation de commande, un capteur incohérent ou une protection temporaire."



            ),



            "priority_shift": [



                "Augmenter priorité : module / état logique / capteur / autorisation / protection",



                "Ne pas conclure immédiatement à une panne mécanique pure",



            ],



            "next_tests": [



                "Lire les codes avant et après redémarrage.",



                "Comparer les états live avant/après reset.",



                "Identifier quelle condition revient au défaut après redémarrage.",



                "Vérifier si une protection ou interlock bloque la fonction.",



            ],



            "preferred_nature": "Module / logique",



        })



    return deductions



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



        "PTO / accessoires": ["pto", "prise de force", "accessoire", "souffleuse", "blower"],



    }



    for system, words in system_keywords.items():



        if contains_any(t, words):



            return system



    return "Inconnu"



def determine_active_nature(selected_nature: str, text: str, field_deductions: list[dict]) -> str:



    if selected_nature != "Inconnue / à déterminer":



        return selected_nature



    if field_deductions:



        return field_deductions[0].get("preferred_nature", "Inconnue / à déterminer")



    return normalize_fault_nature(selected_nature, text)



def build_hypotheses(primary_system: str, active_nature: str, detected: dict, field_deductions: list[dict]) -> list[dict]:



    module = SYSTEM_MODULES.get(primary_system)



    hypotheses = []



    for deduction in field_deductions:



        hypotheses.append({



            "title": "Déduction terrain : " + deduction["title"],



            "support": [



                deduction["deduction"],



                "Changement de priorité : " + " | ".join(deduction["priority_shift"]),



            ],



            "limits": [



                "Déduction prudente basée sur le comportement observé.",



                "À confirmer par mesure objective, données live, schéma ou procédure OEM.",



                "Ne pas conclure à une pièce sans test de confirmation.",



            ],



        })



    if not module:



        hypotheses.append({



            "title": "Information insuffisante pour orienter le diagnostic",



            "support": [



                "Aucun système clair n’a été sélectionné ou détecté.",



                "Les symptômes doivent être reliés à un système mécanique précis.",



            ],



            "limits": [



                "Ajouter système principal, codes, conditions, tests déjà faits et comportement exact.",



            ],



        })



        return hypotheses



    hypotheses_by_nature = module["hypotheses"]



    ordered_natures = []



    if active_nature in hypotheses_by_nature:



        ordered_natures.append(active_nature)



    for nature in ["Capteur / signal", "Électrique / commande", "Module / logique", "Hydraulique / pression", "Mécanique"]:



        if nature not in ordered_natures and nature in hypotheses_by_nature:



            ordered_natures.append(nature)



    facts = detected["facts"]



    tests_done = detected["tests_done"]



    conditions = detected["conditions"]



    for nature in ordered_natures:



        for item in hypotheses_by_nature[nature]:



            support = [



                f"Système principal : {primary_system}.",



                f"Nature priorisée : {active_nature}.",



                f"Catégorie de cette piste : {nature}.",



                "Symptôme/faits observés : " + ", ".join(facts) if facts else "Peu de faits confirmés dans l’entrée.",



                "Conditions : " + ", ".join(conditions) if conditions else "Conditions de panne à préciser.",



                "Tests déjà faits : " + ", ".join(tests_done) if tests_done else "Tests déjà faits non précisés.",



            ]



            limits = [



                "Hypothèse à vérifier, pas conclusion finale.",



                "Confirmer avec mesures, données live, schéma ou procédure OEM.",



                "Ne pas remplacer de pièce sans test de confirmation.",



            ]



            hypotheses.append({



                "title": item,



                "support": support,



                "limits": limits,



            })



    return hypotheses



def build_universal_tests(primary_system: str, active_nature: str, detected: dict, field_deductions: list[dict]) -> list[str]:



    deduction_tests = []



    for deduction in field_deductions:



        deduction_tests.extend(deduction["next_tests"])



    nature_tests = {



        "Mécanique": [



            "Inspecter physiquement le composant : jeu, usure, blocage, ajustement, mouvement réel.",



            "Confirmer que la commande arrive au composant mais que la réaction mécanique est absente ou anormale.",



            "Comparer mouvement demandé vs mouvement réel.",



        ],



        "Électrique / commande": [



            "Mesurer alimentation et ground sous charge, pas seulement à vide.",



            "Vérifier relais, fusibles, sortie module, connecteurs et continuité.",



            "Faire wiggle test pendant surveillance live.",



        ],



        "Hydraulique / pression": [



            "Mesurer pression réelle avec manomètre selon procédure.",



            "Comparer pression demandée vs pression réelle.",



            "Vérifier restriction, fuite interne, valve, pompe et retour.",



        ],



        "Capteur / signal": [



            "Mesurer alimentation, ground et signal de retour du capteur.",



            "Comparer valeur capteur réelle avec données live du module.",



            "Manipuler connecteur/faisceau du capteur pendant surveillance live.",



        ],



        "Module / logique": [



            "Lire états live du module : demande, autorisation, interlock, protection.",



            "Comparer comportement avant/après reset.",



            "Vérifier conditions de sécurité qui bloquent la commande.",



        ],



    }



    base_tests = [



        "Sécuriser la machine et confirmer si elle peut être utilisée sans risque.",



        "Reformuler le symptôme exact : ce qui arrive, quand, combien de fois, dans quelles conditions.",



        "Lire codes actifs, inactifs et historiques avec l’outil adapté.",



        "Comparer commande demandée vs réaction réelle avec données live si disponibles.",



    ]



    module = SYSTEM_MODULES.get(primary_system)



    specific_tests = module["tests"] if module else [



        "Identifier le système principal avant de conclure.",



        "Ajouter données live ou mesures objectives.",



        "Comparer avec schéma/manuel OEM.",



    ]



    selected_nature_tests = nature_tests.get(active_nature, [])



    return list(dict.fromkeys(deduction_tests + selected_nature_tests + base_tests + specific_tests))



def determine_severity(primary_system: str, detected: dict) -> tuple[str, str]:



    risk_flags = detected["risk_flags"]



    facts = detected["facts"]



    if primary_system == "Frein":



        return (



            "Critique",



            "Frein ou immobilisation impliqué : ne pas remettre en service tant que le fonctionnement réel n’est pas confirmé.",



        )



    if "Risque opérationnel ou sécurité" in risk_flags:



        return (



            "Élevé",



            "Risque opérationnel : diagnostic et validation requis avant utilisation normale.",



        )



    if primary_system in ["Transmission", "Direction"]:



        return (



            "Élevé",



            SYSTEM_MODULES.get(primary_system, {}).get("risk", "Risque élevé à valider."),



        )



    if "Surchauffe / température élevée" in facts:



        return (



            "Élevé",



            "Surchauffe ou température élevée : risque de dommage si ignoré.",



        )



    if primary_system in SYSTEM_MODULES:



        return (



            "Moyen à élevé",



            SYSTEM_MODULES[primary_system]["risk"],



        )



    return (



        "À évaluer",



        "Données insuffisantes. Analyse préliminaire seulement.",



    )



def build_prudence(primary_system: str, active_nature: str, detected: dict, field_deductions: list[dict]) -> list[str]:



    prudence = []



    for deduction in field_deductions:



        prudence.append("Déduction terrain détectée : " + deduction["title"])



    if detected["dtcs"]:



        prudence.append("Codes détectés : utiliser la description OEM exacte avant de conclure. Le code seul ne suffit pas.")



    if "Aucun code rapporté" in detected["facts"]:



        prudence.append("Aucun code ne veut pas dire aucun problème. Une panne mécanique, hydraulique ou électrique peut ne pas être mémorisée.")



    if "Courant / alimentation déclaré OK" in detected["tests_done"]:



        prudence.append("Courant présent ne confirme pas le fonctionnement réel : vérifier signal de retour, ground, charge et activation mécanique.")



    if active_nature == "Mécanique":



        prudence.append("Nature mécanique priorisée : ne pas laisser les mots capteur/courant/module détourner l’analyse sans preuve.")



    if active_nature in ["Électrique / commande", "Capteur / signal", "Module / logique"]:



        prudence.append("Nature commande/signal/module priorisée : confirmer avec données live et mesures, pas seulement avec présence de courant.")



    if primary_system == "Frein":



        prudence.append("Pour un frein, la validation mécanique réelle prime sur le témoin ou le courant mesuré.")



    prudence.append("MecaTech IA structure le diagnostic; la décision finale appartient au mécanicien qualifié.")



    return list(dict.fromkeys(prudence))



def confidence_label(detected: dict, field_deductions: list[dict]) -> str:



    score = 0



    if detected["dtcs"]:



        score += 2



    if detected["facts"]:



        score += 1



    if detected["conditions"]:



        score += 1



    if detected["tests_done"]:



        score += 1



    if field_deductions:



        score += 2



    if len(detected["raw_lines"]) >= 3:



        score += 1



    if score <= 1:



        return "Préliminaire — données limitées"



    if score <= 3:



        return "Structurée — nécessite tests"



    if score <= 5:



        return "Moyenne — validation terrain/OEM requise"



    return "Forte orientation — confirmation terrain/OEM requise"



def analyze_case(machine, symptoms, dtcs, context, history, selected_system, selected_nature):



    text = f"{machine} {symptoms} {dtcs} {context} {history}"



    primary_system = choose_primary_system(selected_system, text)



    detected = detect_general_facts(machine, symptoms, dtcs, context, history)



    field_deductions = detect_field_deductions(machine, symptoms, dtcs, context, history)



    active_nature = determine_active_nature(selected_nature, text, field_deductions)



    severity, risk = determine_severity(primary_system, detected)



    hypotheses = build_hypotheses(primary_system, active_nature, detected, field_deductions)



    tests = build_universal_tests(primary_system, active_nature, detected, field_deductions)



    prudence = build_prudence(primary_system, active_nature, detected, field_deductions)



    if primary_system == "Inconnu":



        summary = "Les informations ne permettent pas encore d’identifier clairement le système principal."



    else:



        summary = (



            f"Analyse centrée sur le système : {primary_system}. "



            f"Nature priorisée : {active_nature}. "



            "Le moteur classe les pistes selon le choix du mécanicien, les faits et les réactions terrain."



        )



    return {



        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),



        "version": "v0.4.2",



        "primary_system": primary_system,



        "active_nature": active_nature,



        "selected_nature": selected_nature,



        "summary": summary,



        "dtcs": detected["dtcs"],



        "facts": detected["facts"],



        "conditions": detected["conditions"],



        "tests_done": detected["tests_done"],



        "missing": detected["missing"],



        "risk_flags": detected["risk_flags"],



        "field_deductions": field_deductions,



        "severity": severity,



        "risk": risk,



        "hypotheses": hypotheses,



        "tests": tests,



        "prudence": prudence,



        "confidence_label": confidence_label(detected, field_deductions),



    }



st.title("🔧 MecaTech IA")



st.caption("Prototype MVP v0.4.2 — système + nature de panne + déduction terrain")



col1, col2, col3, col4 = st.columns(4)



with col1:



    st.metric("Version", "v0.4.2")



with col2:



    st.metric("Mode", "Général modulaire")



with col3:



    st.metric("Analyses", st.session_state.analysis_counter)



with col4:



    st.metric("Décision finale", "Mécanicien")



st.divider()



st.sidebar.title("Navigation")



page = st.sidebar.radio(



    "Menu",



    ["Diagnostic", "Historique", "Validation humaine", "À propos"]



)



if page == "Diagnostic":



    st.header("Console diagnostic atelier")



    st.markdown("""



    <div class="info-box">



    Version v0.4.2 : le système touché et la nature suspectée sont séparés.



    Les mots-clés enrichissent l’analyse, mais ne remplacent pas le choix du mécanicien.



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



                "Autre",



            ],



            key="machine_type",



        )



        brand_model = st.text_input(



            "Marque / modèle / année",



            placeholder="Ex: John Deere 772G 2007, Hitachi ZW180 2020",



            key="brand_model",



        )



        hours_km = st.text_input(



            "Heures / km",



            placeholder="Ex: 12 908 h ou inconnu",



            key="hours_km",



        )



    with c2:



        system = st.selectbox(



            "Système principal touché",



            [



                "Transmission",



                "Hydraulique",



                "Moteur",



                "Électrique",



                "Frein",



                "Refroidissement",



                "Direction",



                "PTO / accessoires",



                "Autre / inconnu",



            ],



            key="system",



        )



        fault_nature = st.selectbox(



            "Nature suspectée de la panne",



            [



                "Inconnue / à déterminer",



                "Mécanique",



                "Électrique / commande",



                "Hydraulique / pression",



                "Capteur / signal",



                "Module / logique",



            ],



            key="fault_nature",



        )



        dtcs = st.text_area(



            "Codes DTC / SPN / FMI",



            placeholder="Ex: TCU 522405.5 / SPN 3719 FMI 16 / aucun code actif",



            height=100,



            key="dtcs",



        )



    symptoms = st.text_area(



        "Symptômes observés",



        placeholder="Décris le problème : ce qui arrive, quand, conditions, bruit, témoin, comportement...",



        height=170,



        key="symptoms",



    )



    context = st.text_area(



        "Contexte terrain / tests déjà faits",



        placeholder="Ex: huile OK, filtre remplacé, courant au solénoïde OK, pression non testée, problème chaud/froid...",



        height=140,



        key="context",



    )



    history = st.text_area(



        "Historique machine connu",



        placeholder="Travaux récents, pièces remplacées, problème déjà arrivé, notes du technicien...",



        height=110,



        key="history",



    )



    st.divider()



    if st.button("🔍 Analyser le problème", type="primary", use_container_width=True):



        st.session_state.last_analysis = None



        st.session_state.analysis_counter += 1



        machine = f"{machine_type} | {brand_model} | {hours_km} | {system} | {fault_nature}"



        input_snapshot = {



            "machine_type": machine_type,



            "brand_model": brand_model,



            "hours_km": hours_km,



            "system": system,



            "fault_nature": fault_nature,



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



            selected_system=system,



            selected_nature=fault_nature,



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



            "real_cause": "",



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



            st.metric("Système", analysis["primary_system"])



        with b:



            st.metric("Nature priorisée", analysis["active_nature"])



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



        if analysis.get("field_deductions"):



            st.markdown("### Déductions terrain détectées")



            for deduction in analysis["field_deductions"]:



                with st.expander(deduction["title"], expanded=True):



                    st.write("**Déduction :**")



                    st.write(deduction["deduction"])



                    st.write("**Changement de priorité :**")



                    for item in deduction["priority_shift"]:



                        st.write(f"- {item}")



                    st.write("**Tests suivants recommandés :**")



                    for item in deduction["next_tests"]:



                        st.write(f"- {item}")



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



            "analysis": analysis,



        }



        st.download_button(



            "Télécharger le rapport JSON",



            data=json.dumps(report, ensure_ascii=False, indent=2),



            file_name=f"rapport_mecatech_ia_analyse_{analysis['run_id']}.json",



            mime="application/json",



        )



elif page == "Historique":



    st.header("Historique des diagnostics de cette session")



    if not st.session_state.cases:



        st.info("Aucun diagnostic dans cette session.")



    else:



        st.write(f"Nombre de diagnostics : {len(st.session_state.cases)}")



        for case in reversed(st.session_state.cases):



            analysis = case["analysis"]



            with st.expander(



                f"Analyse #{analysis['run_id']} — {analysis['primary_system']} — {analysis['active_nature']} — {analysis['timestamp']}"



            ):



                st.write("**Machine :**", case["machine"])



                st.write("**Résumé :**", analysis["summary"])



                st.write("**Sévérité :**", analysis["severity"])



                st.write("**Certitude :**", analysis["confidence_label"])



                st.write("**Empreinte entrée :**", analysis["input_hash"])



                if analysis["hypotheses"]:



                    st.write("**Hypothèse principale :**", analysis["hypotheses"][0]["title"])



                st.write("**Validation humaine :**", case.get("human_validation", "Non validé"))



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



        st.write("**Nature priorisée :**", analysis["active_nature"])



        st.write("**Hypothèse principale :**", analysis["hypotheses"][0]["title"])



        validation_options = [



            "Non validé",



            "Confirmé",



            "Partiellement confirmé",



            "Faux diagnostic",



            "À vérifier plus tard",



        ]



        validation = st.radio(



            "Résultat terrain",



            validation_options,



            index=validation_options.index(case.get("human_validation", "Non validé")),



        )



        real_cause = st.text_area(



            "Cause réelle trouvée / notes du technicien",



            value=case.get("real_cause", ""),



            height=140,



        )



        if st.button("Sauvegarder validation", type="primary"):



            case["human_validation"] = validation



            case["real_cause"] = real_cause



            st.success("Validation sauvegardée pour cette session.")



elif page == "À propos":



    st.header("À propos de MecaTech IA v0.4.2")



    st.write("""



    Cette version sépare deux choses importantes :



    1. Le système principal touché :



       frein, transmission, hydraulique, moteur, direction, etc.



    2. La nature suspectée de la panne :



       mécanique, électrique/commande, hydraulique/pression, capteur/signal ou module/logique.



    Pourquoi :



    Un problème de frein peut contenir des mots comme courant, capteur, TCU ou solénoïde



    sans devenir automatiquement un problème électrique. Le mécanicien doit pouvoir dire :



    “Je veux analyser ça comme un problème mécanique” ou “comme un problème capteur/signal”.



    Principe :



    - le système choisi par le mécanicien est prioritaire;



    - la nature suspectée choisie réordonne les hypothèses;



    - les mots-clés enrichissent l’analyse, mais ne décident pas seuls;



    - les déductions terrain peuvent aussi modifier la priorité;



    - aucune conclusion finale sans validation humaine/OEM.



    """)



st.divider()



st.caption("MecaTech IA v0.4.2 — Système + nature de panne + déduction terrain | Read the fault. Find the cause. Fix it — once.")

