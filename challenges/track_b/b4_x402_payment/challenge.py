"""
B4. Make an x402 Payment On-Chain

Two parts:
  1. Server: FastAPI app with an x402-protected endpoint using create_gateway_middleware
  2. Client: GatewayClient with CircleWalletSigner that pays for the protected resource

Environment variables required:
  CIRCLE_API_KEY
  CIRCLE_ENTITY_SECRET

Run server:
  uvicorn challenges.track_b.b4_x402_payment.challenge:app --port 8000

Run client:
  python challenges/track_b/b4_x402_payment/challenge.py
"""

import asyncio
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from circlekit import GatewayClient, create_gateway_middleware
from circlekit.wallets import CircleWalletSigner


def create_server_app(seller_address: str) -> FastAPI:
    """
    Create a FastAPI app with an x402-protected /api/data endpoint.

    The endpoint requires a $0.01 USDC payment via x402 before returning data.

    Args:
        seller_address: On-chain address that receives payments.

    Returns:
        A configured FastAPI application.
    """
    app = FastAPI()

    # Implement: create the gateway middleware
    #   gateway = create_gateway_middleware(
    #       seller_address=seller_address,
    #       chain="arcTestnet",
    #   )
    #
    # Implement: add a GET /api/data route that:
    #   1. Calls await gateway.process_request(
    #          payment_header=request.headers.get("PAYMENT-SIGNATURE"),
    #          path=request.url.path,
    #          price="$0.01",
    #      )
    #   2. If result is a dict, return it as a JSONResponse with the status and headers
    #   3. Otherwise, return the protected content with result.response_headers

    raise NotImplementedError("Create the FastAPI app with x402 gateway middleware")


async def pay_for_resource(
    server_url: str,
    wallet_id: str,
    wallet_address: str,
) -> dict:
    """
    Pay for an x402-protected resource using a Circle Wallet.

    Args:
        server_url: Base URL of the server (e.g., "http://localhost:8000").
        wallet_id: Circle wallet UUID.
        wallet_address: On-chain address of the Circle wallet.

    Returns:
        dict with keys:
            "data"   - Response body from the server
            "amount" - Formatted payment amount (e.g., "0.010000")
    """
    # Implement:
    #   signer = CircleWalletSigner(wallet_id=wallet_id, wallet_address=wallet_address)
    #   client = GatewayClient(chain="arcTestnet", signer=signer)
    #
    #   result = await client.pay(f"{server_url}/api/data")
    #   print(f"Got: {result.data}")
    #   print(f"Paid: {result.formatted_amount} USDC")
    #   await client.close()
    #
    #   return {"data": result.data, "amount": result.formatted_amount}
    raise NotImplementedError("Create a GatewayClient and pay for the resource")


# Server app instance for uvicorn.
# Set CIRCLE_WALLET_ADDRESS and implement create_server_app() before running.
try:
    app = create_server_app(
        seller_address=os.environ.get("CIRCLE_WALLET_ADDRESS", "0x0000000000000000000000000000000000000000"),
    )
except NotImplementedError:
    app = None  # implement create_server_app() first


if __name__ == "__main__":
    wallet_id = os.environ.get("CIRCLE_WALLET_ID", "")
    wallet_address = os.environ.get("CIRCLE_WALLET_ADDRESS", "")

    assert wallet_id, "Set CIRCLE_WALLET_ID environment variable"
    assert wallet_address, "Set CIRCLE_WALLET_ADDRESS environment variable"

    result = asyncio.run(pay_for_resource("http://localhost:8000", wallet_id, wallet_address))

    print(f"Response: {result['data']}")
    print(f"Paid: {result['amount']} USDC")
