from playwright.sync_api import sync_playwright
import re, requests, json, os
from datetime import datetime, timezone, timedelta

TOKEN = '8933487275:AAENSpwpbWoGMfyhLbHXWoHmOsCNwLK1Xmk'
CHAT_ID = '2028252779'
DUBAI = timezone(timedelta(hours=4))
GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GH_REPO = 'ismail-onebullex/cryptopedia-bot'
SNAPSHOT_FILE = 'snapshot.json'
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
        page.wait_for_timeout(2000)
        left = page.inner_text('._sparbi_dataleft')
        right = page.inner_text('._sparbi_dataright')
        body = page.inner_text('body')
        sm = re.search(r'(\d+)\s*Subscribers', body)
        am = re.search(r'\$([\d,]+\.?\d*)', left)
        rm = re.search(r'([\d.]+)%', right)
        wm = re.search(r'Win Rate[^\d]*((?:[\d.]+))%', left)
        tm = re.search(r'Total Trades[^\d]*(\d[\d,]*)', left)
        vm = re.search(r'Trading Volume[^\d]*\$([\d.]+[MKBmkb]?)', left)
        return {
            'subs':   sm.group(1)     if sm else '-',
            'aum':    '$'+am.group(1) if am else '-',
            'roi':    rm.group(1)+'%' if rm else '-',
            'win':    wm.group(1)+'%' if wm else '-',
            'trades': tm.group(1)     if tm else '-',
            'vs':     '$'+vm.group(1) if vm else '-',
            'vn':     pv(vm.group(1)) if vm else 0
        }
    except Exception as e:
        print(f'Fetch error {bot["label"]}: {e}')
        return {'subs':'-','aum':'-','roi':'-','win':'-','trades':'-','vs':'-','vn':0}

def get_snapshot():
    try:
        r = requests.get(
            f'https://api.github.com/repos/{GH_REPO}/contents/{SNAPSHOT_FILE}',
            headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        )
        if r.status_code == 200:
            import base64
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            data = json.loads(content)
            data['_sha'] = r.json()['sha']
            return data
    except: pass
    return None

def save_snapshot(data, sha=None):
    try:
        content = json.dumps(data)
        import base64
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        body = {'message': 'Update snapshot', 'content': encoded}
        if sha: body['sha'] = sha
        requests.put(
            f'https://api.github.com/repos/{GH_REPO}/contents/{SNAPSHOT_FILE}',
            headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'},
            json=body
        )
    except Exception as e:
        print(f'Snapshot save error: {e}')

def send_telegram(msg):
    requests.post('https://api.telegram.org/bot'+TOKEN+'/sendMessage',
        json={'chat_id':CHAT_ID,'text':msg,'parse_mode':'HTML'}, timeout=10)

def is_morning_run():
    now = datetime.now(DUBAI)
    return True  # TEST

def send():
    now = datetime.now(DUBAI)
    now_str = now.strftime('%d.%m.%Y %H:%M') + ' (Dubai)'
    tV = tN = tK = tP = 0
    SEP = 'âââââââââââââ'
    msg = '\U0001f4ca <b>Cryptopedia Dashboard</b>\n\U0001f550 ' + now_str + '\n'
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
    send_telegram(msg)
    print(f'[{now_str}] Ana rapor gonderildi!')

    # Sadece 09:00 calismasinda gunluk degisim mesaji gonder
    if is_morning_run():
        snapshot = get_snapshot()
        current = {'komisyon': tK, 'profit_share': tP, 'toplam_gelir': tK+tP, 'net_pnl': tN, 'volume': tV}
        if snapshot:
            sha = snapshot.pop('_sha', None)
            dK = tK - snapshot.get('komisyon', tK)
            dP = tP - snapshot.get('profit_share', tP)
            dG = (tK+tP) - snapshot.get('toplam_gelir', tK+tP)
            dN = tN - snapshot.get('net_pnl', tN)
            dV = tV - snapshot.get('volume', tV)
            diff_msg = f'\U0001f4c8 <b>Gunluk Degisim (dun 09:00 vs bugun 09:00)</b>\n'
            diff_msg += f'\n\U0001f4ca Volume: {fd(dV)}'
            diff_msg += f'\n\u2705 Net PnL: {fd(dN)}'
            diff_msg += f'\n\U0001f7e1 Komisyon: {fd(dK)}'
            diff_msg += f'\n\U0001f7e3 Profit Share: {fd(dP)}'
            emoji = "\U0001f4c8" if dG >= 0 else "\U0001f4c9"
            diff_msg += f'\n{emoji} <b>Toplam Gelir Farki: {fd(dG)}</b>'
            send_telegram(diff_msg)
            print(f'[{now_str}] Gunluk degisim gonderildi!')
            save_snapshot(current, sha)
        else:
            save_snapshot(current)
            print(f'[{now_str}] Ilk snapshot kaydedildi.')

send()
