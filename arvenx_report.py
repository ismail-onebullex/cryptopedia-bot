import requests
import re
import json
import os
from datetime import datetime, timedelta
import pytz

# ─── AYARLAR ───────────────────────────────────────────────
TOKEN      = '8197716132:AAEni6HiCi-uuH1hDGnirET92bztXaa-Vn8'
CHAT_ID    = '2028252779'
DUBAI_TZ   = pytz.timezone('Asia/Dubai')
STATE_FILE = 'arvenx_prev_state.json'

BOTS = [
    {
        'name':    'ArvenX-AI',
        'label':   'ArvenX-AI',
        'url':     'https://www.onebullex.com/spartan-bot/ArvenX-AI',
        'emoji':   '⚔️',
        'total_pnl': 1066.25,
        'total_fee': 271.64,
    },
    {
        'name':    'PerzamAI',
        'label':   'PerzamAI',
        'url':     'https://www.onebullex.com/spartan-bot/PerzamAI',
        'emoji':   '🛡️',
        'total_pnl': 0.0,
        'total_fee': 0.0,
    },
]

# ─── YARDIMCI FONKSİYONLAR ─────────────────────────────────
def parse_vol(s):
    if not s:
        return 0.0
    s = s.replace('$', '').replace(',', '').strip()
    if s.endswith('M'):
        return float(s[:-1]) * 1_000_000
    if s.endswith('K'):
        return float(s[:-1]) * 1_000
    if s.endswith('B'):
        return float(s[:-1]) * 1_000_000_000
    try:
        return float(s)
    except:
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(bot['url'], headers=headers, timeout=15)
    t = r.text

    subs_m   = re.search(r'([d,]+)s*Subscribers', t)
    aum_m    = re.search(r'AUM.*?$([d,]+.?d*)', t, re.DOTALL)
    roi_m    = re.search(r'30d ROI.*?([d.]+)%', t, re.DOTALL)
    win_m    = re.search(r'Win Rate.*?([d.]+)%', t, re.DOTALL)
    trades_m = re.search(r'Total Trades.*?([d,]+)', t, re.DOTALL)
    vol_m    = re.search(r'Trading Volume.*?$([d.]+[MKBmkb]?)', t, re.DOTALL)

    subs   = subs_m.group(1)   if subs_m   else '--'
    aum    = aum_m.group(1)    if aum_m    else '0'
    roi    = roi_m.group(1)    if roi_m    else '0'
    win    = win_m.group(1)    if win_m    else '0'
    trades = trades_m.group(1) if trades_m else '0'
    vol_s  = vol_m.group(1)    if vol_m    else '0'
    vol_n  = parse_vol(vol_s)

    return {
        'subs':   subs,
        'aum':    aum,
        'roi':    roi,
        'win':    win,
        'trades': trades,
        'vol_s':  vol_s,
        'vol_n':  vol_n,
    }

# ─── DURUM KAYDET / YÜKLe ──────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

