from __future__ import annotations
from functools import cached_property
import math
from typing import Any, List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys


class Consts:
    DRONE_SPEED = 600
    MAP_SIZE = 10000
    MONSTER_TYPE = -1
    MONSTER_ATTACK_RANGE = 500


class Direction(Enum):
    TOP_LEFT = "TL"
    TOP_RIGHT = "TR"
    BOTTOM_LEFT = "BL"
    BOTTOM_RIGHT = "BR"


@dataclass
class Location:
    x: int
    y: int

    def distance(self, other: Location):
        x_distance = abs(self.x - other.x)
        y_distance = abs(self.y - other.y)
        return math.ceil(math.sqrt(x_distance**2 + y_distance **2))

    # def __init__(self, x: int, y: int):
    #     self.x = max(min(Consts.MAP_SIZE, x), 0)
    #     self.y = max(min(Consts.MAP_SIZE, y), 0)

    def is_in_board(self) -> bool:
        return 0 <= self.x < Consts.MAP_SIZE and 0 <= self.y < Consts.MAP_SIZE

    def __repr__(self) -> str:
        return f"{self.x},{self.y}"

    def add(self, location: Location) -> Location:
        return Location(x=self.x + location.x, y=self.y + location.y)
    
    def towards(self, dest: Location, speed: int):
        if dest.distance(self) <= speed:
            return dest
        
        angle = math.atan((self.y - dest.y) / max(0.1, (dest.x - self.x))) * 180 / math.pi
        return self.get_angle_location(angle, speed)
    
    def get_angle_location(self, angle: float, radius: int) -> Location:
            x = math.floor(radius * math.cos(angle))
            y = math.floor(radius * math.sin(angle))
            return self.add(Location(x=x, y=y))

    def generate_circle_locations(self, angle: int = 10, radius: int = Consts.DRONE_SPEED) -> List[Location]:
        locations: List[Location] = []
        for a in range(0, 360, angle):
            loc = self.get_angle_location(angle=a, radius=radius)
            if loc.is_in_board():
                locations.append(loc)
        return locations
    
    def is_location_in_range_of_locations(self, locations: List[Location], _range: int):
        return any(self.distance(location) <= _range for location in locations)


