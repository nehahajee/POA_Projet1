"""Validation des 4 fichiers d'entree (enonce 5.6) -- feature/entrees-validation.

reconfort_io ne verifie que le fichier lui-meme (existe, UTF-8, JSON valide,
format et version). Ici on verifie le CONTENU : champs, types, coherence.

Toute anomalie leve une seule exception metier, ErreurDonnees, avec un message
clair ("carte.json : ..."). agent.py l'attrape, l'affiche sur stderr et sort
avec un code non nul, SANS avoir ecrit de trace.

Point d'entree :  carte, scenario, dico, armoire = valider_entrees(
                      chemin_carte, chemin_scenario, dossier_donnees)
"""
import sys

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE)) # noqa: E402

import reconfort_io as rio

SYMBOLES = "#.RADP"      # symboles autorises dans la grille 
NB_EMOTIONS = 8          # colonnes de l'armoire
NB_INTENSITES = 3        # lignes de l'armoire


class ErreurDonnees(Exception):
    """Fichier d'entree absent, mal forme ou incoherent (enonce 5.6)."""


# ---------------------------------------------------------------------------
# Outils de verification
# ---------------------------------------------------------------------------
 
def _charger(fonction, chemin):
    """Charge un fichier avec reconfort_io et convertit ses erreurs."""
    try:
        return fonction(chemin)
    except rio.ErreurFichier as err:
        raise ErreurDonnees(str(err)) from None
    except RecursionError:
        raise ErreurDonnees(f"{chemin} : JSON trop profondement imbrique") from None
 
 
def _erreur(contexte, message):
    raise ErreurDonnees(f"{contexte} : {message}")
 
 
def _est_entier(valeur):
    # bool est un sous-type de int en Python : True ne doit pas passer.
    return isinstance(valeur, int) and not isinstance(valeur, bool)
 
 
def _champ(objet, nom, type_attendu, contexte):
    """Renvoie objet[nom] apres avoir verifie qu'il existe et a le bon type."""
    if not isinstance(objet, dict):
        _erreur(contexte, "un objet JSON est attendu")
    if nom not in objet:
        _erreur(contexte, f"champ obligatoire absent : '{nom}'")
    valeur = objet[nom]
    if type_attendu is int:
        correct = _est_entier(valeur)
    else:
        correct = isinstance(valeur, type_attendu)
    if not correct:
        _erreur(contexte, f"le champ '{nom}' doit etre de type "
                          f"{type_attendu.__name__}, pas {type(valeur).__name__}")
    return valeur
 
 
def _liste_de_textes(objet, nom, contexte):
    valeurs = _champ(objet, nom, list, contexte)
    for v in valeurs:
        if not isinstance(v, str) or not v:
            _erreur(contexte, f"'{nom}' doit contenir uniquement des textes non vides")
    return valeurs
 
 
def _position(objet, nom, contexte):
    """Verifie un couple [ligne, colonne] d'entiers et le renvoie en tuple."""
    valeur = _champ(objet, nom, list, contexte)
    if len(valeur) != 2 or not all(_est_entier(v) for v in valeur):
        _erreur(contexte, f"'{nom}' doit etre un couple [ligne, colonne] "
                          f"d'entiers, pas {valeur!r}")
    return tuple(valeur)
 
 
# ---------------------------------------------------------------------------
# Carte
# ---------------------------------------------------------------------------
 
def _verifier_sur_symbole(grille, position, symbole, nom, contexte):
    ligne, colonne = position
    if not (0 <= ligne < len(grille) and 0 <= colonne < len(grille[0])):
        _erreur(contexte, f"{nom} en {list(position)} est hors de la grille")
    trouve = grille[ligne][colonne]
    if trouve != symbole:
        _erreur(contexte, f"{nom} en {list(position)} : la grille contient "
                          f"'{trouve}' a cet endroit, '{symbole}' attendu")
 
 
def _verifier_dimensions(carte, grille, contexte):
    dimensions = _champ(carte, "dimensions", dict, contexte)
    hauteur = _champ(dimensions, "hauteur", int, contexte + " (dimensions)")
    largeur = _champ(dimensions, "largeur", int, contexte + " (dimensions)")
    if hauteur <= 0 or largeur <= 0:
        _erreur(contexte, "les dimensions doivent etre strictement positives")
    if len(grille) != hauteur or len(grille[0]) != largeur:
        _erreur(contexte, f"dimensions annoncees {hauteur}x{largeur} mais la "
                          f"grille fait {len(grille)}x{len(grille[0])}")
 
 
