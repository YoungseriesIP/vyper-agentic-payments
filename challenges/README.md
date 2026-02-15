# Hackathon Challenges

Build on Circle's Vyper agentic payment contracts using the `circlekit` Python SDK.

## Setup

```bash
# From the repo root
pip install -e .
pip install -e ../circle-titanoboa-sdk
pip install -e ".[integration]"
```

## Challenges

| # | Name | Difficulty | Contract | What You Build |
|---|------|-----------|----------|----------------|
| 1 | Agent Identity | Easy | `AgentIdentity.vy` | Register an agent with `registerAgent()` |
| 2 | Reputation Feedback | Medium | `AgentReputation.vy` | Record interaction + submit feedback with `submitFeedback()` |
| 3 | Escrow Task | Medium-Hard | `AgentEscrow.vy` | Create a task with `createTask()` + approve with `approveCompletion()` |
| 4 | Spending Limits | Hard | `SpendingLimiter.vy` | Authorize an agent and call `spend()` with 3-tier limits |

## How It Works

Each challenge has:
- **`challenge.py`** — A template with `TODO` placeholders for you to fill in
- **`README.md`** — Instructions and hints

## Running Tests

```bash
# Run all challenge tests (they FAIL until you complete the TODOs)
pytest tests/test_hackathon_challenges.py -v

# Run a specific challenge
pytest tests/test_hackathon_challenges.py -v -k "challenge_1"
```

## Tips

- Read the contract source in `contracts/` before coding
- Use `boa.env.prank(address)` to impersonate accounts
- Check `tests/conftest.py` for fixture patterns
- The existing test suite (`pytest tests/ -v -m "not integration and not challenge"`) is your reference implementation
