import http.server
import urllib.request
import json
import time as time_mod
from datetime import datetime, timezone, timedelta, time as dt_time

PORT = 8899
CODES = ['gb_inx','gb_dji','gb_ixic','gb_aapl','gb_msft','gb_googl','gb_amzn','gb_nvda','gb_meta','gb_tsla',
         'gb_smh','gb_soxx','gb_arkk','gb_gld','gb_xlk','gb_xli','gb_qqq','gb_xlb','gb_xly','gb_xlre',
         'gb_tlt','gb_slv','gb_xlf','gb_xlp','gb_xlv','gb_xlu','gb_xle','gb_ibit',
         'gb_arm','gb_intc','gb_mu','gb_asml','gb_cohr','gb_lite',
         'gb_wdc','gb_stx','gb_sndk',
         'gb_nbis','gb_crwv','gb_eqix','gb_be','gb_pltr']
NM = {'inx':'标普500','dji':'道琼斯','ixic':'纳斯达克综合','aapl':'苹果','msft':'微软','googl':'谷歌','amzn':'亚马逊',
      'nvda':'英伟达','meta':'Meta','tsla':'特斯拉','smh':'半导体SMH','soxx':'半导体SOXX','arkk':'ARK创新',
      'gld':'黄金GLD','xlk':'科技XLK','xli':'工业XLI','qqq':'纳指QQQ','xlb':'材料XLB','xly':'可选消费XLY',
      'xlre':'房地产XLRE','tlt':'长期国债TLT','slv':'白银SLV','xlf':'金融XLY','xlp':'必需消费XLP',
      'xlv':'医疗XLV','xlu':'公用事业XLU','xle':'能源XLE','ibit':'比特币IBIT','arm':'Arm','intc':'英特尔',
      'mu':'美光','asml':'阿斯麦','cohr':'Coherent','lite':'Lumentum','wdc':'西部数据','stx':'希捷',
      'sndk':'SanDisk','nbis':'Nebius','crwv':'CoreWeave','eqix':'易昆尼克斯','be':'Bloom Energy','pltr':'Palantir'}
cache = {"data": None, "time": 0}

def market_status():
    n = datetime.now(timezone(timedelta(hours=-4)))
    if n.weekday() >= 5: return "周末休市", 300
    t = n.time()
    if t < dt_time(9, 30): return "盘前", 300
    if t <= dt_time(16, 0): return "交易中", 60
    return "已收盘", 300

def fetch():
    now = time_mod.time()
    if cache["data"] and now - cache["time"] < 30:
        return cache["data"]
    url = "https://hq.sinajs.cn/list=" + ",".join(CODES)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn"
    })
    try:
        raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk")
    except Exception as e:
        if cache["data"]: return cache["data"]
        return {"status": "error", "msg": str(e)}
    d = {"status": "ok", "data": {}}
    for line in raw.strip().split("\n"):
        if "hq_str_gb_" not in line: continue
        try:
            code = line.split("hq_str_gb_")[1].split("=")[0]
            f = line.split('="')[1].rstrip('";').split(",")
            d["data"][code] = {"price": float(f[1]) or 0, "pct": float(f[2]) or 0,
                               "change": float(f[4]) or 0, "prevClose": float(f[5]) or 0}
            d["data"][code]["name"] = NM.get(code, f[0])
        except: pass
    d["count"] = len(d["data"])
    ms, rs = market_status()
    d["market_status"] = ms
    d["refresh_seconds"] = rs
    cache["data"] = d
    cache["time"] = now
    return d

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/stocks":
            d = fetch()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(d, ensure_ascii=False).encode())
        elif self.path == "/api/config":
            ms, rs = market_status()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"refresh_seconds": rs, "market_status": ms, "trading_hours": ms == "交易中"}).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                with open("index.html", "rb") as f:
                    self.wfile.write(f.read())
            except:
                self.wfile.write(b"<h1>美股看板</h1><p>服务运行中</p>")
    def log_message(self, *a): pass

print(f"🦞 美股看板 http://0.0.0.0:{PORT}")
http.server.HTTPServer(("0.0.0.0", PORT), H).serve_forever()
