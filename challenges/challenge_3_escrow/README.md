# Challenge 3: Escrow Task (Medium-Hard)

Create a task with USDC escrow and approve completion using `AgentEscrow.vy`.

## Goal

Fill in `challenge.py` to:
1. Approve USDC spending by the escrow contract
2. Create a task that locks USDC
3. Have a worker claim the task
4. Have the poster approve completion (releasing USDC to worker)

## What You Need to Know

- Tasks lock USDC in escrow until completion
- Task lifecycle: OPEN → CLAIMED → COMPLETED
- Both poster and worker must be registered agents
- The poster calls `createTask()`, worker calls `claimTask()`, poster calls `approveCompletion()`
- USDC uses 6 decimals (1 USDC = 1_000_000)

## Key Functions

```python
# Approve escrow to spend USDC
usdc.approve(escrow.address, amount)

# Create task — locks USDC
task_id = escrow.createTask(poster_agent_id, amount, description_hash, deadline)

# Worker claims task
escrow.claimTask(task_id, worker_agent_id)

# Poster approves — releases USDC to worker
escrow.approveCompletion(task_id)
```

## Hints

- `description_hash` is 32 bytes — use `b'\x01' + b'\x00' * 31`
- `deadline` is relative seconds (e.g., `86400 * 7` for 7 days)
- The poster must `approve()` USDC to the escrow before creating the task
- Use `boa.env.prank(address)` to switch between poster and worker
- Check `tests/test_agent_escrow.py` for more examples
