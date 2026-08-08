# Lossless Crop

## Cas d'utilisation
Cette application permet de rogner rapidement plusieurs images d'un dossier les unes après les autres.

## Formats pris en charge
- **JPEG** : Modes de rognage sans perte ou avec perte
- **PNG** : Sans perte
- **BMP** : Sans perte
- **WebP** : Avec perte

## Remarque sur le rognage sans perte
L'alignement sur la grille est requis pour effectuer un rognage sans perte sur une image *JPEG*, car les images JPEG regroupent les pixels en blocs appelés MCU (Minimum Coded Units). Les limites du rognage doivent s'aligner sur ces blocs pour effectuer le rognage sans recompression ni perte de qualité.
C'est pourquoi, lorsque vous sélectionnez le moteur sans perte sur une image JPEG, la zone sélectionnée s'ajustera automatiquement aux blocs MCU les plus proches. Si vous ne souhaitez pas cela, vous pouvez utiliser le moteur pixel-parfait qui est avec perte mais vous permet de choisir votre zone de rognage librement.
Le rognage des images *PNG* ou *BMP* est toujours sans perte et ne nécessite pas d'alignement.
Le format *WebP* dans cette application est traité comme un rognage avec perte.

## Flux de travail de base
1. Ouvrez un dossier contenant des images
2. Tracez une sélection sur l'image
3. Rognez et passez à l'image suivante

## Zoom avec l'aperçu flottant (HUD)
Vous pouvez activer l'aperçu flottant en appuyant sur `P` ou `Q` ou depuis le tiroir des paramètres.
Cet aperçu peut être redimensionné en faisant glisser les bords avec le clic gauche et déplacé en maintenant le clic droit enfoncé, de manière cohérente avec la zone de sélection.
Si `Preview HUD` est coché dans 'Layout Memory', la taille et la position de l'aperçu seront sauvegardées et restaurées à la prochaine ouverture de l'application.

### Flux de travail A : "Je n'aime pas le zoom flottant"
Un moyen simple d'obtenir un autre zoom est de travailler avec `Overwrite` actif et d'appuyer sur `S` pour rogner la zone souhaitée ; à chaque rognage, l'image actuelle changera et se rechargera en n'affichant que la partie rognée.
Attention, cela écrasera vos fichiers source.

### Flux de travail B : "Je n'aime pas le zoom flottant"
Et si vous devez rogner différentes petites parties d'une grande image ? Vous pouvez désactiver `Overwrite`, rogner toutes les parties nécessaires sur toutes les images désirées, puis ouvrir le sous-dossier 'cropped' où se trouvent ces petites parties et les re-rogner avec plus de précision.

## Options de la barre d'outils
### Moteur (Engine)
- **Lossless** : Utilise l'outil jpegtran pour effectuer un rognage sans perte des images JPEG. Si l'image n'est pas un *JPEG* valide, cette option est ignorée.
- **Pixel-Perfect** : Utilise le moteur Pillow pour rogner, avec une légère perte de qualité pour *JPEG* et *WebP*, ou sans perte pour *PNG* et *BMP*.

### Rapport forcé (Forced Ratio)
Cette option impose un ratio d'aspect sur le rectangle de rognage. Options disponibles :
- Libre (Freeform)
- Ratio d'origine (Source Ratio)
- Carré 1:1 (1:1 Square)
- 16:9 Panoramique (16:9 Widescreen)
- 4:3 Standard (4:3 Standard)

### Retour d'alignement (Snapping Feedback)
Permet de modifier l'affichage de l'alignement sur la grille.
Cela s'applique uniquement au rognage sans perte (le moteur Lossless doit être sélectionné avec une image JPEG valide).
Il y a 3 options :
- **Real Time Snap** : L'alignement est ajusté en temps réel pendant que l'utilisateur trace la zone.
- **Post Release Snap** : L'alignement s'affiche uniquement lorsque l'utilisateur termine son tracé.
- **Ghosting** : Un autre cadre s'affiche pendant le tracé pour montrer la grille alignée.

### Entrées manuelles de la zone de rognage
Les compteurs (spinboxes) permettent de saisir la taille exacte de la zone de rognage.
*Important* : Pour que les valeurs soient prises en compte, l'utilisateur doit appuyer sur Entrée ou quitter les champs de saisie.

