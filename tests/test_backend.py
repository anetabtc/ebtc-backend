"""Tests for backend.py."""

from aneta_backend_v2.server.backend import AnetaBackendNode, run_thread, \
    start_multiple_threads


def test_main():
    """Tests main function of backend."""
    # Try running main
    run_thread('a')
    # Test some of the methods
    node = AnetaBackendNode('a')
    assert node.get_erg_tx_info(
        "13dfc58b3dea94d073304ae63dfc36a8ed1c0f74d148e8403132f6db3e9716f0")
    assert node.get_btc_tx_info(
        "ebb35eeb7c838536846498625fe8795f3cce6f4b6b5a16834aa4e9cb3fa77a01",
        network='testnet')
    # Test threading
    assert start_multiple_threads(["test1", "test2", "test3"], print)
