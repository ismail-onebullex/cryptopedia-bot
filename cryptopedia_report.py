from playwright.sync_api import sync_playwright
import re, requests, json, os, base64
from datetime import datetime, timezone, timedelta


TOKEN = '8511016923:AAHeCvKLEX3wqNmMxtQjJBFZYET4mGoThLw'
CHAT_ID = '2028252779'
DUBAI = timezone(timedelta(hours=4))
GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GH_REPO = 'ismail-onebullex/cryptopedia-bot'
GH_HEADERS = {'Authorization': f'token {GH_TOKEN}', 'ccept': 'application/vnd.github.v3+json'}
BOTS = [
    {'url':'https://www.onebullex.com/spartan-bot/Cryptopedia-AI-PRO','pnl':4986.17,'fee':1893.13,'label':'Cryptopedia-AI-PRO'},
    {'url':'https://www.onebullex.com/spartan-bot/CryptopediaAI','pnl':13772.74,'fee':4556.36,'label':'CryptopediaAI'}
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
    if s.endswith('K'): return float(s[:-1])*1e3
    try: return float(s)
    except: return 0


def fetch_bot(page, bot):
    try:
        page.goto(bot['url'], timeout=60000)
        page.wait_for_selector('._sparbi_dataleft', timeout=15000)
