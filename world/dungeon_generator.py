import random

# Tile type constants (shared with TileMap)
TILE_WALL    = 0
TILE_FLOOR   = 1
TILE_STAIRS  = 2
TILE_ITEM    = 3
TILE_TRAP    = 4   # Hidden traps (Choco Dungeon / DQ-style)
TILE_WATER   = 5   # Water – slows movement, DQ Rocket Slime style
TILE_LAVA    = 6   # Lava  – burns when stepped on
TILE_SEALED  = 7   # Sealed room door – needs a key (Choco Dungeon)

TRAP_TYPES = ["spike", "sleep", "warp", "poison", "hunger"]


class DungeonGenerator:
    def __init__(self, width=30, height=30):
        self.width = width
        self.height = height
        self.rooms = []

    def generate(self, max_rooms=8, min_size=4, max_size=8, floor_level=1):
        grid = [[TILE_WALL for _ in range(self.height)] for _ in range(self.width)]
        self.rooms = []

        is_boss_floor = (floor_level % 5 == 0 and floor_level > 0)

        for _ in range(max_rooms):
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)

            new_room = (x, y, w, h)

            intersects = False
            for other in self.rooms:
                if self.rooms_intersect(new_room, other):
                    intersects = True
                    break

            if not intersects:
                self.apply_room_to_grid(grid, new_room, floor_level)

                if self.rooms:
                    prev_center = self.get_room_center(self.rooms[-1])
                    curr_center = self.get_room_center(new_room)
                    self.apply_corridor(grid, prev_center, curr_center)

                self.rooms.append(new_room)

        # Place stairs in last room
        if self.rooms:
            last_cx, last_cy = self.get_room_center(self.rooms[-1])
            grid[last_cx][last_cy] = TILE_STAIRS

        # Boss floor: seal the last room behind a door (Choco Dungeon style)
        if is_boss_floor and len(self.rooms) >= 2:
            self._seal_last_room(grid)

        # Add special terrain for deeper floors (Diablo/DQ atmosphere)
        if floor_level >= 3:
            self._add_hazard_tiles(grid, floor_level)

        # Add traps (hidden, revealed on step)
        self._place_traps(grid, floor_level)

        return grid, self.rooms

    # ------------------------------------------------------------------ #
    #  Room helpers                                                        #
    # ------------------------------------------------------------------ #

    def rooms_intersect(self, r1, r2):
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        return (x1 <= x2 + w2 + 1 and x1 + w1 + 1 >= x2 and
                y1 <= y2 + h2 + 1 and y1 + h1 + 1 >= y2)

    def get_room_center(self, room):
        x, y, w, h = room
        return (x + w // 2, y + h // 2)

    def apply_room_to_grid(self, grid, room, floor_level=1):
        x, y, w, h = room
        # Item density scales slightly with floor
        item_chance = min(0.20, 0.10 + floor_level * 0.01)
        for i in range(x, x + w):
            for j in range(y, y + h):
                if random.random() < item_chance:
                    grid[i][j] = TILE_ITEM
                else:
                    grid[i][j] = TILE_FLOOR

    def apply_corridor(self, grid, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        if random.random() > 0.5:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if grid[x][y1] == TILE_WALL:
                    grid[x][y1] = TILE_FLOOR
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if grid[x2][y] == TILE_WALL:
                    grid[x2][y] = TILE_FLOOR
        else:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if grid[x1][y] == TILE_WALL:
                    grid[x1][y] = TILE_FLOOR
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if grid[x][y2] == TILE_WALL:
                    grid[x][y2] = TILE_FLOOR

    # ------------------------------------------------------------------ #
    #  Special feature placement                                           #
    # ------------------------------------------------------------------ #

    def _seal_last_room(self, grid):
        """
        Find the corridor connecting the second-to-last and last room,
        and place a SEALED tile as a gate. (Choco Dungeon style.)
        """
        if len(self.rooms) < 2:
            return
        cx, cy = self.get_room_center(self.rooms[-2])
        lx, ly = self.get_room_center(self.rooms[-1])
        # Walk along corridor and place a single seal near the last room entrance
        dx = 1 if lx > cx else (-1 if lx < cx else 0)
        dy = 1 if ly > cy else (-1 if ly < cy else 0)
        # Try to place the seal 2 tiles from the last room center
        sx = lx - dx * 2
        sy = ly - dy * 2
        if 0 < sx < self.width and 0 < sy < self.height:
            if grid[sx][sy] == TILE_FLOOR:
                grid[sx][sy] = TILE_SEALED

    def _add_hazard_tiles(self, grid, floor_level):
        """Sprinkle water/lava tiles into corridors and edges of rooms."""
        lava_chance  = 0.0 if floor_level < 6 else 0.015
        water_chance = 0.02 if floor_level >= 3 else 0.0

        for x in range(self.width):
            for y in range(self.height):
                if grid[x][y] != TILE_FLOOR:
                    continue
                r = random.random()
                if r < lava_chance:
                    grid[x][y] = TILE_LAVA
                elif r < lava_chance + water_chance:
                    grid[x][y] = TILE_WATER

    def _place_traps(self, grid, floor_level):
        """Place hidden traps. They appear as FLOOR until stepped on."""
        trap_density = min(0.04, 0.01 + floor_level * 0.003)
        for x in range(self.width):
            for y in range(self.height):
                if grid[x][y] == TILE_FLOOR:
                    if random.random() < trap_density:
                        grid[x][y] = TILE_TRAP
