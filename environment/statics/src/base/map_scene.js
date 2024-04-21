import MapFactory from "./map_factory.js"
import SceneCamera from "./scene_camera.js"

export default class MapScene extends Phaser.Scene {
    init(data) {
        this.env = data;
        this.assets_root = data.assets_root;
    }

    preload() {
        this.config = this.config();
        // load assets
        for (const [name, asset] of Object.entries(this.config.assets)) {
            if (asset.type == "tilemapTiledJSON") {
                this.load.tilemapTiledJSON(name, this.get_asset(asset.path));
            } else if (asset.type == "image") {
                this.load.image(name, this.get_asset(asset.path));
            } else if (asset.type == "atlas") {
                this.load.atlas(name, this.get_asset(asset.texture), this.get_asset(asset.sprite));
            }
        }
        // load config
        this.load.json('config.scene', this.get_asset(this.config.scene));
        for (const [name, profile] of Object.entries(this.config.roles)) {
            this.load.json("config." + name, this.get_asset(profile));
        }
    }

    create() {
        const scene_config = this.cache.json.get('config.scene');
        const map = MapFactory.create(this, scene_config.map);

        // create roles
        this.roles = {}
        for (const name of Object.keys(this.config.roles)) {
            const role_config = this.cache.json.get("config." + name);
            const sprite = role_config.sprite;
            this.roles[name] = this.physics.add.sprite(sprite.pos[0], sprite.pos[1], name, sprite.init).setCollideWorldBounds(true);
            if (sprite.size) {
                this.roles[name].setSize(sprite.size[0], sprite.size[1]);
            }
            if (sprite.offset) {
                this.roles[name].setOffset(sprite.offset[0], sprite.offset[1]);
            }
            if (sprite.scale) {
                this.roles[name].setScale(sprite.scale);
            }
            // add anims
            for (const [a_key, anim] of Object.entries(role_config.anims)) {
                this.anims.create({
                    key: name + "." + a_key,
                    frames: this.anims.generateFrameNames(name, anim.frames),
                    frameRate: anim.frameRate || 4,
                    repeat: anim.repeat || -1
                });
            }

            // set body
            const body = role_config.body || {};
            this.roles[name].body.allowGravity = (body.gravity || true);
            this.roles[name].body.immovable = !(body.movable || true);

            if (role_config.is_default) {
                this.player = this.roles[name];
            }
        }

        // add collision
        for (const [name, role] of Object.entries(this.roles)) {
            for (const [o_name, other] of Object.entries(this.roles)) {
                if (o_name == name) {
                    continue;
                }
                this.physics.add.collider(role, other, (role, other) => {
                    role.body.setVelocity(0);
                    other.body.setVelocity(0);
                }, null, this);
            }
        }

        // add camera
        this.camera = new SceneCamera(this, scene_config.camera, map, this.player);

        // set cursors
        this.cursors = this.input.keyboard.createCursorKeys()
    }

    update() {
        const player_velocity = 400;
        this.player.body.setVelocity(0);
        if (this.cursors.left.isDown) {
            this.player.anims.play("Abigail_Chen.left-walk", true);
            this.player.body.setVelocityX(-player_velocity);
        } else if (this.cursors.right.isDown) {
            this.player.anims.play("Abigail_Chen.right-walk", true);
            this.player.body.setVelocityX(player_velocity);
        } else if (this.cursors.up.isDown) {
            this.player.anims.play("Abigail_Chen.up-walk", true);
            this.player.body.setVelocityY(-player_velocity);
        } else if (this.cursors.down.isDown) {
            this.player.anims.play("Abigail_Chen.down-walk", true);
            this.player.body.setVelocityY(player_velocity);
        }
        if (this.cursors.left.isUp && this.cursors.right.isUp && this.cursors.up.isUp && this.cursors.down.isUp) {
            this.player.anims.stop();
        }
    }

    get_asset = (path) => {
        var abs_path = path;
        if (abs_path.startsWith("http")) {
            return abs_path;
        }
        return this.assets_root + "/" + abs_path;
    }

}