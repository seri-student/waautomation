"""Backend API regression tests for AI Restaurant Ordering SaaS."""
import time
import uuid

import pytest
import requests

from conftest import BASE_URL


# ---------------- Health / root ----------------
class TestHealth:
    def test_health(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_root(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------------- Auth ----------------
class TestAuth:
    def test_login_success(self, api_client, test_credentials):
        r = api_client.post(f"{BASE_URL}/api/auth/login", json=test_credentials, timeout=30)
        assert r.status_code == 200
        d = r.json()
        tok = d.get("access_token") or d.get("token")
        assert isinstance(tok, str) and len(tok) > 20
        assert d["user"]["email"] == test_credentials["email"]
        assert d["user"].get("restaurant_id")
        assert "password_hash" not in d["user"]

    def test_login_invalid(self, api_client, test_credentials):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"email": test_credentials["email"], "password": "wrongpass"}, timeout=30)
        assert r.status_code == 401

    def test_login_unknown_email(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"email": "nobody_TEST@x.pk", "password": "abc12345"}, timeout=30)
        assert r.status_code == 401

    def test_me(self, client, test_credentials):
        r = client.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["email"] == test_credentials["email"]
        assert d["restaurant"]["id"] == d["user"]["restaurant_id"]

    @pytest.mark.parametrize("path", [
        "/api/auth/me", "/api/menu", "/api/orders", "/api/customers",
        "/api/analytics/summary", "/api/restaurant", "/api/restaurant/ai-settings",
        "/api/whatsapp/config", "/api/conversations",
    ])
    def test_protected_requires_auth(self, api_client, path):
        r = requests.get(f"{BASE_URL}{path}", timeout=30)
        assert r.status_code == 401, f"{path} returned {r.status_code}"

    def test_bad_token_rejected(self, api_client):
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": "Bearer not.a.token"}, timeout=30)
        assert r.status_code == 401

    def test_bcrypt_hash_format(self, test_credentials):
        from pymongo import MongoClient
        from dotenv import dotenv_values
        env = dotenv_values("/app/backend/.env")
        c = MongoClient(env["MONGO_URL"])
        user = c[env["DB_NAME"]].users.find_one({"email": test_credentials["email"]})
        assert user, "seeded owner user not found"
        h = user.get("password_hash", "")
        assert h.startswith("$2b$"), f"unexpected bcrypt prefix: {h[:10]!r}"


