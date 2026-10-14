NB_COLONNES = 8

def distance_roue(e1,e2,emotions): 
    """
        Étant donné deux émotions e1, e2 et la liste d'émotions correspondant à celles
        sur la roue de Plutchik (qui vont de 0 à 7), on cherche l'index des chaînes e1 et e2
        dans la liste des émotions en utilisant la fonction index(). On fait cela pour
        pouvoir calculer l'écart, et on renvoie l'écart minimal sur la roue (c'est
        pourquoi on renvoie le minimum entre écart et (longueur de la liste - écart)).
        La fonction renvoie donc un entier de 0 (même émotion) à 4 (émotions opposées).
        exemple : e1 est joie (index renverra 0) et e2 est colère (index renvoie 6),
        l'écart vaut 6 et l'autre côté 8 - 6 = 2. On prend le min entre 6 et 2,
        car on prend la distance minimum des deux côtés sur la roue : la distance est 2.
    """
    e1_index = emotions.index(e1)
    e2_index = emotions.index(e2)
    ecart = abs(e2_index - e1_index)
    return min(ecart, len(emotions)-ecart)

def calculer_candidats(emotion, intensite, emotions, intensites):
    """Liste ordonnee des 15 casiers candidats (enonce 6.2).

    Renvoie une liste de dictionnaires {"position", "type_remplacement",
    "tri"}, triee du casier le plus souhaitable au moins souhaitable.
    "type_remplacement" correspond au champ "repli" de la trace.
    Ne regarde jamais le contenu des casiers.
    """
    candidats = []
    i_emotion = emotions.index(emotion)
    i_intensite = intensites.index(intensite)

    for em in emotions:
        distance = distance_roue(em, emotion, emotions)
        if distance <= 2:
            i_em = emotions.index(em)
            if (i_em - i_emotion) % len(emotions) <= 2:
                sens = 0  
            else:
                sens = 1   

            for it in intensites:
                i_it = intensites.index(it)
                position_casier = [i_it, i_em]
                ecart_intensite = abs(i_it - i_intensite)

                if distance == 0 and ecart_intensite == 0:
                    type_remplacement = "aucun"
                elif distance == 0:
                    type_remplacement = "intensite"
                elif distance == 1:
                    type_remplacement = "voisine_1"
                else:
                    type_remplacement = "voisine_2"

                candidats.append({
                    "position": position_casier,
                    "type_remplacement": type_remplacement,
                    "tri": (distance, ecart_intensite, i_it, sens),
                })

    return sorted(candidats, key=lambda c: c["tri"])

def trajet_selecteur(depart, arrivee):
    """
    Prend en entrée le départ et l'arrivée sous forme de [ligne,colonne](casier de l'armoire).

    Renvoie le trajet à faire pour arrivée à la case arrivée en partant 
    de la case départ donné préalablement, c'est-à-dire une liste de directions.
    On fait d'abord le vertical, puis ensuite l'horizontal par le chemin le plus 
    court(annexes C.3).
    exemple: print(trajet_selecteur([1, 0], [1, 4]))  donne : ['E', 'E', 'E', 'E']
    """
    resultat = []

    diff_lignes = arrivee[0]-depart[0]
    if diff_lignes > 0 : 
        for _ in range(diff_lignes) : 
            resultat.append("S")
    elif diff_lignes < 0: 
        for _ in range(diff_lignes): 
            resultat.append("N")
    

    # pour les colonnes on fait modulo pour ne pas avoir de valeur 
    # négatif lorsqu'on calcule la différence , par exemple si on veut aller 
    # de 7 a 1 on obtient -6 mais en faisant modulo on obtient 2 ce qui correspond
    # bien au nombre de pas a faire pour arriver a 1 

    # a = nombre de pas vers la droite (E), nombre de colonnes - a = nombre
    # de pas vers la gauche (O). On regarde si on prend le chemin de gauche
    # ou de droite en comparant a avec le nombre de colonnes - a : à chaque
    # fois on prend le chemin qui coûte le moins (à égalité, on va à droite).
    a = (arrivee[1] - depart[1])%NB_COLONNES
    if a <= NB_COLONNES-a : 
        for _ in range(a): 
            resultat.append("E")
    else: 
        for _ in range(NB_COLONNES-a): 
            resultat.append("O")

    return resultat
    
