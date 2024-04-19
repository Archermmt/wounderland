import BaseTileMap from "../../base_tilemap.js"

export default class Village extends BaseTileMap {
    constructor() {
        super("village")
    }

    config_map() {
        return {
            "map_name": "village",
            "assets": {
                "blocks": {
                    "path": "tilesets/blocks_1.png"
                },
                "Room_Builder_32x32": {
                    "path": "tilesets/Room_Builder_32x32.png"
                },
                "interiors_pt1": {
                    "path": "tilesets/interiors_pt1.png"
                },
                "interiors_pt2": {
                    "path": "tilesets/interiors_pt2.png"
                },
                "interiors_pt3": {
                    "path": "tilesets/interiors_pt3.png"
                },
                "interiors_pt4": {
                    "path": "tilesets/interiors_pt4.png"
                },
                "interiors_pt5": {
                    "path": "tilesets/interiors_pt5.png"
                },
                "CuteRPG_Field_B": {
                    "path": "tilesets/CuteRPG_Field_B.png"
                },
                "CuteRPG_Field_C": {
                    "path": "tilesets/CuteRPG_Field_C.png"
                },
                "CuteRPG_Harbor_C": {
                    "path": "tilesets/CuteRPG_Harbor_C.png"
                },
                "CuteRPG_Village_B": {
                    "path": "tilesets/CuteRPG_Village_B.png"
                },
                "CuteRPG_Forest_B": {
                    "path": "tilesets/CuteRPG_Forest_B.png"
                },
                "CuteRPG_Desert_C": {
                    "path": "tilesets/CuteRPG_Desert_C.png"
                },
                "CuteRPG_Mountains_B": {
                    "path": "tilesets/CuteRPG_Mountains_B.png"
                },
                "CuteRPG_Desert_B": {
                    "path": "tilesets/CuteRPG_Desert_B.png"
                },
                "CuteRPG_Forest_C": {
                    "path": "tilesets/CuteRPG_Forest_C.png"
                }
            },
            "layers": [
                {
                    "name": "Bottom Ground",
                    "tileset": [
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
                }
            ]
        }
    }
}