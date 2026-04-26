# ==============================================
# phase6_networking.py
# Generates warmth-calibrated LinkedIn and email
# outreach messages for professional networking.
#
# Reads contact data from contact_pipeline.xlsx.
# Writes stage advances back on interactive confirm.
# No automated sending — output is terminal only.
#
# Usage:
#   python -m scripts.phase6_networking \
#     --contact "Jane Smith" --stage 1
#   python -m scripts.phase6_networking \
#     --contact "Jane Smith" --stage 2 --role acme-systems-se
#   python -m scripts.phase6_networking --list
# ==============================================

import os
import sys
import argparse
from datetime import date
from anthropic import Anthropic
from dotenv import load_dotenv
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii
from scripts.utils import candidate_config
from scripts.config import CONTACTS_TRACKER_PATH, MODEL_SONNET as MODEL

load_dotenv()

# ==============================================
# SYSTEM PROMPT
# ==============================================

SYSTEM_PROMPT = """You are an expert career coach writing professional networking messages \
for senior defense and systems engineering professionals. Your messages are specific, \
genuine, and appropriately brief.

You always:
- Use en dashes, never em dashes
- Write specific over generic
- Match the directness of the message to the warmth of the relationship
- Keep connection requests within their character limits

You never:
- Use hollow openers like "I came across your profile" or "Hope this message finds you well"
- Invent or guess shared history not explicitly provided
- Reference a specific role unless one is provided
- Use filler phrases or overly formal language"""
