import streamlit as st
import time
import threading
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(
    page_title="ストレッチタイマー",
    page_icon="🧘‍♀️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .timer-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin: 1rem 0;
        color: white;
        text-align: center;
    }
    
    .timer-container.stretch-mode {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .timer-container.break-mode {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
    
    .timer-container.countdown-mode {
        background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
        animation: pulse 0.5s ease-in-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .timer-display {
        font-size: 4rem;
        font-weight: bold;
        margin: 1rem 0;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .status-text {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 1rem 0;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .next-action {
        font-size: 1.2rem;
        margin: 0.5rem 0;
        color: rgba(255,255,255,0.9);
    }
    
    .setting-section {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 25px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .start-btn {
        background: #28a745 !important;
        color: white !important;
    }
    
    .pause-btn {
        background: #ffc107 !important;
        color: #333 !important;
    }
    
    .stop-btn {
        background: #dc3545 !important;
        color: white !important;
    }
    
    @media (max-width: 768px) {
        .timer-display {
            font-size: 3rem;
        }
        
        .status-text {
            font-size: 2rem;
        }
        
        .timer-container {
            padding: 1.5rem 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# 音響機能のJavaScript
audio_js = """
<script>
class AudioManager {
    constructor() {
        this.audioContext = null;
        this.enabled = true;
        this.init();
    }
    
    async init() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('Web Audio API not supported');
        }
    }
    
    playSound(frequency, duration = 200, type = 'start') {
        if (!this.enabled || !this.audioContext) return;
        
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.3, this.audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration / 1000);
    }
    
    setEnabled(enabled) {
        this.enabled = enabled;
    }
}

window.audioManager = new AudioManager();

// Streamlitからの音響制御
window.playTimerSound = function(type) {
    const sounds = {
        'start': [800, 300],
        'end': [400, 500],
        'switch': [600, 500],
        'countdown': [1000, 100]
    };
    
    if (sounds[type] && window.audioManager) {
        window.audioManager.playSound(sounds[type][0], sounds[type][1], type);
    }
};

window.setSoundEnabled = function(enabled) {
    if (window.audioManager) {
        window.audioManager.setEnabled(enabled);
    }
};
</script>
"""

# 円形タイマー表示コンポーネント
def render_circular_timer(current_time, total_time, is_break_mode, is_countdown):
    progress = ((total_time - current_time) / total_time) * 360 if total_time > 0 else 0
    color = '#fa709a' if is_break_mode else '#4facfe'
    
    countdown_class = 'countdown-mode' if is_countdown else ''
    mode_class = 'break-mode' if is_break_mode else 'stretch-mode'
    
    timer_html = f"""
    <div class="timer-container {mode_class} {countdown_class}">
        <div style="
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: conic-gradient({color} {progress}deg, rgba(255,255,255,0.3) {progress}deg);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 1rem 0;
        ">
            <div style="
                width: 160px;
                height: 160px;
                background: rgba(255,255,255,0.95);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: inset 0 0 20px rgba(0,0,0,0.1);
            ">
                <div class="timer-display" style="color: #333;">{current_time}</div>
            </div>
        </div>
    </div>
    """
    
    return timer_html

# セッション状態の初期化
def init_session_state():
    if 'stretch_time' not in st.session_state:
        st.session_state.stretch_time = 60
    if 'break_time' not in st.session_state:
        st.session_state.break_time = 10
    if 'current_time' not in st.session_state:
        st.session_state.current_time = 60
    if 'total_time' not in st.session_state:
        st.session_state.total_time = 60
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'is_paused' not in st.session_state:
        st.session_state.is_paused = False
    if 'is_break_mode' not in st.session_state:
        st.session_state.is_break_mode = False
    if 'continuous_mode' not in st.session_state:
        st.session_state.continuous_mode = False
    if 'sound_enabled' not in st.session_state:
        st.session_state.sound_enabled = True
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None
    if 'timer_thread' not in st.session_state:
        st.session_state.timer_thread = None

# タイマー更新関数（session_stateのコンテキスト問題を回避）
def update_timer():
    # バックグラウンドタイマーは使わずにフロントエンド側で時間管理
    pass

# タイマー終了処理
def handle_timer_end():
    if not st.session_state.is_break_mode:
        # ストレッチ終了 → 休憩開始
        st.session_state.is_break_mode = True
        st.session_state.current_time = st.session_state.break_time
        st.session_state.total_time = st.session_state.break_time
    else:
        # 休憩終了
        if st.session_state.continuous_mode:
            # 連続モード：再びストレッチへ
            st.session_state.is_break_mode = False
            st.session_state.current_time = st.session_state.stretch_time
            st.session_state.total_time = st.session_state.stretch_time
        else:
            # スポットモード：終了
            stop_timer()

# タイマー開始
def start_timer():
    st.session_state.is_running = True
    st.session_state.is_paused = False
    st.session_state.last_update = datetime.now()

# タイマー一時停止
def pause_timer():
    st.session_state.is_paused = True

# タイマー停止
def stop_timer():
    st.session_state.is_running = False
    st.session_state.is_paused = False
    st.session_state.is_break_mode = False
    st.session_state.current_time = st.session_state.stretch_time
    st.session_state.total_time = st.session_state.stretch_time

# メイン画面
def main():
    init_session_state()
    
    # 音響機能JavaScript
    st.components.v1.html(audio_js, height=0)
    
    # タイトル
    st.title("🧘‍♀️ ストレッチタイマー")
    
    # タイマー表示
    is_countdown = st.session_state.current_time <= 5 and st.session_state.is_running and not st.session_state.is_paused
    timer_html = render_circular_timer(
        st.session_state.current_time,
        st.session_state.total_time,
        st.session_state.is_break_mode,
        is_countdown
    )
    st.markdown(timer_html, unsafe_allow_html=True)
    
    # 状態表示
    if not st.session_state.is_running:
        status = "準備完了"
        next_action = "開始ボタンを押してください"
    elif st.session_state.is_paused:
        status = "一時停止中"
        next_action = "再開ボタンを押してください"
    elif st.session_state.is_break_mode:
        status = "休憩中"
        if st.session_state.continuous_mode:
            next_action = f"次：ストレッチ {st.session_state.stretch_time}秒"
        else:
            next_action = "次：終了"
    else:
        status = "ストレッチ中"
        next_action = f"次：休憩 {st.session_state.break_time}秒"
    
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0;">
        <h2 style="color: #333; margin-bottom: 0.5rem;">{status}</h2>
        <p style="color: #666; font-size: 1.1rem;">{next_action}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 設定エリア
    with st.expander("⚙️ 設定", expanded=not st.session_state.is_running):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("ストレッチ時間")
            stretch_options = [30, 40, 50, 60]
            stretch_index = stretch_options.index(st.session_state.stretch_time) if st.session_state.stretch_time in stretch_options else 3
            new_stretch_time = st.selectbox(
                "ストレッチ時間を選択",
                stretch_options,
                index=stretch_index,
                format_func=lambda x: f"{x}秒",
                disabled=st.session_state.is_running,
                key="stretch_select"
            )
            
            if new_stretch_time != st.session_state.stretch_time:
                st.session_state.stretch_time = new_stretch_time
                if not st.session_state.is_running and not st.session_state.is_break_mode:
                    st.session_state.current_time = new_stretch_time
                    st.session_state.total_time = new_stretch_time
        
        with col2:
            st.subheader("休憩時間")
            break_options = [10, 20, 30]
            break_index = break_options.index(st.session_state.break_time) if st.session_state.break_time in break_options else 0
            st.session_state.break_time = st.selectbox(
                "休憩時間を選択",
                break_options,
                index=break_index,
                format_func=lambda x: f"{x}秒",
                disabled=st.session_state.is_running,
                key="break_select"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("動作モード")
            st.session_state.continuous_mode = st.checkbox(
                "連続モード（繰り返し）",
                value=st.session_state.continuous_mode,
                disabled=st.session_state.is_running,
                help="オフの場合は1回のストレッチ→休憩で終了"
            )
        
        with col4:
            st.subheader("効果音")
            new_sound_enabled = st.checkbox(
                "効果音を有効にする",
                value=st.session_state.sound_enabled,
                help="開始音、終了音、切り替え音、カウントダウン音（ブラウザの音量設定を確認してください）"
            )
            
            if st.button("🔊 音声テスト", help="効果音が正常に動作するかテストします"):
                st.components.v1.html("""
                <script>
                if (window.playTimerSound) {
                    window.playTimerSound('start');
                } else {
                    console.log('音響機能が初期化されていません');
                }
                </script>
                """, height=0)
                st.success("テスト音を再生しました（音が聞こえない場合は音量設定を確認してください）")
            
            if new_sound_enabled != st.session_state.sound_enabled:
                st.session_state.sound_enabled = new_sound_enabled
                st.components.v1.html(f"""
                <script>
                if (window.setSoundEnabled) {{
                    window.setSoundEnabled({str(new_sound_enabled).lower()});
                }}
                </script>
                """, height=0)
    
    # 操作ボタン
    col1, col2 = st.columns(2)
    
    with col1:
        if not st.session_state.is_running:
            if st.button("🎯 開始", key="start_btn", use_container_width=True):
                start_timer()
                if st.session_state.sound_enabled:
                    st.components.v1.html("""
                    <script>
                    if (window.playTimerSound) {
                        window.playTimerSound('start');
                    }
                    </script>
                    """, height=0)
                st.rerun()
        elif st.session_state.is_paused:
            if st.button("▶️ 再開", key="resume_btn", use_container_width=True):
                start_timer()
                st.rerun()
        else:
            if st.button("⏸️ 一時停止", key="pause_btn", use_container_width=True):
                pause_timer()
                st.rerun()
    
    with col2:
        if st.button("⏹️ 停止", key="stop_btn", use_container_width=True):
            stop_timer()
            st.rerun()
    
    # タイマーが動作中の場合、時間を更新
    if st.session_state.is_running and not st.session_state.is_paused:
        current = datetime.now()
        if st.session_state.last_update is not None:
            elapsed = (current - st.session_state.last_update).total_seconds()
            if elapsed >= 1.0:
                st.session_state.current_time -= int(elapsed)
                st.session_state.last_update = current
                
                if st.session_state.current_time <= 0:
                    handle_timer_end()
                
                st.rerun()
        else:
            st.session_state.last_update = current
            
        # 定期更新のために少し待機
        time.sleep(0.1)
        st.rerun()
    
    # カウントダウン音の再生
    if is_countdown and st.session_state.sound_enabled:
        st.components.v1.html("""
        <script>
        if (window.playTimerSound) {
            window.playTimerSound('countdown');
        }
        </script>
        """, height=0)

if __name__ == "__main__":
    main()