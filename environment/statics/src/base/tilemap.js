export default class tileMapCreator {
    constructor(scene, config) {
        this.scene = scene;
        this.config = config;
    }

    create() {
        this.map = this.scene.make.tilemap({ key: this.config.asset });
        this.scene.physics.world.setBounds(0, 0, this.map.widthInPixels, this.map.heightInPixels);
        let tilesets = {};
        let group_assets = (assets) => {
            for (const asset of assets) {
                if (asset in tilesets) continue;
                tilesets[asset] = this.map.addTilesetImage(asset, asset);
            }
            let tileset_group = [];
            for (const asset of assets) {
                tileset_group.push(tilesets[asset]);
            }
            return tileset_group;
        }

        this.layers = {}
        for (const layer_info of this.config.layers) {
            let tileset_names;
            if (typeof layer_info.tileset_group === "string") {
                tileset_names = this.config.tileset_groups[layer_info.tileset_group];
            } else {
                tileset_names = layer_info.tileset_group;
            }
            const tileset_group = group_assets(tileset_names);
            const layer = this.map.createLayer(layer_info.name, tileset_group, 0, 0);
            if (layer_info.depth) {
                layer.setDepth(layer_info.depth);
            }
            if (layer_info.collision) {
                if (layer_info.collision.exclusion) {
                    layer.setCollisionByExclusion(layer_info.collision.exclusion);
                }
            }
            this.layers[layer_info.name] = { "layer": layer, "info": layer_info }
        }
        return this.map;
    }
}
