# HuisClos: installation et démarrage / installation and launch

## Français

Ce kit contient le code source de l'application réunissant les pistes A et B, les lanceurs
Windows et macOS, les dépendances épinglées et la documentation. Git n'est pas nécessaire.
Ce n'est pas un exécutable autonome : Python doit être installé une fois au préalable.

### Avant de commencer

- Installer **Python 3.12, 64 bits** depuis [python.org](https://www.python.org/downloads/).
  Sur Windows, activer le lanceur Python et l'option **Add python.exe to PATH**.
  Sur macOS, utiliser l'installateur Python 3.12 adapté au Mac ; ne pas utiliser le Python
  système. Si Python fournit `Install Certificates.command`, l'exécuter après l'installation.
- Prévoir Internet pour les téléchargements initiaux, un navigateur et un dossier où vous
  pouvez écrire. Aucun compte IA, aucune clé API ni GPU n'est nécessaire pour Standard.
- Prévoir plusieurs Go libres pour Python et les dépendances. Enhanced télécharge en plus
  des poids volumineux ; prévoir plusieurs Go supplémentaires. Les sondes Windows historiques
  ont observé environ 0,7 Go de mémoire pour Standard FR et 2,8 Go pour Enhanced EN.
  Ce sont des observations, pas des minima matériels garantis.

### Windows

1. Extraire **tout le ZIP** dans un dossier personnel, par exemple `Documents\HuisClos`.
   Ne pas lancer l'application depuis l'aperçu du ZIP.
2. Double-cliquer sur **Start-HuisClos-Windows.bat**.
3. Au premier lancement, choisir les modèles : **1** Standard FR/EN (défaut), **2** Standard
   avec Enhanced français, ou **3** avec Enhanced français et anglais.
4. Attendre la fin de l'installation. Le navigateur s'ouvre sur `http://127.0.0.1:8501`.
   Garder la fenêtre de commande ouverte. `Ctrl+C` arrête l'application.

Les lancements suivants utilisent le même fichier `.bat` et ne réinstallent pas les paquets
si l'installation est complète. En cas d'avertissement Windows, vérifier la provenance du
kit auprès de la personne qui vous l'a transmis ; les scripts ne sont pas signés.

### macOS

1. Extraire tout le ZIP dans un dossier personnel.
2. Double-cliquer sur **Start-HuisClos-macOS.command**, puis choisir **1**, **2** ou **3**.
3. Attendre l'installation et l'ouverture du navigateur. Garder Terminal ouvert ; `Ctrl+C`
   arrête l'application.

Si le double-clic ne fonctionne pas, ouvrir Terminal, taper `cd `, glisser le dossier du kit
dans la fenêtre, puis appuyer sur Entrée. Exécuter :

```bash
bash ./Start-HuisClos-macOS.command
```

Le kit préserve le droit d'exécution du fichier `.command`. Si votre outil d'extraction le
perd, la commande ci-dessus fonctionne sans changer les réglages de sécurité de macOS.
Le lanceur macOS est fourni ; son installation complète sur un vrai Mac reste à vérifier.
Les paquets doivent proposer des versions compatibles avec votre macOS et votre processeur.

### Choix des modèles

| Choix | Installation | Utilisation |
| --- | --- | --- |
| 1 | Standard FR/EN, règles et spaCy | Défaut de l'application ; anglais expérimental avec réserves fortes. |
| 2 | Standard + CamemBERT français | Permet de choisir Enhanced dans la barre latérale pour un document français. |
| 3 | Standard + CamemBERT FR + GLiNER EN | Enhanced anglais expérimental et non recommandé, perte de précision observée. |

Enhanced est facultatif. Installer ses modèles ne l'active pas automatiquement : choisir
ensuite **Enhanced local detection** dans la barre latérale. Les poids sont téléchargés
depuis Hugging Face à des révisions figées, contrôlés par empreinte, puis testés hors ligne.
Ils ne sont pas inclus dans le ZIP. PyTorch est installé en version CPU sur Windows et en
version native sur macOS ; le verrou historique Enhanced Windows n'est pas appliqué au Mac.

Pour ajouter Enhanced plus tard, ouvrir une console dans le dossier et exécuter :

```powershell
.\Start-HuisClos-Windows.bat --models enhanced-fr
```

```bash
bash ./Start-HuisClos-macOS.command --models enhanced-fr
```

Remplacer `enhanced-fr` par `enhanced` pour FR et EN, ou `standard` pour revenir au choix
Standard. Ce dernier choix ne supprime pas les paquets ou poids déjà installés.

### Vérifications et dépannage

- **Python introuvable** : installer Python 3.12 64 bits, puis rouvrir le lanceur.
- **Téléchargement interrompu** : vérifier Internet et relancer le même fichier. Le reçu de
  réussite n'est écrit qu'après les vérifications. Pour reprendre les étapes d'installation
  après un échec Enhanced, ajouter `--models enhanced-fr --repair` (ou `enhanced`).
- **Enhanced échoue** : relancer avec `--models standard` pour utiliser le socle installé.
- **Pas de navigateur** : ouvrir `http://127.0.0.1:8501` manuellement.
- **Port déjà utilisé** : arrêter l'autre instance ou ajouter `--port 8502` au lanceur.
- **Vérifier sans installer ni lancer** : ajouter `--check` au lanceur. Cette commande vérifie
  les paquets et charge les modèles du choix enregistré, sans téléchargement.
- **Environnement incomplet ou dossier déplacé** : fermer l'application, renommer le dossier
  `.venv-toolkit` en `.venv-toolkit-old`, puis relancer pour recréer une installation locale.
  Les environnements Python ne sont pas portables d'un ordinateur à l'autre.
- **Réseau d'entreprise** : demander à votre service informatique l'accès aux dépôts de
  paquets Python, GitHub et, pour Enhanced, PyTorch et Hugging Face. Le kit ne modifie pas
  les certificats ni les politiques de votre poste.

### Confidentialité, contenu et partage

Après installation, le traitement s'effectue localement ; le serveur écoute seulement sur
`127.0.0.1`. Le connecteur Mistral reste facultatif et exige une configuration et une action
explicites. Le kit ne contient aucune clé API. La pseudonymisation n'est pas une anonymisation :
relire le document, les détections et le message sortant, et ajouter les valeurs manquées.
Ne jamais envoyer la table de correspondance à un outil d'IA.

Partager le **ZIP d'origine**, pas votre dossier de travail après utilisation. Ce ZIP ne
contient ni environnement Python, ni clé, ni table de correspondance, ni corpus d'évaluation
réservé. Les sources applicatives sont dans `src/`, `app/` et `streamlit_app.py`, les outils
dans `scripts/`, les tests dans `tests/` et les guides dans `docs/`. Les tests qui exigent
les corpus ou preuves de gate omis doivent être exécutés depuis le dépôt de développement.
Les rapports publics inclus sont historiques ; ils ne sont pas recalculés à l'installation.
Voir `README.md`, `docs/USER_GUIDE.md`, `docs/LOCAL_MODELS.md` et `LICENSE`.

`TOOLKIT_MANIFEST.json` indique le commit source et les empreintes des fichiers distribués.
Le fichier `.zip.sha256` livré à côté du ZIP permet de vérifier un transfert ; ce n'est pas
une signature d'éditeur. Pour reconstruire le ZIP depuis le dépôt Git avec Python 3.12 :
`python scripts/build_toolkit.py`. Seuls les fichiers autorisés du commit HEAD sont inclus.

## English

Install **Python 3.12, 64-bit**, from [python.org](https://www.python.org/downloads/) first.
On Windows, enable the Python launcher and **Add python.exe to PATH**. On macOS, use the
Python 3.12 installer for your Mac and run its certificate installer if supplied.

1. Extract the entire ZIP to a writable personal folder. Git is unnecessary.
2. Double-click **Start-HuisClos-Windows.bat** or **Start-HuisClos-macOS.command**.
   On Mac, `bash ./Start-HuisClos-macOS.command` in Terminal is the fallback.
3. Choose **1** Standard FR/EN, **2** Standard plus French Enhanced (CamemBERT), or **3**
   Standard plus French/English Enhanced (CamemBERT and GLiNER). English is experimental;
   English Enhanced is not recommended. Standard remains the application default.
4. Keep Internet connected during the first installation. Enhanced needs additional large
   downloads and several GB of free disk space. No AI account or GPU is required for Standard.
5. The app opens at `http://127.0.0.1:8501`. Keep the terminal open; press Ctrl+C to stop.
   Later launches reuse the local installation without dependency downloads.

Launcher options: `--models standard`, `--models enhanced-fr`, `--models enhanced`,
`--install-only`, `--repair`, `--check` (offline diagnostic), and `--port 8502`.
If an Enhanced installation fails, use `--models standard`, or retry Enhanced with `--repair`.
If the kit moves to another location or computer, rename `.venv-toolkit` and install again.
macOS scripts are supplied, but a full installation on physical macOS hardware remains untested.

Review every detection and the exact outgoing message. Pseudonymization is not anonymization.
Never send the sensitive mapping table to an AI tool. Share the original ZIP, not your working
folder. The archive includes application source, tools, test code, documentation, public
historical reports and licences, excluding secrets, reserved corpora, local environments and
neural model weights. Optional model licences are detailed in `docs/LOCAL_MODELS.md`.
