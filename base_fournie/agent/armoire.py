NB_COLONNES = 8


class Roue:
    """
    Structure cyclique (enonce section 7) : une liste d'elements dont le
    dernier est voisin du premier. Sert pour la roue de Plutchik (les 8
    emotions) et pour les colonnes de l'armoire, qui bouclent de 7 a 0.

    Le sens horaire est celui des indices croissants, modulo la taille
    (annexe A).
    exemple : roue = Roue(["joie", "confiance", ..., "anticipation"])
              roue.voisin(7, 1) donne 0, roue.distance("joie", "colere") donne 2.
    """

    def __init__(self, elements):
        self.elements = list(elements)
        self.taille = len(self.elements)

    def indice(self, element):
        """Position de l'element sur la roue (ValueError s'il n'y est pas)."""
        return self.elements.index(element)

    def voisin(self, i, pas):
        """Indice atteint en partant de i et en faisant pas crans (pas > 0 :
        sens horaire, pas < 0 : sens antihoraire)."""
        return (i + pas) % self.taille

    def decalage(self, i, j):
        """Nombre de crans dans le sens horaire pour aller de i a j,
        entre 0 et taille - 1. Le modulo evite les valeurs negatives :
        de 7 a 1 on obtient 2 et non -6."""
        return (j - i) % self.taille

    def distance_indices(self, i, j):
        """Distance minimale entre i et j en tournant dans un sens ou dans
        l'autre : 0 (meme case) jusqu'a taille // 2 (case opposee)."""
        a = self.decalage(i, j)
        return min(a, self.taille - a)

    def distance(self, e1, e2):
        """Distance minimale entre deux elements de la roue."""
        return self.distance_indices(self.indice(e1), self.indice(e2))

    def est_horaire(self, i, j):
        """Vrai si j est atteint au plus court en tournant dans le sens
        horaire depuis i (a egalite, on considere le sens horaire)."""
        a = self.decalage(i, j)
        return a <= self.taille - a


def distance_roue(e1, e2, emotions):
    """
        Étant donné deux émotions e1, e2 et la liste d'émotions correspondant à celles
        sur la roue de Plutchik (qui vont de 0 à 7), on construit la Roue de ces
        émotions et on renvoie l'écart minimal entre e1 et e2 sur cette roue :
        on peut tourner dans les deux sens, donc on garde le plus petit des deux
        trajets. La fonction renvoie donc un entier de 0 (même émotion) à 4
        (émotions opposées).
        exemple : e1 est joie (indice 0) et e2 est colère (indice 6),
        l'écart vaut 6 et l'autre côté 8 - 6 = 2. On prend le min entre 6 et 2,
        car on prend la distance minimum des deux côtés sur la roue : la distance est 2.
    """
    return Roue(emotions).distance(e1, e2)


def calculer_candidats(emotion, intensite, emotions, intensites):
    """Liste ordonnee des 15 casiers candidats (enonce 6.2).

    Renvoie une liste de dictionnaires {"position", "type_remplacement",
    "tri"}, triee du casier le plus souhaitable au moins souhaitable.
    "position" est le casier [ligne, colonne] = [indice intensite, indice emotion].
    "type_remplacement" correspond au champ "repli" de la trace.
    "tri" est la cle de tri de 6.2 : (distance sur la roue, ecart d'intensite,
    intensite la plus faible d'abord, sens horaire (0) avant antihoraire (1)).
    Ne regarde jamais le contenu des casiers.
    """
    roue = Roue(emotions)
    candidats = []
    i_emotion = roue.indice(emotion)
    i_intensite = intensites.index(intensite)

    for i_em in range(roue.taille):
        distance = roue.distance_indices(i_emotion, i_em)
        if distance <= 2:
            if roue.est_horaire(i_emotion, i_em):
                sens = 0
            else:
                sens = 1

            for i_it in range(len(intensites)):
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

    Renvoie le trajet à faire pour arriver à la case arrivée en partant
    de la case départ donnée préalablement, c'est-à-dire une liste de directions
    pour l'action CHERCHER.
    On fait d'abord le vertical (les lignes ne bouclent pas), puis l'horizontal
    par le chemin le plus court sur la roue des colonnes (annexe C.3).
    exemples : trajet_selecteur([1, 0], [1, 4]) donne ['E', 'E', 'E', 'E']
               trajet_selecteur([2, 7], [0, 1]) donne ['N', 'N', 'E', 'E']
    """
    resultat = []

    diff_lignes = arrivee[0] - depart[0]
    if diff_lignes > 0:
        for _ in range(diff_lignes):
            resultat.append("S")
    elif diff_lignes < 0:
        for _ in range(-diff_lignes):
            resultat.append("N")

    # a = nombre de pas vers la droite (E), nombre de colonnes - a = nombre
    # de pas vers la gauche (O). On prend le chemin qui coûte le moins
    # (à égalité, on va à droite) : c'est est_horaire de la Roue.
    colonnes = Roue(range(NB_COLONNES))
    a = colonnes.decalage(depart[1], arrivee[1])
    if colonnes.est_horaire(depart[1], arrivee[1]):
        for _ in range(a):
            resultat.append("E")
    else:
        for _ in range(NB_COLONNES - a):
            resultat.append("O")

    return resultat


def fouiller_armoire(robot, candidats):
    """
    Fouille l'armoire en suivant la liste des candidats (enonce 6.2, annexe C.5).

    Entrée : robot, adjacent à l'armoire. On utilise seulement robot.selecteur
    (casier courant [ligne, colonne]), robot.contenu_casier (objet constaté dans
    le casier courant, None s'il est vide) et robot.chercher(direction), qui doit
    déplacer le sélecteur d'un casier ET mettre à jour robot.contenu_casier.
    candidats : la liste triée renvoyée par calculer_candidats.

    On visite les candidats dans l'ordre et on retient le premier candidat garni
    de la liste. Un casier simplement traversé compte comme vu : s'il est vide,
    on ne revient pas le vérifier. Un casier garni croisé en chemin n'est pas
    retenu tant que ce n'est pas son tour dans la liste.

    La fonction ne fait PAS l'action PRENDRE : c'est à l'appelant (decision.py)
    de la faire, le sélecteur étant laissé sur le casier choisi.

    Sortie : renvoie (position du casier, type de remplacement, objet), ou
    (None, None, None) si les 15 candidats sont vides : la demande échoue
    alors avec le motif "armoire vide".
    """
    casier_vus_vides = []
    for candidat in candidats:
        if candidat["position"] in casier_vus_vides:
            continue

        trajet = trajet_selecteur(robot.selecteur, candidat["position"])
        for direction in trajet:
            robot.chercher(direction)
            if robot.contenu_casier is None:
                casier_vus_vides.append(list(robot.selecteur))

        if robot.contenu_casier is None:
            # trajet vide : le sélecteur était déjà sur ce candidat
            casier_vus_vides.append(list(robot.selecteur))
        else:
            return candidat["position"], candidat["type_remplacement"], robot.contenu_casier

    return None, None, None
