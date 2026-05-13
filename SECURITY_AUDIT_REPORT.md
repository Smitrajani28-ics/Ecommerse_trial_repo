# 🛡️ Security Audit Report

**Project:** Django E-Commerce Site
**Commit:** `2df9d90` — *"adding new files"*
**Date:** April 1, 2026
**Auditor:** Kiro AI

---

## 📊 Summary Dashboard

| Metric | Count |
|---|---|
| 🔴 Critical | 2 |
| 🟠 High | 2 |
| 🟡 Medium | 3 |
| 🟢 Low | 1 |
| **Total Issues** | **8** |

```
Risk Distribution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Critical  ██████████████░░░░░░░░░░░░  25%
🟠 High      ██████████████░░░░░░░░░░░░  25%
🟡 Medium    ███████████████████░░░░░░░  37.5%
🟢 Low       ██████░░░░░░░░░░░░░░░░░░░░  12.5%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🗺️ Affected Components

```
┌─────────────────────────────────────────────────────┐
│                  Django E-Commerce                   │
├──────────┬──────────┬───────────┬───────────────────┤
│ accounts │   cart   │  orders   │     payments      │
│  🔴 🟠   │   🟡    │   🟠     │     🔴 🟡         │
│          │          │           │                   │
│ • Open   │ • Input  │ • Race   │ • Payment Bypass  │
│   Redir  │   Valid  │   Cond   │ • Secret Storage  │
│ • CSRF   │          │          │                   │
│   Logout │          │          │                   │
│ • GET    │          │          │                   │
│   Delete │          │          │                   │
└──────────┴──────────┴───────────┴───────────────────┘
```

---

## 🔴 CRITICAL Issues

### Issue #1 — Open Redirect on Login

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **File** | `accounts/views.py` → `CustomLoginView.post()` |
| **Line** | ~53 |
| **OWASP** | A01:2021 — Broken Access Control |
| **CWE** | CWE-601: URL Redirection to Untrusted Site |

**Description:**
The `next` query parameter is used directly in a redirect after login without any validation.

```python
# ❌ VULNERABLE CODE
next_page = request.GET.get('next', '/')
return redirect(next_page)
```

**Attack Flow:**

```
┌──────────┐    Malicious Link     ┌──────────────┐
│ Attacker │ ──────────────────▶   │    Victim     │
└──────────┘                       └──────┬───────┘
                                          │
    /accounts/login/?next=https://evil.com│
                                          ▼
                                   ┌──────────────┐
                                   │  Login Page   │
                                   │  (Legit Site) │
                                   └──────┬───────┘
                                          │ User logs in
                                          ▼
                                   ┌──────────────┐
                                   │  evil.com     │ ← Redirected!
                                   │  (Phishing)   │
                                   └──────────────┘
```

**Fix:**

```python
# ✅ SECURE CODE
from django.utils.http import url_has_allowed_host_and_scheme

next_page = request.GET.get('next', '/')
if not url_has_allowed_host_and_scheme(
    next_page, allowed_hosts={request.get_host()}
):
    next_page = '/'
return redirect(next_page)
```

---

### Issue #2 — Payment Bypass in Demo Mode

| | |
|---|---|
| **Severity** | 🔴 Critical |
| **File** | `payments/views.py` → `PaymentSuccessView.get()` |
| **Line** | ~78-82 |
| **OWASP** | A04:2021 — Insecure Design |
| **CWE** | CWE-284: Improper Access Control |

**Description:**
When `STRIPE_SECRET_KEY` is empty, visiting the payment success URL auto-completes the order without any actual payment.

```python
# ❌ VULNERABLE CODE
else:
    # For demo/dev without Stripe, mark as completed
    payment.mark_completed()
```

**Attack Flow:**

```
┌──────────┐                        ┌──────────────┐
│ Attacker │                        │   Server     │
└────┬─────┘                        └──────┬───────┘
     │                                      │
     │  1. Create order (add to cart,       │
     │     go through checkout)             │
     │ ──────────────────────────────────▶  │
     │                                      │
     │  2. Skip payment page entirely       │
     │     GET /payments/success/<id>/      │
     │ ──────────────────────────────────▶  │
     │                                      │
     │         ┌─────────────────────┐      │
     │         │ STRIPE_SECRET_KEY   │      │
     │         │ is empty → auto     │      │
     │         │ mark_completed()    │      │
     │         └─────────────────────┘      │
     │                                      │
     │  3. Order marked as PAID 💰          │
     │ ◀────────────────────────────────── │
     │     (without paying anything)        │
```

**Fix:**

```python
# ✅ SECURE CODE
if settings.STRIPE_SECRET_KEY and payment.stripe_payment_intent_id:
    try:
        intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
        if intent.status == 'succeeded':
            payment.mark_completed()
    except Exception as e:
        logger.error(f'Stripe verification error: {e}')
elif settings.DEBUG:
    # Only allow demo bypass in DEBUG mode
    payment.mark_completed()
else:
    logger.warning('Payment verification skipped — no Stripe key and DEBUG=False')
    messages.error(request, 'Payment could not be verified.')
    return redirect('payments:process', order_id=order.id)
