"""
Agent Marketplace - Seller Server

An AI agent offering paid API services via Circle Gateway x402 payments.
This demonstrates the full ERC-8004 agent pattern:

1. Agent identity and capabilities (free discovery endpoint)
2. Paid API services behind x402 paywall
3. Payment info available for reputation feedback

Key circlekit concepts:
  - create_gateway_middleware() creates the middleware
  - gateway.process_request() verifies & settles payments (framework-agnostic)
  - Returns PaymentInfo on success, or a 402 dict when payment is needed

Requires: SELLER_ADDRESS environment variable (receives payments)

Usage:
  SELLER_ADDRESS=0x... python examples/agent-marketplace/server.py
"""

import asyncio
import os
import sys
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

PORT = int(os.getenv("PORT", "4021"))
SELLER_ADDRESS = os.getenv("SELLER_ADDRESS")

if not SELLER_ADDRESS:
    print("Error: SELLER_ADDRESS environment variable is required")
    print("Usage: SELLER_ADDRESS=0x... python examples/agent-marketplace/server.py")
    sys.exit(1)

# ============================================================================
# AGENT METADATA (ERC-8004 style)
# ============================================================================

AGENT_METADATA = {
    "agentId": 1,
    "name": "DataAnalyzer-v1",
    "description": "AI agent specializing in data analysis and content generation",
    "owner": SELLER_ADDRESS,
    "tokenURI": "ipfs://QmAgentMetadata...",
    "registeredAt": datetime.now(timezone.utc).isoformat(),
    "capabilities": ["data-analysis", "content-generation", "summarization"],
    "serviceEndpoints": {
        "info": "/",
        "analyze": "/api/analyze",
        "generate": "/api/generate",
    },
    "pricing": {
        "analyze": "$0.01",
        "generate": "$0.05",
    },
    "x402Support": True,
    "gatewayNetworks": ["eip155:5042002"],
}

# ============================================================================
# FLASK SETUP + x402 ADAPTER
# ============================================================================

from circlekit import create_gateway_middleware
from circlekit.x402 import PaymentInfo
from flask import Flask, jsonify, request

app = Flask(__name__)

gateway = create_gateway_middleware(
    seller_address=SELLER_ADDRESS,
    chain="arcTestnet",
)

# Background event loop for async process_request() calls
_loop = asyncio.new_event_loop()


def _run_event_loop() -> None:
    asyncio.set_event_loop(_loop)
    _loop.run_forever()


_loop_thread = threading.Thread(target=_run_event_loop, daemon=True)
_loop_thread.start()


def require_payment(price: str):
    """
    Flask adapter for circlekit's framework-agnostic process_request().

    Returns PaymentInfo on success, or a Flask Response (402) if payment
    is needed or failed.
    """
    payment_header = request.headers.get("Payment-Signature")
    future = asyncio.run_coroutine_threadsafe(
        gateway.process_request(
            payment_header=payment_header,
            path=request.path,
            price=price,
        ),
        _loop,
    )
    result = future.result(timeout=10)

    if isinstance(result, PaymentInfo):
        return result

    # 402 or error dict
    resp = jsonify(result.get("body", result))
    resp.status_code = result.get("status", 402)
    for k, v in result.get("headers", {}).items():
        resp.headers[k] = v
    return resp


# ============================================================================
# FREE ENDPOINTS
# ============================================================================


@app.route("/")
def index():
    """Agent Discovery (free). ERC-8004 style metadata."""
    return jsonify(
        {
            "success": True,
            "agent": AGENT_METADATA,
            "message": "Use x402 payments to access /api/analyze and /api/generate",
        }
    )


@app.route("/health")
def health():
    """Health check (free)."""
    return jsonify(
        {
            "status": "ok",
            "agent": AGENT_METADATA["name"],
            "seller": SELLER_ADDRESS,
        }
    )


# ============================================================================
# PAID ENDPOINTS (x402 paywall)
# ============================================================================


