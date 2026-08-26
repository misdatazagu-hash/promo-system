import os
from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

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
    success = False
    if request.method == "POST":
        try:
            unique_code = request.form.get("unique_code", "").strip().upper()
            month = request.form.get("month", "").strip()
            day = request.form.get("day", "").strip()
            
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
            
            # --- PAGBASA SA Book2.xlsx (Auto-fill ng Details) ---
            bp_code = business_name = region = store_name = email = ""
            try:
                df = pd.read_excel("Book2.xlsx", sheet_name=0)
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                code_col = None
                for col in df.columns:
                    if 'CODE' in col or 'UNIQ' in col:
                        code_col = col
                        break
                
                if code_col:
                    match = df[df[code_col].astype(str).str.strip().str.upper() == unique_code]
                    if not match.empty:
                        row_data = match.iloc[0]
                        for col in df.columns:
                            val = str(row_data.get(col, ""))
                            if val == "nan":
                                val = ""
                                
                            if 'BP' in col:
                                bp_code = val
                            elif 'BUSINESS' in col:
                                business_name = val
                            elif 'REGION' in col:
                                region = val
                            elif 'STORE' in col:
                                store_name = val
            except Exception as ex:
                print(f"Excel Error: {ex}")
            
            client = get_client()
            spreadsheet = client.open("PROMO PRODUCT MONITORING")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Para sa bawat flavor tab, i-check kung meron nang parehong Unique Code + Month + Day
            for sheet_name, sizes in flavors_data.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    all_records = worksheet.get_all_values()
                    
                    # Hanapin kung may existing row na kapareho ang Unique Code (Col B), Month (Col J), Day (Col K)
                    row_to_delete = None
                    if len(all_records) > 1:
                        for idx, row in enumerate(all_records[1:], start=2):
                            # row[1] = Unique Code, row[9] = Month, row[10] = Day
                            if len(row) > 10:
                                existing_code = str(row[1]).strip().upper()
                                existing_month = str(row[9]).strip()
                                existing_day = str(row[10]).strip()
                                
                                if existing_code == unique_code and existing_month == month and existing_day == day:
                                    row_to_delete = idx
                                    break
                    
                    # Kung nakita ang luma para sa parehong araw at store, burahin muna bago ilagay ang bago
                    if row_to_delete:
                        worksheet.delete_rows(row_to_delete)
                    
                    # Idagdag ang bagong row
                    row_to_insert = [
                        timestamp, unique_code, bp_code, business_name, region, store_name,
                        sizes[0], sizes[1], sizes[2], month, day, email
                    ]
                    worksheet.append_row(row_to_insert)
                    
                except Exception as ex:
                    print(f"Sheet Error sa {sheet_name}: {ex}")
            
            success = True
            
        except Exception as e:
            print(f"General Error: {e}")
            success = False
            
    return render_template("form.html", success=success)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
