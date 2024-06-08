import utils from "./utils.js";

function coordToPosition(coord, tile_size) {
    return (coord[0] * tile_size + tile_size / 2, coord[1] * tile_size + tile_size / 2);
}

function positionToCoord(position, tile_size) {
    return (Math.floor(position[0] / tile_size), Math.floor(position[1] / tile_size));
}



export default class Agent extends Phaser.GameObjects.Sprite {
    constructor(scene, config, tile_size, urls) {
        super(scene, 0, 0, config.name);
        let coord = [0, 0];
        if (config.coord) {
            coord = config.coord;
        } else if (config.zone) {
            coord[0] = Math.floor(Math.random() * (config.zone[0][1] - config.zone[0][0])) + config.zone[0][0];
            coord[1] = Math.floor(Math.random() * (config.zone[1][1] - config.zone[1][0])) + config.zone[1][0];
        }
        const position = coordToPosition(coord, tile_size);
        this.setPosition(position[0], position[1]);
        this.scene = scene;
        this.config = config;
        this.tile_size = tile_size;
        this.name = config.name;
        this.urls = urls;

        // status
        this.status = { direction: "stop", speed: config.move.speed, coord: coord, path: [] };

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

        // emoji
        this.bubbles = {};
        this.text_config = { font: Math.round(this.displayHeight * 0.6) + "px monospace" };
        this.bubbles["agent"] = scene.add.text(0, 0, "🦁", this.text_config);

        // set events
        if (config.interactive || true) {
            this.setInteractive();
        }
        this.setControl(false);
        this.is_thinking = false;
        this.scene.time.delayedCall(this.config.think.interval, this.action, [], this);
    }

    update() {
        this.bubbles["agent"].x = this.body.position.x;
        this.bubbles["agent"].y = this.body.position.y - Math.round(this.displayHeight * 0.8);
        if (!this.is_control) {
            if (this.status.path) {
                let next_pos = coordToPosition(this.status.path[0], this.tile_size);
                if (this.body.position.x == next_pos[0] && this.body.position.y == next_pos[1]) {
                    this.status.path = this.status.path.slice(1);
                    next_pos = coordToPosition(this.status.path[0], this.tile_size);
                }
                this.positionMove(next_pos);
            }
            return;
        }
        const cursors = this.scene.cursors;
        if (cursors.left.isDown) {
            this.directionMove("left");
        } else if (cursors.right.isDown) {
            this.directionMove("right");
        } else if (cursors.up.isDown) {
            this.directionMove("up");
        } else if (cursors.down.isDown) {
            this.directionMove("down");
        }
        if (cursors.left.isUp && cursors.right.isUp && cursors.up.isUp && cursors.down.isUp) {
            this.directionMove("stop");
        }
    }

    action = () => {
        if (!this.is_thinking) {
            this.is_thinking = true;
            let callback = (info) => {
                this.status.path = info.path;
                for (const [name, emoji] of Object.entries(info.emojis)) {
                    if (!this.bubbles.hasOwnProperty(name)) {
                        let e_pos = emoji.coord;
                        e_pos = [e_pos[0] * self.tile_size, e_pos[1] * self.tile_size];
                        this.bubbles["agent"] = scene.add.text(e_pos[0], e_pos[1], "", this.text_config);
                    }
                    if (emoji.text == "") {
                        this.bubbles[name].setVisable(false);
                    } else {
                        this.bubbles[name].setVisable(true);
                        this.bubbles[name].setText(emoji.text);
                    }
                }
                this.is_thinking = false;
                this.scene.time.delayedCall(this.config.think.interval, this.action, [], this);
            }
            utils.jsonRequest(this.urls.agent_think, { name: this.name, status: this.getStatus() }, callback);
        }
    }

    setMoveAnim(direction) {
        const curr_move = this.config.move[direction];
        if (direction === "stop") {
            this.anims.stop();
            const last_move = this.config.move[this.status.direction];
            if (last_move && last_move.texture) {
                this.setTexture(this.name, last_move.texture);
            }
        } else if (curr_move.anim) {
            this.anims.play(this.animations[curr_move.anim], true);
        }
        this.status.direction = direction;
    }

    directionMove(direction) {
        this.setMoveAnim(direction);
        this.body.setVelocity(0);
        if (direction === "left") {
            this.body.setVelocityX(-this.status.speed);
        } else if (direction === "right") {
            this.body.setVelocityX(this.status.speed);
        } else if (direction === "up") {
            this.body.setVelocityY(-this.status.speed);
        } else if (direction === "down") {
            this.body.setVelocityY(this.status.speed);
        }
    }

    positionMove(position) {
        let direction = "stop";
        if (position[0] < self.body.position.x) {
            direction = "left";
        } else if (position[0] > self.body.position.x) {
            direction = "right";
        } else if (position[1] < self.body.position.y) {
            direction = "up";
        } else if (position[1] > self.body.position.y) {
            direction = "down";
        }
        this.setMoveAnim(direction);
        this.moveTo(position[0], position[1], this.status.speed);
    }

    getStatus() {
        this.status.coord = positionToCoord([this.body.position.x, this.body.position.y], self.tile_size);
        return this.status;
    }

    getScratch() {
        return this.config.scratch;
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