"""
YouTube Channel Analytics Scraper — Streamlit App
==================================================
pip install streamlit google-api-python-client pandas openpyxl tqdm
streamlit run app.py
"""

import io
import json
import re
import time
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="YouTube Analytics Scraper",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ────────────────────────────────────────────────────────────────

MAX_COMMENTS_PER_VIDEO = 100
MAX_VIDEOS = 500
REQUEST_DELAY = 0.1

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── App background ── */
.stApp { background: #f0f2f6; color: #111; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1a1a2e !important;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }
[data-testid="stSidebar"] .stMarkdown p { color: #aab !important; }
[data-testid="stSidebar"] input {
    background: #16213e !important;
    color: #fff !important;
    border-color: #0f3460 !important;
    border-radius: 8px !important;
}

/* ── Login card ── */
.login-wrap {
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 24px;
}
.login-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 48px 44px 40px;
    width: 100%; max-width: 440px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.35);
}
.login-logo {
    display: flex; align-items: center; justify-content: center;
    width: 64px; height: 64px;
    background: #FF0000;
    border-radius: 16px;
    font-size: 30px;
    margin: 0 auto 20px;
}
.login-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 26px; font-weight: 700;
    color: #111; text-align: center; margin: 0 0 6px;
}
.login-sub {
    font-size: 14px; color: #666;
    text-align: center; margin: 0 0 32px;
    line-height: 1.5;
}
.login-section-label {
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    color: #999; margin: 20px 0 12px;
    display: flex; align-items: center; gap: 8px;
}
.login-section-label::before,
.login-section-label::after {
    content: ""; flex: 1;
    height: 1px; background: #eee;
}
.login-divider {
    border: none; border-top: 1px solid #eee;
    margin: 24px 0;
}
.security-note {
    background: #f8f9fc;
    border: 1px solid #e8eaf0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 24px;
}
.security-note p {
    font-size: 12px; color: #888;
    margin: 0; line-height: 1.8;
}

