import json
import os
import time

import requests
from dotenv import dotenv_values

BASE = dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"].rstrip("/")
tok = requests.post(f"{BASE}/api/auth/login",
                    json={"email": "owner@pizzapalace.pk", "password": "palace123"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
PHONE = os.environ.get("PHONE", "923001234599")

steps = ["menu dikhao", "1 zinger burger aur fries", "haan coke", "delivery",
         "House 5, DHA Phase 6 Lahore", "yes", "haan confirm", "ji bilkul order place kar do"]

for s in steps:
    t0 = time.time()
    r = requests.post(f"{BASE}/api/simulator/message",
                      json={"phone": PHONE, "name": "QA Ali", "text": s}, headers=H, timeout=180)
    d = r.json()
    outs = [m["text"] for m in d["messages"] if m["direction"] == "out"]
    conv = d.get("conversation") or {}
    print("=" * 70)
    print(f">>> USER: {s}   ({r.status_code}, {time.time()-t0:.1f}s)")
    print(f"<<< AI: {outs[-1] if outs else '(none)'}")
    print(f"[state={conv.get('state')} order_type={conv.get('order_type')} "
          f"addr={conv.get('address')} cart={json.dumps(conv.get('cart'))} order_id={conv.get('order_id')}]")
    orders = requests.get(f"{BASE}/api/orders", headers=H).json()
    mine = [o for o in orders if o["customer_phone"] == PHONE]
    if mine:
        o = mine[0]
        print(f"*** ORDER CREATED #{o['order_number']} total={o['total']} sub={o['subtotal']} "
              f"fee={o['delivery_fee']} eta={o['eta_min']}-{o['eta_max']} status={o['status']} items={[(i['name'],i['qty']) for i in o['items']]}")
        break
else:
    print("!!! NO ORDER CREATED after all steps")
