import os
from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Google Sheets Setup
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    
    # Kukunin ang credentials mula sa Render Environment Variables o local file
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        import json
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    client = gspread.authorize(creds)
    # Pangalan ng iyong Google Sheet
    sheet = client.open("Mais Con Yelo Pearl Shake").sheet1
    return sheet

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        unique_code = request.form.get("unique_code", "").strip().upper()
        month = request.form.get("month")
        day = request.form.get("day")
        bbz = request.form.get("bbz", "0")
        regular = request.form.get("regular", "0")
        grande = request.form.get("grande", "0")
        
        sheet = get_sheet()
        data = sheet.get_all_records()
        
        # Hahanapin sa Google Sheet kung saan tugma ang UNIQUE CODE para makuha ang detalye
        bp_code = ""
        business_name = ""
        region = ""
        store_name = ""
        email = ""
        
        for row in data:
            # I-check ang column kung saan nakalagay ang Unique Code (batay sa screenshot mo, ito ay Column B)
            if str(row.get("Please enter the UNIQUE CODE", "")).strip().upper() == unique_code:
                bp_code = row.get("BP CODE", "")
                business_name = row.get("BUSINESS NAME", "")
                region = row.get("REGION", "")
                store_name = row.get("STORE NAME", "")
                email = row.get("Email Address", "")
                break
                
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        
        # Pagkakasunod-sunod ng columns sa iyong Google Sheet:
        # [Timestamp, UNIQUE CODE, BP CODE, BUSINESS NAME, REGION, STORE NAME, BBZ, REGULAR, GRANDE, MONTH, DAY, Email Address]
        row_to_insert = [
            timestamp,
            unique_code,
            bp_code,
            business_name,
            region,
            store_name,
            bbz,
            regular,
            grande,
            month,
            day,
            email
        ]
        
        sheet.append_row(row_to_insert)
        return render_template("form.html", success=True)
        
    return render_template("form.html", success=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
