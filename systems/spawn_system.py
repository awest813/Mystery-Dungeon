import random
from entities.enemy import get_random_enemy_type

class SpawnSystem:
    def __init__(self, tilemap, player, enemies):
        self.tilemap = tilemap
        self.player = player
        self.enemies = enemies

    def spawn_from_layout(self, rooms, floor_level=1):
        """Positions actors based on generated room layout, scaling enemies to floor."""
        if not rooms:
            return

        is_boss_floor = (floor_level % 5 == 0 and floor_level > 0)

        # Place player in first room
        px, py = self.get_room_center(rooms[0])
        self.player.move_to(px, py)

        # Distribute enemies across other rooms
        other_rooms = rooms[1:] if len(rooms) > 1 else rooms

        for i, enemy in enumerate(self.enemies):
            room = random.choice(other_rooms)

            ex = random.randint(room[0], room[0] + room[2] - 1)
            ey = random.randint(room[1], room[1] + room[3] - 1)

            # Boss: last enemy on boss floors becomes the dark_knight
            if is_boss_floor and i == len(self.enemies) - 1:
                # Place boss in the last room (boss room)
                last_room = rooms[-1]
                bx, by = self.get_room_center(last_room)
                enemy.reset_for_floor(floor_level, enemy_type="dark_knight")
                enemy.move_to(bx, by)
            else:
                enemy.reset_for_floor(floor_level)
                enemy.move_to(ex, ey)

    def get_room_center(self, room):
        x, y, w, h = room
        return (x + w // 2, y + h // 2)

    def find_random_open_floor(self):
        """Find a random walkable tile (for warp traps etc.)."""
        for _ in range(200):
            x = random.randint(0, self.tilemap.width - 1)
            y = random.randint(0, self.tilemap.height - 1)
            if self.tilemap.is_walkable(x, y):
                if (x, y) != (self.player.x, self.player.y):
                    return x, y
        return self.player.x, self.player.y
