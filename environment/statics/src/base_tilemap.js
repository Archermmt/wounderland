export default class BaseTileMap extends Phaser.Scene {
    init(data) {
        this.map_config = this.config_map()
        this.assets_root = data.assets_root
        if (data.tilemap) {
            this.tilemap = data.tilemap
        } else {
            this.tilemap = this.assets_root + "/tilemap.json"
        }
    }

    preload() {
        console.log('BaseTileMap preload with assets_root ' + this.assets_root);
        // load assets
        for (const name in this.map_config.assets) {
            let path = this.assets_root + "/" + this.map_config.assets[name].path;
            console.log("path of " + name + " -> " + path)
            this.load.image(name, this.assets_root + "/" + this.map_config.assets[name].path);
        }
        this.load.tilemapTiledJSON("map", this.tilemap);
    }

    create() {
        console.log('BaseTileMap create');
        const map = this.make.tilemap({ key: "map" });
        this.assets = {}
        for (const name in this.map_config.assets) {
            this.assets[name] = map.addTilesetImage(name, name);
        }
        console.log("assets " + this.assets)

    }
}
