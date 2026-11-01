"""Comparaison idéal / réel, présentée comme des zones d'harmonie et de complémentarité (jamais de 'défauts')."""
from criteres import DIMENSIONS, valeur


def comparer(ideal: dict, reel: dict) -> dict:
    harmonie, complementarite, proches = [], [], []
    for d in DIMENSIONS:
        k = d["cle"]
        ecart = reel[k] - ideal[k]
        ligne = {"critere": d["label"], "ideal": valeur(ideal, k), "reel": valeur(reel, k), "ecart": ecart}
        if abs(ecart) == 0:
            harmonie.append(ligne)
        elif abs(ecart) == 1:
            proches.append(ligne)
        else:
            complementarite.append(ligne)
    total = len(DIMENSIONS)
    score = round(100 * (1 - sum(abs(reel[d["cle"]] - ideal[d["cle"]]) for d in DIMENSIONS) / (4 * total)))
    return {"score": score, "harmonie": harmonie, "proches": proches, "complementarite": complementarite}


# Auto-évaluation : « quel partenaire suis-je ? » (réponses de 1 à 5)
QUESTIONS_MOI = [
    ("ecoute", "Je l'écoute vraiment, sans regarder mon téléphone ni préparer ma réponse."),
    ("temps", "Je lui consacre du temps de qualité chaque semaine."),
    ("valorisation", "Je lui dis régulièrement ce que j'apprécie chez lui/elle."),
    ("gestes", "Je fais de petits gestes d'attention sans qu'on me le demande."),
    ("autonomie", "Je respecte son besoin d'espace et ses projets personnels."),
    ("conflit", "Quand nous sommes en désaccord, je cherche à comprendre avant de me défendre."),
]


def analyser_moi(reponses: dict) -> dict:
    ordre = sorted(reponses.items(), key=lambda kv: kv[1])
    libelle = dict(QUESTIONS_MOI)
    return {"moyenne": round(sum(reponses.values()) / len(reponses), 1),
            "force": [libelle[k] for k, v in ordre[::-1][:2]],
            "a_cultiver": [libelle[k] for k, v in ordre[:2]]}
