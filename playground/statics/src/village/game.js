import Village from './scenes/village.js'

const config = {
    type: Phaser.AUTO,
    pixelArt: true,
    scale: {
        parent: msg.parent,
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
        width: window.innerWidth,
        height: window.innerHeight,
    },
    dom: {
        createContainer: true
    },
    scene: Village,
    physics: {
        default: "arcade",
        arcade: {
            debug: false,
        }
    }
}

const game = new Phaser.Game(config);
game.scene.start("village", msg);