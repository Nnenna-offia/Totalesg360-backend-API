"""Traceability definitions between input and derived emission indicators."""

INPUT_TO_DERIVED_INDICATOR = {
    "S1-DIESEL-L": "ENV-S1-EMISSIONS-TCO2E",
    "S1-LPG-KG": "ENV-S1-EMISSIONS-TCO2E",
    "S1-NATGAS-M3": "ENV-S1-EMISSIONS-TCO2E",
    "S1-REFRIG-KG": "ENV-S1-EMISSIONS-TCO2E",
    "S2-ELEC-KWH": "ENV-S2-EMISSIONS-TCO2E",
    "S3-FERT-KG": "ENV-S3-EMISSIONS-TCO2E",
    "S3-TRANSPORT-KM": "ENV-S3-EMISSIONS-TCO2E",
    "S3-WASTE-M3": "ENV-S3-EMISSIONS-TCO2E",
    "S3-FEED-KG": "ENV-S3-EMISSIONS-TCO2E",
}


DERIVED_INDICATOR_TO_SCOPE = {
    "ENV-S1-EMISSIONS-TCO2E": "scope1",
    "ENV-S2-EMISSIONS-TCO2E": "scope2",
    "ENV-S3-EMISSIONS-TCO2E": "scope3",
}


def get_derived_indicator_for_input(input_indicator_code: str | None) -> str | None:
    """Return the derived indicator code for a given input indicator code."""
    if not input_indicator_code:
        return None
    return INPUT_TO_DERIVED_INDICATOR.get(input_indicator_code)


def get_expected_scope_code_for_input(input_indicator_code: str | None) -> str | None:
    """Return expected emissions scope code (scope1/2/3) for an input indicator code."""
    derived_code = get_derived_indicator_for_input(input_indicator_code)
    if not derived_code:
        return None
    return DERIVED_INDICATOR_TO_SCOPE.get(derived_code)


def get_supporting_inputs_for_derived(derived_indicator_code: str) -> list[str]:
    """Return input indicator codes that roll up into a derived indicator."""
    return [
        input_code
        for input_code, mapped_derived_code in INPUT_TO_DERIVED_INDICATOR.items()
        if mapped_derived_code == derived_indicator_code
    ]
