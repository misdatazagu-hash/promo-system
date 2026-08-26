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
            month = request.form.get("month", "")
            day = request.form.get("day", "")
            
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
            
            # --- PAGBASA SA Book2.xlsx (Kasama ang 'Uniqe' spelling) ---
            bp_code = business_name = region = store_name = email = ""
            try:
                df = pd.read_excel("Book2.xlsx", sheet_name=0)
                # I-normalize ang column names (alisin ang spaces at gawing uppercase)
                original_columns = df.columns
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                # Hanapin ang column na tumutugma sa code (uniq, code, etc.)
                code_col = None
                for col in df.columns:
                    if 'CODE' in col or 'UNIQ' in col:
                        code_col = col
                        break
                
                if code_col:
                    match = df[df[code_col].astype(str).str.strip().str.upper() == unique_code]
                    if not match.empty:
                        row_data = match.iloc[0]
                        
                        # Kunin ang mga detalye gamit ang orihinal o modified column names
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
            
            # I-save sa bawat tab at burahin ang lumang duplicate record kung meron man
            for sheet_name, sizes in flavors_data.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    all_records = worksheet.get_all_records()
                    row_to_delete = None
                    
                    for idx, record in enumerate(all_records):
                        existing_code = str(record.get("UNIQUE CODE", record.get("Unique Code", ""))).strip().upper()
                        if existing_code == unique_code:
                            row_to_delete = idx + 2
                            break
                    
                    if row_to_delete:
                        worksheet.delete_rows(row_to_delete)
                    
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
