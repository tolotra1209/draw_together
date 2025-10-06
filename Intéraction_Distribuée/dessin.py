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
pygame.display.set_caption("Draw Together") 

# --- Couleurs --- 
NOIR, BLANC, GRIS, VERT = (0,0,0), (255,255,255), (200,200,200), (0,255,0) 
MARRON_FONCE = (101, 67, 33) 
COULEURS_BASE = [(0,0,0),(255,0,0),(0,255,0),(0,0,255),(255,255,0),(255,165,0),(255,192,203),(255,255,255)] 

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
slider_handle = pygame.Rect(10 + rayon*2, 55, 10, 20) 
slider_drag = False 

# --- Palette couleurs --- 
palette_rects = [] 
for i, c in enumerate(COULEURS_BASE): 
    rect = pygame.Rect(10 + i*40, 10, 30, 30) 
    palette_rects.append((rect, c)) 
    
# --- Outils --- 
outils = ["crayon","pot","gomme"] 
outils_rects = [] 
for i, nom in enumerate(outils): 
    rect = pygame.Rect(400 + i*60, 10, 50,50) 
    outils_rects.append((rect,nom)) 

icones = {
    "crayon": pygame.transform.scale(pygame.image.load("pencil.png"), (40,40)), 
    "pot": pygame.transform.scale(pygame.image.load("paint.png"), (40,40)), 
    "gomme": pygame.transform.scale(pygame.image.load("eraser.png"), (40,40))
} 
curseurs = {"pot": pygame.transform.scale(pygame.image.load("paint.png"), (24,24))} 
icone_home = pygame.transform.scale(pygame.image.load("home.png"), (30,30)) 
bouton_menu = pygame.Rect(400 + len(outils)*140, 10, 50, 50)

pygame.mouse.set_visible(True) 
font = pygame.font.SysFont(None, 32) 

# --- Flood fill --- 
def flood_fill(surface,x,y,target_color,replacement_color): 
    if target_color == replacement_color: 
        return 
    pile = deque() 
    pile.append((x,y)) 
    largeur,hauteur = surface.get_size() 
    while pile: 
        nx,ny = pile.popleft() 
        if nx<0 or ny<0 or nx>=largeur or ny>=hauteur: 
            continue 
        if surface.get_at((nx,ny))!=target_color: 
            continue 
        surface.set_at((nx,ny),replacement_color) 
        pile.extend([(nx+1,ny),(nx-1,ny),(nx,ny+1),(nx,ny-1)]) 

# --- Animation de transition (GIF) ---
def jouer_transition():
    transition = pygame.image.load("transition.gif")
    clock = pygame.time.Clock()

    try:
        # Récupère toutes les frames du GIF
        frames = []
        frame_durations = []
        frame_count = transition.get_num_frames()
        for i in range(frame_count):
            transition.seek(i)
            frame = transition.copy()
            frame = pygame.transform.scale(frame, (LARGEUR, HAUTEUR))
            frames.append(frame)
            # Durée d'affichage de chaque frame (par défaut ~33 ms si non défini)
            frame_durations.append(getattr(transition.info, "duration", 33))
    except:
        # fallback si pygame ne gère qu'une frame
        frames = [pygame.transform.scale(transition, (LARGEUR, HAUTEUR))]
        frame_durations = [2000]

    # Joue toutes les frames
    for i, frame in enumerate(frames):
        fenetre.blit(frame, (0, 0))
        pygame.display.flip()
        clock.tick(30)  # 30 FPS environ

    # Petite pause de sécurité
    pygame.time.wait(200)