# ─── 3 SAATLİK RAPOR ───────────────────────────────────────
def send_report():
    now = datetime.now(DUBAI_TZ)
    lines = []
    lines.append(f'<b>⚔️ ARVENX &amp; PERZAM RAPORU</b>')
    lines.append(f'🕐 {now.strftime("%d.%m.%Y %H:%M")} (Dubai)')
    lines.append('━━━━━━━━━━━━━━━━━━━━')

    total_vol = 0.0
    total_np  = 0.0
    total_km  = 0.0
    total_ps  = 0.0

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

        total_vol += d['vol_n']
        total_np  += net_pnl
        total_km  += komisyon
        total_ps  += pay

        lines.append(f'{bot["emoji"]} <b>{bot["label"]}</b>')
        lines.append(f'   👥 Subs: {d["subs"]}')
        lines.append(f'   💰 AUM: ${d["aum"]}')
        lines.append(f'   📊 Hacim: ${d["vol_s"]}')
        lines.append(f'   📈 30d ROI: {d["roi"]}%')
        lines.append(f'   🎯 Win Rate: {d["win"]}%')
        lines.append(f'   🔄 Trades: {d["trades"]}')
        lines.append(f'   ─────────────────')
        lines.append(f'   💵 PnL: {fmt_usd(bot["total_pnl"])}')
        lines.append(f'   💸 Fee: -{fmt_usd(bot["total_fee"])}')
        lines.append(f'   ✅ Net PnL: {fmt_usd(net_pnl)}')
        lines.append(f'   🏦 Komisyon: {fmt_usd(komisyon)}')
        lines.append(f'   💎 Pay (%20): {fmt_usd(pay)}')
        lines.append(f'   🌟 TOPLAM: {fmt_usd(toplam)}')
        lines.append('━━━━━━━━━━━━━━━━━━━━')

    # Genel toplam
    lines.append(f'<b>📊 GENEL TOPLAM</b>')
    lines.append(f'   📦 Toplam Hacim: {fmt_usd(total_vol)}')
    lines.append(f'   ✅ Toplam Net PnL: {fmt_usd(total_np)}')
    lines.append(f'   🏦 Toplam Komisyon: {fmt_usd(total_km)}')
    lines.append(f'   💎 Toplam Pay: {fmt_usd(total_ps)}')
    lines.append(f'   🌟 GENEL TOPLAM: {fmt_usd(total_km + total_ps)}')

    send_telegram('\n'.join(lines))
    print(f'[{now}] Rapor gonderildi.')

# ─── 00:00 GÜNLÜK DEĞİŞİM ─────────────────────────────────
def send_daily_change():
    now   = datetime.now(DUBAI_TZ)
    state = load_state()
    lines = []
    lines.append(f'<b>🌅 GÜNLÜK DEĞİŞİM RAPORU</b>')
    lines.append(f'📅 {now.strftime("%d.%m.%Y")} (Dubai)')
    lines.append('━━━━━━━━━━━━━━━━━━━━')

    new_state = {}

    for bot in BOTS:
        try:
            d = fetch_bot(bot)
        except Exception as e:
            lines.append(f'{bot["emoji"]} <b>{bot["label"]}</b>: Veri alinamadi')
            continue

        key       = bot['name']
        prev      = state.get(key, {})
        vol_n     = d['vol_n']
        net_pnl   = bot['total_pnl'] - bot['total_fee']
        komisyon  = vol_n * 0.0005 * 0.6
        pay       = net_pnl * 0.20
        toplam    = komisyon + pay

        prev_vol  = prev.get('vol_n', vol_n)
        prev_km   = prev.get('komisyon', komisyon)
        prev_ps   = prev.get('pay', pay)
        prev_top  = prev.get('toplam', toplam)
        prev_subs = prev.get('subs', d['subs'])

        d_vol  = vol_n - prev_vol
        d_km   = komisyon - prev_km
        d_ps   = pay - prev_ps
        d_top  = toplam - prev_top

        def chg(v):
            return f'(+{fmt_usd(v)})' if v >= 0 else f'({fmt_usd(v)})'

        lines.append(f'{bot["emoji"]} <b>{bot["label"]}</b>')
        lines.append(f'   👥 Subs: {d["subs"]} (dün: {prev_subs})')
        lines.append(f'   📊 Hacim: ${d["vol_s"]} {chg(d_vol)}')
        lines.append(f'   🏦 Komisyon: {fmt_usd(komisyon)} {chg(d_km)}')
        lines.append(f'   💎 Pay: {fmt_usd(pay)} {chg(d_ps)}')
        lines.append(f'   🌟 Toplam: {fmt_usd(toplam)} {chg(d_top)}')
        lines.append('━━━━━━━━━━━━━━━━━━━━')

        new_state[key] = {
            'vol_n':    vol_n,
            'komisyon': komisyon,
            'pay':      pay,
            'toplam':   toplam,
            'subs':     d['subs'],
        }

    save_state(new_state)
    send_telegram('\n'.join(lines))
    print(f'[{now}] Gunluk degisim gonderildi.')

# ─── MAIN ──────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'report'
    if mode == 'daily':
        send_daily_change()
    else:
        send_report()
