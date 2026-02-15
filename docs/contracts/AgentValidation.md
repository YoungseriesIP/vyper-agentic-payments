# AgentValidation.vy

On-chain validation registry for verifying agent work quality.

## Overview

This contract provides independent validation of agent work, supporting multiple validation methods. It integrates with AgentEscrow to verify work before releasing payment.

## Agentic Pattern

Solves the "Is this work legitimate?" problem through:

1. **Trusted Judges** - Human or AI validators with authority
2. **Staked Validators** - Validators who stake tokens, lose stake for bad validations
3. **Cryptographic Proofs** - zkML proofs, TEE attestations

## Validation Lifecycle

```
NONE (0) → PENDING (1) → APPROVED (2) or REJECTED (3)
```

## Key Functions

### Validator Management

```vyper
@external
def addValidator(validator: address, validatorType: uint8)

@external
def removeValidator(validator: address)
```

### Validation Flow

```vyper
@external
def requestValidation(agentId: uint256, taskHash: bytes32) -> uint256

@external
def submitValidation(validationId: uint256, approved: bool, evidenceURI: String[256])
```

### Query Functions

```vyper
@view
def getValidationStatus(validationId: uint256) -> uint8

@view
def isValidator(validator: address) -> bool
```

## Events

| Event | Description |
|-------|-------------|
| `ValidationRequested` | New validation requested |
| `ValidationSubmitted` | Validator submitted result |
| `ValidatorAdded` | New validator registered |
| `ValidatorRemoved` | Validator removed |

## Integration with Escrow

```python
# In AgentEscrow, before releasing disputed funds:
validation_status = validation_contract.getValidationStatus(validation_id)
assert validation_status == STATUS_APPROVED, "Work not validated"
```

## Validator Types

| Type | Value | Use Case |
|------|-------|----------|
| `VALIDATOR_TRUSTED_JUDGE` | 1 | Human arbitrators |
| `VALIDATOR_STAKED` | 2 | Staked validator network |
| `VALIDATOR_CRYPTOGRAPHIC` | 3 | zkML, TEE attestations |

## Usage Example

```python
import boa

validation = boa.load("contracts/AgentValidation.vy", identity_address)

# Add trusted validator
validation.addValidator(judge_address, 1)  # TRUSTED_JUDGE

# Request validation for completed work
task_hash = keccak256(b"task-123")
validation_id = validation.requestValidation(agent_id, task_hash)

# Validator approves
validation.submitValidation(validation_id, True, "ipfs://evidence...")

# Check status
assert validation.getValidationStatus(validation_id) == 2  # APPROVED
```

## Security Considerations

- Only registered validators can submit validations
- Admin can add/remove validators
- Validation results are immutable once submitted
- Task hash prevents tampering with validation scope
