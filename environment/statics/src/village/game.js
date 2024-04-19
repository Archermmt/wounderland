import Village from './scenes/village.js'

const config = {
    type: Phaser.AUTO,
    pixelArt: true,
    scale: {
        parent: env.parent,
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
        width: env.width,
        height: env.height
    },
    scene: Village,
    physics: {
        default: "arcade",
        arcade: {
            debug: true,
        }
    }
}

const game = new Phaser.Game(config);
game.scene.start("village", env)