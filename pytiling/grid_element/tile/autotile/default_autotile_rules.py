import json
from itertools import chain
from .autotile_rule import get_rule_group, AutotileRule
import os

# Load the autotile forms
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "default_autotile_forms.json")
with open(file_path, "r") as file:
    autotile_forms = json.load(file)

# Load the autotile rules
rules_path = os.path.join(script_dir, "default_autotile_rules.json")
with open(rules_path, "r") as file:
    autotile_rules = json.load(file)

# Generate the default_rules list dynamically
default_rules = list(
    chain.from_iterable(
        get_rule_group(
            autotile_forms[rule["type"]],
            tuple(rule["position"]),
            amount=rule.get("amount", 4),
        )
        for rule in autotile_rules["rule_groups"]
    )
) + [
    AutotileRule(autotile_forms[lone_rule["type"]], tuple(lone_rule["position"]))
    for lone_rule in autotile_rules["lone_rules"]
]

# import json
# from itertools import chain
# from .autotile_rule import get_rule_group
# from .autotile_rule import AutotileRule
# import os


# script_dir = os.path.dirname(os.path.abspath(__file__))
# file_path = os.path.join(script_dir, "default_autotile_forms.json")
# with open(file_path, "r") as file:
#     autotile_forms = json.load(file)

# default_rules = list(
#     chain.from_iterable(
#         [
#             get_rule_group(autotile_forms["outer_corner"], (1, 0)),
#             get_rule_group(autotile_forms["inner_corner"], (3, 0)),
#             get_rule_group(autotile_forms["thin_t_junction"], (5, 0)),
#             get_rule_group(autotile_forms["t_junction"], (7, 0)),
#             get_rule_group(autotile_forms["straight"], (1, 2)),
#             get_rule_group(autotile_forms["edge"], (3, 2)),
#             get_rule_group(autotile_forms["thin_corner"], (5, 2)),
#             get_rule_group(autotile_forms["d_junction"], (7, 2)),
#             get_rule_group(autotile_forms["b_junction"], (9, 2)),
#             get_rule_group(autotile_forms["fish_junction"], (9, 0)),
#             get_rule_group(autotile_forms["straight_thin"], (11, 2), amount=2),
#             get_rule_group(autotile_forms["diagonal_junction"], (11, 0), amount=2),
#         ]
#     )
# ) + [
#     AutotileRule(autotile_forms["lone"], (0, 1)),
#     AutotileRule(autotile_forms["cross"], (0, 2)),
#     AutotileRule(autotile_forms["center"], (0, 3)),
# ]
