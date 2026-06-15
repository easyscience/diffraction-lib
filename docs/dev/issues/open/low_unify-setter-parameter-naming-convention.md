# 73. Unify Setter Parameter Naming Convention

**Priority:** `[priority] low`

**Type:** Code style

Some setters use `new`, others use `value`, others use the attribute
name. For example:

```python
@id.setter
def id(self, new):
    self._id.value = new
```

Agree on a single convention (e.g. always `value`) and apply
consistently.

**Depends on:** nothing.
