def cost_fun_generator(G, avoidCurbs=True, uphill=0.083, downhill=-0.1):
    def cost_fun(u, v, d):
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
