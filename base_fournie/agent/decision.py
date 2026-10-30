""" Decision : orchestre une demande de bout en bout (feature/boucle-agent).

C'est le "cerveau" : il ne perçoit rien lui-même et ne touche jamais à la
grille. Il appelle les autres modules dans l'ordre de l'énoncé (section 3.5) :

    traitement_messages  -> comprendre le message
    deplacement          -> rejoindre dictionnaire / armoire / résident
    armoire              -> choisir le casier
    robot                -> les actions (CONSULTER, PRENDRE, DONNER...)
"""

from armoire import calculer_candidats, fouiller_armoire 
from deplacement import (deplacement_armoire, deplacement_dict,
                               deplacement_resident) 
from traitement_messages import reception_message, trouver_emotion 

# Motifs d'échec (enonce 6.3) + deux motifs AJOUTES par nous.
EMOTION_INDETERMINEE = "emotion indeterminee"
ARMOIRE_VIDE = "armoire vide"
RESIDENT_INACCESSIBLE = "resident inaccessible"
DICTIONNAIRE_INACCESSIBLE = "dictionnaire inaccessible"
ARMOIRE_INACCESSIBLE = "armoire inaccessible"


def _echec(robot, numero, id_resident, motif, emotion=None, intensite=None,
           casier=None, repli="aucun"):
    """Journalise une demande échouée : le robot passe à la demande suivante,
    là où il se trouve."""
    robot.trace.ajouter_livraison(demande=numero, resident=id_resident,
                                  emotion=emotion, intensite=intensite,
                                  casier_choisi=casier, repli=repli,
                                  objet=None, succes=False, motif_echec=motif)


def traiter_demande(robot, demande, dico):
    """Traite UNE demande {"numero", "resident", "message"}.

    Ordre : dictionnaire -> CONSULTER -> armoire -> fouille -> vérifier que le
    résident est atteignable -> retour armoire -> PRENDRE -> résident -> DONNER.
    On vérifie le résident AVANT de prendre : le robot ne peut rien poser, donc
    s'il prenait l'objet puis découvrait le résident muré, il le garderait
    pour toujours et bloquerait les demandes suivantes.

    Renvoie True si l'objet a été donné, False sinon (échec journalisé).
    """
    numero = demande["numero"]
    id_resident = demande["resident"]
    robot.demande = numero

    residents = [{"id": i, "position": p} for i, p in robot.residents.items()]
    _, _, _, mots = reception_message(numero, demande["message"],
                                      id_resident, residents)

    # 1. Dictionnaire : CONSULTER, puis émotion du premier mot reconnu.
    if not deplacement_dict(robot, robot.dictionnaire):
        _echec(robot, numero, id_resident, DICTIONNAIRE_INACCESSIBLE)
        return False
    robot.consulter()
    emotion, intensite = trouver_emotion(mots, dico)
    if emotion is None:
        _echec(robot, numero, id_resident, EMOTION_INDETERMINEE)
        return False

    # 2. Armoire : on choisit le casier (sans encore rien prendre).
    if not deplacement_armoire(robot, robot.armoire):
        _echec(robot, numero, id_resident, ARMOIRE_INACCESSIBLE,
               emotion, intensite)
        return False
    candidats = calculer_candidats(emotion, intensite,
                                   dico["emotions"], dico["intensites"])
    casier, repli, objet = fouiller_armoire(robot, candidats)
    if casier is None:
        _echec(robot, numero, id_resident, ARMOIRE_VIDE, emotion, intensite)
        return False

    # 3. Le résident est-il atteignable ? (sinon on ne prend rien)
    if not deplacement_resident(robot, robot.residents[id_resident]):
        _echec(robot, numero, id_resident, RESIDENT_INACCESSIBLE,
               emotion, intensite, casier, repli)
        return False

    # 4. Retour à l'armoire (le sélecteur est resté sur le casier), on prend.
    deplacement_armoire(robot, robot.armoire)
    robot.prendre(objet)

    # 5. Livraison.
    deplacement_resident(robot, robot.residents[id_resident])
    robot.donner(id_resident,objet)
    robot.trace.ajouter_livraison(demande=numero, resident=id_resident,
                                  emotion=emotion, intensite=intensite,
                                  casier_choisi=casier, repli=repli,
                                  objet=objet, succes=True)
    return True


def executer_scenario(robot, scenario, dico):
    """Traite toutes les demandes dans l'ordre. L'état du robot (position,
    sélecteur, carte mentale) est conservé d'une demande à l'autre : il ne
    revient pas à son point de départ (enonce 6.3).
    Renvoie le nombre de demandes réussies."""
    reussies = 0
    for demande in scenario["demandes"]:
        if traiter_demande(robot, demande, dico):
            reussies += 1
    return reussies
