import reconfort_io as rio
from traitement_messages import reception_message, trouver_emotion
from pathlib import Path

BASE = Path(__file__).parent.parent 

carte = rio.charger_carte(BASE /"cartes"/"appartement_01.json")
scenario = rio.charger_scenario(BASE/"cartes"/"scenario_01.json")
dico = rio.charger_dictionnaire(BASE / "donnees" / "dictionnaire.json")

for demande in scenario["demandes"]: 
    numero, id_resident, position, mots = reception_message(demande["numero"],
                       demande["message"], 
                       demande["resident"], 
                       carte['residents'])
    print(numero, id_resident, position, trouver_emotion(mots, dico))

print(reception_message(100, "bonjour", "R2", carte["residents"]))
#reception_message(99, "bonjour", "R9", carte["residents"]) cas d erreur car R9 fait pas parti de la liste des résidents

#pour la partie automatisation des tests: 
#assertEqual vérifie que la position renvoyée pour R1 vaut bien [6, 11] ;
#assertRaises vérifie que R9 provoque bien une ValueError.

#exemple de 6.1 ou sidere gagne contre seule 
mots = rio.normaliser("Je suis sidéré, la télévision s'est allumée toute seule.")
print(trouver_emotion(mots,dico))

#test pour le cas ou il y a aucun mot reconnu
print(trouver_emotion(["bonjour","merci"],dico))