def _verifier_grille(carte, contexte):
    """Grille non vide, faite de textes de meme longueur, symboles connus."""
    grille = _champ(carte, "grille", list, contexte)
    if not grille:
        _erreur(contexte, "la grille est vide")
    for i, ligne in enumerate(grille):
        if not isinstance(ligne, str):
            _erreur(contexte, f"la ligne {i} de la grille doit etre un texte")
        if len(ligne) != len(grille[0]):
            _erreur(contexte, f"grille non rectangulaire : la ligne {i} a "
                              f"{len(ligne)} colonnes, la ligne 0 en a {len(grille[0])}")
        for j, symbole in enumerate(ligne):
            if symbole not in SYMBOLES:
                _erreur(contexte, f"symbole inconnu '{symbole}' en [{i}, {j}]")
    return grille
 
 
def _verifier_residents(carte, grille, contexte):
    ids = set()
    for r in _champ(carte, "residents", list, contexte):
        id_resident = _champ(r, "id", str, contexte + " (residents)")
        _champ(r, "nom", str, contexte + f" (resident {id_resident})")
        if id_resident in ids:
            _erreur(contexte, f"deux residents ont le meme identifiant : {id_resident}")
        ids.add(id_resident)
        _verifier_sur_symbole(grille, _position(r, "position", contexte + f" ({id_resident})"),
                              "P", f"resident {id_resident}", contexte)
 
 
def valider_carte(carte, contexte="carte"):
    _champ(carte, "nom", str, contexte)
    grille = _verifier_grille(carte, contexte)
    _verifier_dimensions(carte, grille, contexte)
 
    depart = _position(carte, "depart_robot", contexte)
    _verifier_sur_symbole(grille, depart, "R", "depart_robot", contexte)
    for cle, symbole in (("armoire", "A"), ("dictionnaire", "D")):
        objet = _champ(carte, cle, dict, contexte)
        position = _position(objet, "position", f"{contexte} ({cle})")
        _verifier_sur_symbole(grille, position, symbole, cle, contexte)
 
    _verifier_residents(carte, grille, contexte)
 
 
# ---------------------------------------------------------------------------
# Dictionnaire
# ---------------------------------------------------------------------------
 
def _verifier_listes_emotions(donnees, contexte):
    emotions = _liste_de_textes(donnees, "emotions", contexte)
    intensites = _liste_de_textes(donnees, "intensites", contexte)
    if len(emotions) != NB_EMOTIONS or len(set(emotions)) != NB_EMOTIONS:
        _erreur(contexte, f"'emotions' doit contenir {NB_EMOTIONS} emotions distinctes")
    if len(intensites) != NB_INTENSITES or len(set(intensites)) != NB_INTENSITES:
        _erreur(contexte, f"'intensites' doit contenir {NB_INTENSITES} intensites distinctes")
    return emotions, intensites
 
 
def valider_dictionnaire(dico, contexte="dictionnaire"):
    _champ(dico, "nom", str, contexte)
    emotions, intensites = _verifier_listes_emotions(dico, contexte)
 
    vus = {}   # mot -> numero de l'entree qui le contient
    for numero, entree in enumerate(_champ(dico, "entrees", list, contexte)):
        ctx = f"{contexte} (entree {numero})"
        formes = _liste_de_textes(entree, "formes", ctx)
        emotion = _champ(entree, "emotion", str, ctx)
        intensite = _champ(entree, "intensite", str, ctx)
        if emotion not in emotions:
            _erreur(ctx, f"emotion inconnue : '{emotion}'")
        if intensite not in intensites:
            _erreur(ctx, f"intensite inconnue : '{intensite}'")
        for mot in formes:
            if mot in vus and vus[mot] != numero:
                _erreur(contexte, f"le mot '{mot}' est dans deux entrees "
                                  f"({vus[mot]} et {numero})")
            vus[mot] = numero
 
 
# ---------------------------------------------------------------------------
# Armoire
# ---------------------------------------------------------------------------
 
