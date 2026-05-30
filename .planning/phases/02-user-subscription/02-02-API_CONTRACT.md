# 02-02 API Contract (Frontend Integration)

> **Index:** 本文是 02-02 接口的 Single Source of Truth。完整产物索引见 [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md)；验证证据见 [`02-02-VALIDATION.md`](./02-02-VALIDATION.md)。

## Base

- Base URL: `/api/v1`
- Content-Type: `application/json`

## Authentication

### Production

- Header: `Authorization: Bearer <access_token>`
- Token requirement: JWT payload `type=access`

### Local/Test Fallback

- Header: `x-user-id: <user_id>`
- Purpose: local debug and API tests

## Endpoints

### 1) Topic Categories

- **GET** `/subscriptions/topics/categories`
- **Auth**: No
- **Response 200**

```json
[
  { "name": "tech", "topic_count": 12 },
  { "name": "finance", "topic_count": 8 }
]
```

### 2) Topic List

- **GET** `/subscriptions/topics`
- **Auth**: Yes
- **Query**
  - `category` (optional, string)
  - `q` (optional, string)
  - `limit` (optional, int, default 20, range 1-100)
  - `offset` (optional, int, default 0, min 0)
- **Response 200**

```json
[
  {
    "id": "5f5f1c4f-8ed6-42a6-a3c4-45b68d8ec8fb",
    "name": "AI",
    "slug": "ai",
    "description": "Artificial Intelligence",
    "category": "tech",
    "subscriber_count": 1024,
    "is_subscribed": true
  }
]
```

### 3) Topic Detail

- **GET** `/subscriptions/topics/{topic_id}`
- **Auth**: Yes
- **Response 200**: same schema as Topic List item
- **Response 404**

```json
{ "detail": "Topic not found" }
```

### 4) My Subscriptions

- **GET** `/subscriptions/me`
- **Auth**: Yes
- **Query**
  - `limit` (optional, int, default 100, range 1-200)
  - `offset` (optional, int, default 0, min 0)
- **Response 200**

```json
[
  {
    "topic": {
      "id": "5f5f1c4f-8ed6-42a6-a3c4-45b68d8ec8fb",
      "name": "AI",
      "slug": "ai",
      "description": "Artificial Intelligence",
      "category": "tech",
      "subscriber_count": 1024,
      "is_subscribed": true
    },
    "is_active": true,
    "priority": 10,
    "push_enabled": true,
    "push_breaking_only": false,
    "subscribed_at": "2026-05-28T08:00:00"
  }
]
```

### 5) Subscribe Existing Topic

- **POST** `/subscriptions/subscribe`
- **Auth**: Yes
- **Body**

```json
{
  "topic_id": "5f5f1c4f-8ed6-42a6-a3c4-45b68d8ec8fb",
  "push_enabled": true,
  "push_breaking_only": false
}
```

- **Response 200**

```json
{ "success": true }
```

### 6) Subscribe by Keyword

- **POST** `/subscriptions/subscribe/keyword`
- **Auth**: Yes
- **Body**

```json
{
  "keyword": "NVIDIA",
  "category": "custom",
  "push_enabled": true,
  "push_breaking_only": false
}
```

- **Response 200**

```json
{
  "success": true,
  "topic": {
    "id": "d35d2d8f-57dc-4f6f-b6f9-b0d94ca87161",
    "name": "NVIDIA",
    "slug": "keyword-nvidia",
    "description": "Keyword subscription: NVIDIA",
    "category": "custom",
    "subscriber_count": 1,
    "is_subscribed": true
  }
}
```

### 7) Update One Subscription

- **PATCH** `/subscriptions/me/{topic_id}`
- **Auth**: Yes
- **Body** (all fields optional; send only changed fields)

```json
{
  "is_active": true,
  "priority": 20,
  "push_enabled": true,
  "push_breaking_only": true
}
```

- **Response 200**

```json
{ "success": true }
```

- **Response 404**

```json
{ "detail": "Subscription not found" }
```

### 8) Reorder Subscriptions

- **PUT** `/subscriptions/me/reorder`
- **Auth**: Yes
- **Body**

```json
{
  "items": [
    { "topic_id": "topic-1", "priority": 30 },
    { "topic_id": "topic-2", "priority": 20 }
  ]
}
```

- **Response 200**

```json
{ "success": true, "updated": 2 }
```

### 9) Unsubscribe

- **DELETE** `/subscriptions/unsubscribe/{topic_id}`
- **Auth**: Yes
- **Response 200**

```json
{ "success": true }
```

- **Response 404**

```json
{ "detail": "Subscription not found" }
```

### 10) User Profile & Settings

- **GET** `/users/me` (Auth: Yes)
- **PUT** `/users/me/settings` (Auth: Yes)
- **GET** `/users/me/export` (Auth: Yes)
- **DELETE** `/users/me` (Auth: Yes)

### 11) Personalized Feed

- **GET** `/articles/feed`
- **Auth**: Yes
- **Query**
  - `page` (default 1, min 1)
  - `page_size` (default 20, range 1-100)
- **Response 200**

```json
{
  "page": 1,
  "page_size": 20,
  "articles": [],
  "has_more": false
}
```

## Error Contract

- Unauthorized: `401`

```json
{ "detail": "Authentication required" }
```

- Invalid token: `401`

```json
{ "detail": "Invalid access token" }
```

## Suggested Frontend Flow

1. `GET /subscriptions/topics/categories`
2. `GET /subscriptions/topics?category=...` or `GET /subscriptions/topics?q=...`
3. Subscribe action:
   - Existing topic: `POST /subscriptions/subscribe`
   - Keyword topic: `POST /subscriptions/subscribe/keyword`
4. Management page:
   - `GET /subscriptions/me`
   - Single edit: `PATCH /subscriptions/me/{topic_id}`
   - Batch sort: `PUT /subscriptions/me/reorder`
   - Remove: `DELETE /subscriptions/unsubscribe/{topic_id}`
