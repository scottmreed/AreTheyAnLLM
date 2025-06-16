import os
from io import BytesIO
import requests
from PIL import Image

IMAGE_URLS = {
    "kitt": "https://github.com/user-attachments/assets/50d8e290-3936-4094-8f98-b983b4a0cdce",
    "al_gore": "https://github.com/user-attachments/assets/1e032170-d5d9-4409-a1e6-bb58c39df63e",
    "elizabeth_holmes": "https://github.com/user-attachments/assets/841a7863-b149-48d6-830b-7a5a8b403fd5",
    "james_joyce": "https://github.com/user-attachments/assets/0cf42037-23ae-4163-ba04-e84592bd7eec",
    "brain": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9e0.png",
}

README_DIR = os.path.join("images", "readme")
ICON_DIR = os.path.join("images", "icons")

os.makedirs(README_DIR, exist_ok=True)
os.makedirs(ICON_DIR, exist_ok=True)


def process_image(name, url):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content))

    half = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    half.save(os.path.join(README_DIR, f"{name}.png"))

    icon = img.resize((50, 50), Image.LANCZOS)
    icon.save(os.path.join(ICON_DIR, f"{name}.png"))

    print(f"Downloaded and processed {name}")


def main():
    for name, url in IMAGE_URLS.items():
        try:
            process_image(name, url)
        except Exception as exc:
            print(f"Could not process {name}: {exc}")


if __name__ == "__main__":
    main()
