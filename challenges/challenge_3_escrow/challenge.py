"""
Challenge 3: Escrow Task (Medium-Hard)

Create a USDC escrow task and approve completion.

Instructions:
  1. Approve USDC spending by the escrow contract (as poster)
  2. Create a task that locks USDC in escrow (as poster)
  3. Claim the task (as worker)
  4. Approve completion to release USDC to worker (as poster)
  5. Return the task_id

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "challenge_3"
"""

import boa


def create_and_complete_task(
    escrow,
    usdc,
    poster: str,
    poster_agent_id: int,
    worker: str,
    worker_agent_id: int,
    amount: int,
    description_hash: bytes,
    deadline: int,
) -> int:
    """
    Create an escrow task and complete it.

    Args:
        escrow: Deployed AgentEscrow contract instance
        usdc: Deployed mock USDC contract instance
        poster: Address of the task poster
        poster_agent_id: Agent ID of the poster
        worker: Address of the worker
        worker_agent_id: Agent ID of the worker
        amount: USDC amount in raw units (6 decimals)
        description_hash: 32-byte task description hash
        deadline: Relative deadline in seconds

    Returns:
        task_id: The ID of the created task
    """
    # TODO: Step 1 — As poster, approve escrow to spend `amount` USDC
    #       usdc.approve(escrow.address, amount)

    # TODO: Step 2 — As poster, create the task
    #       task_id = escrow.createTask(poster_agent_id, amount, description_hash, deadline)

    # TODO: Step 3 — As worker, claim the task
    #       escrow.claimTask(task_id, worker_agent_id)

    # TODO: Step 4 — As poster, approve completion
    #       escrow.approveCompletion(task_id)

    # TODO: Return task_id
    raise NotImplementedError("Complete this challenge!")
