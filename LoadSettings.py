import json


def LoadSettings(filepath: str) -> tuple:
    with open(f"{filepath}\\pressets.json") as f:
        pressets = json.load(f)

    with open(f"{filepath}\\signals.json") as f:
        signals = json.load(f)

    return pressets, signals