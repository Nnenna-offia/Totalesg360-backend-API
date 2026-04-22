GRI_305 = {
    "framework": "GRI",
    "requirements": [
        {
            "code": "GRI_305_1",
            "title": "Direct (Scope 1) GHG emissions",
            "pillar": "ENV",
            "mandatory": True,
        },
        {
            "code": "GRI_305_2",
            "title": "Scope 2 emissions",
            "pillar": "ENV",
            "mandatory": True,
        },
        {
            "code": "GRI_305_3",
            "title": "Scope 3 emissions",
            "pillar": "ENV",
            "mandatory": True,
        },
    ],
    "indicators": [
        {
            "code": "SCOPE_1",
            "name": "Scope 1 Emissions",
            "unit": "tCO2e",
            "pillar": "ENV",
            "collection_method": "activity",
        },
        {
            "code": "SCOPE_2",
            "name": "Scope 2 Emissions",
            "unit": "tCO2e",
            "pillar": "ENV",
            "collection_method": "activity",
        },
        {
            "code": "SCOPE_3",
            "name": "Scope 3 Emissions",
            "unit": "tCO2e",
            "pillar": "ENV",
            "collection_method": "derived",
        },
    ],
    "mapping": [
        ("GRI_305_1", "SCOPE_1"),
        ("GRI_305_2", "SCOPE_2"),
        ("GRI_305_3", "SCOPE_3"),
    ],
}
