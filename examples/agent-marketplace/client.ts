/**
 * Agent Marketplace - Buyer Client
 *
 * An AI agent client that discovers agents, pays for services, and provides feedback.
 * This demonstrates the full ERC-8004 agent lifecycle:
 *
 * 1. Discover agent (read capabilities from free endpoint)
 * 2. Check agent reputation (would read from AgentReputation.vy on-chain)
 * 3. Pay for service via x402 (gasless!)
 * 4. Receive response
 * 5. Submit feedback (would write to AgentReputation.vy on-chain)
 *
 * Key x402 concepts:
 *   - GatewayClient handles all Gateway operations
 *   - gateway.supports() checks if URL supports x402
 *   - gateway.pay() handles full 402 negotiation automatically
 *
 * ⚠️ REQUIRES: PRIVATE_KEY with USDC deposited in Gateway
 * ⚠️ REQUIRES: Server running at SERVER_URL (default: http://localhost:4021)
 *
 * Usage:
 *   1. Start server: SELLER_ADDRESS=0x... npx tsx server.ts
 *   2. Run client: PRIVATE_KEY=0x... npx tsx client.ts
 */
// x402 payment flow pattern based on Circle's x402 Batching SDK examples

import { GatewayClient } from '@circlefin/x402-batching/client';
import type { Hex } from 'viem';
import 'dotenv/config';

// ============================================================================
// CONFIGURATION
// ============================================================================

const PRIVATE_KEY = process.env.PRIVATE_KEY as Hex | undefined;
const SERVER_URL = process.env.SERVER_URL ?? 'http://localhost:4021';

if (!PRIVATE_KEY) {
  console.error('Error: PRIVATE_KEY environment variable is required');
  console.error('Usage: PRIVATE_KEY=0x... npx tsx client.ts');
  console.error('\nGet testnet USDC from: https://faucet.circle.com');
  process.exit(1);
}

// ============================================================================
// TYPES
// ============================================================================

interface AgentMetadata {
  agentId: number;
  name: string;
  description: string;
  owner: string;
  capabilities: string[];
  serviceEndpoints: Record<string, string>;
  pricing: Record<string, string>;
  x402Support: boolean;
}

interface AgentInfoResponse {
  success: boolean;
  agent: AgentMetadata;
  message: string;
}

interface AnalyzeResponse {
  success: boolean;
  service: string;
  result: {
    summary: string;
    confidence: number;
    dataPoints: number;
    insights: string[];
  };
  payment: {
    amount: string;
    payer: string;
    transaction: string;
    network: string;
  };
  reputationHint: {
    message: string;
    proofOfPayment: string;
  };
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║        Agent Marketplace - x402 Buyer Client                   ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  // ──────────────────────────────────────────────────────────────────────────
  // 1. Create Gateway Client
  // ──────────────────────────────────────────────────────────────────────────
  console.log('1. Creating Gateway client...');

  const gateway = new GatewayClient({
    chain: 'arcTestnet',
    privateKey: PRIVATE_KEY!,
  });

  console.log(`   Address: ${gateway.address}`);
  console.log(`   Chain: ${gateway.chainName}`);

  // ──────────────────────────────────────────────────────────────────────────
  // 2. Check Balances
  // ──────────────────────────────────────────────────────────────────────────
  console.log('\n2. Checking balances...');

  const balances = await gateway.getBalances();

  console.log(`   Wallet USDC:  ${balances.wallet.formatted}`);
  console.log(`   Gateway:      ${balances.gateway.formattedAvailable} available`);

