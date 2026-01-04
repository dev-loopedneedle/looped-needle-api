# Expression Evaluator Options Analysis

## Your Requirements

Based on your examples, you need to support:

1. **Nested object access**: `context.company_size`, `scope.season`
2. **Array operations**: `.some()`, `.includes()`, arrow functions
3. **Boolean logic**: `&&`, `||`
4. **Comparisons**: `==`, `!=`, `<`, `>`

Example expressions:
```javascript
// Complex array operations
context.products.some(p => p.materials_composition.some(m => m.material == 'Leather'))

// Array includes
context.target_markets.includes('EU')

// Simple comparisons
context.company_size == 'Large' && scope.has_wet_processing == true
```

## Option Comparison

### 1. **JEXL from GitHub** (Original Plan)
**Installation**: `pip install git+https://github.com/mozilla/python-jexl.git`

**Pros**:
- ✅ Official Mozilla JEXL port
- ✅ Supports JEXL syntax natively
- ✅ Well-maintained
- ✅ Error handling built-in

**Cons**:
- ❌ Not on PyPI (requires git install)
- ❌ Adds deployment complexity
- ❌ May need to add to requirements.txt separately

**Best for**: If you need exact JEXL syntax compatibility

---

### 2. **simpleeval** (Current Fallback)
**Installation**: `pip install simpleeval` ✅ Already installed

**Pros**:
- ✅ Available on PyPI
- ✅ Safe (no code execution)
- ✅ Simple and lightweight
- ✅ Good for basic expressions

**Cons**:
- ❌ Doesn't support `.some()`, `.includes()`, arrow functions
- ❌ Limited to Python-like syntax
- ❌ No array method helpers

**Best for**: Simple expressions like `context.company_size == 'Large'`

---

### 3. **Custom ExpressionEvaluator** (Recommended ✅)
**Implementation**: Created in `src/inference/expression_evaluator.py`

**Pros**:
- ✅ Uses `simpleeval` as base (safe, available)
- ✅ Adds helper functions for complex operations
- ✅ Python-like syntax (familiar to your team)
- ✅ Easy to extend with more helpers
- ✅ No external git dependencies

**Cons**:
- ⚠️ Requires translating JS-style expressions to Python-style
- ⚠️ Need to document helper functions

**Best for**: Your use case - balances flexibility with simplicity

**Expression Translation Guide**:
```python
# JavaScript/JEXL style → Python style

# Array some() with nested check
context.products.some(p => p.materials_composition.some(m => m.material == 'Leather'))
→ has_material(context.products, 'Leather')

# Array includes
context.target_markets.includes('EU')
→ 'EU' in context.target_markets

# Boolean operators
context.company_size == 'Large' && scope.has_wet_processing == True
→ context.company_size == 'Large' and scope.has_wet_processing == True
```

**Available Helper Functions**:
- `has_material(products, material_type)` - Check if any product has material
- `contains(items, value)` - Check if value in list
- `any_match(items, field, value)` - Check if any item matches

---

### 4. **Field Mapping** (Not Recommended)
**What it is**: Pre-defined mappings for common conditions

**Pros**:
- ✅ Very simple
- ✅ Type-safe
- ✅ Fast

**Cons**:
- ❌ Not flexible
- ❌ Can't handle dynamic expressions
- ❌ Requires code changes for new rules

**Best for**: Very simple, fixed rule sets

---

## Recommendation

**Use Option 3: Custom ExpressionEvaluator** ✅

**Why**:
1. **Available now**: Uses `simpleeval` which is already installed
2. **Flexible**: Can add more helper functions as needed
3. **Safe**: Built on `simpleeval` which prevents code injection
4. **Maintainable**: Python syntax is familiar to your team
5. **No deployment issues**: No git dependencies

**Migration Path**:
1. Start with `ExpressionEvaluator` (already implemented)
2. Add helper functions as you discover common patterns
3. If you later need exact JEXL syntax, you can add JEXL from GitHub as an option

**If you need JEXL later**:
- Add to `pyproject.toml` optional dependencies
- Or install manually: `pip install git+https://github.com/mozilla/python-jexl.git`
- The code already supports both (JEXL if available, ExpressionEvaluator as fallback)

---

## Implementation Status

✅ **ExpressionEvaluator** created in `src/inference/expression_evaluator.py`
✅ **RuleEvaluator** updated to use ExpressionEvaluator as fallback
✅ **Helper functions** added: `has_material()`, `contains()`, `any_match()`

## Next Steps

1. Test with sample expressions
2. Add more helper functions as needed
3. Document expression syntax for rule creators
4. Consider adding JEXL from GitHub if exact syntax is required
