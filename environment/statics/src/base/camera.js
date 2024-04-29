export default class LandCamera {
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