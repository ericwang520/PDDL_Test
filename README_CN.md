# 東京旅行規劃系統

這是一個使用 PDDL（Planning Domain Definition Language）和 Fast Downward 規劃器創建旅行計劃的系統。特別為東京旅行設計，結合了 Travel Time API 提供的真實旅行時間數據。

## 功能

- 基於 PDDL 的多天旅行規劃
- 考慮景點開放時間
- 考慮交通時間
- 每天訪問景點數量限制
- 支持從 Travel Time API 獲取實際交通時間

## 使用方法

### 安裝依賴

```bash
pip install numpy pandas requests
```

### 運行規劃器

```bash
python travel_planner.py
```

這將使用默認參數（星期三開始，計劃 5 天行程）生成東京旅行計劃。每天訪問的景點數量被限制為 2 個。

### 使用 Travel Time API 更新旅行時間

```bash
python integrate_travel_times.py
```

預設使用示例數據。如果您擁有 Travel Time API 的憑證，可以使用實際 API：

```bash
python integrate_travel_times.py --real-api --app-id YOUR_APP_ID --api-key YOUR_API_KEY
```

## 自定義參數

您可以通過編輯 `travel_planner.py` 底部的以下變量來自定義旅行計劃：

```python
START_DAY_NAME = "wednesday"  # 旅行開始的星期幾
N_DAYS = 5                    # 旅行的總天數
```

您還可以修改 `opening_hours` 字典來自定義各景點的開放時間，或修改 `stay_times` 字典來調整各景點的參觀時間。

## 工作原理

1. `travel_planner.py` 生成 PDDL 域和問題文件
2. Fast Downward 規劃器求解旅行計劃問題
3. 解析方案並生成人類可讀的行程表

## Travel Time API 集成

`integrate_travel_times.py` 腳本用於將 Travel Time API 的實際交通時間數據集成到系統中：

- 從 API 獲取從搜索點到各景點的旅行時間
- 估算景點之間的旅行時間
- 生成旅行時間矩陣
- 更新 `travel_planner.py` 中的 `travel_time_matrix`
- 生成 PDDL 格式的旅行時間聲明（可複製到問題文件）
