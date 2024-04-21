export default class SceneCamera {
    constructor(scene, config, map, player) {
        this.name = 'scene_camera';
        this.status = {
            "zoom_factor": config.zoom_factor || 1,
            "zoom_range": config.zoom_range || [1, 10, 0.01]
        }
        this.camera = scene.cameras.main;
        this.camera.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
        this.camera.setZoom(this.status.zoom_factor);

        // set events
        if (config.enable_zoom || true) {
            scene.input.on("wheel", this.zoom);
        }
        if (config.enable_drag || false) {
            scene.input.on("pointermove", this.drag);
        }

        // follow player
        this.camera.startFollow(player);
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