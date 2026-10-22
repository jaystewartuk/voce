## How micrograd learns

Every number is a `Value` that remembers the values it was made from, so the gradient can flow back through them. Multiplying two of them sets up the chain rule for that one step:

```python
def __mul__(self, other):
    other = other if isinstance(other, Value) else Value(other)
    out = Value(self.data * other.data, (self, other), '*')

    def _backward():
        self.grad += other.data * out.grad
        other.grad += self.data * out.grad
    out._backward = _backward
    return out
```

| Operation | Local gradient |
|---|---|
| `a + b` | 1 for each |
| `a * b` | the other value |
| `a ** n` | `n * a ** (n - 1)` |

- [x] Read `engine.py` first
- [ ] Then `nn.py`, where the neurons are
