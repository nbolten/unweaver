def cost_fun_generator(G):
    def cost_fun(u, v, d):
        d_rev = G[v][u]
        return d.get("length", None) + d_rev.get("length", None)

    return cost_fun
