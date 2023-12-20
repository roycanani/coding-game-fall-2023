from __future__ import annotations
from functools import cached_property
import math
from typing import Any, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import sys


class Consts:
    DRONE_SPEED = 600


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
        return math.ceil(math.sqrt(x_distance**2 + y_distance))


@dataclass
class FishDetail:
    color: int
    type: int

    def __hash__(self) -> int:
        return hash(f"{self.color}-{self.type}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FishDetail):
            return False
        return self.color == other.color and self.type == other.type


@dataclass
class Fish:
    fish_id: int
    pos: Location
    speed: Location
    detail: FishDetail


@dataclass
class RadarBlip:
    fish_id: int
    dir: Direction


@dataclass
class Drone:
    drone_id: int
    pos: Location
    dead: bool
    battery: int
    scans: List[int]


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
        fish_id = int(input())
        scans.append(fish_id)
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
        drone_id, fish_id = map(int, input().split())
        drone_by_id[drone_id].scans.append(fish_id)


def get_visible_fish() -> List[Fish]:
    visible_fish: List[Fish] = []
    visible_fish_count = int(input())
    for _ in range(visible_fish_count):
        fish_id, fish_x, fish_y, fish_vx, fish_vy = map(int, input().split())
        pos = Location(fish_x, fish_y)
        speed = Location(fish_vx, fish_vy)
        visible_fish.append(Fish(fish_id, pos, speed, fish_details[fish_id]))
    return visible_fish


def priorities_drone_move_direction(
    drone_location: Location, radar_blips: List[RadarBlip]
) -> Location:
    directions = {"TL": 0, "TR": 0, "BL": 0, "BR": 0}
    for radar_blip in radar_blips:
        direction = radar_blip.dir
        directions[direction] += 1
    most_common: Direction = max(directions, key=directions.get)
    return move_in_direction(drone_location, most_common)


def initilize_input(FishDetail) -> Dict[int, FishDetail]:
    fish_details: Dict[int, FishDetail] = {}

    fish_count = int(input())
    for _ in range(fish_count):
        fish_id, color, _type = map(int, input().split())
        fish_details[fish_id] = FishDetail(color, _type)
    return fish_details


def fish_dict_by_type(fish_details: Dict[int, FishDetail]) -> Dict[int, Fish]:
    fish_by_type = {}
    for fish_id, fish_detail in fish_details.items():
        fish_by_type[fish_detail.type] = fish_by_type.get(fish_detail.type, []) + [
            fish_id
        ]
    return fish_by_type


def fish_dict_by_color(fish_details: Dict[int, FishDetail]) -> Dict[int, Fish]:
    fish_by_type = {}
    for fish_id, fish_detail in fish_details.items():
        fish_by_type[fish_detail.color] = fish_by_type.get(fish_detail.type, []) + [
            fish_id
        ]
    return fish_by_type


fish_details = initilize_input(FishDetail)
all_fish_by_type: Dict[int, FishDetail] = fish_dict_by_type(fish_details)
all_fish_by_color: Dict[int, FishDetail] = fish_dict_by_color(fish_details)


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

        self.visible_fish = get_visible_fish()
        self.my_radar_blips = self.get_my_radar_blips(self.my_radar_blips)

    def all_fish_of_color_acievement_amount(self, fish: List[int]) -> int:
        # TODO: Check foe not already achieved.
        all_current_scanned_fish = [*fish, *self.my_scans]
        cnt = 0
        for fish_ids_by_color in all_fish_by_color.values():
            if set(fish_ids_by_color) <= set(all_current_scanned_fish):
                cnt += 1
        return cnt * 4

    def all_fish_of_type_acievement_amount(self, fish: List[int]):
        # TODO: Check foe not already achieved.
        all_current_scanned_fish = [*fish, *self.my_scans]
        cnt = 0
        for fish_ids_by_type in all_fish_by_type.values():
            if set(fish_ids_by_type) <= set(all_current_scanned_fish):
                cnt += 1
        return cnt * 3

    def is_first_fish_scanned(self, fish_id: int) -> int:
        return 1 if fish_id not in self.foe_scans else 0

    def get_fish_of_type_first_scanned_amount(self, fish: List[Fish]) -> int:
        return sum(self.is_first_fish_scanned(f) for f in fish)

    def get_achievements_amount_by_fish(self, fish: List[Fish]) -> int:
        return sum(
            [
                self.all_fish_of_type_acievement_amount(fish),
                self.all_fish_of_color_acievement_amount(fish),
                self.get_fish_of_type_first_scanned_amount(fish),
            ]
        )

    @cached_property
    def my_unscanned_fish_ids(self) -> List[int]:
        final_target_fish = [
            fish_id
            for fish_id in self.fish_details.keys()
            if fish_id not in self.my_scans
        ]
        for drone in self.my_drones:
            final_target_fish = [
                fish_id for fish_id in final_target_fish if fish_id not in drone.scans
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
            list(set([fish for drone in self.my_drones for fish in drone.scans]))
        )
        debug(f"{all_drone_achievements=} {max_achievements=} {base_acievemnts=}")
        if all_drone_achievements > max_achievements and all_drone_achievements - max_achievements > 5:
            return self.my_drones
        else:
            return drones_to_base

    def get_my_radar_blips(
        self, my_radar_blips: Dict[int, List[RadarBlip]]
    ) -> Dict[int, List[RadarBlip]]:
        my_radar_blip_count = int(input())
        for _ in range(my_radar_blip_count):
            drone_id, fish_id, dir = input().split()
            if int(fish_id) in self.my_unscanned_fish_ids:
                drone_id = int(drone_id)
                fish_id = int(fish_id)
                my_radar_blips[drone_id].append(RadarBlip(fish_id, dir))
        return my_radar_blips

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
            print(f"MOVE {loc.x} {loc.y} {light}")


game_turn = 1
while True:
    game = Game()
    game.run_turn()
    game_turn += 1
