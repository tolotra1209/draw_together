import pygame
from collections import deque
import ingescape as igs
import sys

pygame.init()

igs.agent_set_name("DrawTogether")
igs.definition_set_class("DrawTogether")
igs.log_set_console(True)
igs.log_set_file(True, None)
igs.log_set_stream(True)
igs.set_command_line(sys.executable + " " + " ".join(sys.argv))

igs.start_with_device("Wi-Fi", 5670)

# --- Fenêtre ---
LARGEUR, HAUTEUR = 900, 600
HAUTEUR_BANDEAU = 100
fenetre = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Draw Together - 3D Buttons")

# --- Couleurs ---
NOIR, BLANC, GRIS, VERT = (0, 0, 0), (255, 255, 255), (200, 200, 200), (0, 255, 0)
MARRON_FONCE = (101, 67, 33)
COULEURS_BASE = [
    (0, 0, 0),
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 165, 0),
    (255, 192, 203),
    (255, 255, 255),
]

# --- Variables ---
couleur_actuelle = NOIR
outil = "crayon"
rayon = 6
en_cours = True
dessin = False

# --- Canvas ---
canvas = pygame.Surface((LARGEUR, HAUTEUR - HAUTEUR_BANDEAU))
canvas.fill(BLANC)

# --- Piles Undo/Redo ---
undo_stack = []
redo_stack = []


def save_state():
    undo_stack.append(canvas.copy())
    if len(undo_stack) > 50:
        undo_stack.pop(0)
    redo_stack.clear()

# --- Slider taille ---
slider_rect = pygame.Rect(10, 60, 150, 10)
slider_handle = pygame.Rect(10 + rayon * 2, 55, 10, 20)
slider_drag = False

# --- Palette couleurs ---
palette_rects = []
for i, c in enumerate(COULEURS_BASE):
    rect = pygame.Rect(10 + i * 40, 10, 30, 30)
    palette_rects.append((rect, c))

# --- Couleurs boutons (dégradé) ---
COULEUR_HAUT = (255, 200, 80)  # jaune clair
COULEUR_BAS = (230, 120, 20)  # orange foncé
COULEUR_TEXTE = (90, 40, 0)  # marron foncé

# --- Police boutons ---
try:
    police = pygame.font.Font("fonts/Poppins-Bold.ttf", 28)
except:
    police = pygame.font.SysFont("Arial", 28)

font = pygame.font.SysFont(None, 32)

# --- Outils ---
outils = ["crayon", "pot", "gomme"]
outils_rects = []
for i, nom in enumerate(outils):
    rect = pygame.Rect(400 + i * 60, 10, 50, 50)
    outils_rects.append((rect, nom))

# --- Icônes ---
def load_icon(path, size):
    try:
        return pygame.transform.scale(pygame.image.load(path), size)
    except Exception:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (150, 150, 150), surf.get_rect(), 2)
        return surf

icones = {
    "crayon": load_icon("pencil.png", (40, 40)),
    "pot": load_icon("paint.png", (40, 40)),
    "gomme": load_icon("eraser.png", (40, 40)),
}
curseurs = {"pot": load_icon("paint.png", (24, 24))}
icone_home = load_icon("home.png", (30, 30))
bouton_menu = pygame.Rect(400 + len(outils) * 140, 10, 50, 50)

pygame.mouse.set_visible(True)

# --- Flood fill ---

def flood_fill(surface, x, y, target_color, replacement_color):
    if target_color == replacement_color:
        return
    pile = deque()
    pile.append((x, y))
    largeur, hauteur = surface.get_size()
    while pile:
        nx, ny = pile.popleft()
        if nx < 0 or ny < 0 or nx >= largeur or ny >= hauteur:
            continue
        if surface.get_at((nx, ny)) != target_color:
            continue
        surface.set_at((nx, ny), replacement_color)
        pile.extend([(nx + 1, ny), (nx - 1, ny), (nx, ny + 1), (nx, ny - 1)])


# --- Dessin bouton 3D (réutilisable) ---

