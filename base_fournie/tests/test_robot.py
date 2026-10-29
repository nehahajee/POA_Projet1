"""Tests de feature/robot : robot.py

Lancement, depuis base_fournie :
    python -m unittest tests.test_robot -v
"""

import json
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agent"))

from robot import CarteMentale, Robot  # noqa: E402
from deplacement import trouver_chemin, case_voisine, DIRECTIONS  # noqa: E402
from reconfort_io import Trace  # noqa: E402


def charger_json(chemin):
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


SYMBOLES_GRILLE = {"#": "mur", ".": "libre", "R": "libre",
                   "A": "armoire", "D": "dictionnaire", "P": "resident"}


class FauxEnvironnement:
    """Joue le simulateur : lui seul lit la grille et les objets des casiers.
    Il a les trois methodes que le Robot appelle."""

    def __init__(self, carte, armoire):
        self.grille = carte["grille"]
        self.casiers = {}
        for c in armoire["casiers"]:
            self.casiers[(c["ligne"], c["colonne"])] = c["objet"]

    def dans_la_grille(self, position):
        l, c = position
        return 0 <= l < len(self.grille) and 0 <= c < len(self.grille[0])

    def percevoir(self, position):
        resultat = {}
        for direction in DIRECTIONS:
            l, c = case_voisine(position, direction)
            if self.dans_la_grille((l, c)):
                resultat[direction] = SYMBOLES_GRILLE[self.grille[l][c]]
            else:
                resultat[direction] = "mur"
        return resultat

    def est_libre(self, position):
        l, c = position
        return self.dans_la_grille(position) and self.grille[l][c] in ".R"

    def contenu_casier(self, casier):
        return self.casiers.get(tuple(casier))


def creer_robot():
    """Robot neuf sur appartement_01 avec armoire_standard : depart (6, 1),
    selecteur [1, 0]. Le robot recoit la carte SANS la grille (enonce 3.3)."""
    carte = charger_json(RACINE / "cartes" / "appartement_01.json")
    armoire = charger_json(RACINE / "donnees" / "armoire_standard.json")
    env = FauxEnvironnement(carte, armoire)
    connaissances = {cle: valeur for cle, valeur in carte.items() if cle != "grille"}
    trace = Trace(nom_carte="appartement_01", nom_scenario="test")
    robot = Robot(env, connaissances, armoire["casier_depart"], trace)
    return robot, trace, env, armoire


def amener_devant_armoire(robot):
    """De (6, 1) a (6, 3), case adjacente a l'armoire (6, 4)."""
    robot.avancer("E")
    robot.avancer("E")


def carte_appartement_01():
    """Carte mentale au depart de l'annexe D : 9 x 13, armoire en (6, 4),
    dictionnaire en (7, 6), residents en (6, 11) et (3, 3)."""
    return CarteMentale(9, 13, (6, 4), (7, 6), [(6, 11), (3, 3)])


class TestCarteMentale(unittest.TestCase):

    def test_case_inconnue_supposee_libre(self):
        carte = carte_appartement_01()
        self.assertEqual(carte.type_case((6, 7)), "inconnu")
        # (6, 7) est un mur mais le robot ne l'a pas encore vu
        self.assertTrue(carte.est_traversable((6, 7)))

    def test_bord_et_hors_grille_non_traversables(self):
        carte = carte_appartement_01()
        self.assertFalse(carte.est_traversable((0, 5)))    # bord nord
        self.assertFalse(carte.est_traversable((4, 12)))   # bord est
        self.assertFalse(carte.est_traversable((-1, 3)))   # hors grille
        self.assertFalse(carte.est_traversable((9, 3)))    # hors grille

    def test_positions_connues_des_le_depart(self):
        carte = carte_appartement_01()
        self.assertEqual(carte.type_case((6, 4)), "armoire")
        self.assertEqual(carte.type_case((7, 6)), "dictionnaire")
        self.assertEqual(carte.type_case((3, 3)), "resident")
        for case in [(6, 4), (7, 6), (6, 11), (3, 3)]:
            self.assertFalse(carte.est_traversable(case))

    def test_mise_a_jour_apres_perception(self):
        # perception reelle depuis (6, 6) dans appartement_01 : mur a l'est
        carte = carte_appartement_01()
        carte.mettre_a_jour((6, 6), {"N": "libre", "S": "libre",
                                     "E": "mur", "O": "libre"})
        self.assertEqual(carte.type_case((6, 7)), "mur")
        self.assertFalse(carte.est_traversable((6, 7)))
        self.assertTrue(carte.est_traversable((5, 6)))
        # la case du robot est notee libre
        self.assertEqual(carte.type_case((6, 6)), "libre")

    def test_mur_decouvert_change_le_chemin(self):
        # meme depart, meme arrivee : le chemin planifie change une fois le
        # mur (6, 7) percu, c'est ce qui permet la replanification
        carte = carte_appartement_01()
        avant = trouver_chemin((6, 6), (6, 8), carte)
        self.assertEqual(avant, [(6, 6), (6, 7), (6, 8)])

        carte.mettre_a_jour((6, 6), {"N": "libre", "S": "libre",
                                     "E": "mur", "O": "libre"})
        apres = trouver_chemin((6, 6), (6, 8), carte)
        self.assertNotIn((6, 7), apres)
        self.assertGreater(len(apres), len(avant))

    def test_afficher(self):
        carte = CarteMentale(4, 5, (2, 3), (1, 3), [])
        carte.mettre_a_jour((1, 1), {"N": "mur", "S": "libre",
                                     "E": "libre", "O": "mur"})
        attendu = ("#####\n"
                   "#@.D#\n"
                   "#.?A#\n"
                   "#####")
        self.assertEqual(carte.afficher((1, 1)), attendu)


