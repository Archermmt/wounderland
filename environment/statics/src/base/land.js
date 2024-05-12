import { TileMapCreator, MazeCamera } from "./utils.js"
import Agent from "./agent.js"

export default class Land extends Phaser.Scene {
    init(data) {
        this.env = data;
        this.assets_root = data.assets_root;
    }

    preload() {
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
        this.game_config = {};
        for (const [name, config] of Object.entries(this.config.config)) {
            if (name == "agents") {
                this.game_config[name] = {};
                for (const a_name of this.env.agents) {
                    this.game_config[name][a_name] = config[a_name];
                    this.load.json('config.agent.' + a_name, this.getAsset(config[a_name].path));
                }
            } else {
                this.game_config[name] = config;
                this.load.json('config.' + name, this.getAsset(config.path));
            }
        }
    }

    create() {
        const maze_config = this.cache.json.get('config.maze');
        const map_creator = new TileMapCreator(this, maze_config.map);
        this.map = map_creator.create();

        // create agent
        this.agents = {};
        const agent_base_config = this.cache.json.get("config.agent_base");
        for (const name of this.env.agents) {
            let agent_config = this.cache.json.get("config.agent." + name);
            if (agent_base_config) {
                agent_config = { ...agent_base_config, ...agent_config }
            }
            this.agents[name] = new Agent(this, agent_config, this.env.urls);
            this.game_config["agents"][name].status = this.agents[name].getStatus();
            for (const agent of Object.values(this.agents)) {
                this.agents[name].addCollider(agent);
            }
        }
        // add colliders
        for (const layer of Object.values(map_creator.layers)) {
            if (layer.info.collision) {
                for (const agent of Object.values(this.agents)) {
                    agent.addCollider(layer.layer);
                }
            }
        }

        // create camera
        this.camera = new MazeCamera(this, maze_config.camera);

        // change player
        this.changePlayer(this.env.agents[this.env.agents.length - 1]);

        // start retrieve
        this.game_status = { start: false };
        var land = this;
        var xobj = new XMLHttpRequest();
        xobj.overrideMimeType("application/json");
        xobj.onreadystatechange = function () {
            if (xobj.readyState == XMLHttpRequest.DONE) {
                land.game_status = JSON.parse(xobj.responseText);
            }
        }
        xobj.open('POST', this.env.urls.start_game, true);
        xobj.send(JSON.stringify(this.game_config));

        // set events
        this.cursors = this.input.keyboard.createCursorKeys()
        this.input.on('gameobjectdown', this.objClicked);
        this.on_config = false;
    }

    update() {
        if (this.game_status.start) {
            for (const agent of Object.values(this.agents)) {
                agent.update();
            }
        }
        if (this.cursors.space.isDown && !this.on_config) {
            this.on_config = true;
        }
        if (this.cursors.space.isUp && this.on_config) {
            this.configUser();
            this.on_config = false;
        }
    }

    getAsset(path) {
        var abs_path = path;
        if (abs_path.startsWith("http")) {
            return abs_path;
        }
        return this.assets_root + "/" + abs_path;
    }

    configUser = () => {
        console.log("calling configUser");
    }

    changePlayer(name) {
        if (this.player) {
            this.player.setControl(false);
            this.camera.setFollow(this.player, false);
        }
        this.player = this.agents[name];
        this.camera.locate(this.player);
    }

    objClicked = (pointer, obj) => {
        if (obj instanceof Agent) {
            this.changePlayer(obj.name);
        }
    }

}