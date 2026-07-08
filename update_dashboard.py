import os
import json
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT_ID = "84191474"
PARTICIPANTS_URL = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/repository/files/participants.csv/raw?ref=main"
SAMPLES_URL = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/repository/files/samples.csv/raw?ref=main"
STATS_FILE = "pipeline_stats.json"

def calculate_percentage(current, previous):
    try:
        curr = float(current)
        prev = float(previous)
        if prev == 0:
            return 0
        return round((curr / prev) * 100, 1)
    except:
        return 0

try:
    # א. משיכת נתונים עדכניים מ-GitLab (רץ תמיד כדי לשמור על סנכרון גיוס)
    print("Fetching recruitment data from GitLab...")
    participants_df = pd.read_csv(PARTICIPANTS_URL)
    samples_df = pd.read_csv(SAMPLES_URL)

    # תיקון וחישוב המטריקות בהתאם לשם העמודה הנכון (SampleID)
    total_participants = participants_df['ParticipantID'].dropna().nunique()
    unique_sample_donors = samples_df['SampleID'].dropna().nunique()
    total_samples = samples_df['SampleID'].dropna().count()
    
    # ב. ניהול הזיכרון של נתוני ה-MegaMap מהריפו הפרטי
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            saved_stats = json.load(f)
    else:
        saved_stats = {"total": "0", "success": "0", "failed": "0"}

    # קריאת משתני הסביבה (יהיו מלאים רק אם הריפו הפרטי ביצע Trigger)
    megamap_total = os.getenv('MEGAMAP_TOTAL')
    megamap_success = os.getenv('MEGAMAP_SUCCESS')
    megamap_failed = os.getenv('MEGAMAP_FAILED')

    # עדכון קובץ ה-JSON רק אם קיבלנו מידע חדש ואמיתי מהריפו הפרטי
    if megamap_total and megamap_total.strip() != "":
        print(f"New MegaMap telemetry received: Total={megamap_total}")
        saved_stats["total"] = megamap_total
        saved_stats["success"] = megamap_success
        saved_stats["failed"] = megamap_failed
        
        with open(STATS_FILE, "w") as f:
            json.dump(saved_stats, f)
    else:
        print("No new MegaMap telemetry in this run. Using cached statistics.")

    # חישוב אחוזים למשפך
    pct_donors = calculate_percentage(unique_sample_donors, total_participants)
    pct_pipeline = calculate_percentage(saved_stats["total"], unique_sample_donors)
    pct_success = calculate_percentage(saved_stats["success"], saved_stats["total"])

    # ג. הפקת ה-HTML העדכני (שעון ישראל)
    current_time = datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%d/%m/%Y %H:%M:%S")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>דשבורד מחקר סקר</title>
        <style>
            :root {{
                --primary-color: #3498db;
                --bg-color: #f4f7f9;
                --card-bg: #ffffff;
                --text-main: #2c3e50;
                --text-muted: #7f8c8d;
                --funnel-color: #3498db;
            }}
            body {{
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                background-color: var(--bg-color);
                margin: 0;
                padding: 20px;
                text-align: center;
                color: var(--text-main);
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: var(--card-bg);
                padding: 40px 20px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            }}
            h1 {{ font-size: 2rem; margin-bottom: 5px; }}
            h2 {{ font-size: 1.1rem; color: var(--text-muted); margin-bottom: 40px; font-weight: 400; }}

            /* Funnel Styles */
            .funnel-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 10px;
                margin: 40px 0;
            }}
            .funnel-stage {{
                position: relative;
                width: 100%;
                background-color: var(--funnel-color);
                color: white;
                padding: 20px;
                border-radius: 8px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            }}
            .funnel-stage:nth-child(1) {{ width: 100%; opacity: 1.0; }}
            .funnel-stage:nth-child(2) {{ width: 85%; opacity: 0.9; }}
            .funnel-stage:nth-child(3) {{ width: 70%; opacity: 0.8; }}
            .funnel-stage:nth-child(4) {{ width: 55%; opacity: 0.7; }}

            .stage-label {{ font-size: 1rem; font-weight: 500; margin-bottom: 5px; }}
            .stage-value {{ font-size: 1.8rem; font-weight: bold; }}

            .percentage-tag {{
                position: absolute;
                bottom: -15px;
                background: #2c3e50;
                color: white;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 0.8rem;
                z-index: 10;
                border: 2px solid white;
            }}

            /* Supplementary Stats */
            .supplementary-section {{
                margin-top: 50px;
                padding-top: 30px;
                border-top: 1px solid #eee;
            }}
            .sup-title {{
                text-align: right;
                font-size: 1.1rem;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            .grid {{
                display: flex;
                justify-content: center;
                gap: 20px;
            }}
            .card {{
                flex: 1;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 12px;
                border-bottom: 4px solid #bdc3c7;
            }}
            .card .number {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }}
            .card .label {{ font-size: 0.9rem; color: var(--text-muted); }}

            .footer {{ color: #bdc3c7; font-size: 0.85rem; margin-top: 50px; }}

            /* Mobile adjustments */
            @media (max-width: 600px) {{
                .funnel-stage {{ width: 95% !important; padding: 15px; }}
                .stage-value {{ font-size: 1.5rem; }}
                .grid {{ flex-direction: column; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>מרכז בקרה - מחקר סקר</h1>
            <h2>Sheba Microbiome Center</h2>
            
            <div class="funnel-container">
                <div class="funnel-stage">
                    <div class="stage-label">משתתפים רשומים בסקר</div>
                    <div class="stage-value">{total_participants}</div>
                    <div class="percentage-tag">100%</div>
                </div>

                <div class="funnel-stage">
                    <div class="stage-label">משתתפים שתרמו דגימה</div>
                    <div class="stage-value">{unique_sample_donors}</div>
                    <div class="percentage-tag">{pct_donors}% משלב קודם</div>
                </div>

                <div class="funnel-stage">
                    <div class="stage-label">דגימות שזרמו ל-Pipeline</div>
                    <div class="stage-value">{saved_stats["total"]}</div>
                    <div class="percentage-tag">{pct_pipeline}% משלב קודם</div>
                </div>

                <div class="funnel-stage">
                    <div class="stage-label">הסתיימו בהצלחה (>4K reads)</div>
                    <div class="stage-value">{saved_stats["success"]}</div>
                    <div class="percentage-tag">{pct_success}% משלב קודם</div>
                </div>
            </div>

            <div class="supplementary-section">
                <div class="sup-title">נתונים משלימים</div>
                <div class="grid">
                    <div class="card">
                        <div class="number">{total_samples}</div>
                        <div class="label">סך כל הדגימות במקפיא</div>
                    </div>
                    <div class="card">
                        <div class="number">{saved_stats["failed"]}</div>
                        <div class="label">נכשלו / לא עברו סף</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">עודכן לאחרונה באופן אוטומטי ב- {current_time} (שעון ישראל)</div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("Dashboard HTML updated successfully with funnel design!")

except Exception as e:
    print(f"Error generating dashboard: {e}")
    exit(1)
