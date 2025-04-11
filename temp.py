import os
import subprocess
from datetime import datetime, timedelta

locations = ["tokyo_tower", "senso_ji", "akihabara", "meiji_shrine", "tsukiji_market", "odaiba", "shinjuku_garden"]

travel_time_matrix = [
    [0, 62, 123, 185, 240, 300, 123], 
    [62, 0, 62, 123, 185, 240, 185],
    [123, 62, 0, 123, 185, 240, 185], 
    [185, 123, 123, 0, 123, 185, 62], 
    [240, 185, 185, 123, 0, 185, 123],
    [300, 240, 240, 185, 185, 0, 123],
    [123, 185, 185, 62, 123, 123, 0]
]

stay_times = {
    "tokyo_tower": 121, "senso_ji": 121, "akihabara": 121, "meiji_shrine": 121,
    "tsukiji_market": 121, "odaiba": 121, "shinjuku_garden": 121
}

DAY_START_TIME = "08:00"
DAY_TIME = 480

travel_times = {}
for i in range(len(locations)):
    for j in range(len(locations)):
        if i != j:
            travel_times[(locations[i], locations[j])] = travel_time_matrix[i][j]

def generate_pddl_files():
    with open("domain.pddl", "w") as f:
        f.write(f"""(define (domain tokyo_trip)
  (:requirements :strips :typing :action-costs)
  (:types day location)
  (:predicates
    (at ?loc - location)
    (available ?loc - location)
    (visited ?loc - location)
    (day_now ?d - day)
    (next_day ?d1 ?d2 - day)
  )
  (:functions (total-cost - number))
  
  (:action move
    :parameters (?from - location ?to - location)
    :precondition (and (at ?from) (available ?to))
    :effect (and (not (at ?from)) (at ?to) (increase (total-cost) (travel_time ?from ?to)))
  )

  (:action visit
    :parameters (?loc - location)
    :precondition (and (at ?loc) (available ?loc))
    :effect (and (visited ?loc) (increase (total-cost) (play_time ?loc)))
  )
)""")

    with open("problem.pddl", "w") as f:
        f.write(f"""(define (problem tokyo_trip_plan)
  (:domain tokyo_trip)
  (:objects {" ".join(locations)} - location
            day1 day2 day3 day4 day5 - day)
  (:init
    (at tokyo_tower)
    {" ".join(f"(available {loc})" for loc in locations)}
    (day_now day1)
    (next_day day1 day2) (next_day day2 day3) (next_day day3 day4) (next_day day4 day5)
    (= (total-cost) 0)
""")
        for loc, time in stay_times.items():
            f.write(f"    (= (play_time {loc}) {time})\n")
        for (loc1, loc2), time in travel_times.items():
            f.write(f"    (= (travel_time {loc1} {loc2}) {time})\n")
        f.write(f"""  )
  (:goal (and {" ".join(f"(visited {loc})" for loc in locations)}))
  (:metric minimize (total-cost))
)""")

generate_pddl_files()

def run_planner():
    cmd = ["python", "fast-downward.py", "--alias", "seq-sat-lama-2011", "domain.pddl", "problem.pddl"]
    subprocess.run(cmd, check=True)

run_planner()

def parse_sas_plan():
    plan_files = sorted([f for f in os.listdir() if f.startswith("sas_plan")], key=lambda x: os.path.getmtime(x))
    if not plan_files:
        raise FileNotFoundError("No sas_plan files found!")

    latest_plan = plan_files[-1]
    print(f"Using plan: {latest_plan}")

    with open(latest_plan, "r") as f:
        plan = f.readlines()

    current_day = 1
    total_time = 0
    start_time = datetime.strptime(DAY_START_TIME, "%H:%M")

    for action in plan:
        action = action.strip().lower()

        if action.startswith("(move") or action.startswith("(visit"):
            if total_time == 0:
                print(f"=== Start of Day {current_day} at {start_time.strftime('%I:%M %p')} ===")

            if action.startswith("(move"):
                _, from_loc, to_loc = action.strip("()").split()
                time_cost = travel_times.get((from_loc, to_loc), 10)
                start_activity_time = start_time + timedelta(minutes=total_time)
                total_time += time_cost
                current_time = start_time + timedelta(minutes=total_time)
                print(f"Day {current_day} - {start_activity_time.strftime('%I:%M %p')} to {current_time.strftime('%I:%M %p')}: MOVE {from_loc} -> {to_loc}")

            elif action.startswith("(visit"):
                _, loc = action.strip("()").split()
                play_time = stay_times.get(loc, 30)
                start_activity_time = start_time + timedelta(minutes=total_time)
                total_time += play_time
                current_time = start_time + timedelta(minutes=total_time)
                print(f"Day {current_day} - {start_activity_time.strftime('%I:%M %p')} to {current_time.strftime('%I:%M %p')}: VISIT {loc}")

        if total_time >= DAY_TIME:
            print(f"=== End of Day {current_day} at {current_time.strftime('%I:%M %p')} ===\n")
            current_day += 1
            total_time = 0
            start_time = datetime.strptime(DAY_START_TIME, "%H:%M")

    if total_time > 0:
        print(f"=== End of Day {current_day} at {current_time.strftime('%I:%M %p')} ===")

parse_sas_plan()
