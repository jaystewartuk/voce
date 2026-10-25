"""How Python reads: a line of code and exactly how it should sound, by the Python reference's names."""

from __future__ import annotations

import pytest

from voce.speech import spoken_line

LINES = [
    # a lambda's colon is what it returns; a block's colon after a slice; an f-string's symbols between its fields
    ("self._backward = lambda: None", "self dot backward equals lambda returns None"),
    ("rows.sort(key=lambda r: r[1])", "rows dot sort key equals lambda r returns r 1"),
    ("if xs[1:2]: pass", "if xs 1 colon 2, pass"),
    ("out = Value(self.data**other, (self,), f'**{other}')",
     "out equals Value self dot data to the power of other, self, f string double star other"),
    ("x = y  # 0-9", "x equals y, 0-9"),
    # operators, by the reference's names
    ("def f(x: int) -> str:", "def f x colon int returns string"),
    ("area = side ** 2", "area equals side to the power of 2"),
    ("half = n // 2", "half equals n floor divided by 2"),
    ("while chunk := f.read(8192):", "while chunk assignment expression f dot read 8192"),
    ("result = weights @ inputs", "result equals weights at inputs"),
    ("@property", "at property"),
    ("q = ~Q(pk=1) | Q(name=\"x\")", "q equals invert Q P K equals 1 or Q name equals x"),
    ("both = seen & wanted", "both equals seen and wanted"),
    ("toggled = a ^ b", "toggled equals a exclusive or b"),
    ("value: str | None = None", "value colon string or None equals None"),
    ("n = n >> 2", "n equals n right shift 2"),
    ("n >>= 1", "n right shift equals 1"),
    ("n %= 3", "n modulo equals 3"),
    ("m @= w", "m at equals w"),
    ("s |= other", "s or equals other"),
    ("s &= other", "s and equals other"),
    ("s ^= other", "s exclusive or equals other"),
    ("def stub(self): ...", "def stub self, ellipsis"),
    ("handler: Callable[..., None]", "handler colon Callable ellipsis, None"),
    ("return []", "return empty list"),
    ("d.setdefault(k, []).append(v)", "d dot set default k, empty list dot append v"),
    # keywords, built-ins and special methods
    ("del self._cache[key]", "delete self dot cache key"),
    ("nonlocal count", "non local count"),
    ("if not hasattr(self, \"label\") and not issubclass(cls, Base):",
     "if not has attribute self, label and not is subclass class, Base"),
    ("def __repr__(self):", "def dunder repper self"),
    ("def __getitem__(self, key):", "def dunder get item self, key"),
    ("def __lt__(self, other):", "def dunder less than self, other"),
    ("if s.startswith(\"x\") or s.endswith(\"y\"):", "if s dot starts with x or s dot ends with y"),
    ("sys.stdout.write(msg)", "sys dot standard out dot write message"),
    # the standard library and the short names of Python code bases
    ("delta = datetime.now() - timedelta(days=1)", "delta equals date time dot now minus time delta days equals 1"),
    ("@functools.lru_cache(maxsize=None)", "at func tools dot L R U cache max size equals None"),
    ("lhs, rhs = self.process_lhs(compiler, connection)",
     "L H S, R H S equals self dot process L H S compiler, connection"),
    ("qs = Model.objects.filter(pk=pk)", "query set equals Model dot objects dot filter P K equals P K"),
    ("opts = self.model._meta", "options equals self dot model dot meta"),
]


@pytest.mark.parametrize("line, spoken", LINES)
def test_python_line(line, spoken):
    assert spoken_line(line, "python") == spoken


# The tokeniser does not know these operators yet: << is read as two less-thans, and //= as // then =.
@pytest.mark.parametrize("line, spoken", [
    ("n = n << 2", "n equals n left shift 2"),
    ("n <<= 1", "n left shift equals 1"),
    ("n //= 2", "n floor divided equals 2"),
])
def test_python_operators_the_tokeniser_does_not_know_yet(line, spoken):
    assert spoken_line(line, "python") == spoken
