# Layer 1 Quick Start Guide

## What is Layer 1?

Layer 1 implements **enterprise-grade hierarchical organization structures** for multi-entity ESG reporting.

It allows your organization to model complex corporate hierarchies:
- **Groups** (corporate parents)
- **Subsidiaries** (business units)
- **Facilities** (operating sites)
- **Departments** (divisions)

## Installation

### 1. Apply Migration

```bash
python manage.py migrate organizations
```

This creates the `parent` FK field and `organization_type` field on the Organization model with appropriate indexes.

### 2. Verify Installation

```bash
# Check migration applied
python manage.py showmigrations organizations

# Run tests
pytest src/organizations/tests/test_hierarchy.py
```

## Basic Usage

### Create Organization Hierarchy

```python
from organizations.models import Organization
from organizations.services.organization_hierarchy import create_subsidiary

# Create parent group
tgi_group = Organization.objects.create(
    name="TGI Group",
    sector="manufacturing",
    country="NG",
    organization_type=Organization.OrganizationType.GROUP
)

# Create subsidiary
wacot = create_subsidiary(
    parent_organization=tgi_group,
    name="WACOT Rice Limited",
    sector="manufacturing",
    country="NG",
    organization_type="subsidiary"
)

# Create facility under subsidiary
facility = create_subsidiary(
    parent_organization=wacot,
    name="Abakaliki Production Facility",
    sector="manufacturing",
    country="NG",
    organization_type="facility"
)
```

### Query Hierarchy

```python
from organizations.selectors.organization_hierarchy import (
    get_organization_tree,
    get_organization_descendants,
    get_organization_statistics
)

# Get complete tree
tree = get_organization_tree(tgi_group)
print(tree)
# Output:
# {
#   "id": "...",
#   "name": "TGI Group",
#   "subsidiaries": [
#     {
#       "id": "...",
#       "name": "WACOT Rice Limited",
#       "subsidiaries": [...]
#     }
#   ]
# }

# Get all descendants
all_orgs = get_organization_descendants(tgi_group, include_self=False)
for org in all_orgs:
    print(f"- {org.name} ({org.organization_type})")

# Get statistics
stats = get_organization_statistics(tgi_group)
print(f"Total entities: {stats['total_descendants']}")
print(f"Hierarchy depth: {stats['hierarchy_depth']}")
```

## API Endpoints

### Get Hierarchy Tree

```bash
curl -X GET "http://localhost:8000/api/v1/organizations/hierarchy/" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "X-ORG-ID: UUID"
```

### List Direct Subsidiaries

```bash
curl -X GET "http://localhost:8000/api/v1/organizations/subsidiaries/" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "X-ORG-ID: UUID"
```

### Create Subsidiary

```bash
curl -X POST "http://localhost:8000/api/v1/organizations/subsidiaries/" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "X-ORG-ID: UUID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Subsidiary",
    "sector": "manufacturing",
    "country": "NG",
    "organization_type": "subsidiary"
  }'
```

### Get Hierarchy Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/organizations/statistics/" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "X-ORG-ID: UUID"
```

## Model Features

### Properties

```python
org = Organization.objects.get(id="...")

# Get hierarchy level (0=root, 1=child, 2=grandchild, etc.)
level = org.hierarchy_level

# Get parent chain
ancestors = org.get_ancestors()  # Returns list

# Get all descendants
descendants = org.get_descendants(include_self=False)  # Returns list

# Direct children
children = org.subsidiaries.all()  # Via reverse relationship
```

### Organization Types

```python
class OrganizationType(models.TextChoices):
    GROUP = "group"  # Parent company
    SUBSIDIARY = "subsidiary"  # Business unit
    FACILITY = "facility"  # Operating site
    DEPARTMENT = "department"  # Division
```

## Common Tasks

### Task 1: Get All Organizations in a Hierarchy

```python
from organizations.selectors.organization_hierarchy import (
    get_organization_descendants
)

parent = Organization.objects.get(name="TGI Group")
all_orgs = get_organization_descendants(parent, include_self=True)
print(f"Total: {len(all_orgs)}")
```

### Task 2: Filter by Type

```python
facilities = get_organization_descendants(
    parent,
    organization_types=["facility"]
)
```

### Task 3: Get Parent Organization

```python
from organizations.selectors.organization_hierarchy import get_root_organization

