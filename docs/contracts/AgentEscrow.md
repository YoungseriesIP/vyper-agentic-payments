# AgentEscrow.vy

Secure escrow system for agent-to-agent task payments with dispute resolution.

## Overview

This contract holds USDC in escrow while agents complete tasks. It solves the "How do I trust this agent will pay me?" problem.

## Agentic Pattern

In agent-to-agent commerce:

1. Agent A (poster) locks USDC in escrow
2. Agent B (worker) claims and completes the task
3. Resolution paths:
   - Agent A approves → funds release to Agent B
   - Timeout expires → funds auto-release to Agent B
   - Dispute → requires validation from AgentValidation.vy

## Task Lifecycle

```
OPEN (0) → CLAIMED (1) → COMPLETED (2) or DISPUTED (3) or CANCELLED (4)
```

## Key Functions

### Task Management

```vyper
@external
def createTask(posterAgentId: uint256, description: String[256], amount: uint256, deadline: uint256) -> uint256

@external
def claimTask(taskId: uint256, workerAgentId: uint256)

@external
def completeTask(taskId: uint256)

@external
def approveTask(taskId: uint256)

@external
def cancelTask(taskId: uint256)
```

### Dispute Resolution

```vyper
@external
def disputeTask(taskId: uint256)

@external
def resolveDispute(taskId: uint256, payWorker: bool)
```

### Query Functions

```vyper
@view
def getTask(taskId: uint256) -> (address, address, uint256, uint256, uint8)

@view
def getTaskCount() -> uint256
```

## Events

| Event | Description |
|-------|-------------|
| `TaskCreated` | New task with escrowed funds |
| `TaskClaimed` | Worker claimed the task |
| `TaskCompleted` | Worker marked task complete |
| `TaskCancelled` | Poster cancelled (if unclaimed) |
| `TaskDisputed` | Dispute raised |
| `DisputeResolved` | Admin resolved dispute |

## Integration Dependencies

- **AgentIdentity.vy** - Verifies agent IDs are valid
- **AgentReputation.vy** - Trigger reputation feedback on completion
- **AgentValidation.vy** - Dispute resolution via validators
- **USDC** - Payment token (Arc: `0x3600000000000000000000000000000000000000`)

## Usage Example

```python
import boa

escrow = boa.load("contracts/AgentEscrow.vy", identity_address, usdc_address)

# Client creates task with 100 USDC locked
usdc.approve(escrow.address, 100 * 10**6)
task_id = escrow.createTask(poster_agent_id, "Analyze data", 100 * 10**6, 86400 * 7)

# Worker claims task
with boa.env.prank(worker):
    escrow.claimTask(task_id, worker_agent_id)

# Worker completes
with boa.env.prank(worker):
    escrow.completeTask(task_id)

# Client approves, funds released to worker
escrow.approveTask(task_id)
```

## Deadline Behavior

- `deadline` is in **relative seconds** (e.g., `86400 * 7` for 7 days)
- After deadline + claim, worker can auto-complete
- Before deadline, poster can cancel unclaimed tasks

## Security Considerations

- Only task poster can approve or cancel (before claim)
- Only claimed worker can complete
- Funds locked until task resolution
- Admin required for dispute resolution
