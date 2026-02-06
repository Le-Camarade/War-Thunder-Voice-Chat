"""Generate icon.ico from the project logo PNG."""

from PIL import Image

LOGO_PATH = "wt_radio_logo.png"
ICO_PATH = "icon.ico"
SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

img = Image.open(LOGO_PATH)
img.save(ICO_PATH, format="ICO", sizes=SIZES)
print(f"Generated {ICO_PATH} from {LOGO_PATH} ({len(SIZES)} sizes: {', '.join(f'{s[0]}x{s[1]}' for s in SIZES)})")
