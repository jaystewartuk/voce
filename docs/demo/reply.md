## Why the cache misses

The cache key ignores the **query string**, so `/search?q=a` and `/search?q=b` share one entry. Add the query to the key, and keep the TTL short while you test.

```python
def cache_key(request):
    # Include the query string, sorted so ?a=1&b=2 matches ?b=2&a=1
    query = "&".join(sorted(request.query.split("&")))
    return f"{request.path}?{query}"
```

| Request | Before | After |
|---|---|---|
| `/search?q=a` | hit | miss |
| `/search?q=b` | hit (wrong) | miss |

- [x] Reproduce it with two queries
- [ ] Ship the fix behind a flag
