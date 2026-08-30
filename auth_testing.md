# Auth Testing Notes

Auth: JWT Bearer (HS256), token in localStorage, sent as `Authorization: Bearer <token>`.
Passwords hashed with bcrypt. Multi-tenant: each user has `restaurant_id`; all data is scoped by it.

## Demo credentials
- owner@pizzapalace.pk / palace123  (role: owner, restaurant: Pizza Palace)

## Quick API checks
```
API=<REACT_APP_BACKEND_URL>
TOKEN=$(curl -s -X POST "$API/api/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"owner@pizzapalace.pk","password":"palace123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -s "$API/api/auth/me" -H "Authorization: Bearer $TOKEN"
curl -s "$API/api/orders" -H "Authorization: Bearer $TOKEN"
```

## Notes
- 401 without/with invalid token on protected routes.
- Tenant isolation: a token for restaurant A must never return restaurant B's orders/menu/customers.
- Registration creates a brand-new restaurant + owner (fresh tenant).
