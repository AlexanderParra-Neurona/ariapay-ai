# Ariabot API Reference

Base URL (local dev): `http://localhost:8000`

Ariabot is a chat backend for Ariapay. It classifies each question and either answers directly, pulls the user's account/transaction data from the Ariapay API, or falls back to a RAG-based FAQ answer.

## Authentication

There is no session/cookie auth. The frontend calls `POST /v1/auth/login` to obtain an `access_token` from Ariapay's own backend, then passes that token back on every `POST /v1/chat` call that needs account-scoped data (`access_token` field in the request body). Ariabot does not persist tokens — the frontend is responsible for storing and refreshing them.

---

## `GET /v1/health`

Health check.

**Response `200`**
```json
{ "status": "ok" }
```

---

## `POST /v1/auth/login`

Logs in to Ariapay (phone + password + passcode) and returns tokens to use with `/v1/chat`.

**Request body**
```json
{
  "phone_number": "8123456789",
  "country_code": "62",
  "password": "string",
  "passcode": "123456"
}
```

| Field | Type | Notes |
|---|---|---|
| `phone_number` | string | no leading `0`/`+`, digits only, no country code prefix |
| `country_code` | string | e.g. `"62"` |
| `password` | string | account password |
| `passcode` | string | 6-digit passcode, verified in a second step server-side |

**Response `200`**
```json
{
  "access_token": "string",
  "refresh_token": "string"
}
```
Store `access_token`; send it as `access_token` in `/v1/chat` requests for account/transaction questions.

**Errors**
| Status | When |
|---|---|
| `401` | wrong phone/password, or wrong passcode |
| `422` | request body validation failure (missing/malformed fields) |
| `502` | upstream Ariapay API error |

Error body shape (FastAPI default):
```json
{ "detail": "Wrong phone number or password" }
```

---

## `POST /v1/chat`

Main chat endpoint. Send a question; get back a routed answer.

**Request body**
```json
{
  "question": "string",
  "access_token": "string | null"
}
```
`access_token` is optional. Omit it (or send `null`) for anonymous/FAQ questions. It's required for account-profile and transaction-history questions — if missing, the API returns a "please sign in" message instead of erroring.

**Response `200`**
```json
{
  "answer": "string",
  "short_circuit": true,
  "category": "general_faq" | "account_profile" | "transaction_history" | "out_of_scope",
  "policy_decision": "answered" | "declined_out_of_scope" | "declined_auth_required" | "handoff_no_data",
  "citations": [
    { "source": "string", "heading": "string" }
  ],
  "confidence": 0.0
}
```

| Field | Meaning |
|---|---|
| `answer` | text to render in chat |
| `category` | internal routing classification (useful for analytics, not required to act on) |
| `short_circuit` | `true` if answer came from a deterministic path (account data, transaction data, out-of-scope message, sign-in prompt); `false` if answer was generated via RAG/LLM over FAQ docs |
| `policy_decision` | the field the UI should switch on — see below |
| `citations` | sources backing the answer. Empty array when the answer wasn't grounded in retrieved docs (account/transaction/out-of-scope/no-data paths) |
| `confidence` | retrieval confidence for the top-ranked source, `null` when not applicable (any path other than the FAQ/RAG path) |

**`policy_decision` values**

| Value | Meaning | UI handling |
|---|---|---|
| `answered` | assistant produced a real answer (FAQ/RAG, account profile, or transaction summary) | render `answer` normally, show `citations` if present |
| `declined_out_of_scope` | question outside what Ariabot handles | render `answer` as a decline message |
| `declined_auth_required` | account/transaction question asked without a valid/unexpired `access_token` | prompt sign-in (or re-auth on expired session) |
| `handoff_no_data` | assistant understood the question but found nothing to answer with (no matching FAQ docs, no matching transactions, or account fetch failed upstream) | render `answer`, surface a "didn't find that / contact support" affordance — distinct from a decline |

`policy_decision` is what distinguishes "assistant didn't know" (`handoff_no_data`) from "assistant answered" (`answered`) for the decline/handoff UX.

`citations[].source` is the FAQ doc filename a chunk came from; `citations[].heading` is that chunk's markdown heading (`""` if none).

**Behavior by category**

- **`account_profile`** — requires `access_token`. Returns formatted profile (name, email, phone, cards). If token missing/expired, returns a sign-in prompt instead (still `200`, `short_circuit: true`, `policy_decision: "declined_auth_required"`).
- **`transaction_history`** — requires `access_token`. Returns a spend summary + bulleted list of matching transactions. If no transactions match, returns "couldn't find any transactions matching that." (`policy_decision: "handoff_no_data"`).
- **`out_of_scope`** — fixed message telling the user Ariabot only handles Ariapay/account/transaction questions (`policy_decision: "declined_out_of_scope"`).
- **`general_faq`** (or anything not matching the above) — answered via hybrid retrieval + LLM generation over the FAQ knowledge base. `policy_decision` is `"handoff_no_data"` when no matching docs are found, `"answered"` otherwise.

**Errors**
| Status | When |
|---|---|
| `422` | request body validation failure |

Note: `/v1/chat` does not raise `401`/`502` for auth/upstream failures — those are caught and returned as a normal `200` response with an explanatory `answer` and `short_circuit: true`. Only `/v1/auth/login` raises HTTP error statuses for auth failures.

---

## Example flow

```js
// 1. Anonymous FAQ question
const res = await fetch("http://localhost:8000/v1/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "What is Ariapay?" }),
});
const { answer, category, short_circuit } = await res.json();

// 2. Login
const loginRes = await fetch("http://localhost:8000/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    phone_number: "8123456789",
    country_code: "62",
    password: "hunter2",
    passcode: "123456",
  }),
});
const { access_token } = await loginRes.json();

// 3. Account-scoped question
const chatRes = await fetch("http://localhost:8000/v1/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "How much did I spend on food this month?",
    access_token,
  }),
});
```

## CORS

Not currently configured in `app/main.py` — if the frontend is served from a different origin, backend needs a `CORSMiddleware` added before this works cross-origin. Flag to backend team if needed.
