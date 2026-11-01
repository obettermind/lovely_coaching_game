"""Variation contrôlée + règles de cohérence : mêmes choix => images différentes mais jamais contradictoires."""
import random
from criteres import valeur

TENUES_ELEGANTES = ["costume ajusté", "robe/chemisier soigné", "manteau long raffiné", "tenue sobre et impeccable"]
TENUES_DECONTRACTEES = ["pull ample", "jean et t-shirt", "chemise en lin", "tenue confortable"]
TENUES_SPORT = ["tenue de sport technique", "veste de running", "t-shirt athlétique"]
LUMIERES = ["lumière dorée de fin d'après-midi", "lumière douce du matin", "lumière chaude d'intérieur",
            "ciel couvert et lumière diffuse"]
DECORS = {
    "appartement citadin": ["salon lumineux avec baie vitrée", "balcon sur les toits", "cuisine ouverte moderne"],
    "maison avec jardin": ["terrasse devant un jardin fleuri", "véranda avec plantes", "salon cosy donnant sur le jardin"],
    "bord de mer": ["terrasse face à la mer", "promenade au bord de l'eau", "petite crique"],
    "montagne": ["chalet avec cheminée", "sentier de montagne", "terrasse en bois face aux sommets"],
    "atelier créatif": ["atelier avec toiles et outils", "studio de musique", "bureau d'artiste plein de livres"],
    "café-librairie": ["coin lecture d'une librairie", "table de café près d'une fenêtre", "mezzanine remplie de livres"],
}
VUES = {
    "appartement citadin": "à travers les fenêtres, une vue urbaine (immeubles, toits ou rue), aucun jardin",
    "maison avec jardin": "à travers les fenêtres, un jardin verdoyant",
    "bord de mer": "la mer visible, ambiance maritime",
    "montagne": "des sommets ou une forêt visibles, ambiance de montagne",
    "atelier créatif": "pas de vue extérieure marquée, l'atelier est le sujet",
    "café-librairie": "la rue visible derrière la vitrine, ambiance de quartier",
}
POSES = ["regard doux vers l'objectif", "léger sourire, de trois-quarts", "en pleine activité, naturel(le)", "assis(e) détendu(e)"]


def _humeur_expression(i):
    return ["expression mélancolique mais digne", "expression pensive et profonde", "expression sereine",
            "sourire franc", "grand sourire radieux"][i]


def construire_contraintes(choix: dict, graine: int | None = None) -> dict:
    """Retourne des éléments visuels cohérents avec les choix, avec variation aléatoire filtrée."""
    rnd = random.Random(graine)
    env = valeur(choix, "environnement")
    if choix["elegance"] >= 3:
        tenue = rnd.choice(TENUES_ELEGANTES)
    elif choix["sport"] >= 3 and choix["elegance"] <= 2:
        tenue = rnd.choice(TENUES_SPORT)
    else:
        tenue = rnd.choice(TENUES_DECONTRACTEES)
    decor = rnd.choice(DECORS[env])
    # un décor négligé est exclu pour une personne très élégante : on impose "ordonné"
    ambiance = "décor soigné et ordonné" if choix["elegance"] >= 3 else "décor naturel et vécu"
    lumiere = rnd.choice(LUMIERES)
    if choix["apparence"] <= 1:                 # humeur triste/pensive : pas de lumière trop éclatante
        lumiere = "lumière douce et tamisée"
    if choix["intellect"] >= 3 and env not in ("bord de mer", "montagne") and "livres" not in decor and rnd.random() < 0.6:
        decor += ", avec des livres visibles"
    return {"tenue": tenue, "decor": decor, "ambiance": ambiance, "lumiere": lumiere,
            "pose": rnd.choice(POSES), "vue": VUES[env], "expression": _humeur_expression(choix["apparence"])}
