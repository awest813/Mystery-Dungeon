from panda3d.core import NodePath, CardMaker, Point3, Vec3
from panda3d.core import AmbientLight, DirectionalLight
from world.dungeon_generator import (
    TILE_WALL, TILE_FLOOR, TILE_STAIRS, TILE_ITEM,
    TILE_TRAP, TILE_WATER, TILE_LAVA, TILE_SEALED,
    TILE_FORGE, TILE_MATERIAL_NODE, TILE_TOWN_PLOT,
    TILE_HERBALIST, TILE_INN, TILE_SHRINE, TILE_GUILD, TILE_GARDEN, TILE_COMPANION, TILE_RANCH,
)


def _make_floor_tile(*args, **kwargs):
    from render import make_floor_tile
    return make_floor_tile(*args, **kwargs)


def _make_wall_block(*args, **kwargs):
    from render import make_wall_block
    return make_wall_block(*args, **kwargs)


def _make_wall_cap(*args, **kwargs):
    from render import make_wall_cap
    return make_wall_cap(*args, **kwargs)


def _make_stairs_model(*args, **kwargs):
    from render import make_stairs_model
    return make_stairs_model(*args, **kwargs)


def _make_item_pickup(*args, **kwargs):
    from render import make_item_pickup
    return make_item_pickup(*args, **kwargs)


def _make_material_node_model():
    from render import make_material_node_model
    return make_material_node_model()


