class Maze:
    def __init__(self, config: dict):
        def _get_empty():
            return {
                "world": config["world"],
                "sector": "",
                "arena": "",
                "game_object": "",
                "spawning_location": "",
                "collision": False,
                "events": set(),
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
                self.tiles[row][col]["events"].add(tuple(e))
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
