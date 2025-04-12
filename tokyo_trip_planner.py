import os
import subprocess
import json
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import argparse
import logging

# 定義地點名稱和其對應的坐標
locations_with_coords = {
    "tokyo_tower": (35.65858, 139.74543),        # 東京塔
    "senso_ji": (35.71477, 139.79665),           # 淺草寺
    "akihabara": (35.70006, 139.77446),          # 秋葉原
    "meiji_shrine": (35.67640, 139.69933),       # 明治神宮
    "tsukiji_market": (35.66529, 139.77077),     # 築地市場
    "odaiba": (35.62523, 139.77567),             # 台場
    "shinjuku_garden": (35.68518, 139.71005),    # 新宿御苑
}

# 從 locations_with_coords 中提取地點名稱
locations = list(locations_with_coords.keys())

stay_times = {
    "tokyo_tower": 60,
    "senso_ji": 30,
    "akihabara": 40,
    "meiji_shrine": 50,
    "tsukiji_market": 60,
    "odaiba": 40,
    "shinjuku_garden": 50
}

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

opening_hours = {
    "tokyo_tower": {
        "monday":    [(9,17)],
        "tuesday":   [(10,20)],
        "wednesday": [(8,12),(13,18)],
        "thursday":  [],
        "friday":    [(9,17)],
        "saturday":  [(10,16)],
        "sunday":    [(10,16)],
    },
    "senso_ji": {
        "monday":    [(8,18)],
        "tuesday":   [(8,18)],
        "wednesday": [(8,18)],
        "thursday":  [(8,18)],
        "friday":    [(8,18)],
        "saturday":  [(8,18)],
        "sunday":    [(8,18)],
    },
    "akihabara": {
        "monday":    [(10,22)],
        "tuesday":   [(10,22)],
        "wednesday": [(10,22)],
        "thursday":  [(10,22)],
        "friday":    [(10,22)],
        "saturday":  [(10,22)],
        "sunday":    [(10,22)],
    },
    "meiji_shrine": {
        "monday":    [(8,16)],
        "tuesday":   [(8,16)],
        "wednesday": [(8,16)],
        "thursday":  [(8,16)],
        "friday":    [(8,16)],
        "saturday":  [(8,16)],
        "sunday":    [(8,16)],
    },
    "tsukiji_market": {
        "monday":    [(6,14)],
        "tuesday":   [(6,14)],
        "wednesday": [(6,14)],
        "thursday":  [(6,14)],
        "friday":    [(6,14)],
        "saturday":  [(6,14)],
        "sunday":    [(6,14)],
    },
    "odaiba": {
        "monday":    [(10,21)],
        "tuesday":   [(10,21)],
        "wednesday": [(10,21)],
        "thursday":  [(10,21)],
        "friday":    [(10,21)],
        "saturday":  [(10,21)],
        "sunday":    [(10,21)],
    },
    "shinjuku_garden": {
        "monday":    [(9,17)],
        "tuesday":   [(9,17)],
        "wednesday": [(9,17)],
        "thursday":  [(9,17)],
        "friday":    [(9,17)],
        "saturday":  [(9,17)],
        "sunday":    [(9,17)],
    },
}

time_slots = [f"ts_{h}" for h in range(24)]

# 範例 API 響應數據 (僅作參考，不再使用)
api_response = '''
{
    "results": [
        {
            "search_id": "Matrix",
            "locations": [
                {
                    "id": "35.68124,139.76712",
                    "properties": [
                        {
                            "travel_time": 1653
                        }
                    ]
                },
                {
                    "id": "35.71477,139.79665",
                    "properties": [
                        {
                            "travel_time": 2782
                        }
                    ]
                },
                {
                    "id": "35.66529,139.77077",
                    "properties": [
                        {
                            "travel_time": 1505
                        }
                    ]
                },
                {
                    "id": "35.6595,139.70049",
                    "properties": [
                        {
                            "travel_time": 2002
                        }
                    ]
                },
                {
                    "id": "35.68518,139.71005",
                    "properties": [
                        {
                            "travel_time": 2213
                        }
                    ]
                },
                {
                    "id": "35.71006,139.8107",
                    "properties": [
                        {
                            "travel_time": 2812
                        }
                    ]
                },
                {
                    "id": "35.6764,139.69933",
                    "properties": [
                        {
                            "travel_time": 2658
                        }
                    ]
                },
                {
                    "id": "35.71575,139.77453",
                    "properties": [
                        {
                            "travel_time": 2336
                        }
                    ]
                },
                {
                    "id": "35.68518,139.7528",
                    "properties": [
                        {
                            "travel_time": 2355
                        }
                    ]
                },
                {
                    "id": "35.62719,139.77684",
                    "properties": [
                        {
                            "travel_time": 3564
                        }
                    ]
                }
            ],
            "unreachable": []
        }
    ]
}
'''

