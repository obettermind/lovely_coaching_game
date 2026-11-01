"""Fiche idéale (mode imaginaire) et rapport de coaching (mode partenaire réel). Gemini + repli local.
Ajout : fin_de_partie() = suggestions de coaching tirées des pages JSON (via donnees.py)."""
import json
from criteres import decrire, valeur
from coherence import construire_contraintes
import gemini_client as gc
import donnees as d

CADRE = ("Cadre : jeu de réflexion et de coaching bienveillant, pas une thérapie ni un diagnostic. "
         "Évite les stéréotypes : le caractère découle des critères psychologiques, jamais de la corpulence, "
         "du teint ou de l'âge. Ton chaleureux, concret, en français, tutoiement.")


# ---------- Mode partenaire imaginaire ----------
def creer_fiche(choix: dict, graine=None) -> dict:
    cont = construire_contraintes(choix, graine)
    prompt = f"""{CADRE}
Crée la fiche d'un personnage FICTIF adulte correspondant exactement à ces choix :
{decrire(choix)}
Éléments visuels imposés (à respecter) : tenue = {cont['tenue']} ; décor = {cont['decor']} ; {cont['ambiance']} ;
{cont['lumiere']} ; pose = {cont['pose']} ; {cont['expression']}.
Réponds en JSON strict : {{"prenom": str, "metier": str, "trait_dominant": str, "details_visuels": str,
"note": "2 ou 3 phrases : comment ce genre de partenaire aime être traité + son côté psychologique"}}
Aucune contradiction entre les choix, les éléments visuels et la note."""
    try:
        fiche = gc.generer_json(prompt)
    except Exception as e:
        fiche = {"prenom": "Alex" if choix["sexe"] else "Sana", "metier": "créatif(ve)", "trait_dominant": valeur(choix, "apparence"),
                 "details_visuels": "", "note": ("Ce partenaire aime se sentir écouté et valorisé, surtout par "
                 f"{valeur(choix, 'langage_amour')}. Sous une apparence {valeur(choix, 'apparence')}, "
                 "il/elle cherche avant tout sécurité et sincérité."), "erreur": str(e)}
    fiche["contraintes"] = cont
    return fiche


def prompt_image(choix: dict, fiche: dict) -> str:
    c = fiche["contraintes"]
    return (f"Photographie réaliste d'une personne fictive adulte : {valeur(choix,'sexe').lower()}, {valeur(choix,'age')}, "
            f"taille {valeur(choix,'taille')}, corpulence {valeur(choix,'corpulence')}, teint {valeur(choix,'teint')}, "
            f"cheveux {valeur(choix,'cheveux')}. {c['expression']}, {c['pose']}. Tenue : {c['tenue']}. "
            f"Décor : {c['decor']} ({c['ambiance']}), {c['lumiere']}. Vue : {c.get('vue','')}. {fiche.get('details_visuels','')} "
            "Portrait mi-corps inclus dans son environnement, rendu naturel et respectueux, "
            "aucune ressemblance avec une personne réelle, aucun texte dans l'image.")


# ---------- Mode partenaire réel ----------
def rapport_reel(prenom: str, ideal: dict, reel: dict, comparaison: dict, moi: dict, contexte: str = "") -> dict:
    prompt = f"""{CADRE}
Tu es un coach de couple bienveillant. Voici le partenaire RÉEL de l'utilisateur ({prenom}), décrit par lui :
{decrire(reel)}
Son partenaire IDÉAL imaginaire : 
{decrire(ideal)}
Zones d'harmonie : {json.dumps(comparaison['harmonie'], ensure_ascii=False)}
Zones de complémentarité : {json.dumps(comparaison['complementarite'], ensure_ascii=False)}
Auto-évaluation de l'utilisateur (1-5) : moyenne {moi['moyenne']}, points forts {moi['force']}, à cultiver {moi['a_cultiver']}.
Contexte libre donné par l'utilisateur : {contexte or 'aucun'}
Réponds en JSON strict : {{"resume": "2 phrases positives sur {prenom}", "ce_qui_le_nourrit": [3 éléments],
"ce_qui_le_blesse": [3 éléments], "ponts": "comment rapprocher le réel de l'idéal SANS vouloir changer la personne (2-3 phrases)",
"action_semaine": "une action simple et datée mentalement, liée à son langage d'amour",
"miroir": "1-2 phrases sur ce que l'utilisateur peut cultiver chez lui/elle-même"}}
Règle d'or : l'idéal est un miroir des besoins de l'utilisateur, pas un standard à imposer."""
    try:
        return gc.generer_json(prompt)
    except Exception as e:
        k = valeur(reel, "langage_amour")
        return {"resume": f"{prenom} a ses propres qualités, à regarder avec curiosité.",
                "ce_qui_le_nourrit": [f"Le langage d'amour : {k}", "Se sentir écouté(e)", "Être remercié(e)"],
                "ce_qui_le_blesse": ["L'indifférence", "Les comparaisons", "Les critiques en public"],
                "ponts": "Partez des points d'harmonie et exprimez vos besoins sans reproche.",
                "action_semaine": f"Cette semaine, un geste lié à : {k}.",
                "miroir": "Choisissez une habitude à cultiver vous-même.", "erreur": str(e)}


# ---------- Nouvelle conception : suggestions de fin de partie (sans appel à Gemini) ----------
def fin_de_partie(choix_ids: dict, memoire=None) -> dict:
    """Quatre blocs : proposer, dire, doser, defi (+ test_realite et avertissement).
    choix_ids : {"affection": "aff_temps", "besoin": "bes_calme", "desaccord": "des_recul"}
    memoire : instance de donnees.Memoire (facultatif) pour éviter les répétitions d'une partie à l'autre."""
    vues = memoire.deja_vus() if memoire else ()
    sug = d.suggestions_fin_partie(choix_ids, deja_vues=vues)
    if memoire:
        memoire.noter(*sug["_utilises"])
    return sug