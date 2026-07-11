# STE Oracle 15 APIs 評估流程

本專案實作了針對 LLM 的 Oracle 15 APIs 評估流程，主要分為以下階段來進行資料準備、推論、評估與計分：

## 1. 資料準備階段 (Data Preparation)

在這個階段，我們需要準備模型推論所需的 Prompt，包含檢索好的範例 (In-Context Learning Demos) 以及受限的 API 描述。

* **檢索 ICL 範例 (Demo Retrieval)**
  執行 `run_demo_retrieve_complex_apis.py`，該腳本會讀取準備好的訓練集 (`results/ste/gpt_tool_data_train_35_APIs.json`) 與原始測試集 (`tool_metadata/test_queries_grouped.json`)。
  它會過濾出 10 個特定的複雜 API，並使用 `paraphrase-mpnet-base-v2` 嵌入模型，針對這 10 個 API 的每一個測試 Query，從訓練集中計算餘弦相似度，尋找最相似的 8 個範例 (Top 8 Demos)，最後輸出您的測試集檔案 `tool_metadata/test_queries_with_demo_complex_APIs.json` 供推論階段讀取。

* **準備 Oracle 15 APIs 的機制 (基於語意相似度檢索)**
  根據 STE 論文中的設定與專案的實際實作 (`Exploitation/oracle_runner.py`)，我們並不是隨機挑選干擾的 API，而是**動態檢索最相似的 API** 來挑戰模型：
  1. **嵌入模型 (Embedding)**：使用 `SentenceTransformer("sentence-transformers/paraphrase-mpnet-base-v2")` 將全部 35 個 API 的描述 (Description) 轉換為 Embedding 向量。
  2. **相似度比對**：針對每一個測試樣本的 Ground Truth API，計算其與所有 35 個 API 的餘弦相似度 (Cosine Similarity)。
  3. **挑選候選名單**：選出分數最高的 Top 15 個 APIs（這 15 個必定包含 Ground Truth API 本身，以及 14 個在語意與功能上最相近、最容易混淆的干擾 API）。
  4. **隨機打亂**：在組裝 Prompt 前，這 15 個候選 API 的順序會被隨機打亂 (Shuffle)，以防止 LLM 透過選項的固定位置來作弊。

## 2. 模型推論階段 (Inference)

資料準備好後，就可以讓模型進行推論。

* 執行修改好的推論程式：
  ```bash
  python Exploitation/oracle_runner.py
  ```
* **運作機制與參數**：
  * **推論模型**：專案中使用了 `llama3.1:8b-instruct-fp16` 作為基底模型。
  * 模型會讀取 `tool_metadata/test_queries_with_demo_complex_APIs.json`（這份資料已經預先包含了 8 個 ICL Demos），並根據 Oracle (Top 15 相似 API) 的 Prompt 模板 (`prompts/prompt_template.txt`) 進行生成，輸出它認為應該呼叫的 API 以及填寫的參數。最後將結果儲存成推論結果檔（例如 `results/icl/outputs_oracle_15.json`）。

## 3. 評估階段 (Evaluation)

驗證模型輸出的結果是否正確。

* 執行評估程式：
  ```bash
  python Exploitation/evaluation.py
  ```
* **運作機制**：
  此步驟需確保 `evaluation.py` 讀取的是剛剛產生出的推論結果檔。這支程式會透過腳本邏輯（如字串比對或數值比較），去判定模型預測的 API 及參數是否與 Ground Truth (標準答案) 相符，並在資料上打上「成功/失敗」等標籤。

## 4. 計算最終分數 (Scoring)

統計每個 API 的正確率。

* 執行計分程式：
  ```bash
  python Exploitation/get_per_api_accuracy.py
  ```
