def cost_fun_generator(avoidCurbs=True, uphill=83, downhill=-100):
    uphill = uphill * 1000
    downhill = downhill * 1000

    def cost_fun(u, v, d):
        # No curb ramps? No route
        if "curbramps" in d and not d["curbramps"]:
            return None
        # Too steep?
        if "incline" in d and d["incline"] is not None:
            if d["incline"] > uphill or d["incline"] < downhill:
                return None

        return d.get("length", 0)

    return cost_fun
