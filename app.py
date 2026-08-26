import os
from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

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
        
    return gspread.authorize(creds)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            unique_code = request.form.get("unique_code", "").strip().upper()
            month = request.form.get("month")
            day = request.form.get("day")
            
            flavors_data = {
                "Mais Con Yelo": [
                    request.form.get("mcy_bbz", "0"), request.form.get("mcy_reg", "0"), request.form.get("mcy_grande", "0")
                ],
                "Creme Brulee": [
                    request.form.get("cb_bbz", "0"), request.form.get("cb_reg", "0"), request.form.get("cb_grande", "0")
                ],
                "Red_Velvent_Classic": [
                    request.form.get("rvc_bbz", "0"), request.form.get("rvc_reg", "0"), request.form.get("rvc_grande", "0")
                ],
                "Red_Velvent_Crunch": [
                    request.form.get("rvcr_bbz", "0"), request.form.get("rvcr_reg", "0"), request.form.get("rvcr_grande", "0")
                ],
                "Red_Velvent_Cheese_Cake": [
                    request.form.get("rvcc_bbz", "0"), request.form.get("rvcc_reg", "0"), request.form.get("rvcc_grande", "0")
                ]
            }
            
            client = get_client()
            spreadsheet = client.open("PROMO PRODUCT MONITORING")
            
            # Kunin ang details mula sa unang tab (Master list ng codes)
            base_sheet = spreadsheet.get_worksheet(0)
            base_records = base_sheet.get_all_records()
            
            bp_code = business_name = region = store_name = email = ""
            
            for row in base_records:
                # Sinusubukang hanapin ang unique code sa iba't ibang posibleng pangalan ng column
                code_val = str(
                    row.get("Please enter the UNIQUE CODE", 
                    row.get("Please enter the UNIQUE CODE * (Ex. ZAGU or ZAGU01)", 
                    row.get("Uniqe CODE", "")))
                ).strip().upper()
                
                if code_val == unique_code:
                    bp_code = row.get("BP CODE", "")
                    business_name = row.get("BUSINESS NAME", "")
                    region = row.get("REGION", "")
                    store_name = row.get("STORE NAME", "")
                    email = row.get("Email Address", "")
                    break
                    
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # I-save sa kani-kaniyang tabs
            for sheet_name, sizes in flavors_data.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    row_to_insert = [
                        timestamp, unique_code, bp_code, business_name, region, store_name,
                        sizes[0], sizes[1], sizes[2], month, day, email
                    ]
                    worksheet.append_row(row_to_insert)
                except Exception as ex:
                    print(f"Error sa tab na {sheet_name}: {ex}")
            
            return render_template("form.html", success=True)
            
        except Exception as e:
            print(f"General Error: {e}")
            return render_template("form.html", success=False)
            
    return render_template("form.html", success=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
