import os
from ...rule_factory import create_autotile_rules_from_json

script_dir = os.path.dirname(os.path.abspath(__file__))

forms_path = os.path.join(script_dir, "detailed_autotile_forms.json")
rules_definition_path = os.path.join(script_dir, "detailed_rules.json")

# Generate the detailed_rules list dynamically
detailed_rules = create_autotile_rules_from_json(
    forms_path=forms_path,
    rules_path=rules_definition_path,
)
