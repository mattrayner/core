"""Generate ssdp file."""
from collections import OrderedDict, defaultdict
import json
from typing import Dict

from .model import Config, Integration

BASE = """
\"\"\"Automatically generated by hassfest.

To update, run python3 -m script.hassfest
\"\"\"

# fmt: off

SSDP = {}
""".strip()


def sort_dict(value):
    """Sort a dictionary."""
    return OrderedDict((key, value[key]) for key in sorted(value))


def generate_and_validate(integrations: Dict[str, Integration]):
    """Validate and generate ssdp data."""

    data = defaultdict(list)

    for domain in sorted(integrations):
        integration = integrations[domain]

        if not integration.manifest:
            continue

        ssdp = integration.manifest.get("ssdp")

        if not ssdp:
            continue

        try:
            with open(str(integration.path / "config_flow.py")) as fp:
                content = fp.read()
                if (
                    " async_step_ssdp" not in content
                    and "AbstractOAuth2FlowHandler" not in content
                    and "register_discovery_flow" not in content
                ):
                    integration.add_error("ssdp", "Config flow has no async_step_ssdp")
                    continue
        except FileNotFoundError:
            integration.add_error(
                "ssdp", "SSDP info in a manifest requires a config flow to exist"
            )
            continue

        for matcher in ssdp:
            data[domain].append(sort_dict(matcher))

    return BASE.format(json.dumps(data, indent=4))


def validate(integrations: Dict[str, Integration], config: Config):
    """Validate ssdp file."""
    ssdp_path = config.root / "homeassistant/generated/ssdp.py"
    config.cache["ssdp"] = content = generate_and_validate(integrations)

    with open(str(ssdp_path)) as fp:
        if fp.read().strip() != content:
            config.add_error(
                "ssdp",
                "File ssdp.py is not up to date. Run python3 -m script.hassfest",
                fixable=True,
            )
        return


def generate(integrations: Dict[str, Integration], config: Config):
    """Generate ssdp file."""
    ssdp_path = config.root / "homeassistant/generated/ssdp.py"
    with open(str(ssdp_path), "w") as fp:
        fp.write(f"{config.cache['ssdp']}\n")
