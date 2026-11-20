import numpy as np
import pytest

from basketball_ai.court import CourtSpec, homography, shot_value, to_court


def test_homography_recovers_a_known_mapping() -> None:
    true_h = np.array([[0.05, 0.01, -2.0], [0.002, 0.06, -1.0], [0.0001, 0.0002, 1.0]])
    image = [(100.0, 80.0), (900.0, 90.0), (950.0, 600.0), (60.0, 620.0), (500.0, 300.0)]

    def apply(p: tuple[float, float]) -> tuple[float, float]:
        x, y, w = true_h @ np.array([p[0], p[1], 1.0])
        return (x / w, y / w)

    court = [apply(p) for p in image]
    h = homography(image, court)
    for img_pt, court_pt in zip(image, court, strict=True):
        assert to_court(h, img_pt) == pytest.approx(court_pt, abs=1e-6)


def test_homography_needs_four_points() -> None:
    with pytest.raises(ValueError):
        homography([(0, 0)] * 3, [(0, 0)] * 3)


@pytest.mark.parametrize(
    ("spot", "value"),
    [
        ((5.25 + 24.5, 25.0), 3),  # top of the key, behind the arc
        ((5.25 + 20.0, 25.0), 2),  # inside the arc
        ((3.0, 25.0 + 23.0), 3),  # left corner, behind the 22 ft line
        ((3.0, 25.0 + 21.0), 2),  # left corner, inside
        ((94 - 5.25 - 24.5, 25.0), 3),  # the other basket
        ((5.25 + 23.75, 25.0), 2),  # exactly on the line counts as 2
    ],
)
def test_shot_value_uses_the_three_point_line(spot: tuple[float, float], value: int) -> None:
    assert shot_value(spot) == value


def test_line_distance_is_configurable_per_gym() -> None:
    fiba = CourtSpec(length=91.86, width=49.21, three_point_radius=22.15, corner_three_distance=21.65)
    assert shot_value((5.25 + 23.0, 49.21 / 2), fiba) == 3
