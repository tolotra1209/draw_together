import pygame
from collections import deque
import ingescape as igs
import sys
import io, base64, time, hashlib, os
from datetime import datetime

# ---------- Initialisation pygame / Ingescape ----------
pygame.init()

igs.agent_set_name("DrawTogether_2")
igs.definition_set_class("DrawTogether")
igs.log_set_console(True)
igs.log_set_file(True, None)
igs.log_set_stream(True)
igs.set_command_line(sys.executable + " " + " ".join(sys.argv))

# --- Sécurité ---
if not hasattr(igs, "DATA_TYPE_STRING"):
    igs.TYPE_BOOL = 0
    igs.TYPE_INT = 1
    igs.TYPE_DOUBLE = 2
    igs.TYPE_STRING = 3
    igs.TYPE_DATA = 4

elementId = -1

def Elementcreated_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    global elementId 
    elementId = tuple_args[0]

# --- Création des I/O Ingescape ---
try:
    igs.output_create("messageOutput", igs.STRING_T, "Message texte")
    igs.output_create("sendImpulse_chat", igs.IMPULSION_T, "Impulsion déclenchement")
    igs.output_create("sendImpulse_calque", igs.IMPULSION_T, "Impulsion déclenchement")
    igs.output_create("imageUrl", igs.TYPE_STRING, "URL de l'image du canvas")
    igs.output_create("posX", igs.TYPE_DOUBLE, "Position X")
    igs.output_create("posY", igs.TYPE_DOUBLE, "Position Y")
    igs.service_init("elementCreated", Elementcreated_callback, None)
    igs.service_arg_add("elementCreated", "elementId", igs.INTEGER_T)
except Exception as e:
    print("Attention : output/input creation error (non critique si déjà créé):", e)

# Démarrage Ingescape
try:
    igs.start_with_device("Wi-Fi", 5670)
except Exception as e:
    print("Warning: igs.start_with_device error (vérifie réseau/ports):", e)

# ---- Affichage Whiteboard ----
arguments_list = (2.0, "anystring", True, 24, b'\x00')
igs.service_call("Whiteboard", "addImage", (), "")

# ---------- Fenêtre ----------
LARGEUR, HAUTEUR = 900, 600
HAUTEUR_BANDEAU = 100
fenetre = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Draw Together - 3D Buttons")

# ---------- Couleurs ----------
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

# ---------- Variables ----------
couleur_actuelle = NOIR
outil = "crayon"
rayon = 6
dessin = False

# ---------- Canvas (shared layer) ----------
canvas = pygame.Surface((LARGEUR, HAUTEUR - HAUTEUR_BANDEAU))
canvas.fill(BLANC)

# ---------- Undo/Redo ----------
undo_stack = []
redo_stack = []

def save_state():
    undo_stack.append(canvas.copy())
    if len(undo_stack) > 50:
        undo_stack.pop(0)
    redo_stack.clear()

# ---------- Conversion surface <-> base64 ----------
def surface_to_base64(surface):
    """Convertit une surface Pygame en chaîne base64 (PNG)."""
    buffer = io.BytesIO()
    # On sauvegarde en PNG pour compacter
    pygame.image.save(surface, buffer)
    return base64.b64encode(buffer.getvalue())

def base64_to_surface(b64_str):
    """Reconvertit une base64 en surface Pygame."""
    try:
        if isinstance(b64_str, bytes):
            b64_str = b64_str.decode('utf-8', errors='ignore')

        # Nettoyage des caractères parasites
        b64_str = ''.join(c for c in b64_str if c.isalnum() or c in '+/=')

        # Si la longueur n’est pas multiple de 4, la donnée est incomplète
        if len(b64_str) % 4 != 0:
            return None

        buffer = io.BytesIO(base64.b64decode(b64_str))
        return pygame.image.load(buffer).convert()

    except Exception as e:
        # Optionnel : supprime l'affichage de l'erreur pour ne pas polluer le log
        # print("Erreur de décodage:", e)
        return None


