"""Tests de feature/entrees-validation : validation.py

Un fichier CASSE par categorie de l'enonce 5.6. Pour chaque cas, on part de
fichiers valides (les fournis), on casse UNE seule chose, et on verifie que
valider_entrees leve ErreurDonnees avec un message qui nomme le probleme.
Le test "les fichiers valides passent" garantit que les cas casses echouent
bien A CAUSE de la casse, et pas pour une autre raison.
"""

import copy
import json
import sys
import tempfile
import unittest

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agent"))

import validation as val  # noqa: E402

def lire(chemin):
    return json.loads((RACINE / chemin).read_text("utf-8"))


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dossier = Path(self._tmp.name)
        self.carte = lire("cartes/appartement_01.json")
        self.scenario = lire("cartes/scenario_01.json")
        self.dico = lire("donnees/dictionnaire.json")
        self.armoire = lire("donnees/armoire_standard.json")

    def tearDown(self):
        self._tmp.cleanup()

    def ecrire_tout(self):
        """Ecrit les 4 fichiers (eventuellement casses) et renvoie les chemins."""
        (self.dossier / "carte.json").write_text(
            json.dumps(self.carte), encoding="utf-8")
        (self.dossier / "scenario.json").write_text(
            json.dumps(self.scenario), encoding="utf-8")
        (self.dossier / "dictionnaire.json").write_text(
            json.dumps(self.dico), encoding="utf-8")
        (self.dossier / "armoire_standard.json").write_text(
            json.dumps(self.armoire), encoding="utf-8")
        return (self.dossier / "carte.json", self.dossier / "scenario.json",
                self.dossier)

    def valider(self):
        return val.valider_entrees(*self.ecrire_tout())

    def assertCasse(self, morceau):
        """valider() doit lever ErreurDonnees dont le message contient `morceau`."""
        with self.assertRaises(val.ErreurDonnees) as ctx:
            self.valider()
        self.assertIn(morceau, str(ctx.exception))


class TestFichiersValides(Base):
    def test_fichiers_modifiables_de_depart_sont_valides(self):
        carte, scenario, dico, armoire = self.valider()
        self.assertEqual(carte["nom"], "appartement_01")

    def test_les_5_jeux_fournis_sont_valides(self):
        for n in range(1, 6):
            with self.subTest(n=n):
                val.valider_entrees(RACINE / "cartes" / f"appartement_0{n}.json",
                                    RACINE / "cartes" / f"scenario_0{n}.json",
                                    RACINE / "donnees")


class TestLecture(Base):
    def test_fichier_absent(self):
        chemins = self.ecrire_tout()
        (self.dossier / "carte.json").unlink()
        with self.assertRaises(val.ErreurDonnees) as ctx:
            val.valider_entrees(*chemins)
        self.assertIn("introuvable", str(ctx.exception))

    def test_dictionnaire_absent_du_dossier_de_donnees(self):
        chemins = self.ecrire_tout()
        (self.dossier / "dictionnaire.json").unlink()
        with self.assertRaises(val.ErreurDonnees):
            val.valider_entrees(*chemins)

    def test_armoire_nommee_par_le_scenario_absente(self):
        self.scenario["armoire"] = "armoire_fantome"
        self.assertCasse("armoire_fantome")

    def test_chemin_qui_est_un_dossier(self):
        chemins = self.ecrire_tout()
        with self.assertRaises(val.ErreurDonnees):
            val.valider_entrees(self.dossier, chemins[1], chemins[2])

    def test_pas_utf8(self):
        chemins = self.ecrire_tout()
        (self.dossier / "carte.json").write_bytes(b'{"nom": "caf\xe9"}')
        with self.assertRaises(val.ErreurDonnees) as ctx:
            val.valider_entrees(*chemins)
        self.assertIn("UTF-8", str(ctx.exception))

    def test_json_invalide(self):
        chemins = self.ecrire_tout()
        (self.dossier / "carte.json").write_text('{"format": ', encoding="utf-8")
        with self.assertRaises(val.ErreurDonnees) as ctx:
            val.valider_entrees(*chemins)
        self.assertIn("JSON", str(ctx.exception))

    def test_json_trop_imbrique_ne_plante_pas(self):
        chemins = self.ecrire_tout()
        (self.dossier / "carte.json").write_text("[" * 100000, encoding="utf-8")
        with self.assertRaises(val.ErreurDonnees):
            val.valider_entrees(*chemins)

    def test_racine_pas_un_objet(self):
        chemins = self.ecrire_tout()
        (self.dossier / "carte.json").write_text("[1, 2]", encoding="utf-8")
        with self.assertRaises(val.ErreurDonnees):
            val.valider_entrees(*chemins)

    def test_format_inattendu(self):
        self.carte["format"] = "robot-reconfort/armoire"
        self.assertCasse("format")

    def test_version_inattendue(self):
        self.armoire["version"] = 2
        self.assertCasse("version")


