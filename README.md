# Robot de réconfort - CAMARA Zéïnab Aly & HAJEE Neha

**Projet 1 de POA/SMA :** Un robot à **perception locale**
reçoit des messages de résidents, consulte un dictionnaire pour lire
l'émotion, fouille une armoire pour choisir un objet, puis le rapporte au
bon résident. Il ne connaît ni les murs ni le contenu de l'armoire à
l'avance : il les découvre en marchant.

Langage : Python 3 (3.9 ou plus) - Aucune dépendance externe.

## Lancer

Depuis le dossier `base_fournie` :

```
python agent/agent.py <carte.json> <scenario.json> <dossier_donnees> <trace_sortie.json>
```

Exemple :

```
python agent/agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie.json
```

Le dossier de données contient `dictionnaire.json` et les fichiers d'armoire ;
le scénario désigne l'armoire à charger (`"armoire": "armoire_standard"`).
Aucun chemin n'est codé en dur : tout vient des quatre arguments.

**Codes de retour** : `0` succès · `1` fichier d'entrée absent ou invalide
(message sur la sortie d'erreur, **aucune trace écrite**) · `2` mauvais
nombre d'arguments (message d'usage).

**Voir le robot marcher** (débogage et vidéo), à partir d'une trace déjà produite :

```
python affichage.py cartes/appartement_01.json sortie.json 0.1
```

Il affiche la **carte mentale** du robot pas à pas (`?` inconnu, `#` mur
découvert, `@` robot), ce qui montre bien la replanification. Le dernier
argument `0.1` est la pause en secondes entre deux pas. `affichage.py` ne fait pas
partie de l'agent : il ne lit pas la grille et reconstruit la mémoire à
partir des perceptions enregistrées dans la trace.

## Tester

```
python -m unittest discover -s tests -v
```

149 tests, sans dépendance. Ils couvrent les sept familles de l'énoncé :
chemin de longueur connue (annexe B.3), replanification après un mur,
lecture du dictionnaire (premier mot gagnant, aucun mot reconnu), sélecteur
de l'armoire (bouclage colonne 7 → 0), règle de repli, validation des
fichiers (un fichier cassé par catégorie de 5.6), résident muré. Les tests
d'intégration utilisent le **vrai** `Robot` et le **vrai** `Environnement` :
une action illégale lèverait une erreur, donc un test qui passe prouve aussi
que toutes les actions de la trace étaient légales.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `agent/agent.py` | point d'entrée : 4 arguments → valider → simuler → écrire la trace |
| `agent/validation.py` | contrôle du **contenu** des 4 fichiers (énoncé 5.6) avant tout lancement |
| `agent/reconfort_io.py` | fourni : lecture des fichiers (en-tête) et écriture de la trace |
| `agent/environnement.py` | le simulateur : **seul** à lire `grille` et le champ `objet` des casiers |
| `agent/robot.py` | `CarteMentale` (mémoire) ; `Robot` : perception, actions, journalisation |
| `agent/deplacement.py` | planification : BFS sur la carte mentale, `rejoindre` avec replanification |
| `agent/armoire.py` | roue de Plutchik, 15 candidats triés (6.2), trajet du sélecteur, fouille |
| `agent/traitement_messages.py` | normalisation du message, premier mot reconnu (6.1) |
| `agent/decision.py` | enchaîne une demande : dictionnaire → armoire → résident → `PRENDRE` → `DONNER` |
| `affichage.py` | rejoue une trace à l'écran (hors agent) |
| `cartes_test/`, `donnees_test/` | nos propres cartes, voir plus bas |
| `tests/` | tests unitaires et d'intégration |
| `rapport/rapport.tex` | rapport de 3 pages |

**Séparation perception / mémoire / décision / action.** Le robot ne reçoit
jamais la grille : `agent.py` lui passe la carte *sans* le champ `grille`, et
il ne peut qu'interroger l'`Environnement`. La décision n'agit pas
directement : elle appelle les méthodes du `Robot`, qui vérifient la légalité
de chaque action et la journalisent. Détails dans le rapport.

## Nos cartes de test

