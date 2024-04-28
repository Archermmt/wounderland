import os
import json
import shutil

ga_root = "/Users/tongmeng/Desktop/Codes/generative_agents/environment/frontend_server/static_dirs/assets"
profile_folder = os.path.join(ga_root, "characters/profile")

for f in os.listdir():
    folder = os.path.join(os.getcwd(), f)
    if not os.path.isdir(folder):
        continue
    # os.remove(os.path.join(folder, "sprite.json"))
    # shutil.copy(src, os.path.join(folder, "sprite.json"))
    """
    with open(os.path.join(folder, "profile.json"), "w") as profile_f:
        profile_f.write(json.dumps({"name": f}, indent=2))
    """
    src_path = os.path.join(folder, "profile.json")
    dst_path = os.path.join(folder, "persona.json")
    if os.path.isfile(src_path):
        shutil.move(src_path, dst_path)
