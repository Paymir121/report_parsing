"""
Создаёт favicon.ico и icon.ico для exe из logo_dc.svg (иконка приложения).
Использует cairosvg для конвертации SVG в PNG, затем PIL для ICO.
Если cairosvg недоступен — создаёт простую синюю иконку (#007AFF).
"""
import os
import sys

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BUILD_DIR)
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
ICONS_DIR = os.path.join(STATIC_DIR, "icons")
# Иконка приложения: exe, установщик, окно браузера, трей
LOGO_SVG = os.path.join(ICONS_DIR, "logo_dc.svg")
FAVICON_ICO = os.path.join(STATIC_DIR, "favicon.ico")
BUILD_ICON_ICO = os.path.join(BUILD_DIR, "icon.ico")


def create_ico_from_svg():
    """Конвертирует logo_dc.svg в ICO через cairosvg + PIL."""
    try:
        import cairosvg
        from PIL import Image
        import io
    except ImportError:
        return False
    if not os.path.isfile(LOGO_SVG):
        return False
    try:
        png_data = cairosvg.svg2png(
            url=LOGO_SVG,
            output_width=256,
            output_height=256,
        )
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
        img.save(FAVICON_ICO, format="ICO", sizes=sizes)
        img.save(BUILD_ICON_ICO, format="ICO", sizes=sizes)
        return True
    except Exception:
        return False


def create_simple_ico():
    """Создаёт простую синюю иконку (#007AFF) — hexagon-подобная форма."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    color = (0, 122, 255, 255)  # #007AFF
    w, h = 256, 256
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margin = w // 8
    d.polygon(
        [(margin, h // 2), (w // 4, margin), (3 * w // 4, margin),
         (w - margin, h // 2), (3 * w // 4, h - margin), (w // 4, h - margin)],
        fill=color, outline=color,
    )
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    img.save(FAVICON_ICO, format="ICO", sizes=sizes)
    img.save(BUILD_ICON_ICO, format="ICO", sizes=sizes)
    return True


def main():
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    if create_ico_from_svg():
        print("ICO создан из logo_dc.svg")
    elif create_simple_ico():
        print("Создана простая ICO-иконка (cairosvg не найден)")
    else:
        print("Не удалось создать иконку (установите Pillow)")
        sys.exit(1)


if __name__ == "__main__":
    main()
