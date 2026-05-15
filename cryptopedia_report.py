from playwright.sync_api import sync_playwright
import re, requests
from datetime import datetime

TOKEN = '8933487275:AAENSpwpbWoGMfyhLbHXWoHmOsCNwLK1Xmk'
CHAT_ID = '2028252779'
BOTS = [
    {'url':'https://www.onebullex.com/spartan-bot/Cryptopedia-AI-PRO','pnl':4986.17,'fee':1893.13,'label':'Cryptopedia-AI-PRO'},
    {'url':'https://www.onebullex.com/spartan-bot/CryptopediaAI','pnl':13772.74,'fee':4556.36,'label':'CryptopediaAI'}
]

def fu(n):
    if n >= 1e6: return f'${n/1e6:.2f}M'
    return f'${n:,.2f}'

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
        # AUM elementinin yuklendigini bekle
        page.wait_for_selector('._sparbi_dataleft', timeout=15000)
        page.wait_for_timeout(2000)
        left = page.inner_text('._sparbi_dataleft')
        right = page.inner_text('._sparbi_dataright')
        body = page.inner_text('body')
        def g(p, txt):
            m = re.search(p, txt, re.DOTALL|re.IGNORECASE)
            return m.group(1) if m else '-'
        sm = re.search(r'(\d+)\s*Subscribers', body)
        am = re.search(r'\$([\d,]+\.?\d*)', left)
        rm = re.search(r'([\d.]+)%', right)
        wm = re.search(r'Win Rate[^\d]*((?:[\d.]+))%', left)
        tm = re.search(r'Total Trades[^\d]*(\d[\d,]*)', left)
        vm = re.search(r'Trading Volume[^\d]*\$([\d.]+[MKBmkb]?)', left)
        return {
            'subs':   sm.group(1)  if sm else '-',
            'aum':    '$'+am.group(1) if am else '-',
            'roi':    rm.group(1)+'%' if rm else '-',
            'win':    wm.group(1)+'%' if wm else '-',
            'trades': tm.group(1) if tm else '-',
            'vs':     '$'+vm.group(1) if vm else '-',
            'vn':     pv(vm.group(1)) if vm else 0
        }
    except Exception as e:
        print(f'Fetch error {bot["label"]}: {e}')
        return {'subs':'-','aum':'-','roi':'-','win':'-','trades':'-','vs':'-','vn':0}

def send():
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    tV = tN = tK = tP = 0
    SEP = '─────────────'
    msg = '\U0001f4ca <b>Cryptopedia Dashboard</b>\n\U0001f550 ' + now + '\n'
    icons = ['\U0001f536', '\U0001f535']
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for i, bot in enumerate(BOTS):
            d = fetch_bot(page, bot)
            np = bot['pnl'] - bot['fee']
            km = d['vn'] * 0.0005 * 0.6
            ps = np * 0.20
            tV += d['vn']; tN += np; tK += km; tP += ps
            msg += f'\n{SEP}'
            msg += f'\n{icons[i]} <b>{bot["label"]}</b>'
            msg += f'\n\U0001f4b0 AUM: {d["aum"]}  |  \U0001f4c8 ROI: {d["roi"]}'
            msg += f'\n\U0001f3c6 Win: {d["win"]}  |  \U0001f465 Subs: {d["subs"]}'
            msg += f'\n\U0001f4ca Volume: {d["vs"]}  |  \U0001f522 Islem: {d["trades"]}'
            msg += f'\n\u2705 Net PnL: {fu(np)}'
            msg += f'\n\U0001f7e1 Komisyon: {fu(km)}'
            msg += f'\n\U0001f7e3 Profit Share: {fu(ps)}'
            msg += f'\n\U0001f7e2 <b>Toplam Gelir: {fu(km+ps)}</b>'
        browser.close()
    msg += f'\n{SEP}'
    msg += f'\n\U0001f4e6 <b>GENEL TOPLAM</b>'
    msg += f'\n\U0001f4ca Volume: {fu(tV)}'
    msg += f'\n\u2705 Net PnL: {fu(tN)}'
    msg += f'\n\U0001f7e1 Komisyon: {fu(tK)}'
    msg += f'\n\U0001f7e3 Profit Share: {fu(tP)}'
    msg += f'\n\U0001f49a <b>Toplam Gelir: {fu(tK+tP)}</b>'
    requests.post('https://api.telegram.org/bot'+TOKEN+'/sendMessage',
        json={'chat_id':CHAT_ID,'text':msg,'parse_mode':'HTML'}, timeout=10)
    print(f'[{now}] Gonderildi!')

send()
