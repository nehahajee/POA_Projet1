"""
Programme principal : le fichier est lancé avec 4 arguments, valide les fichiers(validation.py), 
construit l'environnement et le robot, exécute le scénario et écrit la trace. 
Lancement depuis base_fournie : python agent/agent.py <carte> <scenario> <dossier_donnees> <trace>
En cas de fichier invalide, écrit un message d'erreur sur stderr et renvoie un 
code différent de 0 (n'écrit aucune trace).
"""
import sys
from pathlib import Path

import reconfort_io as rio
from robot import Robot
from environnement import Environnement
from decision import executer_scenario
from validation import valider_entrees, ErreurDonnees

EQUIPE = ["HAJEE Neha", "CAMARA ALY Zeinab"]

def main(argv):
    """Lance le robot sur une carte et un scénario, et écrit la trace.
        Paramètres : argv (la liste des arguments de la ligne de commande,
        le nom du programme y compris).
        Renvoie : 0 si tout s'est bien passé, 1 si un fichier est absent ou invalide 
        et 2 si le nombre d'arguments est mauvais."""
    if len(argv) != 5:
        print("usage: python agent.py <carte> <scenario> <dossier_donnees> <trace>", file=sys.stderr)
        return 2
    
    chemin_carte = Path(argv[1])
    chemin_scenario = Path(argv[2])
    chemin_dossier_donnees = Path(argv[3])
    chemin_trace = Path(argv[4])

    try:
        carte, scenario, dico, armoire = valider_entrees(chemin_carte, chemin_scenario, chemin_dossier_donnees)

    except ErreurDonnees as err:
        print(f"fichier invalide : {err}", file=sys.stderr)
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
