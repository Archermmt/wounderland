class AgentStatus {
    constructor(config) {
        const move_config = config.move;
        this.controlled = false;
        this.direction = config.direction;
        this.speed = move_config.speed;
        this.think_time = config.think_time || 1000;
        this.percept = config.percept;
        this.plan = config.plan;
    }

    toString = () => {
        let str = "  movement: " + this.direction + " X " + this.speed;
        if (this.controlled) {
            str += "\n  action: controlled";
        } else {
            str += "\n  action: percept+plan / " + this.think_time + " ms";
            str += "\n  percept: " + JSON.stringify(this.percept);
            str += "\n  plan: " + JSON.stringify(this.plan);
        }
        return str
    }
}

export default class Agent extends Phaser.GameObjects.Sprite {
    constructor(scene, config) {
        let position = [0, 0];
        if (config.position) {
            position = config.position;
        } else if (config.zone) {
            position[0] = Math.floor(Math.random() * (config.zone[0][1] - config.zone[0][0])) + config.zone[0][0];
            position[1] = Math.floor(Math.random() * (config.zone[1][1] - config.zone[1][0])) + config.zone[1][0];
        }
        super(scene, position[0], position[1], config.name)
        this.scene = scene;
        this.config = config;
        this.name = config.name;
        this.status = new AgentStatus(config);
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

        // set body
        const body_config = config.body || {};
        this.body.allowGravity = (body_config.gravity || true);
        this.body.immovable = !(body_config.movable || true);
        this.body.setCollideWorldBounds(true);

        // set events
        if (config.interactive || true) {
            this.setInteractive();
        }
        scene.time.delayedCall(this.status.think_time, this.action, [], this);

        //record colliders
        this.colliders = new Set();
    }

    update() {
        if (!this.status.controlled) {
            return;
        }
        this.body.setVelocity(0);
        const cursors = this.scene.cursors;
        if (cursors.left.isDown) {
            this.moveTo("left");
        } else if (cursors.right.isDown) {
            this.moveTo("right");
        } else if (cursors.up.isDown) {
            this.moveTo("up");
        } else if (cursors.down.isDown) {
            this.moveTo("down");
        }
        if (cursors.left.isUp && cursors.right.isUp && cursors.up.isUp && cursors.down.isUp) {
            this.anims.stop();
        }
    }

    toString = () => {
        return this.name + " @ " + Math.round(this.body.position.x) + "," + Math.round(this.body.position.y) + "\n" + this.status;
    }

    moveTo(direction) {
        const move_config = this.config.move;
        this.status.direction = direction;
        if (direction === "left") {
            if (move_config.left) {
                this.anims.play(this.animations[move_config.left.anim], true);
            }
            this.body.setVelocityX(-this.status.speed);
        } else if (direction === "right") {
            if (move_config.right) {
                this.anims.play(this.animations[move_config.right.anim], true);
            }
            this.body.setVelocityX(this.status.speed);
        } else if (direction === "up") {
            if (move_config.up) {
                this.anims.play(this.animations[move_config.up.anim], true);
            }
            this.body.setVelocityY(-this.status.speed);
        } else if (direction === "down") {
            if (move_config.down) {
                this.anims.play(this.animations[move_config.down.anim], true);
            }
            this.body.setVelocityY(this.status.speed);
        }
    }

    percept = () => {
        return "";
    }

    plan = (observation) => {
        let direct;
        if (this.status.plan.mode === "random") {
            const directs = ["left", "right", "up", "down", "stop"];
            direct = directs[Math.floor(Math.random() * directs.length)];
        }
        return direct;
    }

    action = () => {
        if (this.status.controlled) {
            return;
        }
        const observation = this.percept();
        const direct = this.plan(observation);
        this.body.setVelocity(0);
        if (direct === "stop") {
            this.anims.stop();
        } else {
            this.moveTo(direct);
        }
        this.scene.time.delayedCall(this.status.think_time, this.action, [], this);
    }

    addCollider(other) {
        if (this.name == other.name) {
            return false;
        }
        if (this.colliders.has(other.name) || other.colliders.has(this.name)) {
            return false;
        }
        this.colliders.add(other.name);
        other.colliders.add(this.name);
        this.scene.physics.add.collider(this, other, (agent, other) => {
            agent.body.setVelocity(0);
            other.body.setVelocity(0);
        }, null, this);
        return true;
    }

    enableControl() {
        this.status.controlled = true;
    }

    disableControl = () => {
        this.status.controlled = false;
        this.scene.time.delayedCall(this.status.think_time, this.action, [], this);
    }
}