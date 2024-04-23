export default class MapFactory {
    static create(scene, config) {
        const map = scene.make.tilemap({ key: config.asset });
        scene.physics.world.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
        let tilesets = {};
        let group_assets = (assets) => {
            for (const asset of assets) {
                if (asset in tilesets) continue;
                tilesets[asset] = map.addTilesetImage(asset, asset);
            }
            let tileset_group = [];
            for (const asset of assets) {
                tileset_group.push(tilesets[asset]);
            }
            return tileset_group;
        }

        for (const layer_info of config.layers) {
            let tileset_names;
            if (typeof layer_info.tileset_group === "string") {
                tileset_names = config.tileset_groups[layer_info.tileset_group];
            } else {
                tileset_names = layer_info.tileset_group;
            }
            const tileset_group = group_assets(tileset_names);
            const layer = map.createLayer(layer_info.name, tileset_group, 0, 0);
            if (layer_info.depth) {
                layer.setDepth(layer_info.depth);
            }
            if (layer_info.collision) {
                layer.setCollisionByProperty(layer_info.collision);
            }
        }
        return map;
    }
}