import Maze from "./maze.js"
import Agent from "./agent.js"
import utils from "./utils.js";

export default class Land extends Phaser.Scene {
    init(data) {
        this.msg = data;
        this.assets_root = data.assets_root;
        this.urls = data.urls;
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
                for (const a_name of this.msg.agents) {
                    this.game_config[name][a_name] = config[a_name];
                    this.load.json('config.agent.' + a_name, this.getAsset(config[a_name].path));
                }
            } else {
                this.game_config[name] = config;
                this.load.json('config.' + name, this.getAsset(config.path));
            }
        }
        // start game
        this.game_status = { start: false };
        let callback = (info) => {
            this.game_status = info;
            if (this.game_status.start) {
                for (const agent of Object.values(this.agents)) {
                    agent.think();
                }
            }
        }
        utils.jsonRequest(this.urls.start_game, this.game_config, callback);
        // update time
        this.getTime();
    }

    create() {
        // create maze
        const maze_config = this.cache.json.get('config.maze');
        this.maze = new Maze(this, maze_config);

        // create agent
        this.agents = {};
        const agent_base_config = this.cache.json.get("config.agent_base");
        for (const name of this.msg.agents) {
            const agent_config = utils.recursiveUpdate(agent_base_config, this.cache.json.get("config.agent." + name));
            this.agents[name] = new Agent(this, agent_config, maze_config.tile_size, this.msg.urls);
            for (const agent of Object.values(this.agents)) {
                this.agents[name].addCollider(agent);
            }
        }
        // add colliders
        for (const layer of Object.values(this.maze.layers)) {
            if (layer.info.collision) {
                for (const agent of Object.values(this.agents)) {
                    agent.addCollider(layer.layer);
                }
            }
        }
        // change player
        this.changePlayer(this.msg.agents[this.msg.agents.length - 1]);

        // set events
        this.cursors = this.input.keyboard.createCursorKeys()
        this.input.on('gameobjectdown', this.objClicked);
        this.on_config = false;
    }

    update() {
        if (this.game_status.start) {
            for (const agent of Object.values(this.agents)) {
                agent.move();
            }
        }
        this.configPlayer();
        if (this.cursors.space.isDown && !this.on_config) {
            this.on_config = true;
        }
        if (this.cursors.space.isUp && this.on_config) {
            console.log("debugging...");
            this.on_config = false;
        }
    }

    getTime = () => {
        var time = this.msg.user.time;
        let callback = (info) => {
            time.current = info.time;
            this.time.delayedCall(Math.round(1600 / time.rate), this.getTime, [], this);
        }
        let time_config = time.update;
        utils.jsonRequest(this.urls.get_time, time_config, callback);
        if (Object.keys(time.update).length > 0) {
            time.update = {};
        }
    }

    configPlayer() {
        var player = this.msg.player;
        if (Object.keys(player.update).length > 0) {
            if (player.update.player) {
                this.changePlayer(player.update.player);
            }
            if (this.player && (typeof player.update.follow !== "undefined")) {
                this.maze.setFollow(this.player, player.update.follow);
            }
            if (this.player && (typeof player.update.control !== "undefined")) {
                this.player.setControl(player.update.control);
            }
            player.update = {};
        }
        if (this.player) {
            this.player.updateMsg(this.msg.agent);
        }
    }

    changePlayer(name) {
        if (this.player) {
            this.player.setControl(false);
            this.maze.setFollow(this.player, false);
        }
        this.player = this.agents[name];
        this.maze.locate(this.player);
        this.msg.player.portrait = this.player.portrait || "";
        this.msg.agent.profile.scratch = utils.textBlock(this.player.getScratch());
    }

    objClicked = (pointer, obj) => {
        if (obj instanceof Agent) {
            this.changePlayer(obj.name);
        }
    }

    getAsset(path) {
        var abs_path = path;
        if (abs_path.startsWith("http")) {
            return abs_path;
        }
        return this.assets_root + "/" + abs_path;
    }
}