class TileMap:
    THEMES = {
        "CAVE": {
            "floor":  (0.10, 0.10, 0.15, 1),
            "alt":    (0.12, 0.12, 0.20, 1),
            "water":  (0.10, 0.25, 0.50, 1),
            "lava":   (0.80, 0.20, 0.00, 1),
            "wall":   (0.25, 0.22, 0.30, 1),
            "wall_top": (0.35, 0.30, 0.38, 1),
            "fog":    (0.05, 0.05, 0.08, 1),
        },
        "ICE": {
            "floor":  (0.30, 0.40, 0.60, 1),
            "alt":    (0.20, 0.30, 0.50, 1),
            "water":  (0.50, 0.70, 0.90, 1),
            "lava":   (0.80, 0.20, 0.00, 1),
            "wall":   (0.40, 0.45, 0.55, 1),
            "wall_top": (0.55, 0.60, 0.70, 1),
            "fog":    (0.08, 0.10, 0.15, 1),
        },
        "FIRE": {
            "floor":  (0.30, 0.10, 0.10, 1),
            "alt":    (0.40, 0.15, 0.10, 1),
            "water":  (0.10, 0.25, 0.50, 1),
            "lava":   (1.00, 0.30, 0.00, 1),
            "wall":   (0.35, 0.20, 0.15, 1),
            "wall_top": (0.45, 0.28, 0.20, 1),
            "fog":    (0.10, 0.04, 0.04, 1),
        },
        "TOWN": {
            "floor":  (0.20, 0.20, 0.20, 1),
            "alt":    (0.22, 0.22, 0.22, 1),
            "water":  (0.10, 0.30, 0.60, 1),
            "lava":   (0.80, 0.20, 0.00, 1),
            "wall":   (0.30, 0.28, 0.25, 1),
            "wall_top": (0.40, 0.38, 0.35, 1),
            "fog":    (0.06, 0.06, 0.08, 1),
        },
    }

    WALL_HEIGHT = 1.6

    def __init__(self, width=30, height=30):
        self.width = width
        self.height = height
        self.grid = [[TILE_WALL for _ in range(height)] for _ in range(width)]
        self.root = NodePath("TileMap")
        self.visual_nodes = {}
        self.wall_nodes = []
        self.current_theme = "CAVE"
        self.revealed_traps = set()

        self._setup_lighting()

    def _setup_lighting(self):
        self._ambient = AmbientLight("ambient")
        self._ambient.setColor((0.45, 0.45, 0.55, 1))
        self._ambient_np = self.root.attachNewNode(self._ambient)

        self._dir_light = DirectionalLight("dir_light")
        self._dir_light.setColor((0.65, 0.60, 0.55, 1))
        self._dir_np = self.root.attachNewNode(self._dir_light)
        self._dir_np.setHpr(-45, -55, 0)

        self._root_light = None

    def apply_theme(self, theme_name):
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            fog = self.THEMES[theme_name].get("fog", (0.05, 0.05, 0.08, 1))
            if hasattr(self.root, 'getPythonTag') or True:
                pass

    def is_in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def set_tile(self, x, y, tile_type):
        if self.is_in_bounds(x, y):
            self.grid[x][y] = tile_type

    def get_tile(self, x, y):
        if self.is_in_bounds(x, y):
            return self.grid[x][y]
        return TILE_WALL

    def is_walkable(self, x, y):
        t = self.get_tile(x, y)
        return t not in (TILE_WALL, TILE_SEALED)

    def is_stairs(self, x, y):
        return self.get_tile(x, y) == TILE_STAIRS

    def is_item(self, x, y):
        return self.get_tile(x, y) == TILE_ITEM

    def is_trap(self, x, y):
        return self.get_tile(x, y) == TILE_TRAP

    def is_water(self, x, y):
        return self.get_tile(x, y) == TILE_WATER

    def is_lava(self, x, y):
        return self.get_tile(x, y) == TILE_LAVA

    def is_sealed(self, x, y):
        return self.get_tile(x, y) == TILE_SEALED

    def is_forge(self, x, y):
        return self.get_tile(x, y) == TILE_FORGE

    def is_material_node(self, x, y):
        return self.get_tile(x, y) == TILE_MATERIAL_NODE

    def is_town_plot(self, x, y):
        return self.get_tile(x, y) == TILE_TOWN_PLOT

    def is_herbalist(self, x, y):
        return self.get_tile(x, y) == TILE_HERBALIST

    def is_inn(self, x, y):
        return self.get_tile(x, y) == TILE_INN

    def is_shrine(self, x, y):
        return self.get_tile(x, y) == TILE_SHRINE

    def is_guild(self, x, y):
        return self.get_tile(x, y) == TILE_GUILD

    def is_garden(self, x, y):
        return self.get_tile(x, y) == TILE_GARDEN

    def is_companion_tile(self, x, y):
        return self.get_tile(x, y) == TILE_COMPANION

    def is_ranch(self, x, y):
        return self.get_tile(x, y) == TILE_RANCH

    def is_building_tile(self, x, y):
        return self.get_tile(x, y) in (TILE_HERBALIST, TILE_INN, TILE_SHRINE, TILE_GUILD)

    def reveal_trap(self, x, y):
        self.revealed_traps.add((x, y))
        node = self.visual_nodes.get((x, y))
        if node:
            node.setColor(0.8, 0.0, 0.8, 1)

    def open_sealed(self, x, y):
        if self.is_sealed(x, y):
            self.grid[x][y] = TILE_FLOOR
            old_node = self.visual_nodes.pop((x, y), None)
            if old_node:
                old_node.removeNode()
            self._place_floor_tile(x, y, TILE_FLOOR)

    def _get_tile_color(self, tile_type, x, y, theme):
        checker = (x + y) % 2 == 0
        if tile_type == TILE_FLOOR:
            return theme["alt"] if checker else theme["floor"]
        elif tile_type == TILE_STAIRS:
            if self.current_theme == "TOWN":
                return (0.0, 0.7, 1.0, 1)
            return (0.3, 0.9, 0.9, 1)
        elif tile_type == TILE_ITEM:
            return (1.0, 0.8, 0.2, 1)
        elif tile_type == TILE_TRAP:
            return theme["alt"] if checker else theme["floor"]
        elif tile_type == TILE_WATER:
            return theme["water"]
        elif tile_type == TILE_LAVA:
            return theme["lava"]
        elif tile_type == TILE_SEALED:
            return (0.5, 0.35, 0.1, 1)
        elif tile_type == TILE_FORGE:
            return (0.9, 0.5, 0.1, 1)
        elif tile_type == TILE_MATERIAL_NODE:
            return (0.55, 0.35, 0.65, 1)
        elif tile_type == TILE_TOWN_PLOT:
            return (0.15, 0.45, 0.25, 1)
        elif tile_type == TILE_HERBALIST:
            return (0.2, 0.6, 0.2, 1)
        elif tile_type == TILE_INN:
            return (0.7, 0.5, 0.3, 1)
        elif tile_type == TILE_SHRINE:
            return (0.5, 0.3, 0.7, 1)
        elif tile_type == TILE_GUILD:
            return (0.8, 0.7, 0.2, 1)
        elif tile_type == TILE_GARDEN:
            return (0.3, 0.55, 0.2, 1)
        elif tile_type == TILE_COMPANION:
            return (0.8, 0.4, 0.8, 1)
        elif tile_type == TILE_RANCH:
            return (0.4, 0.8, 0.8, 1)
        return theme["floor"]

    def _place_floor_tile(self, x, y, tile_type):
        theme = self.THEMES[self.current_theme]
        color = self._get_tile_color(tile_type, x, y, theme)

        if tile_type == TILE_STAIRS:
            model = _make_stairs_model(color)
        elif tile_type == TILE_ITEM:
            model = _make_item_pickup(color)
        elif tile_type == TILE_MATERIAL_NODE:
            model = _make_material_node_model()
        else:
            model = _make_floor_tile()
            model.setColor(color)

        model.reparentTo(self.root)
        model.setPos(x, y, 0)
        self.visual_nodes[(x, y)] = model
        return model

    def _place_wall(self, x, y, theme):
        model = _make_wall_block()
        color = theme.get("wall", (0.25, 0.22, 0.30, 1))
        top_color = theme.get("wall_top", (0.35, 0.30, 0.38, 1))

        for child in model.getChildren():
            if child.getName() == "top":
                child.setColor(*top_color)
            else:
                child.setColor(*color)

        model.reparentTo(self.root)
        model.setPos(x, y, 0)

        has_open_neighbor = False
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.is_in_bounds(nx, ny) and self.grid[nx][ny] != TILE_WALL:
                has_open_neighbor = True
                break

        if has_open_neighbor:
            cap = _make_wall_cap()
            cap.setColor(*top_color)
            cap.reparentTo(self.root)
            cap.setPos(x, y, 0)

        self.wall_nodes.append(model)
        return model

    def setup_visuals(self):
        self.root.getChildren().detach()
        self.visual_nodes = {}
        self.wall_nodes = []
        self.revealed_traps = {}

        theme = self.THEMES[self.current_theme]

        floor_tiles = []
        wall_tiles = []

        for x in range(self.width):
            for y in range(self.height):
                tile_type = self.grid[x][y]
                if tile_type == TILE_WALL:
                    wall_tiles.append((x, y))
                else:
                    floor_tiles.append((x, y, tile_type))

        for x, y in wall_tiles:
            self._place_wall(x, y, theme)

        for x, y, tile_type in floor_tiles:
            self._place_floor_tile(x, y, tile_type)

        if self._root_light:
            self._root_light.removeNode()
        self._root_light = self.root.attachNewNode(self._ambient_np)
        self._root_light.setLight(self._ambient_np)
        self._root_light.setLight(self._dir_np)

    def reparent_to(self, parent):
        self.root.reparentTo(parent)
