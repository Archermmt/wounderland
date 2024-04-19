import BaseTileMap from "../../base_tilemap.js"

export default class Village extends BaseTileMap {
    constructor() {
        super("village")
    }

    config_map() {
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
            "map_name": "village",
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
                { "name": "Exterior Decoration L2", "tileset_group": tileset_group },
                { "name": "Interior Ground", "tileset_group": tileset_group },
                { "name": "Wall", "tileset_group": ["CuteRPG_Field_C", "Room_Builder_32x32"] },
                { "name": "Interior Furniture L1", "tileset_group": tileset_group },
                { "name": "Interior Furniture L2 ", "tileset_group": tileset_group },
                { "name": "Foreground L1", "tileset_group": tileset_group, "depth": 2 },
                { "name": "Foreground L2", "tileset_group": tileset_group, "depth": 2 },
                { "name": "Collisions", "tileset_group": ["blocks"], "depth": -1, "collision": { "collide": true } }
            ],
            "players": {
                "archer": {
                    "texture": "https://mikewesthad.github.io/phaser-3-tilemap-blog-posts/post-1/assets/atlas/atlas.png",
                    "atlas": "https://mikewesthad.github.io/phaser-3-tilemap-blog-posts/post-1/assets/atlas/atlas.json",
                    "sprite": {
                        "init": "misa-right",
                        "pos": [800, 288],
                        "size": [30, 40],
                        "offset": [0, 20]
                    }
                },
                "elin": {
                    "texture": "https://mikewesthad.github.io/phaser-3-tilemap-blog-posts/post-1/assets/atlas/atlas.png",
                    "atlas": "https://mikewesthad.github.io/phaser-3-tilemap-blog-posts/post-1/assets/atlas/atlas.json",
                    "sprite": {
                        "init": "misa-left",
                        "pos": [900, 288],
                        "size": [30, 40],
                        "offset": [0, 20]
                    }
                }
            }
        }
    }
}