subsidiary = Organization.objects.get(name="WACOT Rice Limited")
root = get_root_organization(subsidiary)
print(f"Root: {root.name}")  # Output: "TGI Group"
```

### Task 4: Move Organization to Different Parent

```python
from organizations.services.organization_hierarchy import move_subsidiary

wacot = Organization.objects.get(name="WACOT Rice Limited")
new_parent = Organization.objects.get(name="Different Group")

move_subsidiary(wacot, new_parent)
```

### Task 5: Get Hierarchy Metrics

```python
from organizations.selectors.organization_hierarchy import (
    get_organization_statistics
)

stats = get_organization_statistics(tgi_group)
print(f"Organization: {stats['organization_name']}")
print(f"Total descendants: {stats['total_descendants']}")
print(f"Direct children: {stats['direct_children']}")
print(f"Max depth: {stats['hierarchy_depth']}")
print(f"Type breakdown: {stats['type_breakdown']}")
```

## Permissions

To manage hierarchy, users need the `organization.manage_hierarchy` capability.

### Check Permission

```python
if user.has_capability("organization.manage_hierarchy"):
    # Can create/update/delete subsidiaries
else:
    # Read-only access
```

## Error Handling

### Circular Reference Prevention

```python
# This will raise ValueError
from organizations.services.organization_hierarchy import move_subsidiary

try:
    move_subsidiary(parent, child)  # Child → Parent (circular!)
except ValueError as e:
    print(f"Error: {e}")  # "Cannot move - would create circular reference"
```

### Invalid Organization Type

```python
try:
    org = Organization.objects.create(
        name="Test",
        organization_type="invalid_type"  # ❌ Not in choices
    )
except ValidationError:
    print("Invalid organization type")
```

## Testing

### Unit Tests

```bash
# Run all hierarchy tests
pytest src/organizations/tests/test_hierarchy.py

# Run specific test class
pytest src/organizations/tests/test_hierarchy.py::OrganizationHierarchyModelTests

# With coverage report
pytest --cov=organizations.models --cov=organizations.selectors \
       --cov=organizations.services src/organizations/tests/test_hierarchy.py
```

### Integration Tests

```python
# Create test data
@pytest.fixture
def org_hierarchy():
    group = Organization.objects.create(
        name="Test Group",
        organization_type="group"
    )
    sub = Organization.objects.create(
        name="Test Subsidiary",
        parent=group,
        organization_type="subsidiary"
    )
    return group, sub

def test_hierarchy_navigation(org_hierarchy):
    group, sub = org_hierarchy
    assert sub.parent == group
    assert sub in group.subsidiaries.all()
```

## Next Steps

1. **Review Full Documentation**: Read [LAYER1_ENTERPRISE_HIERARCHY.md](docs/LAYER1_ENTERPRISE_HIERARCHY.md)
2. **Explore Examples**: Check [test_hierarchy.py](src/organizations/tests/test_hierarchy.py) for detailed examples
3. **API Testing**: Use Postman collection to test endpoints
4. **Layer 2**: Implement ESG Score Consolidation

## Files Modified/Created

### New Files
- ✅ `src/organizations/selectors/organization_hierarchy.py` - 15 selector functions
- ✅ `src/organizations/services/organization_hierarchy.py` - 7 service functions
- ✅ `src/organizations/tests/test_hierarchy.py` - Comprehensive tests
- ✅ `docs/LAYER1_ENTERPRISE_HIERARCHY.md` - Full documentation

### Updated Files
- ✅ `src/organizations/models/organization.py` - Added hierarchy fields and methods
- ✅ `src/organizations/migrations/0010_add_organization_hierarchy.py` - Database schema
- ✅ `src/organizations/api/serializers.py` - 5 new hierarchy serializers
- ✅ `src/organizations/api/views.py` - 4 new hierarchy API views
- ✅ `src/organizations/api/urls.py` - 4 new URL routes

## Support

For issues or questions:
1. Check the test examples: `src/organizations/tests/test_hierarchy.py`
2. Review full API docs: `docs/LAYER1_ENTERPRISE_HIERARCHY.md`
3. Check error messages - they include helpful details

---

**Status**: Production Ready ✅  
**Last Updated**: Current Session  
**Version**: 1.0
