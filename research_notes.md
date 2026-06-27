# LLMs in the Imaginarium: 核心測試與生成準則
*(這份紀錄保存了本專案最核心的 Prompt 工程、測資生成方向、與踩坑經驗，供未來 IDE 重啟時快速恢復 Context 使用)*

---

## 1. 核心評估理念 (Core Evaluation Philosophy)
1. **Parameter Over-population (參數過度生成)**：小模型 (SLM) 在面對複雜 API Schema 時，容易發生「自作聰明」填滿未要求參數的幻覺（例如看到總價與頭期款，就自己算數學求出 `loan_amount` 並塞給 API）。這在真實系統是致命的。
2. **極端干擾測試 (Adversarial Testing)**：必須採用「地獄級干擾」來測試模型的抗壓性，包含：
   - 混入強烈干擾 API (例如測試 Hotel 時，Background Tool 裡一定要放 Restaurant)。
   - 每次推論前**完全隨機洗牌 API 順序**，破除 Recency Bias (模型依賴最後一個 API 的偏誤)。
3. **嚴格字串比對 (Strict Eval)**：只要模型輸出未被要求的參數（哪怕值是正確的），即判定為 Fail。這能最大化凸顯 Intent-based Splitting 帶來的防呆價值。

---

## 2. 測資生成策略 (Test Query Generation Strategy)
為了突顯「語意糾纏 (Semantic Entanglement)」對大型 Schema 的致命影響，測試問句**絕對不能像機器人**。必須包裝成真實世界的使用者情境 (NLU Wrappers)。

### 具體生成方向 (以 60 題終極測試為例)：
*   **Mortgage (房貸)**：
    *   ❌ *不要這樣寫*：`Calculate mortgage for home_value 500000 and downpayment 100000.`
    *   ✅ *應該這樣寫*：`I am looking at a $500,000 condo. I will put down $100,000. Calculate the monthly cost.`
    *   *目標*：刻意不提 `loan_amount`，誘使未切分前的大 API (Group A) 掉入算數學並過度填充參數的陷阱。
*   **Hotels & Restaurants (旅遊餐飲)**：
    *   ❌ *不要這樣寫*：`Find restaurants within bl_lat 40.7, tr_lat 40.8, bl_lon -74.1, tr_lon -74.0.`
    *   ✅ *應該這樣寫*：`My phone's GPS indicates my current view spans from latitude 40.7 to 40.8, and longitude -74.1 to -74.0. Can you recommend 5 places to eat?`
    *   *目標*：將生硬的 Bounding Box 經緯度，包裝成「使用者正在滑動地圖 App」的情境。
*   **Divisions (行政區)**：
    *   *情境包裝*：扮演工程師查系統 Log (`Include deleted records since yesterday for my daily audit.`) 或遊客規劃路線 (`planning a road trip`)。

---

## 3. 實驗架構避坑指南 (Lessons Learned & Pitfalls)
*   **動態 Intent ID 綁定 (Critical Bug Avoided)**：
    *   *慘痛教訓*：在生成測試資料時，如果強制將 Ground Truth Intent ID 寫死為 0，會導致進階查詢（如使用者指定語言 `lang` 或幣別 `currency`）的模型，在 Group B 測試中拿不到對應的 API 欄位，從而引發「Wrong API」或強行幻覺的災難。
    *   *解決方案*：必須使用腳本動態掃描測資的 `action_input`，若包含進階參數 (`adults`, `currency` 等)，才將 `target_intent_id` 設為進階 Intent (例如 1)。

---

## 4. 論文方法論結論分類 (Methodology Categorization)
根據 60 題的實測結果 (Group B 總分勝出 +15%)，未來論文在撰寫 Method 時，應將 API 分為三類探討：
1.  **高度語意糾纏區 (如 Mortgage)**：參數間有數學或互斥關係。切分機制能達成**決定性的輾壓 (+50% 以上提升)**，完美防止參數幻覺。
2.  **正交但高複雜度區 (如 Hotels)**：參數多但各自獨立。切分機制能**顯著降低認知負載**，幫助小模型專注於核心資訊，正確率提升約 20~30%。
3.  **正交且低複雜度區 (如 Restaurants)**：參數少且獨立。切分機制體現 **Do No Harm (無害原則)**，維持原有準確率 (80% vs 80%)。
