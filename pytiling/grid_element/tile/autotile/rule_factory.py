import json
from itertools import chain
from typing import Any

from .autotile_rule import AutotileRule, get_rule_group


def create_autotile_rules_from_json(
    forms_path: str, rules_path: str
) -> list[AutotileRule]:
    """
    Generates a list of AutotileRule objects from JSON definition files.

    Args:
        forms_path (str): The absolute path to the JSON file defining autotile forms.
        rules_path (str): The absolute path to the JSON file defining autotile rules.

    Returns:
        list[AutotileRule]: A list of generated AutotileRule instances.
    """
    with open(forms_path, "r") as file:
        autotile_forms: dict[str, Any] = json.load(file)

    with open(rules_path, "r") as file:
        autotile_rules: dict[str, Any] = json.load(file)

    # Generate rules from rule groups
    rule_groups = list(
        chain.from_iterable(
            get_rule_group(
                autotile_forms[rule["type"]],
                tuple(rule["position"]),
                amount=rule.get("amount", 4),
            )
            for rule in autotile_rules.get("rule_groups", [])
        )
    )

    # Generate rules from lone rules
    lone_rules = [
        AutotileRule(autotile_forms[rule["type"]], tuple(rule["position"]))
        for rule in autotile_rules.get("lone_rules", [])
    ]

    return rule_groups + lone_rules
