"""Tests de feature/traitement_messages : traitement_messages.py, c'est-a-dire
la reception d'une demande et la lecture du dictionnaire (enonce 6.1).

On couvre le point 3 de la section 8 : un message par emotion, un message ou
deux mots connus apparaissent et ou c'est le premier qui gagne, et un message
sans aucun mot reconnu.

Lancement, depuis base_fournie :
    python -m unittest tests.test_traitement_messages -v
"""

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agent"))

import reconfort_io as rio  # noqa: E402
from traitement_messages import reception_message, trouver_emotion  # noqa: E402

CARTE = rio.charger_carte(RACINE / "cartes" / "appartement_01.json")
DICO = rio.charger_dictionnaire(RACINE / "donnees" / "dictionnaire.json")


class TestTrouverEmotion(unittest.TestCase):

    def emotion(self, message):
        """Normalise le message comme le fait le robot, puis cherche son
        emotion dans le dictionnaire. Renvoie (emotion, intensite)."""
        return trouver_emotion(rio.normaliser(message), DICO)

    def test_un_message_par_emotion(self):
        """Un mot du dictionnaire pour chacune des 8 emotions de la roue."""
        messages = [
            ("Je me sens apaisé ce soir.", "joie"),
            ("Je me suis senti accepté par les autres.", "confiance"),
            ("Je suis anxieux depuis ce matin.", "peur"),
            ("Il se passe quelque chose de bizarre.", "surprise"),
            ("J'ai le cafard aujourd'hui.", "tristesse"),
            ("Je suis blasé de tout ça.", "degout"),
            ("Je suis agacé par ce bruit.", "colere"),
            ("Je suis attentif à ce qui va arriver.", "anticipation"),
        ]
        for message, attendue in messages:
            with self.subTest(emotion=attendue):
                self.assertEqual(self.emotion(message), (attendue, "faible"))

    def test_premier_mot_reconnu_gagne(self):
        """Exemple de l'enonce 6.1 : "sidere" (surprise) vient avant "seule"
        (tristesse), c'est donc la surprise qui gagne."""
        message = "Je suis sidéré, la télévision s'est allumée toute seule."
        self.assertEqual(self.emotion(message), ("surprise", "forte"))

    def test_aucun_mot_reconnu(self):
        """Aucun mot du dictionnaire : ni emotion ni intensite."""
        self.assertEqual(self.emotion("Bonjour, merci beaucoup."), (None, None))

    def test_majuscules_et_accents(self):
        """La normalisation rend le message comparable au dictionnaire."""
        self.assertEqual(self.emotion("Je suis ANXIEUX"), ("peur", "faible"))
        self.assertEqual(self.emotion("apaise"), self.emotion("APAISÉ"))


class TestReceptionMessage(unittest.TestCase):

    def test_resident_connu(self):
        """R1 est en [6, 11] sur appartement_01 ; le message est normalise."""
        numero, id_resident, position, mots = reception_message(
            1, "J'ai le cafard", "R1", CARTE["residents"])
        self.assertEqual(numero, 1)
        self.assertEqual(id_resident, "R1")
        self.assertEqual(position, [6, 11])
        self.assertIn("cafard", mots)

    def test_resident_inconnu(self):
        """R9 n'existe pas sur la carte : ValueError."""
        with self.assertRaises(ValueError):
            reception_message(99, "bonjour", "R9", CARTE["residents"])


if __name__ == "__main__":
    unittest.main()
