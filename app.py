import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime  # <--- 이 줄이 꼭 필요합니다!

load_dotenv()

app = Flask(__name__)

# 모든 도메인에서 오는 요청을 허용합니다.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Google Sheets 설정
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gspread_client():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS env var is not set")
    
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

@app.route('/api/submit', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        client = get_gspread_client()
        sheet_id = os.getenv("SPREADSHEET_ID")
        sheet = client.open_by_key(sheet_id).sheet1
        
        session_id = data.get('session_id')
        score = data.get('score')
        
        # 1. 시트에서 같은 세션 ID가 있는지 찾기
        cell = None
        try:
            # session_id가 있을 때만 검색
            if session_id:
                cell = sheet.find(str(session_id))
        except:
            cell = None

        if cell:
            # 2. 이미 있다면 (리뷰 모드 기록 업데이트)
            # E열(5)에 리뷰 점수, F열(6)에 리뷰 오답수
            sheet.update_cell(cell.row, 5, score)
            sheet.update_cell(cell.row, 6, data.get('incorrect_count'))
            return jsonify({"status": "updated"}), 200
        else:
            # 3. 처음이라면 (새로운 행 추가)
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # A: 일시
                str(session_id),                             # B: 세션 ID
                score,                                       # C: 첫 점수
                data.get('incorrect_count'),                # D: 첫 오답수
                "",                                          # E: 리뷰 점수 (비워둠)
                ""                                           # F: 리뷰 오답수 (비워둠)
            ]
            sheet.append_row(row)
            return jsonify({"status": "created"}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500 # 에러 내용을 확인하기 위해 수정

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
