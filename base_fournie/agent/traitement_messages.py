import reconfort_io as rio

def reception_message(numero, message, id_resident, residents): 
    mots = rio.normaliser(message)
    for resident in residents: 
        if resident["id"] == id_resident: 
            return numero, id_resident, resident["position"], mots
    raise ValueError(f"Impossible de trouver le resident avec l'id: {id_resident}")
     
        