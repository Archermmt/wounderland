import MapScene from "../../base/map_scene.js"

export default class Village extends MapScene {
    constructor() {
        super("village")
    }

    config() {
        return {
            "assets": {
                "map": { "type": "tilemapTiledJSON", "path": "tilemap.json" },
                "blocks": { "type": "image", "path": "tilesets/blocks_1.png" },
                "Room_Builder_32x32": { "type": "image", "path": "tilesets/Room_Builder_32x32.png" },
                "interiors_pt1": { "type": "image", "path": "tilesets/interiors_pt1.png" },
                "interiors_pt2": { "type": "image", "path": "tilesets/interiors_pt2.png" },
                "interiors_pt3": { "type": "image", "path": "tilesets/interiors_pt3.png" },
                "interiors_pt4": { "type": "image", "path": "tilesets/interiors_pt4.png" },
                "interiors_pt5": { "type": "image", "path": "tilesets/interiors_pt5.png" },
                "CuteRPG_Field_B": { "type": "image", "path": "tilesets/CuteRPG_Field_B.png" },
                "CuteRPG_Field_C": { "type": "image", "path": "tilesets/CuteRPG_Field_C.png" },
                "CuteRPG_Harbor_C": { "type": "image", "path": "tilesets/CuteRPG_Harbor_C.png" },
                "CuteRPG_Village_B": { "type": "image", "path": "tilesets/CuteRPG_Village_B.png" },
                "CuteRPG_Forest_B": { "type": "image", "path": "tilesets/CuteRPG_Forest_B.png" },
                "CuteRPG_Desert_C": { "type": "image", "path": "tilesets/CuteRPG_Desert_C.png" },
                "CuteRPG_Mountains_B": { "type": "image", "path": "tilesets/CuteRPG_Mountains_B.png" },
                "CuteRPG_Desert_B": { "type": "image", "path": "tilesets/CuteRPG_Desert_B.png" },
                "CuteRPG_Forest_C": { "type": "image", "path": "tilesets/CuteRPG_Forest_C.png" },
                "Arthur_Burton": { "type": "atlas", "texture": "roles/Arthur_Burton/texture.png", "sprite": "roles/Arthur_Burton/sprite.json" },
                "Abigail_Chen": { "type": "atlas", "texture": "roles/Abigail_Chen/texture.png", "sprite": "roles/Abigail_Chen/sprite.json" },
            },
            "scene": "scene.json",
            "roles": {
                "Arthur_Burton": "roles/Arthur_Burton/profile.json",
                "Abigail_Chen": "roles/Abigail_Chen/profile.json"
            }
        }

    }

    /*
    config_scene() {
        let tileset_group = [
            "CuteRPG_Field_B",
            "CuteRPG_Field_C",
            "CuteRPG_Harbor_C",
            "CuteRPG_Village_B",
            "CuteRPG_Forest_B",
            "CuteRPG_Desert_C",
            "CuteRPG_Mountains_B",
            "CuteRPG_Desert_B",
            "CuteRPG_Forest_C",
            "interiors_pt1",
            "interiors_pt2",
            "interiors_pt3",
            "interiors_pt4",
            "interiors_pt5",
            "Room_Builder_32x32"
        ]
        return {
            "map": {
                "assets": {
                    "blocks": { "path": "tilesets/blocks_1.png" },
                    "Room_Builder_32x32": { "path": "tilesets/Room_Builder_32x32.png" },
                    "interiors_pt1": { "path": "tilesets/interiors_pt1.png" },
                    "interiors_pt2": { "path": "tilesets/interiors_pt2.png" },
                    "interiors_pt3": { "path": "tilesets/interiors_pt3.png" },
                    "interiors_pt4": { "path": "tilesets/interiors_pt4.png" },
                    "interiors_pt5": { "path": "tilesets/interiors_pt5.png" },
                    "CuteRPG_Field_B": { "path": "tilesets/CuteRPG_Field_B.png" },
                    "CuteRPG_Field_C": { "path": "tilesets/CuteRPG_Field_C.png" },
                    "CuteRPG_Harbor_C": { "path": "tilesets/CuteRPG_Harbor_C.png" },
                    "CuteRPG_Village_B": { "path": "tilesets/CuteRPG_Village_B.png" },
                    "CuteRPG_Forest_B": { "path": "tilesets/CuteRPG_Forest_B.png" },
                    "CuteRPG_Desert_C": { "path": "tilesets/CuteRPG_Desert_C.png" },
                    "CuteRPG_Mountains_B": { "path": "tilesets/CuteRPG_Mountains_B.png" },
                    "CuteRPG_Desert_B": { "path": "tilesets/CuteRPG_Desert_B.png" },
                    "CuteRPG_Forest_C": { "path": "tilesets/CuteRPG_Forest_C.png" }
                },
                "layers": [
                    { "name": "Bottom Ground", "tileset_group": tileset_group },
                    { "name": "Exterior Ground", "tileset_group": tileset_group },
                    { "name": "Collisions", "tileset_group": ["blocks"], "collision": { "collide": true } }
                ],
                "layers_all": [
                    { "name": "Bottom Ground", "tileset_group": tileset_group },
                    { "name": "Exterior Ground", "tileset_group": tileset_group },
                    { "name": "Exterior Decoration L2", "tileset_group": tileset_group },
                    { "name": "Interior Ground", "tileset_group": tileset_group },
                    { "name": "Wall", "tileset_group": ["CuteRPG_Field_C", "Room_Builder_32x32"] },
                    { "name": "Interior Furniture L1", "tileset_group": tileset_group },
                    { "name": "Interior Furniture L2 ", "tileset_group": tileset_group },
                    { "name": "Foreground L1", "tileset_group": tileset_group, "depth": 2 },
                    { "name": "Foreground L2", "tileset_group": tileset_group, "depth": 2 },
                    { "name": "Collisions", "tileset_group": ["blocks"], "depth": -1, "collision": { "collide": true } }
                ]
            },
            "roles": {
                "archer": {
                    "is_default": true,
                    "atlas": {
                        "texture": "roles/Arthur_Burton.png",
                        "url": "roles/atlas.json",
                    },
                    "sprite": { "init": "down", "pos": [800, 288], "offset": [0, 0] },
                    "anims": {
                        "left-walk": { "frameRate": 4, "repeat": -1, "frames": { "start": 0, "end": 3, "zeroPad": 3, "prefix": "left-walk." } }
                        "right-walk": { "frameRate": 4, "repeat": -1, "frames": { "start": 0, "end": 3, "zeroPad": 3, "prefix": "right-walk." } }
                        "down-walk": { "frameRate": 4, "repeat": -1, "frames": { "start": 0, "end": 3, "zeroPad": 3, "prefix": "down-walk." } }
                        "up-walk": { "frameRate": 4, "repeat": -1, "frames": { "start": 0, "end": 3, "zeroPad": 3, "prefix": "up-walk." } }
                    },
                    "move": { "speed": 400, "left": "left-walk", "right": "right-walk", "up": "up-walk", "down": "down-walk" }
                },
                "elin": {
                    "atlas": {
                        "texture": "roles/Abigail_Chen.png",
                        "url": "roles/atlas.json",
                    },
                    "sprite": { "init": "down", "pos": [900, 288], "offset": [0, 0] },
                    "anims": { "speed": 400 }
                }
            },
            "camera": { "zoom_init": 1, "zoom_range": [0.5, 10, 0.01] }
        }
    }
    */
}