# === Travel Time API 功能 ===
def construct_request_locations(locations_dict, exclude=None):
    """
    從地點字典構建 API 請求的 locations 參數。
    如果提供 exclude，則不包含該地點。
    """
    return ",".join([f"{lat}_{lng}" for name, (lat, lng) in locations_dict.items() if exclude is None or name != exclude])

def fetch_travel_time_data_from_origin(origin, app_id, api_key, locations_dict):
    """
    從指定的起點 (origin) 出發，查詢到其他所有地點的旅行時間 (one-to-many)。
    使用 GET 請求傳遞查詢參數。
    """
    search_point = locations_dict[origin]
    url = "https://api.traveltimeapp.com/v4/time-filter"
    params = {
        "type": "public_transport",
        "arrival_time": "2025-04-11T12:00:00.000Z",  # 使用中午作為到達時間
        "search_lat": search_point[0],
        "search_lng": search_point[1],
        "locations": construct_request_locations(locations_dict, exclude=origin),
        "app_id": app_id,
        "api_key": api_key
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    print(f"API 回應 (origin: {origin}):", response.json())
    return response.json()

def get_travel_time_data(use_api, app_id, api_key):
    """
    獲取旅行時間數據，強制使用 API 取得真實數據。
    返回 travel_times 字典，其中鍵為 (起點, 終點)，值為以分鐘為單位的旅行時間。
    """
    logging.basicConfig(
        filename='tokyo_trip_planner.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("開始獲取旅行時間數據 (使用 API 取得實時數據)")
    
    if not app_id or not api_key:
        raise ValueError("必須提供 API 憑證 (app_id 與 api_key)，無法繼續。")
    
    travel_times = {}
    for origin in locations:
        try:
            print(f"查詢從 {origin} 出發的旅行時間...")
            data = fetch_travel_time_data_from_origin(origin, app_id, api_key, locations_with_coords)
            results = data.get("results", [])
            if results:
                result = results[0]
                for loc in result.get("locations", []):
                    coord_str = loc.get("id", "")
                    try:
                        lat, lng = map(float, coord_str.split(","))
                    except Exception as e:
                        continue
                    # 將 API 返回的座標映射到我們的景點名稱
                    dest = find_closest_coordinates((lat, lng), locations_with_coords)
                    # API 返回的 travel_time 為秒，轉換為分鐘
                    time_sec = loc.get("properties", [{}])[0].get("travel_time", 0)
                    time_min = int(time_sec // 60) if time_sec else 0
                    travel_times[(origin, dest)] = time_min
            else:
                logging.error(f"無結果返回，origin: {origin}")
        except Exception as e:
            error_msg = f"查詢 {origin} 時發生錯誤: {e}"
            print(error_msg)
            logging.error(error_msg)
    
    if not travel_times:
        raise ValueError("無法從 API 獲取任何旅行時間數據，請檢查 API 憑證和網絡連接。")
    
    print_travel_time_matrix(travel_times, locations)
    
    # 輸出一些關鍵路線檢查
    key_routes = [
        ('akihabara', 'meiji_shrine'),
        ('tokyo_tower', 'tsukiji_market'),
        ('meiji_shrine', 'senso_ji')
    ]
    print("\n關鍵旅行時間 (分鐘):")
    for from_loc, to_loc in key_routes:
        t = travel_times.get((from_loc, to_loc), 0)
        print(f"  {from_loc} → {to_loc}: {t} 分鐘")
        logging.info(f"旅行時間: {from_loc} → {to_loc}: {t} 分鐘")
    
    return travel_times

def find_closest_coordinates(api_coords, our_coords_dict):
    """
    找到 API 返回坐標最接近我們的哪個地點
    """
    api_lat, api_lng = api_coords
    min_distance = float('inf')
    closest_loc = None
    for loc_name, (loc_lat, loc_lng) in our_coords_dict.items():
        distance = ((api_lat - loc_lat) ** 2 + (api_lng - loc_lng) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_loc = loc_name
    return closest_loc

def print_travel_time_matrix(travel_times, locations):
    """
    將旅行時間矩陣以表格形式打印出來，並保存到文件中
    """
    matrix = []
    header = [""] + locations
    matrix.append(header)
    
    for loc1 in locations:
        row = [loc1]
        for loc2 in locations:
            if loc1 == loc2:
                time_val = 0
            else:
                time_val = travel_times.get((loc1, loc2), 0)
            row.append(str(time_val))
        matrix.append(row)
    
    print("\n旅行時間矩陣（分鐘）:")
    for row in matrix:
        print("\t".join(row))
    
    with open("travel_time_matrix.txt", "w", encoding="utf-8") as f:
        for row in matrix:
            f.write("\t".join(row) + "\n")
    
    print("旅行時間矩陣已保存到 travel_time_matrix.txt")

# === PDDL 生成功能 ===

def generate_domain_pddl():
    """生成 PDDL 域文件"""
    domain_content = """(define (domain tokyo_trip)
  (:requirements :strips :typing :action-costs)
  (:types
    day location time_slot counter
  )
  (:predicates
    (at ?loc - location)
    (available ?loc - location)
    (visited ?loc - location)
    (day_now ?d - day)
    (next_day ?d1 ?d2 - day)
    (time_slot_now ?ts - time_slot)
    (next_slot ?ts1 ?ts2 - time_slot)
    (open ?loc - location ?d - day ?ts - time_slot)
    (visited_on_day ?loc - location ?d - day)
    (day_visit_count ?d - day ?n - counter)
    (next_count ?n1 ?n2 - counter)
    (max_visits_reached ?d - day)
  )
  (:functions
    (total-cost - number)
    (travel_time ?from - location ?to - location)
    (play_time ?loc - location)
  )
  (:action move
    :parameters (?from - location ?to - location ?d - day ?ts - time_slot)
    :precondition (and
      (at ?from)
      (available ?to)
      (day_now ?d)
      (time_slot_now ?ts)
      (open ?to ?d ?ts)
    )
    :effect (and
      (not (at ?from))
      (at ?to)
      (increase (total-cost) (travel_time ?from ?to))
    )
  )
  (:action visit
    :parameters (?loc - location ?d - day ?ts - time_slot ?n1 ?n2 - counter)
    :precondition (and
      (at ?loc)
      (available ?loc)
      (day_now ?d)
      (time_slot_now ?ts)
      (open ?loc ?d ?ts)
      (day_visit_count ?d ?n1)
      (next_count ?n1 ?n2)
      (not (max_visits_reached ?d))
    )
    :effect (and
      (visited ?loc)
      (visited_on_day ?loc ?d)
      (not (day_visit_count ?d ?n1))
      (day_visit_count ?d ?n2)
      (when (= ?n2 c2)\n        (max_visits_reached ?d))\n      (increase (total-cost) (play_time ?loc))\n    )\n  )\n  (:action advance_slot\n    :parameters (?ts1 - time_slot ?ts2 - time_slot ?d - day)\n    :precondition (and\n      (time_slot_now ?ts1)\n      (day_now ?d)\n      (next_slot ?ts1 ?ts2)\n    )\n    :effect (and\n      (not (time_slot_now ?ts1))\n      (time_slot_now ?ts2)\n      (increase (total-cost) 0)\n    )\n  )\n  (:action advance_day\n    :parameters (?d1 - day ?d2 - day)\n    :precondition (and\n      (day_now ?d1)\n      (next_day ?d1 ?d2)\n      (time_slot_now ts_23)\n    )\n    :effect (and\n      (not (day_now ?d1))\n      (day_now ?d2)\n      (not (time_slot_now ts_23))\n      (time_slot_now ts_8)\n      (increase (total-cost) 0)\n    )\n  )\n)"""    
    with open("domain.pddl", "w", encoding="utf-8") as f:
        f.write(domain_content)
    print("已生成 domain.pddl")

def generate_problem_pddl(start_day_name: str, n_days: int, travel_times_data=None):
    """
    根據旅行開始日期和天數生成PDDL問題文件
    
    參數:
        start_day_name: 旅行開始的星期幾 (例如: 'monday', 'tuesday'等)
        n_days: 旅行天數
        travel_times_data: 旅行時間數據，必須提供
    """
    # 檢查旅行時間數據
    if not travel_times_data:
        raise ValueError("必須提供旅行時間數據 (travel_times_data)。沒有提供數據無法進行規劃。")
        
    day_names = [f"day{i}" for i in range(1, n_days+1)]
    if start_day_name.lower() not in WEEKDAYS:
        raise ValueError(f"無效的星期名稱: {start_day_name}。必須是以下之一: {', '.join(WEEKDAYS)}")
    
    start_idx = WEEKDAYS.index(start_day_name.lower())
    
    # 根據天數選擇景點數量
    selected_locations = locations
    if n_days <= 3:
        selected_locations = ["tokyo_tower", "senso_ji", "akihabara", "meiji_shrine", "tsukiji_market"]
        print(f"因為旅行天數設定為{n_days}天，僅選擇5個景點進行規劃。")
    
    def get_weekday_for_day(i):
        return WEEKDAYS[(start_idx + i) % 7]
    
    problem_content = f"""(define (problem tokyo_trip_plan)
  (:domain tokyo_trip)

  (:objects
    {' '.join(selected_locations)} - location
    {' '.join(day_names)} - day
    {' '.join(time_slots)} - time_slot
    c0 c1 c2 - counter
  )

  (:init
    (at tokyo_tower)
"""
    for loc in selected_locations:
        problem_content += f"    (available {loc})\n"
    
    problem_content += "    (day_now day1)\n"
    problem_content += "    (time_slot_now ts_8)\n"
    
    for i in range(n_days - 1):
        problem_content += f"    (next_day {day_names[i]} {day_names[i+1]})\n"
    
    for h in range(23):
        problem_content += f"    (next_slot ts_{h} ts_{h+1})\n"
    
    # 設置計數器關係
    problem_content += "    (next_count c0 c1)\n"
    problem_content += "    (next_count c1 c2)\n"
    
    # 初始化每天的訪問計數為0
    for day in day_names:
        problem_content += f"    (day_visit_count {day} c0)\n"
    
    problem_content += "    (= (total-cost) 0)\n\n"
    
    # 設置景點停留時間
    for loc in selected_locations:
        pt = stay_times.get(loc, 121)
        problem_content += f"    (= (play_time {loc}) {pt})\n"
    
    # 設置旅行時間
    for (lf, lt), tval in travel_times_data.items():
        if lf in selected_locations and lt in selected_locations:
            problem_content += f"    (= (travel_time {lf} {lt}) {tval})\n"
    
    problem_content += "\n"
    
    # 設置開放時間
    for i, dname in enumerate(day_names):
        wd = get_weekday_for_day(i)
        for loc in selected_locations:
            intervals = opening_hours[loc].get(wd, [])
            for hour in range(24):
                for (start_h, end_h) in intervals:
                    if start_h <= hour < end_h:
                        problem_content += f"    (open {loc} {dname} ts_{hour})\n"
                        break
    
    problem_content += "  )\n\n  (:goal (and\n"
    
    for loc in selected_locations:
        problem_content += f"    (visited {loc})\n"
    
    problem_content += "  ))\n  (:metric minimize (total-cost))\n)\n"
    
    with open("problem.pddl", "w", encoding="utf-8") as f:
        f.write(problem_content)
    
    print("已生成 problem.pddl")

def run_planner():
    """運行 Fast Downward 規劃器"""
    print("\n正在運行 Fast Downward 規劃器...")
    cmd = ["python3", "fast-downward.py", "--alias", "seq-sat-lama-2011", "domain.pddl", "problem.pddl"]
    subprocess.run(cmd, check=True)

def parse_sas_plan_pretty(start_day):
    """解析和格式化 Fast Downward 規劃器生成的計劃"""
    plan_files = sorted([p for p in os.listdir('.') if p.startswith("sas_plan")], key=lambda x: os.path.getmtime(x))
    if not plan_files:
        print("未找到 sas_plan，規劃失敗。")
        return
    
    latest_plan = plan_files[-1]
    print(f"\n使用計劃文件: {latest_plan}\n")
    
    with open(latest_plan, "r", encoding="utf-8") as f:
        actions = [ln.strip().lower() for ln in f if ln.strip().startswith("(")]
    
    def get_time_for_slot(slot_name, day_num):
        hour = int(slot_name.replace("ts_", ""))
        today = datetime.now()
        start_weekday = WEEKDAYS.index(start_day.lower())
        current_weekday = today.weekday()
        days_until_start = (start_weekday - current_weekday) % 7
        travel_start_date = today if days_until_start == 0 else today + timedelta(days=days_until_start)
        trip_date = travel_start_date + timedelta(days=day_num - 1)
        return trip_date.replace(hour=hour, minute=0, second=0)
    
    current_day = 1
    current_slot = "ts_8"
    current_time = get_time_for_slot(current_slot, current_day)
    
    print("=" * 60)
    print("東京旅行計劃")
    print(f"開始日期: {datetime.now().strftime('%Y-%m-%d')} ({start_day.title()})")
    print("=" * 60)
    
    current_location = "tokyo_tower"
    
    for line in actions:
        tokens = line.strip("()").split()
        act = tokens[0]
        
        if act == "move":
            _, loc_from, loc_to, dayx, slot = tokens
            day_num = int(dayx.replace("day", ""))
            if day_num != current_day:
                current_day = day_num
                current_slot = "ts_8"
                current_time = get_time_for_slot(current_slot, current_day)
                current_location = loc_from
                print("\n" + "-" * 60)
                print(f"Day {current_day} - {WEEKDAYS[(WEEKDAYS.index(start_day.lower()) + current_day - 1) % 7].title()} ({current_time.strftime('%Y-%m-%d')})")
                print("-" * 60)
            elif slot != current_slot:
                new_time = get_time_for_slot(slot, current_day)
                if new_time > current_time:
                    current_time = new_time
                current_slot = slot
            if current_location != loc_from:
                current_location = loc_to
                continue
            tmin = travel_times.get((loc_from, loc_to), 30)
            start_t = current_time
            travel_minutes = min(max(tmin, 5), 60)
            end_t = start_t + timedelta(minutes=travel_minutes)
            travel_hours = int(travel_minutes // 60)
            travel_mins = int(travel_minutes % 60)
            time_desc = f"{travel_hours}小時{travel_mins}分鐘" if travel_hours > 0 else f"{travel_mins}分鐘"
            print(f"Day {current_day}, {start_t.strftime('%H:%M')} - {end_t.strftime('%H:%M')}: 移動 {loc_from} → {loc_to} ({time_desc})")
            current_time = end_t
            current_location = loc_to
        
        elif act == "visit":
            if len(tokens) >= 5:
                _, loc, dayx, slot = tokens[0:4]
            else:
                _, loc, dayx, slot = tokens
            day_num = int(dayx.replace("day", ""))
            if day_num != current_day:
                current_day = day_num
                current_slot = "ts_8"
                current_time = get_time_for_slot(current_slot, current_day)
                print("\n" + "-" * 60)
                print(f"Day {current_day} - {WEEKDAYS[(WEEKDAYS.index(start_day.lower()) + current_day - 1) % 7].title()} ({current_time.strftime('%Y-%m-%d')})")
                print("-" * 60)
            elif slot != current_slot:
                new_time = get_time_for_slot(slot, current_day)
                if new_time > current_time:
                    current_time = new_time
                current_slot = slot
            if current_location != loc and "advance_day" not in line:
                tmin = travel_times.get((current_location, loc), 30)
                travel_minutes = min(max(tmin, 5), 60)
                move_start_t = current_time
                move_end_t = move_start_t + timedelta(minutes=travel_minutes)
                travel_hours = int(travel_minutes // 60)
                travel_mins = int(travel_minutes % 60)
                time_desc = f"{travel_hours}小時{travel_mins}分鐘" if travel_hours > 0 else f"{travel_mins}分鐘"
                print(f"Day {current_day}, {move_start_t.strftime('%H:%M')} - {move_end_t.strftime('%H:%M')}: 移動 {current_location} → {loc} ({time_desc})")
                current_time = move_end_t
            pmin = stay_times.get(loc, 60)
            start_t = current_time
            end_t = start_t + timedelta(minutes=pmin)
            visit_hours = int(pmin // 60)
            visit_mins = int(pmin % 60)
            visit_desc = f"{visit_hours}小時{visit_mins}分鐘" if visit_hours > 0 else f"{visit_mins}分鐘"
            print(f"Day {current_day}, {start_t.strftime('%H:%M')} - {end_t.strftime('%H:%M')}: 參觀 {loc} ({visit_desc})")
            current_time = end_t
            current_location = loc
        
        elif act == "advance_slot":
            _, slot_old, slot_new, dayx = tokens
            day_num = int(dayx.replace("day", ""))
            if day_num != current_day:
                current_day = day_num
            new_time = get_time_for_slot(slot_new, current_day)
            if new_time > current_time:
                time_diff = (new_time - current_time).total_seconds() / 60
                if time_diff >= 30:
                    print(f"Day {current_day}, {current_time.strftime('%H:%M')} - {new_time.strftime('%H:%M')}: [空閒時間]")
                current_time = new_time
            current_slot = slot_new
        
        elif act == "advance_day":
            _, day_old, day_new = tokens
            day_num = int(day_new.replace("day", ""))
            current_day = day_num
            current_slot = "ts_8"
            current_time = get_time_for_slot(current_slot, current_day)
            print("\n" + "-" * 60)
            print(f"Day {current_day} - {WEEKDAYS[(WEEKDAYS.index(start_day.lower()) + current_day - 1) % 7].title()} ({current_time.strftime('%Y-%m-%d')})")
            print("-" * 60)
        else:
            print(f"未知動作: {line}")
    
    print("\n" + "=" * 60)
    print("行程結束")
    print("=" * 60)

def plan_tokyo_trip(start_day="wednesday", num_days=5, app_id=None, api_key=None):
    """
    一站式東京旅行規劃功能
    
    參數:
        start_day: 旅行開始的星期幾 (默認: wednesday)
        num_days: 旅行天數 (默認: 5)
        app_id: Travel Time API 的 App ID（必須提供）
        api_key: Travel Time API 的 API Key（必須提供）
    """
    logging.basicConfig(
        filename='tokyo_trip_planner.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    logging.info("="*50)
    logging.info(f"開始規劃東京旅行 (起始日: {start_day}, 天數: {num_days})")
    
    # 檢查 API 憑證
    if not app_id or not api_key:
        error_msg = "必須提供 Travel Time API 的 app_id 和 api_key。"
        print(error_msg)
        logging.error(error_msg)
        return False
    
    print("\n" + "=" * 60)
    print("東京旅行規劃系統")
    print("=" * 60)
    
    try:
        print("\n1. 獲取旅行時間數據...")
        global travel_times
        travel_times = get_travel_time_data(True, app_id, api_key)
        
        print("\n2. 生成 PDDL 文件...")
        logging.info("生成 PDDL 文件")
        generate_domain_pddl()
        generate_problem_pddl(start_day, num_days, travel_times)
        
        print("\n3. 運行規劃器...")
        logging.info("運行 Fast Downward 規劃器")
        try:
            planner_log_file = "planner_output.log"
            logging.info(f"規劃器輸出將保存到 {planner_log_file}")
            cmd = ["python3", "fast-downward.py", "--alias", "seq-sat-lama-2011", "domain.pddl", "problem.pddl"]
            with open(planner_log_file, "w") as log_file:
                subprocess.run(cmd, stdout=log_file, stderr=log_file, check=True)
            
            print(f"規劃器輸出已保存到 {planner_log_file}")
            logging.info("規劃器運行成功")
            
            print("\n4. 生成旅行計劃...")
            logging.info("生成旅行計劃")
            parse_sas_plan_pretty(start_day)
            logging.info("旅行計劃生成完成")
        except Exception as e:
            error_msg = f"\n錯誤: 規劃器運行失敗 - {str(e)}"
            print(error_msg)
            print("請確保 Fast Downward 規劃器已正確安裝並可運行。")
            logging.error(error_msg)
            return False
    except Exception as e:
        error_msg = f"\n錯誤: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        return False
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='東京旅行規劃系統 - 一站式旅行規劃解決方案')
    parser.add_argument('--start-day', type=str, default='wednesday', help='旅行開始的星期幾 (默認: wednesday)')
    parser.add_argument('--days', type=int, default=5, help='旅行天數 (默認: 5)')

    
    args = parser.parse_args()
    
    print(f"\nCommand line arguments:")
    print(f"Start day: {args.start_day}")
    print(f"Number of days: {args.days}")


    app_id = 'd5538d14'
    api_key = 'c2235a842d5e25a6905163aa1976c80e'
    
    plan_tokyo_trip(
        start_day=args.start_day,
        num_days=args.days,
        app_id=app_id,
        api_key=api_key
    )