  if (parseFloat(balances.gateway.formattedAvailable) < 0.01) {
    console.log('\n⚠️  Insufficient Gateway balance');
    console.log('   Run: PRIVATE_KEY=0x... python deposit.py --amount 1');
    return;
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 3. Discover Agent (ERC-8004 pattern)
  // ──────────────────────────────────────────────────────────────────────────
  console.log('\n3. Discovering agent...');

  // In production, we might:
  //   1. Query AgentIdentity.vy for active agents
  //   2. Filter by capabilities
  //   3. Check AgentReputation.vy for reputation scores

  const infoResponse = await fetch(`${SERVER_URL}/`);
  if (!infoResponse.ok) {
    console.log(`   ❌ Failed to fetch agent info: ${infoResponse.status}`);
    console.log('   Make sure server is running: SELLER_ADDRESS=0x... npx tsx server.ts');
    return;
  }

  const agentInfo = (await infoResponse.json()) as AgentInfoResponse;
  const agent = agentInfo.agent;

  console.log(`   Agent: ${agent.name}`);
  console.log(`   Description: ${agent.description}`);
  console.log(`   Capabilities: ${agent.capabilities.join(', ')}`);
  console.log(`   Pricing: analyze=${agent.pricing.analyze}, generate=${agent.pricing.generate}`);
  console.log(`   x402 Support: ${agent.x402Support ? '✅ Yes' : '❌ No'}`);

  // ──────────────────────────────────────────────────────────────────────────
  // 4. Check Reputation (simulated)
  // ──────────────────────────────────────────────────────────────────────────
  console.log('\n4. Checking agent reputation...');

  // ⚠️ SIMULATED: In production, this would read from AgentReputation.vy:
  //   avgScore = reputation.getAverageScore(agentId)
  //   tier = reputation.getReputationTier(agentId)
  //   feedbackCount = reputation.getFeedbackCount(agentId)

  console.log('   📝 [SIMULATED] Would query AgentReputation.vy on-chain');
  console.log('   Average Score: 85/100');
  console.log('   Tier: Gold');
  console.log('   Total Feedbacks: 42');

  // ──────────────────────────────────────────────────────────────────────────
  // 5. Check x402 Support
  // ──────────────────────────────────────────────────────────────────────────
  console.log('\n5. Checking x402 support...');

  const analyzeUrl = `${SERVER_URL}/api/analyze`;
  const support = await gateway.supports(analyzeUrl);

  if (support.supported) {
    console.log('   ✅ Server supports Gateway batching');
  } else {
    console.log(`   ❌ Server does NOT support Gateway batching: ${support.error}`);
    return;
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 6. Pay for Analysis Service (Gasless!)
  // ──────────────────────────────────────────────────────────────────────────
  console.log('\n6. Paying for /api/analyze ($0.01)...');

  try {
    const result = await gateway.pay<AnalyzeResponse>(analyzeUrl);

    console.log(`   ✅ Paid ${result.formattedAmount} USDC (gasless!)`);
    console.log(`   Transaction: ${result.transaction}`);
    console.log('\n   Response from agent:');
    console.log(`   - Summary: ${result.data.result.summary}`);
    console.log(`   - Confidence: ${(result.data.result.confidence * 100).toFixed(0)}%`);
    console.log(`   - Insights: ${result.data.result.insights.length} found`);

    // ──────────────────────────────────────────────────────────────────────────
    // 7. Submit Feedback (simulated)
    // ──────────────────────────────────────────────────────────────────────────
    console.log('\n7. Submitting reputation feedback...');

    // ⚠️ SIMULATED: In production, this would:
    //   1. Call AgentReputation.recordInteraction(agentId, myAddress) - done by server
    //   2. Call AgentReputation.submitFeedback(agentId, score, comment, proofOfPayment)

    const feedbackResponse = await fetch(`${SERVER_URL}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        score: 90,
        comment: 'Great analysis, very insightful!',
        proofOfPayment: result.transaction,
      }),
    });

    if (feedbackResponse.ok) {
      console.log('   ✅ Feedback submitted');
      console.log('   📝 [SIMULATED] Would write to AgentReputation.vy on-chain');
      console.log(`   Score: 90/100`);
      console.log(`   Proof of Payment: ${result.transaction}`);
    }
  } catch (error) {
    console.log(`   ❌ Payment failed: ${(error as Error).message}`);
    return;
  }

  // ──────────────────────────────────────────────────────────────────────────
  // 8. Final Balances
  // ──────────────────────────────────────────────────────────────────────────
  console.log('\n8. Updated balances...');

  const newBalances = await gateway.getBalances();

  console.log(`   Wallet USDC:  ${newBalances.wallet.formatted}`);
  console.log(`   Gateway:      ${newBalances.gateway.formattedAvailable} available`);

  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║                        Complete!                               ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');
}

main().catch(console.error);
