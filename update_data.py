# /// script
# dependencies = [
#   "google-api-python-client",
#   "google-auth-httplib2",
#   "google-auth-oauthlib",
#   "requests"
# ]
# ///

import os
import sys
import datetime
import json
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

sys.stdout.reconfigure(encoding='utf-8')

# Paths relative to the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, 'token.json')
CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, 'client_secret.json')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'dashboard', 'data.json')
ENV_FILE = os.path.join(SCRIPT_DIR, '.env')

# Default API keys from environment or fallback
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Try to load API keys from .env file if it exists
if os.path.exists(ENV_FILE):
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1)
                    k_str = k.strip()
                    v_str = v.strip().strip('"').strip("'")
                    if k_str == 'NOTION_API_KEY' and not NOTION_API_KEY:
                        NOTION_API_KEY = v_str
                    elif k_str == 'NOTION_PAGE_ID' and not NOTION_PAGE_ID:
                        NOTION_PAGE_ID = v_str
                    elif k_str == 'GEMINI_API_KEY' and not GEMINI_API_KEY:
                        GEMINI_API_KEY = v_str
    except Exception as e:
        print(f"Error reading .env file: {e}")

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
]

def get_google_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}")
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                creds = None
        else:
            creds = None
    return creds

def fetch_google_calendar(days=30):
    creds = get_google_credentials()
    if not creds:
        print("Warning: No valid Google Calendar credentials found.")
        return []

    try:
        service = build('calendar', 'v3', credentials=creds)
        start_time = (datetime.datetime.utcnow() - datetime.timedelta(days=int(days))).isoformat() + 'Z'
        end_time = (datetime.datetime.utcnow() + datetime.timedelta(days=int(days))).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    except HttpError as error:
        print(f"An API error occurred fetching Google Calendar: {error}")
        return []

def fetch_notion_notes():
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    url = f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children?page_size=100"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            print(f"Notion API error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception fetching Notion notes: {e}")
        return []

def categorize_title(title):
    title_lower = title.lower()
    work_keywords = ["評選", "會議", "監造", "預算書", "竣工", "保固", "驗收", "技服", "會勘", "德文教會", "公務", "留守", "發文", "簽核", "辦公室", "橋", "分署", "防護", "土方", "擋土"]
    family_keywords = ["ck", "學費", "學校", "期末考", "籃球", "移訓", "溫書假", "享時天堂", "饗食天堂", "石宸睿", "石成瑞", "楊準", "楊准", "小鳥", "洗澡"]
    health_keywords = ["藥", "診所", "醫院", "超音波", "抽血", "健檢", "骨科", "泌尿科", "胃腸", "鄭維鈞", "陳俊孚", "陳昱傑", "甲狀腺", "健康檢查", "張鳳林", "陳首彥"]
    admin_keywords = ["貸款", "扣款", "保費", "管理費", "定檢", "加機油", "充電線", "里健行", "天下雜誌", "利可帶", "水壺"]

    if any(k in title_lower for k in work_keywords):
        return "work"
    if any(k in title_lower for k in family_keywords):
        return "family"
    if any(k in title_lower for k in health_keywords):
        return "health"
    if any(k in title_lower for k in admin_keywords):
        return "admin"
    return "work"

