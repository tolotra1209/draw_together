Draw Together - Application de Dessin Collaboratif
📋 Description

Draw Together est une application de dessin multijoueur interactive qui permet à plusieurs utilisateurs de collaborer sur un même dessin en temps réel, avec des fonctionnalités de dessin par calques, chat intégré et synchronisation via le réseau.
✨ Fonctionnalités
🎨 Fonctionnalités de dessin

    Outils de dessin :

        Crayon avec taille ajustable

        Pot de peinture (remplissage)

        Gomme

    Palette de couleurs : 8 couleurs prédéfinies

    Système de calques : Dessin guidé par calques superposés

    Annulation/Rétablissement : Ctrl+Z / Ctrl+Y

    Curseurs personnalisés : Visuels adaptés à chaque outil

👥 Mode Multijoueur

    Rôles définis : Joueur 1 et Joueur 2 (chacun leur code .py)

    Collaboration en temps réel via Ingescape (fonctionne pour le chat mais pas pour les dessins)

    Personnages à dessiner : Unko, Eby, Datta

    Synchronisation automatique des dessins (non implémenté, chaque joueur voit son calque sur le whiteboard mais pas celui de son partenaire)

<img width="1346" height="784" alt="image" src="https://github.com/user-attachments/assets/8f6f410d-7862-4009-a410-5512c2227faa" />

<img width="1619" height="935" alt="image" src="https://github.com/user-attachments/assets/ee7cac7d-f232-4398-935e-089b9b0a783b" />

🎮 Expérience utilisateur

    Interface 3D : Boutons avec effets visuels

    Système de progression : Carte des niveaux

    Écrans de transition animés

    Musique et sons d'ambiance

    Sauvegarde automatique des calques

💬 Chat intégré

    Communication texte entre joueurs

    Zone de saisie dans l'interface

    Messages envoyés via Ingescape

<img width="1139" height="799" alt="image" src="https://github.com/user-attachments/assets/ea926bf7-1baa-4436-8060-691533856101" />

<img width="1354" height="787" alt="image" src="https://github.com/user-attachments/assets/7bbc49d9-98a3-42b2-b5cc-9fb28f4ec660" />

🛠️ Installation
Prérequis

    Python 3.10

    Pygame

    Ingescape

Installation des dépendances
bash

$ pip install pygame
$ pip install ingescape

Structure des fichiers
text

draw_together/
├── main.py                    # Script principal
├── fonts/                     # Polices
│   └── Poppins-Bold.ttf
├── images/                   # Assets graphiques
│   ├── menu.png
│   ├── map.png
│   ├── choice.png
│   ├── unko.png
│   ├── eby.png
│   └── datta.png
├── icons/                    # Icônes d'outils
│   ├── pencil.png
│   ├── paint.png
│   └── eraser.png
├── sounds/                   # Fichiers audio
│   ├── menu_music.mp3
│   ├── map_music.mp3
│   ├── level1_music.mp3
│   └── transition_sound.mp3
└── calques/                  # Calques de dessin
    ├── datta_body.png
    ├── datta_eyes.png
    └── ...

🚀 Utilisation
Lancement de l'application, de circle avec le system (DrawTogether.igssystem) et du Whiteboard.exe

<img width="1289" height="653" alt="image" src="https://github.com/user-attachments/assets/60ec402b-4d9b-4591-9dff-df56644b965f" />

bash

$ python main_joueur_1.py (resp. 2 pour le joueur 2)

Navigation

    Menu principal :

        Jouer (mode solo)

        Multijoueur

        Quitter

    Mode solo :

        Sélection du personnage

        Dessin calque par calque

        Sauvegarde automatique

    Mode multijoueur :

        Choix du rôle (Joueur 1 ou 2)

        Sélection du personnage

        Dessin collaboratif

        Chat intégré

Contrôles

    Dessin : Clic et glisser

    Changer couleur : Clic sur la palette

    Changer outil : Clic sur l'icône

    Ajuster taille : Glisser le slider

    Annuler : Ctrl+Z

    Rétablir : Ctrl+Y

    Chat : Saisie dans la zone texte + Entrée

🔗 Configuration réseau
Ingescape

L'application utilise Ingescape pour la communication réseau :

    Port par défaut : 5670

    Interface réseau : Wi-Fi

    Synchronisation automatique des données

Configuration multijoueur

    Assurez-vous que tous les joueurs sont sur le même réseau

    Lancez l'application sur chaque machine

    Sélectionnez le mode multijoueur

    Choisissez des rôles différents

💾 Sauvegarde
Fichiers générés

    Calques : Sauvegardés dans ~/DrawTogether_calques/

    Canvas complet : Sauvegardé dans ~/DrawTogether_canvas.png

    Format : PNG avec transparence

Structure de sauvegarde
text

~/DrawTogether_calques/
├── calque_0_20240101_120000.png
├── calque_1_20240101_120100.png
└── ...

🎯 Personnalisation
Modification des calques

Pour ajouter de nouveaux personnages :

    Créez les images de calques

    Ajoutez-les au dictionnaire calques_complets dans le code

    Placez les images dans le dossier calques/

Ajout de couleurs

Modifiez la liste COULEURS_BASE dans le code :
python

COULEURS_BASE = [
    (0, 0, 0),       # Noir
    (255, 0, 0),     # Rouge
    # ... ajoutez vos couleurs
]

⚠️ Dépannage
Problèmes courants

    Ingescape non installé :
    bash

$ pip install ingescape

Fichiers manquants :

    Vérifiez que tous les dossiers (fonts, images, icons, sounds) existent

    Placez les fichiers requis aux bons emplacements

Problèmes réseau :

    Vérifiez la connexion Wi-Fi

    Assurez-vous que le port 5670 n'est pas bloqué

Erreurs d'import :

    Vérifiez que Pygame est installé

bash

$ pip install pygame --upgrade

Logs

    Les logs sont écrits dans la console

    Activer/désactiver avec igs.log_set_console() et igs.log_set_file()

📝 Notes de développement
Architecture

    Interface : Pygame pour le rendu graphique

    Réseau : Ingescape pour la communication

    Données : Base64 pour l'échange d'images

    État : Système de piles pour undo/redo

Points d'extension

    Ajout de nouveaux outils de dessin

    Support de plus de joueurs

    Export vers d'autres formats

    Interface web/mobile

📄 Licence

Application éducative - Libre d'utilisation et modification
👥 Crédits

    Développé avec Pygame et Ingescape pat BASTIDE Guillaume et RANDRIAMAROVELO Tolotra

    Graphismes originaux

    Sons libres de droits

🤝 Contribution

Les contributions sont les bienvenues :

    Fork du projet

    Création d'une branche

    Commit des modifications

    Push et Pull Request

Version : 1.16
Dernière mise à jour : décembre 2025
