import gemini_client as gc

for m in ["gemini-3.1-flash-lite-image", "gemini-3.1-flash-image",
          "gemini-2.5-flash-image", "gemini-3.1-flash-image-preview"]:
    gc.IMAGE_MODEL = m
    try:
        img = gc.generer_image("Portrait simple d'une personne fictive souriante, fond neutre")
        print(m, "->", "OK" if img else "pas d'image")
    except Exception as e:
        print(m, "-> ERREUR", str(e)[:120])