@app.route("/api/analyze")
def analyze():
    """Data Analysis ($0.01), protected by x402."""
    result = require_payment("$0.01")
    if not isinstance(result, PaymentInfo):
        return result  # 402 response

    print(f"[PAYMENT] Analyze request paid by {result.payer}")
    print(f"          Amount: {result.amount}")
    print(f"          Tx: {result.transaction}")

    resp = jsonify(
        {
            "success": True,
            "service": "analyze",
            "result": {
                "summary": "Analysis complete. Key findings indicate positive trends.",
                "confidence": 0.87,
                "dataPoints": 42,
                "insights": [
                    "Trend A shows 15% growth",
                    "Pattern B correlates with external factor C",
                    "Anomaly detected in sector D",
                ],
            },
            "payment": {
                "amount": result.amount,
                "payer": result.payer,
                "transaction": result.transaction,
            },
            "reputationHint": {
                "message": "Submit feedback with this transaction hash as proofOfPayment",
                "proofOfPayment": result.transaction,
            },
        }
    )
    for k, v in result.response_headers.items():
        resp.headers[k] = v
    return resp


@app.route("/api/generate", methods=["POST"])
def generate():
    """Content Generation ($0.05), protected by x402."""
    result = require_payment("$0.05")
    if not isinstance(result, PaymentInfo):
        return result  # 402 response

    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt", "default prompt")
    style = body.get("style", "professional")

    print(f"[PAYMENT] Generate request paid by {result.payer}")
    print(f'          Prompt: "{prompt[:50]}..."')
    print(f"          Tx: {result.transaction}")

    resp = jsonify(
        {
            "success": True,
            "service": "generate",
            "input": {"prompt": prompt, "style": style},
            "result": {
                "content": f'Generated {style} content based on: "{prompt}"',
                "wordCount": 150,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            },
            "payment": {
                "amount": result.amount,
                "payer": result.payer,
                "transaction": result.transaction,
            },
            "reputationHint": {
                "message": "Submit feedback with this transaction hash as proofOfPayment",
                "proofOfPayment": result.transaction,
            },
        }
    )
    for k, v in result.response_headers.items():
        resp.headers[k] = v
    return resp


# ============================================================================
# FEEDBACK ENDPOINT (free, simulated on-chain write)
# ============================================================================


@app.route("/feedback", methods=["POST"])
def feedback():
    """Record feedback (free). In production, writes to AgentReputation.vy."""
    body = request.get_json(silent=True) or {}

    print(f"[FEEDBACK] Score: {body.get('score')}/100")
    print(f"           Comment: {body.get('comment')}")
    print(f"           Proof: {body.get('proofOfPayment')}")

    return jsonify(
        {
            "success": True,
            "message": "Feedback recorded (simulated - would write to AgentReputation.vy)",
            "feedback": {
                "score": body.get("score"),
                "comment": body.get("comment"),
                "proofOfPayment": body.get("proofOfPayment"),
            },
        }
    )


# ============================================================================
# START SERVER
# ============================================================================

if __name__ == "__main__":
    print(f"""
{"=" * 64}
  Agent Marketplace - x402 Seller (circlekit)
{"=" * 64}

Server:    http://localhost:{PORT}
Agent:     {AGENT_METADATA["name"]}
Seller:    {SELLER_ADDRESS}
Networks:  All Gateway-supported chains

Endpoints:
  GET  /              - Agent info (free)
  GET  /health        - Health check (free)
  GET  /api/analyze   - Data analysis ($0.01)
  POST /api/generate  - Content generation ($0.05)
  POST /feedback      - Submit reputation feedback (free)

Test free endpoints:
  curl http://localhost:{PORT}/
  curl http://localhost:{PORT}/health

Test paywalled endpoints (returns 402):
  curl http://localhost:{PORT}/api/analyze

To pay, run client.py in another terminal:
  PRIVATE_KEY=0x... python examples/agent-marketplace/client.py

Get testnet USDC from: https://faucet.circle.com
""")
    app.run(host="0.0.0.0", port=PORT, debug=False)
