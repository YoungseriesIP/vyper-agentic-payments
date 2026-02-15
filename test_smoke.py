# test_smoke.py
import boa

def test_vyper_works():
    code = """
# @version ^0.4.0
counter: public(uint256)

@external
def increment():
    self.counter += 1
"""
    contract = boa.loads(code)
    contract.increment()
    assert contract.counter() == 1
