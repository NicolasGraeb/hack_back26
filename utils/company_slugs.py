"""Slug → id firmy (logo w c_logo: {slug}_{id}.ext)."""

# Oba Reviver mają ten sam slug, rozróżnia id: reviver_4 vs reviver_9
SLUG_BY_COMPANY_ID: dict[int, str] = {
    1: "cloudara",
    2: "digmio",
    3: "polionix",
    4: "reviver",
    5: "zentatez",
    6: "innovacini",
    7: "magnerin",
    8: "bully",
    9: "reviver",
    10: "lynkers",
}
