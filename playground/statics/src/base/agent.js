import utils from "./utils.js";

export default class Agent extends Phaser.GameObjects.Sprite {
    constructor(scene, config, urls) {
        let position = [0, 0];
        if (config.position) {
            position = config.position;
        } else if (config.zone) {
            position[0] = Math.floor(Math.random() * (config.zone[0][1] - config.zone[0][0])) + config.zone[0][0];
            position[1] = Math.floor(Math.random() * (config.zone[1][1] - config.zone[1][0])) + config.zone[1][0];
        }
        super(scene, 0, 0, config.name);
        this.setPosition(position[0] + this.width / 2, position[1] + this.height / 2);
        this.scene = scene;
        this.config = config;
        this.name = config.name;
        this.urls = urls;

        // status
        this.status = { direction: "stop", speed: config.move.speed, position: position };

        // add sprite
        scene.add.existing(this);
        scene.physics.add.existing(this);
        const sprite_config = config.sprite || {};
        if (sprite_config.size) {
            this.setSize(sprite_config.size[0], sprite_config.size[1]);
        }
        if (sprite_config.offset) {
            this.setOffset(sprite_config.offset[0], sprite_config.offset[1]);
        }
        if (sprite_config.scale) {
            this.setScale(sprite_config.scale);
        }

        // add anims
        this.animations = {};
        for (const [a_key, anim] of Object.entries(config.anims)) {
            this.animations[a_key] = scene.anims.create({
                key: this.name + "." + a_key,
                frames: scene.anims.generateFrameNames(this.name, anim.frames),
                frameRate: anim.frameRate || 4,
                repeat: anim.repeat || -1
            });
        }

        // add portrait
        if (this.config.portrait) {
            this.portrait = scene.getAsset(this.config.portrait);
        }

        // set body
        const body_config = config.body || {};
        this.body.allowGravity = (body_config.gravity || true);
        this.body.immovable = !(body_config.movable || true);
        this.body.setCollideWorldBounds(true);
        this.colliders = new Set();

        // pronunciation
        var text_config = { font: Math.round(this.displayHeight * 0.6) + "px monospace" };
        this.bubble = scene.add.text(0, 0, "🦁", text_config);
        this.locateBubble();

        // set events
        if (config.interactive || true) {
            this.setInteractive();
        }
        this.setControl(false);
        this.is_thinking = false;
        this.scene.time.delayedCall(this.config.think.interval, this.action, [], this);
    }

    locateBubble() {
        this.bubble.x = this.body.position.x;
        this.bubble.y = this.body.position.y - Math.round(this.displayHeight * 0.8);
    }

    update() {
        this.locateBubble();
        if (!this.is_control) {
            return;
        }
        const cursors = this.scene.cursors;
        if (cursors.left.isDown) {
            this.move("left");
        } else if (cursors.right.isDown) {
            this.move("right");
        } else if (cursors.up.isDown) {
            this.move("up");
        } else if (cursors.down.isDown) {
            this.move("down");
        }
        if (cursors.left.isUp && cursors.right.isUp && cursors.up.isUp && cursors.down.isUp) {
            this.move("stop");
        }
    }

    action = () => {
        if (!this.is_thinking) {
            this.is_thinking = true;
            let callback = (info) => {
                if (!this.is_control) {
                    this.move(info.direct);
                }
                this.is_thinking = false;
                this.scene.time.delayedCall(this.config.think.interval, this.action, [], this);
            }
            utils.jsonRequest(this.urls.agent_think, { name: this.name, status: this.getStatus() }, callback);
        }
    }

    move(direction) {
        const curr_move = this.config.move[direction];
        this.body.setVelocity(0);
        if (direction === "stop") {
            this.anims.stop();
            const last_move = this.config.move[this.status.direction];
            if (last_move && last_move.texture) {
                this.setTexture(this.name, last_move.texture);
            }
        } else if (curr_move.anim) {
            this.anims.play(this.animations[curr_move.anim], true);
        }
        if (direction === "left") {
            this.body.setVelocityX(-this.status.speed);
        } else if (direction === "right") {
            this.body.setVelocityX(this.status.speed);
        } else if (direction === "up") {
            this.body.setVelocityY(-this.status.speed);
        } else if (direction === "down") {
            this.body.setVelocityY(this.status.speed);
        }
        this.status.direction = direction;
    }

    getStatus() {
        this.status.position = [Math.round(this.body.position.x), Math.round(this.body.position.y)];
        return this.status;
    }

    getDescribe() {
        return this.config.describe;
    }

    toString = () => {
        return this.name + "\n" + JSON.stringify(this.status);
    }

    addCollider(other) {
        if (other instanceof Agent) {
            if (this.name === other.name) {
                return false;
            }
            if (this.colliders.has(other.name) || other.colliders.has(this.name)) {
                return false;
            }
            this.colliders.add(other.name);
            other.colliders.add(this.name);
            this.scene.physics.add.collider(this, other, (agent, other) => {
                agent.move("stop");
                other.move("stop");
            });
        } else {
            this.scene.physics.add.collider(this, other, (agent, other) => {
                agent.move("stop");
            });
        }
        return true;
    }

    setControl(is_control) {
        this.is_control = is_control;
    }
}