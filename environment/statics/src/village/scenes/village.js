import Land from "../../base/land.js"

export default class Village extends Land {
    constructor() {
        super("village")
    }

    config() {
        var config = {
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
                "CuteRPG_Forest_C": { "type": "image", "path": "tilemap/CuteRPG_Forest_C.png" }
            },
            "land": "land.json",
            "agent_common": "persona.json",
            "agents": {}
        }
        const agents = ["Abigail_Chen", "Adam_Smith", "Arthur_Burton", "Ayesha_Khan"];
        for (const agent of agents) {
            config.assets[agent] = { "type": "atlas", "texture": "agents/" + agent + "/texture.png", "sprite": "agents/sprite.json" };
            config.assets[agent + ".portrait"] = { "type": "image", "path": "agents/" + agent + "/portrait.png" };
            config.agents[agent] = "agents/" + agent + "/persona.json";
        }
        return config;
    }

    update() {
        super.update();
        if (this.env.update) {
            if (this.env.update.player) {
                this.changePlayer(this.env.update.player);
            }
            if (this.player && (typeof this.env.update.follow_player !== "undefined")) {
                this.camera.setFollow(this.player, this.env.update.follow_player);
            }
            if (this.player && (typeof this.env.update.control_player !== "undefined")) {
                this.player.setControl(this.env.update.control_player);
            }
            this.env.update = null;
        }
        if (this.player && this.env.display.profile) {
            this.env.player.profile.status = this.player.getStatus();
        }
    }

    changePlayer(name) {
        super.changePlayer(name);
        this.env.player["name"] = this.player.name;
        this.env.player["profile"] = {
            "portrait": this.player.portrait_path,
            "status": this.player.getStatus(),
            "describe": this.player.getDescribe()
        }
    }
}