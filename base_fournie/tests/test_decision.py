"""Tests de feature/boucle-agent : decision.py

    python -m unittest discover -s tests -v      (depuis la racine)

Robot leve ValueError si une action est illegale (AVANCER dans un mur, PRENDRE casier vide, DONNER pas
adjacent...). Donc "le test passe" veut aussi dire "toutes les actions de la
trace etaient legales".
"""

import copy
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0,str(RACINE / "agent"))

import reconfort_io as rio  # noqa: E402
import decision  # noqa: E402
from robot import Robot  # noqa: E402
from environnement import Environnement  # noqa: E402

DICO = rio.charger_dictionnaire(str(RACINE / "donnees" / "dictionnaire.json"))
ARMOIRE = rio.charger_armoire(str(RACINE / "donnees" / "armoire_standard.json"))

# Resident P emmure : la seule case libre autour de lui est fermee.
GRILLE_MURE = ["#########",
               "#R.A.D..#",
               "#.#####.#",
               "#.#P..#.#",
               "#.#####.#",
               "#.......#",
               "#########"]
# Meme appartement, mais le resident est joignable par la droite.
GRILLE_OUVERTE = ["#########",
                  "#R.A.D..#",
                  "#.#####.#",
                  "#.#P....#",
                  "#.#####.#",
                  "#.......#",
                  "#########"]


def carte_mini(grille, residents=None):
    return {
        "nom": "mini",
        "grille": grille,
        "dimensions": {"hauteur": len(grille), "largeur": len(grille[0])},
        "depart_robot": [1, 1],
        "armoire": {"position": [1, 3]},
        "dictionnaire": {"position": [1, 5]},
        "residents": residents or [{"id": "R1", "nom": "X", "position": [3, 3]}],
    }


def fabriquer_robot(carte, armoire=ARMOIRE):
    trace = rio.Trace(carte["nom"], "test", ["a", "b"])
    env = Environnement(carte, armoire)
    return Robot(env, carte, armoire["casier_depart"], trace)


def armoire_vide():
    vide = copy.deepcopy(ARMOIRE)
    for casier in vide["casiers"]:
        casier["objet"] = None
    return vide


def demande(numero, message, resident="R1"):
    return {"numero": numero, "resident": resident, "message": message}


class TestDemandeReussie(unittest.TestCase):
    def setUp(self):
        self.carte = rio.charger_carte(str(RACINE / "cartes" / "appartement_01.json"))
        self.robot = fabriquer_robot(self.carte)

    def test_exemple_de_l_enonce(self):
        # Annexe : "seule" -> tristesse/moyenne -> couverture, repli aucun.
        ok = decision.traiter_demande(
            self.robot, demande(1, "Je me sens tellement seule ce soir"), DICO)
        self.assertTrue(ok)
        liv = self.robot.trace.livraisons[0]
        self.assertEqual((liv["emotion"], liv["intensite"]),
                         ("tristesse", "moyenne"))
        self.assertEqual(liv["objet"], "couverture")
        self.assertEqual(liv["casier_choisi"], [1, 4])
        self.assertEqual(liv["repli"], "aucun")
        self.assertTrue(liv["succes"])
        self.assertIsNone(liv["motif_echec"])

    def test_le_robot_ne_porte_plus_rien_et_est_pres_du_resident(self):
        decision.traiter_demande(self.robot, demande(1, "je suis seule"), DICO)
        self.assertIsNone(self.robot.objet_porte)
        self.assertTrue(self.robot.est_adjacent(self.robot.residents["R1"]))

    def test_dernier_pas_est_donner_et_il_y_a_un_consulter_et_un_prendre(self):
        decision.traiter_demande(self.robot, demande(1, "je suis seule"), DICO)
        actions = [p["action"] for p in self.robot.trace.pas]
        self.assertEqual(actions[-1], "DONNER")
        self.assertEqual(actions.count("CONSULTER"), 1)
        self.assertEqual(actions.count("PRENDRE"), 1)
        self.assertLess(actions.index("CONSULTER"), actions.index("PRENDRE"))

    def test_pas_utilises_egale_nombre_de_pas_de_la_demande(self):
        decision.traiter_demande(self.robot, demande(1, "je suis seule"), DICO)
        self.assertEqual(self.robot.trace.livraisons[0]["pas_utilises"],
                         len(self.robot.trace.pas))

    def test_toutes_les_actions_portent_le_numero_de_demande(self):
        decision.traiter_demande(self.robot, demande(7, "je suis seule"), DICO)
        self.assertTrue(all(p["demande"] == 7 for p in self.robot.trace.pas))

    def test_premier_mot_reconnu_gagne(self):
        # "heureux" (joie) vient avant "seule" (tristesse) dans le message.
        decision.traiter_demande(
            self.robot, demande(1, "heureux mais seule"), DICO)
        self.assertEqual(self.robot.trace.livraisons[0]["emotion"], "joie")


