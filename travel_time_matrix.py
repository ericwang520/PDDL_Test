import json
import requests
import numpy as np
import pandas as pd

# 範例 API 響應數據
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

def fetch_travel_time_data(app_id, api_key):
    """
    從 Travel Time API 獲取旅行時間數據
    """
    url = "https://api.traveltimeapp.com/v4/time-filter"
    params = {
        "type": "public_transport",
        "arrival_time": "2025-04-11T21:44:15.839Z",
        "search_lat": 35.65858,
        "search_lng": 139.74543,
        "locations": "35.71006_139.81070,35.71477_139.79665,35.68518_139.75280,35.67640_139.69933,35.71575_139.77453,35.68518_139.71005,35.66529_139.77077,35.62719_139.77684,35.65950_139.70049,35.68124_139.76712",
        "app_id": app_id,
        "api_key": api_key
    }
    
    response = requests.get(url, params=params)
    return response.json()

def extract_coordinates_and_times(response_data):
    """
    從 API 響應中提取坐標和旅行時間
    """
    if isinstance(response_data, str):
        data = json.loads(response_data)
    else:
        data = response_data
    
    locations = data['results'][0]['locations']
    
    # 提取坐標和時間
    coords_times = []
    for loc in locations:
        coord = loc['id']
        travel_time = loc['properties'][0]['travel_time']
        lat, lng = map(float, coord.split(','))
        coords_times.append((lat, lng, travel_time))
    
    return coords_times

def create_travel_time_matrix(coords_times):
    """
    創建旅行時間矩陣
    """
    n = len(coords_times)
    
    # 提取坐標和旅行時間
    coordinates = [(lat, lng) for lat, lng, _ in coords_times]
    times = [time for _, _, time in coords_times]
    
    # 創建位置標籤
    location_labels = [f"Loc_{i+1} ({lat:.5f}, {lng:.5f})" for i, (lat, lng, _) in enumerate(coords_times)]
    
    # 創建旅行時間矩陣 (假設是對稱的)
    matrix = np.zeros((n, n))
    
    # 由於API只提供了從搜索點到每個位置的時間，而非位置間的時間
    # 這裡我們做一個簡單假設：位置i到位置j的時間是它們到搜索點時間的差的絕對值
    # 實際應用中，您可能需要多次調用API來獲取完整的位置間時間矩陣
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0
            else:
                # 基於時間差的簡單假設
                matrix[i][j] = abs(times[i] - times[j])
    
    return matrix, location_labels

def format_matrix_output(matrix, labels):
    """
    格式化輸出矩陣
    """
    df = pd.DataFrame(matrix, index=labels, columns=labels)
    
    # 轉換為分鐘
    df = df / 60
    df = df.round(1)
    
    return df

def travel_time_matrix_from_api(use_sample=True, app_id=None, api_key=None):
    """
    主函數：從API獲取數據並生成旅行時間矩陣
    """
    if use_sample:
        response_data = api_response
    else:
        response_data = fetch_travel_time_data(app_id, api_key)
    
    coords_times = extract_coordinates_and_times(response_data)
    matrix, labels = create_travel_time_matrix(coords_times)
    formatted_df = format_matrix_output(matrix, labels)
    
    return formatted_df

if __name__ == "__main__":
    # 使用範例數據
    travel_matrix = travel_time_matrix_from_api()
    
    print("旅行時間矩陣 (分鐘):")
    print(travel_matrix)
    
    # 將矩陣保存為 CSV 檔案
    travel_matrix.to_csv("travel_time_matrix.csv")
    print("\n矩陣已保存為 travel_time_matrix.csv")
    
    # 生成 PDDL 格式的旅行時間定義
    print("\nPDDL 格式的旅行時間定義:")
    n = len(travel_matrix)
    for i in range(n):
        for j in range(n):
            if i != j:
                time_value = int(travel_matrix.iloc[i, j] * 60)  # 轉回秒
                print(f"(= (travel_time loc{i+1} loc{j+1}) {time_value})") 