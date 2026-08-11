"""Tests for schema->service mappings (WeightsResponse.from_state)."""

from datetime import UTC, datetime

from app.models.schemas import WeightsResponse


class _FakeWeightsState:
    def __init__(
        self,
        public_weight: float,
        real_weight: float,
        real_count: int,
        updated_at=None,
    ) -> None:
        self.public_weight = public_weight
        self.real_weight = real_weight
        self.real_count = real_count
        self.updated_at = updated_at


def test_from_state_maps_all_fields():
    state = _FakeWeightsState(
        public_weight=0.99,
        real_weight=0.01,
        real_count=1,
        updated_at=datetime.now(UTC),
    )
    response = WeightsResponse.from_state(state)

    assert response.public_weight == 0.99
    assert response.real_weight == 0.01
    assert response.real_count == 1
    assert response.updated_at is not None


def test_from_state_maps_initial_state_without_updated_at():
    response = WeightsResponse.from_state(_FakeWeightsState(1.0, 0.0, 0))

    assert response.public_weight == 1.0
    assert response.real_weight == 0.0
    assert response.real_count == 0
    assert response.updated_at is None