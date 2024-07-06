import utils from "./utils.js";

function coordToPosition(coord, tile_size) {
    return [coord[0] * tile_size, coord[1] * tile_size];
}

function positionToCoord(position, tile_size) {
    return [Math.floor(position[0] / tile_size), Math.floor(position[1] / tile_size)];
}

export default class Agent extends Phaser.GameObjects.Sprite {
    constructor(scene, config, tile_size, urls, broadcast_agents) {
        super(scene, 0, 0, config.name);
        let coord = [0, 0];
        if (config.coord) {
            coord = config.coord;
        } else if (config.zone) {
            coord[0] = Math.floor(Math.random() * (config.zone[0][1] - config.zone[0][0])) + config.zone[0][0];
            coord[1] = Math.floor(Math.random() * (config.zone[1][1] - config.zone[1][0])) + config.zone[1][0];
        }
        const position = coordToPosition(coord, tile_size);
        this.setPosition(position[0] + tile_size / 2, position[1] + tile_size / 2);
        this.scene = scene;
        this.config = config;
        this.tile_size = tile_size;
        this.name = config.name;
        this.urls = urls;
        this.broadcast_agents = broadcast_agents;

        // status
        this.status = { state: "init", currently: config.currently, direction: "stop", speed: config.move.speed, coord: coord, address: "", path: [] };
        this.info = { associate: {}, chats: [], concepts: {}, actions: {}, schedule: {}, llm: {} };

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
        this.text_config = {
            font: Math.round(this.displayHeight * 0.6) + "px monospace", fill: "#000000",
            padding: { x: 4, y: 4 }
        };
        this.bubbles[this.name] = scene.add.text(0, 0, "🦁", this.text_config);

        // set events
        if (config.interactive || true) {
            this.setInteractive();
        }
        this.setControl(false);

        // flag for think
        this.enable_think = false;
        this.enable_move = true;
        this.thinking = false;
    }

    enableThink = () => {
        this.enable_think = true;
    }

    think = () => {
        if (this.enable_think && !this.thinking) {
            this.enable_think = false;
            this.status.state = "think";
            let callback = (info) => {
                const plan = info.plan;
                this.status.path = plan.path;
                this.broadcast_agents(true);
                if (this.status.path.length > 0) {
                    this.status.state = "move";
                } else {
                    this.status.state = "action";
                }
                for (const [name, emoji] of Object.entries(plan.emojis)) {
                    if (!(name in this.bubbles)) {
                        let pos = coordToPosition(emoji.coord, this.tile_size);
                        pos[1] = pos[1] - Math.round(this.displayHeight * 0.8) - 4;
                        this.bubbles[name] = this.scene.add.text(pos[0], pos[1], emoji.emoji, this.text_config);
                    }
                    this.bubbles[name].setText(emoji.emoji);
                }
                for (const [key, value] of Object.entries(info.info)) {
                    if (key in this.info) {
                        this.info[key] = value;
                    } else if (key in this.status) {
                        this.status[key] = value;
                    }
                }
                this.thinking = false;
                this.scene.time.delayedCall(this.config.think.interval, this.enableThink, [], this);
            }
            this.thinking = true;
            this.broadcast_agents(false);
            utils.jsonRequest(this.urls.agent_think, { name: this.name, status: this.getStatus() }, callback);
        }
    }

    move() {
        this.bubbles[this.name].x = this.body.position.x;
        this.bubbles[this.name].y = this.body.position.y - Math.round(this.displayHeight * 0.8) - 4;
        if (!this.is_control) {
            if (this.status.path.length > 0 && this.enable_move) {
                let next_pos = coordToPosition(this.status.path[0], this.tile_size);
                if (this.body.position.x == next_pos[0] && this.body.position.y == next_pos[1]) {
                    this.status.path = this.status.path.slice(1);
                    if (this.status.path.length > 0) {
                        next_pos = coordToPosition(this.status.path[0], this.tile_size);
                    } else {
                        next_pos = [];
                    }
                }
                if (next_pos.length > 0) {
                    this.positionMove(next_pos);
                } else {
                    this.status.state = "action";
                }
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

    updateMsg(msg) {
        if (msg.display.profile) {
            msg.profile.status = utils.textBlock(this.getStatus());
        } else if (msg.display.memory) {
            msg.memory.associate = utils.textBlock(this.info.associate);
            msg.memory.chats = this.info.chats;
        } else if (msg.display.percept) {
            msg.percept.concepts = utils.textBlock(this.info.concepts);
        } else if (msg.display.plan) {
            msg.plan.actions = utils.textBlock(this.info.actions);
            msg.plan.schedule = utils.textBlock(this.info.schedule);
        } else if (msg.display.stat) {
            msg.stat.llm = utils.textBlock(this.info.llm);
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
        const step = this.tile_size / 20;
        if (position[0] < this.body.position.x) {
            direction = "left";
            this.body.position.x -= Math.min(step, this.body.position.x - position[0]);
        } else if (position[0] > this.body.position.x) {
            direction = "right";
            this.body.position.x += Math.min(step, position[0] - this.body.position.x);
        } else if (position[1] < this.body.position.y) {
            direction = "up";
            this.body.position.y -= Math.min(step, this.body.position.y - position[1]);
        } else if (position[1] > this.body.position.y) {
            direction = "down";
            this.body.position.y += Math.min(step, position[1] - this.body.position.y);
        }
        this.setMoveAnim(direction);
    }

    getStatus() {
        this.status.coord = positionToCoord([this.body.position.x, this.body.position.y], this.tile_size);
        return this.status;
    }

    getScratch() {
        return this.config.scratch;
    }

    getInfo(key) {
        return this.info[key];
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
                if (agent.is_control) {
                    agent.directionMove("stop");
                    //other.directionMove("stop");
                }
            });
        } else {
            this.scene.physics.add.collider(this, other, (agent, other) => {
                if (agent.is_control) {
                    agent.directionMove("stop");
                }
            });
        }
        return true;
    }

    setControl(is_control) {
        this.is_control = is_control;
    }
}