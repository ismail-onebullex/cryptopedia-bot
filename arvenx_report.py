import requests
import re
import json
import os
from datetime import datetime
import pytz

TOKEN      = '8197716132:AAEni6HiCi-uuH1hDGnirET92bztXaa-Vn8'
CHAT_ID    = '2028252779'
DUBAI_TZ   = pytz.timezone('Asia/Dubai')
STATE_FILE = 'arvenx_prev_state.json'

BOTS = [
    {
        'name':      'ArvenX-AI',
        'label':     'ArvenX-AI',
        'url':       'https://www.onebullex.com/spartan-bot/ArvenX-AI',
        'emoji':     '⚔️',
        'total_pnl': 1066.25,
        'total_fee': 271.64,
    },
    {
        'name':      'PerzamAI',
        'label':     'PerzamAI',
        'url':       'https://www.onebullex.com/spartan-bot/PerzamAI',
        'emoji':     'U0001f6e1️',
        'total_pnl': 0.0,
        'total_fee': 0.0,
    },
]

def parse_vol(s):
    if not s:
        return 0.0
    s = s.replace('$', '').replace(',', '').strip()
    if s.upper().endswith('M'):
        return float(s[:-1]) * 1_000_000
    if s.upper().endswith('K'):
        return float(s[:-1]) * 1_000
    if s.upper().endswith('B'):
        return float(s[:-1]) * 1_000_000_000
    try:
        return float(s)
    except Exception:
        return 0.0

def fmt_usd(n):
    if abs(n) >= 1_000_000:
        return f'${n/1_000_000:.2f}M'
    return f'${n:,.2f}'

def send_telegram(msg):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    resp = requests.post(url, json={
        'chat_id': CHAT_ID,
        'text': msg,
        'parse_mode': 'HTML'
    }, timeout=10)
    return resp

def fetch_bot(bot):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    r = requests.get(bot['url'], headers=headers, timeout=15)
    t = r.text
    subs_m   = re.search(r'(\d[\d,]*)\s*Subscribers', t)
    aum_m    = re.search(r'AUM\s*\(USDT\)\s*\$([\d,]+\.?\d*)', t)
    roi_m    = re.search(r'30d ROI\s*\(%\)\s*([\d.]+)%', t)
    win_m    = re.search(r'Win Rate\s*\(%\)\s*([\d.]+)%', t)
    trades_m = re.search(r'Total Trades\s*([\d,]+)', t)
    vol_m    = re.search(r'Trading Volume\s*\$([\d.]+[MKBmkb]?)', t)
    subs   = subs_m.group(1)   if subs_m   else '--'
    aum    = aum_m.group(1)    if aum_m    else '0'
    roi    = roi_m.group(1)    if roi_m    else '0'
    win    = win_m.group(1)    if win_m    else '0'
    trades = trades_m.group(1) if trades_m else '0'
    vol_s  = vol_m.group(1)    if vol_m    else '0'
    vol_n  = parse_vol(vol_s)
    return {'subs': subs, 'aum': aum, 'roi': roi, 'win': win, 'trades': trades, 'vol_s': vol_s, 'vol_n': vol_n}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def send_report():
    now = datetime.now(DUBAI_TZ)
    SEP = '━' * 20
    lines = [
        '<b>⚔️ ARVENX &amp; PERZAM RAPORU</b>',
        f'⏰ {now.strftime("%d.%m.%Y %H:%M")} (Dubai)',
        SEP,
    ]
    total_vol = total_np = total_km = total_ps = 0.0
    for bot in BOTS:
        try:
            d = fetch_bot(bot)
        except Exception as e:
            lines.append(f'{bot["emoji"]} <b>{bot["label"]}</b>: Veri alinamadi ({e})')
            continue
        net_pnl  = bot['total_pnl'] - bot['total_fee']
        komisyon = d['vol_n'] * 0.0005 * 0.6
        pay      = net_pnl * 0.20
        toplam   = komisyon + pay
        total_vol += d['vol_n']; total_np += net_pnl; total_km += komisyon; total_ps += pay
        lines += [
            f'{bot["emoji"]} <b>{bot["label"]}</b>',
            f'   U0001f465 Subs: {d["subs"]}',
            f'   U0001f4b0 AUM: ${d["aum"]}',
            f'   U0001f4ca Hacim: ${d["vol_s"]}',
            f'   U0001f4c8 30d ROI: {d["roi"]}%',
            f'   U0001f3af Win Rate: {d["win"]}%',
            f'   U0001f504 Trades: {d["trades"]}',
            '   ' + '─'*17,
            f'   U0001f4b5 PnL: {fmt_usd(bot["total_pnl"])}',
            f'   U0001f4b8 Fee: -{fmt_usd(bot["total_fee"])}',
            f'   ✅ Net PnL: {fmt_usd(net_pnl)}',
            f'   U0001f3e6 Komisyon: {fmt_usd(komisyon)}',
            f'   U0001f48e Pay (%20): {fmt_usd(pay)}',
            f'   ⭐ TOPLAM: {fmt_usd(toplam)}',
            SEP,
        ]
    lines += [
        '<b>U0001f4ca GENEL TOPLAM</b>',
        f'   U0001f4e6 Toplam Hacim: {fmt_usd(total_vol)}',
        f'   ✅ Toplam Net PnL: {fmt_usd(total_np)}',
        f'   U0001f3e6 Toplam Komisyon: {fmt_usd(total_km)}',
        f'   U0001f48e Toplam Pay: {fmt_usd(total_ps)}',
        f'   ⭐ GENEL TOPLAM: {fmt_usd(total_km + total_ps)}',
    ]
    send_telegram('\n'.join(lines))
    print(f'[{now}] Rapor gonderildi.')

