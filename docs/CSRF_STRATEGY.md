# CSRF Protection Strategy

## Overview

This API uses **cookie-based JWT authentication** with **CSRF token protection** for mutation requests (POST, PUT, DELETE).

### Why Both JWT + CSRF?
- **JWT (access_token cookie)** - Authenticates the user
- **CSRF token** - Prevents cross-site request forgery attacks on authenticated users

---

## CSRF Flow Architecture

### Main Components

| Component | Type | HttpOnly | Frontend Access | Purpose |
|-----------|------|----------|-----------------|---------|
| `access_token` | Cookie | Yes | No | JWT for authentication |
| `refresh_token` | Cookie | Yes | No | JWT for token rotation |
| `csrftoken` | Cookie | **No** | Yes | CSRF protection token |
| `X-CSRFToken` | Header | N/A | Frontend sends | CSRF validation header |

---

## Recommended Frontend Flow

### **Flow A: Primary (After Login)**

```
STEP 1: LOGIN
└─ POST /api/v1/auth/login/
   ├─ Request:  {"email": "...", "password": "..."}
   └─ Response: 200 OK
      {
        "user": {...},
        "memberships": [...],
        "csrf_token": "KV4x2fJ9m3kL8pQwZ1tY0uV5aB6cD7eF"  ← STORE THIS
      }
      Cookies Set:
      - access_token (HttpOnly, Secure)
      - csrftoken (Secure, readable by JS)
      Headers:
      - X-CSRFToken: "KV4x2fJ9m3kL8pQwZ1tY0uV5aB6cD7eF"

STEP 2: MUTATION REQUEST (POST/PUT/DELETE)
└─ POST /api/v1/indicators/
   ├─ Headers:
   │  ├─ X-CSRFToken: "KV4x2fJ9m3kL8pQwZ1tY0uV5aB6cD7eF"  ← SEND YOUR STORED TOKEN
   │  └─ Content-Type: application/json
   ├─ Body: {...}
   └─ Cookies (auto-sent by browser):
      - access_token (validates JWT)
      - csrftoken (Django validates against X-CSRFToken header)

VALIDATION:
Django CsrfViewMiddleware checks:
✓ X-CSRFToken header value matches csrftoken cookie value
✓ If match → Request allowed
✓ If mismatch → 403 Forbidden
```

### **Flow B: Bootstrap (Before Login)**

For unauthenticated mutations (signup, password reset):

```
STEP 1: GET CSRF TOKEN
└─ GET /api/v1/auth/csrf/
   └─ Response: 200 OK
      {
        "csrf_token": "Kx2V4m9fL0pJ1qW8aZ3tY6uB5cD7eE"  ← STORE THIS
      }
      Cookies Set:
      - csrftoken (same value)

STEP 2: PUBLIC MUTATION
└─ POST /api/v1/auth/signup/
   ├─ Headers:
   │  └─ X-CSRFToken: "Kx2V4m9fL0pJ1qW8aZ3tY6uB5cD7eE"
   ├─ Body: {...}
   └─ Cookies (auto-sent):
      - csrftoken
```

### **Flow C: Token Refresh**

When access_token expires:

```
STEP 1: REFRESH TOKEN
└─ POST /api/v1/auth/refresh/
   └─ Response: 200 OK
      {
        "csrf_token": "NEW_TOKEN_VALUE"  ← UPDATE YOUR STORED TOKEN
      }
      Cookies Updated:
      - access_token (new JWT)
      - refresh_token (new refresh JWT)
      - csrftoken (rotated for security)

STEP 2: USE NEW CSRF TOKEN
└─ ALL subsequent requests use the NEW csrf_token
```

---

## Frontend Implementation Examples

### JavaScript (Fetch API)

```javascript
// Store CSRF token after login
let csrfToken = null;

// 1. LOGIN
const loginResponse = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  credentials: 'include',  // ← CRITICAL: sends cookies
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({email: '...', password: '...'})
});

const loginData = await loginResponse.json();
csrfToken = loginData.csrf_token;  // Store for mutations

// 2. MAKE MUTATION REQUEST
const response = await fetch('/api/v1/indicators/', {
  method: 'POST',
  credentials: 'include',  // ← Auto-sends cookies
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken  // ← Send your stored token
  },
  body: JSON.stringify({...})
});

// 3. ON TOKEN REFRESH
const refreshResponse = await fetch('/api/v1/auth/refresh/', {
  method: 'POST',
  credentials: 'include'
});

const refreshData = await refreshResponse.json();
csrfToken = refreshData.csrf_token;  // Update stored token
```

### TypeScript/React

```typescript
import { useState, useEffect } from 'react';

export function useCSRF() {
  const [csrf, setCSRF] = useState<string | null>(null);

  const updateCSRF = (token: string) => {
    setCSRF(token);
    // Optionally persist to localStorage
    localStorage.setItem('csrf_token', token);
  };

  // After login
  const handleLogin = async (email: string, password: string) => {
    const res = await fetch('/api/v1/auth/login/', {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });
    const data = await res.json();
    updateCSRF(data.csrf_token);
  };

  // Generic mutation helper
  const mutate = (
    url: string,
    method: 'POST' | 'PUT' | 'DELETE',
    body: any
  ) => {
    if (!csrf) throw new Error('CSRF token not set');
    
    return fetch(url, {
      method,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify(body)
    });
  };

  return {csrf, updateCSRF, mutate};
}
```

### Axios

