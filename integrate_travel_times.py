import json
import requests
import numpy as np
import pandas as pd
import os
import argparse

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

# 範例 API 響應數據 (如果您不使用真實 API 調用)
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

def construct_request_locations(locations_dict):
    """
    從地點字典構建 API 請求的 locations 參數
    """
    return ",".join([f"{lat}_{lng}" for lat, lng in locations_dict.values()])

def fetch_travel_time_data(app_id, api_key, locations_dict, search_point=None):
    """
    從 Travel Time API 獲取旅行時間數據
    search_point: 搜索起點坐標元組 (lat, lng)，默認使用東京塔
    """
    if search_point is None:
        search_point = locations_dict["tokyo_tower"]  # 默認以東京塔為搜索起點
    
    url = "https://api.traveltimeapp.com/v4/time-filter"
    params = {
        "type": "public_transport",
        "arrival_time": "2025-04-11T12:00:00.000Z",  # 使用中午時間作為到達時間
        "search_lat": search_point[0],
        "search_lng": search_point[1],
        "locations": construct_request_locations(locations_dict),
        "app_id": app_id,
        "api_key": api_key
    }
    
    response = requests.get(url, params=params)
    return response.json()

def find_closest_coordinates(api_coords, our_coords_dict):
    """
    找到 API 返回坐標最接近我們的哪個地點
    """
    api_lat, api_lng = api_coords
    
    min_distance = float('inf')
    closest_loc = None
    
    for loc_name, (loc_lat, loc_lng) in our_coords_dict.items():
        # 使用簡單的歐氏距離計算
        distance = ((api_lat - loc_lat)**2 + (api_lng - loc_lng)**2)**0.5
        if distance < min_distance:
            min_distance = distance
            closest_loc = loc_name
    
    return closest_loc

def extract_travel_times(response_data, loc_dict):
    """
    從 API 響應中提取旅行時間並映射到我們的地點
    """
    if isinstance(response_data, str):
        data = json.loads(response_data)
    else:
        data = response_data
    
    locations = data['results'][0]['locations']
    
    # 創建一個字典來存儲旅行時間
    travel_times = {}
    for loc in locations:
        coord_str = loc['id']
        lat, lng = map(float, coord_str.split(','))
        travel_time = loc['properties'][0]['travel_time']
        
        # 找到最接近的已知地點
        closest_loc = find_closest_coordinates((lat, lng), loc_dict)
        if closest_loc:
            travel_times[closest_loc] = travel_time
    
    return travel_times

def create_travel_time_matrix(loc_dict, travel_times_from_search):
    """
    創建完整的旅行時間矩陣
    
    這裡我們使用一個簡化的假設：
    地點 A 到地點 B 的時間 = |地點 A 到搜索點的時間 - 地點 B 到搜索點的時間|
    
    注意：這只是一個粗略的估計。真實世界中，您應該為每對地點獲取實際的旅行時間。
    """
    locations = list(loc_dict.keys())
    n = len(locations)
    
    # 創建空矩陣
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    
    # 填充矩陣
    for i, loc_i in enumerate(locations):
        for j, loc_j in enumerate(locations):
            if i == j:
                matrix[i][j] = 0  # 同一地點之間的時間為0
            else:
                # 使用時間差估計
                time_i = travel_times_from_search.get(loc_i, 0)
                time_j = travel_times_from_search.get(loc_j, 0)
                
                # 使用時間差的絕對值作為近似
                # 這只是一個估計，實際應用中應該為每對地點獲取準確的旅行時間
                matrix[i][j] = abs(time_i - time_j)
    
    return matrix, locations

def generate_pddl_time_declarations(matrix, locations):
    """
    生成 PDDL 格式的旅行時間聲明
    """
    declarations = []
    
    for i, loc_i in enumerate(locations):
        for j, loc_j in enumerate(locations):
            if i != j:
                time_value = matrix[i][j]
                declarations.append(f"(= (travel_time {loc_i} {loc_j}) {time_value})")
    
    return declarations

