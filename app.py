import os
import json
from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

app = Flask(__name__)


# ============================================================
# GOOGLE SHEETS CONNECTION
# ============================================================
def get_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_json = os.environ.get("GOOGLE_CREDENTIALS")

    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict, scope
        )
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )

    return gspread.authorize(creds)


# ============================================================
# MASTER STORE LOOKUP
# UNIQUE CODE -> BP CODE / BUSINESS NAME / REGION / STORE NAME
# ============================================================
def get_store_details(unique_code):
    """
    Reads Book2.xlsx and finds the exact Unique Code.

    Expected columns in Book2.xlsx:
        BP CODE
        BUSINESS NAME
        REGION
        STORE NAME
        Uniqe CODE

    Returns:
        dict with BP Code, Business Name, Region and Store Name
        or None if the Unique Code does not exist.
    """

    unique_code = str(unique_code).strip().upper()

    if not unique_code:
        return None

    try:
        df = pd.read_excel("Book2.xlsx", sheet_name=0)

        # Normalize headers:
        # "Uniqe CODE" -> "UNIQE CODE"
        df.columns = [
            str(col).strip().upper().replace("_", " ")
            for col in df.columns
        ]

        # The uploaded master file uses "Uniqe CODE".
        # We explicitly support both the existing spelling and the
        # correct spelling "UNIQUE CODE".
        code_candidates = [
            "UNIQUE CODE",
            "UNIQE CODE"
        ]

        code_col = next(
            (col for col in code_candidates if col in df.columns),
            None
        )

        if not code_col:
            raise ValueError(
                "Hindi makita ang Unique Code column sa Book2.xlsx. "
                "Expected: 'Uniqe CODE' or 'UNIQUE CODE'."
            )

        required_columns = [
            "BP CODE",
            "BUSINESS NAME",
            "REGION",
            "STORE NAME"
        ]

        missing = [col for col in required_columns if col not in df.columns]

        if missing:
            raise ValueError(
                "Missing columns sa Book2.xlsx: " + ", ".join(missing)
            )

        # Normalize the values in the Unique Code column.
        code_values = (
            df[code_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        match = df[code_values == unique_code]

        if match.empty:
            return None

        # Use the first exact match.
        row = match.iloc[0]

        def clean_value(value):
            if pd.isna(value):
                return ""
            return str(value).strip()

        return {
            "bp_code": clean_value(row["BP CODE"]),
            "business_name": clean_value(row["BUSINESS NAME"]),
            "region": clean_value(row["REGION"]),
            "store_name": clean_value(row["STORE NAME"])
        }

    except Exception as ex:
        print(f"Master Store Lookup Error: {ex}")
        raise


# ============================================================
# FORM
# ============================================================
@app.route("/", methods=["GET", "POST"])
def index():
    success = False
    error = ""

    if request.method == "POST":
        try:
            # ------------------------------------------------
            # FORM INPUTS
            # ------------------------------------------------
            unique_code = request.form.get(
                "unique_code", ""
            ).strip().upper()

            month = request.form.get("month", "").strip()
            day = request.form.get("day", "").strip()

            # ------------------------------------------------
            # VALIDATE BASIC INPUTS
            # ------------------------------------------------
            if not unique_code:
                error = "Please enter the UNIQUE CODE."
                return render_template(
                    "form.html",
                    success=False,
                    error=error
                )

            if not month:
                error = "Please select the MONTH."
                return render_template(
                    "form.html",
                    success=False,
                    error=error
                )

            if not day:
                error = "Please select the DAY."
                return render_template(
                    "form.html",
                    success=False,
                    error=error
                )

            # ------------------------------------------------
            # AUTOMATIC STORE LOOKUP
            # ------------------------------------------------
            store = get_store_details(unique_code)

            if not store:
                error = (
                    f"Unique Code '{unique_code}' was not found "
                    "in Book2.xlsx. Please check the code."
                )

                return render_template(
                    "form.html",
                    success=False,
                    error=error
                )

            bp_code = store["bp_code"]
            business_name = store["business_name"]
            region = store["region"]
            store_name = store["store_name"]

            # Prevent saving an incomplete master record.
            missing_details = []

            if not bp_code:
                missing_details.append("BP CODE")
            if not business_name:
                missing_details.append("BUSINESS NAME")
            if not region:
                missing_details.append("REGION")
            if not store_name:
                missing_details.append("STORE NAME")

            if missing_details:
                error = (
                    f"Unique Code '{unique_code}' was found, "
                    f"but the master record is missing: "
                    f"{', '.join(missing_details)}."
                )

                return render_template(
                    "form.html",
                    success=False,
                    error=error
                )

            # ------------------------------------------------
            # FLAVOR DATA
            # ------------------------------------------------
            flavors_data = {
                "Mais Con Yelo": [
                    int(request.form.get("mcy_bbz") or 0),
                    int(request.form.get("mcy_reg") or 0),
                    int(request.form.get("mcy_grande") or 0)
                ],

                "Creme Brulee": [
                    int(request.form.get("cb_bbz") or 0),
                    int(request.form.get("cb_reg") or 0),
                    int(request.form.get("cb_grande") or 0)
                ],

                "Red_Velvent_Classic": [
                    int(request.form.get("rvc_bbz") or 0),
                    int(request.form.get("rvc_reg") or 0),
                    int(request.form.get("rvc_grande") or 0)
                ],

                "Red_Velvent_Crunch": [
                    int(request.form.get("rvcr_bbz") or 0),
                    int(request.form.get("rvcr_reg") or 0),
                    int(request.form.get("rvcr_grande") or 0)
                ],

                "Red_Velvent_Cheese_Cake": [
                    int(request.form.get("rvcc_bbz") or 0),
                    int(request.form.get("rvcc_reg") or 0),
                    int(request.form.get("rvcc_grande") or 0)
                ]
            }

            # ------------------------------------------------
            # GOOGLE SHEETS
            # ------------------------------------------------
            client = get_client()
            spreadsheet = client.open("PROMO PRODUCT MONITORING")

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ------------------------------------------------
            # SAVE EACH FLAVOR
            # ------------------------------------------------
            for sheet_name, sizes in flavors_data.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    all_records = worksheet.get_all_values()

                    # ------------------------------------------------
                    # SMART REPLACEMENT (DELETE OLD RECORD IF EXISTS)
                    # ------------------------------------------------
                    rows_to_delete = []

                    if len(all_records) > 1:
                        for idx, row in enumerate(
                            all_records[1:], start=2
                        ):
                            if len(row) > 1:
                                existing_code = (
                                    str(row[1]).strip().upper()
                                )

                                if existing_code == unique_code:
                                    rows_to_delete.append(idx)

                    for r_idx in sorted(
                        rows_to_delete, reverse=True
                    ):
                        worksheet.delete_rows(r_idx)

                    email = request.form.get(
                        "email", ""
                    ).strip()

                    row_to_insert = [
                        timestamp,
                        unique_code,
                        bp_code,
                        business_name,
                        region,
                        store_name,
                        sizes[0],
                        sizes[1],
                        sizes[2],
                        month,
                        int(day) if day else 0,
                        email
                    ]

                    # ------------------------------------------------
                    # EXACT ROW INSERTION (A TO L COLUMNS)
                    # ------------------------------------------------
                    col_a_values = worksheet.col_values(1)
                    next_row = len(col_a_values) + 1
                    if next_row < 4:
                        next_row = 4

                    range_to_update = f"A{next_row}:L{next_row}"
                    worksheet.update(range_to_update, [row_to_insert])

                except Exception as ex:
                    print(
                        f"Sheet Error sa {sheet_name}: {ex}"
                    )

            success = True

        except Exception as ex:
            print(f"General Error: {ex}")
            error = (
                "May error sa pag-submit. "
                "Please check the server console."
            )
            success = False

    return render_template(
        "form.html",
        success=success,
        error=error
    )


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
