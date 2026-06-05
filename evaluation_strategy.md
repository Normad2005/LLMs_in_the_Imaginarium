# Evaluation Strategy

## 1. 測試集設計

### API 組成
從 RapidAPI 篩選 30 個 API，涵蓋 12 個功能領域。所有 API 均經人工實際呼叫驗證，確保即時可用且回應格式與文件描述一致。

依據 `intent_definer.py` 的輸出，將 30 個 API 分為兩組：

| 組別 | 定義 | 數量（預計） |
|---|---|---|
| **Simple APIs** | `num_intents == 1`，不需要拆分 | ~15 個 |
| **Complex APIs** | `num_intents >= 2`，需要拆分為多個 Tool Erratum Units | ~15 個 |

分組報告結果，用以驗證核心 claim：**本方法對 Complex APIs 的提升幅度顯著大於 Simple APIs**。

---

## 2. 評估指標

### 2.1 Wellformed Rate
$$\text{Wellformed} = \frac{\text{non\_err}}{\text{total}}$$

模型輸出能被成功解析為合法 API 呼叫的比例。以下任一情況計為格式錯誤（`err=1`）：
- `parse_successful == False`：模型未遵循 Action / Action Input 格式
- `action_input` 無法被解析為合法 JSON

> 若模型直接輸出 Final Answer 而未呼叫 API（`finish=True`），計為 `no_call`，不列入 wellformed 計算。

### 2.2 API Match Rate
$$\text{API Match} = \frac{\text{api\_match}}{\text{non\_err}}$$

在格式正確的輸出中，模型選出正確 API 的比例。分母排除格式錯誤的樣本。

### 2.3 Argument Correctness
$$\text{Correct} = \frac{\text{args\_correct}}{\text{total}}$$

模型填入的參數與 ground truth 相符的比例，分母為全部樣本。

參數正確性的判斷方式依 API 類型而異：

- **String Match APIs**（14 個，如 `verify_email`、`get_car_makes`）：
  對每個 ground truth 參數 key，檢查模型輸出中對應 key 的值是否完全相符（不區分大小寫）。
  
- **Semantic Match APIs**（其餘 16 個）：
  由強模型（GPT-4o）語意判斷是否正確，判斷依據為：
  > "The API call doesn't have to be exactly identical to the ground truth, but the argument names and structure should exactly follow the API Description."
  
  回應以 "Yes." 開頭視為正確，以 "No." 開頭視為錯誤。

### 2.4 Avg Prompt Tokens（Token 效率）
$$\text{Avg Prompt Tokens} = \frac{\sum \text{prompt\_tokens}}{\text{count}}$$

每筆推論的 prompt token 數平均值，直接從 Ollama 回應的 `prompt_eval_count` 欄位取得（非估算）。用以衡量各方法的推論成本。

---

## 3. 比較方法（Baselines & Proposed）

### 3.1 方法列表

| 方法 | 說明 | Prompt 內容 | 資料來源 |
|---|---|---|---|
| **Full Desc** | 所有 API 的完整 description 全部放入 prompt | N 個完整 API desc | `tool_test.json` |
| **Full Desc + ICL** | 完整 desc + 跨 API 檢索的相似案例 | N 個完整 API desc + K 筆 examples | `tool_test_with_demo.json` |
| **Retrieve Doc** *(baseline)* | 檢索 Top-K 個最相似的完整 API description | K 份完整 API desc | `tool_test_with_doc.json` |
| **Retrieve Unit** *(proposed)* | 檢索 Top-K 個最相關的 Tool Erratum Unit | K 份小型文件（rules + examples） | `tool_test_with_erratum.json` |
| **Retrieve Unit + Desc** *(ablation)* | Retrieve Unit + 對應 API 的完整 description | K 份小型文件 + K 份完整 desc | `tool_test_with_erratum.json` |

> **Retrieve Doc 與 Retrieve Unit 的控制變因：**
> 兩者的文件數量相同（均為 Top-K），檢索機制相同（embedding 相似度），
> 唯一差異為文件內容：前者為完整 API description，後者為意圖專屬的精簡文件。

### 3.2 K 值設定
Retrieve Doc 和 Retrieve Unit 均使用 `K=2`，與 `erratum_retrieve.py` 的 `TOP_K` 設定一致。

### 3.3 執行檔對應