### Conserver la sélection (Keep selection)
Utile pour conserver le rectangle de sélection d'une image à l'autre si les tailles de rognage sont similaires.

### Écraser (Overwrite)
L'activation de cette option écrase le fichier source après le rognage.

### Icône Paramètres (Settings Gear)
Ouvre le tiroir des paramètres.

## Tiroir des paramètres
Fournit de nombreuses options de visibilité et de persistance.
### Paramètres généraux
- Enregistrer les paramètres : conserve les paramètres utilisateur et les recharge au prochain démarrage.
- Ouvrir le dernier dossier : ouvre le dernier dossier de travail utilisé au démarrage.
- Ajuster l'aperçu (Fit preview) : modifie la façon dont l'image est affichée dans l'aperçu. L'activer affiche la zone sélectionnée complète.
- Thème sombre (Dark Theme) : active le thème sombre (le thème clair est appliqué par défaut).

### Affichage (Show / Display)
Affecte ce qui est affiché ou masqué dans l'interface utilisateur.

### Mémoire de disposition (Layout Memory)
- Fenêtre principale (Main Window) : recharge la taille et la position de la fenêtre principale au démarrage.
- Aperçu HUD (Preview HUD) : recharge la taille et la position de l'aperçu HUD au démarrage.

## Barre de menus
La barre de menus peut être affichée en appuyant sur *Alt*.
Les commandes courantes sont expliquées dans la section des commandes, seules les actions spéciales sont détaillées ici.

- Fichier -> Voir les logs : Ouvre le dossier contenant les fichiers journaux de l'application.
- Récent -> Dossier : Ouvre le dossier sélectionné dans la liste récente.
- Aide -> Manuel utilisateur : Affiche ce manuel.
- Aide -> À propos : Affiche la fenêtre À propos.

## Raccourcis clavier globaux et contrôles de la souris

| Actions clavier | Touches | Actions souris | Contrôle |
| :--- | :--- | :--- | :--- |
| **Rogner & Suivant** | <kbd>Espace</kbd> | **Tracer un cadre** | <kbd>Clic gauche</kbd> + Glisser |
| **Rogner** | <kbd>S</kbd> ou <kbd>Clic milieu</kbd> | **Déplacer le cadre** | <kbd>Clic droit</kbd> + Glisser |
| **Ouvrir le dossier** | <kbd>O</kbd> | **Naviguer** | <kbd>Molette de la souris</kbd> |
| **Ouvrir l'image** | <kbd>I</kbd> | **Rogner** | <kbd>Clic milieu</kbd> |
| **Passer à la suivante** | <kbd>F</kbd> ou <kbd>D</kbd> | | |
| **Passer à la précédente** | <kbd>B</kbd> ou <kbd>A</kbd> | | |
| **Pivoter (horaire)** | <kbd>R</kbd> | | |
| **Basculer l'aperçu** | <kbd>P</kbd> ou <kbd>Q</kbd> | | |
| **Basculer le menu** | <kbd>Alt</kbd> | | |
| **Quitter l'appli** | <kbd>Échap</kbd> | | |

## Commandes
Plusieurs façons d'effectuer les mêmes actions dans l'application :
- *Ouvrir le dossier* : Ouvre un dossier contenant des images valides.
- *Ouvrir l'image* : Permet de choisir une image individuelle pour ouvrir son dossier.
- *Passer à la suivante* : Passe à l'image suivante.
- *Passer à la précédente* : Passe à l'image précédente.
- *Rogner* : Rogne la zone sélectionnée.
- *Rogner & Suivant* : Rogne et passe à l'image suivante.
- *Pivoter* : Pivote l'image dans le sens horaire.
- *Quitter* : Ferme l'application.

## Prise en charge du glisser-déposer (Drag and Drop)
- Glisser un dossier dans l'application équivaut à la commande Ouvrir le dossier.
- Glisser une image dans l'application équivaut à la commande Ouvrir l'image.

## Icônes de la barre d'outils
À gauche de la barre d'outils, les icônes permettent de déclencher Ouvrir le dossier, Ouvrir l'image, Rogner, Rogner & Suivant et Pivoter dans cet ordre d'apparition.
