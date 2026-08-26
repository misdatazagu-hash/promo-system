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
            
            # Basahin ang Book2.xlsx para makuha ang tamang details gamit ang Unique Code
            bp_code = business_name = region = store_name = email = ""
            try:
                df = pd.read_excel("Book2.xlsx", sheet_name=0)
                match = df[df['Uniqe CODE'].astype(str).str.strip().str.upper() == unique_code]
                if not match.empty:
                    row_data = match.iloc[0]
                    bp_code = str(row_data.get("BP CODE", ""))
                    business_name = str(row_data.get("BUSINESS NAME", ""))
                    region = str(row_data.get("REGION", ""))
                    store_name = str(row_data.get("STORE NAME", ""))
            except Exception as ex:
                print(f"Error sa pagbasa ng Book2.xlsx: {ex}")
            
            client = get_client()
            spreadsheet = client.open("PROMO PRODUCT MONITORING")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # I-save sa bawat tab at tanggalin ang lumang entry kung may kaparehong Unique Code
            for sheet_name, sizes in flavors_data.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    
                    # Kunin lahat ng records para hanapin kung umiiral na ang Unique Code
                    all_records = worksheet.get_all_records()
                    row_to_delete = None
                    
                    # Mag-loop mula sa huli pabalik o una para hanapin ang duplicate
                    for idx, record in enumerate(all_records):
                        # Siguraduhing tumutugma ang column header name (hal. 'UNIQUE CODE')
                        existing_code = str(record.get("UNIQUE CODE", "")).strip().upper()
                        if existing_code == unique_code:
                            # Ang index ng gspread get_all_records ay nagsisimula sa 0, 
                            # pero ang row sa sheet ay header pa (row 1), kaya index + 2
                            row_to_delete = idx + 2
                            break
                    
                    # Kung nahanap ang lumang record, burahin muna bago i-append ang bago
                    if row_to_delete:
                        worksheet.delete_rows(row_to_delete)
                    
                    # I-append ang bagong updated data
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