def send_daily_change():
    now = datetime.now(DUBAI_TZ)
    state = load_state()
    SEP = '━' * 20
    lines = [
        '<b>U0001f305 GUNLUK DEGISIM RAPORU</b>',
        f'U0001f4c5 {now.strftime("%d.%m.%Y")} (Dubai)',
        SEP,
    ]
    new_state = {}
    for bot in BOTS:
        try:
            d = fetch_bot(bot)
        except Exception:
            lines.append(f'{bot["emoji"]} <b>{bot["label"]}</b>: Veri alinamadi')
            continue
        key = bot['name']
        prev = state.get(key, {})
        vol_n = d['vol_n']
        net_pnl  = bot['total_pnl'] - bot['total_fee']
        komisyon = vol_n * 0.0005 * 0.6
        pay      = net_pnl * 0.20
        toplam   = komisyon + pay
        prev_vol  = prev.get('vol_n', vol_n)
        prev_km   = prev.get('komisyon', komisyon)
        prev_ps   = prev.get('pay', pay)
        prev_top  = prev.get('toplam', toplam)
        prev_subs = prev.get('subs', d['subs'])
        def chg(v): return f'(+{fmt_usd(v)})' if v >= 0 else f'({fmt_usd(v)})'
        lines += [
            f'{bot["emoji"]} <b>{bot["label"]}</b>',
            f'   U0001f465 Subs: {d["subs"]} (dun: {prev_subs})',
            f'   U0001f4ca Hacim: ${d["vol_s"]} {chg(vol_n - prev_vol)}',
            f'   U0001f3e6 Komisyon: {fmt_usd(komisyon)} {chg(komisyon - prev_km)}',
            f'   U0001f48e Pay: {fmt_usd(pay)} {chg(pay - prev_ps)}',
            f'   ⭐ Toplam: {fmt_usd(toplam)} {chg(toplam - prev_top)}',
            SEP,
        ]
        new_state[key] = {'vol_n': vol_n, 'komisyon': komisyon, 'pay': pay, 'toplam': toplam, 'subs': d['subs']}
    save_state(new_state)
    send_telegram('\n'.join(lines))
    print(f'[{now}] Gunluk degisim gonderildi.')

if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'report'
    if mode == 'daily':
        send_daily_change()
    else:
        send_report()
