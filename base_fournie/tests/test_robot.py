"""Tests de feature/robot : robot.py

Lancement, depuis base_fournie :
    python -m unittest tests.test_robot -v
"""

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agent"))

from robot import CarteMentale  # noqa: E402
from deplacement import trouver_chemin  # noqa: E402


def carte_appartement_01():
    """Carte mentale au depart de l'annexe D : 9 x 13, armoire en (6, 4),
    dictionnaire en (7, 6), residents en (6, 11) et (3, 3)."""
    return CarteMentale(9, 13, (6, 4), (7, 6), [(6, 11), (3, 3)])


class TestCarteMentale(unittest.TestCase):

    def test_case_inconnue_supposee_libre(self):
        carte = carte_appartement_01()
        self.assertEqual(carte.type_case((6, 7)), "inconnu")
        # (6, 7) est un mur en realite, mais le robot ne l'a pas encore vu
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


if __name__ == "__main__":
    unittest.main()
