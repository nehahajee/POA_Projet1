"""Perception, mémoire et action du robot (feature/robot).

    CarteMentale : ce que le robot sait de l'appartement (la mémoire).
    Robot        : état du robot, perception et actions.

Le robot ne lit jamais la grille de la carte : il ne connaît que ce qu'il
a perçu, plus les positions données au départ (énoncé 3.2).
"""

from deplacement import case_voisine, cases_adjacentes
from armoire import Roue, NB_COLONNES

# Symbole utilisé par afficher() pour chaque type de case connu.
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
    carte réelle (énoncé 7).

    On ne stocke que les cases connues, dans un dictionnaire
    {(ligne, colonne): type}, où type vaut "mur", "libre", "armoire",
    "dictionnaire" ou "resident". Une case absente du dictionnaire est
    inconnue, et on la suppose libre : c'est l'hypothèse optimiste de
    l'annexe B.5. Grâce à elle, si le parcours en largeur ne trouve aucun
    chemin sur cette carte, il n'en existe aucun en réalité (annexe B.6).

    Exemple : carte = CarteMentale(9, 13, (6, 4), (7, 6), [(6, 11), (3, 3)])
              carte.est_traversable((6, 7)) donne True (case inconnue)
    """

    def __init__(self, hauteur, largeur, armoire, dictionnaire, residents):
        """Crée la carte mentale de départ : tout est inconnu, sauf l'armoire,
        le dictionnaire et les résidents, dont le robot connaît la position
        dès le départ (énoncé 3.2). On les inscrit tout de suite pour ne
        jamais planifier un chemin qui les traverse.

        Paramètres :
            hauteur, largeur : dimensions de l'appartement (entiers)
            armoire : position (ligne, colonne) de l'armoire
            dictionnaire : position (ligne, colonne) du dictionnaire
            residents : liste des positions (ligne, colonne) des résidents
        Renvoie : rien (constructeur).
        """
        self.hauteur = hauteur
        self.largeur = largeur
        self.cases = {}
        self.cases[tuple(armoire)] = "armoire"
        self.cases[tuple(dictionnaire)] = "dictionnaire"
        for position in residents:
            self.cases[tuple(position)] = "resident"

    def dans_la_grille(self, case):
        """Indique si une case se trouve à l'intérieur des dimensions de
        l'appartement.

        Paramètres :
            case : position (ligne, colonne)
        Renvoie : True si la case est dans la grille, False sinon.
        """
        ligne, colonne = case
        if ligne >= 0 and ligne <= self.hauteur - 1:
            if colonne >= 0 and colonne <= self.largeur - 1:
                return True
        return False

    def est_au_bord(self, case):
        """Indique si une case est sur le bord de la grille. Le bord est
        toujours un mur (énoncé 3.1) : le robot le sait sans l'avoir vu.

        Paramètres :
            case : position (ligne, colonne)
        Renvoie : True si la case est sur le bord, False sinon.
        """
        ligne, colonne = case
        if ligne == 0 or ligne == self.hauteur - 1:
            return True
        if colonne == 0 or colonne == self.largeur - 1:
            return True
        return False

    def type_case(self, case):
        """Donne ce que le robot sait d'une case.

        Paramètres :
            case : position (ligne, colonne)
        Renvoie : le type connu ("mur", "libre", "armoire", "dictionnaire",
            "resident"), ou "inconnu" si le robot ne l'a jamais perçue.
        """
        return self.cases.get(tuple(case), "inconnu")

    def est_traversable(self, case):
        """Indique si le robot peut planifier un passage par une case. C'est
        la méthode appelée par trouver_chemin() dans deplacement.py.
        Jamais hors de la grille ni sur le bord ; sinon, seulement si la case
        est libre ou inconnue (supposée libre, annexe B.5).

        Paramètres :
            case : position (ligne, colonne)
        Renvoie : True si la case est traversable, False sinon.
        """
        if self.dans_la_grille(case) == False or self.est_au_bord(case) == True:
            return False
        else:
            type = self.type_case(case)
            if type == "libre" or type == "inconnu":
                return True
            return False

    def mettre_a_jour(self, position, perception):
        """Inscrit dans la carte ce que le robot voit : sa propre case, qui
        est forcément libre, et ses 4 voisines.

        Paramètres :
            position : position (ligne, colonne) du robot
            perception : dictionnaire des 4 directions, par exemple
                {"N": "libre", "S": "mur", "E": "libre", "O": "mur"}
        Renvoie : rien (modifie la carte).
        """
        self.cases[tuple(position)] = "libre"
        for direction, valeur in perception.items():
            self.cases[case_voisine(position, direction)] = valeur

    def afficher(self, position_robot=None):
        """Dessine la carte mentale en texte, pour le débogage et la vidéo :
        "@" pour le robot, "?" pour une case jamais vue, "#" pour le bord, et
        les symboles de SYMBOLES pour le reste.

        Paramètres :
            position_robot : position (ligne, colonne) du robot, ou None pour
                ne pas l'afficher
        Renvoie : la carte sous forme de chaîne, une ligne de texte par ligne
            de la grille.
        """
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


class Robot:
    """
    Le robot de réconfort : son état (position, carte mentale, sélecteur de
    l'armoire, objet porté), sa perception et ses actions (énoncé 3.4 et 7).

    Chaque action suit le même ordre : vérifier qu'elle est légale (sinon
    ValueError, et rien n'est écrit dans la trace), journaliser le pas avec
    l'état AVANT l'action, modifier l'état, puis percevoir.

    Le robot n'interroge l'environnement que par env.percevoir(),
    env.est_libre() et env.contenu_casier() : il ne lit jamais la grille ni
    le contenu des casiers directement (énoncé 3.2 et 3.3).
    """

    def __init__(self, env, connaissances, casier_depart, trace):
        """Crée le robot à sa position de départ et lui fait percevoir ses
        quatre cases voisines.

        Paramètres :
            env : l'environnement (le simulateur), qui répond aux perceptions
            connaissances : ce que le robot sait au départ, au format de la
                carte JSON mais sans "grille" (dimensions, depart_robot,
                armoire, dictionnaire, residents)
            casier_depart : casier [ligne, colonne] où se trouve le sélecteur
                au début de la simulation
            trace : objet Trace de reconfort_io, où chaque action est écrite
        Renvoie : rien (constructeur).
        """
        self.env = env
        self.trace = trace
        self.selecteur = list(casier_depart)
        self.armoire = tuple(connaissances["armoire"]["position"])
        self.dictionnaire = tuple(connaissances["dictionnaire"]["position"])
        self.residents = {}
        for resident in connaissances["residents"]:
            self.residents[resident["id"]] = tuple(resident["position"])

        self.position = tuple(connaissances["depart_robot"])
        self.carte = CarteMentale(connaissances["dimensions"]["hauteur"], connaissances["dimensions"]["largeur"],
                                  self.armoire, self.dictionnaire, self.residents.values())

        self.objet_porte = None
        self.demande = None
        self.perception = None
        self.contenu_casier = None
        self.percevoir()

    def est_adjacent(self, cible):
        """Indique si le robot est sur une case orthogonalement adjacente à
        une cible, condition pour interagir avec elle (énoncé 3.1).

        Paramètres :
            cible : position (ligne, colonne) de l'armoire, du dictionnaire
                ou d'un résident
        Renvoie : True si le robot est adjacent à la cible, False sinon.
        """
        return self.position in cases_adjacentes(tuple(cible))

    def percevoir(self):
        """Perçoit les 4 cases voisines et les inscrit dans la carte mentale
        (énoncé 3.2). Si le robot est devant l'armoire, regarde aussi le
        contenu du casier courant (énoncé 5.5).

        Paramètres : aucun.
        Renvoie : rien (met à jour self.perception, la carte mentale et
            self.contenu_casier, qui vaut None loin de l'armoire).
        """
        self.perception = self.env.percevoir(self.position)
        self.carte.mettre_a_jour(self.position, self.perception)
        if self.est_adjacent(self.armoire):
            self.contenu_casier = self.env.contenu_casier(self.selecteur)
        else:
            self.contenu_casier = None

    def _journaliser(self, action, argument=None):
        """Ajoute un pas à la trace avec l'état actuel du robot. À appeler
        dans chaque action AVANT de modifier la position ou le sélecteur,
        puisque la trace doit contenir l'état d'avant l'action (énoncé 5.5).

        Paramètres :
            action : nom de l'action ("AVANCER", "CHERCHER", ...)
            argument : direction ou nom d'objet, None si l'action n'en a pas
        Renvoie : rien (ajoute un pas à self.trace).
        """
        self.trace.ajouter_pas(demande=self.demande,
                               position=self.position,
                               casier=self.selecteur,
                               action=action,
                               argument=argument,
                               perception=self.perception,
                               contenu_casier=self.contenu_casier)

    def avancer(self, direction):
        """Action AVANCER (énoncé 3.4) : déplace le robot d'une case. La case
        visée doit être libre en réalité : on demande à l'environnement, pas
        à la carte mentale, qui suppose libres les cases inconnues.

        Paramètres :
            direction : "N", "S", "E" ou "O"
        Renvoie : rien (modifie self.position, puis perçoit).
        Lève : ValueError si la case visée n'est pas libre.
        """
        case = case_voisine(self.position, direction)
        if not self.env.est_libre(case):
            raise ValueError(f"AVANCER {direction} illegal depuis {self.position} : "
                             f"la case {case} n'est pas libre")
        self._journaliser("AVANCER", direction)
        self.position = case
        self.percevoir()

    def chercher(self, direction):
        """Action CHERCHER (énoncé 3.4, annexe C.2) : déplace le sélecteur de
        l'armoire d'un casier. N et S changent la ligne, sans boucler ; E et O
        changent la colonne, qui boucle de 7 à 0 (Roue).

        Paramètres :
            direction : "N", "S", "E" ou "O"
        Renvoie : rien (modifie self.selecteur, puis perçoit le nouveau casier).
        Lève : ValueError si le robot n'est pas devant l'armoire, ou pour N
            depuis la ligne 0 et S depuis la ligne 2.
        """
        if not self.est_adjacent(self.armoire):
            raise ValueError(f"CHERCHER {direction} illegal depuis {self.position} : "
                             f"le robot n'est pas adjacent a l'armoire")

        ligne = self.selecteur[0]
        colonne = self.selecteur[1]
        if (direction == "N" and ligne == 0) or (direction == "S" and ligne == 2):
            raise ValueError(f"CHERCHER {direction} illegal depuis le casier "
                             f"{self.selecteur} : les lignes ne bouclent pas")

        self._journaliser("CHERCHER", direction)

        colonnes = Roue(range(NB_COLONNES))
        if direction == "N":
            self.selecteur[0] = ligne - 1
        elif direction == "S":
            self.selecteur[0] = ligne + 1
        elif direction == "E":
            self.selecteur[1] = colonnes.voisin(colonne, 1)
        elif direction == "O":
            self.selecteur[1] = colonnes.voisin(colonne, -1)

        self.percevoir()

    def consulter(self):
        """Action CONSULTER (énoncé 3.4) : lit le dictionnaire posé près de
        l'armoire. Le robot n'analyse pas le message lui-même : c'est
        decision.py qui appelle ensuite trouver_emotion().

        Paramètres : aucun.
        Renvoie : rien (ajoute le pas à la trace, puis perçoit).
        Lève : ValueError si le robot n'est pas adjacent au dictionnaire.
        """
        if not self.est_adjacent(self.dictionnaire):
            raise ValueError(f"CONSULTER illegal depuis {self.position} : "
                             f"le robot n'est pas adjacent au dictionnaire")
        self._journaliser("CONSULTER")
        self.percevoir()

    def prendre(self, objet):
        """Action PRENDRE (énoncé 3.4) : prend l'objet du casier où se trouve
        le sélecteur. Le casier ne se vide pas (stock illimité au projet 1).

        Paramètres :
            objet : nom de l'objet, troisième valeur renvoyée par
                fouiller_armoire()
        Renvoie : rien (le robot porte maintenant l'objet, puis perçoit).
        Lève : ValueError si le robot n'est pas devant l'armoire, si le casier
            ne contient pas cet objet (ou est vide), ou s'il porte déjà un objet.
        """
        if not self.est_adjacent(self.armoire):
            raise ValueError(f"PRENDRE illegal depuis {self.position} : "
                             f"le robot n'est pas adjacent a l'armoire")
        if self.contenu_casier != objet:
            raise ValueError(f"PRENDRE {objet} illegal : le casier {self.selecteur} "
                             f"contient {self.contenu_casier}")
        if self.objet_porte is not None:
            raise ValueError(f"PRENDRE {objet} illegal : le robot porte deja "
                             f"{self.objet_porte}")
        self._journaliser("PRENDRE", objet)
        self.objet_porte = objet
        self.percevoir()

    def donner(self, id_resident, objet):
        """Action DONNER (énoncé 3.4) : remet l'objet porté au résident de la
        demande. Dans la trace, l'argument est le nom de l'objet.

        Paramètres :
            id_resident : identifiant du résident, par exemple "R1"
            objet : nom de l'objet à donner
        Renvoie : rien (le robot ne porte plus rien, puis perçoit).
        Lève : ValueError si le résident est inconnu, si le robot n'est pas
            adjacent à ce résident, ou s'il ne porte pas cet objet.
        """
        if id_resident not in self.residents:
            raise ValueError(f"DONNER illegal : resident {id_resident} inconnu")

        if not self.est_adjacent(self.residents[id_resident]):
            raise ValueError(f"DONNER illegal depuis {self.position} : le robot "
                             f"n'est pas adjacent au resident {id_resident} "
                             f"en {self.residents[id_resident]}")

        if self.objet_porte != objet:
            raise ValueError(f"DONNER {objet} illegal : le robot porte "
                             f"{self.objet_porte}")

        self._journaliser("DONNER", objet)
        self.objet_porte = None
        self.percevoir()

    def attendre(self):
        """Action ATTENDRE (énoncé 3.4) : passe un tour sans rien faire.
        Toujours légale.

        Paramètres : aucun.
        Renvoie : rien (ajoute le pas à la trace, puis perçoit).
        """
        self._journaliser("ATTENDRE")
        self.percevoir()
