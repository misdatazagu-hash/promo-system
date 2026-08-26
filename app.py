import os
from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        import json
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    client = gspread.authorize(creds)
    # Siguraduhing tugma sa pangalan ng tab o spreadsheet mo (hal. Form_Responses)
    sheet = client.open("PROMO PRODUCT MONITORING").worksheet("Form_Responses")
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
        
        bp_code = ""
        business_name = ""
        region = ""
        store_name = ""
        email = ""
        
        # Paghanap ng store details base sa Unique Code mula sa parehong sheet o database
        for row in data:
            # Sinisigurado nating match ang unique code column
            code_val = str(row.get("Please enter the UNIQUE CODE", row.get("Please enter the UNIQUE CODE * (Ex. ZAGU or ZAGU01)", ""))).strip().upper()
            if code_val == unique_code:
                bp_code = row.get("BP CODE", "")
                business_name = row.get("BUSINESS NAME", "")
                region = row.get("REGION", "")
                store_name = row.get("STORE NAME", "")
                email = row.get("Email Address", "")
                break
                
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        
        # Eksaktong pagkakasunod-sunod batay sa iyong Google Sheet columns:
        # [Timestamp, Unique Code, BP Code, Business Name, Region, Store Name, BBZ, Regular, Grande, Month, Day, Email Address]
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
