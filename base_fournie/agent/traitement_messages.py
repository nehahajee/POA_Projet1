"""traitement_messages lit une demande d'un résident et trouve son émotion grâce au dictionnaire."""
import reconfort_io as rio

def reception_message(numero, message, id_resident, residents): 
    """
    Étant donné un numero, un message, l'id du résident et la liste des résidents
    la fonction reception message renvoie le numéro, l'id du résident , 
    sa position et une liste mots qui contient une version normalisée de la chaine de
    caractères message donnée en paramètres 
    """
    mots = rio.normaliser(message)
    for resident in residents: 
        if resident["id"] == id_resident: 
            return numero, id_resident, resident["position"], mots
    raise ValueError(f"Impossible de trouver le resident avec l'id: {id_resident}")


def trouver_emotion(mots,dico): 
    """
    Étant donné une liste de mots qui contient une version normalisée d'une chaine de caractères 
    et un dictionnaire (qui contient des entrées voir dictionnaire.json dans le dossier donnees)
    renvoie un degre et une emotion si trouvé sinon renvoie (None, None)
    """
    for m in mots: 
        for d in dico["entrees"]:
            if m in d["formes"] : 
                return d["emotion"], d["intensite"]
    return None , None