def hash_string(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

# ---------- Slider taille ----------
slider_rect = pygame.Rect(10, 60, 150, 10)
slider_handle = pygame.Rect(10 + rayon * 2, 55, 10, 20)
slider_drag = False

# ---------- Palette couleurs ----------
palette_rects = []
for i, c in enumerate(COULEURS_BASE):
    rect = pygame.Rect(10 + i * 40, 10, 30, 30)
    palette_rects.append((rect, c))

# ---------- Boutons / Styles ----------
COULEUR_HAUT = (255, 200, 80)  # jaune clair
COULEUR_BAS = (230, 120, 20)   # orange foncé
COULEUR_TEXTE = (90, 40, 0)    # marron foncé

try:
    police = pygame.font.Font("fonts/Poppins-Bold.ttf", 28)
except Exception:
    police = pygame.font.SysFont("Arial", 28)

font = pygame.font.SysFont(None, 32)

# ---------- Outils ----------
outils = ["crayon", "pot", "gomme"]
outils_rects = []
for i, nom in enumerate(outils):
    rect = pygame.Rect(400 + i * 60, 10, 50, 50)
    outils_rects.append((rect, nom))

# ---------- Icônes loader ----------
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

# ---------- Flood fill ----------
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

# ---------- Dessin bouton 3D ----------
def dessiner_bouton_3d(surface, rect, texte, police,
                       couleur_haut, couleur_bas, couleur_texte,
                       survol=False, arrondi=12, border_color=(80, 40, 0)):
    if survol:
        couleur_haut = tuple(min(255, c + 20) for c in couleur_haut)
        couleur_bas = tuple(min(255, c + 20) for c in couleur_bas)

    bouton_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    for y in range(rect.height):
        ratio = y / rect.height
        r = int(couleur_haut[0] * (1 - ratio) + couleur_bas[0] * ratio)
        g = int(couleur_haut[1] * (1 - ratio) + couleur_bas[1] * ratio)
        b = int(couleur_haut[2] * (1 - ratio) + couleur_bas[2] * ratio)
        pygame.draw.rect(bouton_surf, (r, g, b), (0, y, rect.width, 1))

    masque = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(masque, (255, 255, 255, 255),
                     masque.get_rect(), border_radius=arrondi)
    bouton_surf.blit(masque, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.rect(bouton_surf, border_color, masque.get_rect(), 2, border_radius=arrondi)

    highlight = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
    pygame.draw.rect(highlight, (255, 255, 255, 60),
                     highlight.get_rect(), border_radius=arrondi)
    bouton_surf.blit(highlight, (0, 0))

    rendu = police.render(texte, True, couleur_texte)
    bouton_surf.blit(
        rendu,
        ((rect.width - rendu.get_width()) // 2,
         (rect.height - rendu.get_height()) // 2)
    )
    surface.blit(bouton_surf, rect.topleft)

def draw_button_and_check(surface, rect, texte, police, mouse_pos, couleur_haut=COULEUR_HAUT, couleur_bas=COULEUR_BAS, couleur_texte=COULEUR_TEXTE):
    survol = rect.collidepoint(mouse_pos)
    dessiner_bouton_3d(surface, rect, texte, police, couleur_haut, couleur_bas, couleur_texte, survol)
    return survol

# ---------- Sons ----------
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

def jouer_transition():
    try:
        transition = pygame.image.load("transition.gif")
        fenetre.blit(pygame.transform.scale(transition, (LARGEUR, HAUTEUR)), (0, 0))
        pygame.display.flip()
        pygame.time.wait(300)
    except Exception:
        pygame.time.wait(200)

# ---------- Synchronisation Ingescape (polling) ----------
last_remote_hash = None
last_local_send = 0.0
SEND_INTERVAL = 1.0  # en secondes (tester 0.3 - 0.5)

def send_canvas_if_needed():
    try:
        # Convertir le canvas actuel en base64
        data = surface_to_base64(canvas)

        # Envoyer au whiteboard avec la transparence
        igs.output_set_string("canvas_data", data.decode('utf-8'))
        igs.service_call("Whiteboard", "chat", ("calque mis à jour"), "")
        igs.service_call("Whiteboard", "remove", (elementId), "")
        igs.service_call("Whiteboard", "addImage", (data, 150, 50, 600, 400), "")
    except Exception as e:
        print("Erreur d'envoi au whiteboard:", e)

def poll_remote_and_blit():
    global last_remote_hash
    try:
        remote_data = None

        # --- Lecture de la donnée distante ---
        try:
            remote_data = igs.input_data("canvas_data")
        except Exception:
            # fallback -> certaines versions renvoient via input_get_data()
            try:
                raw = igs.input_get_data("canvas_data")
                if raw:
                    remote_data = raw
            except Exception:
                remote_data = None

        if not remote_data:
            return

        # --- Correction importante : conversion bytes -> str ---
        if isinstance(remote_data, bytes):
            try:
                remote_data = remote_data.decode("utf-8")
            except Exception:
                # si la donnée contient déjà du texte encodé base64, on la garde brute
                remote_data = remote_data.decode(errors="ignore")

        # --- Évite de redessiner si la donnée est identique ---
        h = hash_string(remote_data)
        if last_remote_hash == h:
            return
        last_remote_hash = h

        # --- Décodage et fusion sur le canevas ---
        surf = base64_to_surface(remote_data)
        if surf:
            canvas.blit(surf, (0, 0))

    except Exception as e:
        print("Erreur lecture Ingescape/poll:", e)


# ---------- Menus et fonctions multijoueur ----------
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

    images_surfaces = []
    for img in images:
        try:
            images_surfaces.append(pygame.transform.scale(pygame.image.load(img), (largeur_img, hauteur_img)))
        except Exception:
            images_surfaces.append(pygame.Surface((largeur_img, hauteur_img)))

    fond_choice = None
    try:
        fond_choice = pygame.transform.scale(pygame.image.load("choice.png"), (LARGEUR, HAUTEUR))
    except Exception:
        fond_choice = pygame.Surface((LARGEUR, HAUTEUR))
        fond_choice.fill((220, 220, 220))

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
                sauvegarder_et_quitter()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(x, y):
                        return noms[i]

def afficher_carte_multijoueur(role):
    jouer_musique("map_music.mp3")

    try:
        fond = pygame.transform.scale(pygame.image.load("map.png"), (LARGEUR, HAUTEUR))
    except Exception:
        fond = pygame.Surface((LARGEUR, HAUTEUR))
        fond.fill((180, 200, 220))

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

        draw_button_and_check(fenetre, bouton_retour, "Retour", police, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sauvegarder_et_quitter()
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
    try:
        fond = pygame.transform.scale(pygame.image.load("menu.png"), (LARGEUR, HAUTEUR))
    except Exception:
        fond = pygame.Surface((LARGEUR, HAUTEUR))
        fond.fill((200, 200, 200))

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
                sauvegarder_et_quitter()
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
    try:
        fond = pygame.transform.scale(pygame.image.load("menu.png"), (LARGEUR, HAUTEUR))
    except Exception:
        fond = pygame.Surface((LARGEUR, HAUTEUR))
        fond.fill((200, 200, 200))

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
                sauvegarder_et_quitter()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if bouton_2j.collidepoint(x, y):
                    choisir_role()
                    return
                elif bouton_retour.collidepoint(x, y):
                    menu()
                    return

# ---------- Menu principal ----------
def menu():
    global canvas
    try:
        fond_menu = pygame.transform.scale(pygame.image.load("menu.png"), (LARGEUR, HAUTEUR))
    except Exception:
        fond_menu = pygame.Surface((LARGEUR, HAUTEUR))
        fond_menu.fill((200, 200, 200))
    try:
        logo = pygame.transform.scale(pygame.image.load("logo.png"), (200, 150))
    except Exception:
        logo = pygame.Surface((200, 150))
        logo.fill((150, 150, 150))

    bouton_jouer = pygame.Rect(LARGEUR // 2 - 100, 300, 200, 50)
    bouton_multi = pygame.Rect(LARGEUR // 2 - 100, 400, 200, 50)
    bouton_quitter = pygame.Rect(LARGEUR // 2 - 100, 500, 200, 50)

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
                sauvegarder_et_quitter()
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
                    sauvegarder_et_quitter()
        pygame.display.flip()

# ---------- Affichage de la carte des niveaux (solo) ----------
def afficher_carte():
    jouer_musique("map_music.mp3")

    try:
        carte = pygame.transform.scale(pygame.image.load("map.png"), (LARGEUR, HAUTEUR))
    except Exception:
        carte = pygame.Surface((LARGEUR, HAUTEUR))
        carte.fill((180, 200, 220))

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
                sauvegarder_et_quitter()
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

# ---------- Sélection du dessin (solo) ----------
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

    images_surfaces = []
    for img in images:
        try:
            images_surfaces.append(pygame.transform.scale(pygame.image.load(img), (largeur_img, hauteur_img)))
        except Exception:
            images_surfaces.append(pygame.Surface((largeur_img, hauteur_img)))

    fond_choice = None
    try:
        fond_choice = pygame.transform.scale(pygame.image.load("choice.png"), (LARGEUR, HAUTEUR))
    except Exception:
        fond_choice = pygame.Surface((LARGEUR, HAUTEUR))
        fond_choice.fill((220, 220, 220))

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
                sauvegarder_et_quitter()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(x, y):
                        return noms[i]

# ---------- Dessin par calques (solo) ----------
def lancer_dessin_par_calques(personnage):
    global canvas, dessin, rayon, outil, couleur_actuelle, bouton_menu
    dessin_finished = False

    # Définition des calques pour chaque personnage
    calques = {
        "Datta": ["datta_body.png", "datta_eyes.png", "datta_mouth.png", "datta_noodles.png", "datta_eggs.png"],
        "Eby": ["eby_body.png", "eby_eyes.png", "eby_mouth.png", "eby_tail.png"],
        "Unko": ["unko_body.png", "unko_eyes.png", "unko_mouth.png"],
    }

    layers = calques.get(personnage, [])
    current_layer = 0

    # Charger le premier calque
    current_guide = None
    try:
        current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
        current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
        current_guide.set_alpha(102)
    except Exception:
        current_guide = None

    bouton_suivant = pygame.Rect(LARGEUR - 140, HAUTEUR - 60, 120, 40)
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sauvegarder_et_quitter()
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
                    # Sauvegarde de l'état actuel du calque avant de passer au suivant
                    sauvegarder_et_quitter(current_layer)
                    send_canvas_url()

                    if current_layer < len(layers) - 1:
                        current_layer += 1
                        try:
                            current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
                            current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
                            current_guide.set_alpha(102)
                        except Exception:
                            current_guide = None
                    else:
                        dessin_finished = True  # Si c'est le dernier calque, terminer
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

# ---------- Dessin par calques multijoueur ----------
def lancer_dessin_par_calques_multijoueur(personnage, role):
    global canvas, dessin, rayon, outil, couleur_actuelle, bouton_menu, last_remote_hash, last_local_send
    dessin_finished = False

    # Définition des calques
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
        print("Aucun calque pour ce rôle ou personnage.")
        return

    current_layer = 0
    bouton_suivant = pygame.Rect(LARGEUR - 140, HAUTEUR - 60, 120, 40)

    # Charger le premier calque avec transparence
    current_guide = None
    try:
        current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
        current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
        current_guide.set_alpha(102)
    except Exception:
        current_guide = None

    # --- Zone de texte pour chat dans le bandeau ---
    input_rect = pygame.Rect(LARGEUR - 300, 20, 200, 30)
    chat_input = ""
    font_input = pygame.font.SysFont("Arial", 20)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sauvegarder_et_quitter()
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if (mods & pygame.KMOD_CTRL):
                    if event.key == pygame.K_z and undo_stack:
                        redo_stack.append(canvas.copy())
                        canvas.blit(undo_stack.pop(), (0, 0))
                    elif event.key == pygame.K_y and redo_stack:
                        undo_stack.append(canvas.copy())
                        canvas.blit(redo_stack.pop(), (0, 0))
                # --- Saisie dans la zone de texte ---
                if event.key == pygame.K_RETURN:
                    if chat_input.strip():
                        send_chat_message(chat_input.strip())
                        chat_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    chat_input = chat_input[:-1]
                else:
                    if len(chat_input) < 50 and event.unicode.isprintable():
                        chat_input += event.unicode

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
                    sauvegarder_et_quitter(current_layer)
                    send_canvas_url()
                    if current_layer < len(layers) - 1:
                        current_layer += 1
                        try:
                            current_guide = pygame.image.load(layers[current_layer]).convert_alpha()
                            current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height()))
                            current_guide.set_alpha(102)
                        except Exception:
                            current_guide = None
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

        # Palette et outils
        for rect, c in palette_rects:
            pygame.draw.rect(fenetre, c, rect)
            pygame.draw.rect(fenetre, VERT if c == couleur_actuelle else NOIR, rect, 3 if c == couleur_actuelle else 2)
        for rect, nom in outils_rects:
            survol = rect.collidepoint(mouse_pos)
            dessiner_bouton_3d(fenetre, rect, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, survol)
            fenetre.blit(icones[nom], (rect.x + 5, rect.y + 5))
            pygame.draw.rect(fenetre, VERT if nom == outil else NOIR, rect, 3 if nom == outil else 2)

        # Slider
        pygame.draw.rect(fenetre, (150, 150, 150), slider_rect)
        pygame.draw.rect(fenetre, (0, 0, 0), slider_handle)
        fenetre.blit(font.render(f"Taille: {rayon}", True, NOIR), (170, 55))

        # Menu home
        survol_menu = bouton_menu.collidepoint(mouse_pos)
        dessiner_bouton_3d(fenetre, bouton_menu, "", police, COULEUR_HAUT, COULEUR_BAS, COULEUR_TEXTE, survol_menu)
        fenetre.blit(icone_home, (bouton_menu.x + 10, bouton_menu.y + 10))
        pygame.draw.rect(fenetre, NOIR, bouton_menu, 2)

        # Bouton suivant
        if not dessin_finished:
            draw_button_and_check(fenetre, bouton_suivant, "Suivant" if current_layer < len(layers) - 1 else "Terminer", police, mouse_pos)

        # --- Affichage du rectangle de texte ---
        pygame.draw.rect(fenetre, BLANC, input_rect)
        pygame.draw.rect(fenetre, NOIR, input_rect, 2)
        txt_surface = font_input.render(chat_input, True, NOIR)
        fenetre.blit(txt_surface, (input_rect.x + 5, input_rect.y + 5))

        # Curseur de dessin
        x, y = pygame.mouse.get_pos()
        taille_curseur = rayon if y >= HAUTEUR_BANDEAU else 6
        if outil == "crayon":
            pygame.draw.circle(fenetre, couleur_actuelle, (x, y), taille_curseur)
        elif outil == "gomme":
            pygame.draw.circle(fenetre, NOIR, (x, y), taille_curseur, 1)
        elif outil == "pot":
            fenetre.blit(curseurs["pot"], (x - 12, y - 12))

        pygame.display.flip()

# ---------- Sauvegarde et sortie ----------
def sauvegarder_et_quitter(current_layer):
    try:
        # Créer un dossier pour sauvegarder les calques
        calque_dossier = os.path.join(os.path.expanduser("~"), "DrawTogether_calques")
        os.makedirs(calque_dossier, exist_ok=True)

        # Crée un fichier PNG avec un fond transparent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chemin_calque = os.path.join(calque_dossier, f"calque_{current_layer}_{timestamp}.png")

        # Sauvegarde du calque actuel avec transparence
        pygame.image.save(canvas, chemin_calque)
        print(f"Calque {current_layer} sauvegardé à : {chemin_calque}")

    except Exception as e:
        print("Erreur de sauvegarde du calque :", e)

def send_chat_message(message):
    try:
        igs.output_set_string("messageOutput", message) 
        igs.output_set_impulsion("sendImpulse_chat")         
        print(f"Message envoyé: {message}")
    except Exception as e:
        print("Erreur envoi chat:", e)

def send_canvas_url():
    try:
        # Sauvegarde du canvas en PNG
        image_path = os.path.join(os.path.expanduser("~"), "DrawTogether_canvas.png")
        pygame.image.save(canvas, image_path)

        # URL locale
        local_url = f"file:///{os.path.abspath(image_path).replace(os.sep, '/')}"

        # Envoi à Ingescape
        igs.output_set_string("imageUrl", local_url)
        igs.output_set_double("posX", 100)
        igs.output_set_double("posY", 0)
        igs.output_set_impulsion("sendImpulse_calque")         

        print(f"Canvas envoyé à Ingescape : {local_url}")

    except Exception as e:
        print("Erreur lors de l'envoi du canvas :", e)

# ---------- Lancement ----------
if __name__ == "__main__":
    try:
        menu()
    except SystemExit:
        pass
    except Exception as e:
        print("Erreur non gérée :", e)
        sauvegarder_et_quitter()
