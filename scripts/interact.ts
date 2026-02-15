/**
 * interact.ts
 * 
 * Interact with deployed Vyper contracts on Arc Testnet.
 * Demonstrates how to read from and write to the contracts.
 * 
 * Prerequisites:
 * - Deployed contracts (run deploy-viem.ts first)
 * - PRIVATE_KEY environment variable
 * 
 * Usage:
 *   npx ts-node scripts/interact.ts
 */

import 'dotenv/config';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { 
  createWalletClient, 
  createPublicClient, 
  http, 
  defineChain,
  encodeFunctionData,
} from 'viem';
import type { Hex, Abi } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const ARTIFACTS_DIR = join(process.cwd(), 'artifacts');
const DEPLOYMENTS_FILE = join(process.cwd(), 'deployments.json');

const arcTestnet = defineChain({
  id: 5042002,
  name: 'Arc Testnet',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://rpc.testnet.arc.circle.com'] },
  },
  blockExplorers: {
    default: {
      name: 'Arc Explorer',
      url: 'https://explorer.testnet.arc.circle.com',
    },
  },
  testnet: true,
});

interface Artifact {
  contractName: string;
  abi: Abi;
  bytecode: Hex;
}

interface DeploymentRecord {
  [chainId: string]: {
    [contractName: string]: {
      address: string;
      txHash: string;
      deployedAt: string;
    };
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

function loadArtifact(contractName: string): Artifact {
  const artifactPath = join(ARTIFACTS_DIR, `${contractName}.json`);
  if (!existsSync(artifactPath)) {
    throw new Error(`Artifact not found: ${contractName}.json`);
  }
  const raw = JSON.parse(readFileSync(artifactPath, 'utf-8'));
  return { contractName: raw.contractName, abi: raw.abi as Abi, bytecode: raw.bytecode as Hex };
}

function loadDeployments(): DeploymentRecord {
  if (!existsSync(DEPLOYMENTS_FILE)) {
    throw new Error(`Deployments not found. Run deploy-viem.ts first.`);
  }
  return JSON.parse(readFileSync(DEPLOYMENTS_FILE, 'utf-8')) as DeploymentRecord;
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function main(): Promise<void> {
  console.log('╔════════════════════════════════════════════════════════════════╗');
  console.log('║       Interact with Deployed Contracts                         ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const PRIVATE_KEY = process.env.PRIVATE_KEY;
  if (!PRIVATE_KEY) {
    console.error('❌ PRIVATE_KEY is required.');
    process.exit(1);
  }

  const account = privateKeyToAccount(PRIVATE_KEY as Hex);
  
  const publicClient = createPublicClient({
    chain: arcTestnet,
    transport: http(),
  });

  const walletClient = createWalletClient({
    account,
    chain: arcTestnet,
    transport: http(),
  });

  console.log(`Using account: ${account.address}\n`);

  const deployments = loadDeployments();
  const chainId = String(arcTestnet.id);
  
  if (!deployments[chainId]) {
    console.error(`No deployments found for chain ${chainId}`);
    process.exit(1);
  }

  console.log('Deployed contracts:');
  for (const [name, info] of Object.entries(deployments[chainId])) {
    console.log(`  ${name}: ${info.address}`);
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Example: Read from AgentIdentity
  // ─────────────────────────────────────────────────────────────────────────────
  const identityDeployment = deployments[chainId]['AgentIdentity'];
  
  if (identityDeployment) {
    console.log('\n═══════════════════════════════════════════════════════════════════');
    console.log('AgentIdentity Contract');
    console.log('═══════════════════════════════════════════════════════════════════\n');
    
    const artifact = loadArtifact('AgentIdentity');
    const address = identityDeployment.address as Hex;

    // Read name()
    const name = await publicClient.readContract({
      address,
      abi: artifact.abi,
      functionName: 'name',
    });
    console.log(`Name: ${name}`);

    // Read symbol()
    const symbol = await publicClient.readContract({
      address,
      abi: artifact.abi,
      functionName: 'symbol',
    });
    console.log(`Symbol: ${symbol}`);

    // Read totalAgents()
    const totalAgents = await publicClient.readContract({
      address,
      abi: artifact.abi,
      functionName: 'totalAgents',
    });
    console.log(`Total Agents: ${totalAgents}`);

    // Example write: Register a new agent
    console.log('\n📝 Registering a new agent...');
    
    const metadataURI = `ipfs://QmExample${Date.now()}`;
    
    const data = encodeFunctionData({
      abi: artifact.abi,
      functionName: 'registerAgent',
      args: [metadataURI],
    });

    const txHash = await walletClient.sendTransaction({
      to: address,
      data,
      chain: arcTestnet,
      account,
    });

    console.log(`Transaction: ${txHash}`);
    
    const receipt = await publicClient.waitForTransactionReceipt({ hash: txHash });
    console.log(`Status: ${receipt.status}`);
    console.log(`Gas used: ${receipt.gasUsed}`);

    // Read updated totalAgents
    const newTotalAgents = await publicClient.readContract({
      address,
      abi: artifact.abi,
      functionName: 'totalAgents',
    });
    console.log(`New Total Agents: ${newTotalAgents}`);
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // Example: Read from AgentReputation
  // ─────────────────────────────────────────────────────────────────────────────
  const reputationDeployment = deployments[chainId]['AgentReputation'];
  
  if (reputationDeployment) {
    console.log('\n═══════════════════════════════════════════════════════════════════');
    console.log('AgentReputation Contract');
    console.log('═══════════════════════════════════════════════════════════════════\n');
    
    const artifact = loadArtifact('AgentReputation');
    const address = reputationDeployment.address as Hex;

    const identityRegistry = await publicClient.readContract({
      address,
      abi: artifact.abi,
      functionName: 'identityRegistry',
    });
    console.log(`Identity Registry: ${identityRegistry}`);

    // Check agent 1's reputation
    try {
      const avgScore = await publicClient.readContract({
        address,
        abi: artifact.abi,
        functionName: 'getAverageScore',
        args: [BigInt(1)],
      });
      console.log(`Agent 1 Average Score: ${Number(avgScore) / 100}`);
    } catch {
      console.log('Agent 1 not found or no feedback yet');
    }
  }

  console.log('\n═══════════════════════════════════════════════════════════════════');
  console.log('INTERACTION COMPLETE');
  console.log('═══════════════════════════════════════════════════════════════════');
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
