"""
Programme principal : le fichier est lancé avec 4 arguments, charge les fichiers, 
construit l'environnement et le robot, exécute le scénario et écrit la trace. 
"""
import sys
from pathlib import Path

import reconfort_io as rio
from robot import Robot
from environnement import Environnement
from decision import executer_scenario

EQUIPE = ["HAJEE Neha", "CAMARA ALY Zeinab"]

def main(argv): 
    """Paramètres : argv , la liste des arguments le nom du programme y compris
    Renvoie: les trois cas c'est-à-dire, 0 en cas de succès, 1 pour un fichier invalide et 
    2 pour un mauvais nombre d'arguments
    """
    if len(argv) != 5: 
        print(" usage: python agent.py <carte> <scenario> <dossier_donnees> <trace>", file = sys.stderr)
        return 2
    
    chemin_carte = Path(argv[1])
    chemin_scenario = Path(argv[2])
    chemin_dossier_donnees = Path(argv[3])
    chemin_trace = Path(argv[4])

    try: 
        carte = rio.charger_carte(chemin_carte)
        scenario = rio.charger_scenario(chemin_scenario)
        dico = rio.charger_dictionnaire(chemin_dossier_donnees / "dictionnaire.json")
        armoire = rio.charger_armoire(chemin_dossier_donnees / f"{scenario['armoire']}.json")

        #validation 

    except rio.ErreurFichier as err:
        print(f"erreur de chargement : {err}", file=sys.stderr)
        return 1

    env = Environnement(carte, armoire)
    trace = rio.Trace(carte["nom"], scenario["nom"], EQUIPE)
    connaissances = {cle: valeur for cle, valeur in carte.items() if cle != "grille"}
    robot = Robot(env, connaissances, armoire["casier_depart"], trace)

    executer_scenario(robot, scenario, dico)

    chemin_trace.parent.mkdir(parents=True, exist_ok=True)
    trace.ecrire(chemin_trace)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))