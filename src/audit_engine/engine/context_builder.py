"""Context builder for audit instances."""

from typing import Any

from src.audit_engine.models import Brand, Product, SupplyChainNode


def capture_brand_context(
    brand: Brand, products: list[Product], supply_chain_nodes: list[SupplyChainNode]
) -> dict[str, Any]:
    """
    Capture brand context snapshot for audit instance.

    Args:
        brand: Brand model
        products: List of products
        supply_chain_nodes: List of supply chain nodes

    Returns:
        Brand context dictionary
    """
    return {
        "brand": {
            "id": str(brand.id),
            "name": brand.name,
            "registration_country": brand.registration_country,
            "company_size": brand.company_size,
            "target_markets": brand.target_markets,
        },
        "products": [
            {
                "id": str(product.id),
                "name": product.name,
                "category": product.category,
                "materials_composition": product.materials_composition,
                "manufacturing_processes": product.manufacturing_processes,
            }
            for product in products
        ],
        "supply_chain_nodes": [
            {
                "id": str(node.id),
                "role": node.role,
                "country": node.country,
                "tier_level": node.tier_level,
            }
            for node in supply_chain_nodes
        ],
    }

