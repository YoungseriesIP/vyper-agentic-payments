/**
 * Agent Marketplace - Seller Server
 *
 * An AI agent offering paid API services via Circle Gateway x402 payments.
 * This demonstrates the full ERC-8004 agent pattern:
 *
 * 1. Agent identity and capabilities (free discovery endpoint)
 * 2. Paid API services behind x402 paywall
 * 3. Payment info available for reputation feedback
 *
 * Key x402 concepts:
 *   - createGatewayMiddleware() sets up payment handling
 *   - gateway.require('$0.01') protects routes with micropayments
 *   - req.payment contains payer, amount, transaction after successful payment
 *
 * ⚠️ REQUIRES: SELLER_ADDRESS environment variable (receives payments)
 *
 * Usage:
 *   SELLER_ADDRESS=0x... npx tsx server.ts
 */

import express from 'express';
import { createGatewayMiddleware, type PaymentRequest } from '@circlefin/x402-batching/server';
import 'dotenv/config';

// ============================================================================
// CONFIGURATION
// ============================================================================

const PORT = process.env.PORT ?? 4021;
const SELLER_ADDRESS = process.env.SELLER_ADDRESS;

if (!SELLER_ADDRESS) {
  console.error('Error: SELLER_ADDRESS environment variable is required');
  console.error('Usage: SELLER_ADDRESS=0x... npx tsx server.ts');
  process.exit(1);
}

// ============================================================================
// AGENT METADATA (ERC-8004 style)
// ============================================================================

// ⚠️ ASSUMPTION: In production, this would be read from AgentIdentity.vy on-chain
// The tokenURI stored in the contract would point to JSON like this
const AGENT_METADATA = {
  agentId: 1,
  name: 'DataAnalyzer-v1',
  description: 'AI agent specializing in data analysis and content generation',
  owner: SELLER_ADDRESS,
  tokenURI: 'ipfs://QmAgentMetadata...', // Would be real IPFS hash
  registeredAt: new Date().toISOString(),
  capabilities: ['data-analysis', 'content-generation', 'summarization'],
  serviceEndpoints: {
    info: '/',
    analyze: '/api/analyze',
    generate: '/api/generate',
  },
  pricing: {
    analyze: '$0.01',
    generate: '$0.05',
  },
  x402Support: true,
  gatewayNetworks: ['eip155:5042002'], // Arc Testnet
};

// ============================================================================
// EXPRESS SETUP
// ============================================================================

const app = express();
app.use(express.json());

// Create Gateway middleware
// Accepts payments from ALL Gateway-supported chains by default
const gateway = createGatewayMiddleware({
  sellerAddress: SELLER_ADDRESS,
  // networks: ['eip155:5042002'], // Uncomment to restrict to Arc Testnet only
});

// ============================================================================
// FREE ENDPOINTS
// ============================================================================

/**
 * GET / - Agent Discovery (free)
 *
 * Returns ERC-8004 style agent metadata for discovery.
 * Clients use this to understand agent capabilities before paying.
 *
 * In production, this data would come from AgentIdentity.vy on-chain:
 *   agentId = identity.getAgentByAddress(sellerAddress)
 *   tokenURI = identity.tokenURI(agentId)
 *   metadata = fetch(tokenURI)
 */
app.get('/', (_req, res) => {
  res.json({
    success: true,
    agent: AGENT_METADATA,
    message: 'Use x402 payments to access /api/analyze and /api/generate',
  });
});

/**
 * GET /health - Health check (free)
 */
app.get('/health', (_req, res) => {
  res.json({
    status: 'ok',
    agent: AGENT_METADATA.name,
    seller: SELLER_ADDRESS,
  });
});

// ============================================================================
// PAID ENDPOINTS (x402 paywall)
// ============================================================================

/**
 * GET /api/analyze - Data Analysis ($0.01)
 *
 * Protected by gateway.require('$0.01')
 * - Without payment: Returns 402 Payment Required
 * - With payment: Verifies, settles, and returns analysis
 */
