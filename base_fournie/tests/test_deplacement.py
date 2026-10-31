"""Tests de feature/deplacement : deplacement.py

trouver_chemin est teste seul, avec CarteConnue (une carte entierement
connue). deplacement et rejoindre sont testes avec le vrai Robot et le vrai
Environnement : le Robot ne recoit pas la grille, seulement les positions
connues, et leve ValueError si un pas est illegal.

Lancement, depuis base_fournie :
    python -m unittest tests.test_deplacement -v
"""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agent"))

import reconfort_io as rio  # noqa: E402
import deplacement as dep  # noqa: E402
from environnement import Environnement  # noqa: E402
from robot import Robot  # noqa: E402


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


def robot_sur_carte(carte):
    """Vrai Robot sur une carte complete. L'Environnement lit la grille, le
    Robot ne recoit que les connaissances, c'est-a-dire la carte sans la
    grille (enonce 3.3). Aucun casier : on ne teste que les deplacements."""
    env = Environnement(carte, {"casiers": []})
    connaissances = {cle: valeur for cle, valeur in carte.items() if cle != "grille"}
    return Robot(env, connaissances, [1, 0], rio.Trace(carte["nom"], "test"))


def robot_sur(grille, depart):
    """Vrai Robot sur une petite grille ecrite a la main. Les positions de
    l'armoire (A), du dictionnaire (D) et des residents (P) sont lues dans la
    grille pour fabriquer la carte, comme dans un fichier JSON."""
    carte = {"nom": "mini", "grille": grille,
             "dimensions": {"hauteur": len(grille), "largeur": len(grille[0])},
             "depart_robot": list(depart), "residents": []}
    for l, ligne in enumerate(grille):
        for c, symbole in enumerate(ligne):
            if symbole == "A":
                carte["armoire"] = {"position": [l, c]}
            elif symbole == "D":
                carte["dictionnaire"] = {"position": [l, c]}
            elif symbole == "P":
                numero = len(carte["residents"]) + 1
                carte["residents"].append({"id": f"P{numero}", "nom": "test",
                                           "position": [l, c]})
    return robot_sur_carte(carte)


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
        robot = robot_sur(["AD#", "#R#", "###"], (1, 1))
        self.assertFalse(dep.deplacement(None, robot))
        self.assertFalse(dep.deplacement([], robot))

    def test_chemin_qui_ne_part_pas_du_robot(self):
        robot = robot_sur(["#AD##", "#R..#", "#####"], (1, 1))
        self.assertFalse(dep.deplacement([(1, 2), (1, 3)], robot))
        self.assertEqual(robot.position, (1, 1))

    def test_suit_un_chemin_libre(self):
        robot = robot_sur(["#AD##", "#R..#", "#####"], (1, 1))
        self.assertTrue(dep.deplacement([(1, 1), (1, 2), (1, 3)], robot))
        self.assertEqual(robot.position, (1, 3))
        self.assertEqual(len(robot.trace.pas), 2)

    def test_s_arrete_avant_un_mur_decouvert(self):
        # Plan tout droit vers l'est ; le mur (1, 3) est decouvert en arrivant
        # en (1,2). deplacement doit s'arreter la, sans jamais entrer dans le
        # mur (Robot leverait ValueError).
        grille = ["##AD###",
                  "#R.#..#",
                  "#.....#",
                  "#######"]
        robot = robot_sur(grille, (1, 1))
        chemin = [(1, 1), (1, 2), (1, 3), (1, 4)]
        self.assertFalse(dep.deplacement(chemin, robot))
        self.assertEqual(robot.position, (1, 2))


class TestRejoindre(unittest.TestCase):
    def test_replanification_apres_mur_decouvert(self):
        # Annexe D : la partie droite n'est reliee que par (4, 11) ; le robot
        # part en ligne 6, decouvre le mur [6,7] et replanifie.
        carte = charger_carte_json("appartement_01")
        robot = robot_sur_carte(carte)
        resident = tuple(carte["residents"][0]["position"])  # R1
        with mock.patch.object(dep, "trouver_chemin",
                               wraps=dep.trouver_chemin) as espion:
            ok = dep.rejoindre(dep.cases_adjacentes(resident), robot)
        self.assertTrue(ok)
        self.assertIn(robot.position, dep.cases_adjacentes(resident))
        self.assertGreater(espion.call_count, 1, "aucune replanification ?")

    def test_resident_mure_termine_et_renvoie_false(self):
        grille = ["###AD####",
                  "#R......#",
                  "#.#####.#",
                  "#.#P..#.#",   # P emmure dans une piece close
                  "#.#####.#",
                  "#.......#",
                  "#########"]
        robot = robot_sur(grille, (1, 1))
        # (3,4) est la seule case libre autour de P, mais elle est fermee.
        self.assertFalse(dep.rejoindre([(3, 4)], robot))

    def test_toutes_les_cartes_fournies_aucun_deplacement_illegal(self):
        # Robot leve ValueError si un pas est illegal : le test echouerait.
        for chemin_carte in sorted((RACINE / "cartes").glob("appartement_*.json")):
            carte = json.loads(chemin_carte.read_text("utf-8"))
            with self.subTest(carte=carte["nom"]):
                robot = robot_sur_carte(carte)
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
        self.robot = robot_sur_carte(self.carte)

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
        grille = ["###AD####",
                  "#R......#",
                  "#.#####.#",
                  "#.#P..#.#",
                  "#.#####.#",
                  "#.......#",
                  "#########"]
        robot = robot_sur(grille, (1, 1))
        self.assertFalse(dep.deplacement_resident(robot, (3, 3)))


if __name__ == "__main__":
    unittest.main()
