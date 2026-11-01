"""Critères du jeu. Chaque option est stockée par son INDEX (0-4) pour pouvoir comparer."""

CRITERES = [
    # --- Identité
    {"cle": "sexe", "label": "Partenaire", "groupe": "Identité", "options": ["Femme", "Homme"]},
    {"cle": "age", "label": "Tranche d'âge", "groupe": "Identité",
     "options": ["25-30 ans", "30-40 ans", "40-50 ans", "50-60 ans"]},
    # --- Physique
    {"cle": "taille", "label": "Taille", "groupe": "Physique",
     "options": ["petite", "plutôt petite", "moyenne", "grande", "très grande"]},
    {"cle": "corpulence", "label": "Corpulence", "groupe": "Physique",
     "options": ["fine", "athlétique", "moyenne", "ronde", "forte"]},
    {"cle": "teint", "label": "Teint", "groupe": "Physique",
     "options": ["très clair", "clair", "mat", "métissé", "foncé"]},
    {"cle": "cheveux", "label": "Cheveux", "groupe": "Physique",
     "options": ["blonds", "châtains", "roux", "noirs", "gris / blancs"]},
    # --- Personnalité (dimensions comparables : échelle 0-4)
    {"cle": "intellect", "label": "Intellect", "groupe": "Personnalité", "dimension": True,
     "options": ["non", "un peu", "moyen", "beaucoup", "très intellectuel(le)"]},
    {"cle": "sport", "label": "Sport", "groupe": "Personnalité", "dimension": True,
     "options": ["non", "un peu", "moyen", "beaucoup", "très sportif(ve)"]},
    {"cle": "elegance", "label": "Élégance", "groupe": "Personnalité", "dimension": True,
     "options": ["non", "un peu", "moyenne", "beaucoup", "très élégant(e)"]},
    {"cle": "apparence", "label": "Humeur dominante", "groupe": "Personnalité", "dimension": True,
     "options": ["triste", "pensif(ve)", "serein(e)", "joyeux(se)", "très joyeux(se)"]},
    {"cle": "humour", "label": "Humour", "groupe": "Personnalité", "dimension": True,
     "options": ["sérieux(se)", "discret(e)", "moyen", "drôle", "très drôle"]},
    {"cle": "sensibilite", "label": "Expression des émotions", "groupe": "Personnalité", "dimension": True,
     "options": ["très réservé(e)", "pudique", "équilibré(e)", "expressif(ve)", "très émotif(ve)"]},
    {"cle": "independance", "label": "Besoin d'indépendance", "groupe": "Personnalité", "dimension": True,
     "options": ["très fusionnel(le)", "fusionnel(le)", "équilibré(e)", "indépendant(e)", "très indépendant(e)"]},
    # --- Relation
    {"cle": "langage_amour", "label": "Langage d'amour principal", "groupe": "Relation",
     "options": ["mots valorisants", "temps de qualité", "cadeaux", "services rendus", "contact physique"]},
    {"cle": "environnement", "label": "Son environnement", "groupe": "Relation",
     "options": ["appartement citadin", "maison avec jardin", "bord de mer", "montagne",
                 "atelier créatif", "café-librairie"]},
]

PAR_CLE = {c["cle"]: c for c in CRITERES}
DIMENSIONS = [c for c in CRITERES if c.get("dimension")]


def valeur(choix: dict, cle: str) -> str:
    return PAR_CLE[cle]["options"][choix[cle]]


def decrire(choix: dict) -> str:
    """Texte lisible des choix (pour les prompts)."""
    return "\n".join(f"- {c['label']} : {valeur(choix, c['cle'])}" for c in CRITERES if c["cle"] in choix)
