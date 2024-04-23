import MapFactory from "./factory.js"
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
        this.load.json('config.scene', this.getAsset(this.config.scene));
        if (this.config.role_common) {
            this.load.json('config.role_common', this.getAsset(this.config.role_common));
        }
        for (const [name, profile] of Object.entries(this.config.roles)) {
            this.load.json("config.role." + name, this.getAsset(profile));
        }
    }

    create() {
        const scene_config = this.cache.json.get('config.scene');
        const map = MapFactory.create(this, scene_config.map);
        this.camera = new SceneCamera(this, scene_config.camera, map);
        // create roles
        this.roles = {}
        const common_config = this.cache.json.get("config.role_common");
        for (const name of Object.keys(this.config.roles)) {
            let role_config = this.cache.json.get("config.role." + name);
            if (common_config) {
                role_config = { ...common_config, ...role_config }
            }
            this.roles[name] = new Agent(this, role_config);
            for (const role of Object.values(this.roles)) {
                this.roles[name].addCollider(role);
            }
        }
        this.changePlayer(scene_config.player);

        // set events
        this.cursors = this.input.keyboard.createCursorKeys()
        this.input.on('gameobjectdown', (pointer, obj) => {
            if (obj instanceof Agent) {
                console.log("Change player to " + obj);
                this.changePlayer(obj.name);
            }
        });
    }

    update() {
        for (const role of Object.values(this.roles)) {
            role.update();
        }
    }

    getAsset(path) {
        var abs_path = path;
        if (abs_path.startsWith("http")) {
            return abs_path;
        }
        return this.assets_root + "/" + abs_path;
    }

    changePlayer(name) {
        if (this.player) {
            this.player.disableControl();
        }
        this.player = this.roles[name];
        this.player.enableControl();
        this.camera.startFollow(this.player);
    }

}