class TestPerceptionInitiale(unittest.TestCase):

    def setUp(self):
        self.robot, self.trace, self.env, self.armoire = creer_robot()

    def test_perception_au_depart(self):
        self.assertEqual(self.robot.perception, {"N": "libre", "S": "libre",
                                                 "E": "libre", "O": "mur"})

    def test_carte_mise_a_jour_depart(self):
        self.assertEqual(self.robot.carte.type_case((6, 0)), "mur")
        self.assertEqual(self.robot.carte.type_case((6, 2)), "libre")

    def test_casier_invisible_loin_de_l_armoire(self):
        self.assertIsNone(self.robot.contenu_casier)

    def test_position_est_un_tuple(self):
        self.assertEqual(self.robot.position, (6, 1))


class TestTrace(unittest.TestCase):

    def setUp(self):
        self.robot, self.trace, self.env, self.armoire = creer_robot()

    def test_construction_n_ecrit_rien(self):
        self.assertEqual(len(self.trace.pas), 0)

    def test_pas_contient_etat_avant_action(self):
        self.robot.avancer("E")
        pas = self.trace.pas[0]
        self.assertEqual(pas["position"], [6, 1])
        self.assertEqual(pas["casier"], [1, 0])
        self.assertEqual(pas["action"], "AVANCER")
        self.assertEqual(pas["argument"], "E")
        # perception vue depuis (6, 1), et non depuis (6, 2)
        self.assertEqual(pas["perception"], {"N": "libre", "S": "libre",
                                             "E": "libre", "O": "mur"})

    def test_t_augmente(self):
        self.robot.avancer("E")
        self.robot.attendre()
        self.robot.avancer("O")
        self.assertEqual([p["t"] for p in self.trace.pas], [0, 1, 2])

    def test_casier_trace_ne_change_pas_apres_coup(self):
        amener_devant_armoire(self.robot)
        self.robot.chercher("O")
        self.assertEqual(self.robot.selecteur, [1, 7])
        self.assertEqual(self.trace.pas[-1]["casier"], [1, 0])


class TestAvancer(unittest.TestCase):

    def setUp(self):
        self.robot, self.trace, self.env, self.armoire = creer_robot()

    def test_avancer_case_libre(self):
        self.robot.avancer("E")
        self.assertEqual(self.robot.position, (6, 2))
        self.assertEqual(len(self.trace.pas), 1)

    def test_avancer_dans_un_mur_refuse(self):
        # depuis (6, 1), la case a l'ouest (6, 0) est un mur
        with self.assertRaises(ValueError):
            self.robot.avancer("O")
        self.assertEqual(len(self.trace.pas), 0)
        self.assertEqual(self.robot.position, (6, 1))

    def test_avancer_dans_un_meuble_refuse(self):
        amener_devant_armoire(self.robot)
        n = len(self.trace.pas)
        with self.assertRaises(ValueError):
            self.robot.avancer("E")
        self.assertEqual(len(self.trace.pas), n)
        self.assertEqual(self.robot.position, (6, 3))

    def test_casier_visible_devant_armoire(self):
        amener_devant_armoire(self.robot)
        self.assertEqual(self.robot.contenu_casier, "photo de famille")


class TestChercher(unittest.TestCase):

    def setUp(self):
        self.robot, self.trace, self.env, self.armoire = creer_robot()
        amener_devant_armoire(self.robot)

    def test_bouclage_0_vers_7(self):
        self.robot.chercher("O")
        self.assertEqual(self.robot.selecteur, [1, 7])
        self.assertEqual(self.robot.contenu_casier, "calendrier")

    def test_bouclage_7_vers_0(self):
        self.robot.chercher("O")
        self.robot.chercher("E")
        self.assertEqual(self.robot.selecteur, [1, 0])

    def test_monter_et_descendre(self):
        self.robot.chercher("N")
        self.assertEqual(self.robot.selecteur, [0, 0])
        self.assertEqual(self.robot.contenu_casier, "tisane")
        self.robot.chercher("S")
        self.robot.chercher("S")
        self.assertEqual(self.robot.selecteur, [2, 0])
        self.assertEqual(self.robot.contenu_casier, "guirlande lumineuse")

    def test_nord_refuse_en_ligne_0(self):
        self.robot.chercher("N")
        n = len(self.trace.pas)
        with self.assertRaises(ValueError):
            self.robot.chercher("N")
        self.assertEqual(len(self.trace.pas), n)
        self.assertEqual(self.robot.selecteur, [0, 0])


if __name__ == "__main__":
    unittest.main()
