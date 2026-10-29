"""Tests de armoire.py (enonce section 8, points 4 et 5).

Lancement, depuis base_fournie :
    python -m unittest tests.test_armoire -v
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))

from armoire import (Roue, distance_roue, calculer_candidats,
                     trajet_selecteur, fouiller_armoire)

BASE = Path(__file__).parent.parent

EMOTIONS = ["joie", "confiance", "peur", "surprise",
            "tristesse", "degout", "colere", "anticipation"]
INTENSITES = ["faible", "moyenne", "forte"]


class FauxRobot:
    """Robot minimal pour tester fouiller_armoire sans robot.py.

    Il joue aussi le role du simulateur : contenus associe a chaque casier
    (ligne, colonne) son objet, un casier absent etant vide. Il refuse les
    mouvements illegaux (N en ligne 0, S en ligne 2) et note tous les casiers
    devant lesquels le selecteur est passe, dans l'ordre.
    """

    def __init__(self, contenus, depart=(1, 0)):
        self.contenus = contenus
        self.selecteur = list(depart)
        self.mouvements = []
        self.casiers_vus = [tuple(depart)]

    @property
    def contenu_casier(self):
        return self.contenus.get(tuple(self.selecteur))

    def chercher(self, direction):
        ligne, colonne = self.selecteur
        if direction == "N":
            if ligne == 0:
                raise AssertionError("CHERCHER N illegal depuis la ligne 0")
            ligne -= 1
        elif direction == "S":
            if ligne == 2:
                raise AssertionError("CHERCHER S illegal depuis la ligne 2")
            ligne += 1
        elif direction == "E":
            colonne = (colonne + 1) % 8
        elif direction == "O":
            colonne = (colonne - 1) % 8
        else:
            raise AssertionError("direction inconnue : " + direction)
        self.selecteur = [ligne, colonne]
        self.mouvements.append(direction)
        self.casiers_vus.append((ligne, colonne))


def armoire_pleine():
    """Les 24 casiers garnis, chacun avec un objet nomme d'apres sa position."""
    return {(l, c): "objet_%d_%d" % (l, c) for l in range(3) for c in range(8)}


def armoire_standard():
    """Contenus de donnees/armoire_standard.json (le test joue le simulateur,
    il a donc le droit de lire le champ objet)."""
    with open(BASE / "donnees" / "armoire_standard.json", encoding="utf-8") as f:
        donnees = json.load(f)
    return {(c["ligne"], c["colonne"]): c["objet"]
            for c in donnees["casiers"] if c["objet"] is not None}


class TestRoue(unittest.TestCase):

    def setUp(self):
        self.roue = Roue(EMOTIONS)

    def test_voisin_boucle_dans_les_deux_sens(self):
        self.assertEqual(self.roue.voisin(7, 1), 0)
        self.assertEqual(self.roue.voisin(0, -1), 7)
        self.assertEqual(self.roue.voisin(3, 2), 5)

    def test_decalage_jamais_negatif(self):
        self.assertEqual(self.roue.decalage(7, 1), 2)
        self.assertEqual(self.roue.decalage(1, 7), 6)

    def test_est_horaire(self):
        self.assertTrue(self.roue.est_horaire(7, 0))
        self.assertFalse(self.roue.est_horaire(0, 7))
        # a egalite (case opposee), on considere le sens horaire
        self.assertTrue(self.roue.est_horaire(0, 4))


class TestDistanceRoue(unittest.TestCase):

    def test_meme_emotion(self):
        self.assertEqual(distance_roue("peur", "peur", EMOTIONS), 0)

    def test_voisines_y_compris_par_le_bouclage(self):
        self.assertEqual(distance_roue("joie", "confiance", EMOTIONS), 1)
        self.assertEqual(distance_roue("joie", "anticipation", EMOTIONS), 1)

    def test_exemple_docstring_joie_colere(self):
        self.assertEqual(distance_roue("joie", "colere", EMOTIONS), 2)
        self.assertEqual(distance_roue("colere", "joie", EMOTIONS), 2)

    def test_opposees_a_distance_4(self):
        for e1, e2 in [("joie", "tristesse"), ("confiance", "degout"),
                       ("peur", "colere"), ("surprise", "anticipation")]:
            self.assertEqual(distance_roue(e1, e2, EMOTIONS), 4)