def dessiner_bouton_3d(surface, rect, texte, police,
                       couleur_haut, couleur_bas, couleur_texte,
                       survol=False, arrondi=12, border_color=(80, 40, 0)):

    # Ajuste les couleurs si survolé (effet clair)
    if survol:
        couleur_haut = tuple(min(255, c + 20) for c in couleur_haut)
        couleur_bas = tuple(min(255, c + 20) for c in couleur_bas)

    # Surface temporaire transparente
    bouton_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

    # Créer le dégradé vertical dans le rectangle
    for y in range(rect.height):
        ratio = y / rect.height
        r = int(couleur_haut[0] * (1 - ratio) + couleur_bas[0] * ratio)
        g = int(couleur_haut[1] * (1 - ratio) + couleur_bas[1] * ratio)
        b = int(couleur_haut[2] * (1 - ratio) + couleur_bas[2] * ratio)
        pygame.draw.rect(bouton_surf, (r, g, b), (0, y, rect.width, 1))

    # Masque arrondi (forme finale du bouton)
    masque = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(masque, (255, 255, 255, 255),
                     masque.get_rect(), border_radius=arrondi)

    # Appliquer le masque
    bouton_surf.blit(masque, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Bordure
    pygame.draw.rect(bouton_surf, border_color, masque.get_rect(), 2, border_radius=arrondi)

    # Brillance (lumière douce sur le haut du bouton)
    highlight = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
    pygame.draw.rect(highlight, (255, 255, 255, 60),
                     highlight.get_rect(), border_radius=arrondi)
    bouton_surf.blit(highlight, (0, 0))

    # Texte centré
    rendu = police.render(texte, True, couleur_texte)
    bouton_surf.blit(
        rendu,
        ((rect.width - rendu.get_width()) // 2,
         (rect.height - rendu.get_height()) // 2)
    )

    # Affichage final sur la surface principale
    surface.blit(bouton_surf, rect.topleft)

# Petit helper pour dessiner et retourner si survol

def draw_button_and_check(surface, rect, texte, police, mouse_pos, couleur_haut=COULEUR_HAUT, couleur_bas=COULEUR_BAS, couleur_texte=COULEUR_TEXTE):
    survol = rect.collidepoint(mouse_pos)
    dessiner_bouton_3d(surface, rect, texte, police, couleur_haut, couleur_bas, couleur_texte, survol)
    return survol


# --- Musiques / Sons ---

def jouer_musique(fichier, loop=True):
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(fichier)
        pygame.mixer.music.play(-1 if loop else 0)
    except Exception:
        pass


def arreter_musique():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


def jouer_son(fichier):
    try:
        son = pygame.mixer.Sound(fichier)
        son.play()
    except Exception:
        pass


# --- Transition GIF (simple fallback) ---

def jouer_transition():
    try:
        transition = pygame.image.load("transition.gif")
        clock = pygame.time.Clock()
        fenetre.blit(pygame.transform.scale(transition, (LARGEUR, HAUTEUR)), (0, 0))
        pygame.display.flip()
        pygame.time.wait(300)
    except Exception:
        pygame.time.wait(200)


# --- Fonctions multijoueur / modes (réutilisent dessiner_bouton_3d) ---

def lancer_dessin_par_calques_multijoueur(personnage, role):
    global canvas, dessin, rayon, outil, couleur_actuelle, bouton_menu

    calques_complets = {
        "Datta": {
            1: ["datta_body.png", "datta_eggs.png"],
            2: ["datta_eyes.png", "datta_mouth.png", "datta_noodles.png"],
        },
        "Eby": {
            1: ["eby_body.png", "eby_mouth.png"],
            2: ["eby_eyes.png", "eby_tail.png"],
        },
        "Unko": {
            1: ["unko_body.png"],
            2: ["unko_eyes.png", "unko_mouth.png"],
        },
    }

    layers = calques_complets.get(personnage, {}).get(role, [])
    if not layers:
        print("⚠️ Aucun calque pour ce rôle ou personnage.")
        return

    current_layer = 0
    dessin_finished = False
    bouton_suivant = pygame.Rect(LARGEUR - 140, HAUTEUR - 60, 120, 40)

    current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
    current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
    current_guide.set_alpha(102)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if (mods & pygame.KMOD_CTRL):
                    if event.key == pygame.K_z and undo_stack:
                        redo_stack.append(canvas.copy())
                        canvas.blit(undo_stack.pop(), (0, 0))
                    elif event.key == pygame.K_y and redo_stack:
                        undo_stack.append(canvas.copy())
                        canvas.blit(redo_stack.pop(), (0, 0))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                clique_interface = False
                if y < HAUTEUR_BANDEAU:
                    for rect, c in palette_rects:
                        if rect.collidepoint(x, y):
                            couleur_actuelle = c
                            outil = "crayon"
                            clique_interface = True
                    for rect, nom in outils_rects:
                        if rect.collidepoint(x, y):
                            outil = nom
                            clique_interface = True
                    if slider_rect.collidepoint(x, y):
                        slider_handle.x = max(slider_rect.left, min(slider_rect.right - 10, x))
                        rayon = int((slider_handle.x - slider_rect.left) / 2) + 1
                        global slider_drag
                        slider_drag = True
                        clique_interface = True
                    if bouton_menu.collidepoint(x, y):
                        canvas.fill(BLANC)
                        menu()
                        return
                if not dessin_finished and bouton_suivant.collidepoint(x, y):
                    if current_layer < len(layers) - 1:
                        current_layer += 1
                        current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
                        current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
                        current_guide.set_alpha(102)
                    else:
                        dessin_finished = True
                if (not clique_interface and not dessin_finished and
                    y >= HAUTEUR_BANDEAU and not bouton_suivant.collidepoint(x, y)):
                    save_state()
                    dessin = True
                    if outil == "crayon":
                        pygame.draw.circle(canvas, couleur_actuelle, (x, y - HAUTEUR_BANDEAU), rayon)
                    elif outil == "gomme":
                        pygame.draw.circle(canvas, BLANC, (x, y - HAUTEUR_BANDEAU), rayon)
                    elif outil == "pot":
                        target_color = canvas.get_at((x, y - HAUTEUR_BANDEAU))
                        flood_fill(canvas, x, y - HAUTEUR_BANDEAU, target_color, couleur_actuelle)
                        save_state()
            elif event.type == pygame.MOUSEBUTTONUP:
                dessin = False
                slider_drag = False
            elif event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                if dessin and not dessin_finished and y >= HAUTEUR_BANDEAU and not bouton_suivant.collidepoint(x, y):
                    if outil == "crayon":
                        pygame.draw.circle(canvas, couleur_actuelle, (x, y - HAUTEUR_BANDEAU), rayon)
                    elif outil == "gomme":
                        pygame.draw.circle(canvas, BLANC, (x, y - HAUTEUR_BANDEAU), rayon)
                if slider_drag:
                    slider_handle.x = max(slider_rect.left, min(slider_rect.right - 10, x))
                    rayon = int((slider_handle.x - slider_rect.left) / 2) + 1

        # --- AFFICHAGE ---
        fenetre.fill(GRIS)
        fenetre.blit(canvas, (0, HAUTEUR_BANDEAU))
        if current_guide and not dessin_finished:
            fenetre.blit(current_guide, (0, HAUTEUR_BANDEAU))

        pygame.draw.rect(fenetre, (180, 180, 180), (0, 0, LARGEUR, HAUTEUR_BANDEAU))

        # Palette
        for rect, c in palette_rects:
            pygame.draw.rect(fenetre, c, rect)
            pygame.draw.rect(fenetre, VERT if c == couleur_actuelle else NOIR, rect, 3 if c == couleur_actuelle else 2)

        # Outils
        for rect, nom in outils_rects:
            survol = rect.collidepoint(mouse_pos)
            dessiner_bouton_3d(fenetre, rect, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, survol)
            fenetre.blit(icones[nom], (rect.x + 5, rect.y + 5))
            pygame.draw.rect(fenetre, VERT if nom == outil else NOIR, rect, 3 if nom == outil else 2)

        # Slider visuel
        pygame.draw.rect(fenetre, (150, 150, 150), slider_rect)
        pygame.draw.rect(fenetre, (0, 0, 0), slider_handle)
        fenetre.blit(font.render(f"Taille: {rayon}", True, NOIR), (170, 55))

        # Menu (icône) - dessiné en 3D
        survol_menu = bouton_menu.collidepoint(mouse_pos)
        dessiner_bouton_3d(fenetre, bouton_menu, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, survol_menu)
        fenetre.blit(icone_home, (bouton_menu.x + 10, bouton_menu.y + 10))

        # Suivant / Terminer
        if not dessin_finished:
            survol_suiv = draw_button_and_check(fenetre, bouton_suivant, "Suivant" if current_layer < len(layers) - 1 else "Terminer", police, mouse_pos)

        # Curseur
        x, y = pygame.mouse.get_pos()
        taille_curseur = rayon if y >= HAUTEUR_BANDEAU else 6
        if outil == "crayon":
            pygame.draw.circle(fenetre, couleur_actuelle, (x, y), taille_curseur)
        elif outil == "gomme":
            pygame.draw.circle(fenetre, NOIR, (x, y), taille_curseur, 1)
        elif outil == "pot":
            fenetre.blit(curseurs["pot"], (x - 12, y - 12))

        pygame.display.flip()


def selection_dessin_multijoueur(role):
    images = ["unko.png", "eby.png", "datta.png"]
    noms = ["Unko", "Eby", "Datta"]

    rects = []
    decal_x = 100
    y_pos = 200
    largeur_img, hauteur_img = 150, 150

    for i, img in enumerate(images):
        rect = pygame.Rect(decal_x + i * 250, y_pos, largeur_img, hauteur_img)
        rects.append(rect)

    images_surfaces = [pygame.transform.scale(pygame.image.load(img), (largeur_img, hauteur_img)) for img in images]
    fond_choice = pygame.transform.scale(pygame.image.load("choice.png"), (LARGEUR, HAUTEUR))

    selection = True
    pygame.mouse.set_visible(True)
    while selection:
        mouse_pos = pygame.mouse.get_pos()
        fenetre.blit(fond_choice, (0, 0))

        titre = font.render("Quel personnage dessiner ?", True, NOIR)
        titre_rect = pygame.Rect((LARGEUR - titre.get_width()) // 2 - 20, 40, titre.get_width() + 40, titre.get_height() + 20)
        pygame.draw.rect(fenetre, BLANC, titre_rect)
        pygame.draw.rect(fenetre, MARRON_FONCE, titre_rect, 3)
        fenetre.blit(titre, (titre_rect.x + 20, titre_rect.y + 10))

        for i, rect in enumerate(rects):
            # bouton 3D autour de l'image
            dessiner_bouton_3d(fenetre, rect, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, rect.collidepoint(mouse_pos))
            fenetre.blit(images_surfaces[i], (rect.x, rect.y))

            texte = font.render(noms[i], True, MARRON_FONCE)
            texte_rect = pygame.Rect(rect.x, rect.y + hauteur_img + 5, largeur_img, texte.get_height() + 4)
            dessiner_bouton_3d(fenetre, texte_rect, noms[i], police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, texte_rect.collidepoint(mouse_pos))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(x, y):
                        return noms[i]


def afficher_carte_multijoueur(role):
    jouer_musique("map_music.mp3")

    fond = pygame.transform.scale(pygame.image.load("map.png"), (LARGEUR, HAUTEUR))
    bouton_retour = pygame.Rect(20, 20, 120, 40)

    niveaux = [
        {"pos": (224, 542), "actif": True},
        {"pos": (675, 428), "actif": False},
        {"pos": (279, 316), "actif": False},
        {"pos": (750, 216), "actif": False},
        {"pos": (441, 219), "actif": False},
    ]

    en_carte = True
    pygame.mouse.set_visible(True)

    while en_carte:
        mouse_pos = pygame.mouse.get_pos()
        fenetre.blit(fond, (0, 0))

        # Bouton retour 3D
        draw_button_and_check(fenetre, bouton_retour, "Retour", police, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if bouton_retour.collidepoint(x, y):
                    choisir_role()
                    return
                for i, niv in enumerate(niveaux):
                    nx, ny = niv["pos"]
                    if (x - nx) ** 2 + (y - ny) ** 2 <= 15 ** 2:
                        if niv["actif"]:
                            if i == 0:
                                arreter_musique()
                                jouer_musique("level1_music.mp3")
                            personnage = selection_dessin_multijoueur(role)
                            lancer_dessin_par_calques_multijoueur(personnage, role)
                            return


def choisir_role():
    fond = pygame.transform.scale(pygame.image.load("menu.png"), (LARGEUR, HAUTEUR))
    bouton_j1 = pygame.Rect(LARGEUR // 2 - 150, 300, 120, 50)
    bouton_j2 = pygame.Rect(LARGEUR // 2 + 30, 300, 120, 50)
    bouton_retour = pygame.Rect(LARGEUR // 2 - 100, 400, 200, 50)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        fenetre.blit(fond, (0, 0))
        titre = font.render("Choisir votre rôle", True, NOIR)
        fenetre.blit(titre, (LARGEUR // 2 - titre.get_width() // 2, 200))

        draw_button_and_check(fenetre, bouton_j1, "Joueur 1", police, mouse_pos)
        draw_button_and_check(fenetre, bouton_j2, "Joueur 2", police, mouse_pos)
        draw_button_and_check(fenetre, bouton_retour, "Retour", police, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if bouton_j1.collidepoint(x, y):
                    role = 1
                    jouer_transition()
                    afficher_carte_multijoueur(role)
                    return
                elif bouton_j2.collidepoint(x, y):
                    role = 2
                    jouer_transition()
                    afficher_carte_multijoueur(role)
                    return
                elif bouton_retour.collidepoint(x, y):
                    menu_multijoueur()
                    return


def menu_multijoueur():
    fond = pygame.transform.scale(pygame.image.load("menu.png"), (LARGEUR, HAUTEUR))
    bouton_2j = pygame.Rect(LARGEUR // 2 - 100, 300, 200, 50)
    bouton_retour = pygame.Rect(LARGEUR // 2 - 100, 400, 200, 50)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        fenetre.blit(fond, (0, 0))
        titre = font.render("Mode Multijoueur", True, NOIR)
        fenetre.blit(titre, (LARGEUR // 2 - titre.get_width() // 2, 200))

        draw_button_and_check(fenetre, bouton_2j, "2 Joueurs", police, mouse_pos)
        draw_button_and_check(fenetre, bouton_retour, "Retour", police, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if bouton_2j.collidepoint(x, y):
                    choisir_role()
                    return
                elif bouton_retour.collidepoint(x, y):
                    menu()
                    return


# --- Menu principal ---
def menu():
    global canvas
    bouton_jouer = pygame.Rect(LARGEUR // 2 - 100, 300, 200, 50)
    bouton_multi = pygame.Rect(LARGEUR // 2 - 100, 400, 200, 50)
    bouton_quitter = pygame.Rect(LARGEUR // 2 - 100, 500, 200, 50)

    fond_menu = pygame.transform.scale(pygame.image.load("menu.png"), (LARGEUR, HAUTEUR))
    logo = pygame.transform.scale(pygame.image.load("logo.png"), (200, 150))

    in_menu = True
    jouer_musique("menu_music.mp3")
    while in_menu:
        mouse_pos = pygame.mouse.get_pos()
        fenetre.blit(fond_menu, (0, 0))
        fenetre.blit(logo, (LARGEUR // 2 - 100, 100))

        draw_button_and_check(fenetre, bouton_jouer, "Jouer", police, mouse_pos)
        draw_button_and_check(fenetre, bouton_multi, "Multijoueur", police, mouse_pos)
        draw_button_and_check(fenetre, bouton_quitter, "Quitter", police, mouse_pos)

        pygame.mouse.set_visible(True)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if bouton_jouer.collidepoint(x, y):
                    jouer_son("transition_sound.mp3")
                    canvas.fill(BLANC)
                    in_menu = False
                    jouer_transition()
                    afficher_carte()
                elif bouton_multi.collidepoint(x, y):
                    jouer_son("transition_sound.mp3")
                    canvas.fill(BLANC)
                    in_menu = False
                    jouer_transition()
                    menu_multijoueur()
                elif bouton_quitter.collidepoint(x, y):
                    pygame.quit(); exit()
        pygame.display.flip()


# --- Affichage de la carte des niveaux ---
def afficher_carte():
    jouer_musique("map_music.mp3")

    global canvas

    carte = pygame.transform.scale(pygame.image.load("map.png"), (LARGEUR, HAUTEUR))
    bouton_retour = pygame.Rect(20, 20, 120, 40)

    niveaux = [
        {"pos": (224, 542), "actif": True},
        {"pos": (675, 428), "actif": False},
        {"pos": (279, 316), "actif": False},
        {"pos": (750, 216), "actif": False},
        {"pos": (441, 219), "actif": False},
    ]

    en_carte = True
    pygame.mouse.set_visible(True)
    while en_carte:
        mouse_pos = pygame.mouse.get_pos()
        fenetre.blit(carte, (0, 0))

        draw_button_and_check(fenetre, bouton_retour, "Retour", police, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if bouton_retour.collidepoint(x, y):
                    menu()
                    return
                for i, niv in enumerate(niveaux):
                    nx, ny = niv["pos"]
                    if (x - nx) ** 2 + (y - ny) ** 2 <= 15 ** 2:
                        if niv["actif"]:
                            if i == 0:
                                arreter_musique()
                                jouer_musique("level1_music.mp3")
                            personnage_choisi = selection_dessin()
                            lancer_dessin_par_calques(personnage_choisi)
                            return


# --- Sélection du dessin ---
def selection_dessin():
    images = ["unko.png", "eby.png", "datta.png"]
    noms = ["Unko", "Eby", "Datta"]

    rects = []
    decal_x = 100
    y_pos = 200
    largeur_img, hauteur_img = 150, 150
    for i, img in enumerate(images):
        rect = pygame.Rect(decal_x + i * 250, y_pos, largeur_img, hauteur_img)
        rects.append(rect)

    images_surfaces = [pygame.transform.scale(pygame.image.load(img), (largeur_img, hauteur_img)) for img in images]
    fond_choice = pygame.transform.scale(pygame.image.load("choice.png"), (LARGEUR, HAUTEUR))

    selection = True
    pygame.mouse.set_visible(True)
    while selection:
        mouse_pos = pygame.mouse.get_pos()
        fenetre.blit(fond_choice, (0, 0))

        titre = font.render("Quel personnage dessiner ?", True, NOIR)
        titre_rect = pygame.Rect((LARGEUR - titre.get_width()) // 2 - 20, 40, titre.get_width() + 40, titre.get_height() + 20)
        pygame.draw.rect(fenetre, BLANC, titre_rect)
        pygame.draw.rect(fenetre, MARRON_FONCE, titre_rect, 3)
        fenetre.blit(titre, (titre_rect.x + 20, titre_rect.y + 10))

        for i, rect in enumerate(rects):
            dessiner_bouton_3d(fenetre, rect, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, rect.collidepoint(mouse_pos))
            fenetre.blit(images_surfaces[i], (rect.x, rect.y))

            texte = font.render(noms[i], True, MARRON_FONCE)
            texte_rect = pygame.Rect(rect.x, rect.y + hauteur_img + 5, largeur_img, texte.get_height() + 4)
            dessiner_bouton_3d(fenetre, texte_rect, noms[i], police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, texte_rect.collidepoint(mouse_pos))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(x, y):
                        return noms[i]


# --- Dessin par calques ---
def lancer_dessin_par_calques(personnage):
    global canvas, dessin, rayon, outil, couleur_actuelle, bouton_menu
    dessin_finished = False

    calques = {
        "Datta": ["datta_body.png", "datta_eyes.png", "datta_mouth.png", "datta_noodles.png", "datta_eggs.png"],
        "Eby": ["eby_body.png", "eby_eyes.png", "eby_mouth.png", "eby_tail.png"],
        "Unko": ["unko_body.png", "unko_eyes.png", "unko_mouth.png"],
    }
    layers = calques.get(personnage, [])
    current_layer = 0

    bouton_suivant = pygame.Rect(LARGEUR - 140, HAUTEUR - 60, 120, 40)

    current_guide = None
    if layers:
        current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
        current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
        current_guide.set_alpha(102)

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
                elif event.type == pygame.KEYDOWN:
                    mods = pygame.key.get_mods()
                    if (mods & pygame.KMOD_CTRL):
                        if event.key == pygame.K_z and undo_stack:
                            redo_stack.append(canvas.copy())
                            canvas.blit(undo_stack.pop(), (0, 0))
                        elif event.key == pygame.K_y and redo_stack:
                            undo_stack.append(canvas.copy())
                            canvas.blit(redo_stack.pop(), (0, 0))
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    clique_interface = False
                    if y < HAUTEUR_BANDEAU:
                        for rect, c in palette_rects:
                            if rect.collidepoint(x, y):
                                couleur_actuelle = c
                                outil = "crayon"
                                clique_interface = True
                        for rect, nom in outils_rects:
                            if rect.collidepoint(x, y):
                                outil = nom
                                clique_interface = True
                        if slider_rect.collidepoint(x, y):
                            slider_handle.x = max(slider_rect.left, min(slider_rect.right - 10, x))
                            rayon = int((slider_handle.x - slider_rect.left) / 2) + 1
                            global slider_drag
                            slider_drag = True
                            clique_interface = True
                        if bouton_menu.collidepoint(x, y):
                            canvas.fill(BLANC)
                            menu()
                            return
                    if not dessin_finished and bouton_suivant.collidepoint(x, y):
                        if current_layer < len(layers) - 1:
                            current_layer += 1
                            current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
                            current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
                            current_guide.set_alpha(102)
                        else:
                            dessin_finished = True
                    if (not clique_interface and not dessin_finished and
                        y >= HAUTEUR_BANDEAU and not bouton_suivant.collidepoint(x, y)):
                        save_state()
                        dessin = True
                        if outil == "crayon":
                            pygame.draw.circle(canvas, couleur_actuelle, (x, y - HAUTEUR_BANDEAU), rayon)
                        elif outil == "gomme":
                            pygame.draw.circle(canvas, BLANC, (x, y - HAUTEUR_BANDEAU), rayon)
                        elif outil == "pot":
                            target_color = canvas.get_at((x, y - HAUTEUR_BANDEAU))
                            flood_fill(canvas, x, y - HAUTEUR_BANDEAU, target_color, couleur_actuelle)
                            save_state()
                elif event.type == pygame.MOUSEBUTTONUP:
                    dessin = False
                    slider_drag = False
                elif event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    if dessin and not dessin_finished and y >= HAUTEUR_BANDEAU and not bouton_suivant.collidepoint(x, y):
                        if outil == "crayon":
                            pygame.draw.circle(canvas, couleur_actuelle, (x, y - HAUTEUR_BANDEAU), rayon)
                        elif outil == "gomme":
                            pygame.draw.circle(canvas, BLANC, (x, y - HAUTEUR_BANDEAU), rayon)
                    if slider_drag:
                        slider_handle.x = max(slider_rect.left, min(slider_rect.right - 10, x))
                        rayon = int((slider_handle.x - slider_rect.left) / 2) + 1

            # --- AFFICHAGE ---
            fenetre.fill(GRIS)
            fenetre.blit(canvas, (0, HAUTEUR_BANDEAU))
            if current_guide and not dessin_finished:
                fenetre.blit(current_guide, (0, HAUTEUR_BANDEAU))

            pygame.draw.rect(fenetre, (180, 180, 180), (0, 0, LARGEUR, HAUTEUR_BANDEAU))

            for rect, c in palette_rects:
                pygame.draw.rect(fenetre, c, rect)
                pygame.draw.rect(fenetre, VERT if c == couleur_actuelle else NOIR, rect, 3 if c == couleur_actuelle else 2)
            for rect, nom in outils_rects:
                survol = rect.collidepoint(mouse_pos)
                dessiner_bouton_3d(fenetre, rect, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, survol)
                fenetre.blit(icones[nom], (rect.x + 5, rect.y + 5))
                pygame.draw.rect(fenetre, VERT if nom == outil else NOIR, rect, 3 if nom == outil else 2)

            pygame.draw.rect(fenetre, (150, 150, 150), slider_rect)
            pygame.draw.rect(fenetre, (0, 0, 0), slider_handle)
            fenetre.blit(font.render(f"Taille: {rayon}", True, NOIR), (170, 55))

            survol_menu = bouton_menu.collidepoint(mouse_pos)
            dessiner_bouton_3d(fenetre, bouton_menu, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, survol_menu)
            fenetre.blit(icone_home, (bouton_menu.x + 10, bouton_menu.y + 10))
            pygame.draw.rect(fenetre, NOIR, bouton_menu, 2)

            if not dessin_finished:
                draw_button_and_check(fenetre, bouton_suivant, "Suivant" if current_layer < len(layers) - 1 else "Terminer", police, mouse_pos)

            x, y = pygame.mouse.get_pos()
            taille_curseur = rayon if y >= HAUTEUR_BANDEAU else 6
            if outil == "crayon":
                pygame.draw.circle(fenetre, couleur_actuelle, (x, y), taille_curseur)
            elif outil == "gomme":
                pygame.draw.circle(fenetre, NOIR, (x, y), taille_curseur, 1)
            elif outil == "pot":
                fenetre.blit(curseurs["pot"], (x - 12, y - 12))
            pygame.display.flip()


# --- Lancement ---
menu()
pygame.quit()
