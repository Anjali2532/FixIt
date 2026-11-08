"""Check uploaded images and store a clean copy with a generated name."""

from io import BytesIO
from pathlib import Path
import uuid
import warnings

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_PIXELS = 20_000_000


def photo_path(name):
    if not name or len(name) != 36 or not name.endswith(".jpg"):
        return None
    try:
        int(name[:32], 16)
    except ValueError:
        return None
    return Path(current_app.config["UPLOAD_FOLDER"]) / name


def save_photo(upload):
    data = upload.stream.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES:
        raise ValueError(
            "This photo is too large (maximum 5 MB). Please choose a smaller image."
        )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Only JPG, PNG, or WEBP images can be uploaded.")
                if image.width * image.height > MAX_PHOTO_PIXELS:
                    raise ValueError(
                        "This image has too many pixels. Please choose an image under 20 megapixels."
                    )
                image.verify()
            with Image.open(BytesIO(data)) as image:
                image = ImageOps.exif_transpose(image)
                image.load()
                clean = Image.new("RGB", image.size, "white")
                if "A" in image.getbands():
                    clean.paste(image.convert("RGB"), mask=image.getchannel("A"))
                else:
                    clean.paste(image.convert("RGB"))
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ValueError("This file is not a valid JPG, PNG, or WEBP image.") from error
    name = uuid.uuid4().hex + ".jpg"
    path = photo_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            clean.save(output, format="JPEG", quality=85)
        path.chmod(0o600)
    except OSError:
        path.unlink(missing_ok=True)
        raise
    return name


def remove_photo(name):
    path = photo_path(name)
    if path:
        path.unlink(missing_ok=True)