class TestCalculerCandidats(unittest.TestCase):

    def test_quinze_casiers_distincts(self):
        candidats = calculer_candidats("tristesse", "moyenne", EMOTIONS, INTENSITES)
        positions = [tuple(c["position"]) for c in candidats]
        self.assertEqual(len(positions), 15)
        self.assertEqual(len(set(positions)), 15)

    def test_jamais_d_emotion_a_distance_3_ou_4(self):
        candidats = calculer_candidats("tristesse", "moyenne", EMOTIONS, INTENSITES)
        colonnes = {c["position"][1] for c in candidats}
        # tristesse = 4 : colonnes 2 a 6, jamais joie (0), confiance (1), anticipation (7)
        self.assertEqual(colonnes, {2, 3, 4, 5, 6})

    def test_cinq_premiers_annexe_c5(self):
        candidats = calculer_candidats("surprise", "forte", EMOTIONS, INTENSITES)
        attendus = [([2, 3], "aucun"), ([1, 3], "intensite"), ([0, 3], "intensite"),
                    ([2, 4], "voisine_1"), ([2, 2], "voisine_1")]
        obtenus = [(c["position"], c["type_remplacement"]) for c in candidats[:5]]
        self.assertEqual(obtenus, attendus)

    def test_intensite_la_plus_faible_d_abord(self):
        # moyenne : faible et forte sont a ecart 1, faible passe avant
        candidats = calculer_candidats("joie", "moyenne", EMOTIONS, INTENSITES)
        self.assertEqual(candidats[0]["position"], [1, 0])
        self.assertEqual(candidats[1]["position"], [0, 0])
        self.assertEqual(candidats[2]["position"], [2, 0])

    def test_sens_horaire_avant_antihoraire_avec_bouclage(self):
        # voisines de joie : confiance (horaire) avant anticipation (antihoraire)
        candidats = calculer_candidats("joie", "moyenne", EMOTIONS, INTENSITES)
        self.assertEqual(candidats[3]["position"], [1, 1])
        self.assertEqual(candidats[4]["position"], [1, 7])

    def test_repartition_des_replis(self):
        candidats = calculer_candidats("peur", "faible", EMOTIONS, INTENSITES)
        replis = [c["type_remplacement"] for c in candidats]
        self.assertEqual(replis.count("aucun"), 1)
        self.assertEqual(replis.count("intensite"), 2)
        self.assertEqual(replis.count("voisine_1"), 6)
        self.assertEqual(replis.count("voisine_2"), 6)
        # la liste est triee : aucun, puis intensite, puis voisine_1, puis voisine_2
        self.assertEqual(replis, sorted(replis, key=["aucun", "intensite",
                                                     "voisine_1", "voisine_2"].index))


class TestTrajetSelecteur(unittest.TestCase):

    def test_trois_exemples_annexe_c3(self):
        self.assertEqual(trajet_selecteur([1, 0], [1, 4]), ["E", "E", "E", "E"])
        self.assertEqual(trajet_selecteur([2, 7], [0, 1]), ["N", "N", "E", "E"])
        self.assertEqual(trajet_selecteur([1, 0], [2, 6]), ["S", "O", "O"])

    def test_remonter_d_une_ligne(self):
        self.assertEqual(trajet_selecteur([2, 3], [1, 3]), ["N"])

    def test_bouclage_7_vers_0_et_0_vers_7(self):
        self.assertEqual(trajet_selecteur([0, 7], [0, 0]), ["E"])
        self.assertEqual(trajet_selecteur([0, 0], [0, 7]), ["O"])

    def test_deja_sur_le_casier(self):
        self.assertEqual(trajet_selecteur([1, 5], [1, 5]), [])

    def test_trajet_mene_bien_a_l_arrivee(self):
        # pour tous les couples de casiers : on arrive au bon endroit,
        # sans mouvement illegal, en |dl| + min(a, 8 - a) mouvements
        for l1 in range(3):
            for c1 in range(8):
                for l2 in range(3):
                    for c2 in range(8):
                        robot = FauxRobot({}, depart=(l1, c1))
                        for direction in trajet_selecteur([l1, c1], [l2, c2]):
                            robot.chercher(direction)
                        self.assertEqual(robot.selecteur, [l2, c2])
                        a = (c2 - c1) % 8
                        self.assertEqual(len(robot.mouvements),
                                         abs(l2 - l1) + min(a, 8 - a))


