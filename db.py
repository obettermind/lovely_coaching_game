import sqlite3, json, os
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "partenaire.db")
IMG_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMG_DIR, exist_ok=True)


def _c():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS partenaires(
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, nom TEXT, choix TEXT, fiche TEXT,
        note TEXT, image TEXT, cree TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS defis(
        id INTEGER PRIMARY KEY AUTOINCREMENT, texte TEXT, fait INTEGER DEFAULT 0, cree TEXT)""")
    return c


def sauver_partenaire(type_, nom, choix, fiche, note, image_bytes=None) -> int:
    chemin = None
    with _c() as c:
        cur = c.execute("INSERT INTO partenaires(type,nom,choix,fiche,note,image,cree) VALUES(?,?,?,?,?,?,?)",
                        (type_, nom, json.dumps(choix), json.dumps(fiche, ensure_ascii=False), note, None,
                         datetime.now().isoformat(timespec="seconds")))
        pid = cur.lastrowid
        if image_bytes:
            chemin = os.path.join(IMG_DIR, f"p{pid}_{datetime.now():%H%M%S}.png")
            open(chemin, "wb").write(image_bytes)
            c.execute("UPDATE partenaires SET image=? WHERE id=?", (chemin, pid))
    return pid


def lister_partenaires(type_=None):
    with _c() as c:
        q = "SELECT id,type,nom,choix,fiche,note,image,cree FROM partenaires"
        rows = c.execute(q + (" WHERE type=?" if type_ else "") + " ORDER BY id DESC",
                         (type_,) if type_ else ()).fetchall()
    return [dict(id=r[0], type=r[1], nom=r[2], choix=json.loads(r[3]), fiche=json.loads(r[4]),
                 note=r[5], image=r[6], cree=r[7]) for r in rows]


def ajouter_defi(texte):
    with _c() as c:
        c.execute("INSERT INTO defis(texte,cree) VALUES(?,?)", (texte, datetime.now().isoformat(timespec="seconds")))


def lister_defis():
    with _c() as c:
        return c.execute("SELECT id,texte,fait,cree FROM defis ORDER BY id DESC").fetchall()


def valider_defi(did):
    with _c() as c:
        c.execute("UPDATE defis SET fait=1 WHERE id=?", (did,))
