"""db.py : stockage PAR VISITEUR (session Streamlit).
Rien n'est écrit sur le serveur : chaque visiteur ne voit que ses propres portraits, défis et partenaires,
et tout disparaît à la fermeture de la page. Même interface qu'avant, donc app.py ne change pas.
"""
from datetime import datetime
import streamlit as st

_P, _D = "_db_partenaires", "_db_defis"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sauver_partenaire(type_, nom, choix, fiche, note, image_bytes=None) -> int:
    liste = st.session_state.setdefault(_P, [])
    pid = len(liste) + 1
    liste.append(dict(id=pid, type=type_, nom=nom, choix=choix, fiche=fiche, note=note,
                      image=image_bytes, cree=_now()))
    return pid


def lister_partenaires(type_=None):
    liste = st.session_state.get(_P, [])
    return [p for p in reversed(liste) if type_ is None or p["type"] == type_]


def ajouter_defi(texte):
    liste = st.session_state.setdefault(_D, [])
    liste.append(dict(id=len(liste) + 1, texte=texte, fait=0, cree=_now()))


def lister_defis():
    return [(d["id"], d["texte"], d["fait"], d["cree"]) for d in reversed(st.session_state.get(_D, []))]


def valider_defi(did):
    for d in st.session_state.get(_D, []):
        if d["id"] == did:
            d["fait"] = 1
