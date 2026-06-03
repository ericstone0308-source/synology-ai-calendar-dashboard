# 🗓️ Synology NAS 3D 認知脈絡日曆與 Notion 儀表板

這是一個專為 Synology NAS 設計的個人排程與記事智慧整合系統。它能將您的 **Google 行事曆**（過去 30 天至未來 30 天）與 **Notion 隨手雜記**進行深度融合，並透過 **Google Gemini 2.5 Flash API** 生成具有前瞻性與回溯性的「3D 認知分析報告」，最後以極具質感的**深色太空玻璃擬態（Glassmorphism）時間軸與卡片**呈現在網頁儀表板上。

此專案完美支援電腦與手機瀏覽，並可搭配 **Tailscale** 進行安全的遠端外網存取。

---

## ✨ 核心特色
1. **三維時間智庫（3D Temporal Context Model）**：
   * **⏪ 過去回溯**：自動分析過去 30 天的已發生事項與 Notion 遺留待辦，消除記憶斷層。
   * **🔎 當下聚焦**：高解析度重新包裹一至兩週內的行程，串聯因果動作鏈（例如：「看診天＝領藥天，大門順手拿藥」）。
   * **⏩ 未來防禦**：預測未來一個月內的大型行程與瓶頸，提前給予防禦性建議。
2. **自動定時更新**：配合 NAS 系統 crontab 排程，每天上午 11:00 與下午 4:00 自動執行背景更新。
3. **優雅的視覺設計**：流暢的毛玻璃卡片、微光邊框與朦朧粒子背景，時間軸與備忘卡片點擊雙向發光滾動聯結。
4. **API 自動重試防禦**：針對 Gemini API 的 503 暫時不可用或 429 限流錯誤，內建指數退避重試機制。

---

## 📂 專案檔案結構
* `update_data.py`：主要的 Python 抓取與 AI 報告生成腳本。
* `SKILL.md`：供 AI 代理人讀取的技能部署規範說明書。
* `.env.example`：環境變數設定檔範本（包含 Notion 金鑰、Notion 頁面 ID、Gemini 金鑰）。
* `dashboard/`：儀表板的前端網頁檔案目錄。
  * `index.html`：網頁骨架（自適應佈局、搜尋與篩選）。
  * `style.css`：玻璃擬態深色太空風樣式表。
  * `app.js`：網頁渲染邏輯、時間戳記防快取讀取與雙向互動。

---

## 🛠️ 部署教學

### 第一步：在 NAS 建立專案目錄與複製檔案
1. 開啟 DSM 的 **File Station**。
2. 在 `web` 共用資料夾下建立名為 `calendar-dashboard` 的資料夾。
3. 將本專案的所有檔案（不含 `.git`）上傳至 `/web/calendar-dashboard`，其中網頁部分放在 `/web/calendar-dashboard/dashboard` 下。
4. 將 `.env.example` 重新命名為 `.env`，並填入您的金鑰：
   ```text
   NOTION_API_KEY=您的_Notion_API_金鑰
   NOTION_PAGE_ID=您的_Notion_頁面_ID
   GEMINI_API_KEY=您的_Gemini_API_金鑰
   ```
5. 將您在 Google Cloud Console 下載的 Google 日曆 OAuth 憑證 `client_secret.json` 與已授權的 `token.json` 也上傳至 `/web/calendar-dashboard/`。

### 第二步：安裝 Python 虛擬環境
1. 使用 SSH 連線至您的 Synology NAS：
   ```bash
   ssh your_nas_username@your_nas_ip
   ```
2. 切換至專案目錄並建立虛擬環境：
   ```bash
   cd /volume1/web/calendar-dashboard
   python3 -m venv venv
   ```
3. 安裝所需的依賴套件：
   ```bash
   ./venv/bin/pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib requests
   ```
4. 測試執行：
   ```bash
   ./venv/bin/python update_data.py
   ```
   *成功執行後，會在 `dashboard/` 底下看到生成的 `data.json`。*

### 第三步：設定自動更新排程 (Cron)
我們需要讓系統每天自動更新兩次。請在 NAS 的 `/etc/crontab` 中加入以下排程（欄位之間必須使用 **TAB** 鍵隔開）：
```text
0	11,16	*	*	*	您的NAS帳號	cd /volume1/web/calendar-dashboard && ./venv/bin/python update_data.py > /volume1/web/calendar-dashboard/cron_run.log 2>&1
```
修改後重啟排程服務：
```bash
sudo systemctl restart crond
```

### 第四步：在 Web Station 建立網頁服務
1. 開啟 NAS 中的 **Web Station**。
2. 點選 **網頁服務入口** > **建立服務入口** > 選擇 **網頁服務入口**。
3. 新增一個網頁服務：
   * **名稱**：`calendar-dashboard`
   * **主目錄**：選擇 `/web/calendar-dashboard/dashboard`
   * **HTTP 後端伺服器**：選擇 `Nginx`
4. 入口類型選擇 **連接埠對應**，勾選 **HTTP**，埠號設定為 **`8085`**（或您喜歡的埠號）。
5. 點選儲存後，在瀏覽器輸入 `http://<您的NAS_IP>:8085` 即可存取！

---

## 🔒 遠端安全連線 (Tailscale)
為了保護您的隱私，強烈建議不要在路由器對外開港。
1. 在 NAS 的 **套件中心** 安裝並登入 **Tailscale**。
2. 在您的手機與其他電腦上下載並登入**同一個** Tailscale 帳號。
3. 連線成功後，不論身在何處，皆可透過您的 NAS Tailscale IP 進行存取：
   👉 `http://<NAS_Tailscale_IP>:8085`
