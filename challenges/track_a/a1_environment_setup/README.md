# A1. Environment Setup

Install tools and fund a wallet on Arc Testnet. No code to write, just configuration.

## Steps

1. **Install Moccasin and Vyper**

   ```bash
   pip install moccasin
   ```

2. **Configure Arc Testnet** in `moccasin.toml`

   Arc Testnet details:
   - Chain ID: `5042002`
   - RPC: set `ARC_TESTNET_RPC` in your `.env` (see `.env.example`)
   - Native gas token: USDC
   - USDC address: `0x3600000000000000000000000000000000000000`

3. **Fund a wallet** from the [Arc Testnet faucet](https://faucet.circle.com)

   The faucet provides 20 USDC per 2 hours per address.

4. **Verify your balance** on the [Arc block explorer](https://explorer.arc.network)

## Checkpoint

Your wallet has a non-zero USDC balance on Arc.