# ---------------- Analytics ----------------
class TestAnalytics:
    def test_summary(self, client):
        r = client.get(f"{BASE_URL}/api/analytics/summary", timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ["today_orders", "today_sales", "pending_orders", "average_order_value",
                  "total_orders", "top_items"]:
            assert k in d
        assert isinstance(d["top_items"], list)


# ---------------- Menu CRUD ----------------
class TestMenu:
    def test_get_menu(self, client):
        r = client.get(f"{BASE_URL}/api/menu", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert len(d["categories"]) > 0
        assert len(d["items"]) > 0
        it = d["items"][0]
        for k in ["id", "name", "price", "available", "category_id"]:
            assert k in it
        assert "_id" not in it

    def test_category_and_item_crud(self, client):
        cat = client.post(f"{BASE_URL}/api/menu/categories",
                          json={"name": f"TEST_Cat_{uuid.uuid4().hex[:6]}", "sort_order": 50}, timeout=30)
        assert cat.status_code == 200, cat.text
        cid = cat.json()["id"]
        try:
            item = client.post(f"{BASE_URL}/api/menu/items", json={
                "category_id": cid, "name": "TEST_Item", "price": 499.0,
                "description": "test", "available": True, "image_url": "http://x/y.jpg"}, timeout=30)
            assert item.status_code == 200, item.text
            iid = item.json()["id"]
            assert item.json()["price"] == 499.0

            menu = client.get(f"{BASE_URL}/api/menu", timeout=30).json()
            assert any(i["id"] == iid for i in menu["items"])
            assert any(c["id"] == cid for c in menu["categories"])

            upd = client.put(f"{BASE_URL}/api/menu/items/{iid}",
                             json={"price": 599.0, "name": "TEST_Item_Upd"}, timeout=30)
            assert upd.status_code == 200
            assert upd.json()["price"] == 599.0
            menu = client.get(f"{BASE_URL}/api/menu", timeout=30).json()
            got = [i for i in menu["items"] if i["id"] == iid][0]
            assert got["price"] == 599.0 and got["name"] == "TEST_Item_Upd"

            # toggle availability false (regression: falsy values dropped by update filter)
            tog = client.put(f"{BASE_URL}/api/menu/items/{iid}", json={"available": False}, timeout=30)
            assert tog.status_code == 200
            menu = client.get(f"{BASE_URL}/api/menu", timeout=30).json()
            got = [i for i in menu["items"] if i["id"] == iid][0]
            assert got["available"] is False, "availability toggle to False did not persist"

            d = client.delete(f"{BASE_URL}/api/menu/items/{iid}", timeout=30)
            assert d.status_code == 200
            menu = client.get(f"{BASE_URL}/api/menu", timeout=30).json()
            assert not any(i["id"] == iid for i in menu["items"])
        finally:
            client.delete(f"{BASE_URL}/api/menu/categories/{cid}", timeout=30)


# ---------------- Restaurant + AI settings ----------------
class TestSettings:
    def test_restaurant_get_update(self, client):
        r = client.get(f"{BASE_URL}/api/restaurant", timeout=30)
        assert r.status_code == 200
        orig = r.json()
        assert orig.get("name")
        up = client.put(f"{BASE_URL}/api/restaurant", json={"delivery_fee": 149.0, "city": "Lahore"}, timeout=30)
        assert up.status_code == 200
        assert client.get(f"{BASE_URL}/api/restaurant", timeout=30).json()["delivery_fee"] == 149.0
        client.put(f"{BASE_URL}/api/restaurant",
                   json={"delivery_fee": orig.get("delivery_fee", 149.0), "city": orig.get("city", "Lahore")},
                   timeout=30)

    def test_ai_settings_get_update(self, client):
        r = client.get(f"{BASE_URL}/api/restaurant/ai-settings", timeout=30)
        assert r.status_code == 200
        orig = r.json()
        up = client.put(f"{BASE_URL}/api/restaurant/ai-settings",
                        json={"upsell_enabled": False, "personality": "TEST personality"}, timeout=30)
        assert up.status_code == 200
        got = client.get(f"{BASE_URL}/api/restaurant/ai-settings", timeout=30).json()
        assert got["personality"] == "TEST personality"
        assert got["upsell_enabled"] is False, "upsell_enabled=False did not persist"
        client.put(f"{BASE_URL}/api/restaurant/ai-settings", json={
            "upsell_enabled": orig.get("upsell_enabled", True),
            "personality": orig.get("personality", "friendly")}, timeout=30)


# ---------------- WhatsApp provider config ----------------
class TestWhatsApp:
    @pytest.fixture(scope="class", autouse=True)
    def restore_provider(self, client):
        yield
        client.post(f"{BASE_URL}/api/whatsapp/provider", json={"provider": "simulator"}, timeout=30)
        client.put(f"{BASE_URL}/api/whatsapp/meta",
                   json={"meta_access_token": "", "meta_phone_number_id": ""}, timeout=30)

    def test_config(self, client):
        r = client.get(f"{BASE_URL}/api/whatsapp/config", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["provider"] in ("simulator", "evolution", "meta")
        assert "evolution" in d and "meta" in d

    def test_provider_switch_persists(self, client):
        for p in ["evolution", "meta", "simulator"]:
            r = client.post(f"{BASE_URL}/api/whatsapp/provider", json={"provider": p}, timeout=30)
            assert r.status_code == 200
            assert r.json()["provider"] == p
            assert client.get(f"{BASE_URL}/api/whatsapp/config", timeout=30).json()["provider"] == p

    def test_meta_credentials_masked(self, client):
        r = client.put(f"{BASE_URL}/api/whatsapp/meta", json={
            "meta_access_token": "TESTTOKEN1234567890", "meta_phone_number_id": "1234567890"}, timeout=30)
        assert r.status_code == 200
        masked = r.json()["meta"]["meta_access_token_masked"]
        assert "TESTTOKEN1234567890" not in masked and "•" in masked
        client.put(f"{BASE_URL}/api/whatsapp/meta", json={"meta_access_token": ""}, timeout=30)

    def test_connect_simulator(self, client):
        client.post(f"{BASE_URL}/api/whatsapp/provider", json={"provider": "simulator"}, timeout=30)
        r = client.post(f"{BASE_URL}/api/whatsapp/connect", timeout=60)
        assert r.status_code == 200
        assert r.json()["status"] == "connected"


# ---------------- Full AI ordering flow via simulator ----------------
TEST_PHONE = "923009998877"


def _sim(client, text, phone=TEST_PHONE):
    r = client.post(f"{BASE_URL}/api/simulator/message",
                    json={"phone": phone, "name": "TEST_QA_Customer", "text": text}, timeout=180)
    assert r.status_code == 200, f"simulator failed {r.status_code}: {r.text[:400]}"
    d = r.json()
    outs = [m["text"] for m in d["messages"] if m.get("direction") == "out"]
    return d, (outs[-1] if outs else "")


@pytest.fixture(scope="class")
def order_flow(client):
    """Runs the whole AI conversation once, shared by assertions."""
    result = {}
    _sim(client, "menu dikhao")
    time.sleep(1)
    d1, reply1 = _sim(client, "menu dikhao")
    result["menu_reply"] = reply1
    d2, reply2 = _sim(client, "1 zinger burger aur fries")
    result["add_reply"] = reply2
    result["cart"] = (d2.get("conversation") or {}).get("cart", [])
    d3, reply3 = _sim(client, "haan coke")
    result["upsell_reply"] = reply3
    d4, reply4 = _sim(client, "delivery")
    d5, reply5 = _sim(client, "House 5, DHA Phase 6 Lahore")
    result["summary_reply"] = reply5 + "\n" + reply4
    d6, reply6 = _sim(client, "yes")
    # AI is non-deterministic: it may re-ask for confirmation, allow up to 2 retries
    for extra in ["haan confirm kar do", "ji order place kar do"]:
        orders = client.get(f"{BASE_URL}/api/orders", timeout=30).json()
        if any(o.get("customer_phone") == TEST_PHONE for o in orders):
            break
        d6, reply6 = _sim(client, extra)
    result["confirm_reply"] = reply6
    result["conversation"] = d6.get("conversation")
    result["all_out"] = "\n".join(m["text"] for m in d6["messages"] if m.get("direction") == "out")
    return result


class TestAIOrderFlow:
    def test_menu_shown(self, order_flow):
        txt = order_flow["menu_reply"].lower()
        assert any(k in txt for k in ["burger", "pizza", "fries", "zinger"]), order_flow["menu_reply"][:500]

    def test_items_added_to_cart(self, order_flow):
        cart = order_flow["cart"]
        assert len(cart) >= 1, f"cart empty; reply={order_flow['add_reply'][:400]}"
        for c in cart:
            assert c["qty"] >= 1 and c["unit_price"] > 0

    def test_summary_has_totals(self, order_flow):
        txt = order_flow["all_out"].lower()
        assert "total" in txt, txt[-600:]

    def test_order_created_with_number_and_eta(self, client, order_flow):
        conv = order_flow["conversation"] or {}
        orders = client.get(f"{BASE_URL}/api/orders", timeout=30).json()
        mine = [o for o in orders if o.get("customer_phone") == TEST_PHONE]
        assert mine, f"no order created. confirm reply={order_flow['confirm_reply'][:500]}"
        o = mine[0]
        assert o["order_number"]
        assert o["eta_min"] and o["eta_max"]
        assert o["status"] == "New"
        # deterministic math
        subtotal = round(sum(i["line_total"] for i in o["items"]), 2)
        assert abs(subtotal - o["subtotal"]) < 0.01
        assert abs(round(o["subtotal"] + o["delivery_fee"], 2) - o["total"]) < 0.01
        assert o["currency"] == "PKR"
        if o["order_type"] == "delivery":
            assert o["delivery_fee"] > 0
            assert o.get("address")
        assert str(o["order_number"]) in order_flow["all_out"], "order number not sent to customer"
        assert conv.get("id")

    def test_order_detail_and_status_progression(self, client):
        orders = client.get(f"{BASE_URL}/api/orders", timeout=30).json()
        mine = [o for o in orders if o.get("customer_phone") == TEST_PHONE]
        assert mine
        oid = mine[0]["id"]
        det = client.get(f"{BASE_URL}/api/orders/{oid}", timeout=30)
        assert det.status_code == 200
        assert det.json()["id"] == oid

        for st in ["Confirmed", "Preparing", "Ready", "Out for Delivery", "Delivered"]:
            r = client.patch(f"{BASE_URL}/api/orders/{oid}/status", json={"status": st}, timeout=60)
            assert r.status_code == 200, r.text
            assert r.json()["status"] == st
        final = client.get(f"{BASE_URL}/api/orders/{oid}", timeout=30).json()
        assert final["status"] == "Delivered"
        assert len(final["status_history"]) >= 6

        # status notification pushed back into the conversation
        sim = client.get(f"{BASE_URL}/api/simulator/messages", params={"phone": TEST_PHONE}, timeout=30).json()
        out = "\n".join(m["text"] for m in sim["messages"] if m.get("direction") == "out").lower()
        assert "deliver" in out or "delivered" in out, out[-500:]

    def test_invalid_status_rejected(self, client):
        orders = client.get(f"{BASE_URL}/api/orders", timeout=30).json()
        oid = [o for o in orders if o.get("customer_phone") == TEST_PHONE][0]["id"]
        r = client.patch(f"{BASE_URL}/api/orders/{oid}/status", json={"status": "Bogus"}, timeout=30)
        assert r.status_code == 400

    def test_order_404(self, client):
        r = client.get(f"{BASE_URL}/api/orders/does-not-exist", timeout=30)
        assert r.status_code == 404


# ---------------- Customers ----------------
class TestCustomers:
    def test_list_and_detail(self, client):
        r = client.get(f"{BASE_URL}/api/customers", timeout=30)
        assert r.status_code == 200
        custs = r.json()
        assert isinstance(custs, list) and custs
        cid = custs[0]["id"]
        d = client.get(f"{BASE_URL}/api/customers/{cid}", timeout=30)
        assert d.status_code == 200
        body = d.json()
        assert body["customer"]["id"] == cid
        assert isinstance(body["orders"], list)
        assert isinstance(body["messages"], list)

    def test_customer_404(self, client):
        assert client.get(f"{BASE_URL}/api/customers/nope-TEST", timeout=30).status_code == 404


# ---------------- Conversations / handoff ----------------
class TestConversations:
    def test_list_and_handoff_and_reply(self, client):
        r = client.get(f"{BASE_URL}/api/conversations", timeout=60)
        assert r.status_code == 200
        convs = r.json()
        assert convs, "no conversations"
        conv = convs[0]
        assert "customer" in conv and "last_message" in conv
        cid = conv["id"]

        off = client.post(f"{BASE_URL}/api/conversations/{cid}/handoff", json={"ai_active": False}, timeout=30)
        assert off.status_code == 200 and off.json()["ai_active"] is False
        msgs = client.get(f"{BASE_URL}/api/conversations/{cid}/messages", timeout=30).json()
        assert msgs["conversation"]["ai_active"] is False
        assert msgs["conversation"]["state"] == "HUMAN_HANDOFF"

        rep = client.post(f"{BASE_URL}/api/conversations/{cid}/reply",
                          json={"text": "TEST_human_reply_hello"}, timeout=30)
        assert rep.status_code == 200
        after = client.get(f"{BASE_URL}/api/conversations/{cid}/messages", timeout=30).json()
        assert any(m["text"] == "TEST_human_reply_hello" and m.get("sender") == "human"
                   for m in after["messages"])

        on = client.post(f"{BASE_URL}/api/conversations/{cid}/handoff", json={"ai_active": True}, timeout=30)
        assert on.status_code == 200 and on.json()["ai_active"] is True

    def test_conversation_404(self, client):
        assert client.get(f"{BASE_URL}/api/conversations/nope-TEST/messages", timeout=30).status_code == 404


# ---------------- SSE stream ----------------
class TestStream:
    def test_stream_requires_token(self, api_client):
        r = requests.get(f"{BASE_URL}/api/stream", timeout=30, stream=True)
        body = r.text[:200]
        r.close()
        # Design: SSE returns 200 with an "unauthorized" error event instead of 401
        assert "unauthorized" in body, body

    def test_stream_opens_with_token(self, auth_token):
        r = requests.get(f"{BASE_URL}/api/stream", params={"token": auth_token},
                         timeout=30, stream=True)
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        r.close()


# ---------------- Multi-tenant isolation ----------------
class TestTenantIsolation:
    def test_new_tenant_sees_no_other_data(self, api_client, client):
        email = f"test_tenant_{uuid.uuid4().hex[:8]}@example.com"
        reg = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "name": "TEST Owner", "restaurant_name": "TEST Resto",
            "email": email, "password": "testpass123"}, timeout=60)
        assert reg.status_code in (200, 201), reg.text
        tok = reg.json().get("access_token") or reg.json().get("token")
        assert tok
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {tok}"})
        orders = s.get(f"{BASE_URL}/api/orders", timeout=30).json()
        assert orders == [] or all(o.get("customer_phone") != TEST_PHONE for o in orders)
        mine_rid = s.get(f"{BASE_URL}/api/auth/me", timeout=30).json()["user"]["restaurant_id"]
        other_rid = client.get(f"{BASE_URL}/api/auth/me", timeout=30).json()["user"]["restaurant_id"]
        assert mine_rid != other_rid
        # cannot read other tenant's order
        other_orders = client.get(f"{BASE_URL}/api/orders", timeout=30).json()
        if other_orders:
            r = s.get(f"{BASE_URL}/api/orders/{other_orders[0]['id']}", timeout=30)
            assert r.status_code == 404
