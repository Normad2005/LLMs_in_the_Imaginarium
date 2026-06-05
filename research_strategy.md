# From Trial-and-Error to Tool Errata: Intent-Aware API Decomposition for Small Language Models

## 研究概覽

本研究提出一套以意圖為導向的工具勘誤生成框架（Intent-Guided Tool Errata Generation）。核心概念是：**將一份對小型語言模型（7-8B）來說過於複雜的 API 文件，根據使用意圖拆解成數份各自聚焦於單一情境的小型 API 文件（Tool Erratum Unit）**，讓小模型在推論時只需閱讀與當前任務相關的那一份，從根本上降低認知負擔。

---

## 問題動機

小型語言模型在工具呼叫任務中的主要瓶頸，並非推理能力不足，而是**資訊處理負擔過重**。一份完整的 API 文件往往同時描述多種使用情境與大量參數，小模型容易「迷失在中間（Lost in the Middle）」，無法判斷哪些參數與當前查詢相關，導致參數填寫錯誤。

傳統 STE（Simulated Trial and Error）方法透過累積成功案例（demonstrations）來輔助模型，但模型學到的是「當問題是 A，就用參數 B」的表層模仿，而非對 API 使用邏輯的真正理解。此外，STE 的探索是隨機的，可能集中在某些使用情境，導致其他情境覆蓋不足。

---

## 核心概念：Tool Erratum Unit

Tool Erratum Unit 是本研究的核心產出，定位為**意圖專屬的小型 API 文件**，由三個部分組成：

```
Tool Erratum Unit
├── Scenario    → 一句話描述此意圖的使用情境（用於推論時的語意檢索）
├── Small API Doc → 2-3 條精簡規則（取代冗長的原始 API Description）
└── Trail Results → 2-3 筆代表性的成功探索案例（作為 few-shot 示範）
```

### 對比示例：Football Stats API

**原始 API Description（對小模型不友善）：**

```json
{
  "optional_parameters": [
    { "name": "first_team",        "type": "String"  },
    { "name": "second_team",       "type": "String"  },
    { "name": "type_of_statistics","type": "Enum", "options": ["full time result", "half time result", ...] },
    { "name": "league_id",         "type": "Integer" },
    { "name": "season",            "type": "String", "description": "Format: YYYY" },
    { "name": "page",              "type": "Integer", "default": 1 }
  ]
}
```

6 個參數混在一起，小模型無法判斷哪些參數適用於當前情境。

**拆分後的 Tool Erratum Units（對小模型友善）：**

```
Unit 0: Head-to-Head Query
  Scenario      : When the user wants to compare the historical match
                  record between two specific teams.
  Small API Doc : - Both first_team and second_team must be provided;
                    omitting either will result in an error.
                  - Team names must match the exact full names used
                    in the database (no abbreviations or nicknames).
  Trail Results : [2-3 successful trajectories]

Unit 1: Single Team Performance
  Scenario      : When the user wants to check the recent performance
                  or statistics of one specific team.
  Small API Doc : - Provide first_team only; leave second_team empty.
                  - Use season (format: YYYY) to restrict results
                    to a specific season if needed.
  Trail Results : [2-3 successful trajectories]

Unit 2: League Standings
  Scenario      : When the user wants to retrieve the overall
                  standings or rankings of a league.
  Small API Doc : - Do not provide team names; use league_id instead.
                  - season is required and must follow the YYYY format.
  Trail Results : [2-3 successful trajectories]
```

每個 Unit 只有 2 條規則，小模型讀完立刻知道該填什麼，不會被其他意圖的參數干擾。

---

## 完整流程

### Phase 1：意圖定義（Intent Definition）

**執行腳本：** `intent_definer.py`

強模型（GPT-4）閱讀每個 API 的原始 Description，判斷該 API 是否需要拆分以及拆成幾個意圖。

**拆分準則：**
- 只有當一個 API 存在多個本質不同的使用情境，且各情境所需的核心參數群互不相同，小模型若閱讀完整文件會產生混淆，才進行拆分
- 若參數差異只是「填不同的值」或「使用不同的可選篩選條件」，維持為 1 個意圖，不拆分
- 簡單 API → 1 個意圖；複雜 API → N 個意圖（上限 5 個）

**輸出：** `results/intent_definitions.json`

