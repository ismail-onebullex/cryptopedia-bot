#!/usr/bin/env python3
import requests, re
from datetime import datetime

TOKEN = '8933487275:AAENSpwpbWoGMfyhLbHXWoHmOsCNwLK1Xmk'
CHAT_ID = '2028252779'
BOTS = [
    {'url':'https://www.onebullex.com/spartan-bot/Cryptopedia-AI-PRO','pnl':4986.17,'fee':1893.13,'label':'Cryptopedia-AI-PRO'},
    {'url':'https://www.onebullex.com/spartan-bot/CryptopediaAI','pnl':13772.74,'fee':4556.36,'label':'CryptopediaAI'}
]

def pv(s):
    if not s: return 0
    s = s.replace('$','').replace(',','').strip()
    if s.endswith('M'): return float(s[:-1]) * 1e6
    if s.endswith('K'): return float(s[:-1]) * 1e3
    try: return float(s)
    except: return 0

def fu(n):
    if n >= 1e6: return '$' + '{:.2f}'.format(n/1e6) + 'M'
    return '$' + '{:,.2f}'.format(n)

def fetch(bot):
    try:
        t = requests.get(bot['url'], headers={'User-Agent':'Mozilla/5.0'}, timeout=15).text
        def g(p): m = re.search(p, t, re.DOTALL|re.IGNORECASE); return m.group(1) if m else '-'
        vn = pv(g(r'Trading Volume.{1,20}\$([d.]+[MKBmkb]?)'))
        return {
            'subs': g(r'(\d+)\s*Subscribers'),
            'aum': '$' + g(r'AUM .USDT..{1,30}\$([d,]+\.?\d*)'),
            'roi': g(r'30d ROI.{1,40}([d.]+)%') + '%',
            'win': g(r'Win Rate.{1,40}([d.]+)%') + '%',
            'trades': g(r'Total Trades.{1,15}([d,]+)'),
            'vs': '$' + g(r'Trading Volume.{1,20}\$([d.]+[MKBmkb]?)'),
            'vn': vn
        }
    except:
        return {'subs':'-','aum':'-','roi':'-','win':'-','trades':'-','vs':'-','vn':0}

def send():
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    tV = tN = tK = tP = 0
    msg = '\U0001f4ca <b>Cryptopedia Dashboard</b>\n\U0001f550 ' + now + '\n'
    icons = ['\U0001f536', '\U0001f535']
    for i, bot in enumerate(BOTS):
        d = fetch(bot)
        np = bot['pnl'] - bot['fee']
        km = d['vn'] * 0.0005 * 0.6
        ps = np * 0.20
        tV += d['vn']; tN += np; tK += km; tP += ps
        msg += '\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501'
        msg += '\n' + icons[i] + ' <b>' + bot['label'] + '</b>'
        msg += '\n\U0001f4b0 AUM: ' + d['aum'] + '  |  \U0001f4c8 ROI: ' + d['roi']
        msg += '\n\U0001f3c6 Win: ' + d['win'] + '  |  \U0001f465 Subs: ' + d['subs']
        msg += '\n\U0001f4ca Volume: ' + d['vs'] + '  |  \U0001f522 Islem: ' + d['trades']
        msg += '\n\u2705 Net PnL: ' + fu(np)
        msg += '\n\U0001f7e1 Komisyon: ' + fu(km)
        msg += '\n\U0001f7e3 Profit Share: ' + fu(ps)
        msg += '\n\U0001f7e2 <b>Toplam Gelir: ' + fu(km+ps) + '</b>'
    msg += '\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501'
    msg += '\n\U0001f4e6 <b>GENEL TOPLAM</b>'
    msg += '\n\U0001f4ca Volume: ' + fu(tV)
    msg += '\n\u2705 Net PnL: ' + fu(tN)
    msg += '\n\U0001f7e1 Komisyon: ' + fu(tK)
    msg += '\n\U0001f7e3 Profit Share: ' + fu(tP)
    msg += '\n\U0001f49a <b>Toplam Gelir: ' + fu(tK+tP) + '</b>'
    requests.post(
        'https://api.telegram.org/bot' + TOKEN + '/sendMessage',
        json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'},
        timeout=10
    )
    print('[' + now + '] Gonderildi!')

send()
