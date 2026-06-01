[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · **Français** · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Analyse du code et recommandations évaluées : BgRemover

## Échelle d'évaluation

| Symbole | Priorité | Signification |
|---------|----------|---------------|
| 🔴 | Critique | À corriger impérativement : provoque erreurs, plantages ou incohérences |
| 🟠 | Haute | À corriger rapidement : nuit fortement à la fiabilité ou à la maintenabilité |
| 🟡 | Moyenne | Recommandé : améliore la qualité du code, la lisibilité ou les tests |
| 🟢 | Basse | Optionnel : polissage et améliorations complémentaires |

---

## État actuel (2026, revue « admiring-mayer »)

Revue d'une liste de recommandations soumise en externe (15 constats) face au code réel. Résultat : **14 confirmés, 1 faux positif** (#4). Les constats confirmés sont regroupés ci-dessous en **six paquets d'implémentation** ; l'ordre des paquets est aussi l'ordre de travail recommandé. Chaque entrée conserve le constat d'origine, la preuve (`fichier:ligne`) et l'orientation du correctif ; le tableau suivant fait foi pour l'état actuel. La numérotation (#1–#15) correspond à la liste de revue d'origine.

Constats historiques et journaux de travail complets (séries 1–5) : [../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md).

### État d'avancement (vérifié le 2026-06-01)

| Statut | Points |
|--------|--------|
| ✅ Terminé | #1, #2, #3, #5, #6, #7, #8, #10, #11, #13, #14, #15 |
| ⬜ Ouvert | #12 |
| ➖ Abandonné | #4 – faux positif |

---

## Paquets de recommandations

**Paquet 1 — À faire immédiatement** 🔴

- **#1 L'annulation de l'IA doit terminer le thread.** `AIWorker._work` (`bgremover/workers.py:74`) retourne à l'annulation sans émettre de signal ; `quit_on=(finished, error)` (`bgremover/worker_controller.py:152`) ne se déclenche alors jamais → le QThread continue de tourner, `ai_thread`/`ai_worker` restent définis et le bouton IA reste désactivé pour le reste de la session (déclencheur : « charger une image pendant que l'IA calcule »). Correctif : émettre un signal `done` sans paramètre dans le bloc `finally` (`_always_finished`) et l'ajouter à `quit_on` ; l'infrastructure existe déjà (worker de warmup). **Implémenté dans cette PR, avec un test du cycle d'annulation.**

**Paquet 2 — Gains rapides et sûrs (terminé)** 🟠 🟡

- **#2 Réinitialiser l'état transitoire du canvas de façon centrale.** `apply_loaded_image` (`canvas.py:234`) appelle `cancel_overlay_only()` sans `cropModeChanged(False)` et n'annule pas le lasso → la séquence du signal de recadrage reste `[True]`, d'anciens points de lasso survivent. Introduire une méthode `_reset_transient_state()`.
- **#11 Configurer le logging indépendamment des handlers tiers.** `logging.basicConfig()` (`logging_config.py:61`) est un no-op dès que le logger racine a déjà des handlers → le chemin de log affiché ≠ celui réellement écrit. Configurer explicitement le logger nommé `BgRemover` (plus propre que `force=True`).
- **#10 Pointer le script de diagnostic vers le chemin de log actuel.** `diagnose_mac.sh:178` lit encore `~/.bgremover.log` ; le logger écrit en réalité dans `~/Library/Application Support/BgRemover/bgremover.log` (QStandardPaths). Aligner le chemin.
- **#8 Normaliser le format d'export de façon robuste.** `_save_as` (`main_window.py:304`) ignore le filtre choisi dans la boîte de dialogue ; `save_image_file` (`image_ops.py:46`) enregistre silencieusement en PNG quand l'extension manque. Modèle de format central avec suffixe par défaut ; fusionner les dicts de format dupliqués (dialogue vs. MainWindow). *(Le `KeyError` EXR signalé n'est atteignable que via des réglages manipulés/dérive de dicts ; le cas de l'extension manquante est le cœur visible par l'utilisateur.)*
- **#14 Synchroniser CI et vérifications de doc.** `RESOURCES.md:102` et `TESTING.md:10` indiquent encore « 3.10/3.12 » (en réalité 3.10–3.13) ; `ui-nightly.yml` manque dans les listes de workflows et dans `test_resource_docs.py:35`. Vérifier aussi la liste des workflows et la matrice Python.
- **#15 Faire de la CI de release une vraie barrière.** `ci.yml` ne lance la matrice complète que sur `release: published` (trop tard comme barrière) ; `ui-nightly.yml:18` `continue-on-error: true` masque les échecs. Ajouter un run candidat par tag/pré-release et faire remonter visiblement les échecs nocturnes.

**Paquet 3 — Substance avec mesure (terminé)** 🟠

- **#5 Ne pas réallouer l'overlay à chaque mouvement du pinceau.** `_refresh_overlay` (`canvas.py:263`) → `mask_to_overlay` construit un overlay RGBA complet (40 MP ≈ 160 Mio) — même pour un masque vide et à chaque mouvement de souris. Le créer paresseusement, mettre à jour une région sale ou regrouper les événements.
- **#6 Borner la baguette magique, la rendre annulable, la mesurer.** `flood_fill` (`image_utils.py:48`) fait croître la région en Python ; mesuré ≈ 3,3 s à 2,25 MP (→ secondes à deux chiffres à 40 MP). Ajouter une implémentation scanline/native (p. ex. `scipy.ndimage.label`) et un chemin d'annulation.
- **#7 Sérialiser le warmup rembg et l'appel IA.** `_on_warmup_done` (`main_window.py:270`) affiche « IA prête » même après des erreurs de warmup ; le bouton IA reste utilisable pendant le warmup → init du modèle en parallèle. Séparer succès/erreur et verrouiller le bouton jusqu'à la fin du warmup.
- **#3 Appliquer le budget mémoire de l'historique.** `restore` (`canvas_history.py:81`) et `redo` (`:47`) ajoutent à la pile d'annulation mais contournent l'éviction de `push` → restaurer de façon répétée croît sans limite. Utiliser un helper de rognage commun et tester le budget total.

**Paquet 4 — Sécurité** 🟡

- **#12 Durcir la mise en scène temporaire des plugins Qt.** `qt_plugins.py` (lignes 26/29/48) utilise sous macOS un chemin prévisible dans `/private/tmp`, des fichiers `.tmp` fixes et seulement une comparaison de taille. Comme des plugins Qt exécutables y sont chargés, le pré-amorçage est un vecteur local d'injection de code. Utiliser un répertoire `0700` propre à l'utilisateur, des fichiers temporaires uniques et une vérification de contenu/hash.

**Paquet 5 — Tests et méthodologie** 🟡

- **#13 Orienter les tests vers le comportement, pas le texte source.** Les vérifications AST dans `test_static_checks.py` ne contrôlent que des occurrences de chaînes et ne détectent pas le bug d'annulation IA (#1). Ajouter des tests dynamiques pour le cycle d'annulation, le chargement pendant recadrage/lasso, l'erreur de warmup, un format d'export inconnu, le logging avec un handler existant et le budget mémoire après restauration.

**Paquet 6 — Abandonner / requalifier** 🟢

- **#4 Soustraction Cmd sous macOS — faux positif.** Sans `AA_MacDontSwapCtrlAndMeta` (défini nulle part), Qt mappe Cmd→`ControlModifier` sous macOS ; la vérification dans `canvas.py:80` répond donc déjà à Cmd+clic et le texte de l'UI est correct. Accepter en plus `MetaModifier` lierait à tort la touche Control physique à « soustraire ». **Abandonner le changement de code** ; tout au plus ajouter un test de plateforme qui fige le mapping Qt.
