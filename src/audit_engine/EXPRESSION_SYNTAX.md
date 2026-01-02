# Expression Syntax Guide

## Overview

The audit engine uses a custom `ExpressionEvaluator` that supports Python-like expressions with helper functions for common operations.

## Basic Syntax

### Nested Object Access
```python
# Access nested properties
context.company_size == 'Large'
scope.season == 'SS24'
context.brand.name == 'MyBrand'
```

### Boolean Logic
```python
# Use Python operators: and, or, not
context.company_size == 'Large' and scope.has_wet_processing == True
context.target_markets or scope.audit_type == 'full'
not context.is_small_brand
```

### Comparisons
```python
# Standard comparison operators
context.company_size == 'Large'
scope.score > 50
context.product_count >= 10
scope.depth != 'shallow'
```

### List/Array Operations
```python
# Check if value is in list
'EU' in context.target_markets
'Leather' in scope.materials

# Or use helper function
contains(context.target_markets, 'EU')
```

## Helper Functions

### `has_material(products, material_type)`
Check if any product contains the specified material.

**Example:**
```python
has_material(context.products, 'Leather')
```

**Equivalent to:**
```javascript
context.products.some(p => p.materials_composition.some(m => m.material == 'Leather'))
```

### `contains(items, value)`
Check if value exists in list.

**Example:**
```python
contains(context.target_markets, 'EU')
```

**Equivalent to:**
```javascript
context.target_markets.includes('EU')
```

### `any_match(items, field, value)`
Check if any item in list has field == value.

**Example:**
```python
any_match(context.products, 'category', 'Apparel')
```

**Equivalent to:**
```javascript
context.products.some(p => p.category == 'Apparel')
```

### `all_match(items, field, value)`
Check if all items in list have field == value.

**Example:**
```python
all_match(context.products, 'category', 'Apparel')
```

**Equivalent to:**
```javascript
context.products.every(p => p.category == 'Apparel')
```

### `has_supply_chain_role(nodes, role)`
Check if any supply chain node has the specified role.

**Example:**
```python
has_supply_chain_role(context.supply_chain_nodes, 'CutAndSew')
```

**Equivalent to:**
```javascript
context.supply_chain_nodes.some(n => n.role == 'CutAndSew')
```

### `has_supply_chain_in_country(nodes, country)`
Check if any supply chain node is in the specified country.

**Example:**
```python
has_supply_chain_in_country(context.supply_chain_nodes, 'CN')
```

**Equivalent to:**
```javascript
context.supply_chain_nodes.some(n => n.country == 'CN')
```

### `count_match(items, field, value)`
Count items in list where field == value.

**Example:**
```python
count_match(context.products, 'category', 'Apparel') > 5
```

## Complex Examples

### Example 1: Material Check
```python
# Check if brand has leather products
has_material(context.products, 'Leather') and context.company_size == 'Large'
```

### Example 2: Market and Processing
```python
# Check EU market and wet processing
'EU' in context.target_markets and scope.has_wet_processing == True
```

### Example 3: Supply Chain Depth
```python
# Check supply chain depth and country
has_supply_chain_in_country(context.supply_chain_nodes, 'CN') and scope.supply_chain_depth == 'full_chain'
```

### Example 4: Multiple Conditions
```python
# Complex condition with multiple checks
(context.company_size == 'Large' or context.company_size == 'SME') and \
has_material(context.products, 'Cotton') and \
'EU' in context.target_markets
```

## Context Structure

### Brand Context (`context`)
```python
{
    "brand": {
        "id": "...",
        "name": "...",
        "registration_country": "...",
        "company_size": "Micro|SME|Large",
        "target_markets": ["EU", "US", ...]
    },
    "products": [
        {
            "id": "...",
            "name": "...",
            "category": "...",
            "materials_composition": [
                {"material_type": "Cotton", "percentage": 80},
                {"material_type": "Polyester", "percentage": 20}
            ],
            "manufacturing_processes": ["CutAndSew", ...]
        }
    ],
    "supply_chain_nodes": [
        {
            "id": "...",
            "role": "CutAndSew|FabricMill|...",
            "country": "CN|BD|...",
            "tier_level": 1
        }
    ]
}
```

### Scope (`scope`)
Questionnaire responses - structure depends on questionnaire definition.

## Error Handling

Invalid expressions will:
1. Return `(False, error_message)`
2. Log the error with expression details
3. Continue processing other rules (partial success)

## Tips

1. **Use helper functions** for complex array operations
2. **Use `in` operator** for simple list membership checks
3. **Use `and`/`or`** instead of `&&`/`||`
4. **Access nested properties** with dot notation
5. **Test expressions** before adding to rules

## Migration from JavaScript/Other Languages

If you have JavaScript or other language expressions, translate them:

| JavaScript | Python |
|------------|--------|
| `&&` | `and` |
| `\|\|` | `or` |
| `.includes()` | `in` or `contains()` |
| `.some()` | `any_match()` or helper function |
| `.every()` | `all_match()` |
| Arrow functions | Helper functions |

