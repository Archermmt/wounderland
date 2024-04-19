export default class BaseTileMap extends Phaser.Scene {
    init(data) {
        this.env = data
        this.map_config = this.config_map();
        this.assets_root = data.assets_root;
        if (data.tilemap) {
            this.tilemap = data.tilemap;
        } else {
            this.tilemap = this.assets_root + "/tilemap.json";
        }
        this.zoom_factor = 1
    }

    preload() {
        // load assets and mao
        this.load.tilemapTiledJSON("map", this.tilemap);
        for (const name in this.map_config.assets) {
            this.load.image(name, this.assets_root + "/" + this.map_config.assets[name].path);
        }

        // load players
        for (const name in this.map_config.players) {
            let player = this.map_config.players[name];
            this.load.atlas(name, player.texture, player.atlas);
        }
    }

    create() {
        this.camera = this.cameras.main;
        this.camera.setBounds(0, 0, this.env.width, this.env.height);

        // create map
        const map = this.make.tilemap({ key: "map" });
        let assets = {};
        for (const name in this.map_config.assets) {
            assets[name] = map.addTilesetImage(name, name);
        }
        let layers = {};
        for (const layer of this.map_config.layers) {
            let tileset_group = []
            for (const t_name of layer.tileset_group) {
                tileset_group.push(assets[t_name]);
            }
            layers[layer.name] = map.createLayer(layer.name, tileset_group, 0, 0);
            if (layer.depth) {
                layers[layer.name].setDepth(layer.depth);
            }
            if (layer.collision) {
                layers[layer.name].setCollisionByProperty(layer.collision);
            }
        }

        // create players
        let players = {}
        for (const name in this.map_config.players) {
            let sprite = this.map_config.players[name].sprite;
            players[name] = this.physics.add.sprite(sprite.pos[0], sprite.pos[1], name, sprite.init);
            if (sprite.size) {
                players[name].setSize(sprite.size[0], sprite.size[1]);
            }
            if (sprite.offset) {
                players[name].setOffset(sprite.offset[0], sprite.offset[1]);
            }
        }

        // set events
        this.input.on("wheel", this.zoom_camera)
        this.input.on("pointermove", this.drag_camera);
    }

    zoom_camera = (pointer, gameObjects, deltaC, deltaY, deltaZ) => {
        this.zoom_factor = Math.min(Math.max(this.zoom_factor + deltaY * 0.01, 1), 10);
        this.camera.setZoom(this.zoom_factor);
    }

    drag_camera = (pointer) => {
        if (!pointer.isDown) return;
        this.camera.scrollX -= (pointer.x - pointer.prevPosition.x) / this.camera.zoom;
        this.camera.scrollY -= (pointer.y - pointer.prevPosition.y) / this.camera.zoom;
    }

}