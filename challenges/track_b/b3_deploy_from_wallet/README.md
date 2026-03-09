# B3. Deploy a Vyper Contract from Your Circle Wallet

Use `circlekit`'s `CircleWalletSigner` and `CircleTxExecutor` to sign and broadcast a contract deployment from your Developer-Controlled Wallet.

## Spec

- Deploy the Vault contract from Track A2 using your Circle Wallet as the deployer
- The deployment transaction should be signed by your Circle Wallet
- Confirm the deployment on the [Arc block explorer](https://explorer.arc.network)

## Environment Variables

Set these before running:

```bash
export CIRCLE_API_KEY="your-api-key"
export CIRCLE_ENTITY_SECRET="your-entity-secret"
```

## What to Implement

Fill in `challenge.py`:

1. `create_signer(wallet_id, wallet_address)`: create a `CircleWalletSigner` instance
2. `create_tx_executor(wallet_id, wallet_address)`: create a `CircleTxExecutor` instance
3. `deploy_vault_from_circle_wallet(signer, tx_executor)`: configure boa with the signer, set the Arc testnet RPC, and deploy `contracts/Vault.vy`

## Hints

- `CircleWalletSigner` and `CircleTxExecutor` read `CIRCLE_API_KEY` and `CIRCLE_ENTITY_SECRET` from the environment automatically
- Use `boa.set_network_env("https://arc-testnet.drpc.org")` to point at Arc testnet
- The USDC address on Arc testnet is `0x3600000000000000000000000000000000000000`

## Checkpoint

A deployed contract whose deployer address matches your Circle Wallet.
