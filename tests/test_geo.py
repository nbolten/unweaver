from shapely.geometry import LineString

from unweaver.geo import cut


def test_cut():
    ls = LineString(((0, 0), (0, 1)))

    l1, l2 = cut(ls, 0.5)

    assert len(l1) == 2
    assert len(l2) == 2

    assert l1[0][0] == 0
    assert l1[0][1] == 0
    assert l1[1][0] == 0
    assert l1[1][1] == 0.5

    assert l2[0][0] == 0
    assert l2[0][1] == 0.5
    assert l2[1][0] == 0
    assert l2[1][1] == 1

    ls1 = LineString(l1)
    ls2 = LineString(l2)
    assert ls1.length == 0.5
    assert ls2.length == 0.5
