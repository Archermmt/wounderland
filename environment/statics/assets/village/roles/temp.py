import os
import json
import shutil

src = os.path.join(os.getcwd(), "sprite.json")
for f in os.listdir():
    folder = os.path.join(os.getcwd(), f)
    if not os.path.isdir(folder):
        continue
    # os.remove(os.path.join(folder, "sprite.json"))
    # shutil.copy(src, os.path.join(folder, "sprite.json"))
    with open(os.path.join(folder, "profile.json"), "w") as profile_f:
        profile_f.write(json.dumps({"name": f}, indent=2))
