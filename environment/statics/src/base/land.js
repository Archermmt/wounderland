import create_map from "./tilemap.js"
import SceneCamera from "./camera.js"
import Agent from "./agent.js"

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
        const map = create_map(this, land_config.map);
        this.camera = new SceneCamera(this, land_config.camera, map);

        // create agent
        this.agents = {}
        const common_config = this.cache.json.get("config.agent_common");
        for (const name of Object.keys(this.config.agents)) {
            let agent_config = this.cache.json.get("config.agent." + name);
            if (common_config) {
                agent_config = { ...common_config, ...agent_config }
            }
            this.agents[name] = new Agent(this, agent_config);
            for (const agent of Object.values(this.agents)) {
                this.agents[name].addCollider(agent);
            }
        }
        this.changePlayer(land_config.player);

        // set events
        this.cursors = this.input.keyboard.createCursorKeys()
        this.input.on('gameobjectdown', this.objClicked);
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
            this.player.disableControl();
        }
        this.player = this.agents[name];
        this.player.enableControl();
        this.camera.startFollow(this.player);
    }

    objClicked = (pointer, obj) => {
        if (obj instanceof Agent) {
            console.log("Change player to " + obj);
            this.changePlayer(obj.name);
        }
    }

}