"""Rebuild the fork's original MIT-licensed weather icon (requires Pillow)."""

from pathlib import Path

from PIL import Image, ImageDraw


def build() -> None:
    """Render one original drawing at both Home Assistant icon sizes."""
    factor = 4
    image = Image.new("RGBA", (256 * factor, 256 * factor))
    draw = ImageDraw.Draw(image)

    def box(values):
        return tuple(round(value * factor) for value in values)

    # Sun behind a cloud, three rain streaks. No provider or HA trademarks.
    draw.ellipse(box((124, 8, 236, 120)), fill="#F4B942")
    cloud = "#E9F2F6"
    edge = "#193D52"
    draw.rounded_rectangle(box((8, 96, 248, 184)), radius=40 * factor, fill=edge)
    draw.ellipse(box((38, 52, 160, 174)), fill=edge)
    draw.ellipse(box((126, 80, 218, 172)), fill=edge)
    draw.rounded_rectangle(box((18, 106, 238, 174)), radius=30 * factor, fill=cloud)
    draw.ellipse(box((48, 62, 150, 164)), fill=cloud)
    draw.ellipse(box((136, 90, 208, 162)), fill=cloud)
    draw.rectangle(box((62, 112, 196, 166)), fill=cloud)
    for x in (76, 128, 180):
        draw.line(box((x + 8, 200, x - 8, 240)), fill="#167FAD", width=12 * factor)
        for y, offset in ((200, 8), (240, -8)):
            draw.ellipse(box((x + offset - 6, y - 6, x + offset + 6, y + 6)), fill="#167FAD")

    # A square trimmed subject avoids padding and stays consistent at both sizes.
    image = image.crop(image.getbbox())
    side = max(image.size)
    square = Image.new("RGBA", (side, side))
    square.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    output = Path(__file__).resolve().parents[1] / "custom_components/meteoswiss/brand"
    output.mkdir(parents=True, exist_ok=True)
    for filename, size in (("icon.png", 256), ("icon@2x.png", 512)):
        square.resize((size, size), Image.Resampling.LANCZOS).save(output / filename, optimize=True)


if __name__ == "__main__":
    build()
