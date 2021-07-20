from typing import Any, Dict


def cost_fun_generator(
    avoidCurbs: bool = True, uphill: float = 0.083, downhill: float = -0.1
):
    def cost_fun(u: str, v: str, d: Dict[str, Any]):
        # No curb ramps? No route
        if d["footway"] == "crossing" and not d["curbramps"]:
            return None
        # Too steep?
        if d["incline"] is not None:
            if d["incline"] > uphill or d["incline"] < downhill:
                return None

        if d["length"] is None:
            return 0
        return d["length"]

    return cost_fun
