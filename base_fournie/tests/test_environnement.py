"""Tests de feature/perception-memoire : environnement.py

Les valeurs attendues viennent de l'enonce (annexe D et exemple de trace 5.5)
sur appartement_01 :

    colonne 0123456789012
    ligne 6   #R..A..#...P#
    ligne 7   #.....D....#
"""

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import reconfort_io as rio  # noqa: E402
from agent.environnement import Environnement  # noqa: E402


def charger_env(nom_carte="appartement_01"):
    carte = rio.charger_carte(RACINE / "cartes" / f"{nom_carte}.json")
    armoire = rio.charger_armoire(RACINE / "donnees" / "armoire_standard.json")
    return Environnement(carte, armoire), carte, armoire


class TestPercevoir(unittest.TestCase):
    def setUp(self):
        self.env, self.carte, _ = charger_env()

    def test_depart_exemple_de_l_enonce(self):
        # Exemple de trace (5.5) : robot en [6,1].
        self.assertEqual(
            self.env.percevoir((6, 1)),
            {"N": "libre", "S": "libre", "E": "libre", "O": "mur"})

    def test_voisin_armoire(self):
        # Armoire en [6,4] : depuis [6,5], elle est a l'ouest.
        self.assertEqual(self.env.percevoir((6, 5))["O"], "armoire")

    def test_voisin_dictionnaire(self):
        # Dictionnaire en [7,6] : depuis [7,5], il est a l'est.
        self.assertEqual(self.env.percevoir((7, 5))["E"], "dictionnaire")

    def test_voisin_resident(self):
        # R1 en [6,11] : depuis [6,10], il est a l'est.
        self.assertEqual(self.env.percevoir((6, 10))["E"], "resident")

    def test_mur_vu_depuis_la_ligne_6(self):
        # Annexe D : le mur [6,7] n'est decouvert qu'en arrivant en [6,6].
        self.assertEqual(self.env.percevoir((6, 6))["E"], "mur")

    def test_quatre_directions_exactement(self):
        self.assertEqual(set(self.env.percevoir((6, 1))), {"N", "S", "E", "O"})

    def test_hors_grille_est_un_mur(self):
        self.assertEqual(self.env.percevoir((0, 0))["N"], "mur")
        self.assertEqual(self.env.percevoir((0, 0))["O"], "mur")

    def test_valeurs_possibles(self):
        valides = {"mur", "libre", "armoire", "dictionnaire", "resident"}
        for l in range(self.carte["dimensions"]["hauteur"]):
            for c in range(self.carte["dimensions"]["largeur"]):
                self.assertTrue(set(self.env.percevoir((l, c)).values()) <= valides)


class TestEstLibre(unittest.TestCase):
    def setUp(self):
        self.env, self.carte, _ = charger_env()

    def test_depart_est_libre(self):
        self.assertTrue(self.env.est_libre(self.carte["depart_robot"]))

    def test_case_libre(self):
        self.assertTrue(self.env.est_libre((6, 2)))

    def test_mur(self):
        self.assertFalse(self.env.est_libre((6, 0)))
        self.assertFalse(self.env.est_libre((6, 7)))

    def test_armoire_dictionnaire_residents_non_traversables(self):
        self.assertFalse(self.env.est_libre(self.carte["armoire"]["position"]))
        self.assertFalse(self.env.est_libre(self.carte["dictionnaire"]["position"]))
        for resident in self.carte["residents"]:
            self.assertFalse(self.env.est_libre(resident["position"]))

    def test_hors_grille(self):
        self.assertFalse(self.env.est_libre((-1, 3)))
        self.assertFalse(self.env.est_libre((3, -1)))
        self.assertFalse(self.env.est_libre((99, 3)))
        self.assertFalse(self.env.est_libre((3, 99)))


class TestContenuCasier(unittest.TestCase):
    def setUp(self):
        self.env, _, self.armoire = charger_env()

    def test_casier_garni(self):
        # Annexe D : tristesse / moyenne, casier [1,4] = couverture.
        self.assertEqual(self.env.contenu_casier((1, 4)), "couverture")

    def test_casier_vide(self):
        # Annexe C.5 : toute la colonne surprise (colonne 3) est vide.
        for ligne in range(3):
            self.assertIsNone(self.env.contenu_casier((ligne, 3)))

    def test_accepte_liste_et_couple(self):
        self.assertEqual(self.env.contenu_casier([1, 4]),
                         self.env.contenu_casier((1, 4)))

    def test_casier_inconnu_est_vide(self):
        self.assertIsNone(self.env.contenu_casier((9, 9)))

    def test_tous_les_casiers_correspondent_au_fichier(self):
        for casier in self.armoire["casiers"]:
            self.assertEqual(
                self.env.contenu_casier((casier["ligne"], casier["colonne"])),
                casier["objet"])


class TestIsolation(unittest.TestCase):
    def test_pas_d_attribut_public_grille_ou_objet(self):
        env, _, _ = charger_env()
        self.assertFalse(hasattr(env, "grille"))
        self.assertFalse(hasattr(env, "objets"))

    def test_toutes_les_cartes_fournies(self):
        for chemin in sorted((RACINE / "cartes").glob("appartement_*.json")):
            with self.subTest(carte=chemin.stem):
                env, carte, _ = charger_env(chemin.stem)
                self.assertTrue(env.est_libre(carte["depart_robot"]))
                self.assertFalse(env.est_libre(carte["armoire"]["position"]))
                self.assertFalse(env.est_libre(carte["dictionnaire"]["position"]))


if __name__ == "__main__":
    unittest.main()
