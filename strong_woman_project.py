import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ページ設定
st.set_page_config(
    page_title="GROW+",
    page_icon="🌱",
    layout="wide"
)

# データファイルのパス
DATA_FILE = "strong_woman_data.json"

def load_data():
    """データを読み込む"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"records": []}

def save_data(data):
    """データを保存する"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    st.title("🌱 GROW+")
    st.markdown("---")
    
    # サイドバーでページ選択
    page = st.sidebar.selectbox(
        "ページを選択",
        ["📝 データ入力", "📊 週次レポート", "💡 アドバイス"]
    )
    
    if page == "📝 データ入力":
        data_input_page()
    elif page == "📊 週次レポート":
        weekly_report_page()
    elif page == "💡 アドバイス":
        advice_page()

def data_input_page():
    """データ入力ページ"""
    st.header("📝 今日の記録を入力してください")
    
    # チャット風のインターフェース
    st.markdown("### 💬 チャット形式で入力")
    
    # 入力フォーム
    with st.form("daily_record_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🛏️ 睡眠")
            sleep_time = st.time_input("就寝時間", value=datetime.strptime("23:00", "%H:%M").time())
            wake_time = st.time_input("起床時間", value=datetime.strptime("07:00", "%H:%M").time())
            
            st.subheader("🍽️ 食事")
            breakfast = st.text_input("朝食", placeholder="例: ご飯、味噌汁、卵焼き")
            lunch = st.text_input("昼食", placeholder="例: サンドイッチ、サラダ")
            dinner = st.text_input("夕食", placeholder="例: 魚、野菜炒め、ご飯")
            
        with col2:
            st.subheader("🏃‍♀️ 運動")
            exercise_type = st.selectbox("運動の種類", 
                ["なし", "ウォーキング", "ジョギング", "筋トレ", "ヨガ", "その他"])
            exercise_duration = st.number_input("運動時間（分）", min_value=0, max_value=300, value=0)
            exercise_notes = st.text_area("運動メモ", placeholder="今日の運動について...")
            
            st.subheader("💭 今日の振り返り")
            mood = st.select_slider("今日の気分", 
                options=["😢", "😐", "🙂", "😊", "😄"], value="🙂")
            daily_notes = st.text_area("今日の出来事・感想", placeholder="今日はどんな日でしたか？")
        
        submitted = st.form_submit_button("📋 記録を保存", type="primary")
        
        if submitted:
            # データを保存
            data = load_data()
            record = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sleep_time": sleep_time.strftime("%H:%M"),
                "wake_time": wake_time.strftime("%H:%M"),
                "breakfast": breakfast,
                "lunch": lunch,
                "dinner": dinner,
                "exercise_type": exercise_type,
                "exercise_duration": exercise_duration,
                "exercise_notes": exercise_notes,
                "mood": mood,
                "daily_notes": daily_notes,
                "timestamp": datetime.now().isoformat()
            }
            data["records"].append(record)
            save_data(data)
            st.success("✅ 今日の記録が保存されました！")
            st.balloons()
    
    # 最近の記録を表示
    st.markdown("---")
    st.subheader("📅 最近の記録")
    data = load_data()
    if data["records"]:
        recent_records = sorted(data["records"], key=lambda x: x["date"], reverse=True)[:5]
        for record in recent_records:
            with st.expander(f"{record['date']} - {record['mood']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"🛏️ 就寝: {record['sleep_time']} → 起床: {record['wake_time']}")
                    st.write(f"🍽️ 朝食: {record['breakfast']}")
                    st.write(f"🍽️ 昼食: {record['lunch']}")
                    st.write(f"🍽️ 夕食: {record['dinner']}")
                with col2:
                    st.write(f"🏃‍♀️ 運動: {record['exercise_type']} ({record['exercise_duration']}分)")
                    if record['exercise_notes']:
                        st.write(f"📝 運動メモ: {record['exercise_notes']}")
                    if record['daily_notes']:
                        st.write(f"💭 今日の振り返り: {record['daily_notes']}")
    else:
        st.info("まだ記録がありません。最初の記録を入力してみましょう！")

def weekly_report_page():
    """週次レポートページ"""
    st.header("📊 週次レポート")
    st.info("🚧 この機能は実装中です。データ入力が蓄積されたら、週次の集計とグラフを表示します。")

def advice_page():
    """アドバイスページ"""
    st.header("💡 来週のアドバイス")
    st.info("🚧 この機能は実装中です。記録されたデータを分析して、個人に合わせたアドバイスを生成します。")

if __name__ == "__main__":
    main()