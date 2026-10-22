# Code, read aloud

Most readers stumble over code. voce reads it the way a person says it out loud. Listen to this:

```python
def total(prices: list[float]) -> float:
    return sum(p for p in prices if p > 0)
```

And this, in JavaScript:

```javascript
const ready = user?.email !== undefined && items.length >= 1;
```

Operators are named the way each language's own manual names them, so `?.` is "optional chaining", and `!==` is
"not strictly equal to".

Inline code reads naturally too: call `fetch()` with the address, then `await` the answer.
