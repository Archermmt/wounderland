import Land from "../../base/land.js"

export default class Village extends Land {
    constructor() {
        super("village")
    }

    config() {
        const root = "assets/village/";
        var config = {
            "assets": {
                "map": { "type": "tilemapTiledJSON", "path": root + "tilemap/tilemap.json" },
                "blocks": { "type": "image", "path": root + "tilemap/blocks_1.png" },
                "Room_Builder_32x32": { "type": "image", "path": root + "tilemap/Room_Builder_32x32.png" },
                "interiors_pt1": { "type": "image", "path": root + "tilemap/interiors_pt1.png" },
                "interiors_pt2": { "type": "image", "path": root + "tilemap/interiors_pt2.png" },
                "interiors_pt3": { "type": "image", "path": root + "tilemap/interiors_pt3.png" },
                "interiors_pt4": { "type": "image", "path": root + "tilemap/interiors_pt4.png" },
                "interiors_pt5": { "type": "image", "path": root + "tilemap/interiors_pt5.png" },
                "CuteRPG_Field_B": { "type": "image", "path": root + "tilemap/CuteRPG_Field_B.png" },
                "CuteRPG_Field_C": { "type": "image", "path": root + "tilemap/CuteRPG_Field_C.png" },
                "CuteRPG_Harbor_C": { "type": "image", "path": root + "tilemap/CuteRPG_Harbor_C.png" },
                "CuteRPG_Village_B": { "type": "image", "path": root + "tilemap/CuteRPG_Village_B.png" },
                "CuteRPG_Forest_B": { "type": "image", "path": root + "tilemap/CuteRPG_Forest_B.png" },
                "CuteRPG_Desert_C": { "type": "image", "path": root + "tilemap/CuteRPG_Desert_C.png" },
                "CuteRPG_Mountains_B": { "type": "image", "path": root + "tilemap/CuteRPG_Mountains_B.png" },
                "CuteRPG_Desert_B": { "type": "image", "path": root + "tilemap/CuteRPG_Desert_B.png" },
                "CuteRPG_Forest_C": { "type": "image", "path": root + "tilemap/CuteRPG_Forest_C.png" }
            },
            "config": {
                "maze": { "path": root + "maze.json" },
                "agent_base": { "path": root + "agent.json" },
                "agents": {}
            }
        }
        const agents = ["Abigail Chen", "Adam Smith", "Arthur Burton", "Ayesha Khan", "Isabella Rodriguez", "Klaus Mueller", "Maria Lopez"];
        for (const agent of agents) {
            const agent_root = root + "agents/" + agent.replace(" ", "_") + "/";
            config.assets[agent] = { "type": "atlas", "texture": agent_root + "texture.png", "sprite": root + "agents/sprite.json" };
            config.config.agents[agent] = { "path": agent_root + "agent.json" };
        }
        return config;
    }

    update() {
        super.update();
        var agent_board = this.msg.agent_board;
        var agent_update = agent_board.update;
        var agent_info = agent_board.info;
        if (agent_update) {
            if (agent_update.player) {
                this.changePlayer(agent_update.player);
            }
            if (this.player && (typeof agent_update.follow_player !== "undefined")) {
                this.maze.setFollow(this.player, agent_update.follow_player);
            }
            if (this.player && (typeof agent_update.control_player !== "undefined")) {
                this.player.setControl(agent_update.control_player);
            }
            agent_board.update = null;
        }
        if (this.player && agent_info.profile.display) {
            agent_info.profile.status = this.player.getStatus();
        }
    }

    changePlayer(name) {
        super.changePlayer(name);
        var agent_board = this.msg.agent_board;
        var agent_info = agent_board.info;
        if (this.player && agent_info.profile.display) {
            agent_info.profile["portrait"] = this.player.portrait || "";
            agent_info.profile["status"] = this.player.getStatus();
            agent_info.profile["describe"] = this.player.getDescribe();
        }
    }
}