@dataclass
class CreatureDetail:
    color: int
    type: int

    def __hash__(self) -> int:
        return hash(f"{self.color}-{self.type}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CreatureDetail):
            return False
        return self.color == other.color and self.type == other.type

    @property
    def is_monster(self):
        return self.type == Consts.MONSTER_TYPE


@dataclass
class Creature:
    creature_id: int
    pos: Location
    speed: Location
    detail: CreatureDetail


@dataclass
class RadarBlip:
    creature_id: int
    dir: Direction


@dataclass
class Drone:
    drone_id: int
    pos: Location
    dead: bool
    battery: int
    scans: List[int]


@dataclass
class DirectionData:
    direction: Direction
    edge: Location
    fish_amount: int = 0
    distance_from_drone: Optional[float] = None

    def __init__(self, direction: Direction, drone_location: Location, fish_amount=0):
        self.edge = self.edge_from_direction(direction)
        self.fish_amount = fish_amount
        self.distance_from_drone = self.edge.distance(drone_location)
        self.direction = direction

    def score(self) -> float:
        return self.fish_amount / max(0.01, self.distance_from_drone)

    @staticmethod
    def edge_from_direction(direction: Direction):
        if direction.value == "TL":
            return Location(0, 0)
        elif direction.value == "TR":
            return Location(Consts.MAP_SIZE - 1, 0)
        elif direction.value == "BL":
            return Location(0, Consts.MAP_SIZE - 1)
        elif direction.value == "BR":
            return Location(Consts.MAP_SIZE - 1, Consts.MAP_SIZE - 1)
        else:
            raise ValueError(f"Unsupported direction {direction}")


def debug(message: Any):
    print(message, file=sys.stderr)


def move_in_direction(current_location: Location, direction: Direction) -> Location:
    if direction == Direction.TOP_LEFT.value:
        return Location(
            current_location.x - Consts.DRONE_SPEED,
            current_location.y - Consts.DRONE_SPEED,
        )
    if direction == Direction.TOP_RIGHT.value:
        return Location(
            current_location.x + Consts.DRONE_SPEED,
            current_location.y - Consts.DRONE_SPEED,
        )
    if direction == Direction.BOTTOM_LEFT.value:
        return Location(
            current_location.x - Consts.DRONE_SPEED,
            current_location.y + Consts.DRONE_SPEED,
        )
    if direction == Direction.BOTTOM_RIGHT.value:
        return Location(
            current_location.x + Consts.DRONE_SPEED,
            current_location.y + Consts.DRONE_SPEED,
        )


def get_scans() -> List[int]:
    scans = []
    scan_count = int(input())
    for _ in range(scan_count):
        creature_id = int(input())
        scans.append(creature_id)
    return scans


def get_drone_info() -> Tuple[List[Drone], Dict[int, List[RadarBlip]]]:
    drones: List[Drone] = []
    radar_blips: Dict[int, List[RadarBlip]] = {}
    drone_count = int(input())
    for _ in range(drone_count):
        drone_id, drone_x, drone_y, dead, battery = map(int, input().split())
        pos = Location(drone_x, drone_y)
        drone = Drone(drone_id, pos, dead == "1", battery, [])
        # drone_by_id[drone_id] = drone
        drones.append(drone)
        radar_blips[drone_id] = []

    return drones, radar_blips


def get_drone_by_id(
    my_drones: List[Drone], foe_drones: List[Drone]
) -> Dict[int, Drone]:
    drone_by_id: Dict[int, Drone] = {}
    for drone in my_drones + foe_drones:
        drone_by_id[drone.drone_id] = drone
    return drone_by_id


def update_scans(drone_by_id: Dict[int, Drone]) -> None:
    drone_scan_count = int(input())
    for _ in range(drone_scan_count):
        drone_id, creature_id = map(int, input().split())
        drone_by_id[drone_id].scans.append(creature_id)


def get_visible_creatures(
    fish_details: Dict[int, CreatureDetail], monster_details: Dict[int, CreatureDetail]
) -> Tuple[List[Creature], List[Creature]]:
    visible_fish: List[Creature] = []
    visible_monsters: List[Creature] = []
    visible_creature_count = int(input())
    for _ in range(visible_creature_count):
        creature_id, creature_x, creature_y, creature_vx, creature_vy = map(
            int, input().split()
        )
        pos = Location(creature_x, creature_y)
        speed = Location(creature_vx, creature_vy)
        if creature_id in monster_details:
            creature = Creature(creature_id, pos, speed, monster_details[creature_id])
            visible_monsters.append(creature)
        elif creature_id in  fish_details:
            creature = Creature(creature_id, pos, speed, fish_details[creature_id])
            visible_fish.append(creature)
        else:
            raise Exception(f"Unrecognized creature {creature}")
    return visible_fish, visible_monsters


def priorities_drone_move_direction(
    drone_location: Location, radar_blips: List[RadarBlip]
) -> Location:
    directions_to_direction_data = {}
    for direction in Direction:
        directions_to_direction_data[direction.value] = DirectionData(
            direction=direction, drone_location=drone_location
        )

    for radar_blip in radar_blips:
        direction = radar_blip.dir
        directions_to_direction_data[direction].fish_amount += 1
    best_direction: Direction = max(
        directions_to_direction_data,
        key=lambda direction: directions_to_direction_data[direction].score(),
    )
    return move_in_direction(drone_location, best_direction)


def initilize_input(
    CreatureDetail,
) -> Tuple[Dict[int, CreatureDetail], Dict[int, CreatureDetail]]:
    fish_details: Dict[int, CreatureDetail] = {}
    monster_details: Dict[int, CreatureDetail] = {}

    creature_count = int(input())
    for _ in range(creature_count):
        creature_id, color, _type = map(int, input().split())
        detail: CreatureDetail = CreatureDetail(color=color, type=_type)
        if detail.is_monster:
            monster_details[creature_id] = detail
        else:
            fish_details[creature_id] = detail
    return fish_details, monster_details


def fish_dict_by_type(fish_details: Dict[int, CreatureDetail]) -> Dict[int, Creature]:
    fish_by_type = {}
    for creature_id, fish_detail in fish_details.items():
        fish_by_type[fish_detail.type] = fish_by_type.get(fish_detail.type, []) + [
            creature_id
        ]
    return fish_by_type


def fish_dict_by_color(fish_details: Dict[int, CreatureDetail]) -> Dict[int, Creature]:
    fish_by_type = {}
    for creature_id, fish_detail in fish_details.items():
        fish_by_type[fish_detail.color] = fish_by_type.get(fish_detail.type, []) + [
            creature_id
        ]
    return fish_by_type


fish_details, monster_details = initilize_input(CreatureDetail)
all_fish_by_type: Dict[int, CreatureDetail] = fish_dict_by_type(fish_details)
all_fish_by_color: Dict[int, CreatureDetail] = fish_dict_by_color(fish_details)


class Game:
    def __init__(self) -> None:
        self.fish_details = fish_details
        self.all_fish_by_type = all_fish_by_type
        self.my_score = int(input())
        self.foe_score = int(input())

        self.my_scans = get_scans()
        self.foe_scans = get_scans()

        self.my_drones, self.my_radar_blips = get_drone_info()
        self.foe_drones, self.foe_radar_blips = get_drone_info()

        self.drone_by_id: Dict[int, Drone] = get_drone_by_id(
            self.my_drones, self.foe_drones
        )
        update_scans(self.drone_by_id)

        self.visible_fish, self.visible_monsters = get_visible_creatures(
            fish_details, monster_details
        )
        self.my_radar_blips = self.get_my_radar_blips(self.my_radar_blips)
        debug(self.visible_monsters)

    def all_fish_of_color_acievement_amount(self, Creature: List[int]) -> int:
        # TODO: Check foe not already achieved.
        all_current_scanned_fish = [*Creature, *self.my_scans]
        cnt = 0
        for creature_ids_by_color in all_fish_by_color.values():
            if set(creature_ids_by_color) <= set(all_current_scanned_fish):
                cnt += 1
        return cnt * 3

    def all_fish_of_type_acievement_amount(self, Creature: List[int]):
        # TODO: Check foe not already achieved.
        all_current_scanned_fish = [*Creature, *self.my_scans]
        cnt = 0
        for creature_ids_by_type in all_fish_by_type.values():
            if set(creature_ids_by_type) <= set(all_current_scanned_fish):
                cnt += 1
        return cnt * 4

    def is_first_fish_scanned(self, creature_id: int) -> int:
        return 1 if creature_id not in self.foe_scans else 0

    def get_fish_of_type_first_scanned_amount(self, Creature: List[Creature]) -> int:
        return sum(self.is_first_fish_scanned(f) for f in Creature)

    def get_achievements_amount_by_fish(self, Creature: List[Creature]) -> int:
        return sum(
            [
                self.all_fish_of_type_acievement_amount(Creature),
                self.all_fish_of_color_acievement_amount(Creature),
                self.get_fish_of_type_first_scanned_amount(Creature),
            ]
        )

    @cached_property
    def my_unscanned_creature_ids(self) -> List[int]:
        final_target_fish = [
            creature_id
            for creature_id in self.fish_details.keys()
            if creature_id not in self.my_scans
        ]
        for drone in self.my_drones:
            final_target_fish = [
                creature_id for creature_id in final_target_fish if creature_id not in drone.scans
            ]
        return final_target_fish

    def get_drones_that_should_go_to_base(self) -> List[Drone]:
        # TODO: Make sure that if 2 drones add same acievements only q goes up.
        #
        drones_to_base = []
        base_acievemnts = self.get_achievements_amount_by_fish([])
        max_achievements = base_acievemnts
        for drone in self.my_drones:
            drone_achivements = self.get_achievements_amount_by_fish(drone.scans)
            if drone_achivements > base_acievemnts + 5:
                drones_to_base.append(drone)
            if max_achievements < drone_achivements:
                max_achievements = drone_achivements

        all_drone_achievements = self.get_achievements_amount_by_fish(
            list(
                set([Creature for drone in self.my_drones for Creature in drone.scans])
            )
        )
        if (
            all_drone_achievements > max_achievements
            and all_drone_achievements - max_achievements > 5
        ):
            return self.my_drones
        else:
            return drones_to_base

    def get_my_radar_blips(
        self, my_radar_blips: Dict[int, List[RadarBlip]]
    ) -> Dict[int, List[RadarBlip]]:
        my_radar_blip_count = int(input())
        for _ in range(my_radar_blip_count):
            drone_id, creature_id, dir = input().split()
            # Ignore monsters
            if int(creature_id) in self.fish_details:
                if int(creature_id) in self.my_unscanned_creature_ids:
                    drone_id = int(drone_id)
                    creature_id = int(creature_id)
                    my_radar_blips[drone_id].append(RadarBlip(creature_id, dir))
        return my_radar_blips
    
    def find_safe_dest(self, drone: Drone, dest: Location) -> Location:
        """
        Return a location who is safe - e.g. no monsters in attack range, and
        is as close the given destination as possible
        """
        debug(f"Dest : {dest}")
        next_turn_loc = drone.pos.towards(dest, speed=Consts.DRONE_SPEED)
        debug(f"Towards: {next_turn_loc}")
        monsters_locations = [
            monster.pos.add(monster.speed) for monster in self.visible_monsters
        ]
        if not next_turn_loc.is_location_in_range_of_locations(locations=monsters_locations, _range=Consts.MONSTER_ATTACK_RANGE):
            return dest
        
        best_location = drone.pos
        best_distance = sys.maxsize
        debug(f"Monstres: {monsters_locations}")
        for location in drone.pos.generate_circle_locations():
            debug(f"Circle option: {location}")
            if not location.is_location_in_range_of_locations(monsters_locations, _range=Consts.MONSTER_ATTACK_RANGE):
                distance = location.distance(dest)
                if location.distance(dest) < best_distance:
                    best_distance = distance
                    best_location = location

        return best_location

        

    def run_turn(self) -> None:
        should_go_to_base = self.get_drones_that_should_go_to_base()
        for drone in self.my_drones:
            loc = priorities_drone_move_direction(
                drone_location=drone.pos,
                radar_blips=self.my_radar_blips[drone.drone_id],
            )
            light = 1 if drone.battery >= 5 and game_turn % 2 == 0 else 0
            # if len(drone.scans) > 1 or len(self.my_radar_blips[drone.drone_id]) == 0:
            if drone in should_go_to_base:
                loc = Location(drone.pos.x, 0)

            loc = self.find_safe_dest(drone, loc)

            print(f"MOVE {loc.x} {loc.y} {light}")


game_turn = 1
while True:
    game = Game()
    game.run_turn()
    game_turn += 1
