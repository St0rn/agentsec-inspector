# Installation Linux

AgentSec Inspector prend en charge Linux x86_64 sous la forme d’une AppImage autonome. L’utilisateur final n’a pas besoin d’installer Python, Node.js ou Rust.

## Installation d’une AppImage publiée

Téléchargement direct : [AgentSec Inspector 1.1.0 AppImage x86_64](https://github.com/St0rn/agentsec-inspector/releases/download/v1.1.0/AgentSec-Inspector_1.1.0_amd64.AppImage). Le [paquet DEB](https://github.com/St0rn/agentsec-inspector/releases/download/v1.1.0/AgentSec-Inspector_1.1.0_amd64.deb) est publié dans la même release.

Téléchargez l’artefact `AgentSec Inspector_*.AppImage`, puis exécutez depuis la racine du dépôt :

```bash
chmod +x scripts/linux/*.sh
scripts/linux/install.sh --artifact /chemin/vers/AgentSec-Inspector.AppImage
scripts/linux/verify-installation.sh
```

L’installation utilisateur place :

- l’AppImage dans `~/.local/lib/agentsec-inspector/` ;
- la commande `agentsec-inspector` dans `~/.local/bin/` ;
- l’entrée de menu dans `~/.local/share/applications/`.

Ajoutez `~/.local/bin` au `PATH` si votre distribution ne le fait pas déjà.

## Lancement

```bash
agentsec-inspector
```

ou :

```bash
scripts/linux/start-production.sh
```

## Mise à jour

La mise à jour crée d’abord une sauvegarde des données, installe le nouvel artefact, vérifie son intégrité et restaure l’ancienne application si la vérification échoue :

```bash
scripts/linux/update.sh /chemin/vers/nouvelle-version.AppImage 1.1.0
```

## Sauvegarde et restauration

```bash
scripts/linux/backup.sh /chemin/vers/agentsec-backup.tar.gz
scripts/linux/restore.sh /chemin/vers/agentsec-backup.tar.gz --yes
```

La restauration vérifie l’empreinte éventuelle, bloque les chemins d’archive dangereux, contrôle l’intégrité SQLite et conserve les anciennes données dans un répertoire horodaté.

## Désinstallation

Par défaut, les projets, preuves et rapports sont conservés :

```bash
scripts/linux/uninstall.sh
```

La suppression des données exige deux options explicites :

```bash
scripts/linux/uninstall.sh --delete-data --yes
```

## Limites de validation

Les scripts de développement, de base de données et de tests ont été exécutés sous Linux dans l’environnement de développement. La génération AppImage/DEB exige WebKitGTK et les bibliothèques Tauri ; elle est validée par `.github/workflows/linux-build.yml` sur Ubuntu lorsqu’un run est disponible.
