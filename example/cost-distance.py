def cost_fun_generator():
    def cost_fun(u, v, d):
        return d.get("length", None)

    return cost_fun
