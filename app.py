import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="生產排程系統")
st.title("🏭 智能排產與週報表統整 (五天工作制)")

# --- 設定生產參數 ---
with st.sidebar:
    st.header("⚙️ 生產參數設定")
    uph = st.number_input("單線 UPH", value=30)
    lines = ["C1", "C2", "C3", "C4", "C5", "C6"]
    daily_hrs = 15  # 早晚班 8+7 小時
    daily_cap_per_line = uph * daily_hrs
    st.info(f"單線日產能: {daily_cap_per_line} | 全廠日產能: {daily_cap_per_line * len(lines)}")

# --- 上傳檔案 ---
uploaded_file = st.file_uploader("上傳原始工單 Excel", type=["xlsx"])

if uploaded_file:
    raw_df = pd.read_excel(uploaded_file)
    raw_df.columns = [c.strip() for c in raw_df.columns]
    
    # 建立副本以免更動原始數據
    pending_orders = raw_df.copy().to_dict('records')
    
    # 排產變數
    current_date = datetime(2026, 3, 30) # 從 3/30 週一開始
    daily_schedules = []
    
    # 核心演算：分配工單到每一天
    while any(o['QTY'] > 0 for o in pending_orders):
        # 💡 關鍵修正：跳過週六 (5) 與週日 (6)
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
            
        day_entry = {"日期": current_date.strftime("%m/%d (%a)")}
        # 取得該週週一作為統整基準
        monday_date = current_date - timedelta(days=current_date.weekday())
        day_entry["週次"] = monday_date.strftime("%Y-%m-%d")
        
        for line in lines:
            line_rem_cap = daily_cap_per_line
            line_tasks = []
            
            for order in pending_orders:
                if order['QTY'] <= 0: continue
                
                # 產線限制檢查
                if order['Production Line'] != 'All' and order['Production Line'] != line:
                    continue
                
                take = min(line_rem_cap, order['QTY'])
                if take > 0:
                    line_tasks.append(f"{order['Project']} WO{order['WO']} ({int(take)})")
                    order['QTY'] -= take
                    line_rem_cap -= take
                
                if line_rem_cap <= 0: break
            
            day_entry[line] = " + ".join(line_tasks) if line_tasks else "-"
        
        daily_schedules.append(day_entry)
        current_date += timedelta(days=1)

    # --- 顯示結果 1：日報表 ---
    st.subheader("📅 每日產線分配明細 (已跳過週末)")
    display_df = pd.DataFrame(daily_schedules)
    st.dataframe(display_df.drop(columns=["週次"]), use_container_width=True)

    # --- 顯示結果 2：週統整 Matrix ---
    st.divider()
    st.subheader("📊 每周 Project 出貨統整")
    
    matrix_data = []
    for day in daily_schedules:
        for line in lines:
            if day[line] != "-":
                tasks = day[line].split(" + ")
                for t in tasks:
                    if "(" in t:
                        try:
                            project = t.split(" ")[0]
                            qty = int(t.split("(")[1].replace(")", ""))
                            matrix_data.append({"Project": project, "週次": day["週次"], "Qty": qty})
                        except: continue
    
    if matrix_data:
        m_df = pd.DataFrame(matrix_data)
        pivot_df = m_df.pivot_table(index="Project", columns="週次", values="Qty", aggfunc="sum").fillna(0)
        st.table(pivot_df.astype(int))