def generate_ai_report(events, reminders):
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY is not set. Skipping AI report generation.")
        return "⚠️ 未偵測到 GEMINI_API_KEY 密鑰，已跳過 AI 智能分析。請在 `.env` 檔案中設定密鑰以啟用此功能！"

    print("Generating AI report using Gemini...")
    
    # Structure the prompt data cleanly
    events_summary = []
    for ev in events:
        events_summary.append(f"- [{ev['date']} {ev['time']}] ({ev['category']}) {ev['title']}")
        
    reminders_summary = []
    for rem in reminders:
        reminders_summary.append(f"- [備忘筆記] ({rem['category']}) {rem['content']}")

    prompt = f"""
你是一位極度聰明、富有戰略眼光、工程專案管理經驗與家庭生活智慧的「首席生活與工作參謀」。
請將以下輸入的使用者過去一個月至未來一個月的 Google 行事曆事件以及 Notion 中的生活/工作隨手雜記進行「深度融會貫通與前瞻性預測」。

你的目標是幫使用者建立一個最符合大腦高效記憶的**「過去回溯、當下聚焦、未來防禦」三維時間智庫**，層層打通隱形關係，並提供具體行動方針。

【輸入數據】
1. 行事曆事件（包含過去 30 天與未來 30 天）：
{chr(10).join(events_summary)}

2. Notion 隨手雜記：
{chr(10).join(reminders_summary)}

【大腦印記與前瞻預測撰寫指南】
請以有深度、有質感、像印入大腦般好讀的 Markdown 格式撰寫，必須包含以下三個層次的深度洞察：

### ⏪ 第一層：【過去一月脈絡銜接】（經驗與未完待續）
- 掃描過去 30 天的行程與筆記，找出哪些「已發生但尚未完結」的事務（例如：上月剛辦完的鑽心、竣工、檢驗，或某次看診、尚未領完的藥物、仍待處理的小雜記）。
- 建立與當下的連結，告訴大腦：*「因為過去發生了 A，所以這週我們需要做 B 作為銜接。」* 幫助大腦瞬間找回脈絡，消除遺漏的焦慮。

### 🔎 第二層：【當週/雙週焦點行動鏈】（高解析度執行）
- 將最近 1-2 週的行程與備忘雜記交織，重新以「場景化」、「因果化」進行重組。
- **主題標籤**：為這兩週起一個響亮的主題標籤（例如：【評選衝刺與週末移訓週】）。
- **關鍵記憶鏈**：將多個散落的任務打包成大腦一瞬間就能記住的「動作鏈條」（例如：「看診天＝領藥天，大門順手拿藥」、「週四評選會後若副座修改，週五早上發文記得順手抽換附件」）。
- **每日節奏與心智感受**：以第一人稱貼身參謀口吻，描述最關鍵幾天的忙碌點與身心能量的分配（例如：週四是高壓守備日，晚上應多休息；週五下午放空，晚上切換為家庭吃大餐模式）。

### ⏩ 第三層：【未來一月防禦性預警】（前瞻與風險防禦）
- 掃描 15-30 天後的遠期行程與重大死線（如一個月後的重大合約驗收、大健檢、搶門診掛號等）。
- **主動提案（防禦動作）**：告訴使用者這件事我會在當天提醒你，但**「今天/這週」你應該先做些什麼防禦性準備**，才不會到時候措手不及（例如：提前預約定檢、提前安排空腹健檢當天的輕度文書工作、針對即將到來的評選會先行交叉查核 Notion 雜記中的缺失廠商）。

請用第一人稱貼身首席參謀的口吻，語氣溫暖、專業且充滿前瞻智慧，排版使用極具質感的 Markdown 格式。
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    import time
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                res_data = response.json()
                text = res_data['candidates'][0]['content']['parts'][0]['text']
                return text
            elif response.status_code in [500, 503, 429]:
                print(f"Gemini API returned status {response.status_code}. Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return f"❌ 產生 AI 報告失敗：API 回傳代碼 {response.status_code}（服務暫時不可用，已重試 {max_retries} 次）。"
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return f"❌ 產生 AI 報告失敗：API 回傳代碼 {response.status_code}。"
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"Exception on attempt {attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                return f"❌ 產生 AI 報告時發生異常：{str(e)}。"
    
    return "❌ 產生 AI 報告失敗：API 多次重試均未回應。"

def main():
    print("Fetching calendar...")
    cal_items = fetch_google_calendar(30)
    print(f"Fetched {len(cal_items)} calendar items.")
    
    print("Fetching Notion notes...")
    notion_items = fetch_notion_notes()
    print(f"Fetched {len(notion_items)} Notion items.")
    
    events = []
    notion_reminders = []
    
    # 1. Parse Google Calendar events
    for item in cal_items:
        start = item['start'].get('dateTime', item['start'].get('date'))
        end = item['end'].get('dateTime', item['end'].get('date'))
        title = item.get('summary', '(No Title)')
        desc = item.get('description', '')
        
        date_str = start[:10]
        time_str = start[11:16] if len(start) > 10 else "00:00"
        
        events.append({
            "id": item['id'],
            "source": "calendar",
            "date": date_str,
            "time": time_str,
            "title": title,
            "description": desc,
            "category": categorize_title(title),
            "dependencies": []
        })
        
    # 2. Parse Notion items
    for b in notion_items:
        btype = b.get('type')
        created_time = b.get('created_time', '')[:10]
        
        content = ""
        if btype in b:
            type_data = b[btype]
            if isinstance(type_data, dict) and 'rich_text' in type_data:
                content = ''.join([t.get('plain_text', '') for t in type_data['rich_text']])
        
        if not content.strip():
            continue
            
        parsed_date = None
        for word in content.split():
            if "2026-" in word:
                parts = word.split('-')
                if len(parts) >= 3:
                    parsed_date = word[:10]
                    break
        
        category = categorize_title(content)
        
        if parsed_date:
            events.append({
                "id": b['id'],
                "source": "notion",
                "date": parsed_date,
                "time": "00:00",
                "title": content,
                "description": f"Notion Note created at {created_time}",
                "category": category,
                "dependencies": []
            })
        else:
            notion_reminders.append({
                "id": b['id'],
                "content": content,
                "created_time": created_time,
                "category": category
            })
            
    events.sort(key=lambda x: (x['date'], x['time']))
    
    # 3. Apply logical threads & dependencies
    for ev in events:
        title = ev['title']
        date = ev['date']
        
        if "溫泉橋" in title:
            shuting_reminder = next((r for r in notion_reminders if "舒婷" in r['content']), None)
            if shuting_reminder:
                ev['dependencies'].append({
                    "target_id": shuting_reminder['id'],
                    "text": "溫泉橋回覆意見前需「問舒婷」釐清報署確認程序",
                    "target_title": shuting_reminder['content']
                })
                
        if "斗豐橋" in title:
            settlement_reminder = next((r for r in notion_reminders if "斗豐橋簽竣工" in r['content']), None)
            if settlement_reminder:
                ev['dependencies'].append({
                    "target_id": settlement_reminder['id'],
                    "text": "查驗完成後，需一併跑竣工結算簽辦流程",
                    "target_title": settlement_reminder['content']
                })
                
        if "超音波" in title and date == "2026-06-16":
            medicine_event = next((e for e in events if "甲狀腺領藥" in e['title']), None)
            if medicine_event:
                ev['dependencies'].append({
                    "target_id": medicine_event['id'],
                    "text": "看診檢查當天，可順便在大廳「領取甲狀腺藥物」，省去重複往返",
                    "target_title": medicine_event['title']
                })
                
        if "鄭維鈞" in title and date == "2026-06-25":
            family_med = next((e for e in events if "張鳳林拿藥" in e['title']), None)
            if family_med:
                ev['dependencies'].append({
                    "target_id": family_med['id'],
                    "text": "本日看診排隊時，可順便「幫張鳳林拿藥」",
                    "target_title": family_med['title']
                })
                
        if "高雄市" in title and date == "2026-06-04":
            swap_reminder = next((r for r in notion_reminders if "附件" in r['content'] and "抽換" in r['content']), None)
            if swap_reminder:
                ev['dependencies'].append({
                    "target_id": swap_reminder['id'],
                    "text": "6/4 評選會後若副座修改內容，務必前往秘書室「抽換附件」",
                    "target_title": swap_reminder['content']
                })

    # 4. Generate AI report
    ai_report = generate_ai_report(events, notion_reminders)

    output_data = {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": events,
        "reminders": notion_reminders,
        "ai_report": ai_report
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Data successfully generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
