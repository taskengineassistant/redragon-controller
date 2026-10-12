# Create icon placeholder
from PIL import Image, ImageDraw

img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.ellipse([20, 20, 236, 236], fill=(255, 0, 0, 255))
draw.text((95, 85), 'R', fill=(255, 255, 255, 255), font_size=140)
img.save('assets/redragon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
print("Created assets/redragon.ico")