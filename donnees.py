"""donnees.py : charge les pages de critères (data/page*.json), tire images et suggestions
de façon aléatoire mais COHÉRENTE : chaque tirage reste dans le réservoir de l'option choisie.

Un « choix » est un dict {id_critere: id_option}, par exemple :
    {"affection": "aff_temps", "besoin": "bes_calme", "desaccord": "des_recul"}
(c'est l'équivalent, en identifiants lisibles, des anciens index de criteres.py).
"""
import json
import random
from functools import lru_cache
from pathlib import Path

RACINE = Path(__file__).resolve().parent
DATA = RACINE / "data"
FICHIER_MEMOIRE = DATA / "memoire_tirages.json"
BLOCS = ("proposer", "dire", "doser")


# ---------- Chargement ----------
@lru_cache(maxsize=1)
def pages() -> tuple:
    """Toutes les pages, triées par ordre (fichiers data/page*.json)."""
    lues = []
    for f in sorted(DATA.glob("page*.json")):
        with open(f, encoding="utf-8") as fh:
            lues.append(json.load(fh))
    lues.sort(key=lambda p: p["page"]["ordre"])
    return tuple(lues)


@lru_cache(maxsize=1)
def _index() -> dict:
    idx = {}
    for p in pages():
        for c in p["criteres"]:
            for o in c["options"]:
                idx[o["id"]] = {"option": o, "critere": c, "page": p["page"]}
    return idx


def option(oid: str) -> dict:
    try:
        return _index()[oid]["option"]
    except KeyError:
        raise KeyError(f"Option inconnue : {oid}") from None


def libelle(oid: str) -> str:
    return option(oid)["libelle"]


def meta() -> dict:
    return pages()[0]["meta"] if pages() else {}


# ---------- Choix ----------
def valider_choix(choix: dict) -> list:
    """Liste de problèmes (vide si le choix est valide)."""
    problemes = []
    for crit_id, oid in choix.items():
        info = _index().get(oid)
        if info is None:
            problemes.append(f"Option inconnue : {oid}")
        elif info["critere"]["id"] != crit_id:
            problemes.append(f"{oid} n'appartient pas au critère {crit_id}")
    return problemes


def decrire_ids(choix: dict) -> str:
    """Texte lisible des choix, pour les prompts (équivalent de criteres.decrire)."""
    lignes = []
    for crit_id, oid in choix.items():
        info = _index().get(oid)
        if info and info["critere"]["id"] == crit_id:
            lignes.append(f"- {info['critere']['question']} : {info['option']['libelle']}")
    return "\n".join(lignes)


# ---------- Tirages cohérents ----------
def tirer_image(oid: str, deja_vus=(), rng=random) -> dict:
    """Une variante d'illustration de CETTE option. Préfère les images qui existent
    et celles non vues récemment."""
    variantes = option(oid)["scene"]["variantes"]
    dispo = [v for v in variantes if (RACINE / v["fichier"]).exists()] or variantes
    frais = [v for v in dispo if v["id"] not in deja_vus]
    v = rng.choice(frais or dispo)
    return {**v, "chemin": RACINE / v["fichier"]}


def suggestions_fin_partie(choix: dict, deja_vues=(), rng=random) -> dict:
    """Les quatre blocs de fin de partie. Chaque bloc s'appuie sur une option différente
    quand c'est possible, pour que tous les critères choisis comptent."""
    oids = [o for o in choix.values() if o in _index()]
    if not oids:
        raise ValueError("Aucun choix valide pour les suggestions.")
    ordre = oids[:]
    rng.shuffle(ordre)

    def piocher(bloc, oid, exclure=()):
        pool = option(oid)["suggestions"].get(bloc, [])
        frais = [p for p in pool if p not in deja_vues and p not in exclure]
        return rng.choice(frais or [p for p in pool if p not in exclure] or pool) if pool else ""

    res = {"_options": {}}
    for i, bloc in enumerate(BLOCS):
        oid = ordre[i % len(ordre)]
        res[bloc] = piocher(bloc, oid)
        res["_options"][bloc] = oid

    # Défi : bloc "defi" du JSON s'il existe, sinon une idée « proposer » reformulée
    oid_defi = rng.choice(ordre)
    sug = option(oid_defi)["suggestions"]
    if sug.get("defi"):
        res["defi"] = piocher("defi", oid_defi)
    else:
        base = piocher("proposer", oid_defi, exclure=(res["proposer"],))
        res["defi"] = "Cette semaine : " + (base[:1].lower() + base[1:] if base else "")
    res["_options"]["defi"] = oid_defi

    tests = meta().get("test_realite", [])
    res["test_realite"] = rng.choice(tests) if tests else ""
    res["avertissement"] = meta().get("avertissement", "")
    res["_utilises"] = [res[b] for b in (*BLOCS, "defi")]
    return res


# ---------- Mode duo / comparaison (critères par identifiants) ----------
def comparer_ids(a: dict, b: dict) -> dict:
    """Harmonie = même option ; complémentarité = options différentes."""
    harmonie, compl = [], []
    for crit_id, oid_a in a.items():
        oid_b = b.get(crit_id)
        if oid_b is None or oid_a not in _index() or oid_b not in _index():
            continue
        question = _index()[oid_a]["critere"]["question"]
        if oid_a == oid_b:
            harmonie.append({"critere": question, "valeur": libelle(oid_a)})
        else:
            compl.append({"critere": question, "a": libelle(oid_a), "b": libelle(oid_b)})
    return {"harmonie": harmonie, "complementarite": compl}


# ---------- Mémoire anti-répétition ----------
class Memoire:
    """Retient les derniers tirages. Ici un simple fichier JSON (un seul joueur) ;
    pour plusieurs joueurs, stocker la même liste par session dans partenaire.db."""

    def __init__(self, fichier=FICHIER_MEMOIRE, taille=40):
        self.fichier, self.taille = Path(fichier), taille
        try:
            self.vus = json.loads(self.fichier.read_text(encoding="utf-8"))
        except Exception:
            self.vus = []

    def deja_vus(self) -> set:
        return set(self.vus)

    def noter(self, *elements):
        self.vus = (self.vus + [e for e in elements if e])[-self.taille:]
        try:
            self.fichier.write_text(json.dumps(self.vus, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass


# ---------- Contrôle des données ----------
def verifier() -> tuple:
    """(problèmes de structure, images manquantes)."""
    problemes, manquantes, vus = [], [], set()
    for p in pages():
        for c in p["criteres"]:
            for o in c["options"]:
                if o["id"] in vus:
                    problemes.append(f"Identifiant en double : {o['id']}")
                vus.add(o["id"])
                if len(o["scene"]["variantes"]) < 2:
                    problemes.append(f"{o['id']} : moins de 2 variantes d'image")
                for bloc in BLOCS:
                    if not o["suggestions"].get(bloc):
                        problemes.append(f"{o['id']} : bloc « {bloc} » vide")
                for v in o["scene"]["variantes"]:
                    if not (RACINE / v["fichier"]).exists():
                        manquantes.append(v["fichier"])
    return problemes, manquantes


if __name__ == "__main__":
    problemes, manquantes = verifier()
    print(f"{len(pages())} page(s) chargée(s), {len(_index())} option(s).")
    print("Structure :", "OK" if not problemes else "")
    for p in problemes:
        print("  -", p)
    print(f"Images manquantes : {len(manquantes)}")
    for m in manquantes[:10]:
        print("  -", m)
    if len(manquantes) > 10:
        print(f"  ... et {len(manquantes) - 10} autres")