class TestCarte(Base):
    def test_champ_absent(self):
        del self.carte["residents"]
        self.assertCasse("residents")

    def test_mauvais_type(self):
        self.carte["dimensions"]["hauteur"] = "9"
        self.assertCasse("hauteur")

    def test_booleen_n_est_pas_un_entier(self):
        self.carte["depart_robot"] = [True, 1]
        self.assertCasse("depart_robot")

    def test_grille_non_rectangulaire(self):
        self.carte["grille"][3] = self.carte["grille"][3][:-1]
        self.assertCasse("rectangulaire")

    def test_dimensions_incoherentes(self):
        self.carte["dimensions"]["largeur"] = 14
        self.assertCasse("dimensions")

    def test_symbole_inconnu(self):
        ligne = self.carte["grille"][2]
        self.carte["grille"][2] = ligne[:5] + "?" + ligne[6:]
        self.assertCasse("symbole inconnu")

    def test_position_hors_grille(self):
        self.carte["armoire"]["position"] = [50, 4]
        self.assertCasse("hors de la grille")

    def test_depart_pas_sur_R(self):
        self.carte["depart_robot"] = [6, 2]
        self.assertCasse("depart_robot")

    def test_armoire_pas_sur_A(self):
        self.carte["armoire"]["position"] = [6, 5]
        self.assertCasse("armoire")

    def test_dictionnaire_pas_sur_D(self):
        self.carte["dictionnaire"]["position"] = [7, 7]
        self.assertCasse("dictionnaire")

    def test_resident_pas_sur_P(self):
        self.carte["residents"][0]["position"] = [6, 10]
        self.assertCasse("R1")

    def test_ids_residents_en_double(self):
        self.carte["residents"][1]["id"] = "R1"
        self.assertCasse("meme identifiant")


class TestDictionnaire(Base):
    def test_emotion_inconnue(self):
        self.dico["entrees"][0]["emotion"] = "nostalgie"
        self.assertCasse("emotion inconnue")

    def test_intensite_inconnue(self):
        self.dico["entrees"][0]["intensite"] = "extreme"
        self.assertCasse("intensite inconnue")

    def test_mot_dans_deux_entrees(self):
        mot = self.dico["entrees"][0]["formes"][0]
        self.dico["entrees"][1]["formes"].append(mot)
        self.assertCasse(mot)

    def test_champ_absent(self):
        del self.dico["entrees"]
        self.assertCasse("entrees")


class TestArmoire(Base):
    def test_casier_hors_bornes_ligne(self):
        self.armoire["casiers"][0]["ligne"] = 3
        self.assertCasse("hors de l'armoire")

    def test_casier_hors_bornes_colonne(self):
        self.armoire["casiers"][0]["colonne"] = 8
        self.assertCasse("hors de l'armoire")

    def test_casier_en_double(self):
        self.armoire["casiers"].append(copy.deepcopy(self.armoire["casiers"][0]))
        self.assertCasse("deux fois")

    def test_etiquette_incoherente_avec_la_position(self):
        self.armoire["casiers"][0]["emotion"] = "colere" \
            if self.armoire["casiers"][0]["emotion"] != "colere" else "joie"
        self.assertCasse("etiquette")

    def test_casier_depart_hors_armoire(self):
        self.armoire["casier_depart"] = [1, 9]
        self.assertCasse("casier_depart")

    def test_objet_de_mauvais_type(self):
        self.armoire["casiers"][0]["objet"] = 42
        self.assertCasse("objet")

    def test_emotions_armoire_differentes_du_dictionnaire(self):
        # Ordre change dans l'armoire seule : les etiquettes des casiers ne
        # correspondent plus a leur colonne -> erreur.
        e = self.armoire["emotions"]
        e[0], e[1] = e[1], e[0]
        with self.assertRaises(val.ErreurDonnees):
            self.valider()

    def test_coherence_croisee_seule(self):
        # Armoire valide en elle-meme, mais ordre different du dictionnaire.
        self.dico["emotions"] = list(reversed(self.dico["emotions"]))
        self.assertCasse("differe")


class TestScenario(Base):
    def test_scenario_pour_une_autre_carte(self):
        self.scenario["carte"] = "appartement_02"
        self.assertCasse("appartement_02")

    def test_resident_absent_de_la_carte(self):
        self.scenario["demandes"][0]["resident"] = "R9"
        self.assertCasse("R9")

    def test_numero_en_double(self):
        self.scenario["demandes"][1]["numero"] = self.scenario["demandes"][0]["numero"]
        self.assertCasse("double")

    def test_nom_d_armoire_avec_chemin(self):
        self.scenario["armoire"] = "../secret"
        self.assertCasse("invalide")

    def test_champ_message_absent(self):
        del self.scenario["demandes"][0]["message"]
        self.assertCasse("message")


if __name__ == "__main__":
    unittest.main()
