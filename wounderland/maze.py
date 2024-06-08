"""wounderland.maze"""

import random
from itertools import product
from wounderland import utils
from wounderland.memory import Event


class Tile:
    def __init__(
        self,
        coord,
        world,
        address_keys,
        address=None,
        collision=False,
    ):
        # in order: world, sector, arena, game_object
        self.coord = coord
        self.address = [world]
        if address:
            self.address += address
        self.address_keys = address_keys
        self.address_map = dict(zip(address_keys[: len(self.address)], self.address))
        self.collision = collision
        self.event_cnt = 0
        self._events = set()
        if len(self.address) == 4:
            self.add_event(Event(self.address[-1], address=self.address))

    def __str__(self):
        return utils.dump_dict(self.to_dict())

    def __eq__(self, other):
        if isinstance(other, Tile):
            return hash(self.coord) == hash(other.coord)
        return False

    def to_dict(self):
        address = ":".join(self.address)
        if self.collision:
            address += "(collision)"
        return {
            "coord[{},{}]".format(self.coord[0], self.coord[1]): address,
            "events": self.events,
        }

    def add_event(self, event):
        if isinstance(event, (tuple, list)):
            event = Event.from_list(event)
        self._events.add(event)

    def remove_events(self, subject=None, event=None):
        r_events = set()
        for eve in self._events:
            if subject and eve.subject == subject:
                r_events.add(eve)
            if event and eve == event:
                r_events.add(eve)
        for r_eve in r_events:
            self._events.remove(r_eve)

    def update_event(self, event, mode):
        for eve in self._events:
            if eve == event:
                eve.update(mode)

    def has_address(self, key):
        return key in self.address_map

    def get_address(self, level, as_list=True):
        assert level in self.address_keys, "Can not find {} from {}".format(
            level, self.address_keys
        )
        pos = self.address_keys.index(level) + 1
        if as_list:
            return self.address[:pos]
        return ":".join(self.address[:pos])

    def get_addresses(self):
        addresses = []
        if len(self.address) > 1:
            addresses = [
                ":".join(self.address[:i]) for i in range(2, len(self.address) + 1)
            ]
        return addresses

    @property
    def events(self):
        return self._events

    @property
    def is_empty(self):
        return len(self.address) == 1 and not self._events


class Maze:
    def __init__(self, config, logger):
        # define tiles
        self.maze_height, self.maze_width = config["size"]
        self.tile_size = config["tile_size"]
        address_keys = config["tile_address_keys"]
        self.tiles = [
            [
                Tile((x, y), config["world"], address_keys)
                for x in range(self.maze_width)
            ]
            for y in range(self.maze_height)
        ]
        for tile in config["tiles"]:
            x, y = tile.pop("coord")
            self.tiles[y][x] = Tile((x, y), config["world"], address_keys, **tile)

        # define address
        self.address_tiles = dict()
        for i in range(self.maze_height):
            for j in range(self.maze_width):
                for add in self.tile_at([j, i]).get_addresses():
                    self.address_tiles.setdefault(add, set()).add((j, i))

        # slot for persona
        self.persona_tiles = {}
        self.logger = logger

    def find_path(self, src_coord, dst_coord):
        map = [[0 for _ in range(self.maze_width)] for _ in range(self.maze_height)]
        frontier = [src_coord]
        map[src_coord[1]][src_coord[0]] = 1
        while map[dst_coord[1]][dst_coord[0]] == 0:
            new_frontier = []
            for f in frontier:
                for c in [
                    (f[0] - 1, f[1]),
                    (f[0] + 1, f[1]),
                    (f[0], f[1] - 1),
                    (f[0], f[1] + 1),
                ]:
                    if (
                        0 < c[0] < self.maze_width - 1
                        and 0 < c[1] < self.maze_height - 1
                        and map[c[1]][c[0]] == 0
                        and not self.tile_at(c).collision
                    ):
                        map[c[1]][c[0]] = map[f[1]][f[0]] + 1
                        new_frontier.append(c)
            frontier = new_frontier
        step = map[dst_coord[1]][dst_coord[0]]
        path = [dst_coord]
        while step > 1:
            f = path[-1]
            for c in [
                (f[0] - 1, f[1]),
                (f[0] + 1, f[1]),
                (f[0], f[1] - 1),
                (f[0], f[1] + 1),
            ]:
                if map[c[1]][c[0]] == step - 1:
                    path.append(c)
                    break
            step -= 1
        return path[::-1]

    def tile_at(self, coord):
        return self.tiles[coord[1]][coord[0]]

    def events_at(self, coord):
        return self.tile_at(coord).events

    def add_event(self, coord, event):
        self.tile_at(coord).add_event(event)

    def remove_events(self, coord, subject=None, event=None):
        self.tile_at(coord).remove_events(subject=subject, event=event)

    def update_events(self, coord, mode, events=None):
        events = events or self.events_at(coord)
        for e in events:
            self.tile_at(coord).update_event(e, mode)

    def get_scope(self, coord, config):
        coords = []
        vision_r = config["vision_r"]
        if config["mode"] == "box":
            x_range = [
                max(coord[0] - vision_r, 0),
                min(coord[0] + vision_r + 1, self.maze_width),
            ]
            y_range = [
                max(coord[1] - vision_r, 0),
                min(coord[1] + vision_r + 1, self.maze_height),
            ]
            coords = list(product(list(range(*x_range)), list(range(*y_range))))
        return [self.tile_at(c) for c in coords]

    def get_address_tiles(self, address):
        addr = ":".join(address)
        if addr in self.address_tiles:
            return self.address_tiles[addr]
        return random.choice(self.maze.address_tiles.values())
