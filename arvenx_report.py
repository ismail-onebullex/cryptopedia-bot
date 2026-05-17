from playwright.sync_api import sync_playwright
import re, requests, json, os, base64
from datetime import datetime, timezone, timedelta

TOKEN      = '8197716132:AAEni6HiCi-uuH1hDGnirET92bztXaa-Vn8'
CHAT_ID    = '-5144582160'
DUBAI = timezone(timedelta(hours=4))
GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GH_REPO = 'ismail-onebullex/cryptopedia-bot'
GH_HEADERS = {'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
BOTS = [
    {
        'name': 'ArvenX-AI', 'label': 'ArvenX-AI',
        'url': 'https://www.onebullex.com/spartan-bot/ArvenX-AI',
        'emoji': '⚔️', 'pnl': 1066.25, 'fee': 271.64,
    },
    {
        'name': 'PerzamAI', 'label': 'PerzamAI',
        'url': 'https://www.onebullex.com/spartan-bot/PerzamAI',
        'emoji': 'U0001f6e1️', 'pnl': 0.0, 'fee': 0.0,
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

def gh_get(path):
    try:
        r = requests.get(f'https://api.github.com/repos/{GH_REPO}/contents/{path}', headers=GH_HEADERS)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def gh_put(path, content, msg, sha=None):
    try:
        body = {'message': msg, 'content': base64.b64encode(content.encode()).decode()}
        if sha: body['sha'] = sha
        requests.put(f'https://api.github.com/repos/{GH_REPO}/contents/{path}', headers=GH_HEADERS, json=body)
    except Exception as e:
        print(f'gh_put error: {e}')

def keep_alive():
    try:
        now = datetime.now(DUBAI).strftime('%d.%m.%Y %H:%M')
        f = gh_get('last_run.txt')
        sha = f['sha'] if f else None
        gh_put('last_run.txt', f'Last run: {now} Dubai', 'keep-alive', sha)
    except: pass

def send_tg(msg):
    requests.post('https://api.telegram.org/bot'+TOKEN+'/sendMessage',
        json={'chat_id':CHAT_ID,'text':msg,'parse_mode':'HTML'}, timeout=10)

def send():
    now = datetime.now(DUBAI)
    now_str = now.strftime('%d.%m.%Y %H:%M') + ' (Dubai)'
    today = now.strftime('%d.%m.%Y')
    tV = tN = tK = tP = tS = 0
    SEP = '-------------'
    msg = '\U0001f4ca <b>ARVENX & PERZAM Dashboard</b>\n\U0001f550 ' + now_str + '\n'
    icons = ['\U0001f536', '\U0001f535']
    bots_data = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for i, bot in enumerate(BOTS):
            d = fetch_bot(page, bot)
            np = bot['pnl'] - bot['fee']
            km = d['vn'] * 0.0005 * 0.6
            ps = np * 0.20
            tV += d['vn']; tN += np; tK += km; tP += ps
            bots_data.append({**d, 'label': bot['label'], 'pnl': bot['pnl'], 'fee': bot['fee'],
                               'net_pnl': np, 'komisyon': km, 'profit_share': ps, 'toplam_gelir': km+ps})
            msg += f'\n{SEP}\n{icons[i]} <b>{bot["label"]}</b>'
            msg += f'\n\U0001f4b0 AUM: {d["aum"]}  |  \U0001f4c8 ROI: {d["roi"]}'
            msg += f'\n\U0001f3c6 Win: {d["win"]}  |  \U0001f465 Subs: {d["subs"]}'
            msg += f'\n\U0001f4ca Volume: {d["vs"]}  |  \U0001f522 Islem: {d["trades"]}'
            msg += f'\n\u2705 Net PnL: {fu(np)}'
            msg += f'\n\U0001f7e1 Komisyon: {fu(km)}'
            msg += f'\n\U0001f7e3 Profit Share: {fu(ps)}'
            msg += f'\n\U0001f7e2 <b>Toplam Gelir: {fu(km+ps)}</b>'
        browser.close()
    msg += f'\n{SEP}\n\U0001f4e6 <b>GENEL TOPLAM</b>'
    msg += f'\n\U0001f4ca Volume: {fu(tV)}'
    msg += f'\n\u2705 Net PnL: {fu(tN)}'
    msg += f'\n\U0001f7e1 Komisyon: {fu(tK)}'
    msg += f'\n\U0001f7e3 Profit Share: {fu(tP)}'
    msg += f'\n\U0001f49a <b>Toplam Gelir: {fu(tK+tP)}</b>'
    send_tg(msg)
    print(f'[{now_str}] Rapor gonderildi!')

    # data.json kaydet (Mini App icin)
    data_file = gh_get('data.json')
    data = {'updated': now_str, 'bots': bots_data,
            'total': {'volume': tV, 'net_pnl': tN, 'komisyon': tK, 'profit_share': tP, 'toplam_gelir': tK+tP}}
    gh_put('data.json', json.dumps(data, ensure_ascii=False), 'Update data.json', data_file['sha'] if data_file else None)

    # Keep-alive commit
    keep_alive()

    # Gunluk degisim - snapshot bugune ait degilse gonder
    snap_file = gh_get('snapshot.json')
    current = {'date': today, 'komisyon': tK, 'profit_share': tP, 'toplam_gelir': tK+tP, 'net_pnl': tN, 'volume': tV, 'subs': tS}
    if snap_file:
        prev = json.loads(base64.b64decode(snap_file['content']).decode())
        snap_date = prev.get('date', '')
        if snap_date != today:
            # Bugun ilk calisma - degisim hesapla ve gonder
            dK = tK - prev.get('komisyon', tK)
            dP = tP - prev.get('profit_share', tP)
            dG = (tK+tP) - prev.get('toplam_gelir', tK+tP)
            dN = tN - prev.get('net_pnl', tN)
            dV = tV - prev.get('volume', tV)
            dS = tS - prev.get('subs', tS)
            snap_date_str = prev.get('date', '?')
            diff = f'\U0001f4c8 <b>Gunluk Degisim</b>\n'
            diff += f'\U0001f4c5 {snap_date_str} \u2192 {today}\n'
            diff += f'\n\U0001f465 Subs: {dS:+d} ({prev.get("subs", tS)} → {tS})'
            diff += f'\n\U0001f4ca Volume: {fd(dV)}'
            diff += f'\n\u2705 Net PnL: {fd(dN)}'
            diff += f'\n\U0001f7e1 Komisyon: {fd(dK)}'
            diff += f'\n\U0001f7e3 Profit Share: {fd(dP)}'
            emoji = '\U0001f4c8' if dG >= 0 else '\U0001f4c9'
            diff += f'\n{emoji} <b>Toplam Gelir Farki: {fd(dG)}</b>'
            send_tg(diff)
            print(f'[{now_str}] Gunluk degisim gonderildi! ({snap_date} -> {today})')
            # Snapshot'i guncelle
            gh_put('snapshot.json', json.dumps(current), 'Update snapshot', snap_file['sha'])
        else:
            print(f'[{now_str}] Bugun zaten snapshot var ({snap_date}), degisim gonderilmedi.')
    else:
        # Ilk kez - snapshot olustur
        gh_put('snapshot.json', json.dumps(current), 'Init snapshot')
        print(f'[{now_str}] Ilk snapshot kaydedildi.')

send()
