"""Remove QA-created data (test phones, test tenants, test meta creds)."""
from dotenv import dotenv_values
from pymongo import MongoClient

env = dotenv_values("/app/backend/.env")
db = MongoClient(env["MONGO_URL"])[env["DB_NAME"]]

PHONES = ["923009998877", "923001230011", "923063676354", "923092878630"]

cust_ids = [c["id"] for c in db.customers.find({"phone": {"$in": PHONES}}, {"id": 1})]
conv_ids = [c["id"] for c in db.conversations.find({"customer_id": {"$in": cust_ids}}, {"id": 1})]
print("orders:", db.orders.delete_many({"customer_phone": {"$in": PHONES}}).deleted_count)
print("messages:", db.messages.delete_many({"conversation_id": {"$in": conv_ids}}).deleted_count)
print("conversations:", db.conversations.delete_many({"id": {"$in": conv_ids}}).deleted_count)
print("customers:", db.customers.delete_many({"id": {"$in": cust_ids}}).deleted_count)

# test tenants created by the registration/isolation test
tenant_users = list(db.users.find({"email": {"$regex": "^test_tenant_"}}, {"id": 1, "restaurant_id": 1}))
rids = [u["restaurant_id"] for u in tenant_users]
if rids:
    for coll in ["restaurants", "menu_categories", "menu_items", "ai_settings", "whatsapp_connections"]:
        q = {"id": {"$in": rids}} if coll == "restaurants" else {"restaurant_id": {"$in": rids}}
        print(coll, db[coll].delete_many(q).deleted_count)
print("test users:", db.users.delete_many({"email": {"$regex": "^test_tenant_"}}).deleted_count)

# clear QA-injected meta credentials on the demo restaurant
print("meta creds reset:", db.whatsapp_connections.update_many(
    {"meta_phone_number_id": "1234567890"},
    {"$set": {"meta_phone_number_id": "", "meta_access_token": ""}}).modified_count)

# clear QA menu leftovers
print("qa menu items:", db.menu_items.delete_many({"name": {"$regex": "^(QA_|TEST_)"}}).deleted_count)
print("qa categories:", db.menu_categories.delete_many({"name": {"$regex": "^(QA_|TEST_)"}}).deleted_count)
