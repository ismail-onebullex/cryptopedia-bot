from playwright.sync_api import sync_playwright
import re, requests, json, os, base64
from datetime import datetime, timezone, timedelta


TOKEN      = '8882759241:AAFRwZJEYPy3OYTgRo1q0W-IVPK2LzIpp8I'
CHAT_IDS   = ['2028252779', '-5144582160']
DUBAI = timezone(timedelta(hours=4))
GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GH_REPO = 'ismail-onebullex/cryptopedia-bot'
GH_HEADERS = {'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
BOTS = [
    {
        'name': 'ArvenX-AI', 'label': 'ArvenX-AI',
        'url': 'https://www.onebullex.com/spartan-bot/ArvenX-AI',
        'emoji': 'âï¸', 'pnl': 1066.25, 'fee': 271.64,
    },
    {
        'name': 'PerzamAI', 'label': 'PerzamAI',
        'url': 'https://www.onebullex.com/spartan-bot/PerzamAI',
        'emoji': 'U0001f6e1ï¸', 'pnl': 0.0, 'fee': 0.0,
    },
]


def fu(n):
    if n >= 1e6: return f'${n/1e6:.2f}M'
    return f'${n:,.2f}'


def fd(n):
    sign = '+' if n >= 0 else ''
    if abs(n) >= 1e6: return f'{sign}${abs(n)/1e6:.2f}M'
    return f'{sign}${n:,.2f}'


def pv(s):
    if not s or s == '-': return 0
    s = s.replace('$','').replace(',','').strip()
    if s.endswith('M'): return float(s[:-1])*1e6
