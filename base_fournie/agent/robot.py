"""Perception, memoire et action du robot (feature/robot).

    CarteMentale : ce que le robot sait de l'appartement (la memoire).
    Robot        : etat du robot, perception et actions (a venir).

Le robot ne lit jamais la grille de la carte : il ne connait que ce qu'il
a percu, plus les positions donnees au depart (enonce 3.2).
"""

from deplacement import case_voisine

# Symbole utilise par afficher() pour chaque type de case connu.
SYMBOLES = {
    "mur": "#",
    "libre": ".",
    "armoire": "A",
    "dictionnaire": "D",
    "resident": "P",
}


class CarteMentale:
    """
    Carte que le robot construit au fil de ses perceptions, distincte de la
    carte reelle (enonce 7).

    On ne stocke que les cases connues, dans un dictionnaire
    {(ligne, colonne): type}, ou type vaut "mur", "libre", "armoire",
    "dictionnaire" ou "resident". Une case absente du dictionnaire est
    inconnue, et on la suppose libre : c'est l'hypothese optimiste de
    l'annexe B.5. Grace a elle, si le parcours en largeur ne trouve aucun
    chemin sur cette carte, il n'en existe aucun en realite (annexe B.6).

    Au depart, le robot connait deja la position de l'armoire, du
    dictionnaire et des residents (enonce 3.2) : on les inscrit tout de
    suite, pour ne jamais planifier un chemin qui les traverse.
    exemple : carte = CarteMentale(9, 13, (6, 4), (7, 6), [(6, 11), (3, 3)])
              carte.est_traversable((6, 7)) donne True (inconnue)
    """

    def __init__(self, hauteur, largeur, armoire, dictionnaire, residents):
        self.hauteur = hauteur
        self.largeur = largeur
        self.cases = {}
        self.cases[tuple(armoire)] = "armoire"
        self.cases[tuple(dictionnaire)] = "dictionnaire"
        for position in residents:
            self.cases[tuple(position)] = "resident"

    def dans_la_grille(self, case):
        """Vrai si case est a l'interieur des dimensions de l'appartement."""
        ligne, colonne = case
        if ligne >= 0 and ligne <= self.hauteur - 1:
            if colonne >= 0 and colonne <= self.largeur - 1:
                return True
        return False

    def est_au_bord(self, case):
        """Vrai si case est sur le bord de la grille, qui est toujours un
        mur (enonce 3.1)."""
        ligne, colonne = case
        if ligne == 0 or ligne == self.hauteur - 1:
            return True
        if colonne == 0 or colonne == self.largeur - 1:
            return True
        return False

    def type_case(self, case):
        """Type connu de case, ou "inconnu" si le robot ne l'a jamais percue."""
        return self.cases.get(tuple(case), "inconnu")

    def est_traversable(self, case):
        """Vrai si le robot peut planifier un passage par case : jamais hors
        de la grille ni sur le bord, et seulement si la case est libre ou
        inconnue (supposee libre, annexe B.5)."""
        if self.dans_la_grille(case) == False or self.est_au_bord(case) == True:
            return False
        else:
            type = self.type_case(case)
            if type == "libre" or type == "inconnu":
                return True
            return False

    def mettre_a_jour(self, position, perception):
        """Inscrit la case du robot (forcement libre) et ses 4 voisines,
        perception etant par exemple {"N": "libre", "S": "mur", ...}."""
        self.cases[tuple(position)] = "libre"
        for direction, valeur in perception.items():
            self.cases[case_voisine(position, direction)] = valeur

    def afficher(self, position_robot=None):
        """Carte mentale en texte : "@" pour le robot, "?" pour une case
        jamais vue, "#" pour le bord, et SYMBOLES pour le reste."""
        lignes = []
        for i in range(self.hauteur):
            texte = ""
            for j in range(self.largeur):
                case = (i, j)
                if position_robot is not None and case == tuple(position_robot):
                    texte += "@"
                elif case in self.cases:
                    texte += SYMBOLES[self.cases[case]]
                elif self.est_au_bord(case):
                    texte += "#"
                else:
                    texte += "?"
            lignes.append(texte)
        return "\n".join(lignes)
