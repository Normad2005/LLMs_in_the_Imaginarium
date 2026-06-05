# LLMs in the Imaginarium: 進度與策略同步 (Progress & Strategy Sync)

## 1. 目前進度 (Current Progress)

我們已經成功重構並穩定了核心的探索腳本，目前已完成以下關鍵進度：

*   **STE 探索腳本 (ste_runner.py) 穩定化**：
    *   成功套用原版 STE 論文的架構與 Prompt。
    *   修復了本機/遠端開源模型（如 `gpt-oss:120b`）常見的崩潰問題，包含：實作防呆重試迴圈（解決模型偶發性輸出空白）、修正 Stop-Token 導致的截斷問題，並將 Context Window 擴充至 16384 以容納巨大的 API 回傳值。
    *   **目前腳本已經可以全自動在背景穩定運行，探索 API 並收集對話軌跡。**
*   **關鍵瓶頸的實證觀察**：
    *   在執行過程中，我們觀察到一個極具研究價值的痛點：**當 LLM 面對包含十幾個參數的「巨型 API 文件」（如 `get_divisions_near_location`）時，認知負荷 (Cognitive Load) 會嚴重超載。**
    *   這導致模型在生成 Action JSON 時，注意力被龐雜的規則分散，頻繁出現格式錯誤、少括號、甚至直接中斷的問題。

---

## 2. 未來策略方針：分群與 API 文件拆分 (Clustering & API Decomposition)

為了徹底解決上述「巨型 API 文件導致 LLM 崩潰」的痛點，我們接下來的研究策略將圍繞在 **「將大 API 拆分為小 API (Decomposition)」**：

### 第一步：情境分群 (Intent Clustering) - *目前 `intent_definer.py` 正在做的*
1. 透過 STE 腳本讓 LLM 自由探索該 API 的各種可能用法，收集大量的 User Queries。
2. 利用 KMeans 等分群演算法，將這些 Queries 進行 Embedding 分群，歸納出該 API 的幾個核心「使用情境 (Intents)」。

### 第二步：利用 STE 探索萃取「小 API 文件」 (Empirical API Decomposition) - *接下來的核心亮點*
1. **核心痛點**：每一次 ReAct 呼叫，如果都把整包完整的 API 文件餵給 LLM，不僅浪費 Token，更會造成嚴重的「注意力渙散 (Cognitive Overload)」，導致 JSON 填寫錯誤。
2. **STE 的真正價值 (The "How")**：
   * 在 `intent_definer.py` 完成分群後，我們會針對**每一個特定的 Intent 群組**，獨立運行 `ste_runner.py` 進行探索。
   * 透過觀察 STE 在這個特定 Intent 下產生的大量「成功對話軌跡 (Successful Trajectories)」，我們可以**實證分析 (Empirically analyze)** 該 Intent 實際真正用到了哪些參數。
   * 根據這些真實的成功呼叫紀錄，我們將沒用到的冗餘參數直接剔除，為該 Intent 萃取出量身打造的**「精簡版 API 文件 (Small API Document)」**！

### 第三步：ICL 測試與 Token 成本統計 (ICL & Token Tracking)
1. 在利用 STE 軌跡成功萃取出「小 API 文件」後，我們將進入 **In-Context Learning (ICL)** 測試階段。
2. 針對未來的同類型 Query，我們只餵給 LLM「精簡版文件」，並附上 STE 跑出來的高品質軌跡作為 Few-shot 範例。

### 第四步：實驗評估與比較基準 (Evaluation Metrics & Baselines)
為了在論文/報告中強而有力地證明我們方法的優越性，接下來的評分 (Evaluation) 將著重於以下幾個維度：
1. **比較基準 (Baselines)**：
   * **Baseline (傳統 Retrieve)**：Retrieve 回「同樣數量/長度」的原始完整 API 文件（不做拆分）。
   * **Proposed (Intent-based Small API)**：Retrieve 回我們透過 STE 萃取出的「意圖專屬小 API 文件」。
2. **評分指標 (Metrics)**：
   * **格式錯誤率 (JSON Error Rate)**：比較兩者在 Action JSON 填寫時的語法錯誤或幻覺頻率（證明小文件能降低 Cognitive Load）。
   * **任務成功率 (Task Success Rate)**：最終是否成功呼叫 API 並獲取正確資訊。
   * **Token 消耗與成本 (Token Cost)**：精準計算 `prompt_tokens` 的下降幅度，證明小文件的經濟效益。
   * **互動回合數 (ReAct Turns)**：統計成功解決問題所需的平均回合數（回合數越少，代表模型一次就做對，沒有陷入 error retry 迴圈）。

---
*文件更新時間：2026-06-05*