class TestFouillerArmoire(unittest.TestCase):

    def fouiller(self, contenus, emotion, intensite, depart=(1, 0)):
        robot = FauxRobot(contenus, depart)
        candidats = calculer_candidats(emotion, intensite, EMOTIONS, INTENSITES)
        return robot, fouiller_armoire(robot, candidats)

    def test_casier_exact_garni(self):
        robot, resultat = self.fouiller(armoire_pleine(), "tristesse", "moyenne")
        self.assertEqual(resultat, ([1, 4], "aucun", "objet_1_4"))
        self.assertEqual(robot.mouvements, ["E", "E", "E", "E"])

    def test_casier_exact_deja_sous_le_selecteur(self):
        robot, resultat = self.fouiller(armoire_pleine(), "joie", "moyenne")
        self.assertEqual(resultat, ([1, 0], "aucun", "objet_1_0"))
        self.assertEqual(robot.mouvements, [])

    def test_repli_en_intensite(self):
        contenus = armoire_pleine()
        del contenus[(1, 4)]
        robot, resultat = self.fouiller(contenus, "tristesse", "moyenne")
        self.assertEqual(resultat, ([0, 4], "intensite", "objet_0_4"))
        self.assertIn((1, 4), robot.casiers_vus)

    def test_colonne_entiere_vide_annexe_c5(self):
        robot, resultat = self.fouiller(armoire_standard(), "surprise", "forte")
        self.assertEqual(resultat, ([2, 4], "voisine_1", "telephone"))
        # les trois casiers plus prioritaires ont bien ete vus avant de conclure
        for casier in [(2, 3), (1, 3), (0, 3)]:
            self.assertIn(casier, robot.casiers_vus)
        # bouton d'appel en [2, 2] croise en chemin, mais pas pris (rang 5)
        self.assertIn((2, 2), robot.casiers_vus)
        self.assertEqual(robot.selecteur, [2, 4])
        self.assertEqual(len(robot.mouvements), 9)

    def test_garni_croise_hors_tour_pas_pris(self):
        # depuis [1, 0], le selecteur croise [1, 1], [1, 2], [1, 3], tous garnis,
        # mais c'est le casier exact [1, 4], premier de la liste, qui est pris
        robot, resultat = self.fouiller(armoire_pleine(), "tristesse", "moyenne")
        for casier in [(1, 1), (1, 2), (1, 3)]:
            self.assertIn(casier, robot.casiers_vus)
        self.assertEqual(resultat[0], [1, 4])

    def test_armoire_vide_a_distance_2(self):
        # seules les colonnes a distance 3 et 4 de tristesse sont garnies
        contenus = {(l, c): "loin" for l in range(3) for c in (0, 1, 7)}
        robot, resultat = self.fouiller(contenus, "tristesse", "moyenne")
        self.assertEqual(resultat, (None, None, None))
        # pas de repli annonce sans fouille : les 15 candidats ont ete vus
        for candidat in calculer_candidats("tristesse", "moyenne", EMOTIONS, INTENSITES):
            self.assertIn(tuple(candidat["position"]), robot.casiers_vus)


if __name__ == "__main__":
    unittest.main()
