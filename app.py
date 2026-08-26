from datetime import datetime
import json
import os
from flask import Flask, render_template, request
import gspread

app = Flask(__name__)

# Suriin kung nasa Render (cloud) o lokal na computer
if "GOOGLE_CREDENTIALS" in os.environ:
  # Kung nasa Render, kukunin ang credentials mula sa Environment Variable
  creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
  gc = gspread.service_account_from_dict(creds_dict)
else:
  # Kung nasa lokal na computer mo pa rin, gagamitin ang credentials.json file
  gc = gspread.service_account(filename="credentials.json")

sh = gc.open("PROMO PRODUCT MONITORING")


@app.route("/")
def index():
  return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
  # Kunin ang impormasyon galing sa form
  report_date_str = request.form.get("report_date")  # Format: YYYY-MM-DD
  bp_code = request.form.get("bp_code")
  business_name = request.form.get("business_name")
  region = request.form.get("region")
  store_name = request.form.get("store_name")
  email = request.form.get("email")

  # I-convert ang date para makuha ang Month at Day (naayos na ang format)
  selected_date = datetime.strptime(report_date_str, "%Y-%m-%d")
  timestamp = f"{report_date_str} 00:00:00"
  month_name = selected_date.strftime("%B")
  day_num = selected_date.strftime("%d").lstrip("0")

  # Mga produkto at ang eksaktong pangalan ng kanilang Tabs/Worksheets sa Google Sheets
  products = {
      "Mais Con Yelo": {
          "BBZ": request.form.get("mais_bbz"),
          "Regular": request.form.get("mais_reg"),
          "Grande": request.form.get("mais_grd"),
      },
      "Creme Brulee": {
          "BBZ": request.form.get("creme_bbz"),
          "Regular": request.form.get("creme_reg"),
          "Grande": request.form.get("creme_grd"),
      },
      "Red_Velvent_Classic": {
          "BBZ": request.form.get("rvcl_bbz"),
          "Regular": request.form.get("rvcl_reg"),
          "Grande": request.form.get("rvcl_grd"),
      },
      "Red_Velvent_Crunch": {
          "BBZ": request.form.get("rvc_bbz"),
          "Regular": request.form.get("rvc_reg"),
          "Grande": request.form.get("rvc_grd"),
      },
      "Red_Velvent_Cheese_Cake": {
          "BBZ": request.form.get("rvch_bbz"),
          "Regular": request.form.get("rvch_reg"),
          "Grande": request.form.get("rvch_grd"),
      },
  }

  # Isa-isang isave ang bawat produkto sa kani-kanilang tab sa Google Sheet
  for sheet_name, sizes in products.items():
    worksheet = sh.worksheet(sheet_name)

    row_data = [
        timestamp,
        bp_code,
        bp_code,
        business_name,
        region,
        store_name,
        sizes["BBZ"],
        sizes["Regular"],
        sizes["Grande"],
        month_name,
        day_num,
        email,
    ]

    # Idagdag ang row nang diretso sa online Google Sheet tab
    worksheet.append_row(row_data)

  return (
      "<h3>Report Submitted & Saved Successfully to Google Sheets! <a"
      " href='/'>Submit Another</a></h3>"
  )


if __name__ == "__main__":
  app.run(debug=True, port=5000)