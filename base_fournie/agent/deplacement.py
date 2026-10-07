"""Deplacement generique du robot (feature/deplacement).

Fonctions utilisees par deplacement_dict(), deplacement_resident() et
deplacement_case_depart() :

    trouver_chemin(position_actuelle, destination, carte)   -> chemin | None
    deplacement(chemin, robot)                              -> bool
    rejoindre(destination, robot)                           -> bool

Rappel de l'enonce (3.2) : le robot ne connait pas les murs. On ne lit donc
JAMAIS le champ "grille" ici : trouver_chemin travaille sur la CARTE MENTALE
du robot (voir carte_mentale.py), et suppose libre tout ce qu'il n'a pas
encore vu (hypothese optimiste, annexe B.5).

Contrat attendu de `carte` (carte mentale) :
    carte.est_traversable((ligne, colonne)) -> bool

Contrat attendu de `robot` :
    robot.position : (ligne, colonne) actuelle
    robot.carte    : la carte mentale
    robot.avancer(direction) : execute UNE action AVANCER ("N", "S", "E", "O"),
        la journalise dans la trace, met a jour robot.position, puis percoit
        les 4 cases voisines et met a jour robot.carte.
"""

from collections import deque

# Effet de chaque direction sur (ligne, colonne) -- enonce 3.1.
# L'ordre est fixe : il rend le choix entre deux chemins de meme longueur
# deterministe (utile pour comparer des traces et pour deboguer).
DIRECTIONS = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "O": (0, -1),
}


# ---------------------------------------------------------------------------
# Petits outils sur les coordonnees
# ---------------------------------------------------------------------------

def case_voisine(position, direction):
    """Case obtenue en faisant un pas dans `direction` depuis `position`."""
    dl, dc = DIRECTIONS[direction]
    return (position[0] + dl, position[1] + dc)


def cases_adjacentes(position):
    """Les 4 cases orthogonalement adjacentes, dans l'ordre N, S, E, O.

    Utile pour construire la destination quand la cible (dictionnaire,
    armoire, resident) n'est pas traversable : le robot doit se placer sur
    une case libre adjacente (enonce 3.1).
    """
    return [case_voisine(position, d) for d in DIRECTIONS]


def direction_vers(depart, suivante):
    """Direction ("N", "S", "E", "O") pour passer de `depart` a `suivante`.

    Leve ValueError si les deux cases ne sont pas orthogonalement voisines.
    """
    for direction in DIRECTIONS:
        if case_voisine(depart, direction) == tuple(suivante):
            return direction
    raise ValueError(f"{depart} et {suivante} ne sont pas adjacentes")


def _en_ensemble(destination):
    """Accepte une case (l, c) ou une collection de cases ; renvoie un set."""
    if (len(destination) == 2
            and all(isinstance(x, int) for x in destination)):
        return {tuple(destination)}
    return {tuple(case) for case in destination}


# ---------------------------------------------------------------------------
# Planification : parcours en largeur sur la carte mentale
# ---------------------------------------------------------------------------

def trouver_chemin(position_actuelle, destination, carte):
    """Plus court chemin de `position_actuelle` a `destination` sur `carte`.

    `destination` est soit une case (ligne, colonne), soit une collection de
    cases : le chemin vers la plus proche est alors renvoye (typiquement les
    cases libres adjacentes a une cible non traversable).

    Retourne la liste des cases a parcourir, depart et arrivee inclus
    (donc [position_actuelle] si on y est deja), ou None si la carte
    mentale ne permet d'atteindre aucune destination.

    Comme la carte mentale contient au moins autant de cases libres que la
    realite (annexe B.6), None prouve qu'aucun chemin n'existe pour de bon.
    """
    depart = tuple(position_actuelle)
    arrivees = _en_ensemble(destination)

    if depart in arrivees:
        return [depart]

    # `predecesseur` sert deux fois : marquer les cases deja vues, et
    # reconstruire le chemin a l'envers (annexe B.4).
    predecesseur = {depart: None}
    file = deque([depart])  # file (FIFO), pas pile : sinon ce n'est plus
                            # un plus court chemin

    while file:
        courant = file.popleft()
        for voisin in cases_adjacentes(courant):
            if voisin in predecesseur:
                continue
            if not carte.est_traversable(voisin):
                continue
            predecesseur[voisin] = courant
            if voisin in arrivees:
                return _reconstruire(predecesseur, voisin)
            file.append(voisin)

    return None


def _reconstruire(predecesseur, case):
    chemin = [case]
    while predecesseur[chemin[-1]] is not None:
        chemin.append(predecesseur[chemin[-1]])
    chemin.reverse()
    return chemin


# ---------------------------------------------------------------------------
# Execution du deplacement
# ---------------------------------------------------------------------------

def deplacement(chemin, robot):
    """Suit `chemin` pas a pas. True si l'arrivee est atteinte, False sinon.

    Avant chaque pas, on verifie que la case suivante est toujours
    traversable d'apres la carte mentale : le robot a percu ses voisines a
    l'arrivee sur la case courante, donc un mur decouvert en route est deja
    connu ici. On s'arrete alors AVANT de se cogner (un deplacement illegal
    annule les points, enonce 10) et on renvoie False : l'appelant doit
    replanifier (voir rejoindre()).

    Renvoie aussi False si `chemin` est None/vide ou ne part pas de la
    position du robot.
    """
    if not chemin:
        return False
    if tuple(chemin[0]) != tuple(robot.position):
        return False

    for suivante in chemin[1:]:
        if not robot.carte.est_traversable(suivante):
            return False  # plan devenu faux : mur decouvert en route
        robot.avancer(direction_vers(robot.position, suivante))
        if tuple(robot.position) != tuple(suivante):
            return False  # le pas n'a pas eu l'effet attendu

    return True


def rejoindre(destination, robot):
    """Amene le robot sur `destination` en replanifiant au besoin.

    C'est la boucle de l'annexe B.5 : planifier sur la carte mentale, avancer,
    et recommencer des qu'un mur decouvert invalide le plan. A utiliser dans
    deplacement_dict(), deplacement_resident() et deplacement_case_depart().

    Retourne True une fois arrive. Retourne False si la destination est
    inaccessible (preuve : le parcours en largeur echoue sur la carte
    mentale, voir trouver_chemin). Termine toujours : chaque replanification
    est causee par un mur nouvellement decouvert, et il n'y en a qu'un
    nombre fini.
    """
    precedent = None
    while True:
        chemin = trouver_chemin(robot.position, destination, robot.carte)
        if chemin is None:
            return False
        if deplacement(chemin, robot):
            return True
        if chemin == precedent:
            # Meme plan, meme echec : on tournerait en rond. Ne devrait
            # arriver que si robot.avancer ne deplace pas le robot.
            raise RuntimeError("deplacement sans progres : verifier robot.avancer")
        precedent = chemin