```

---

## 🟠 HIGH Issues

### Issue #3 — CSRF Logout via GET

| | |
|---|---|
| **Severity** | 🟠 High |
| **File** | `accounts/views.py` → `CustomLogoutView.get()` |
| **OWASP** | A01:2021 — Broken Access Control |
| **CWE** | CWE-352: Cross-Site Request Forgery |

**Description:**
Logout is triggered by a simple GET request. An attacker can embed a hidden image tag on any website to force-logout users.

```html
<!-- Attacker's website -->
<img src="https://yoursite.com/accounts/logout/" style="display:none">
<!-- User is now logged out without knowing -->
```

**Fix:**
Change logout to require POST with CSRF token:

```python
# ✅ SECURE CODE
from django.views.decorators.http import require_POST

class CustomLogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('/')
```

---

### Issue #4 — Race Condition on Stock Reduction

| | |
|---|---|
| **Severity** | 🟠 High |
| **File** | `orders/views.py` → `OrderCreateView.post()` |
| **OWASP** | A04:2021 — Insecure Design |
| **CWE** | CWE-362: Race Condition |

**Description:**
Stock is reduced without database-level locking. Concurrent checkouts can oversell products.

```
Timeline (stock = 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  User A                    User B
    │                         │
    ├─ Read stock: 1          │
    │                         ├─ Read stock: 1
    ├─ reduce_stock(1)        │
    │  stock → 0              ├─ reduce_stock(1)
    │                         │  stock → -1  ❌ OVERSOLD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Fix:**

```python
# ✅ SECURE CODE
from django.db import transaction

with transaction.atomic():
    for item in cart_items:
        # Lock the product row
        product = Product.objects.select_for_update().get(pk=item.product.pk)
        if product.stock_quantity < item.quantity:
            messages.error(request, f'"{product.name}" is out of stock.')
            return redirect('cart:cart_detail')
        OrderItem.objects.create(
            order=order, product=product,
            product_name=product.name, product_sku=product.sku,
            quantity=item.quantity, unit_price=product.price,
            total_price=item.quantity * product.price,
        )
        product.reduce_stock(item.quantity)
```

---

## 🟡 MEDIUM Issues

### Issue #5 — Address Deletion via GET

| | |
|---|---|
| **Severity** | 🟡 Medium |
| **File** | `accounts/views.py` → `delete_address()` |
| **CWE** | CWE-352: Cross-Site Request Forgery |

Destructive action performed on GET request. Should require POST.

```python
# ✅ FIX
from django.views.decorators.http import require_POST

@login_required
@require_POST
def delete_address(request, address_id):
    ...
```

---

### Issue #6 — Unhandled Integer Parsing in Cart

| | |
|---|---|
| **Severity** | 🟡 Medium |
| **File** | `cart/views.py` → `cart_add()`, `cart_update()` |
| **CWE** | CWE-20: Improper Input Validation |

Sending `quantity=abc` causes an unhandled `ValueError` → HTTP 500.

```python
# ❌ CURRENT
quantity = int(request.POST.get('quantity', 1))

# ✅ FIX
try:
    quantity = int(request.POST.get('quantity', 1))
except (ValueError, TypeError):
    quantity = 1
```

---

### Issue #7 — Stripe Client Secret Persisted in DB

| | |
|---|---|
| **Severity** | 🟡 Medium |
| **File** | `payments/models.py` |
| **CWE** | CWE-312: Cleartext Storage of Sensitive Information |

The `stripe_client_secret` is stored in plaintext. A database breach exposes active payment sessions. Consider clearing it after use or not persisting it at all.

---

## 🟢 LOW Issues

### Issue #8 — .env File History Exposure

| | |
|---|---|
| **Severity** | 🟢 Low |
| **File** | `.env` / `.gitignore` |
| **CWE** | CWE-200: Exposure of Sensitive Information |

The `.env` is in `.gitignore` now, but if it was ever committed previously, secrets like `SECRET_KEY` and `DB_PASSWORD` remain in git history. Verify with:

```bash
git log --all --full-history -- .env
```

If found, rotate all secrets and consider using `git filter-branch` or `BFG Repo-Cleaner` to purge history.

---

## ✅ Remediation Priority

```
Priority Matrix (Impact vs Effort)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          │  Low Effort    │  High Effort
──────────┼────────────────┼──────────────
High      │ #1 Open Redir  │ #4 Race Cond
Impact    │ #2 Payment     │
          │ #3 CSRF Logout │
──────────┼────────────────┼──────────────
Low       │ #5 GET Delete  │ #7 Secret
Impact    │ #6 Input Valid  │    Storage
          │ #8 .env History│
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Recommended fix order:**
1. 🔴 #1 Open Redirect — 5 min fix, critical impact
2. 🔴 #2 Payment Bypass — 10 min fix, critical impact
3. 🟠 #3 CSRF Logout — 10 min fix
4. 🟡 #5 GET Delete — 2 min fix
5. 🟡 #6 Input Validation — 5 min fix
6. 🟠 #4 Race Condition — 30 min fix (needs testing)
7. 🟡 #7 Secret Storage — 20 min refactor
8. 🟢 #8 .env History — 15 min if applicable

---

*Generated by Kiro AI Security Audit*
