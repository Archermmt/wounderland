class AgentStatus {
    constructor(config) {
        const move_config = config.move;
        this.controlled = false;
        this.position = config.position;
        this.direction = config.direction;
        this.speed = move_config.speed;
    }

    toString = () => {
        let tag;
        if (this.controlled) {
            tag = "[Palyer]";
        } else {
            tag = "[Free]";
        }
        return tag + "\n  position: " + this.position + "\n  direction: " + this.direction + "\n  speed: " + this.speed;
    }
}

export default class Agent extends Phaser.GameObjects.Sprite {
    constructor(scene, config) {
        super(scene, config.position[0], config.position[1], config.name)
        this.scene = scene;
        this.config = config;
        this.name = config.name;
        this.status = new AgentStatus(config);
        // add sprite
        scene.add.existing(this);
        scene.physics.add.existing(this);
        if (config.interactive || true) {
            this.setInteractive();
        }
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

        //record colliders
        this.colliders = new Set();
    }

    update() {
        if (!this.status.controlled) {
            return;
        }
        this.body.setVelocity(0);
        const move_config = this.config.move;
        const cursors = this.scene.cursors;
        if (cursors.left.isDown) {
            if (move_config.left) {
                this.anims.play(this.animations[move_config.left.anim], true);
                this.status.direction = "left";
            }
            this.body.setVelocityX(-this.status.speed);
        } else if (cursors.right.isDown) {
            if (move_config.right) {
                this.anims.play(this.animations[move_config.right.anim], true);
                this.status.direction = "right";
            }
            this.body.setVelocityX(this.status.speed);
        } else if (cursors.up.isDown) {
            if (move_config.up) {
                this.anims.play(this.animations[move_config.up.anim], true);
                this.status.direction = "up";
            }
            this.body.setVelocityY(-this.status.speed);
        } else if (cursors.down.isDown) {
            if (move_config.down) {
                this.anims.play(this.animations[move_config.down.anim], true);
                this.status.direction = "down";
            }
            this.body.setVelocityY(this.status.speed);
        }
        if (cursors.space.isDown) {
            console.log("profile: " + this);
        }
        if (cursors.left.isUp && cursors.right.isUp && cursors.up.isUp && cursors.down.isUp) {
            this.anims.stop();
        }
    }

    toString = () => {
        return "<" + this.name + ">" + this.status;
    }

    addCollider = (other) => {
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

    enableControl = () => {
        this.status.controlled = true;
    }

    disableControl = () => {
        this.status.controlled = false;
    }
}