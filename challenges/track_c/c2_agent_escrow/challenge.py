"""
C2. AgentEscrow with Hash-Commitment Release

A Vyper escrow factory where each job holds a payer's USDC deposit against
a bytes32 hash of the agreed output specification. Funds release only when
a designated verifier confirms the delivery, or after a timeout expires.

The existing contracts/AgentEscrow.vy provides a starting point with
task creation, claiming, and approval. This challenge extends it with
hash-commitment verification, a challenge period, and arbiter resolution.

Key functions per challenges.md spec:
  - deposit(job_id, payee, amount, spec_hash)
  - submit_delivery(job_id, delivery_hash)
  - confirm_release(job_id)
  - challenge(job_id)
  - force_release(job_id)
  - arbiter_resolve(job_id, release)

Run test:
  pytest tests/test_hackathon_challenges.py -v -k "C2"
"""

import boa


def deposit(
    escrow,
    usdc,
    payer: str,
    payee: str,
    amount: int,
    spec_hash: bytes,
) -> int:
    """
    Payer deposits USDC and sets the agreed specification hash.

    Args:
        escrow: Deployed AgentEscrow contract instance.
        usdc: Deployed USDC token contract instance.
        payer: Address depositing USDC.
        payee: Address of the provider who will deliver.
        amount: USDC amount in raw units (6 decimals).
        spec_hash: 32-byte hash of the agreed output specification.

    Returns:
        job_id: The ID of the created escrow job.
    """
    # Implement: as payer, approve escrow then create a job with the spec hash
    raise NotImplementedError("Approve USDC and create the escrow job")


def submit_delivery(escrow, provider: str, job_id: int, delivery_hash: bytes):
    """
    Provider submits a hash of their deliverable.

    Args:
        escrow: Deployed AgentEscrow contract instance.
        provider: Address of the provider submitting delivery.
        job_id: The escrow job ID.
        delivery_hash: 32-byte hash of the delivered output.
    """
    # Implement: as provider, submit the delivery hash for verification
    raise NotImplementedError("Submit the delivery hash for the job")


def confirm_release(escrow, verifier: str, job_id: int):
    """
    Verifier confirms the delivery matches the spec, releasing funds to provider.

    Args:
        escrow: Deployed AgentEscrow contract instance.
        verifier: Address of the designated verifier.
        job_id: The escrow job ID.
    """
    # Implement: as verifier, confirm the match and release funds
    raise NotImplementedError("Confirm the delivery and release funds")


def challenge(escrow, challenger: str, job_id: int):
    """
    Verifier or payer challenges the delivery, entering a dispute state.

    Args:
        escrow: Deployed AgentEscrow contract instance.
        challenger: Address raising the challenge (verifier or payer).
        job_id: The escrow job ID.
    """
    # Implement: as challenger, dispute the delivery
    raise NotImplementedError("Challenge the delivery on this job")


def force_release(escrow, job_id: int):
    """
    Release funds to provider after the timeout expires with no verifier action.
    Callable by anyone once the timeout has passed.

    Args:
        escrow: Deployed AgentEscrow contract instance.
        job_id: The escrow job ID.
    """
    # Implement: call force release after the timeout window has elapsed
    raise NotImplementedError("Force-release funds after timeout expiry")


def arbiter_resolve(escrow, arbiter: str, job_id: int, release: bool):
    """
    Arbiter makes a final decision on a challenged job.

    Args:
        escrow: Deployed AgentEscrow contract instance.
        arbiter: Address of the arbiter (admin or designated resolver).
        job_id: The escrow job ID.
        release: True to release funds to provider, False to refund payer
                 (minus a small non-refundable work fee).
    """
    # Implement: as arbiter, resolve the dispute in favor of one party
    raise NotImplementedError("Resolve the dispute as arbiter")
