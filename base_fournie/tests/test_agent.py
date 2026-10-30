"""Tests de feature/agent : agent.py, c'est-a-dire le programme complet.

On teste le contrat d'appel (enonce section 2) : quatre arguments, code 0 si
tout va bien, code non nul et aucune trace ecrite si un fichier est absent
ou refuse par la validation (section 5.6). Les fichiers casses, categorie
par categorie, sont testes dans test_validation.py.

Lancement, depuis base_fournie :
    python -m unittest tests.test_agent -v
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agent"))

import agent  # noqa: E402

CARTE = RACINE / "cartes" / "appartement_01.json"
SCENARIO = RACINE / "cartes" / "scenario_01.json"
DONNEES = RACINE / "donnees"


class TestAgent(unittest.TestCase):

    def setUp(self):
        """Dossier temporaire neuf pour chaque test : si la trace existe,
        c'est forcement ce test qui l'a ecrite."""
        self.dossier = tempfile.TemporaryDirectory()
        self.trace = Path(self.dossier.name) / "trace.json"

    def tearDown(self):
        """Supprime le dossier temporaire, meme si le test a echoue."""
        self.dossier.cleanup()

    def lancer(self, arguments):
        """Appelle agent.main comme le ferait la ligne de commande et renvoie
        (code de retour, texte ecrit sur stderr)."""
        erreur = io.StringIO()
        with contextlib.redirect_stderr(erreur):
            code = agent.main(["agent.py"] + [str(a) for a in arguments])
        return code, erreur.getvalue()

    def test_scenario_1(self):
        """appartement_01 + scenario_01 : code 0, trace ecrite, 4 demandes
        reussies et l'equipe de rendu.json."""
        code, _ = self.lancer([CARTE, SCENARIO, DONNEES, self.trace])
        self.assertEqual(code, 0)
        self.assertTrue(self.trace.exists())

        with open(self.trace, encoding="utf-8") as f:
            trace = json.load(f)
        self.assertEqual(trace["equipe"], agent.EQUIPE)
        self.assertEqual(trace["resume"]["demandes"], 4)
        self.assertEqual(trace["resume"]["reussies"], 4)

    def test_scenario_2(self):
        """Carte inexistante : code 1, message sur stderr, aucune trace."""
        absente = RACINE / "cartes" / "inexistante.json"
        code, erreur = self.lancer([absente, SCENARIO, DONNEES, self.trace])
        self.assertEqual(code, 1)
        self.assertFalse(self.trace.exists())
        self.assertNotEqual(erreur, "")

    def test_scenario_3(self):
        """Aucun argument, ou un argument en trop : code 2, aucune trace."""
        code, erreur = self.lancer([])
        self.assertEqual(code, 2)
        self.assertNotEqual(erreur, "")

        code, _ = self.lancer([CARTE, SCENARIO, DONNEES, self.trace, "en_trop"])
        self.assertEqual(code, 2)
        self.assertFalse(self.trace.exists())

    def test_scenario_4(self):
        """scenario_01 (prevu pour appartement_01) lance sur appartement_02 :
        la validation le refuse, code 1, message sur stderr, aucune trace."""
        autre_carte = RACINE / "cartes" / "appartement_02.json"
        code, erreur = self.lancer([autre_carte, SCENARIO, DONNEES, self.trace])
        self.assertEqual(code, 1)
        self.assertFalse(self.trace.exists())
        self.assertNotEqual(erreur, "")


if __name__ == "__main__":
    unittest.main()