```json
{
  "calculate_mortgage_payment": {
    "num_intents": 3,
    "intents": [
      {
        "intent_id": 0,
        "name": "Basic Mortgage Payment",
        "description": "The user knows the loan amount and wants to calculate the monthly payment."
      },
      {
        "intent_id": 1,
        "name": "Mortgage from Home Value",
        "description": "The user provides home value and downpayment, letting the API derive the loan amount."
      },
      {
        "intent_id": 2,
        "name": "Total Home Ownership Cost",
        "description": "The user wants the full monthly cost including HOA, property tax, and insurance."
      }
    ]
  },
  "get_motorcycle_data": {
    "num_intents": 1,
    "intents": [
      {
        "intent_id": 0,
        "name": "Motorcycle Lookup",
        "description": "The user wants to look up motorcycle data using any combination of make, model, and year as filters."
      }
    ]
  }
}
```

---

### Phase 2：意圖導向的 STE 探索（Intent-Guided STE Exploration）

**執行腳本：** `ste_runner.py`（更新版）

對每個意圖獨立執行一輪 STE loop，確保每個意圖都有足夠的探索覆蓋。

**流程：**
```
對每個 API：
  讀取該 API 的 intent_definitions
  對每個 intent：
    根據 intent description 生成 pseudo query（受意圖描述約束）
    執行 ReAct 推理 + 真實 API 呼叫
    記錄完整軌跡（Thought / Action / Observation）
    Reflection 判斷成功或失敗
    標記 intent_id 到每個 session
```

**與原始 STE 的差異：**

| | 原始 STE | 本方法 |
|---|---|---|
| 查詢生成 | 隨機，可能集中在某些情境 | 受意圖描述引導，每個意圖獨立探索 |
| 覆蓋保證 | 無法保證每種用法都被探索 | 每個意圖都有獨立的 episodes 配額 |
| 事後分群 | 需要（clustering） | 不需要（session 已帶 intent_id） |

**輸出：** `results/ste/ste_output.json`（每個 session 帶有 `intent_id`）

---

### Phase 3：Tool Erratum Unit 生成（Semantic Abstraction）

**執行腳本：** `tool_erratum_builder.py`

對每個意圖的 STE 軌跡，強模型將探索經驗蒸餾為精簡規則。

**軌跡分類（資訊量由高到低）：**

```
修正軌跡（Correction）：第一輪失敗但後來成功
  → 直接呈現「填錯了什麼 → 如何修正」，是最有資訊量的來源

純失敗軌跡（Pure Failure）：全程失敗
  → 顯示常見的錯誤模式與 API 的隱性約束

純成功軌跡（Pure Success）：第一輪即成功
  → 確認正確的參數用法
```

**生成規則的要求：**
- 最多 3 條規則，相關約束合併成一句
- 具體而非抽象（例：「states 必須是大寫州別縮寫，以逗號分隔，如 NY,FL」）
- 排除 ReAct 格式規則、API 選擇規則、重複規則

**空意圖處理：** 若某意圖的 STE 完全沒有 session 被分配到，仍保留該 Unit，規則純粹從 API Description 生成，examples 欄位為空。

**輸出：** `results/tool_errata_repository.json`

---

### Phase 4：推論時的語意檢索（Semantic Retrieval at Inference）

**執行腳本：** `erratum_retrieve.py`

```
User Query
    ↓
[假想情境生成] 模型將 query 轉換為抽象的情境描述（Hypothetical Scenario）
    ↓
[Unit 檢索] 假想情境 embedding 比對所有 Unit 的 Scenario embedding（跨所有 API）
    ↓
取 Top-K 個最相關的 Unit
（Unit 所屬的 api_name 即為候選工具）
    ↓
[Prompt 組裝] Small API Doc（規則）+ Trail Results（案例）
    ↓
小模型選出正確 API + 填入正確參數
```

**假想情境生成的目的：** 橋接用戶自然語言與 Unit Scenario 的語意空間，減少直接用 query 比對 Scenario 時的語意落差（借鑑 ToolDreamer 的 Hypothetical Document Embedding 概念）。

---

## 實驗設計

### 測試集

從 ToolBench 的 RapidAPI 中挑選 30 個 API，確保：
- 全部可正常呼叫（人工驗證）
- 覆蓋 12 個功能領域
- 難易度分層（簡單 API vs. 複雜 API）

**關鍵分組（核心分析）：**

```
簡單 API（1 個 intent，不拆分）：~15 個
複雜 API（2+ 個 intent，拆分）  ：~15 個
```

分組報告結果可直接論證：**本方法對複雜 API 的提升幅度明顯大於簡單 API**，是核心 claim 的直接驗證。