# --- Menu principal --- 
def menu(): 
    global canvas 
    bouton_jouer = pygame.Rect(LARGEUR//2-100, 300, 200, 50) 
    bouton_quitter = pygame.Rect(LARGEUR//2-100, 400, 200, 50) 

    fond_menu = pygame.transform.scale(pygame.image.load("menu.png"), (LARGEUR, HAUTEUR)) 
    logo = pygame.transform.scale(pygame.image.load("logo.png"), (200, 150)) 

    in_menu = True 
    while in_menu: 
        fenetre.blit(fond_menu, (0, 0)) 
        fenetre.blit(logo, (LARGEUR//2 - 100, 100))

        pygame.draw.rect(fenetre, BLANC, bouton_jouer) 
        pygame.draw.rect(fenetre, NOIR, bouton_jouer, 2) 
        pygame.draw.rect(fenetre, BLANC, bouton_quitter) 
        pygame.draw.rect(fenetre, NOIR, bouton_quitter, 2) 
    
        fenetre.blit(font.render("Jouer", True, MARRON_FONCE), (LARGEUR//2-35, 310)) 
        fenetre.blit(font.render("Quitter", True, MARRON_FONCE), (LARGEUR//2-40, 410)) 
    
        pygame.mouse.set_visible(True) 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                pygame.quit() 
                exit() 
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x,y = event.pos 
                if bouton_jouer.collidepoint(x,y): 
                    canvas.fill(BLANC)  
                    in_menu = False 
                    jouer_transition()
                    afficher_carte()
                elif bouton_quitter.collidepoint(x,y): 
                    pygame.quit() 
                    exit() 
        pygame.display.flip() 

# --- Affichage de la carte des niveaux ---
def afficher_carte():
    global canvas

    # Chargement de l'image de carte
    carte = pygame.transform.scale(pygame.image.load("map.png"), (LARGEUR, HAUTEUR))
    bouton_retour = pygame.Rect(20, 20, 120, 40)

    # Positions approximatives des ronds (à ajuster ensuite)
    niveaux = [
        {"pos": (231, 550), "actif": True},   # Niveau 1 actif
        {"pos": (671, 432), "actif": False},  # Niveau 2 inactif
        {"pos": (292, 314), "actif": False},  # Niveau 3 inactif
        {"pos": (739, 200), "actif": False},  # Niveau 4 inactif
        {"pos": (456, 204), "actif": False},  # Niveau 5 inactif
    ]

    en_carte = True
    pygame.mouse.set_visible(True)
    while en_carte:
        fenetre.blit(carte, (0, 0))
        
        # Bouton retour
        pygame.draw.rect(fenetre, BLANC, bouton_retour)
        pygame.draw.rect(fenetre, NOIR, bouton_retour, 2)
        fenetre.blit(font.render("Retour", True, NOIR), (bouton_retour.x + 15, bouton_retour.y + 5))

        # Dessin des ronds des niveaux
        for i, niv in enumerate(niveaux):
            couleur = (0, 255, 0) if niv["actif"] else (150, 150, 150)
            pygame.draw.circle(fenetre, couleur, niv["pos"], 15)
            pygame.draw.circle(fenetre, NOIR, niv["pos"], 2)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos

                # Bouton retour
                if bouton_retour.collidepoint(x, y):
                    menu()
                    return

                # Détection clic sur niveau
                for niv in niveaux:
                    nx, ny = niv["pos"]
                    if (x - nx) ** 2 + (y - ny) ** 2 <= 15 ** 2:  # Clic dans le cercle
                        if niv["actif"]:
                            personnage_choisi = selection_dessin()
                            lancer_dessin_par_calques(personnage_choisi)
                            return

# --- Sélection du dessin --- 
def selection_dessin(): 
    images = ["datta.png", "eby.png", "unko.png"] 
    noms = ["Datta", "Eby", "Unko"] 
    rects = [] 
    decal_x = 100 
    y_pos = 200 
    largeur_img, hauteur_img = 150, 150 
    for i, img in enumerate(images): 
        rect = pygame.Rect(decal_x + i*250, y_pos, largeur_img, hauteur_img) 
        rects.append(rect) 
        
    images_surfaces = [pygame.transform.scale(pygame.image.load(img), (largeur_img, hauteur_img)) for img in images] 
    fond_choice = pygame.transform.scale(pygame.image.load("choice.png"), (LARGEUR, HAUTEUR)) 
    
    selection = True 
    pygame.mouse.set_visible(True) 
    while selection: 
        fenetre.blit(fond_choice, (0,0)) 
        
        titre = font.render("Quel personnage dessiner ?", True, NOIR) 
        fenetre.blit(titre, ((LARGEUR - titre.get_width())//2, 50)) 
        
        for i, rect in enumerate(rects): 
            pygame.draw.rect(fenetre, BLANC, rect) 
            pygame.draw.rect(fenetre, MARRON_FONCE, rect, 3) 
            fenetre.blit(images_surfaces[i], (rect.x, rect.y)) 
            texte = font.render(noms[i], True, MARRON_FONCE) 
            texte_rect = pygame.Rect(rect.x, rect.y + hauteur_img + 5, largeur_img, texte.get_height() + 4) 
            pygame.draw.rect(fenetre, BLANC, texte_rect) 
            pygame.draw.rect(fenetre, MARRON_FONCE, texte_rect, 2) 
            fenetre.blit(texte, (texte_rect.x + (largeur_img - texte.get_width())//2, texte_rect.y + 2)) 
            
        pygame.display.flip() 
        
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                pygame.quit() 
                exit() 
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos 
                for i, rect in enumerate(rects): 
                    if rect.collidepoint(x,y): 
                        return noms[i] 
                    
# --- Dessin par calques --- 
def lancer_dessin_par_calques(personnage): 
    global canvas, dessin, rayon, outil, couleur_actuelle, bouton_menu 
    dessin_finished = False 

    calques = {
        "Datta": ["datta_body.png","datta_eyes.png","datta_mouth.png","datta_noodles.png","datta_eggs.png"], 
        "Eby": ["eby_body.png","eby_eyes.png","eby_mouth.png","eby_tail.png"], 
        "Unko": ["unko_body.png","unko_eyes.png","unko_mouth.png"]
    } 
    layers = calques.get(personnage, []) 
    current_layer = 0 

    bouton_suivant = pygame.Rect(LARGEUR-140, HAUTEUR-60, 120, 40) 

    # --- Calque-guide (non dessinable) --- 
    current_guide = None
    if layers: 
        current_guide = pygame.image.load(layers[current_layer]).convert_alpha() 
        current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height())) 
        current_guide.set_alpha(102) 
        
        running = True 
        while running: 
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: 
                    pygame.quit() 
                    exit() 
                elif event.type==pygame.KEYDOWN: 
                    mods = pygame.key.get_mods() 
                    if (mods & pygame.KMOD_CTRL): 
                        if event.key==pygame.K_z and undo_stack: 
                            redo_stack.append(canvas.copy()) 
                            canvas.blit(undo_stack.pop(), (0,0))
                        elif event.key==pygame.K_y and redo_stack: 
                            undo_stack.append(canvas.copy()) 
                            canvas.blit(redo_stack.pop(), (0,0)) 
                elif event.type==pygame.MOUSEBUTTONDOWN: 
                    x,y = event.pos 
                    clique_interface = False 
                    if y < HAUTEUR_BANDEAU: 
                        for rect,c in palette_rects: 
                            if rect.collidepoint(x,y): 
                                couleur_actuelle = c 
                                outil = "crayon" 
                                clique_interface = True 
                        for rect,nom in outils_rects: 
                            if rect.collidepoint(x,y): 
                                outil = nom 
                                clique_interface = True 
                        if slider_rect.collidepoint(x,y): 
                            slider_handle.x = max(slider_rect.left,min(slider_rect.right-10,x)) 
                            rayon = int((slider_handle.x - slider_rect.left)/2)+1 
                            slider_drag = True 
                            clique_interface = True 
                        if bouton_menu.collidepoint(x,y): 
                            canvas.fill(BLANC) 
                            menu() 
                            return 
                    # --- Bouton Suivant / Terminer --- 
                    if not dessin_finished and bouton_suivant.collidepoint(x,y): 
                        if current_layer < len(layers)-1: 
                            current_layer +=1 
                            current_guide = pygame.image.load(layers[current_layer]).convert_alpha() 
                            current_guide = pygame.transform.scale(current_guide, (canvas.get_width(), canvas.get_height())) 
                            current_guide.set_alpha(102) 
                        else: 
                            dessin_finished = True 
                    # --- Dessin (si pas sur interface ni sur le bouton suivant) --- 
                    if (not clique_interface and not dessin_finished and 
                        y >= HAUTEUR_BANDEAU and not bouton_suivant.collidepoint(x,y)): 
                        save_state() 
                        dessin = True 
                        if outil=="crayon": 
                            pygame.draw.circle(canvas, couleur_actuelle, (x, y-HAUTEUR_BANDEAU), rayon) 
                        elif outil=="gomme": 
                            pygame.draw.circle(canvas, BLANC, (x, y-HAUTEUR_BANDEAU), rayon) 
                        elif outil=="pot": 
                            target_color = canvas.get_at((x, y-HAUTEUR_BANDEAU)) 
                            flood_fill(canvas, x, y-HAUTEUR_BANDEAU, target_color, couleur_actuelle) 
                            save_state() 
                elif event.type==pygame.MOUSEBUTTONUP: 
                    dessin=False 
                    slider_drag=False 
                elif event.type==pygame.MOUSEMOTION: 
                    x,y = event.pos 
                    if dessin and not dessin_finished and y>=HAUTEUR_BANDEAU and not bouton_suivant.collidepoint(x,y): 
                        if outil=="crayon": 
                            pygame.draw.circle(canvas, couleur_actuelle, (x,y-HAUTEUR_BANDEAU),rayon) 
                        elif outil=="gomme": 
                            pygame.draw.circle(canvas,BLANC,(x,y-HAUTEUR_BANDEAU),rayon) 
                    if slider_drag: 
                        slider_handle.x = max(slider_rect.left,min(slider_rect.right-10,x)) 
                        rayon = int((slider_handle.x - slider_rect.left)/2)+1 
                    
            # --- AFFICHAGE --- 
            fenetre.fill(GRIS) 
            fenetre.blit(canvas,(0,HAUTEUR_BANDEAU)) 
            # superposition du guide 
            if current_guide and not dessin_finished: 
                fenetre.blit(current_guide,(0,HAUTEUR_BANDEAU)) 
            
            pygame.draw.rect(fenetre,(180,180,180),(0,0,LARGEUR,HAUTEUR_BANDEAU)) 
            
            # Palette 
            for rect,c in palette_rects: 
                pygame.draw.rect(fenetre,c,rect) 
                pygame.draw.rect(fenetre,VERT if c==couleur_actuelle else NOIR,rect,3 if c==couleur_actuelle else 2) 
            # Outils 
            for rect,nom in outils_rects: 
                pygame.draw.rect(fenetre,BLANC,rect) 
                fenetre.blit(icones[nom],(rect.x+5,rect.y+5)) 
                pygame.draw.rect(fenetre,VERT if nom==outil else NOIR, rect,3 if nom==outil else 2) 
            # Slider 
            pygame.draw.rect(fenetre,(150,150,150),slider_rect) 
            pygame.draw.rect(fenetre,(0,0,0),slider_handle) 
            fenetre.blit(font.render(f"Taille: {rayon}",True,NOIR),(170,55)) 
            # Menu 
            pygame.draw.rect(fenetre, BLANC, bouton_menu) 
            fenetre.blit(icone_home, (bouton_menu.x+10, bouton_menu.y+10)) 
            pygame.draw.rect(fenetre, NOIR, bouton_menu, 2) 
            # Suivant / Terminer 
            if not dessin_finished: 
                pygame.draw.rect(fenetre, VERT, bouton_suivant) 
                texte_btn = font.render("Suivant" if current_layer < len(layers)-1 else "Terminer", True, NOIR) 
                fenetre.blit(texte_btn, (bouton_suivant.x+10, bouton_suivant.y+5)) 
            # Curseur 
            x,y = pygame.mouse.get_pos() 
            taille_curseur = rayon if y >= HAUTEUR_BANDEAU else 6 
            if outil=="crayon": 
                pygame.draw.circle(fenetre, couleur_actuelle, (x, y), taille_curseur) 
            elif outil=="gomme": 
                pygame.draw.circle(fenetre, NOIR, (x, y), taille_curseur, 1) 
            elif outil=="pot": 
                fenetre.blit(curseurs["pot"], (x-12, y-12)) 
            pygame.display.flip() 
        
# --- Lancement --- 
menu() 
pygame.quit()
