from .event import Event


class Maze:
    def __init__(self, config, logger):
        def _get_empty():
            return {
                "world": config["world"],
                "sector": "",
                "arena": "",
                "game_object": "",
                "spawning_location": "",
                "collision": False,
                "event_cnt": 0,
                "events": {},
            }

        # define tiles
        self.maze_height, self.maze_width = config["size"]
        self.sq_tile_size = config["tile_size"]
        self.tiles = [
            [_get_empty() for _ in range(self.maze_width)]
            for _ in range(self.maze_height)
        ]
        for tile in config["tiles"]:
            row, col = tile.pop("coord")
            events = tile.pop("events")
            self.tiles[row][col].update(tile)
            for e in events:
                event_id = "event_" + str(len(self.tiles[row][col]["events"]))
                self.tiles[row][col]["events"][event_id] = Event.from_tuple(e)
            self.tiles[row][col]["event_cnt"] = len(self.tiles[row][col]["events"])
        # define address
        self.address_tiles = dict()
        for i in range(self.maze_height):
            for j in range(self.maze_width):
                addresses = []
                if self.tiles[i][j]["sector"]:
                    add = f'{self.tiles[i][j]["world"]}:'
                    add += f'{self.tiles[i][j]["sector"]}'
                    addresses += [add]
                if self.tiles[i][j]["arena"]:
                    add = f'{self.tiles[i][j]["world"]}:'
                    add += f'{self.tiles[i][j]["sector"]}:'
                    add += f'{self.tiles[i][j]["arena"]}'
                    addresses += [add]
                if self.tiles[i][j]["game_object"]:
                    add = f'{self.tiles[i][j]["world"]}:'
                    add += f'{self.tiles[i][j]["sector"]}:'
                    add += f'{self.tiles[i][j]["arena"]}:'
                    add += f'{self.tiles[i][j]["game_object"]}'
                    addresses += [add]
                if self.tiles[i][j]["spawning_location"]:
                    add = f'<spawn_loc>{self.tiles[i][j]["spawning_location"]}'
                    addresses += [add]
                for add in addresses:
                    if add in self.address_tiles:
                        self.address_tiles[add].add((j, i))
                    else:
                        self.address_tiles[add] = set([(j, i)])
        # slot for persona
        self.persona_tiles = {}
        self.logger = logger

    def get_tile(self, pos):
        return self.tiles[pos[0]][pos[1]]

    def add_event(self, pos, event):
        self.get_tile(pos)["event_cnt"] += 1
        event_id = "event_" + str(self.tiles[pos[1]][pos[0]]["event_cnt"])
        if isinstance(event, tuple):
            event = Event.from_tuple(event)
        self.get_tile(pos)["events"][event_id] = event

    def remove_events(self, pos, subject=None, event=None):
        remove_ids, tile = set(), self.get_tile(pos)
        for id, eve in tile["events"].items():
            if subject and eve.subject == subject:
                remove_ids.add(id)
            if event and eve == event:
                remove_ids.add(id)
        for id in remove_ids:
            tile["events"].pop(id)

    def update_event(self, pos, mode, event):
        for eve in self.get_tile(pos)["events"].values():
            if eve == event:
                eve.update(mode)
