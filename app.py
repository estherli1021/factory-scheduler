import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="五天兩班制排產系統")
st.title("🏭 智能排產系統 v3.0 (優先級與雙班制)")

# --- 生產參數 ---
uph = 30
lines = ["C1", "C2", "C3", "C4", "C5", "C6"]
shift1_hrs, shift2_hrs = 8, 7  # 1st: 8h, 2nd: 7h
s1_cap = uph * shift1_hrs
s2_cap = uph * shift2_hrs

# --- 上傳檔案 ---
uploaded_file = st.file_uploader("上傳原始工單 (請包含 Priority 欄位: H/L)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    # 💡 邏輯 1: 加上優先級排序 (H 在前, L 在後)
    # 假設 Excel 有一個 'Priority' 欄位
    if 'Priority' not in df.columns:
        st.warning("Excel 中未偵測到 'Priority' 欄位，將預設為相同優先級。")
        df['Priority'] = 'L'
    
    # 將 H 排在 L 前面
    df['priority_val'] = df['Priority'].map({'H': 0, 'L': 1})
    df = df.sort_values(by='priority_val').drop(columns=['priority_val'])
    pending_orders = df.to_dict('records')
    
    current_date = datetime(2026, 3, 30)
    all_days_data = []

    # 核心演算
    while any(o['QTY'] > 0 for o in pending_orders):
        # 跳過週六週日
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
            
        day_str = current_date.strftime("%m/%d (%a)")
        day_tasks = {"Production Line": lines}
        
        for shift_name, shift_cap in [("First shift", s1_cap), ("Second shift", s2_cap)]:
            shift_col_name = f"{day_str} | {shift_name}"
            line_results = []
            
            for line in lines:
                rem_cap = shift_cap
                content = []