* **運作機制與結果**：
  這是整個流程的最後一步，它會統整 `evaluation.py` 判定過的資料，並計算出每一個 API 的正確率（Accuracy）。

  **最新的 Oracle 測試準確率結果已完整儲存至** `results/per_api_accuracy_summary.json`。

  **Oracle Complex APIs (10 APIs) 準確率測試結果**：
  * `get_hotels_by_location`: **100.00%** (15/15)
  * `get_planet_data`: **86.67%** (13/15)
  * `get_flights_in_bounding_box`: **80.00%** (12/15)
  * `calculate_mortgage_payment`: **73.33%** (11/15)
  * `get_restaurants_by_location`: **73.33%** (11/15)
  * `get_divisions_near_location`: **73.33%** (11/15)
  * `get_trades_futures`: **60.00%** (9/15)
  * `calculate_route`: **40.00%** (6/15)
  * `search_businesses`: **40.00%** (6/15)
  * `list_of_deals`: **26.67%** (4/15)

  <details>
  <summary><b>Oracle Simple APIs (25 APIs) 準確率測試結果 (點擊展開)</b></summary>
  
  * `verify_email`: **100.00%** (15/15)
  * `convert_currency`: **100.00%** (15/15)
  * `get_lol_champion_stats`: **100.00%** (15/15)
  * `get_airport_delay_statistics`: **100.00%** (15/15)
  * `get_timezone_info`: **100.00%** (15/15)
  * `get_celestial_body_position`: **100.00%** (15/15)
  * `get_handball_scheduled_matches`: **100.00%** (15/15)
  * `get_weather_forecast`: **100.00%** (15/15)
  * `get_animal_facts`: **93.33%** (14/15)
  * `search_public_restrooms`: **93.33%** (14/15)
  * `get_dog_breeds_metadata`: **93.33%** (14/15)
  * `get_air_quality_data`: **93.33%** (14/15)
  * `search_manga`: **86.67%** (13/15)
  * `search_exercises_by_name`: **86.67%** (13/15)
  * `get_recipe`: **86.67%** (13/15)
  * `get_airlines`: **73.33%** (11/15)
  * `get_motorcycle_data`: **73.33%** (11/15)
  * `get_financial_data`: **66.67%** (10/15)
  * `search_cocktails`: **66.67%** (10/15)
  * `search_arxiv_papers`: **66.67%** (10/15)
  * `search_amazon_products`: **66.67%** (10/15)
  * `get_media_news`: **53.33%** (8/15)
  * `get_filtered_game_giveaways`: **53.33%** (8/15)
  * `search_streaming_shows`: **46.67%** (7/15)
  * `get_salary_estimation`: **40.00%** (6/15)
  </details>

---

## 5. 整體評估實驗結果 (Overall Evaluation Results)

以下是使用 `evaluation.py` 計算出的各項實驗設定成績匯總：

### Table 1: Generation Performance (End-to-End)

| 設定 (Configuration)               | Well-formed Rate | API Match (LLM) | Argument Correctness (Strict) | Avg Prompt Tokens |
| :--------------------------------- | :--------------: | :-------------: | :---------------------------: | :---------------: |
| **Unsplit (Lower Bound)**       |      99.33%      |     99.33%      |            72.67%             |       6003        |
| **Split (Golden Upper Bound)**  |     100.00%      |    100.00%      |            80.00%             |       5867        |
| **Dynamic Union (End-to-End)**  |      99.05%      |    100.00%      |            79.05%             |       5844        |
| **Top-1 Intent (Ablation)**     |      99.05%      |     98.08%      |            74.29%             |       5548        |
| **Oracle Complex (10 APIs)**    |     100.00%      |     98.00%      |            65.33%             |       7978        |
| **Oracle Simple (25 APIs)**     |     100.00%      |     96.27%      |            81.60%             |       5575        |

### Table 2: Retrieval Performance (HyDE + Dense Retrieval, Top-10)

| 指標 (Metric)                   | 數值 (Value) |
| :------------------------------ | :----------: |
| 🎯 **Global API Recall@10**      |   100.00%    |
| 🎯 **Intra-API Intent Recall@1** |    84.00%    |

---
