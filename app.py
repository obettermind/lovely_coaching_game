import random
from urllib.parse import quote
import streamlit as st
from criteres import CRITERES, PAR_CLE
from coach import creer_fiche, prompt_image, rapport_reel, fin_de_partie
from comparer import comparer, QUESTIONS_MOI, analyser_moi
import gemini_client as gc
import donnees as dn
import db

st.set_page_config(page_title="BM_Portrait du Cœur", page_icon="💞", layout="wide")
st.markdown("""<style>[data-testid="stImage"] img{aspect-ratio:3/4;object-fit:cover;border-radius:12px;}</style>""", unsafe_allow_html=True)
st.title("💞 BM_Portrait du Cœur")
st.caption("Un jeu Better Mind pour les couples — mieux comprendre, mieux communiquer, mieux vivre à deux. "
           "Jeu de réflexion et de coaching bienveillant, ni thérapie ni diagnostic.")


def formulaire(prefix: str, groupes: list[str], exclure: tuple = ()) -> dict:
    """Affiche les critères d'un ou plusieurs groupes et renvoie {cle: index}."""
    choix = {}
    for g in groupes:
        st.markdown(f"**{g}**")
        cols = st.columns(3)
        crits = [c for c in CRITERES if c["groupe"] == g and c["cle"] not in exclure]
        for i, c in enumerate(crits):
            with cols[i % 3]:
                opts = c["options"]
                if len(opts) == 2:
                    lab = st.radio(c["label"], opts, key=f"{prefix}_{c['cle']}", horizontal=True)
                elif c.get("dimension") or c["cle"] in ("taille",):
                    lab = st.select_slider(c["label"], opts, value=opts[len(opts) // 2], key=f"{prefix}_{c['cle']}")
                else:
                    lab = st.selectbox(c["label"], opts, key=f"{prefix}_{c['cle']}")
                choix[c["cle"]] = opts.index(lab)
    return choix


def afficher_partenaire(p_choix, fiche, image, note, prompt=None, erreur_img=None):
    c1, c2 = st.columns([3, 2])
    with c1:
        if image:
            st.image(image, use_container_width=True)
        else:
            raison = ("quota gratuit d'images atteint" if erreur_img and ("429" in erreur_img or "RESOURCE_EXHAUSTED" in erreur_img)
                      else "génération impossible pour le moment")
            st.info(f"📷 Photo indisponible ({raison}). Le personnage et sa note restent valables.")
            if prompt:
                st.link_button("🔗 Ouvrir dans Gemini avec ce prompt", "https://gemini.google.com/app?q=" + quote(prompt))
                with st.expander("📋 Si le prompt ne s'est pas rempli : copie-le ici (icône en haut à droite)"):
                    st.code(prompt, language=None)
            if erreur_img:
                with st.expander("Détails techniques"):
                    st.code(erreur_img[:600], language=None)
    with c2:
        st.subheader(fiche.get("prenom", ""))
        st.caption(f"{fiche.get('metier','')} · {fiche.get('trait_dominant','')}")
        st.write(note)


# ====================================================================================
# NOUVELLE CONCEPTION : Portrait du cœur (pages JSON, images, suggestions de fin de partie)
# ====================================================================================
CLES_PC = ("pc_page", "pc_choix", "pc_images", "pc_sug")


def _init_pc():
    st.session_state.setdefault("pc_page", 0)
    st.session_state.setdefault("pc_choix", {})      # {id_critere: id_option}
    st.session_state.setdefault("pc_images", {})     # {id_option: variante tirée pour cette partie}
    st.session_state.setdefault("pc_sug", None)      # suggestions de fin de partie


def _reset_pc():
    for k in CLES_PC:
        st.session_state.pop(k, None)


def _image(oid: str, mem) -> dict:
    """Variante d'illustration de cette option, tirée une fois par partie (stable pendant la partie)."""
    imgs = st.session_state["pc_images"]
    if oid not in imgs:
        v = dn.tirer_image(oid, deja_vus=mem.deja_vus())
        imgs[oid] = v
        mem.noter(v["id"])
    return imgs[oid]


def _carte(oid: str, crit_id: str, mem):
    opt = dn.option(oid)
    v = _image(oid, mem)
    choisi = st.session_state["pc_choix"].get(crit_id) == oid
    with st.container(border=True):
        if v["chemin"].exists():
            st.image(str(v["chemin"]), use_container_width=True)
        else:
            st.markdown(f"🖼️ *{v['description']}*")      # texte de remplacement tant que l'image n'existe pas
        st.markdown(f"**{opt['libelle']}**")
        if st.button("✅ Choisi" if choisi else "Choisir", key=f"pc_btn_{oid}",
                     type="primary" if choisi else "secondary", use_container_width=True):
            st.session_state["pc_choix"][crit_id] = oid
            st.rerun()


def _ecran_resultat(choix: dict):
    sug = st.session_state["pc_sug"]
    prenom = st.session_state.get("pc_prenom", "").strip()
    st.subheader(f"Portrait de {prenom}" if prenom else "Votre portrait du cœur")
    st.markdown(dn.decrire_ids(choix))

    imgs = [(oid, st.session_state["pc_images"].get(oid)) for oid in choix.values()]
    imgs = [(oid, v) for oid, v in imgs if v and v["chemin"].exists()]
    if imgs:
        cols = st.columns(min(len(imgs), 4))
        for k, (oid, v) in enumerate(imgs):
            with cols[k % len(cols)]:
                st.image(str(v["chemin"]), caption=dn.libelle(oid), use_container_width=True)

    st.markdown("### Ce que vous pouvez faire maintenant")
    st.success("🎁 **Aujourd'hui, vous pourriez lui proposer…**  \n" + sug["proposer"])
    st.info("💬 **Vous pourriez lui dire…**  \n" + sug["dire"])
    st.warning("⚖️ **À éviter ou à doser**  \n" + sug["doser"])
    st.success("🎯 **Défi de la semaine**  \n" + sug["defi"])
    st.caption("🪞 " + sug["test_realite"])
    st.caption(sug["avertissement"])

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("🔄 D'autres suggestions", key="pc_autres", use_container_width=True):
        st.session_state["pc_sug"] = fin_de_partie(choix, dn.Memoire())
        st.rerun()
    if b2.button("➕ Ajouter le défi à mes défis", key="pc_defi", use_container_width=True):
        db.ajouter_defi(sug["defi"])
        st.toast("Défi ajouté à l'onglet Défis.")
    if b3.button("💾 Garder ce portrait", key="pc_garder", use_container_width=True):
        propre = {k: v for k, v in sug.items() if not k.startswith("_")}
        db.sauver_partenaire("portrait", "Portrait du cœur", choix, propre,
                             ", ".join(dn.libelle(o) for o in choix.values()))
        st.toast("Portrait gardé (sans nom ni identité).")
    if b4.button("🆕 Nouvelle partie", key="pc_reset", type="primary", use_container_width=True):
        _reset_pc()
        st.rerun()


def _portraits_gardes():
    portraits = db.lister_partenaires("portrait")
    if not portraits:
        return
    with st.expander(f"📚 Mes portraits gardés ({len(portraits)})"):
        for p in portraits:
            try:
                libs = ", ".join(dn.libelle(o) for o in p["choix"].values())
            except KeyError:
                libs = "(critères d'une ancienne version)"
            st.markdown(f"**{p['cree'][:10]}** — {libs}")


def onglet_portrait():
    _init_pc()
    pages = dn.pages()
    if not pages:
        st.error("Aucune page trouvée dans le dossier data (fichiers page*.json).")
        return
    choix = st.session_state["pc_choix"]

    if st.session_state["pc_sug"] is not None:
        _ecran_resultat(choix)
        _portraits_gardes()
        return

    mem = dn.Memoire()
    n = len(pages)
    i = min(st.session_state["pc_page"], n - 1)
    page = pages[i]

    if i == 0:
        c1, c2 = st.columns(2)
        c1.text_input("Prénom ou surnom (facultatif, jamais conservé)", key="pc_prenom")
        c2.radio("Vous décrivez…", ["Mon partenaire actuel", "Un partenaire potentiel"],
                 key="pc_cadre", horizontal=True)
        st.caption("Vous décrivez votre perception : c'est un miroir pour vous, pas un jugement sur l'autre.")

    st.progress((i + 1) / n, text=f"Page {i + 1} sur {n} · {page['page']['titre']}")
    st.caption(page["page"]["sous_titre"])

    for crit in page["criteres"]:
        st.markdown(f"#### {crit['question']}")
        cols = st.columns(len(crit["options"]))
        for col, o in zip(cols, crit["options"]):
            with col:
                _carte(o["id"], crit["id"], mem)

    complet = all(c["id"] in choix for c in page["criteres"])
    if not complet:
        st.caption("Choisissez une carte pour chaque question pour continuer.")
    b1, b2, _ = st.columns([1, 1.5, 3])
    if i > 0 and b1.button("← Précédent", key="pc_prev"):
        st.session_state["pc_page"] = i - 1
        st.rerun()
    if i < n - 1:
        if b2.button("Suivant →", key="pc_next", type="primary", disabled=not complet):
            st.session_state["pc_page"] = i + 1
            st.rerun()
    else:
        if b2.button("Voir mes suggestions ✨", key="pc_voir", type="primary", disabled=not complet):
            st.session_state["pc_sug"] = fin_de_partie(choix, dn.Memoire())
            st.rerun()
    _portraits_gardes()


tab0, tab1, tab2, tab3, tab4 = st.tabs(["🆕 Portrait du cœur", "✨ Mon partenaire imaginaire",
                                        "🤝 Mon partenaire réel", "🎯 Défis", "🖼️ Galerie"])

# ------------------------------------------------------------------ PORTRAIT DU CŒUR (nouveau)
with tab0:
    onglet_portrait()

# ------------------------------------------------------------------ IMAGINAIRE
with tab1:
    choix = formulaire("ideal", ["Identité", "Physique", "Personnalité", "Relation"])
    c1, c2 = st.columns(2)
    go = c1.button("Révéler mon partenaire", type="primary")
    autre = c2.button("Autre version (même profil)") and "ideal_last" in st.session_state
    if go or autre:
        with st.spinner("Création du personnage…"):
            fiche = creer_fiche(choix, graine=random.randint(1, 10**6))
            prompt_img = prompt_image(choix, fiche)
            erreur_img = None
            try:
                img = gc.generer_image(prompt_img)
            except Exception as e:
                img, erreur_img = None, str(e)
            st.session_state["ideal_last"] = dict(choix=choix, fiche=fiche, img=img, prompt=prompt_img, erreur_img=erreur_img)
    if "ideal_last" in st.session_state:
        r = st.session_state["ideal_last"]
        afficher_partenaire(r["choix"], r["fiche"], r["img"], r["fiche"].get("note", ""), r.get("prompt"), r.get("erreur_img"))
        if st.button("💾 Garder dans ma galerie"):
            db.sauver_partenaire("ideal", r["fiche"].get("prenom", "Idéal"), r["choix"], r["fiche"],
                                 r["fiche"].get("note", ""), r["img"])
            st.success("Ajouté à la galerie.")

# ------------------------------------------------------------------ RÉEL
with tab2:
    st.markdown("### 1. Ton idéal")
    ideaux = db.lister_partenaires("ideal")
    if not ideaux and "ideal_last" not in st.session_state:
        st.info("Crée d'abord un partenaire imaginaire (onglet ✨) et garde-le dans la galerie : il servira de référence.")
        ideal = None
    else:
        noms = [f"{p['nom']} (#{p['id']})" for p in ideaux]
        if "ideal_last" in st.session_state:
            noms.insert(0, "Celui que je viens de créer")
        pick = st.selectbox("Partenaire de référence", noms)
        ideal = (st.session_state["ideal_last"]["choix"] if pick == "Celui que je viens de créer"
                 else ideaux[noms.index(pick) - (1 if "ideal_last" in st.session_state else 0)]["choix"])

    st.markdown("### 2. Ton partenaire réel (aucune photo, juste tes ressentis)")
    prenom = st.text_input("Son prénom (ou surnom)")
    reel = formulaire("reel", ["Personnalité", "Relation"], exclure=("environnement",))

    st.markdown("### 3. Et toi, quel partenaire es-tu ? (1 = rarement, 5 = toujours)")
    rep = {k: st.slider(q, 1, 5, 3, key=f"moi_{k}") for k, q in QUESTIONS_MOI}
    contexte = st.text_area("Un contexte à partager ? (facultatif : ce qui va bien, ce qui te préoccupe…)")

    if st.button("Obtenir mon coaching", type="primary", disabled=not (ideal and prenom)):
        with st.spinner("Analyse en cours…"):
            reel_complet = dict(reel)
            comp = comparer(ideal, reel_complet)
            moi = analyser_moi(rep)
            rap = rapport_reel(prenom, ideal, reel_complet, comp, moi, contexte)
            st.session_state["reel_last"] = dict(comp=comp, moi=moi, rap=rap, prenom=prenom, reel=reel_complet)
    if "reel_last" in st.session_state:
        r = st.session_state["reel_last"]
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Harmonie avec ton idéal", f"{r['comp']['score']} %")
        m2.metric("Ton score « partenaire »", f"{r['moi']['moyenne']} / 5")
        st.success(r["rap"]["resume"])
        if r["comp"]["harmonie"]:
            st.markdown("**Ce qui vous correspond déjà :** " + ", ".join(l["critere"] for l in r["comp"]["harmonie"] + r["comp"]["proches"]))
        if r["comp"]["complementarite"]:
            st.markdown("**Zones de complémentarité (à explorer, pas à corriger) :** "
                        + ", ".join(f"{l['critere']} (idéal : {l['ideal']} / réel : {l['reel']})" for l in r["comp"]["complementarite"]))
        a, b = st.columns(2)
        a.markdown(f"**Ce qui nourrit {r['prenom']}**\n" + "\n".join(f"- {x}" for x in r["rap"]["ce_qui_le_nourrit"]))
        b.markdown(f"**Ce qui peut le/la blesser**\n" + "\n".join(f"- {x}" for x in r["rap"]["ce_qui_le_blesse"]))
        st.markdown(f"**Faire le pont :** {r['rap']['ponts']}")
        st.markdown(f"**🪞 Miroir :** {r['rap']['miroir']}")
        st.info(f"🎯 Action de la semaine : {r['rap']['action_semaine']}")
        if st.button("Ajouter cette action à mes défis"):
            db.ajouter_defi(r["rap"]["action_semaine"])
            db.sauver_partenaire("reel", r["prenom"], r["reel"], r["rap"], r["rap"]["resume"])
            st.success("Défi ajouté.")

# ------------------------------------------------------------------ DÉFIS
with tab3:
    defis = db.lister_defis()
    if not defis:
        st.write("Aucun défi pour l'instant. Ils apparaissent après un coaching « partenaire réel » ou un « portrait du cœur ».")
    for did, texte, fait, cree in defis:
        c1, c2 = st.columns([6, 1])
        c1.write(("✅ " if fait else "⬜ ") + texte + f"  \n*{cree[:10]}*")
        if not fait and c2.button("Fait", key=f"d{did}"):
            db.valider_defi(did)
            st.rerun()

# ------------------------------------------------------------------ GALERIE
with tab4:
    gal = db.lister_partenaires("ideal")
    cols = st.columns(3)
    for i, p in enumerate(gal):
        with cols[i % 3]:
            if p["image"]:
                st.image(p["image"])
            st.markdown(f"**{p['nom']}**")
            st.caption(p["note"])