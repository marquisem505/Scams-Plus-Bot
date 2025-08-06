import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Bot Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-2286707356"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "6967780222"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DEFAULT_RANK = "Lookout"

VALID_RANKS = [
    "Lookout",
    "Runner",
    "Closer",
    "Inner Circle",
    "OG Members"
]

PROMOTION_REQUEST_TEMPLATE = (
    "📤 New Promotion Request:\n\n"
    "👤 User: {username}\n"
    "🏷 Current Rank: {current_rank}\n"
    "🎯 Requested Topic: {topic}\n"
    "📩 Message: {message}"
)
# --- Topic Mapping ---
topic_name_to_id = {
    "Welcome To Scam's Plus - Start Here": 2458,
    "General Chat": 2401,
    "Scammers Warnings": 2408,
    "Announcements": 2405,
    "Con Academy": 2406,
    "Questions": 2411,
    "Tools & Bots": 2404,
    "Verified Guides": 2403,
    "Verified Vendors / Collabs": 2407,
    "Testing Lab": 2454,
    "VIP Lounge": 2402
}
# --- Rank Access ---
rank_access_topics = {
    "Lookout": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"]
    ],
    "Runner": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"]
    ],
    "Closer": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"],
        topic_name_to_id["Verified Vendors / Collabs"],
        topic_name_to_id["Testing Lab"]
    ],
    "Inner Circle": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"],
        topic_name_to_id["Verified Vendors / Collabs"],
        topic_name_to_id["Testing Lab"],
        topic_name_to_id["VIP Lounge"]
    ],
    "OG Member": [
        topic_name_to_id["Welcome To Scam's Plus - Start Here"],
        topic_name_to_id["General Chat"],
        topic_name_to_id["Scammers Warnings"],
        topic_name_to_id["Announcements"],
        topic_name_to_id["Con Academy"],
        topic_name_to_id["Questions"],
        topic_name_to_id["Tools & Bots"],
        topic_name_to_id["Verified Guides"],
        topic_name_to_id["Verified Vendors / Collabs"],
        topic_name_to_id["Testing Lab"],
        topic_name_to_id["VIP Lounge"]
    ]
}
# --- Environment Flags ---
IS_DEV_MODE = True  # Set to False in production