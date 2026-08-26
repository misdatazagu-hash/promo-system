import os
from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Google Sheets Setup
def get_client():
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
    return client

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        unique_code = request.form.get("unique_code", "").strip().upper()
        month = request.form.get("month")
        day = request.form.get("day")
        
        # 5 Flavors values
        flavors_data = {
            "Mais Con Yelo": request.form.get("mais_con_yelo", "0"),
            "Creme Brulee": request.form.get("creme_brulee", "0"),
            "Red_Velvent_Classic": request.form.get("rv_classic", "0"),
            "Red_Velvent_Crunch": request.form.get("rv_crunch", "0"),
            "Red_Velvent_Cheese_Cake": request.form.get("rv_cheesecake", "0")
        }
        
        client = get_client()
        spreadsheet = client.open("PROMO PRODUCT MONITORING") # Siguraduhing tugma sa pangalan ng Google Sheet mo
        
        # Kunin ang reference details mula sa unang tab (o kung saan nakalista ang mga unique codes)
        base_sheet = spreadsheet.get_worksheet(0)
        base_records = base_sheet.get_all_records()
        
        bp_code = ""
        business_name = ""
        region = ""
        store_name = ""
        email = ""
        
        for row in base_records:
            if str(row.get("Please enter the UNIQUE CODE", "")).strip().upper() == unique_code:
                bp_code = row.get("BP CODE", "")
                business_name = row.get("BUSINESS NAME", "")
                region = row.get("REGION", "")
                store_name = row.get("STORE NAME", "")
                email = row.get("Email Address", "")
                break
                
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # I-loop at idagdag ang row sa kani-kaniyang tab ng bawat flavor
        for sheet_name, qty in flavors_data.items():
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                row_to_insert = [
                    timestamp,
                    unique_code,
                    bp_code,
                    business_name,
                    region,
                    store_name,
                    qty,
                    month,
                    day,
                    email
                ]
                worksheet.append_row(row_to_insert)
            except Exception as e:
                print(f"Error updating sheet {sheet_name}: {e}")
        
        return render_template("form.html", success=True)
        
    return render_template("form.html", success=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
