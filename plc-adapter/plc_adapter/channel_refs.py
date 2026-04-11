from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlcTagChannelRef:
    raw: str
    controller_id: str
    path: str

    @property
    def segments(self) -> list[str]:
        return [segment for segment in self.path.split("/") if segment]

    def to_dict(self) -> dict[str, object]:
        return {
            "raw": self.raw,
            "scheme": "plc_tag",
            "controller_id": self.controller_id,
            "path": self.path,
            "segments": self.segments,
        }


def parse_plc_tag_ref(raw: str) -> PlcTagChannelRef:
    prefix = "plc_tag://"
    if not raw.startswith(prefix):
        raise ValueError(f"unsupported channel ref scheme: {raw}")

    remainder = raw[len(prefix) :]
    if "/" not in remainder:
        raise ValueError(f"channel ref must contain controller and path: {raw}")

    controller_id, path = remainder.split("/", 1)
    if not controller_id:
        raise ValueError(f"channel ref missing controller_id: {raw}")
    if not path:
        raise ValueError(f"channel ref missing path: {raw}")
    return PlcTagChannelRef(raw=raw, controller_id=controller_id, path=path)
