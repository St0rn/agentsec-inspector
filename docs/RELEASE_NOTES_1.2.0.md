# AgentSec Inspector v1.2.0

Cette version refond le moteur de rapports et renforce la traçabilité des audits.

## Rapports professionnels

- Nouveau rendu HTML/PDF aux couleurs d’AgentSec Inspector, avec couverture, sommaire, indicateurs, tableaux, en-têtes, pieds de page et pagination A4.
- Rapports techniques et exécutifs en français ou en anglais, produits à partir d’un modèle de données commun aux exports HTML, PDF et JSON.
- Prévisualisation HTML sécurisée avant génération.
- Findings détaillés avec classification, statut, impact, conditions d’exploitation, étapes de reproduction, résultat attendu/observé, recommandations, référentiels, preuves et appels d’outils.
- Affichage du **Payload** exact envoyé pour les scénarios et les tests Custom Payload dans l’historique, les findings et les rapports.
- Compatibilité avec les anciennes exécutions : la requête conservée est présentée sans inventer l’enveloppe de transport absente.
- Fonction **Enregistrer sous** avec sélecteur de fichier natif lorsqu’il est disponible et repli vers le téléchargement standard.
- Noms de fichiers uniques et empreinte SHA-256 pour chaque export.

## Organisation par projet

- Targets, Findings et Reports sont regroupés par client et mission.
- Chaque groupe peut être replié ou déplié et indique son nombre d’éléments.

## Qualité et sécurité

- Échappement HTML strict des données de rapport et politique CSP restrictive pour la prévisualisation.
- Tests de non-régression sur les payloads multi-tours, les anciens audits, les preuves volumineuses, les caractères spéciaux, les données absentes et les rapports FR/EN.
- 71 tests backend et 23 tests frontend réussis avant création du tag.

## Installateurs

- `AgentSec-Inspector_1.2.0_x64_en-US.msi`
- `AgentSec-Inspector_1.2.0_x64-setup.exe`
- `AgentSec-Inspector_1.2.0_amd64.AppImage`
- `AgentSec-Inspector_1.2.0_amd64.deb`
- `SHA256SUMS.txt`

Les empreintes sont générées directement à partir des quatre artefacts validés et publiées dans `SHA256SUMS.txt`.