def _verifier_casier(casier, ctx, emotions, intensites):
    """Verifie un casier et renvoie sa position (ligne, colonne)."""
    ligne = _champ(casier, "ligne", int, ctx)
    colonne = _champ(casier, "colonne", int, ctx)
    emotion = _champ(casier, "emotion", str, ctx)
    intensite = _champ(casier, "intensite", str, ctx)
    if "objet" not in casier:
        _erreur(ctx, "champ obligatoire absent : 'objet'")
    if casier["objet"] is not None and not isinstance(casier["objet"], str):
        _erreur(ctx, "'objet' doit etre un texte ou null")
    if not (0 <= ligne < NB_INTENSITES and 0 <= colonne < NB_EMOTIONS):
        _erreur(ctx, f"casier [{ligne}, {colonne}] hors de l'armoire "
                     f"({NB_INTENSITES} lignes x {NB_EMOTIONS} colonnes)")
    if emotion != emotions[colonne] or intensite != intensites[ligne]:
        _erreur(ctx, f"l'etiquette {emotion}/{intensite} ne correspond pas a "
                     f"la position [{ligne}, {colonne}] "
                     f"({emotions[colonne]}/{intensites[ligne]} attendu)")
    return ligne, colonne
 
 
def valider_armoire(armoire, contexte="armoire"):
    _champ(armoire, "nom", str, contexte)
    emotions, intensites = _verifier_listes_emotions(armoire, contexte)
 
    depart = _position(armoire, "casier_depart", contexte)
    if not (0 <= depart[0] < NB_INTENSITES and 0 <= depart[1] < NB_EMOTIONS):
        _erreur(contexte, f"casier_depart {list(depart)} est hors de l'armoire "
                          f"({NB_INTENSITES} lignes x {NB_EMOTIONS} colonnes)")
 
    vus = set()
    for numero, casier in enumerate(_champ(armoire, "casiers", list, contexte)):
        position = _verifier_casier(casier, f"{contexte} (casier {numero})",
                                    emotions, intensites)
        if position in vus:
            _erreur(contexte, f"casier {list(position)} defini deux fois")
        vus.add(position)
 
 
# ---------------------------------------------------------------------------
# Scenario et coherences croisees
# ---------------------------------------------------------------------------
 
def valider_scenario(scenario, carte, contexte="scenario"):
    """`carte` doit deja etre validee."""
    _champ(scenario, "nom", str, contexte)
    nom_carte = _champ(scenario, "carte", str, contexte)
    nom_armoire = _champ(scenario, "armoire", str, contexte)
    if nom_carte != carte["nom"]:
        _erreur(contexte, f"scenario prevu pour la carte '{nom_carte}', "
                          f"mais la carte fournie est '{carte['nom']}'")
    if not nom_armoire or any(c in nom_armoire for c in "/\\") or ".." in nom_armoire:
        _erreur(contexte, f"nom d'armoire invalide : {nom_armoire!r}")
 
    ids = {r["id"] for r in carte["residents"]}
    numeros = set()
    for demande in _champ(scenario, "demandes", list, contexte):
        ctx = f"{contexte} (demande)"
        numero = _champ(demande, "numero", int, ctx)
        resident = _champ(demande, "resident", str, ctx)
        _champ(demande, "message", str, ctx)
        if numero in numeros:
            _erreur(ctx, f"numero de demande {numero} en double")
        numeros.add(numero)
        if resident not in ids:
            _erreur(ctx, f"la demande {numero} s'adresse a '{resident}', "
                         f"absent de la carte")
 
 
def valider_coherence(dico, armoire):
    """Armoire et dictionnaire doivent partager emotions et intensites,
    dans le meme ordre (l'ordre est celui de la roue)."""
    for champ in ("emotions", "intensites"):
        if dico[champ] != armoire[champ]:
            _erreur("armoire/dictionnaire",
                    f"'{champ}' differe entre l'armoire et le dictionnaire")
 
 
# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------
 
def valider_entrees(chemin_carte, chemin_scenario, dossier_donnees):
    """Charge ET valide les 4 fichiers. Renvoie (carte, scenario, dico, armoire)
    ou leve ErreurDonnees. N'ecrit rien."""
    carte = _charger(rio.charger_carte, chemin_carte)
    valider_carte(carte, Path(chemin_carte).name)
 
    scenario = _charger(rio.charger_scenario, chemin_scenario)
    valider_scenario(scenario, carte, Path(chemin_scenario).name)
 
    dossier = Path(dossier_donnees)
    chemin_dico = dossier / "dictionnaire.json"
    dico = _charger(rio.charger_dictionnaire, chemin_dico)
    valider_dictionnaire(dico, chemin_dico.name)
 
    chemin_armoire = dossier / f"{scenario['armoire']}.json"
    armoire = _charger(rio.charger_armoire, chemin_armoire)
    valider_armoire(armoire, chemin_armoire.name)
 
    valider_coherence(dico, armoire)
    return carte, scenario, dico, armoire
 