class TestEchecs(unittest.TestCase):
    def test_emotion_indeterminee(self):
        robot = fabriquer_robot(carte_mini(GRILLE_OUVERTE))
        ok = decision.traiter_demande(robot, demande(1, "zzz qwerty"), DICO)
        self.assertFalse(ok)
        liv = robot.trace.livraisons[0]
        self.assertEqual(liv["motif_echec"], "emotion indeterminee")
        self.assertIsNone(liv["emotion"])
        self.assertIsNone(liv["objet"])
        self.assertIsNone(robot.objet_porte)
        # Il est quand meme alle consulter le dictionnaire.
        self.assertIn("CONSULTER", [p["action"] for p in robot.trace.pas])
        self.assertNotIn("PRENDRE", [p["action"] for p in robot.trace.pas])

    def test_armoire_vide(self):
        robot = fabriquer_robot(carte_mini(GRILLE_OUVERTE), armoire_vide())
        ok = decision.traiter_demande(robot, demande(1, "je suis seule"), DICO)
        self.assertFalse(ok)
        liv = robot.trace.livraisons[0]
        self.assertEqual(liv["motif_echec"], "armoire vide")
        self.assertEqual(liv["emotion"], "tristesse")
        self.assertIsNone(liv["casier_choisi"])
        self.assertIsNone(robot.objet_porte)

    def test_resident_inaccessible_on_ne_prend_rien(self):
        robot = fabriquer_robot(carte_mini(GRILLE_MURE))
        ok = decision.traiter_demande(robot, demande(1, "je suis seule"), DICO)
        self.assertFalse(ok)
        liv = robot.trace.livraisons[0]
        self.assertEqual(liv["motif_echec"], "resident inaccessible")
        self.assertIsNone(robot.objet_porte)
        self.assertNotIn("PRENDRE", [p["action"] for p in robot.trace.pas])

    def test_meme_appartement_resident_joignable_reussit(self):
        robot = fabriquer_robot(carte_mini(GRILLE_OUVERTE))
        self.assertTrue(
            decision.traiter_demande(robot, demande(1, "je suis seule"), DICO))

    def test_resident_inconnu(self):
        robot = fabriquer_robot(carte_mini(GRILLE_OUVERTE))
        with self.assertRaises(ValueError):
            decision.traiter_demande(
                robot, demande(1, "je suis seule", resident="R9"), DICO)

    def test_un_echec_n_empeche_pas_la_demande_suivante(self):
        robot = fabriquer_robot(carte_mini(GRILLE_OUVERTE))
        scenario = {"demandes": [demande(1, "zzz"),
                                 demande(2, "je suis seule")]}
        self.assertEqual(decision.executer_scenario(robot, scenario, DICO), 1)
        self.assertEqual([l["succes"] for l in robot.trace.livraisons],
                         [False, True])


class TestScenario(unittest.TestCase):
    def test_etat_conserve_entre_les_demandes(self):
        carte = rio.charger_carte(str(RACINE / "cartes" / "appartement_01.json"))
        robot = fabriquer_robot(carte)
        decision.traiter_demande(robot, demande(1, "je suis seule"), DICO)
        fin_1 = robot.position
        decision.traiter_demande(
            robot, demande(2, "je suis inquiet", "R2"), DICO)
        premier_pas_2 = next(p for p in robot.trace.pas if p["demande"] == 2)
        # La demande 2 commence la ou la demande 1 s'est terminee.
        self.assertEqual(tuple(premier_pas_2["position"]), fin_1)

    def test_les_5_scenarios_fournis(self):
        for n in range(1, 6):
            sc = rio.charger_scenario(str(RACINE / "cartes" / f"scenario_0{n}.json"))
            carte = rio.charger_carte(str(RACINE / "cartes" / f"{sc['carte']}.json"))
            with self.subTest(scenario=sc["nom"]):
                robot = fabriquer_robot(carte)
                reussies = decision.executer_scenario(robot, sc, DICO)
                trace = robot.trace.en_dictionnaire()
                self.assertEqual(len(trace["livraisons"]), len(sc["demandes"]))
                self.assertEqual(trace["resume"]["reussies"], reussies)
                self.assertEqual(
                    sum(l["pas_utilises"] for l in trace["livraisons"]),
                    trace["resume"]["pas_total"])
                self.assertIsNone(robot.objet_porte)

    def test_repli_voisine_1_scenario_3(self):
        sc = rio.charger_scenario(str(RACINE / "cartes" / "scenario_03.json"))
        carte = rio.charger_carte(str(RACINE / "cartes" / f"{sc['carte']}.json"))
        robot = fabriquer_robot(carte)
        decision.executer_scenario(robot, sc, DICO)
        liv = robot.trace.livraisons[0]
        self.assertEqual((liv["repli"], liv["objet"]), ("voisine_1", "telephone"))


if __name__ == "__main__":
    unittest.main()
