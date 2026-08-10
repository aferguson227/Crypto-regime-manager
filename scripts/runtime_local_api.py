#!/usr/bin/env python3
"""Read-only local runtime API plus My Bots registry control.

No trading/order endpoint exists. The only write action is portfolio UI membership
(add/remove a strategy from My Bots).
"""
from __future__ import annotations
import json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from scripts.runtime_state_manager import state_dir
from scripts.managed_bot_registry import current,add,remove,seed

HOST='127.0.0.1';PORT=8765
FILES={
 '/api/live-service':'kucoin_live_service_status.json',
 '/api/paper':'paper_portfolio.json',
 '/api/managed-portfolio':'managed_bot_portfolio.json',
 '/api/live-portfolio':'live_portfolio_truth.json',
 '/api/live-prices':'kucoin_live_prices.json',
}
def load_state(name):
 p=state_dir()/name
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except:return {}
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*_):return
 def headers(self,code=200):
  self.send_response(code)
  self.send_header('Content-Type','application/json; charset=utf-8')
  self.send_header('Cache-Control','no-store')
  self.send_header('Access-Control-Allow-Origin','*')
  self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
  self.send_header('Access-Control-Allow-Headers','Content-Type')
  self.send_header('Access-Control-Allow-Private-Network','true')
  self.end_headers()
 def sendj(self,d,code=200):
  self.headers(code);self.wfile.write(json.dumps(d).encode('utf-8'))
 def do_OPTIONS(self):self.headers(204)
 def do_GET(self):
  if self.path.startswith('/api/runtime'):
   self.sendj({'live_service':load_state('kucoin_live_service_status.json'),
               'paper':load_state('paper_portfolio.json'),
               'managed':load_state('managed_bot_portfolio.json'),
               'registry':seed()});return
  if self.path.startswith('/api/registry'):self.sendj(seed());return
  path=self.path.split('?',1)[0]
  if path in FILES:self.sendj(load_state(FILES[path]));return
  self.sendj({'error':'not_found'},404)
 def do_POST(self):
  if self.path.split('?',1)[0]!='/api/registry':self.sendj({'error':'write_not_supported'},405);return
  try:
   n=int(self.headers.get('Content-Length') or 0);body=json.loads(self.rfile.read(n) or b'{}')
   action=str(body.get('action') or '').lower();asset=body.get('asset')
   if action=='add' and asset:self.sendj(add(asset));return
   if action=='remove' and asset:self.sendj(remove(asset));return
   self.sendj({'error':'expected action add/remove and asset'},400)
  except Exception as exc:self.sendj({'error':f'{type(exc).__name__}: {exc}'},500)
def start_background(host=HOST,port=PORT):
 try:
  server=ThreadingHTTPServer((host,port),Handler)
 except OSError:
  return None
 t=threading.Thread(target=server.serve_forever,name='crm-runtime-local-api',daemon=True);t.start()
 return server
