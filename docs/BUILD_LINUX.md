# Build Linux x64

## Prérequis

- Linux x86_64 ;
- Python 3.12 ou supérieur ;
- Node.js 22 ou supérieur ;
- Rust stable et Cargo ;
- GCC, `pkg-config`, WebKitGTK 4.1, GTK 3, JavaScriptCoreGTK 4.1 et libsoup 3.

Sur Debian ou Ubuntu, après vérification et avec l’accord de l’administrateur :

```bash
sudo apt-get update
sudo apt-get install build-essential libwebkit2gtk-4.1-dev \
  libappindicator3-dev librsvg2-dev patchelf libssl-dev \
  libgtk-3-dev libsoup-3.0-dev
```

AgentSec Inspector n’installe jamais ces paquets automatiquement.

## Préparation et contrôles

```bash
scripts/linux/check-prerequisites.sh --build
scripts/linux/install-dev.sh
scripts/linux/test-all.sh
```

## Génération des paquets

```bash
scripts/linux/build-linux.sh
```

Le script :

1. vérifie le système et les dépendances ;
2. exécute les contrôles qualité et les tests ;
3. compile le frontend ;
4. construit le backend autonome avec PyInstaller ;
5. intègre le backend comme binaire Tauri ;
6. génère une AppImage et un paquet DEB ;
7. calcule les empreintes SHA-256 ;
8. écrit `logs/build/linux-build-report.txt`.

Les artefacts se trouvent sous `src-tauri/target/release/bundle/`.

## Vérification de l’artefact

```bash
artifact="$(find src-tauri/target/release/bundle -name '*.AppImage' -print -quit)"
scripts/linux/install.sh --artifact "$artifact"
scripts/linux/verify-installation.sh
```

La vérification extrait réellement l’AppImage, trouve le backend intégré, initialise une base temporaire, teste la santé, l’authentification, la création/lecture d’un projet et les journaux structurés.
