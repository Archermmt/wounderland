from .event import Event
from wounderland import utils


class Tile:
    def __init__(
        self,
        coord,
        world,
        address=None,
        spawning_location=None,
        collision=False,
        events=None,
    ):
        # in order: world, sector, arena, gameobject
        self.coord = coord
        self.address = [world]
        if address:
            self.address += address
        self.spawning_location = spawning_location
        self.collision = collision
        self.event_cnt = 0
        self._events = {}
        for eve in events or []:
            self.add_event(eve)

    def __str__(self):
        address = ":".join(self.address)
        if self.spawning_location:
            address += "<{}>".format(self.spawning_location)
        if self.collision:
            address += "(collision)"
        des = {
            "coord[{},{}]".format(self.coord[0], self.coord[1]): address,
            "events": self.events,
        }
        return utils.dump_dict(des)

    def add_event(self, event):
        if isinstance(event, (tuple, list)):
            event = Event.from_list(event)
        self._events["event_" + str(self.event_cnt)] = event
        self.event_cnt += 1

    def remove_events(self, subject=None, event=None):
        remove_ids = set()
        for id, eve in self._events.items():
            if subject and eve.subject == subject:
                remove_ids.add(id)
            if event and eve == event:
                remove_ids.add(id)
        for id in remove_ids:
            self._events.pop(id)

    def update_event(self, event, mode):
        for eve in self._events.values():
            if eve == event:
                eve.update(mode)

    def get_addresses(self):
        addresses = []
        if len(self.address) > 1:
            addresses = [
                ":".join(self.address[:i]) for i in range(2, len(self.address) + 1)
            ]
        if self.spawning_location:
            addresses += [f"<spawn_loc>{self.spawning_location}"]
        return addresses

    @property
    def events(self):
        return self._events

    @property
    def is_empty(self):
        return (
            len(self.address) == 1 and not self._events and not self.spawning_location
        )


class Maze:
    def __init__(self, config, logger):
        # define tiles
        self.maze_height, self.maze_width = config["size"]
        self.sq_tile_size = config["tile_size"]
        self.tiles = [
            [Tile((x, y), config["world"]) for x in range(self.maze_width)]
            for y in range(self.maze_height)
        ]
        for tile in config["tiles"]:
            x, y = tile.pop("coord")
            self.tiles[y][x] = Tile((x, y), config["world"], **tile)

        # define address
        self.address_tiles = dict()
        for i in range(self.maze_height):
            for j in range(self.maze_width):
                for add in self.tile_at([j, i]).get_addresses():
                    self.address_tiles.setdefault(add, set()).add((j, i))

        # slot for persona
        self.persona_tiles = {}
        self.logger = logger

    def tile_at(self, coord):
        return self.tiles[coord[1]][coord[0]]

    def events_at(self, coord):
        return self.tile_at(coord).events

    def add_event(self, coord, event):
        self.tile_at(coord).add_event(event)

    def remove_events(self, coord, subject=None, event=None):
        self.tile_at(coord).remove_events(subject=subject, event=event)

    def update_event(self, coord, event, mode):
        self.tile_at(coord).update_event(event, mode)