app.get('/api/analyze', gateway.require('$0.01'), (req, res) => {
  const payment = (req as unknown as PaymentRequest).payment;

  // Log payment for potential reputation feedback
  console.log(`[PAYMENT] Analyze request paid by ${payment?.payer}`);
  console.log(`          Amount: ${payment?.amount}`);
  console.log(`          Tx: ${payment?.transaction}`);

  // ⚠️ ASSUMPTION: In production, we would record this interaction
  // for later reputation feedback in AgentReputation.vy:
  //   reputation.recordInteraction(agentId, payment.payer)

  res.json({
    success: true,
    service: 'analyze',
    result: {
      summary: 'Analysis complete. Key findings indicate positive trends.',
      confidence: 0.87,
      dataPoints: 42,
      insights: [
        'Trend A shows 15% growth',
        'Pattern B correlates with external factor C',
        'Anomaly detected in sector D',
      ],
    },
    payment: {
      amount: payment?.amount,
      payer: payment?.payer,
      transaction: payment?.transaction,
      network: payment?.network,
    },
    // Hint for client: use this transaction as proofOfPayment in AgentReputation
    reputationHint: {
      message: 'Submit feedback with this transaction hash as proofOfPayment',
      proofOfPayment: payment?.transaction,
    },
  });
});

/**
 * POST /api/generate - Content Generation ($0.05)
 *
 * Accepts a prompt in the request body and generates content.
 * Higher price for more compute-intensive operation.
 */
app.post('/api/generate', gateway.require('$0.05'), (req, res) => {
  const body = req.body as { prompt?: string; style?: string };
  const prompt = body?.prompt ?? 'default prompt';
  const style = body?.style ?? 'professional';
  const payment = (req as unknown as PaymentRequest).payment;

  console.log(`[PAYMENT] Generate request paid by ${payment?.payer}`);
  console.log(`          Prompt: "${prompt.substring(0, 50)}..."`);
  console.log(`          Tx: ${payment?.transaction}`);

  res.json({
    success: true,
    service: 'generate',
    input: { prompt, style },
    result: {
      content: `Generated ${style} content based on: "${prompt}"`,
      wordCount: 150,
      generatedAt: new Date().toISOString(),
    },
    payment: {
      amount: payment?.amount,
      payer: payment?.payer,
      transaction: payment?.transaction,
      network: payment?.network,
    },
    reputationHint: {
      message: 'Submit feedback with this transaction hash as proofOfPayment',
      proofOfPayment: payment?.transaction,
    },
  });
});

/**
 * POST /feedback - Record Feedback (free, would write to AgentReputation on-chain)
 *
 * In production, this would submit a transaction to AgentReputation.vy:
 *   reputation.submitFeedback(agentId, score, comment, proofOfPayment)
 *
 * For now, we just log it and return success.
 */
app.post('/feedback', (req, res) => {
  const body = req.body as {
    score?: number;
    comment?: string;
    proofOfPayment?: string;
  };

  console.log(`[FEEDBACK] Score: ${body?.score}/100`);
  console.log(`           Comment: ${body?.comment}`);
  console.log(`           Proof: ${body?.proofOfPayment}`);

  // ⚠️ SIMULATED: In production, this would be an on-chain transaction:
  //   txHash = reputation.submitFeedback(agentId, score, comment, proofOfPayment)

  res.json({
    success: true,
    message: 'Feedback recorded (simulated - would write to AgentReputation.vy)',
    feedback: {
      score: body?.score,
      comment: body?.comment,
      proofOfPayment: body?.proofOfPayment,
    },
  });
});

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║        Agent Marketplace - x402 Seller Example                 ║
╚════════════════════════════════════════════════════════════════╝

Server:    http://localhost:${PORT}
Agent:     ${AGENT_METADATA.name}
Seller:    ${SELLER_ADDRESS}
Networks:  All Gateway-supported chains

Endpoints:
  GET  /              - Agent info (free)
  GET  /health        - Health check (free)
  GET  /api/analyze   - Data analysis ($0.01)
  POST /api/generate  - Content generation ($0.05)
  POST /feedback      - Submit reputation feedback (free)

Test free endpoints:
  curl http://localhost:${PORT}/
  curl http://localhost:${PORT}/health

Test paywalled endpoints (returns 402):
  curl http://localhost:${PORT}/api/analyze

To pay, run client.ts in another terminal:
  PRIVATE_KEY=0x... npx tsx client.ts

Get testnet USDC from: https://faucet.circle.com
`);
});
