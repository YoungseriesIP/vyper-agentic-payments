# B4. Make an x402 Payment On-Chain

Set up a local x402-protected endpoint using `circlekit`'s server middleware, then pay it from your Circle Wallet using `GatewayClient`.

## Spec

Two parts:

1. **Server side** — a FastAPI app with an endpoint protected by `create_gateway_middleware`. The endpoint requires a `$0.01` payment before returning data.

2. **Client side** — a `GatewayClient` configured with your Circle Wallet that calls the protected endpoint and pays the x402 fee.

## Environment Variables

Set these before running:

```bash
export CIRCLE_API_KEY="your-api-key"
export CIRCLE_ENTITY_SECRET="your-entity-secret"
```

## What to Implement

Fill in `challenge.py`:

1. `create_server_app(seller_address)` — return a FastAPI app with a `/api/data` endpoint protected by `create_gateway_middleware` at `$0.01`
2. `pay_for_resource(server_url, wallet_id, wallet_address)` — create a `GatewayClient` with a `CircleWalletSigner`, call `gateway.pay()` on the endpoint, and return the result

## Hints

- The server uses `create_gateway_middleware(seller_address=..., chain="arcTestnet")`
- The middleware's `process_request()` is async — use `await` in the FastAPI handler
- The client uses `GatewayClient(chain="arcTestnet", signer=signer)`
- `gateway.pay()` is async — use `await`
- Call `await gateway.close()` when done, or use `async with`

## Checkpoint

An on-chain x402 payment transaction initiated from your Circle Wallet, confirmed on the Arc block explorer.
