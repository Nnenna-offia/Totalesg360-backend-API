"""Helpers to normalize location payloads.

Functions to transform incoming objects so that settlement/ward/LGA/state
are represented by names rather than nested ids.
"""
from typing import Any, Dict, Optional


def _find_state(node: Optional[Dict[str, Any]]) -> Optional[str]:
    """Walk parent links to find a node that looks like a state and return its name.

    Heuristics: look for keys that indicate hierarchy (`parent`, `parent_location`),
    or a `level`/`type` field equal to 'state'. If none found return None.
    """
    seen = set()
    while node and isinstance(node, dict):
        node_id = id(node)
        if node_id in seen:
            break
        seen.add(node_id)

        # direct state fields
        if node.get("type") == "state" or node.get("level") == "state":
            return node.get("name")
        # common name field
        if node.get("is_state"):
            return node.get("name")

        # try parent pointers
        parent = node.get("parent") or node.get("parent_location") or node.get("parent_loc")
        if not parent:
            # sometimes state may be attached as `state` key directly
            if node.get("state") and isinstance(node.get("state"), dict):
                return node["state"].get("name")
            return None
        node = parent
    return None


def transform_location_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of `item` with normalized location fields:

    - `settlement`: replaced with settlement name if available (settlement.name)
    - `ward`: `location.name`
    - `lga`: `parent_location.name`
    - `state`: inferred from parent chain, if present

    The function is defensive: if a name can't be found it leaves the original
    value (id or dict) so callers can decide how to handle missing data.
    """
    out = item.copy()

    # settlement -> settlement.name
    settlement = item.get("settlement")
    if isinstance(settlement, dict):
        out["settlement"] = settlement.get("name")
    else:
        # if only an id was provided, leave as-is or set to None
        out["settlement"] = settlement

    # ward -> location.name
    location = item.get("location")
    if isinstance(location, dict):
        out["ward"] = location.get("name")
    else:
        out["ward"] = None

    # lga -> parent_location.name
    parent_location = item.get("parent_location")
    if isinstance(parent_location, dict):
        out["lga"] = parent_location.get("name")
    else:
        out["lga"] = None

    # try to infer state from parent chain (look at parent_location first)
    state = _find_state(parent_location) or _find_state(location) or item.get("state")
    out["state"] = state

    return out


# Example usage
if __name__ == "__main__":
    sample = {"id":27,"name":"Cool FM","location":{"id":9130,"name":"City Center 1","code":None},"parent_location":{"id":319,"name":"Municipal Area Council","code":None}}
    print(transform_location_item(sample))
