import reconfort_io as rio
from traitement_messages import reception_message
from pathlib import Path

BASE = Path(__file__).parent.parent 

carte = rio.charger_carte(BASE /"cartes"/"appartement_01.json")
scenario = rio.charger_scenario(BASE/"cartes"/"scenario_01.json")

for demande in scenario["demandes"]: 
    print(reception_message(demande["numero"],demande["message"],demande["resident"],carte["residents"]))


print(reception_message(100, "bonjour", "R2", carte["residents"]))
reception_message(99, "bonjour", "R9", carte["residents"])

#pour la partie automatisation des tests: 
#assertEqual vérifie que la position renvoyée pour R1 vaut bien [6, 11] ;
#assertRaises vérifie que R9 provoque bien une ValueError.