
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