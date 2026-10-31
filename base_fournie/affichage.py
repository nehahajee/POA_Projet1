"""Affiche la trace du parcours du robot sur une carte donnee, avec un temps
de pause reglable entre deux pas (parametre [pause], 0.15 s par defaut).
Ne fait pas partie de l'agent, sert pour le debogage et la video.
Ne lit pas la grille mais reconstruit la memoire du robot a partir des
perceptions enregistrees dans la trace.
Lancement depuis base_fournie : python3 affichage.py <carte.json> <trace.json> [pause]"""

import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE / "agent"))

import reconfort_io as rio  # noqa: E402
from robot import CarteMentale  # noqa: E402
from deplacement import case_voisine  # noqa: E402

PAUSE_PAR_DEFAUT = 0.15
LEGENDE = "@ robot   ? inconnu   # mur   A armoire   D dictionnaire   P resident"


def carte_mentale_de_depart(carte):
    """Memoire du robot au depart, comme dans Robot : tout est inconnu sauf
    l'armoire, le dictionnaire et les residents. La grille n'est jamais lue.

    Parametres :
        carte : la carte chargee par reconfort_io
    Renvoie : une CarteMentale.
    """
    hauteur = carte["dimensions"]["hauteur"]
    largeur = carte["dimensions"]["largeur"]
    armoire = carte["armoire"]["position"]
    dictionnaire = carte["dictionnaire"]["position"]
    residents = [r["position"] for r in carte["residents"]]
    return CarteMentale(hauteur, largeur, armoire, dictionnaire, residents)


def dessiner(carte_mentale, pas, objet_porte):
    """Efface l'ecran et dessine une image : la carte mentale avec le robot,
    puis l'action du pas, le selecteur et l'objet porte.

    Parametres :
        carte_mentale : la memoire du robot a ce pas
        pas : un pas de la trace (position, action, argument, ...)
        objet_porte : l'objet que porte le robot, ou None
    Renvoie : rien (affiche dans le terminal).
    """
    print("\033[2J\033[H", end="")
    # Numeros de colonnes au-dessus et de lignes a gauche, comme l'annexe D,
    # pour lire directement les coordonnees [ligne, colonne] d'une case.
    colonnes = "".join(str(j % 10) for j in range(carte_mentale.largeur))
    print(f"   {colonnes}")
    for i, ligne in enumerate(carte_mentale.afficher(pas["position"]).split("\n")):
        print(f"{i:>2} {ligne}")
    print()
    print(f"t = {pas['t']}   demande {pas['demande']}   "
          f"{pas['action']} {pas['argument'] or ''}")
    ligne = f"selecteur : {pas['casier']}"
    if pas["contenu_casier"] is not None:
        ligne += f"   casier : {pas['contenu_casier']}"
    print(ligne)
    print(f"porte : {objet_porte or 'rien'}")
    print(LEGENDE)


def afficher_bilan(trace):
    """Affiche le resume de la trace et une ligne par livraison."""
    print()
    print(f"resume : {trace['resume']}")
    for liv in trace["livraisons"]:
        etat = "reussie" if liv["succes"] else f"echec ({liv['motif_echec']})"
        print(f"  demande {liv['demande']} -> {liv['resident']} : {etat}, "
              f"objet : {liv['objet']}")


def main(argv):
    """Rejoue une trace pas a pas dans le terminal.

    Parametres :
        argv : la liste des arguments de la ligne de commande, nom du
            programme compris (3 ou 4 elements).
    Renvoie : 0 si tout s'est bien passe (ou si on a interrompu avec Ctrl+C),
        1 si un fichier est absent, invalide ou ne correspond pas a la carte,
        2 si le nombre d'arguments est mauvais.
    """
    if len(argv) not in (3, 4):
        print("usage: python3 affichage.py <carte.json> <trace.json> [pause]",
              file=sys.stderr)
        return 2

    try:
        pause = float(argv[3]) if len(argv) == 4 else PAUSE_PAR_DEFAUT
    except ValueError:
        print(f"pause invalide : {argv[3]!r} (un nombre de secondes est attendu)",
              file=sys.stderr)
        return 2

    try:
        carte = rio.charger_carte(Path(argv[1]))
        with open(argv[2], encoding="utf-8") as f:
            trace = json.load(f)
    except (rio.ErreurFichier, OSError, json.JSONDecodeError) as err:
        print(f"erreur de chargement : {err}", file=sys.stderr)
        return 1

    if trace.get("carte") != carte["nom"]:
        print(f"la trace concerne la carte {trace.get('carte')!r}, "
              f"pas {carte['nom']!r}", file=sys.stderr)
        return 1

    memoire = carte_mentale_de_depart(carte)
    objet_porte = None

    try:
        for pas in trace["pas"]:
            # La trace donne l'etat AVANT l'action : on met d'abord a jour la
            # memoire avec ce que le robot voyait, puis on dessine.
            memoire.mettre_a_jour(pas["position"], pas["perception"])
            dessiner(memoire, pas, objet_porte)
            time.sleep(pause)
            if pas["action"] == "PRENDRE":
                objet_porte = pas["argument"]
            elif pas["action"] == "DONNER":
                objet_porte = None

        # Position d'arrivee du dernier pas, jamais enregistree dans la trace.
        if trace["pas"] and trace["pas"][-1]["action"] == "AVANCER":
            dernier = dict(trace["pas"][-1])
            dernier["position"] = case_voisine(dernier["position"], dernier["argument"])
            dessiner(memoire, dernier, objet_porte)
    except KeyboardInterrupt:
        print("\ninterrompu")
        return 0

    afficher_bilan(trace)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
