"""Tests de feature/deplacement : deplacement.py

FauxRobot joue le role du vrai Robot (robot.py, pas encore ecrit) : il a une
position, une carte mentale, et un avancer() qui deplace, puis percoit. Le
monde reel est `Environnement` simulé qui n'a pas encore été implementé.

"""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agent"))

import deplacement as dep  # noqa: E402
# from environnement import Environnement  # noqa: E402


class CarteMentale:
    """Carte mentale minimale (a remplacer par celle de robot.py)."""

    def __init__(self, hauteur, largeur, obstacles_connus=()):
        self.hauteur, self.largeur = hauteur, largeur
        self._murs = set()
        self._obstacles = {tuple(c) for c in obstacles_connus}

    def est_traversable(self, case):
        l, c = case
        if not (0 < l < self.hauteur - 1 and 0 < c < self.largeur - 1):
            return False  # le bord est toujours un mur
        return tuple(case) not in self._murs | self._obstacles  # inconnu = libre

    def mettre_a_jour(self, position, perception):
        for direction, valeur in perception.items():
            case = dep.case_voisine(position, direction)
            if valeur == "mur":
                self._murs.add(case)
            elif valeur != "libre":
                self._obstacles.add(case)


class FauxRobot:
    def __init__(self, grille, depart):
        # self.env = Environnement({"grille": grille}, {"casiers": []})
        self.env = MondeSimule(grille) #Faux environnement
        self.position = tuple(depart)
        # Le robot connait d'avance armoire, dictionnaire et residents.
        obstacles = [(l, c) for l, row in enumerate(grille)
                     for c, ch in enumerate(row) if ch in "ADP"]
        self.carte = CarteMentale(len(grille), len(grille[0]), obstacles)
        self.nb_pas = 0
        self._percevoir()

    def _percevoir(self):
        self.carte.mettre_a_jour(self.position, self.env.percevoir(self.position))

    def avancer(self, direction):
        cible = dep.case_voisine(self.position, direction)
        assert self.env.est_libre(cible), f"deplacement illegal vers {cible}"
        self.position = cible
        self.nb_pas += 1
        self._percevoir()


class MondeSimule:
    """Faux environnement"""
    SYMBOLES = {"#": "mur", ".": "libre", "R": "libre",
                "A": "armoire", "D": "dictionnaire", "P": "resident"}

    def __init__(self, grille):
        self.grille = grille

    def percevoir(self, position):
        resultat = {}
        for direction in dep.DIRECTIONS:
            l, c = dep.case_voisine(position, direction)
            dans = 0 <= l < len(self.grille) and 0 <= c < len(self.grille[0])
            resultat[direction] = self.SYMBOLES[self.grille[l][c]] if dans else "mur"
        return resultat

    def est_libre(self, position):
        l, c = position
        return (0 <= l < len(self.grille) and 0 <= c < len(self.grille[0])
                and self.grille[l][c] in ".R")


class CarteConnue:
    """Carte entierement connue, pour tester trouver_chemin seul."""

    def __init__(self, grille):
        self.grille = grille

    def est_traversable(self, case):
        l, c = case
        return (0 <= l < len(self.grille) and 0 <= c < len(self.grille[0])
                and self.grille[l][c] in ".R")


