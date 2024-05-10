export class tileMapCreator {
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


export class MazeCamera {
    constructor(land, config) {
        this.name = 'land_camera';
        this.status = {
            "zoom_factor": config.zoom_factor || 1,
            "zoom_range": config.zoom_range || [1, 10, 0.01]
        }
        this.camera = land.cameras.main;
        this.camera.setBounds(0, 0, land.map.widthInPixels, land.map.heightInPixels);
        this.camera.setZoom(this.status.zoom_factor);
        this.offset(0, 0);

        // set events
        if (config.enable_zoom || true) {
            land.input.on("wheel", this.zoom);
        }
        if (config.enable_drag || true) {
            land.input.on("pointermove", this.drag);
        }
    }

    setFollow(obj, follow) {
        if (follow) {
            this.camera.startFollow(obj);
            this.camera.followOffset.set(-this.offsetCoords.x, this.offsetCoords.y);
        } else {
            this.camera.stopFollow();
        }
    }

    locate(obj) {
        this.camera.startFollow(obj);
        this.camera.stopFollow();
        this.camera.scrollX += this.offsetCoords.x / this.camera.zoom;
        this.camera.scrollY += this.offsetCoords.y / this.camera.zoom;
    }

    offset(x, y) {
        this.offsetCoords = { "x": x, "y": y };
    }

    zoom = (pointer, gameObjects, deltaX, deltaY, deltaZ) => {
        const z_range = this.status.zoom_range;
        this.status.zoom_factor = Math.min(Math.max(this.status.zoom_factor + deltaY * z_range[2], z_range[0]), z_range[1]);
        this.camera.setZoom(this.status.zoom_factor);
    }

    drag = (pointer) => {
        if (!pointer.isDown) return;
        this.camera.scrollX -= (pointer.x - pointer.prevPosition.x) / this.camera.zoom;
        this.camera.scrollY -= (pointer.y - pointer.prevPosition.y) / this.camera.zoom;
    }
}