| 方法 | 執行檔 | 參數 |
|---|---|---|
| Full Desc | `icl_runner.py` | `--setting default --retrieve_desc all` |
| Full Desc + ICL | `icl_runner.py` | `--setting ICL --retrieve_desc all` |
| Full Desc + ICL (filtered) | `icl_runner.py` | `--setting ICL --retrieve_desc filtered` |
| Retrieve Doc | `doc_runner.py` | `--retrieve_desc none` |
| Retrieve Unit | `erratum_runner.py` | `--retrieve_desc none` |
| Retrieve Unit + Desc | `erratum_runner.py` | `--retrieve_desc filtered` |

---

## 4. 模型設定

| 模型 | 角色 | 用途 |
|---|---|---|
| GPT-4o（`gpt-oss:120b`） | 強模型 | Upper bound；Argument Correctness 語意判斷 |
| Llama-3-8B（`llama3.1:8b-instruct-fp16`） | 小模型 | 主要評估對象 |

每個方法分別用兩個模型執行，共產出以下輸出檔：

```
results/icl/
  outputs_default_all.json           ← Full Desc, Llama
  outputs_default_all_baseline.json  ← Full Desc, GPT
  outputs_ICL_all.json               ← ICL, Llama
  outputs_ICL_filtered.json          ← ICL filtered, Llama
  outputs_erratum_none.json          ← Retrieve Unit, Llama
  outputs_erratum_filtered.json      ← Retrieve Unit + Desc, Llama
  outputs_doc_none.json              ← Retrieve Doc, Llama
```

---

## 5. 主要結果表格

### 5.1 全體 API

| 方法 | Wellformed (%) | API Match (%) | Correct (%) | Avg Tokens |
|---|---|---|---|---|
| Full Desc (GPT-4o) | - | - | - | - |
| Full Desc (Llama-8B) | - | - | - | - |
| Full Desc + ICL (Llama-8B) | - | - | - | - |
| Retrieve Doc, K=2 (Llama-8B) | - | - | - | - |
| **Retrieve Unit, K=2 (Llama-8B)** | - | - | - | - |
| Retrieve Unit + Desc (Llama-8B) | - | - | - | - |

### 5.2 依 API 複雜度分組

| 方法 | Simple APIs Correct (%) | Complex APIs Correct (%) |
|---|---|---|
| Full Desc (GPT-4o) | - | - |
| Full Desc (Llama-8B) | - | - |
| Retrieve Doc (Llama-8B) | - | - |
| **Retrieve Unit (Llama-8B)** | - | - |

> 預期結果：Retrieve Unit 對 Complex APIs 的提升幅度顯著大於 Simple APIs，
> 驗證「將複雜 API 文件拆解為意圖專屬小型文件」的核心貢獻。

---

## 6. 消融實驗（Ablation Study）

| 移除的組件 | 對應方法 | 目的 |
|---|---|---|
| 移除 Tool Errata rules，只保留 Examples | 修改 `build_erratum_block()`，略去 rules | 驗證規則本身的貢獻（vs. 純案例） |
| 移除 Examples，只保留 rules | 修改 `build_erratum_block()`，略去 examples | 驗證案例的貢獻（vs. 純規則） |
| 用完整 API desc 取代 Small API doc | `Retrieve Unit + Desc` | 驗證「精簡文件」vs「完整文件 + Unit 結構」 |
| 不做假想情境生成，直接用 query 檢索 | 修改 `erratum_retrieve.py` | 驗證 Hypothetical Scenario 的貢獻 |

---

## 7. 執行順序

```
# Step 1：建立 Tool Errata Repository（離線，只需執行一次）
python intent_definer.py
python ste_runner.py
python postprocessing.py
python tool_erratum_builder.py

# Step 2：建立測試集的檢索結果
python erratum_retrieve.py      → tool_test_with_erratum.json
python demo_retrieve.py         → tool_test_with_demo.json
python doc_retrieve.py          → tool_test_with_doc.json

# Step 3：執行推論
python icl_runner.py --setting default --retrieve_desc all
python icl_runner.py --setting ICL --retrieve_desc all
python icl_runner.py --setting ICL --retrieve_desc filtered
python erratum_runner.py --retrieve_desc none
python erratum_runner.py --retrieve_desc filtered
python doc_runner.py

# Step 4：評分
python evaluation.py
# eval_pred_file(file) → 標註每筆結果
# eval_batch(file)     → 印出 Wellformed / API Match / Correct / Avg Tokens
```