```javascript
import axios from 'axios';

// Create instance with credentials
const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true  // ← Auto-send cookies
});

// Store CSRF after login
let csrfToken = null;

api.interceptors.response.use(
  response => {
    // Capture CSRF from login/refresh responses
    if (response.data?.csrf_token) {
      csrfToken = response.data.csrf_token;
    }
    return response;
  }
);

// Add CSRF header to mutations
api.interceptors.request.use(request => {
  if (['POST', 'PUT', 'DELETE'].includes(request.method?.toUpperCase())) {
    request.headers['X-CSRFToken'] = csrfToken;
  }
  return request;
});

// Usage
const login = () => api.post('/auth/login/', {email, password});
const createIndicator = () => api.post('/indicators/', {...});
```

---

## Backend Implementation Details

### Cookie Configuration (Development vs Production)

**Development (HTTP, localhost):**
```python
DEBUG = True
CSRF_COOKIE_SECURE = False      # Allow HTTP
CSRF_COOKIE_SAMESITE = "Lax"    # Allow same-site requests
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
```

**Production (HTTPS):**
```python
DEBUG = False
CSRF_COOKIE_SECURE = True       # Require HTTPS
CSRF_COOKIE_SAMESITE = "None"   # Allow cross-site with Secure flag
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"
```

### CSRF Validation (in `src/accounts/auth/authentication.py`)

```python
# For authenticated requests (with access_token)
# CsrfViewMiddleware is invoked to validate:
if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
    reason = CsrfViewMiddleware(...).process_view(request, ...)
    if reason is not None:
        raise PermissionDenied("CSRF validation failed")
```

**What it checks:**
1. Request has `X-CSRFToken` header
2. Header value matches `csrftoken` cookie value
3. If mismatch → 403 Forbidden

---

## Security Considerations

### Token Rotation
- ✅ Token is **rotated on login** (prevents fixation)
- ✅ Token is **rotated on refresh** (keeps fresh)
- ✅ Old tokens become invalid immediately

### HttpOnly Enforcement
- ✅ `access_token` is HttpOnly → JS cannot read (XSS protection)
- ✅ `refresh_token` is HttpOnly → JS cannot read (XSS protection)
- ⚠️ `csrftoken` is NOT HttpOnly → JS must read it (by design)

### SameSite Policy
- **Lax** (development): Allow same-site requests, reject cross-site
- **None** (production): Allow cross-site only with Secure=True

---

## Common Issues & Solutions

### Issue: "CSRF validation failed"

**Cause:** One or more of:
1. ❌ No `X-CSRFToken` header sent
2. ❌ Header value doesn't match cookie
3. ❌ CSRF token not set (didn't call login or `/auth/csrf/`)
4. ❌ Credentials not included (`withCredentials: false`)

**Solution:**
```javascript
// Ensure credentials are sent
fetch(url, {
  credentials: 'include',  // ← REQUIRED
  headers: {
    'X-CSRFToken': csrfToken  // ← REQUIRED for mutations
  }
})
```

### Issue: "CSRF token missing"

**Cause:** Did not call login or `/auth/csrf/` before mutation

**Solution:**
```javascript
// First: Get CSRF token
const data = await fetch('/api/v1/auth/csrf/').then(r => r.json());
csrfToken = data.csrf_token;

// Then: Use it on mutations
```

### Issue: 403 Forbidden on browser, but works in Postman

**Cause:** CORS + credentials issue

**Solution:**
```javascript
// When using credentials, CORS headers matter:
// 1. Frontend requests with credentials: 'include'
// 2. Backend must have Access-Control-Allow-Credentials: true
// 3. Backend must NOT use Access-Control-Allow-Origin: *
//    (must explicitly list origin like http://localhost:3000)
```

---

## Testing CSRF Protection

### With cURL (demonstrates CSRF protection)

```bash
# 1. Get CSRF token
curl -i -c cookies.txt https://api.example.com/api/v1/auth/csrf/

# 2. Extract csrftoken from cookies.txt
# Example: csrf_token value from Set-Cookie header

# 3. Try mutation WITHOUT X-CSRFToken header → Should fail
curl -i -b cookies.txt -X POST \
  -H "Content-Type: application/json" \
  https://api.example.com/api/v1/indicators/
# Expected: 403 Forbidden

# 4. Try mutation WITH X-CSRFToken header → Should succeed
CSRF_TOKEN="value_from_step_2"
curl -i -b cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  https://api.example.com/api/v1/indicators/
# Expected: 201 Created (or appropriate response)
```

---

## FAQ

**Q: Why do we need CSRF if we're using HttpOnly cookies?**
A: HttpOnly protects against XSS (JavaScript injection). CSRF protects against cross-site request forgery (attacker site making requests on behalf of user). Both are needed.

**Q: Can frontend read the CSRF token from the cookie directly?**
A: Yes, that's why we set `HttpOnly=False` on csrftoken. JavaScript can read it via `document.cookie` and prefer reading from response body (cleaner).

**Q: What if the frontend is on a different domain?**
A: CSRF protection still works. The CSRF token in the X-CSRFToken header is validated server-side, regardless of origin. CORS settings allow cross-origin requests.

**Q: Do I need to send CSRF token on GET requests?**
A: No, only on mutations (POST, PUT, DELETE, PATCH). GET requests are read-only and don't need CSRF protection.

**Q: Can CSRF tokens be reused?**
A: Yes, a CSRF token is valid until it expires or is regenerated. You don't need a new token on every request—reuse the same one until login/refresh.

---

## Related Documentation

- [Django CSRF Protection](https://docs.djangoproject.com/en/stable/ref/csrf/)
- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Authentication Flow](./AUTHENTICATION.md) (if exists)
