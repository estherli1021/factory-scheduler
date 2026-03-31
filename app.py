import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🏭 6-Line 智能排產模擬器")

# --- 參數設定 ---
st.sidebar.header("生產參數調整")
uph = st.sidebar.number_input("單線 UPH", value=30)
lines_count = st.sidebar.slider("可用產線數量", 1, 6, 6)
shift1_hrs = 8  # 07:30 - 15:30
shift2_hrs = 7  # 16:00 - 23:00
daily_hrs_per_line = shift1_hrs + shift2_hrs
total_hourly_capacity = uph * lines_count

# --- 上傳檔案 ---
uploaded_file = st.file_uploader("請上傳工單 Excel (包含 WO, QTY, Production Line)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    total_qty = df['QTY'].sum()
    
    st.subheader("📊 生產概況分析")
    col1, col2, col3 = st.columns(3)
    col1.metric("總待產數量", f"{total_qty} units")
    col2.metric("全廠每小時產能", f"{total_hourly_capacity} units/hr")
    
    # 計算理論完工天數
    total_days = math.ceil(total_qty / (total_hourly_capacity * daily_hrs_per_line))
    col3.metric("預計所需工期", f"{total_days} 天")

    # --- 排產核心演算法 (簡化版) ---
    start_date = datetime(2026, 3, 30)
    current_qty = total_qty
    schedule_data = []
    
    temp_date = start_date
    while current_qty > 0:
        daily_output = min(current_qty, total_hourly_capacity * daily_hrs_per_line)
        # 找出該日期屬於哪一週的週一
        monday_of_week = temp_date - timedelta(days=temp_date.weekday())
        
        schedule_data.append({
            "生產日期": temp_date.strftime('%Y-%m-%d'),
            "週次起始": monday_of_week.strftime('%Y-%m-%d'),
            "當日產出": daily_output,
            "剩餘數量": current_qty - daily_output
        })
        current_qty -= daily_output
        temp_date += timedelta(days=1)
        if temp_date.weekday() == 6: # 假設週日不開工
            temp_date += timedelta(days=1)

    # --- 輸出結果 ---
    res_df = pd.DataFrame(schedule_data)
    st.write("### 📅 每日排程計畫預覽")
    st.dataframe(res_df, use_container_width=True)

    # 匯出您要的週報表格式
    st.write("### 📈 每周生產統整 (Matrix View)")
    weekly_summary = res_df.groupby("週次起始")["當日產出"].sum().reset_index()
    st.table(weekly_summary)