from __future__ import annotations
import math
from typing import List, Dict, Tuple
from dataclasses import dataclass


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


@dataclass
class Fish:
    fish_id: int
    pos: Location
    speed: Location
    detail: FishDetail


@dataclass
class RadarBlip:
    fish_id: int
    dir: str


@dataclass
class Drone:
    drone_id: int
    pos: Location
    dead: bool
    battery: int
    scans: List[int]


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


def get_closest_visible_unexplored_fish(
    visible_fish: List[Fish], scans: List[Fish], drone_location: Location
) -> Location:
    available_fish: List[Fish] = [
        fish for fish in visible_fish if fish.fish_id not in scans
    ]
    sorted_by_distance = sorted(
        available_fish, key=lambda fish: drone_location.distance(fish.pos)
    )
    return sorted_by_distance[0].pos if len(sorted_by_distance) > 0 else drone_location


def get_my_radar_blips(
    my_radar_blips: Dict[int, List[RadarBlip]]
) -> Dict[int, List[RadarBlip]]:
    my_radar_blip_count = int(input())
    for _ in range(my_radar_blip_count):
        drone_id, fish_id, dir = input().split()
        drone_id = int(drone_id)
        fish_id = int(fish_id)
        my_radar_blips[drone_id].append(RadarBlip(fish_id, dir))
    return my_radar_blips


def initilize_input(FishDetail):
    fish_details: Dict[int, FishDetail] = {}

    fish_count = int(input())
    for _ in range(fish_count):
        fish_id, color, _type = map(int, input().split())
        fish_details[fish_id] = FishDetail(color, _type)
    return fish_details


fish_details = initilize_input(FishDetail)


class Game:
    def __init__(self) -> None:
        self.my_score = int(input())
        self.foe_score = int(input())

        self.my_scans = get_scans()
        self.foe_scans = get_scans()

        self.my_drones, self.my_radar_blips = get_drone_info()
        self.foe_drones, self.foe_radar_blips = get_drone_info()

        self.drone_by_id = get_drone_by_id(self.my_drones, self.foe_drones)
        update_scans(self.drone_by_id)

        self.visible_fish = get_visible_fish()
        self.my_radar_blips = get_my_radar_blips(self.my_radar_blips)

    def run_turn(self) -> None:
        for drone in self.my_drones:
            x = drone.pos.x
            y = drone.pos.y
            loc = get_closest_visible_unexplored_fish(
                self.visible_fish, self.my_scans, drone.pos
            )
            # TODO: Implement logic on where to move here
            target_x = 5000
            target_y = 5000
            light = 1

            print(f"MOVE {loc.x} {loc.y} {light}")


while True:
    game = Game()
    game.run_turn()