/* ── Main app ── */
.yt-header {
    display: flex; align-items: center; gap: 14px;
    padding: 28px 0 20px;
    border-bottom: 2px solid #e0e3ea;
    margin-bottom: 28px;
}
.yt-logo {
    background: #FF0000; border-radius: 10px;
    width: 44px; height: 44px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; flex-shrink: 0;
}
.yt-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px; font-weight: 700; color: #111;
    margin: 0; letter-spacing: -0.3px;
}
.yt-sub { font-size: 13px; color: #888; margin: 2px 0 0; }

/* ── Metric cards ── */
.metric-row {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 14px; margin: 20px 0;
}
.metric-card {
    background: #ffffff;
    border: 1px solid #e0e3ea;
    border-radius: 14px; padding: 20px 22px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.metric-label {
    font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.8px; color: #999;
    font-weight: 600; margin-bottom: 8px;
}
.metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 26px; font-weight: 700; color: #111; line-height: 1;
}
.metric-sub { font-size: 11px; color: #aaa; margin-top: 5px; }

/* ── Channel banner ── */
.channel-banner {
    background: #fff;
    border: 1px solid #e0e3ea;
    border-radius: 16px; padding: 24px 28px;
    margin-bottom: 24px;
    display: flex; gap: 20px; align-items: flex-start;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.channel-thumb {
    width: 72px; height: 72px; border-radius: 50%;
    object-fit: cover; flex-shrink: 0;
    border: 3px solid #FF0000;
}
.channel-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 20px; font-weight: 700; color: #111; margin: 0 0 4px;
}
.channel-handle { font-size: 13px; color: #FF0000; margin: 0 0 8px; }
.channel-desc { font-size: 13px; color: #666; line-height: 1.6; max-width: 600px; }

/* ── Top video card ── */
.top-video {
    background: #fff; border: 1px solid #e8eaf0;
    border-radius: 10px; padding: 14px 16px;
    margin-bottom: 8px; display: flex; gap: 14px; align-items: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.rank-badge {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 14px; font-weight: 700; color: #FF0000;
    width: 28px; flex-shrink: 0; text-align: center;
}
.video-title-text {
    font-size: 13px; font-weight: 500; color: #222;
    flex: 1; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.video-views {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px; font-weight: 600; color: #666; flex-shrink: 0;
}

/* ── Section heading ── */
.section-heading {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 14px; font-weight: 700; color: #555;
    text-transform: uppercase; letter-spacing: 1px;
    margin: 28px 0 14px; padding-bottom: 8px;
    border-bottom: 2px solid #e8eaf0;
}

/* ── Progress ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #FF0000, #FF6B6B) !important;
    border-radius: 4px;
}

/* ── Buttons ── */
.stButton > button {
    background: #FF0000 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 14px !important;
    padding: 10px 24px !important; transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── Download button ── */
.stDownloadButton > button {
    background: #fff !important; color: #333 !important;
    border: 1px solid #dde !important; border-radius: 8px !important;
    font-weight: 500 !important;
}
.stDownloadButton > button:hover {
    border-color: #FF0000 !important; color: #FF0000 !important;
}

/* ── Inputs (main area) ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #fff !important;
    border-color: #dde !important; color: #111 !important;
    border-radius: 8px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    font-weight: 600 !important; color: #666 !important;
}
.stTabs [aria-selected="true"] { color: #FF0000 !important; }

/* ── Alert ── */
.stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Logger ──────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Core Functions ───────────────────────────────────────────────────────────

def create_youtube_client(api_key: str):
    return build("youtube", "v3", developerKey=api_key)


def resolve_channel_id(youtube, channel_input: str) -> tuple:
    channel_input = channel_input.strip()
    if channel_input.startswith("@"):
        response = youtube.search().list(
            part="snippet", q=channel_input, type="channel", maxResults=5
        ).execute()
        for item in response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            ch_resp = youtube.channels().list(
                part="snippet,statistics,brandingSettings", id=channel_id
            ).execute()
            if ch_resp["items"]:
                ch = ch_resp["items"][0]
                custom_url = ch["snippet"].get("customUrl", "").lower()
                handle_lower = channel_input.lower().lstrip("@")
                if custom_url in [f"@{handle_lower}", handle_lower]:
                    return channel_id, ch
        if response.get("items"):
            channel_id = response["items"][0]["snippet"]["channelId"]
            ch_resp = youtube.channels().list(
                part="snippet,statistics,brandingSettings", id=channel_id
            ).execute()
            if ch_resp["items"]:
                return channel_id, ch_resp["items"][0]
        raise ValueError(f"ไม่พบช่องสำหรับ handle: {channel_input}")
    elif channel_input.startswith("UC"):
        ch_resp = youtube.channels().list(
            part="snippet,statistics,brandingSettings", id=channel_input
        ).execute()
        if ch_resp["items"]:
            return channel_input, ch_resp["items"][0]
        raise ValueError(f"ไม่พบ Channel ID: {channel_input}")
    else:
        raise ValueError("กรุณาใส่ @handle หรือ Channel ID ที่ขึ้นต้นด้วย UC")


def parse_channel_info(channel_data: dict) -> dict:
    snippet = channel_data.get("snippet", {})
    stats = channel_data.get("statistics", {})
    branding = channel_data.get("brandingSettings", {}).get("channel", {})
    return {
        "channel_id": channel_data["id"],
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "custom_url": snippet.get("customUrl", ""),
        "country": snippet.get("country", ""),
        "published_at": snippet.get("publishedAt", ""),
        "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "view_count": int(stats.get("viewCount", 0)),
        "keywords": branding.get("keywords", ""),
    }


def get_uploads_playlist_id(youtube, channel_id: str) -> str:
    response = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    if not response["items"]:
        raise ValueError(f"ไม่พบ channel: {channel_id}")
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def parse_duration(iso_duration: str) -> int:
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, iso_duration)
    if not match:
        return 0
    return (int(match.group(1) or 0) * 3600 +
            int(match.group(2) or 0) * 60 +
            int(match.group(3) or 0))


def format_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def parse_video_item(item: dict) -> dict:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    status = item.get("status", {})
    topics = item.get("topicDetails", {})
    dur = parse_duration(content.get("duration", "PT0S"))
    tags = snippet.get("tags", [])
    return {
        "video_id": item["id"],
        "title": snippet.get("title", ""),
        "description": snippet.get("description", "")[:500],
        "published_at": snippet.get("publishedAt", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "tags": ", ".join(tags) if tags else "",
        "category_id": snippet.get("categoryId", ""),
        "default_language": snippet.get("defaultAudioLanguage", snippet.get("defaultLanguage", "")),
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0)),
        "favorite_count": int(stats.get("favoriteCount", 0)),
        "duration_seconds": dur,
        "duration_formatted": format_duration(dur),
        "definition": content.get("definition", ""),
        "caption": content.get("caption", "false"),
        "licensed_content": content.get("licensedContent", False),
        "privacy_status": status.get("privacyStatus", ""),
        "embeddable": status.get("embeddable", True),
        "topic_categories": ", ".join(
            [t.split("/")[-1].replace("_", " ") for t in topics.get("topicCategories", [])]
        ),
        "video_url": f"https://www.youtube.com/watch?v={item['id']}",
    }


def get_all_video_ids(youtube, playlist_id: str, max_videos: int, progress_cb=None) -> list:
    video_ids = []
    next_page_token = None
    while len(video_ids) < max_videos:
        params = {
            "part": "contentDetails",
            "playlistId": playlist_id,
            "maxResults": min(50, max_videos - len(video_ids)),
        }
        if next_page_token:
            params["pageToken"] = next_page_token
        response = youtube.playlistItems().list(**params).execute()
        for item in response.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        if progress_cb:
            progress_cb(len(video_ids), max_videos, "ดึง Video IDs")
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(REQUEST_DELAY)
    return video_ids


def get_video_details_batch(youtube, video_ids: list, progress_cb=None) -> list:
    all_videos = []
    total = len(video_ids)
    for i in range(0, total, 50):
        batch = video_ids[i:i+50]
        response = youtube.videos().list(
            part="snippet,statistics,contentDetails,status,topicDetails",
            id=",".join(batch)
        ).execute()
        for item in response.get("items", []):
            all_videos.append(parse_video_item(item))
        if progress_cb:
            progress_cb(min(i + 50, total), total, "ดึงรายละเอียดวิดีโอ")
        time.sleep(REQUEST_DELAY)
    return all_videos


def get_comments_for_video(youtube, video_id: str, max_comments: int) -> list:
    comments = []
    next_page_token = None
    try:
        while len(comments) < max_comments:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(100, max_comments - len(comments)),
                "order": "relevance",
                "textFormat": "plainText",
            }
            if next_page_token:
                params["pageToken"] = next_page_token
            response = youtube.commentThreads().list(**params).execute()
            for item in response.get("items", []):
                top = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "video_id": video_id,
                    "comment_id": item["id"],
                    "author": top.get("authorDisplayName", ""),
                    "author_channel_id": top.get("authorChannelId", {}).get("value", ""),
                    "text": top.get("textDisplay", ""),
                    "like_count": int(top.get("likeCount", 0)),
                    "reply_count": item["snippet"].get("totalReplyCount", 0),
                    "published_at": top.get("publishedAt", ""),
                    "updated_at": top.get("updatedAt", ""),
                })
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
            time.sleep(REQUEST_DELAY)
    except HttpError as e:
        if e.resp.status == 403 or "disabled" in str(e).lower():
            pass
        else:
            logger.warning(f"Comment error {video_id}: {e}")
    return comments


# ─── Export Helpers ──────────────────────────────────────────────────────────

def build_excel_bytes(channel_info: dict, videos: list, comments: list) -> bytes:
    df_ch = pd.DataFrame([channel_info])
    df_vid = pd.DataFrame(videos)
    df_com = pd.DataFrame(comments) if comments else pd.DataFrame()

    summary_rows = []
    if not df_vid.empty:
        top = df_vid.loc[df_vid["view_count"].idxmax()]
        bot = df_vid.loc[df_vid["view_count"].idxmin()]
        summary_rows = [
            ("จำนวนวิดีโอทั้งหมด", len(df_vid)),
            ("ยอดวิวรวม", df_vid["view_count"].sum()),
            ("ยอดวิวเฉลี่ย", round(df_vid["view_count"].mean(), 0)),
            ("ยอดวิวสูงสุด", df_vid["view_count"].max()),
            ("ยอดไลค์รวม", df_vid["like_count"].sum()),
            ("ยอดคอมเมนต์รวม", df_vid["comment_count"].sum()),
            ("ความยาวเฉลี่ย (นาที)", round(df_vid["duration_seconds"].mean() / 60, 1)),
            ("VDO ยอดวิวสูงสุด", top["title"]),
            ("VDO ยอดวิวต่ำสุด", bot["title"]),
        ]
    df_sum = pd.DataFrame(summary_rows, columns=["metric", "value"])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_ch.to_excel(writer, sheet_name="Channel Info", index=False)
        if not df_vid.empty:
            df_vid.to_excel(writer, sheet_name="Videos", index=False)
        if not df_com.empty:
            df_com.to_excel(writer, sheet_name="Comments", index=False)
        if not df_sum.empty:
            df_sum.to_excel(writer, sheet_name="Summary", index=False)
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max((len(str(cell.value or "")) for cell in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)
    buf.seek(0)
    return buf.read()


def build_json_bytes(channel_info, videos, comments) -> bytes:
    data = {
        "scraped_at": datetime.now().isoformat(),
        "channel": channel_info,
        "videos": videos,
        "comments": comments,
    }
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


# ─── Number Formatter ─────────────────────────────────────────────────────────

def fmt_num(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ─── Streamlit App ────────────────────────────────────────────────────────────

def render_header():
    st.markdown("""
    <div class="yt-header">
        <div class="yt-logo">▶</div>
        <div>
            <p class="yt-title">YouTube Analytics Scraper</p>
            <p class="yt-sub">ดึงข้อมูลวิดีโอ สถิติ และ comments จากช่อง YouTube ใดก็ได้</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_setup_page():
    """หน้า Login — Username + Password + API Key"""

    # ── Credentials (ตั้งค่าใน .streamlit/secrets.toml หรือ Streamlit Cloud Secrets)
    # secrets.toml:
    #   APP_USERNAME = "admin"
    #   APP_PASSWORD = "yourpassword"
    import streamlit as st
    try:
        valid_user = st.secrets["APP_USERNAME"]
        valid_pass = st.secrets["APP_PASSWORD"]
    except Exception:
        valid_user = "admin"
        valid_pass = "1234"

    # ── Full-page gradient background ────────────────────────────────────────
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 55%, #0f3460 100%) !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    /* Force Streamlit columns to center */
    .block-container { padding-top: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Centered card layout ──────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; justify-content:center; padding-top:60px; padding-bottom:40px;">
      <div style="background:#ffffff; border-radius:24px; padding:52px 48px 44px;
                  width:420px; box-shadow:0 32px 80px rgba(0,0,0,0.45);">

        <!-- Logo -->
        <div style="display:flex; justify-content:center; margin-bottom:20px;">
          <div style="background:#FF0000; border-radius:18px; width:68px; height:68px;
               display:flex; align-items:center; justify-content:center;
               font-size:32px; box-shadow:0 8px 24px rgba(255,0,0,0.35);">▶</div>
        </div>

        <!-- Title -->
        <p style="font-family:'Space Grotesk',sans-serif; font-size:28px; font-weight:700;
           color:#111; text-align:center; margin:0 0 6px;">YouTube Analytics</p>
        <p style="font-size:14px; color:#888; text-align:center; margin:0 0 36px; line-height:1.5;">
          เข้าสู่ระบบเพื่อเริ่มใช้งาน
        </p>

        <!-- Section divider: Account -->
        <p style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px;
           color:#bbb; margin:0 0 16px; text-align:center;">
          ── บัญชีผู้ใช้ ──
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Form fields (must use Streamlit native for interactivity) ────────────
    _, col, _ = st.columns([1, 8, 1])
    with col:
        # Card wrapper (just visual padding)
        st.markdown("""
        <div style="background:#fff; border-radius:0 0 24px 24px;
             margin-top:-48px; padding:0 48px 0; position:relative; z-index:1;">
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("👤  Username", placeholder="กรอก Username")
        password = st.text_input("🔒  Password", type="password", placeholder="กรอก Password")

        st.markdown("""<hr style="border:none;border-top:1px solid #eee;margin:20px 0 16px;">
        <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
           color:#bbb;text-align:center;margin:0 0 14px;">── YouTube API Key ──</p>
        """, unsafe_allow_html=True)

        api_key = st.text_input(
            "🔑  YouTube Data API v3 Key",
            type="password",
            placeholder="AIzaSy...",
        )
        st.markdown("""
        <p style="font-size:12px; color:#aaa; margin:-6px 0 20px; line-height:1.6;">
        ยังไม่มี Key?
        <a href="https://console.cloud.google.com/apis/credentials"
           target="_blank" style="color:#FF0000; font-weight:600;">
          Google Cloud Console →</a>
        </p>
        """, unsafe_allow_html=True)

        login_btn = st.button("เข้าสู่ระบบ →", use_container_width=True)

        st.markdown("""
        <div style="background:#f8f9fc; border:1px solid #eee; border-radius:10px;
             padding:14px 16px; margin-top:20px;">
          <p style="font-size:11px; color:#bbb; margin:0; line-height:1.9; text-align:center;">
            🔒 ข้อมูลทั้งหมดเก็บเฉพาะใน session นี้เท่านั้น<br>
            ปิดหน้าต่าง = ล้างข้อมูลทันที
          </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Validation ────────────────────────────────────────────────────────────
    if login_btn:
        errors = []
        if not username:
            errors.append("กรุณากรอก Username")
        if not password:
            errors.append("กรุณากรอก Password")
        if not api_key:
            errors.append("กรุณากรอก API Key")
        elif not api_key.startswith("AIza"):
            errors.append("API Key ไม่ถูกต้อง (ควรขึ้นต้นด้วย AIza...)")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        elif username != valid_user or password != valid_pass:
            st.error("❌ Username หรือ Password ไม่ถูกต้อง")
        else:
            with st.spinner("กำลังตรวจสอบ API Key..."):
                try:
                    yt = create_youtube_client(api_key)
                    yt.videos().list(part="snippet", id="dQw4w9WgXcQ").execute()
                    st.session_state.api_key = api_key
                    st.session_state.setup_done = True
                    st.rerun()
                except HttpError as e:
                    if "400" in str(e) or "invalid" in str(e).lower():
                        st.error("❌ API Key ไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง")
                    elif "403" in str(e):
                        st.error("❌ API Key ถูกต้องแต่ยังไม่ได้เปิดใช้ YouTube Data API v3")
                    else:
                        st.error(f"❌ ไม่สามารถเชื่อมต่อได้: {e}")
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")


def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("### ⚙️ การตั้งค่า")

        # แสดง key status + ปุ่ม logout
        masked = "•" * 20 + st.session_state.api_key[-4:]
        st.markdown(f"""
        <div style="background:#1a1a1a; border:1px solid #2a2a2a; border-radius:8px;
             padding:10px 12px; margin-bottom:12px;">
            <p style="font-size:11px; color:#555; margin:0 0 3px;
               text-transform:uppercase; letter-spacing:0.5px;">🔑 API Key</p>
            <p style="font-size:13px; color:#888; margin:0; font-family:monospace;">{masked}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 เปลี่ยน API Key", use_container_width=True):
            st.session_state.setup_done = False
            st.session_state.api_key = ""
            st.session_state.result = None
            st.rerun()

        st.markdown("---")

        channel = st.text_input(
            "📺 ชื่อช่อง",
            placeholder="@handle หรือ UCxxxxxxxx",
            help="รองรับทั้ง @handle และ Channel ID"
        )

        st.markdown("---")
        st.markdown("**ตัวเลือกการดึงข้อมูล**")

        max_videos = st.number_input(
            "🎬 จำนวนวิดีโอสูงสุด",
            min_value=1, max_value=10000,
            value=50, step=10,
            help="จำนวนวิดีโอล่าสุดที่ต้องการดึง"
        )

        fetch_comments = st.checkbox("💬 ดึง Comments ด้วย", value=False)

        max_comments = MAX_COMMENTS_PER_VIDEO
        if fetch_comments:
            max_comments = st.number_input(
                "💬 Comments ต่อวิดีโอ",
                min_value=0, max_value=200,
                value=20, step=10
            )

        st.markdown("---")
        st.markdown("**Export Format**")
        export_excel = st.checkbox("📊 Excel (.xlsx)", value=True)
        export_json = st.checkbox("📄 JSON (.json)", value=False)

        st.markdown("---")
        run = st.button("🚀 เริ่มดึงข้อมูล", use_container_width=True)

        st.markdown("""
        <div style="margin-top:24px; font-size:11px; color:#444; line-height:1.7;">
        💡 <strong style="color:#555">หมายเหตุ</strong><br>
        • YouTube API มี quota 10,000 units/วัน<br>
        • แต่ละวิดีโอใช้ ~2–3 units<br>
        • Comments ใช้ quota มากกว่า
        </div>
        """, unsafe_allow_html=True)

    return {
        "api_key": st.session_state.api_key,
        "channel": channel,
        "max_videos": int(max_videos),
        "fetch_comments": fetch_comments,
        "max_comments": int(max_comments),
        "export_excel": export_excel,
        "export_json": export_json,
        "run": run,
    }


def render_channel_banner(ch: dict):
    thumb = ch.get("thumbnail_url", "")
    img_html = f'<img src="{thumb}" class="channel-thumb">' if thumb else \
               '<div style="width:72px;height:72px;border-radius:50%;background:#FF0000;display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0;">▶</div>'

    desc = (ch.get("description", "")[:200] + "…") if len(ch.get("description", "")) > 200 else ch.get("description", "")
    country = f" · 🌏 {ch['country']}" if ch.get("country") else ""
    since = ch.get("published_at", "")[:4]
    since_str = f" · สร้างปี {since}" if since else ""

    st.markdown(f"""
    <div class="channel-banner">
        {img_html}
        <div style="flex:1; min-width:0;">
            <p class="channel-name">{ch['title']}</p>
            <p class="channel-handle">{ch.get('custom_url', '')}{country}{since_str}</p>
            <p class="channel-desc">{desc}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(ch: dict, videos: list):
    df = pd.DataFrame(videos)
    avg_views = fmt_num(int(df["view_count"].mean())) if not df.empty else "—"
    total_views = fmt_num(df["view_count"].sum()) if not df.empty else "—"

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-label">Subscribers</div>
            <div class="metric-value">{fmt_num(ch['subscriber_count'])}</div>
            <div class="metric-sub">ผู้ติดตาม</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Videos</div>
            <div class="metric-value">{len(videos):,}</div>
            <div class="metric-sub">วิดีโอที่ดึงได้</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Views</div>
            <div class="metric-value">{total_views}</div>
            <div class="metric-sub">ยอดวิวรวม</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Views</div>
            <div class="metric-value">{avg_views}</div>
            <div class="metric-sub">เฉลี่ยต่อวิดีโอ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_top_videos(videos: list, n: int = 10):
    st.markdown('<p class="section-heading">🏆 Top Videos by Views</p>', unsafe_allow_html=True)
    df = pd.DataFrame(videos).sort_values("view_count", ascending=False).head(n)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        st.markdown(f"""
        <div class="top-video">
            <span class="rank-badge">#{i}</span>
            <a href="{row['video_url']}" target="_blank" 
               style="text-decoration:none; flex:1; min-width:0;">
                <span class="video-title-text">{row['title']}</span>
            </a>
            <span class="video-views">{fmt_num(int(row['view_count']))} views</span>
        </div>
        """, unsafe_allow_html=True)


def render_charts(videos: list):
    df = pd.DataFrame(videos)
    if df.empty:
        return

    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    df["year_month"] = df["published_at"].dt.to_period("M").astype(str)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-heading">📈 Views Distribution</p>', unsafe_allow_html=True)
        hist_data = df["view_count"].clip(upper=df["view_count"].quantile(0.95))
        st.bar_chart(
            hist_data.value_counts(bins=20).sort_index().rename("count"),
            color="#FF0000"
        )

    with col2:
        st.markdown('<p class="section-heading">📅 Uploads per Month</p>', unsafe_allow_html=True)
        monthly = df.groupby("year_month").size().tail(24)
        st.bar_chart(monthly.rename("uploads"), color="#FF4444")

    st.markdown('<p class="section-heading">💡 Views vs Likes Scatter</p>', unsafe_allow_html=True)
    scatter_df = df[["title", "view_count", "like_count", "duration_seconds"]].copy()
    scatter_df.columns = ["title", "Views", "Likes", "Duration (s)"]
    st.scatter_chart(scatter_df, x="Views", y="Likes", size="Duration (s)", color="#FF0000")


def render_data_tables(videos: list, comments: list):
    st.markdown('<p class="section-heading">📋 ข้อมูลวิดีโอทั้งหมด</p>', unsafe_allow_html=True)
    df = pd.DataFrame(videos)
    display_cols = ["title", "published_at", "view_count", "like_count",
                    "comment_count", "duration_formatted", "video_url"]
    available = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[available].sort_values("view_count", ascending=False),
        use_container_width=True,
        height=400,
        column_config={
            "video_url": st.column_config.LinkColumn("🔗 URL"),
            "view_count": st.column_config.NumberColumn("👁 Views", format="%d"),
            "like_count": st.column_config.NumberColumn("👍 Likes", format="%d"),
            "comment_count": st.column_config.NumberColumn("💬 Comments", format="%d"),
        }
    )

    if comments:
        st.markdown('<p class="section-heading">💬 Comments Sample</p>', unsafe_allow_html=True)
        df_com = pd.DataFrame(comments)
        st.dataframe(
            df_com[["video_id", "author", "text", "like_count", "published_at"]].head(200),
            use_container_width=True, height=300
        )


def render_downloads(channel_info, videos, comments, cfg):
    st.markdown('<p class="section-heading">⬇️ ดาวน์โหลด</p>', unsafe_allow_html=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in channel_info["title"])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    cols = st.columns(2)
    if cfg["export_excel"]:
        with cols[0]:
            excel_bytes = build_excel_bytes(channel_info, videos, comments)
            st.download_button(
                "📊 ดาวน์โหลด Excel",
                data=excel_bytes,
                file_name=f"youtube_{safe}_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    if cfg["export_json"]:
        with cols[1]:
            json_bytes = build_json_bytes(channel_info, videos, comments)
            st.download_button(
                "📄 ดาวน์โหลด JSON",
                data=json_bytes,
                file_name=f"youtube_{safe}_{ts}.json",
                mime="application/json",
                use_container_width=True
            )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # ─── Session state init ───────────────────────────────────────────────────
    if "setup_done" not in st.session_state:
        st.session_state.setup_done = False
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "result" not in st.session_state:
        st.session_state.result = None

    # ─── Gate: show setup page until API Key is validated ────────────────────
    if not st.session_state.setup_done:
        render_setup_page()
        st.stop()

    # ─── Main app (API Key already validated) ─────────────────────────────────
    render_header()
    cfg = render_sidebar()

    if cfg["run"]:
        if not cfg["channel"]:
            st.error("❌ กรุณาใส่ชื่อช่องหรือ Channel ID")
            st.stop()

        # ─── Scraping with live progress ──
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(done, total, label):
            pct = min(done / max(total, 1), 1.0)
            progress_bar.progress(pct)
            status_text.markdown(
                f'<p style="color:#888;font-size:13px;">⏳ {label}: {done}/{total}</p>',
                unsafe_allow_html=True
            )

        try:
            youtube = create_youtube_client(cfg["api_key"])

            status_text.markdown('<p style="color:#888;font-size:13px;">🔍 ค้นหาช่อง...</p>', unsafe_allow_html=True)
            channel_id, raw_ch = resolve_channel_id(youtube, cfg["channel"])
            channel_info = parse_channel_info(raw_ch)

            status_text.markdown('<p style="color:#888;font-size:13px;">📋 ดึง Video IDs...</p>', unsafe_allow_html=True)
            playlist_id = get_uploads_playlist_id(youtube, channel_id)
            video_ids = get_all_video_ids(youtube, playlist_id, cfg["max_videos"], update_progress)

            video_ids = video_ids[:cfg["max_videos"]]
            videos = get_video_details_batch(youtube, video_ids, update_progress)

            comments = []
            if cfg["fetch_comments"] and videos:
                for idx, vid_id in enumerate(video_ids):
                    update_progress(idx + 1, len(video_ids), "ดึง Comments")
                    comments.extend(get_comments_for_video(youtube, vid_id, cfg["max_comments"]))
                    time.sleep(REQUEST_DELAY)

            progress_bar.progress(1.0)
            status_text.markdown('<p style="color:#00cc66;font-size:13px;">✅ ดึงข้อมูลเสร็จแล้ว!</p>', unsafe_allow_html=True)

            st.session_state.result = {
                "channel": channel_info,
                "videos": videos,
                "comments": comments,
                "cfg": cfg,
            }

        except HttpError as e:
            progress_bar.empty()
            status_text.empty()
            err_msg = str(e)
            if "quota" in err_msg.lower():
                st.error("❌ API Quota หมด กรุณารอถึงวันถัดไปหรือใช้ API Key อื่น")
            elif "invalid" in err_msg.lower() or "400" in err_msg:
                st.error("❌ API Key ไม่ถูกต้อง")
            else:
                st.error(f"❌ YouTube API Error: {e}")
            st.stop()

        except ValueError as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ {e}")
            st.stop()

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            st.stop()

    # ─── Render Results ────────────────────────────────────────────────────────
    if st.session_state.result:
        res = st.session_state.result
        ch = res["channel"]
        videos = res["videos"]
        comments = res["comments"]
        result_cfg = res["cfg"]

        render_channel_banner(ch)
        render_metrics(ch, videos)

        if videos:
            tab1, tab2, tab3 = st.tabs(["🏆 Top Videos", "📊 Charts", "📋 Data Table"])

            with tab1:
                render_top_videos(videos, n=10)

            with tab2:
                render_charts(videos)

            with tab3:
                render_data_tables(videos, comments)

            render_downloads(ch, videos, comments, result_cfg)

    else:
        # Welcome state
        st.markdown("""
        <div style="text-align:center; padding:80px 20px; color:#333;">
            <div style="font-size:72px; margin-bottom:16px;">▶️</div>
            <p style="font-family:'Space Grotesk',sans-serif; font-size:22px; 
               font-weight:700; color:#555; margin:0 0 10px;">
                พร้อมดึงข้อมูล YouTube
            </p>
            <p style="font-size:14px; color:#444; max-width:400px; margin:0 auto; line-height:1.7;">
                ใส่ชื่อช่องใน Sidebar ด้านซ้าย<br>
                จากนั้นกด <strong style="color:#FF4444">🚀 เริ่มดึงข้อมูล</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()