# TranslateGemma Project Blueprint

## 1) 產品定位與願景
- 目標: 把 TranslateGemma 打造成「本地優先、可擴充、跨模態」的多語言翻譯工作台。
- 核心價值:
  - 一站式: 文字、圖片、PDF、語音、影片、會議摘要都能處理。
  - 可控性: 本地模型 + 可選雲端模型，兼顧隱私與品質。
  - 專業化: 支援術語表、翻譯記憶、風格指南與品質評分。

## 2) 當前能力盤點 (As-Is)
- 已有功能:
  - Text / Image OCR / PDF / Voice / Streaming / Video dubbing / Meeting summary
  - Web UI (Gradio), API (FastAPI), MCP server
- 主要風險:
  - 文件編碼與結構不一致，影響維護與 onboarding
  - 翻譯品質尚未有標準化評估流程
  - 缺少術語管理、翻譯記憶、批次工作流與權限/配額設計

## 3) To-Be 全方位翻譯大師能力地圖
- 核心引擎層:
  - 多模型路由 (Ollama/Gemma + 可選 Gemini/OpenAI)
  - 品質評分與自動重寫 (Quality Estimation + Self-Refine)
  - 術語表/風格指南/翻譯記憶 (TM)
- 工作流層:
  - 批次翻譯管線 (資料夾、CSV、SRT、DOCX、XLSX)
  - 任務佇列與重試機制
  - 版本化輸出與差異比對
- 產品層:
  - 專案空間 (Project/Workspace)
  - 團隊協作 (角色、審核、註解)
  - 跨平台入口 (Web、MCP、未來桌面/瀏覽器插件)

## 4) 專案文件藍圖 (Documentation Architecture)
建議在 `docs/` 維護以下文件:

1. `docs/PRODUCT_VISION.md`
- 產品願景、目標客群、核心場景、非目標。

2. `docs/PRD.md`
- 需求定義: User stories、成功指標、MVP 範圍、驗收標準。

3. `docs/ARCHITECTURE.md`
- 系統架構圖、模組邊界、資料流、第三方依賴。

4. `docs/API_SPEC.md`
- API 契約、錯誤碼、版本策略、範例請求/回應。

5. `docs/QUALITY_PLAN.md`
- 翻譯品質指標 (BLEU/COMET + 人評)、測試集、回歸流程。

6. `docs/OPERATIONS.md`
- 部署、監控、日誌、故障排除、資源需求。

7. `docs/SECURITY_PRIVACY.md`
- 本地資料策略、PII 處理、金鑰管理、模型輸入輸出保護。

8. `docs/ROADMAP.md`
- 季度里程碑、風險、依賴、Done 定義。

9. `docs/CONTRIBUTING.md`
- 開發流程、分支策略、PR 規範、測試與 lint 規範。

10. `docs/DECISIONS/` (ADR)
- 重大技術決策紀錄 (Architecture Decision Records)。

## 5) 里程碑規劃 (30 / 60 / 90 天)

### 0-30 天: 基礎穩定 + 文件重建
- 目標:
  - 完成文件重建與統一編碼 (UTF-8)
  - 建立品質基線與最小回歸測試
- 交付:
  - 完整 `docs/` 骨架
  - 20-50 筆多語測試集 (中英日韓 + 長文/PDF/OCR)
  - CI: 單元測試 + smoke test
- 成功指標:
  - 新成員 1 小時可完成本地啟動
  - 關鍵流程 (text/image/pdf/voice) smoke test 全綠

### 31-60 天: 品質提升 + 生產工作流
- 目標:
  - 引入術語表、翻譯記憶、批次翻譯
  - 增加品質評分與人審流程
- 交付:
  - `glossary` 與 `translation_memory` 模組
  - 批次任務佇列與任務狀態頁
  - 品質報表 (每語對、每模型)
- 成功指標:
  - 專業領域文案術語一致率 > 90%
  - 批次任務失敗可重試且可追蹤

### 61-90 天: 平台化 + 生態整合
- 目標:
  - 多模型路由 + 成本/延遲策略
  - 更完整的 API/MCP 能力與插件化
- 交付:
  - Provider 抽象層 (Local/Cloud)
  - API v1 穩定版 + Webhook/Job API
  - MCP 新工具: `translate_pdf`, `translate_batch`, `list_languages`
- 成功指標:
  - 平均翻譯延遲下降 30%
  - API/MCP 使用量穩定成長，錯誤率 < 1%

## 6) 技術實作優先順序
1. 文件與編碼治理 (先解決可維護性)
2. 測試框架與品質評估基線
3. 術語表 + 翻譯記憶
4. 批次管線與任務管理
5. 多模型路由與品質自動重寫

## 7) KPI 與驗收標準
- 品質: COMET/人評分數持續上升
- 速度: p95 延遲、每千字成本、GPU/CPU 使用率
- 穩定: API 成功率、任務重試成功率
- 產品: DAU、留存率、批次任務完成率

## 8) 下一步 (本週可執行)
1. 建立 `docs/` 文件骨架與模板 (PRD/Architecture/API/Quality)
2. 新增 `tests/smoke/` 覆蓋 text/image/pdf/voice
3. 建立 `datasets/eval/` 小型多語評測集
4. 在 UI 加入「術語表」與「翻譯風格」選項 (先做設定，後接引擎)
5. 規劃 `provider` 抽象介面，為多模型路由做準備

## 9) 風險與對策
- 模型輸出不穩定: 增加 quality gate + fallback model
- OCR 品質波動: 預處理與語言自動偵測
- 影片/語音耗時高: 佇列化、快取與切片平行處理
- 維運負擔增加: 模組化與可觀測性先行

---

這份藍圖可作為未來 3 個月的執行主線。若你同意，我下一步可以直接幫你把 `docs/` 的 10 份文件模板一次建立好，讓團隊可立即填寫與追蹤。