Dans `cartes_test/` (avec `donnees_test/`) :

| Carte | Ce qu'elle teste |
|---|---|
| `test_grand` | appartement 24 × 40, 4 résidents, 6 demandes |
| `test_impasse` | cul-de-sac : coût de l'hypothèse optimiste |
| `test_mure` | résident enfermé dans une pièce close, demandé deux fois |
| `test_dico_inaccessible` | dictionnaire muré |
| `scenario_colonne_vide` (+ `armoire_tristesse_vide`) | colonne entière vide : repli sur une voisine |

Exemple :

```
python agent/agent.py cartes_test/test_mure.json cartes_test/scenario_mure.json donnees_test sortie.json
```

## Choix de conception (là où l'énoncé ne dit rien)

- **Résident vérifié avant `PRENDRE`.** Le robot ne peut rien poser : s'il
  prenait l'objet puis découvrait le résident muré, il le garderait pour
  toujours et ses `PRENDRE` suivants seraient illégaux. Il marche donc
  d'abord vers le résident (avec sa perception et sa mémoire, **jamais la
  grille**), puis revient prendre l'objet. Si le résident est inaccessible :
  `succes = false`, motif `resident inaccessible`, rien n'a été pris, il passe
  à la demande suivante. Prix : plus de
  pas (`scenario_01` : 160 → 260). Voir l'échec 1 du rapport.
- **Deux motifs d'échec ajoutés** : `dictionnaire inaccessible` et
  `armoire inaccessible`, pour terminer proprement si l'un d'eux est muré.
  L'énoncé n'en prévoit que trois (`emotion indeterminee`, `armoire vide`,
  `resident inaccessible`). Ce choix est de notre initiative.
- **Après un échec, le robot reste où il est** et traite la demande suivante ;
  il ne retourne pas à sa case de départ (6.3). Sa mémoire est conservée
  d'une demande à l'autre.
- **Carte mentale** : une case jamais vue est supposée libre (annexe B.5) ; si
  le BFS (Breadth-First Search) échoue sur cette carte, aucun chemin réel n'existe (B.6).
- **Fouille de l'armoire** : un casier garni croisé en chemin n'est pris que
  si c'est son tour dans la liste triée ; un casier vide déjà vu n'est pas
  revérifié.
- **Validation** : `validation.py` lève une seule exception métier
  (`ErreurDonnees`), attrapée par `agent.py`. Elle vérifie aussi la cohérence
  croisée armoire / dictionnaire (mêmes émotions et intensités, même ordre) et
  que le fichier d'armoire nommé par le scénario existe.

## État

**Ce qui marche.**
Les cinq appartements fournis et nos cinq cartes de test se terminent sans
erreur, sans action illégale, avec les livraisons attendues. Les 149 tests
passent. Les fichiers invalides produisent un message sur `stderr`, un code
non nul et aucune trace. La replanification et la preuve d'inaccessibilité
fonctionnent sans jamais lire la grille.

**Ce qui ne marche pas, ou pas bien.**
- **Trajets non optimaux.** L'hypothèse optimiste fait entrer le robot dans
  des culs-de-sac (`test_impasse` : 68 `AVANCER` contre 40 pour un robot qui
  connaîtrait la carte). C'est le prix de la garantie B.6.
- **Un résident muré déjà identifié coûte encore des pas.** Le robot va
  d'abord au dictionnaire et à l'armoire avant de tester le résident
  (`test_mure`, demande 3 : 53 pas pour un échec déjà prouvé). Nous avons
  mesuré une variante qui teste le résident avant l'armoire (299 → 131 pas),
  décrite dans le rapport mais **non intégrée** à ce stade.
- **Lecture du message rudimentaire** (règle 6.1) : « Je ne suis pas triste »
  donne *tristesse*, la négation n'est pas analysée.
- **Règle de repli** : elle suit la distance sur la roue de Plutchik, qui ne
  mesure pas la compatibilité de réconfort d'un objet (voir la critique dans le
  rapport).
- Stock d'objets illimité (projet 1) : `PRENDRE` ne vide pas le casier.

## Vidéo

`demo.mp4`, également déclarée dans `rendu.json`.