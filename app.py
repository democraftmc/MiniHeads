import requests
from PIL import Image, ImageDraw
from flask import Flask, send_file, request, render_template
import io

app = Flask(__name__)

def download_skin(uuid):
    """Download Minecraft avatar skin using mc-heads.net API."""
    url = f"https://api.creepernation.net/raw/{uuid}?size=64"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        return Image.open(response.raw).convert("RGBA")
    else:
        raise Exception("Failed to download skin")

def extract_head(skin):
    """Extract the head (8x8) and top head (8x8) from the skin."""
    head = skin.crop((8, 8, 16, 16))  # Head
    top_head = skin.crop((39, 6, 49, 16))  # Top head
    return head, top_head

def create_avatar(head, top_head):
    """Create a 12x12 image and place the head and top head with an outline."""
    canvas = Image.new("RGBA", (12, 12), (0, 0, 0, 0))

    # Paste top head at (0,0) and head at (1,1)
    canvas.paste(head, (2, 2), head)
    canvas.paste(top_head, (1, 1), top_head)
    
    # Draw black outline
    draw = ImageDraw.Draw(canvas)
    outline_color = (0, 0, 0, 255)
    for x in range(12):
        for y in range(12):
            if canvas.getpixel((x, y))[3] != 0 and canvas.getpixel((x - 1, y))[3] == 0 and canvas.getpixel((x, y)) != (0, 0, 0, 255):  # If not transparent
                draw.point((x - 1, y), outline_color)
            if x < 11:
                if canvas.getpixel((x, y))[3] != 0 and canvas.getpixel((x + 1, y))[3] == 0 and canvas.getpixel((x, y)) != (0, 0, 0, 255):  # If not transparent
                    draw.point((x + 1, y), outline_color)
            if canvas.getpixel((x, y))[3] != 0 and canvas.getpixel((x, y - 1))[3] == 0 and canvas.getpixel((x, y)) != (0, 0, 0, 255):  # If not transparent
                draw.point((x, y - 1), outline_color)
            if y < 11:
                if canvas.getpixel((x, y))[3] != 0 and canvas.getpixel((x, y + 1))[3] == 0 and canvas.getpixel((x, y)) != (0, 0, 0, 255):  # If not transparent
                    draw.point((x, y + 1), outline_color)

    return canvas

def upscale_image(image, scale=16):
    """Upscale the image by a factor of scale."""
    new_size = (image.width * scale, image.height * scale)
    return image.resize(new_size, Image.NEAREST)


@app.route("/")
def home():
    """Render the home page with the input form."""
    username = request.args.get("username")
    if username:
        avatar_url = f"/avatar/{username}"
        return render_template("index.html", username=username, avatar_url=avatar_url)
    return render_template("index.html", username=None)

@app.route("/avatar/<uuid>")
def generate_avatar(uuid):
    """Flask route to generate and serve an avatar."""
    try:
        skin = download_skin(uuid)
        head, top_head = extract_head(skin)
        avatar = create_avatar(head, top_head)
        upscaled_avatar = upscale_image(avatar, 16)

        # Save to a BytesIO buffer and send as response
        img_io = io.BytesIO()
        upscaled_avatar.save(img_io, "PNG")
        img_io.seek(0)
        return send_file(img_io, mimetype="image/png")
    
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)