---

### 比較方法（Baselines）

| 方法 | 說明 | Prompt 內容 | 文件數量 |
|---|---|---|---|
| Full Desc | 全部 API Description | 所有 N 個 API 的完整文件 | N 份 |
| **Retrieve Doc** | 檢索最相似的完整 API Doc | Top-K 個完整 API Description | K 份 |
| ICL | 傳統 RAG | 完整 API Desc + 相似案例 | N 份 + examples |
| **Retrieve Unit（proposed）** | 檢索最相似的 Tool Erratum Unit | Top-K 個 Small API Doc + Trail Results | K 份 |

**Retrieve Doc vs. Retrieve Unit 是最關鍵的比較：**
- 文件數量相同（都是 K 份）
- 檢索機制相同（embedding 相似度）
- 唯一差異：文件內容（完整 description vs. 意圖專屬精簡文件）

---

### 消融實驗

| 實驗組 | retrieve_desc | 說明 |
|---|---|---|
| erratum_none | none | 純靠 Unit（無 API Description） |
| erratum_filtered | filtered | Unit + 對應 API 的完整 Description |

---

### 評估指標

| 指標 | 說明 |
|---|---|
| API Match Rate | 選對 API 的比例（分母排除格式錯誤） |
| Argument Correctness | 參數填寫正確率（分母為全部樣本） |
| Wellformed Rate | 輸出格式正確率 |
| Avg Prompt Tokens | 平均 prompt token 數（來自 Ollama done chunk 的 `prompt_eval_count`） |

---

### 實驗矩陣

```
                        小模型（Llama-3-8B）                大模型（GPT-4o）
                   API    Args   Tokens            API    Args   Tokens
Full Desc           -      -       -                -      -       -
Retrieve Doc(K=2)   -      -       -                -      -       -
ICL                 -      -       -                -      -       -
Retrieve Unit(K=2)  -      -       -                -      -       -
  └ erratum_none    -      -       -                -      -       -
  └ erratum_filtered-      -       -                -      -       -
```

**預期論證：**
1. 小模型 Retrieve Unit > Retrieve Doc → 拆分後比完整文件有效（核心 claim）
2. 複雜 API 組的提升幅度 > 簡單 API 組 → 拆分對複雜 API 最有效
3. 小模型 Retrieve Unit ≈ 大模型 Full Desc → 靠 errata 縮小大小模型差距
4. Retrieve Unit tokens << Full Desc tokens → 效率提升

---

## 程式碼架構

```
專案根目錄
├── intent_definer.py          # Phase 1：定義每個 API 的使用意圖
├── ste_runner.py              # Phase 2：意圖導向的 STE 探索
├── tool_erratum_builder.py    # Phase 3：生成 Tool Erratum Units
├── erratum_retrieve.py        # Phase 4：推論時的語意檢索
│
├── doc_retrieve.py            # Baseline：檢索完整 API Description
├── demo_retrieve.py           # 跨 API 的 demo 檢索（ICL 用）
│
├── icl_runner.py              # 推論執行（default / ICL / semantic）
│   └── --retrieve_desc        #   all：全部 API desc
│                              #   filtered：只放 demo 出現的 API desc
│
├── erratum_runner.py          # 推論執行（erratum）
│   └── --retrieve_desc        #   none：純靠 Unit
│                              #   filtered：Unit + 對應 API desc
│
└── evaluation.py              # 評估（API Match / Args Correct / Tokens）
```

---

## 執行流程

```bash
# Step 1: 定義意圖（人工審查輸出後再繼續）
python intent_definer.py

# Step 2: STE 探索
python ste_runner.py

# Step 3: 生成 Tool Erratum Units
python tool_erratum_builder.py

# Step 4: 推論前的檢索前處理
python erratum_retrieve.py          # 生成 tool_test_with_erratum.json
python demo_retrieve.py             # 生成 tool_test_with_demo.json（ICL 用）
python doc_retrieve.py              # 生成 tool_test_with_doc.json（baseline 用）

# Step 5: 推論
python icl_runner.py --setting default --retrieve_desc all
python icl_runner.py --setting default --retrieve_desc filtered
python icl_runner.py --setting ICL --retrieve_desc all
python icl_runner.py --setting ICL --retrieve_desc filtered
python erratum_runner.py --retrieve_desc none
python erratum_runner.py --retrieve_desc filtered

# Step 6: 評估
python evaluation.py
```
