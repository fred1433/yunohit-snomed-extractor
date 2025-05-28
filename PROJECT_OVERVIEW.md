# Documentation Complète du Projet d'Extraction SNOMED CT

## 1. Introduction et Objectif

Ce projet vise à extraire des informations médicales structurées à partir de notes médicales textuelles. Plus précisément, il identifie et code les termes médicaux selon trois hiérarchies principales de la terminologie SNOMED CT :
*   **Constatation clinique (Clinical Finding)**
*   **Intervention (Procedure)**
*   **Structure corporelle (Body Structure)**

De plus, le système est capable d'identifier des **modifieurs contextuels** associés à ces termes, tels que :
*   Négation (Absence de la constatation/intervention)
*   Famille (Concerne un membre de la famille du patient)
*   Suspicion (Le diagnostic ou l'observation est suspecté mais non confirmé)
*   Antécédent (Concerne un historique médical passé)

L'objectif final est de fournir une sortie structurée (objets Python et potentiellement JSON) des concepts SNOMED CT extraits, enrichis de leurs codes et modifieurs contextuels, pour faciliter l'analyse et l'exploitation des données médicales.

## 2. Fonctionnalités Clés

*   Extraction de concepts SNOMED CT à partir de texte libre.
*   Identification des hiérarchies : Constatation clinique, Intervention, Structure corporelle.
*   Extraction des codes SNOMED CT correspondants (fournis par l'IA générative).
*   Identification des modifieurs contextuels : négation, famille, suspicion, antécédent.
*   Utilisation de l'API Google Gemini (modèle `gemini-1.5-pro-latest`) pour le traitement du langage naturel.
*   Structure de données claire utilisant Pydantic pour la validation et la sérialisation.
*   Configuration flexible via un fichier `.env`.
*   Affichage des résultats enrichi dans le terminal.

## 3. Pile Technologique

*   **Langage** : Python 3.x
*   **Traitement du Langage Naturel** : API Google Gemini (`google-generativeai`)
*   **Modélisation de données** : Pydantic (`pydantic`, `dataclasses-json`)
*   **Gestion des dépendances** : `pip` et `requirements.txt`
*   **Gestion de la configuration** : `python-dotenv`
*   **Affichage console amélioré** : `rich`

## 4. Structure du Projet

Le projet est organisé comme suit :

```
.
├── .env                  # Fichier de configuration (non versionné) pour les clés API
├── .git/                 # Répertoire Git
├── .gitignore            # Fichier spécifiant les fichiers ignorés par Git
├── PROJECT_OVERVIEW.md   # Ce document
├── README.md             # Instructions de base et présentation du projet
├── config.py             # Gestion de la configuration (chargement de la clé API, nom du modèle)
├── main.py               # Point d'entrée principal du script, exécute l'extraction et affiche les résultats
├── models.py             # Définition des dataclasses Pydantic pour structurer les données extraites
├── requirements.txt      # Liste des dépendances Python du projet
└── snomed_extractor.py   # Contient la logique principale d'extraction SNOMED CT via l'API Gemini
```

**Description des fichiers clés :**

*   **`main.py`**:
    *   Orchestre le processus d'extraction.
    *   Utilise une note médicale d'exemple (modifiable).
    *   Initialise `SnomedExtractor`.
    *   Appelle la méthode d'extraction.
    *   Affiche les résultats de manière formatée dans la console.

*   **`snomed_extractor.py`**:
    *   Contient la classe `SnomedExtractor`.
    *   Gère l'interaction avec l'API Google Gemini.
    *   Construit le prompt spécifique envoyé à Gemini pour l'extraction.
    *   Parse la réponse de Gemini pour la transformer en objets `SNOMEDExtraction` (définis dans `models.py`).
    *   Implémente la stratégie d'extraction "ONE-SHOT" (une seule requête à l'API pour tout extraire).

*   **`models.py`**:
    *   Définit les structures de données utilisées pour représenter les informations médicales extraites :
        *   `ClinicalFinding`
        *   `Procedure`
        *   `BodyStructure`
        *   `MedicalNote` (regroupe les listes des trois types d'entités ci-dessus)
        *   `SNOMEDExtraction` (contient l'objet `MedicalNote` et la note brute d'origine)
    *   Utilise `Pydantic` pour la validation des données et `dataclasses-json` pour faciliter la sérialisation/désérialisation (bien que la sérialisation JSON explicite ait été mise de côté pour l'instant).
    *   Les modifieurs contextuels (`negated`, `family_history`, `suspected`, `past_history`) sont des champs booléens dans chaque entité.

*   **`config.py`**:
    *   Charge la clé API Google à partir du fichier `.env`.
    *   Définit le nom du modèle Gemini à utiliser (`gemini-1.5-pro-latest`).

*   **`requirements.txt`**:
    *   Liste toutes les bibliothèques Python nécessaires pour exécuter le projet.

*   **`README.md`**:
    *   Fournit un aperçu rapide du projet et des instructions d'installation et d'exécution de base.

*   **`.env` (exemple)**:
    ```
    GOOGLE_API_KEY="VOTRE_CLE_API_GOOGLE_ICI"
    ```

## 5. Instructions de Configuration et d'Installation

1.  **Cloner le dépôt (si ce n'est pas déjà fait)**:
    Si le projet est versionné avec Git :
    ```bash
    git clone <url_du_depot>
    cd <nom_du_repertoire_du_projet>
    ```

2.  **Créer et activer un environnement virtuel** (recommandé):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Sur macOS/Linux
    # venv\Scripts\activate   # Sur Windows
    ```

3.  **Installer les dépendances**:
    Assurez-vous que `pip` est à jour, puis installez les paquets listés dans `requirements.txt`:
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  **Configurer la clé API Google**:
    *   Créez un fichier nommé `.env` à la racine du projet.
    *   Ajoutez votre clé API Google Gemini dans ce fichier :
        ```
        GOOGLE_API_KEY="VOTRE_CLE_API_GOOGLE_ICI"
        ```
    *   Assurez-vous que ce fichier est bien listé dans `.gitignore` pour ne pas le versionner.

## 6. Comment Exécuter le Projet

Une fois l'installation et la configuration terminées, vous pouvez exécuter le script principal :

```bash
python main.py
```

Le script va :
1.  Charger la note médicale d'exemple définie dans `main.py`.
2.  Initialiser le `SnomedExtractor`.
3.  Envoyer la note et un prompt spécifique à l'API Gemini.
4.  Recevoir et parser la réponse.
5.  Afficher les entités SNOMED CT extraites (Constatations cliniques, Interventions, Structures corporelles) avec leurs codes, termes et modifieurs contextuels dans le terminal.

**Exemple de sortie attendue (structure) :**

```
Note Médicale Originale:
------------------------
Le patient, M. Jean Dupont, ... (texte complet de la note) ...

Résultats de l'Extraction SNOMED CT:
------------------------------------

🔬 Constatations Cliniques:
  - Terme: Diabète sucré de type 2
    Code SNOMED CT: 44054006
    Modifieurs:  अतीत (Antécédent)
  - Terme: Hypertension artérielle
    Code SNOMED CT: 38341003
    Modifieurs:  अतीत (Antécédent)
  - Terme: Douleur thoracique
    Code SNOMED CT: 29857009
    Modifieurs: ❓ (Suspicion)
  - Terme: Grippe
    Code SNOMED CT: 6142004
    Modifieurs: ❌ (Négation)

🛠️ Interventions:
  - Terme: Appendicectomie
    Code SNOMED CT: 80146002
    Modifieurs:  अतीत (Antécédent)
  - Terme: Administration d'insuline
    Code SNOMED CT: 428653004
    Modifieurs: Aucun

 Anatomiques:
  - Terme: Poumon
    Code SNOMED CT: 39607008
    Modifieurs: Aucun
  - Terme: Appendice
    Code SNOMED CT: 65481003
    Modifieurs: Aucun
```

## 7. Logique d'Extraction SNOMED CT (Approche "ONE-SHOT")

L'extraction des informations SNOMED CT repose sur une interaction unique (ONE-SHOT) avec le modèle Google Gemini.

*   **Préparation du Prompt**:
    Un prompt détaillé et structuré est construit dans `SnomedExtractor`. Ce prompt :
    *   Décrit la tâche : extraire des entités médicales et leurs codes SNOMED CT.
    *   Spécifie les hiérarchies SNOMED CT cibles.
    *   Demande l'identification des modifieurs contextuels (négation, famille, suspicion, antécédent).
    *   Fournit un exemple du format de sortie attendu (JSON parsable) pour guider le modèle. Il est crucial que ce format soit cohérent avec les modèles Pydantic définis dans `models.py`.
    *   Inclut la note médicale à analyser.

*   **Interaction avec Gemini**:
    *   Le modèle `gemini-1.5-pro-latest` est utilisé (configuré dans `config.py`).
    *   **Point crucial** : Aucune `generation_config` (comme `temperature`, `top_p`, `top_k`) n'est spécifiée lors de l'appel à l'API pour cette tâche d'extraction. Il a été observé que la présence de ces paramètres pouvait rendre le modèle (notamment `gemini-2.5-pro-preview-05-06`) trop restrictif et bloquer les réponses pour des raisons de sécurité, même avec des prompts "éducatifs". En omettant `generation_config`, le modèle semble plus apte à traiter les demandes médicales sans blocage excessif.

*   **Parsing de la Réponse**:
    *   Gemini est instruit de répondre dans un format JSON.
    *   La réponse textuelle de Gemini (qui est une chaîne JSON) est parsée en utilisant `json.loads()`.
    *   Les données parsées sont ensuite utilisées pour instancier les objets Pydantic (`ClinicalFinding`, `Procedure`, `BodyStructure`) qui sont regroupés dans un objet `MedicalNote`, lui-même contenu dans `SNOMEDExtraction`.

## 8. Évolution du Projet et Décisions Clés

Le développement du projet a suivi plusieurs étapes itératives :

1.  **Choix Initial du Modèle et Premiers Tests**:
    *   Commencé avec `gemini-1.5-pro-preview-0514`, puis `gemini-1.5-pro-latest`.
    *   Une tentative avec `gemini-2.5-pro-preview-05-06` a initialement échoué en raison de blocages de sécurité stricts.

2.  **Stratégies de Prompting et Fallbacks (Abandonnées)**:
    *   Face aux blocages, des prompts plus "éducatifs" ont été testés.
    *   Des mécanismes de fallback complexes avaient été envisagés et partiellement implémentés :
        *   Fallback vers un prompt simplifié.
        *   Stratégie "TWO-SHOT" : une requête pour extraire les termes, une autre pour obtenir les codes SNOMED CT.
        *   Fallback vers une extraction manuelle avec des codes SNOMED CT hard-codés pour la note d'exemple.
    *   Ces fallbacks ont été **supprimés** par la suite pour simplifier le code, car la solution sans `generation_config` s'est avérée efficace.

3.  **Découverte de l'Impact de `generation_config`**:
    *   Des tests ont révélé que la `generation_config` (avec `temperature`, `top_p`, `top_k`) rendait les modèles plus stricts.
    *   La suppression de cette configuration pour les appels d'extraction médicale a permis au prompt "éducatif" de fonctionner directement avec `gemini-1.5-pro-latest` (et potentiellement d'autres versions) pour retourner les termes et les codes SNOMED CT.

4.  **Ajout des Modifieurs Contextuels**:
    *   Les exigences ont évolué pour inclure l'extraction de modifieurs (négation, famille, suspicion, antécédent).
    *   Les modèles Pydantic (`models.py`) et le prompt (`snomed_extractor.py`) ont été adaptés en conséquence.

5.  **Simplification et Approche "ONE-SHOT" Finale**:
    *   La logique a été grandement simplifiée pour ne conserver qu'une méthode d'extraction "ONE-SHOT" utilisant un prompt "éducatif" et un appel à Gemini sans `generation_config` spécifique.

6.  **Validation des Codes SNOMED CT (Point d'Attention)**:
    *   Actuellement, les codes SNOMED CT sont ceux fournis par Gemini. Leur validité et leur adéquation par rapport à une version spécifique de la terminologie SNOMED CT (par exemple, la version française RF2) **ne sont pas vérifiées activement** par le programme.
    *   Une discussion a eu lieu sur la manière de valider ces codes, mentionnant l'utilisation potentielle de fichiers de terminologie SNOMED CT (format RF2) ou d'une API de terminologie comme Snowstorm. **Ceci reste un développement futur important.**

## 9. Pour la Suite / Points d'Attention pour la Reprise

*   **Validation des Codes SNOMED CT**:
    *   **Priorité haute**. Implémenter un mécanisme pour valider les codes SNOMED CT extraits par Gemini.
    *   Explorer l'intégration avec des fichiers RF2 de la terminologie SNOMED CT française ou une API comme Snowstorm.
    *   Définir comment gérer les codes non valides ou les termes pour lesquels Gemini ne fournit pas de code.

*   **Affinement du Prompt**:
    *   Bien que le prompt actuel fonctionne, des tests avec une plus grande variété de notes médicales pourraient révéler des besoins d'ajustement pour améliorer la précision et la couverture de l'extraction.
    *   Considérer l'ajout d'exemples "few-shot" plus variés dans le prompt si nécessaire.

*   **Gestion des Erreurs et Robustesse**:
    *   Améliorer la gestion des erreurs lors de l'appel à l'API Gemini (ex: erreurs réseau, quotas dépassés).
    *   Renforcer le parsing de la réponse JSON de Gemini pour gérer les cas où le format ne serait pas exactement celui attendu (bien que Pydantic offre déjà une bonne validation).

*   **Tests Unitaires et d'Intégration**:
    *   Mettre en place une suite de tests pour valider le comportement de `SnomedExtractor` et des modèles de données, surtout si des modifications sont apportées au prompt ou à la logique de parsing.

*   **Interface Utilisateur / Intégration**:
    *   Actuellement, le projet est un script en ligne de commande. Selon les besoins, une interface utilisateur (web, de bureau) ou une API pourrait être développée.

*   **Évaluation de la Performance**:
    *   Si le volume de notes à traiter devient important, évaluer la performance (temps de réponse de l'API, consommation de ressources).

*   **Confidentialité et Sécurité des Données**:
    *   Si le système doit traiter de vraies notes médicales, s'assurer de la conformité avec les réglementations sur la protection des données de santé (ex: HDS en France, HIPAA aux États-Unis). L'utilisation d'une API externe comme Gemini pour des données sensibles nécessite une attention particulière.

Ce document devrait fournir une base solide pour comprendre et reprendre le projet. N'hésitez pas si d'autres clarifications sont nécessaires. 