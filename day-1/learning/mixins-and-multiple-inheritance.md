# Mixins and multiple inheritance

Where I met it:
```python
class TimestampMixin:
    """Mixin that adds timezone-aware created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(...)
    updated_at: Mapped[datetime] = mapped_column(...)

class Document(Base, TimestampMixin): ...
class Tenant(Base, TimestampMixin): ...
```

## 1. Multiple inheritance
A Python class can have **more than one parent**:
```python
class Document(Base, TimestampMixin):
    ...
```
`Document` gets everything from both `Base` and `TimestampMixin`. JavaScript classes allow only one parent (`extends`), so people copy methods in with `Object.assign` or write "mixin functions".

## 2. What a mixin is
A **mixin** is a small class that is **not meant to be used alone**. It holds one reusable piece of behaviour or fields, and other classes "mix it in".

- `TimestampMixin` has no table and no meaning by itself.
- Every model that needs `created_at` and `updated_at` lists it as a parent.
- One definition, used by three models: `Tenant`, `User` and `Document`.

Without it, the same two columns would be copied into every model.

## 3. Method Resolution Order (MRO)
When a name could come from several parents, Python searches them in a fixed order, the **MRO**. I can print it:

```python
class Base: pass
class TimestampMixin:
    def stamp(self): return "created_at/updated_at"
class Document(Base, TimestampMixin): pass

print([c.__name__ for c in Document.__mro__])
# ['Document', 'Base', 'TimestampMixin', 'object']
```
- Search order: the class itself, then parents **left to right**, then `object`.
- That is why `Base` is written first: it takes priority if both parents define the same name.
- `super()` follows this same order.

## 4. Rules of thumb
| Rule | Why |
|---|---|
| Put the main base first, mixins after | The main base wins in a name clash |
| Keep a mixin small and focused | Several mixins with overlapping names get confusing |
| A mixin should not need `__init__` arguments | It must combine with any class |
| Prefer **composition** when behaviour is not "is a" | Inheritance for sharing fields/columns is fine; for business logic, hold an object instead |

## 5. Mixin vs the other tools
| Tool | Use when |
|---|---|
| **Mixin** | Many classes need the same fields or small behaviour |
| **Inheritance from one base** | A true "is a" relationship (`JsonStorage` is a `Storage`) |
| **Composition** | One object uses another (`DocumentStore` holds a `Storage`) |
| **Abstract class / Protocol** | I want to define an interface other classes must follow |

## Common mistakes
| Mistake | What happens |
|---|---|
| Mixin first, base second | The mixin can shadow the base's names |
| A mixin with required `__init__` parameters | Combining it breaks the other class's constructor |
| Using a mixin where a plain function would do | Needless complexity |

## Quick check
- What does `class Document(Base, TimestampMixin)` give `Document`?
- What is a mixin, and why is `TimestampMixin` not used alone?
- What does the MRO decide?
- Why is a base class usually listed before the mixins?
