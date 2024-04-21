import os
import shutil

src = os.path.join(os.getcwd(), "sprite.json")
for f in os.listdir():
    folder = os.path.join(os.getcwd(), f)
    if not os.path.isdir(folder):
        continue
    shutil.copy(src, os.path.join(folder, "sprite.json"))
