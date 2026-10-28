"""Simulateur : le monde reel (feature/perception-memoire).

C'est le SEUL module (avec la validation des fichiers) autorise a lire le champ
`grille` de la carte et le champ `objet` des casiers (enonce 3.2 et 3.3).
L'agent (robot, decision, deplacement...) n'a pas le droit d'y toucher : il
interroge l'environnement uniquement via les trois methodes publiques ci-dessous.

    percevoir(position)      -> ce que le robot voit depuis `position`
    contenu_casier(casier)   -> l'objet du casier, ou None s'il est vide
    est_libre(position)      -> la case est-elle traversable ?

Les attributs internes commencent par un underscore : l'agent ne doit pas
les utiliser.
"""

# Symbole de la grille -> ce que le robot percoit (enonce 3.1 et 5.5).
# 'R' (case de depart) est une case libre comme les autres.
_PERCEPTION = {
    "#": "mur",
    ".": "libre",
    "R": "libre",
    "A": "armoire",
    "D": "dictionnaire",
    "P": "resident",
}

# Seules les cases '.' et 'R' sont traversables.
_TRAVERSABLES = (".", "R")

# Effet de chaque direction sur (ligne, colonne) -- enonce 3.1.
_DIRECTIONS = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "O": (0, -1),
}


class Environnement:
    def __init__(self, carte, armoire):
        """carte et armoire : les dictionnaires renvoyes par
        reconfort_io.charger_carte et reconfort_io.charger_armoire."""
        self._grille = list(carte["grille"])
        self._hauteur = len(self._grille)
        self._largeur = len(self._grille[0]) if self._grille else 0
        self._objets = {
            (casier["ligne"], casier["colonne"]): casier["objet"]
            for casier in armoire["casiers"]
        }

    # ------------------------------------------------------------------
    # Interface publique
    # ------------------------------------------------------------------

    def percevoir(self, position):
        """Les 4 cases orthogonalement adjacentes a `position`.

        Retourne {"N": ..., "S": ..., "E": ..., "O": ...} avec pour valeur
        "mur", "libre", "armoire", "dictionnaire" ou "resident". Rien de plus :
        pas de vision en ligne droite, pas de diagonale (enonce 3.2).
        """
        ligne, colonne = position
        return {
            direction: self._percevoir_case(ligne + dl, colonne + dc)
            for direction, (dl, dc) in _DIRECTIONS.items()
        }

    def contenu_casier(self, casier):
        """Objet present dans le casier [ligne, colonne], ou None s'il est vide.

        A appeler lorsque le robot est adjacent a l'armoire ET que le
        selecteur est sur ce casier.
        Un casier inconnu est considere comme vide.
        """
        return self._objets.get((casier[0], casier[1]))

    def est_libre(self, position):
        """True si le robot peut se tenir sur `position`.

        Garde-fou : le robot l'utilise pour verifier qu'un AVANCER est legal
        avant de l'executer (un deplacement illegal annule les points).
        Hors de la grille, murs, armoire, dictionnaire, residents : False.
        """
        ligne, colonne = position
        if not self._dans_la_grille(ligne, colonne):
            return False
        return self._grille[ligne][colonne] in _TRAVERSABLES

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _dans_la_grille(self, ligne, colonne):
        return 0 <= ligne < self._hauteur and 0 <= colonne < self._largeur

    def _percevoir_case(self, ligne, colonne):
        if not self._dans_la_grille(ligne, colonne):
            return "mur"  # le bord est toujours un mur 
        return _PERCEPTION[self._grille[ligne][colonne]]
