import Land from "../../base/land.js"

export default class Village extends Land {
    constructor() {
        super("village")
    }

    config() {
        return {
            "assets": {
                "map": { "type": "tilemapTiledJSON", "path": "tilemap/tilemap.json" },
                "blocks": { "type": "image", "path": "tilemap/blocks_1.png" },
                "Room_Builder_32x32": { "type": "image", "path": "tilemap/Room_Builder_32x32.png" },
                "interiors_pt1": { "type": "image", "path": "tilemap/interiors_pt1.png" },
                "interiors_pt2": { "type": "image", "path": "tilemap/interiors_pt2.png" },
                "interiors_pt3": { "type": "image", "path": "tilemap/interiors_pt3.png" },
                "interiors_pt4": { "type": "image", "path": "tilemap/interiors_pt4.png" },
                "interiors_pt5": { "type": "image", "path": "tilemap/interiors_pt5.png" },
                "CuteRPG_Field_B": { "type": "image", "path": "tilemap/CuteRPG_Field_B.png" },
                "CuteRPG_Field_C": { "type": "image", "path": "tilemap/CuteRPG_Field_C.png" },
                "CuteRPG_Harbor_C": { "type": "image", "path": "tilemap/CuteRPG_Harbor_C.png" },
                "CuteRPG_Village_B": { "type": "image", "path": "tilemap/CuteRPG_Village_B.png" },
                "CuteRPG_Forest_B": { "type": "image", "path": "tilemap/CuteRPG_Forest_B.png" },
                "CuteRPG_Desert_C": { "type": "image", "path": "tilemap/CuteRPG_Desert_C.png" },
                "CuteRPG_Mountains_B": { "type": "image", "path": "tilemap/CuteRPG_Mountains_B.png" },
                "CuteRPG_Desert_B": { "type": "image", "path": "tilemap/CuteRPG_Desert_B.png" },
                "CuteRPG_Forest_C": { "type": "image", "path": "tilemap/CuteRPG_Forest_C.png" },
                "Abigail_Chen": { "type": "atlas", "texture": "agents/Abigail_Chen/texture.png", "sprite": "agents/sprite.json" },
                "Adam_Smith": { "type": "atlas", "texture": "agents/Adam_Smith/texture.png", "sprite": "agents/sprite.json" },
                "Arthur_Burton": { "type": "atlas", "texture": "agents/Arthur_Burton/texture.png", "sprite": "agents/sprite.json" },
                "Ayesha_Khan": { "type": "atlas", "texture": "agents/Ayesha_Khan/texture.png", "sprite": "agents/sprite.json" },
            },
            "land": "land.json",
            "agent_common": "agent.json",
            "agents": {
                "Abigail_Chen": "agents/Abigail_Chen/profile.json",
                "Adam_Smith": "agents/Adam_Smith/profile.json",
                "Arthur_Burton": "agents/Arthur_Burton/profile.json",
                "Ayesha_Khan": "agents/Ayesha_Khan/profile.json",
            }
        }
    }
}