def adjacentes(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def charger_carte_json(nom):
    return json.loads((RACINE / "cartes" / f"{nom}.json").read_text("utf-8"))


class TestTrouverChemin(unittest.TestCase):
    # Mini-grille de l'annexe B.3 : le chemin le plus court fait 7 pas.
    GRILLE_B3 = [
        "######",
        "#R.#.#",
        "#.#..#",
        "#...##",
        "######",
    ]

    def test_annexe_b3_longueur_7(self):
        chemin = dep.trouver_chemin((1, 1), (1, 4), CarteConnue(self.GRILLE_B3))
        self.assertEqual(len(chemin) - 1, 7)
        self.assertEqual(chemin[0], (1, 1))
        self.assertEqual(chemin[-1], (1, 4))

    def test_chemin_valide(self):
        carte = CarteConnue(self.GRILLE_B3)
        chemin = dep.trouver_chemin((1, 1), (1, 4), carte)
        for a, b in zip(chemin, chemin[1:]):
            self.assertTrue(adjacentes(a, b))
            self.assertTrue(carte.est_traversable(b))

    def test_deja_arrive(self):
        carte = CarteConnue(self.GRILLE_B3)
        self.assertEqual(dep.trouver_chemin((1, 1), (1, 1), carte), [(1, 1)])

    def test_plusieurs_destinations_prend_la_plus_proche(self):
        carte = CarteConnue(self.GRILLE_B3)
        chemin = dep.trouver_chemin((1, 1), [(1, 4), (2, 1)], carte)
        self.assertEqual(chemin, [(1, 1), (2, 1)])

    def test_aucun_chemin(self):
        grille = ["#####",
                  "#R#.#",
                  "#####"]
        self.assertIsNone(
            dep.trouver_chemin((1, 1), (1, 3), CarteConnue(grille)))

    def test_direction_vers(self):
        self.assertEqual(dep.direction_vers((3, 3), (2, 3)), "N")
        self.assertEqual(dep.direction_vers((3, 3), (4, 3)), "S")
        self.assertEqual(dep.direction_vers((3, 3), (3, 4)), "E")
        self.assertEqual(dep.direction_vers((3, 3), (3, 2)), "O")
        with self.assertRaises(ValueError):
            dep.direction_vers((3, 3), (4, 4))


class TestDeplacement(unittest.TestCase):
    def test_chemin_vide_ou_none(self):
        robot = FauxRobot(["###", "#R#", "###"], (1, 1))
        self.assertFalse(dep.deplacement(None, robot))
        self.assertFalse(dep.deplacement([], robot))

    def test_chemin_qui_ne_part_pas_du_robot(self):
        robot = FauxRobot(["#####", "#R..#", "#####"], (1, 1))
        self.assertFalse(dep.deplacement([(1, 2), (1, 3)], robot))
        self.assertEqual(robot.position, (1, 1))

    def test_suit_un_chemin_libre(self):
        robot = FauxRobot(["#####", "#R..#", "#####"], (1, 1))
        self.assertTrue(dep.deplacement([(1, 1), (1, 2), (1, 3)], robot))
        self.assertEqual(robot.position, (1, 3))
        self.assertEqual(robot.nb_pas, 2)

    def test_s_arrete_avant_un_mur_decouvert(self):
        # Plan tout droit vers l'est ; le mur (1,3) est decouvert en arrivant
        # en (1,2). deplacement doit s'arreter la, sans jamais entrer dans le
        # mur (FauxRobot leverait une erreur).
        grille = ["#######",
                  "#R.#..#",
                  "#.....#",
                  "#######"]
        robot = FauxRobot(grille, (1, 1))
        chemin = [(1, 1), (1, 2), (1, 3), (1, 4)]
        self.assertFalse(dep.deplacement(chemin, robot))
        self.assertEqual(robot.position, (1, 2))


class TestRejoindre(unittest.TestCase):
    def test_replanification_apres_mur_decouvert(self):
        # Annexe D : la partie droite n'est reliee que par (4, 11) ; le robot
        # part en ligne 6, decouvre le mur [6,7] et replanifie.
        carte = charger_carte_json("appartement_01")
        robot = FauxRobot(carte["grille"], carte["depart_robot"])
        resident = tuple(carte["residents"][0]["position"])  # R1
        with mock.patch.object(dep, "trouver_chemin",
                               wraps=dep.trouver_chemin) as espion:
            ok = dep.rejoindre(dep.cases_adjacentes(resident), robot)
        self.assertTrue(ok)
        self.assertIn(robot.position, dep.cases_adjacentes(resident))
        self.assertGreater(espion.call_count, 1, "aucune replanification ?")

    def test_resident_mure_termine_et_renvoie_false(self):
        grille = ["#########",
                  "#R......#",
                  "#.#####.#",
                  "#.#P..#.#",   # P emmure dans une piece close
                  "#.#####.#",
                  "#.......#",
                  "#########"]
        robot = FauxRobot(grille, (1, 1))
        # (3,4) est la seule case libre autour de P, mais elle est fermee.
        self.assertFalse(dep.rejoindre([(3, 4)], robot))

    def test_toutes_les_cartes_fournies_aucun_deplacement_illegal(self):
        # FauxRobot leve AssertionError si un pas est illegal.
        for chemin_carte in sorted((RACINE / "cartes").glob("appartement_*.json")):
            carte = json.loads(chemin_carte.read_text("utf-8"))
            with self.subTest(carte=carte["nom"]):
                robot = FauxRobot(carte["grille"], carte["depart_robot"])
                cibles = [carte["dictionnaire"]["position"],
                          carte["armoire"]["position"]]
                cibles += [r["position"] for r in carte["residents"]]
                for cible in cibles:
                    dep.rejoindre(dep.cases_adjacentes(tuple(cible)), robot)
                ok = dep.rejoindre(tuple(carte["depart_robot"]), robot)
                self.assertTrue(ok)
                self.assertEqual(robot.position, tuple(carte["depart_robot"]))


class TestFonctionsDeNavigation(unittest.TestCase):
    def setUp(self):
        self.carte = charger_carte_json("appartement_01")
        self.robot = FauxRobot(self.carte["grille"], self.carte["depart_robot"])

    def test_deplacement_dict(self):
        pos = tuple(self.carte["dictionnaire"]["position"])
        self.assertTrue(dep.deplacement_dict(self.robot, pos))
        self.assertTrue(adjacentes(self.robot.position, pos))

    def test_deplacement_armoire(self):
        pos = tuple(self.carte["armoire"]["position"])
        self.assertTrue(dep.deplacement_armoire(self.robot, pos))
        self.assertTrue(adjacentes(self.robot.position, pos))

    def test_deplacement_resident(self):
        pos = tuple(self.carte["residents"][1]["position"])  # R2
        self.assertTrue(dep.deplacement_resident(self.robot, pos))
        self.assertTrue(adjacentes(self.robot.position, pos))

    def test_deplacement_resident_inaccessible(self):
        grille = ["#########",
                  "#R......#",
                  "#.#####.#",
                  "#.#P..#.#",
                  "#.#####.#",
                  "#.......#",
                  "#########"]
        robot = FauxRobot(grille, (1, 1))
        self.assertFalse(dep.deplacement_resident(robot, (3, 3)))


if __name__ == "__main__":
    unittest.main()