def integrate_with_travel_planner_py(matrix, locations):
    """
    將生成的矩陣集成到 travel_planner.py 文件中
    """
    # 先讀取現有的 travel_planner.py
    try:
        with open("travel_planner.py", "r", encoding="utf-8") as f:
            content = f.readlines()
    except FileNotFoundError:
        print("未找到 travel_planner.py 文件")
        return False
    
    # 構建新的 travel_time_matrix 定義，嚴格按照原始格式
    matrix_lines = []
    matrix_lines.append("travel_time_matrix = [\n")
    for row in matrix:
        row_str = "    ["
        for i, val in enumerate(row):
            row_str += str(int(val))  # 確保值是整數
            if i < len(row) - 1:
                row_str += ", "
        row_str += "],"
        matrix_lines.append(row_str + "\n")
    matrix_lines.append("]\n")
    
    # 查找矩陣定義的開始和結束行
    start_line = -1
    end_line = -1
    for i, line in enumerate(content):
        if line.strip().startswith("travel_time_matrix = ["):
            start_line = i
        if start_line != -1 and line.strip() == "]":
            end_line = i
            break
    
    if start_line != -1 and end_line != -1:
        # 替換矩陣定義
        new_content = content[:start_line] + matrix_lines + content[end_line+1:]
        
        # 寫回文件
        with open("travel_planner.py", "w", encoding="utf-8") as f:
            f.writelines(new_content)
        print("成功更新 travel_planner.py 中的旅行時間矩陣")
        return True
    else:
        print("無法在 travel_planner.py 中找到完整的 travel_time_matrix 定義")
        return False

def save_matrix_for_inspection(matrix, locations, filename="travel_time_matrix.csv"):
    """
    將旅行時間矩陣保存為 CSV 文件以便查看
    """
    df = pd.DataFrame(matrix, index=locations, columns=locations)
    df.to_csv(filename)
    print(f"矩陣已保存至 {filename}")

def main(use_sample_data=True, app_id=None, api_key=None):
    """
    主函數
    """
    # 使用範例數據或從 API 獲取實際數據
    if use_sample_data:
        response_data = api_response
        print("使用範例數據...")
    else:
        if not app_id or not api_key:
            print("缺少 API 憑證，無法從 API 獲取數據")
            return
        response_data = fetch_travel_time_data(app_id, api_key, locations_with_coords)
        print("從 API 獲取數據成功")
    
    # 提取旅行時間數據
    travel_times = extract_travel_times(response_data, locations_with_coords)
    
    # 創建旅行時間矩陣
    matrix, locs = create_travel_time_matrix(locations_with_coords, travel_times)
    
    # 保存矩陣以便查看
    save_matrix_for_inspection(matrix, locs)
    
    # 生成 PDDL 格式的旅行時間聲明
    pddl_declarations = generate_pddl_time_declarations(matrix, locs)
    
    # 打印 PDDL 聲明（以便複製到 PDDL 文件）
    print("\nPDDL 旅行時間聲明:")
    for decl in pddl_declarations:
        print(decl)
    
    # 嘗試集成到 travel_planner.py
    integrate_with_travel_planner_py(matrix, locs)
    
    return matrix, locs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='整合 Travel Time API 數據到旅行規劃系統')
    parser.add_argument('--real-api', action='store_true', help='使用真實 API 而非示例數據')
    parser.add_argument('--app-id', type=str, help='Travel Time API 的 App ID')
    parser.add_argument('--api-key', type=str, help='Travel Time API 的 API Key')
    parser.add_argument('--save-csv', type=str, default='travel_time_matrix.csv',
                        help='保存 CSV 矩陣的文件名 (默認: travel_time_matrix.csv)')
    
    args = parser.parse_args()
    
    if args.real_api and (not args.app_id or not args.api_key):
        print("錯誤: 使用真實 API 時必須提供 app-id 和 api-key")
        parser.print_help()
        exit(1)
    
    main(use_sample_data=not args.real_api, app_id=args.app_id, api_key=args.api_key) 