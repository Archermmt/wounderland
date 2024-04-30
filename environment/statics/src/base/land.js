import tileMapCreator from "./tilemap.js"
import LandCamera from "./camera.js"
import { Agent, AgentBoard } from "./agent.js"

export default class Land extends Phaser.Scene {
    current_player = "unknown";
    new_player = "unknown";
    init(data) {
        this.env = data;
        this.assets_root = data.assets_root;
    }

    preload() {
        this.on_debug = false;
        this.config = this.config();
        // load assets
        for (const [name, asset] of Object.entries(this.config.assets)) {
            if (asset.type == "tilemapTiledJSON") {
                this.load.tilemapTiledJSON(name, this.getAsset(asset.path));
            } else if (asset.type == "image") {
                this.load.image(name, this.getAsset(asset.path));
            } else if (asset.type == "atlas") {
                this.load.atlas(name, this.getAsset(asset.texture), this.getAsset(asset.sprite));
            }
        }
        // load config
        this.load.json('config.land', this.getAsset(this.config.land));
        if (this.config.agent_common) {
            this.load.json('config.agent_common', this.getAsset(this.config.agent_common));
        }
        for (const [name, profile] of Object.entries(this.config.agents)) {
            this.load.json("config.agent." + name, this.getAsset(profile));
        }
    }

    create() {
        const land_config = this.cache.json.get('config.land');
        const map_creator = new tileMapCreator(this, land_config.map);
        this.map = map_creator.create();

        // create agent
        this.agents = {};
        var agent_names = [];
        const common_config = this.cache.json.get("config.agent_common");
        for (const name of Object.keys(this.config.agents)) {
            let agent_config = this.cache.json.get("config.agent." + name);
            if (common_config) {
                agent_config = { ...common_config, ...agent_config }
            }
            agent_names.push(name);
            this.agents[name] = new Agent(this, agent_config);
            for (const agent of Object.values(this.agents)) {
                this.agents[name].addCollider(agent);
            }
        }
        // add colliders
        for (const [name, layer] of Object.entries(map_creator.layers)) {
            if (layer.info.collision) {
                for (const agent of Object.values(this.agents)) {
                    agent.addCollider(layer.layer);
                }
            }
        }

        // create camera
        this.camera = new LandCamera(this, land_config.camera);

        // create agent board
        this.agent_board = new AgentBoard(this);
        this.env.agents = agent_names;

        // set events
        this.cursors = this.input.keyboard.createCursorKeys()
        this.input.on('gameobjectdown', this.objClicked);

        // change player
        this.changePlayer(agent_names[0]);
    }

    update() {
        for (const agent of Object.values(this.agents)) {
            agent.update();
        }
        if (this.cursors.space.isDown) {
            this.on_debug = true;
        }
        if (this.cursors.space.isUp && this.on_debug) {
            this.debug();
            this.on_debug = false;
        }
        if (this.env.update_info) {
            if (this.env.update_info.player) {
                this.changePlayer(this.env.update_info.player);
            }
            if (this.player && (typeof this.env.update_info.follow_player !== "undefined")) {
                this.camera.setFollow(this.player, this.env.update_info.follow_player);
            }
            if (this.player && (typeof this.env.update_info.control_player !== "undefined")) {
                this.player.setControl(this.env.update_info.control_player);
            }
            this.env.update_info = null;
        }
        if (this.player && this.env.display.profile) {
            this.env.player.profile.status = this.player.getStatus();
        }
    }

    getAsset(path) {
        var abs_path = path;
        if (abs_path.startsWith("http")) {
            return abs_path;
        }
        return this.assets_root + "/" + abs_path;
    }

    debug = () => {
        for (const agent of Object.values(this.agents)) {
            console.log(agent.toString());
        }
    }

    changePlayer = (name) => {
        if (this.player) {
            this.player.setControl(false);
            this.camera.setFollow(this.player, false);
        }
        this.player = this.agents[name];
        this.camera.locate(this.player);
        this.env.player["name"] = this.player.name;
        this.env.player["profile"] = {
            "portrait": this.player.portrait_path,
            "status": this.player.getStatus(),
            "describe": this.player.getDescribe()
        }
        console.log("Change player to " + this.player);
    }

    objClicked = (pointer, obj) => {
        if (obj instanceof Agent) {
            this.changePlayer(obj.name);
        }
    }

}