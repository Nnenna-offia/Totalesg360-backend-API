from django.core.exceptions import ValidationError

from compliance.models import FrameworkRequirement, IndicatorFrameworkMapping
from indicators.models import Indicator
from organizations.models import RegulatoryFramework


def _normalize_collection_method(value: str) -> str:
    raw = (value or "direct").strip().lower()
    if raw == "activity":
        return Indicator.CollectionMethod.ACTIVITY
    if raw in ("direct", "derived"):
        # "derived" is treated as non-manual direct indicator in current schema.
        return Indicator.CollectionMethod.DIRECT
    raise ValidationError(f"Unsupported indicator collection_method: {value}")


def _framework_defaults(framework_data: dict) -> dict:
    return {
        "name": framework_data["name"],
        "jurisdiction": framework_data["jurisdiction"],
        "sector": framework_data.get("sector") or "",
        "description": framework_data.get("description", ""),
        "priority": framework_data.get("priority", 0),
        "is_active": framework_data.get("is_active", True),
        "is_system": framework_data.get("is_system", True),
    }


def seed_framework(framework_data):
    defaults = _framework_defaults(framework_data)
    obj, created = RegulatoryFramework.objects.get_or_create(
        code=framework_data["code"],
        defaults=defaults,
    )

    if not created:
        changed = []
        for key, value in defaults.items():
            if getattr(obj, key) != value:
                setattr(obj, key, value)
                changed.append(key)
        if changed:
            obj.save(update_fields=changed)

    return obj, created


def seed_requirements(framework, requirements):
    result = {}
    for req in requirements:
        defaults = {
            "title": req["title"],
            "description": req.get("description", ""),
            "pillar": req["pillar"],
            "is_mandatory": req.get("mandatory", req.get("is_mandatory", True)),
            "status": req.get("status", FrameworkRequirement.Status.ACTIVE),
            "priority": req.get("priority", 0),
            "guidance_url": req.get("guidance_url", ""),
            "version": req.get("version", ""),
        }

        obj, created = FrameworkRequirement.objects.get_or_create(
            framework=framework,
            code=req["code"],
            defaults=defaults,
        )

        if not created:
            changed = []
            for key, value in defaults.items():
                if getattr(obj, key) != value:
                    setattr(obj, key, value)
                    changed.append(key)
            if changed:
                obj.save(update_fields=changed)

        result[req["code"]] = obj

    return result


def seed_indicators(indicators):
    result = {}
    for ind in indicators:
        defaults = {
            "name": ind["name"],
            "description": ind.get("description", ""),
            "pillar": ind["pillar"],
            "data_type": ind.get("data_type", Indicator.DataType.NUMBER),
            "unit": ind.get("unit"),
            "is_active": ind.get("is_active", True),
            "version": ind.get("version"),
            "collection_method": _normalize_collection_method(ind.get("collection_method", "direct")),
        }

        obj, created = Indicator.objects.get_or_create(
            code=ind["code"],
            defaults=defaults,
        )

        if not created:
            changed = []
            for key, value in defaults.items():
                if getattr(obj, key) != value:
                    setattr(obj, key, value)
                    changed.append(key)
            if changed:
                obj.save(update_fields=changed)

        result[ind["code"]] = obj

    return result


def seed_mapping(framework, requirements, indicators, mapping):
    for order, (req_code, ind_code) in enumerate(mapping, start=1):
        requirement = requirements[req_code]
        indicator = indicators[ind_code]

        IndicatorFrameworkMapping.objects.update_or_create(
            framework=framework,
            requirement=requirement,
            indicator=indicator,
            defaults={
                "mapping_type": IndicatorFrameworkMapping.MappingType.PRIMARY,
                "is_primary": True,
                "coverage_percent": 0,
                "is_active": True,
            },
        )


def _validate_dataset(dataset):
    req_codes = {item["code"] for item in dataset.get("requirements", [])}
    ind_codes = {item["code"] for item in dataset.get("indicators", [])}
    mapping_pairs = dataset.get("mapping", [])

    if not req_codes:
        raise ValidationError(f"Dataset {dataset.get('framework')} has no requirements")
    if not ind_codes:
        raise ValidationError(f"Dataset {dataset.get('framework')} has no indicators")
    if not mapping_pairs:
        raise ValidationError(f"Dataset {dataset.get('framework')} has no requirement/indicator mappings")

    mapped_req_codes = set()
    mapped_ind_codes = set()

    for req_code, ind_code in mapping_pairs:
        if req_code not in req_codes:
            raise ValidationError(f"Mapping references unknown requirement code: {req_code}")
        if ind_code not in ind_codes:
            raise ValidationError(f"Mapping references unknown indicator code: {ind_code}")
        mapped_req_codes.add(req_code)
        mapped_ind_codes.add(ind_code)

    missing_requirements = req_codes.difference(mapped_req_codes)
    missing_indicators = ind_codes.difference(mapped_ind_codes)

    if missing_requirements:
        raise ValidationError(f"Unmapped requirements found: {sorted(missing_requirements)}")
    if missing_indicators:
        raise ValidationError(f"Unmapped indicators found: {sorted(missing_indicators)}")


def seed_dataset(*, framework, dataset):
    _validate_dataset(dataset)

    requirements = seed_requirements(framework, dataset["requirements"])
    indicators = seed_indicators(dataset["indicators"])
    seed_mapping(framework, requirements, indicators, dataset["mapping"])

    return {
        "requirements": len(requirements),
        "indicators": len(indicators),
        "mappings": len(dataset["mapping"]),
    }
