import asyncio

from app.broker.mock import MockBrokerAdapter


def test_mock_snapshot_has_product_data():
    snapshot = asyncio.run(MockBrokerAdapter().fetch_snapshot())
    assert len(snapshot.trades) == 42
    assert snapshot.holdings
    assert snapshot.rms["availablecash"] > 0

