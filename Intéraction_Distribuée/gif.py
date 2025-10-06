from PIL import Image, ImageSequence, ImageDraw, ImageFilter
import numpy as np

# --- paramètres ---
menu_path = "menu.png"  # ton image de menu
map_path = "map.png"    # ton image de map
output_path = "transition.gif"
duration = 2000  # durée totale en ms
fps = 30
frames = int(fps * (duration / 1000))

# --- charger les images ---
menu = Image.open(menu_path).convert("RGB")
map_img = Image.open(map_path).convert("RGB")
width, height = menu.size

# --- créer les frames ---
frames_list = []
for i in range(frames):
    progress = i / frames
    # position verticale : monte du menu vers la map
    y_offset = int(height * progress)

    # mélange entre menu et map (fondu doux)
    blended = Image.blend(menu, map_img, progress)

    # créer calque de nuages
    cloud_layer = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(cloud_layer)
    for _ in range(20):
        cx = np.random.randint(0, width)
        cy = np.random.randint(0, height)
        r = np.random.randint(50, 150)
        alpha = np.random.randint(80, 150)
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(255, 255, 255, alpha))
    cloud_layer = cloud_layer.filter(ImageFilter.GaussianBlur(10))

    # composer l’image
    frame = blended.copy()
    frame = frame.filter(ImageFilter.GaussianBlur(progress * 2))  # effet vitesse
    frame.paste(cloud_layer, (0, int(-y_offset/2)), cloud_layer)

    frames_list.append(frame)

# --- sauvegarder le GIF ---
frames_list[0].save(
    output_path,
    save_all=True,
    append_images=frames_list[1:],
    duration=int(duration/frames),
    loop=0,
)

print("✅ GIF généré :", output_path)
