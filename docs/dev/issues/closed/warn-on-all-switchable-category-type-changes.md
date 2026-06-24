# 72. Warn on All Switchable-Category Type Changes

Closed by
[`switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md).
Type-change warnings now run through owner `_swap_<name>` hooks, so
every category-owned selector assignment has a uniform owner-mediated
place to warn about values that will be discarded.
