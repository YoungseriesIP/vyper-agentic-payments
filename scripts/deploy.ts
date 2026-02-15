/**
 * deploy.ts
 * 
 * Deploy Vyper contracts using Circle's Smart Contract Platform SDK.
 * This provides managed deployments with gas sponsorship on supported chains.
 * 
 * Prerequisites:
 * - Run scripts/compile-vyper.ts first
 * - CIRCLE_API_KEY environment variable
 * - CIRCLE_ENTITY_SECRET environment variable
 * - CIRCLE_WALLET_ID environment variable (from setup-wallet.ts)
 * 
 * Usage:
 *   npx ts-node scripts/deploy.ts [contract-name]
 * 
 * For most users, deploy-viem.ts is recommended instead.
 */

import 'dotenv/config';
import { readFileSync, existsSync, writeFileSync } from 'fs';
import { join } from 'path';
import { initiateSmartContractPlatformClient } from '@circle-fin/smart-contract-platform';

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const ARTIFACTS_DIR = join(process.cwd(), 'artifacts');
const DEPLOYMENTS_FILE = join(process.cwd(), 'deployments.json');

const DEPLOY_ORDER = [
  'AgentIdentity',
  'AgentReputation', 
  'AgentValidation',
  'AgentEscrow',
  'SpendingLimiter',
  'PaymentSplitter',
  'SubscriptionManager',
];

interface Artifact {
  contractName: string;
  abi: unknown[];
  bytecode: string;
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
  return JSON.parse(readFileSync(artifactPath, 'utf-8')) as Artifact;
}

function loadDeployments(): DeploymentRecord {
  if (existsSync(DEPLOYMENTS_FILE)) {
    return JSON.parse(readFileSync(DEPLOYMENTS_FILE, 'utf-8')) as DeploymentRecord;
  }
  return {};
}

function saveDeployments(deployments: DeploymentRecord): void {
  writeFileSync(DEPLOYMENTS_FILE, JSON.stringify(deployments, null, 2));
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function main(): Promise<void> {
  console.log('╔════════════════════════════════════════════════════════════════╗');
  console.log('║       Deploy Vyper Contracts (Circle SDK)                      ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const CIRCLE_API_KEY = process.env.CIRCLE_API_KEY;
  const CIRCLE_ENTITY_SECRET = process.env.CIRCLE_ENTITY_SECRET;
  const CIRCLE_WALLET_ID = process.env.CIRCLE_WALLET_ID;

  if (!CIRCLE_API_KEY || !CIRCLE_ENTITY_SECRET || !CIRCLE_WALLET_ID) {
    console.error('❌ Missing required environment variables:');
    if (!CIRCLE_API_KEY) console.error('   - CIRCLE_API_KEY');
    if (!CIRCLE_ENTITY_SECRET) console.error('   - CIRCLE_ENTITY_SECRET');
    if (!CIRCLE_WALLET_ID) console.error('   - CIRCLE_WALLET_ID');
    console.error('\nRun scripts/setup-wallet.ts first.');
    process.exit(1);
  }

  const client = initiateSmartContractPlatformClient({
    apiKey: CIRCLE_API_KEY,
    entitySecret: CIRCLE_ENTITY_SECRET,
  });

  const targetContract = process.argv[2];
  const contractsToDeploy = targetContract ? [targetContract] : DEPLOY_ORDER;

  const deployments = loadDeployments();
  const chainId = '5042002'; // Arc Testnet

  if (!deployments[chainId]) {
    deployments[chainId] = {};
  }

  console.log(`Deploying to Arc Testnet (Chain ID: ${chainId})`);
  console.log(`Contracts: ${contractsToDeploy.join(', ')}\n`);

  for (const contractName of contractsToDeploy) {
    try {
      console.log(`\n📦 Deploying ${contractName}...`);
      
      const artifact = loadArtifact(contractName);
      const constructorArgs: string[] = [];
      
      if (['AgentReputation', 'AgentValidation', 'AgentEscrow'].includes(contractName)) {
        const identityAddr = deployments[chainId]['AgentIdentity']?.address;
        if (!identityAddr) {
          console.error(`❌ ${contractName} requires AgentIdentity first`);
          continue;
        }
        constructorArgs.push(identityAddr);
      }

      if (contractName === 'AgentEscrow') {
        const usdcAddress = process.env.USDC_ADDRESS || '0x3600000000000000000000000000000000000000';
        constructorArgs.push(usdcAddress);
      }

      // Deploy using Circle's Smart Contract Platform
      const deployResponse = await client.deployContract({
        name: contractName,
        description: `Vyper Agentic Payments - ${contractName}`,
        walletId: CIRCLE_WALLET_ID,
        blockchain: 'ETH-SEPOLIA',
        abiJson: JSON.stringify(artifact.abi),
        bytecode: artifact.bytecode,
        constructorParameters: constructorArgs,
        fee: { type: 'level', config: { feeLevel: 'MEDIUM' } },
      });

      if (!deployResponse.data) {
        throw new Error(`Failed to deploy ${contractName}`);
      }

      const contractId = deployResponse.data.contractId;
      console.log(`   Contract ID: ${contractId}`);
      console.log(`   Waiting for deployment...`);

      // Poll for deployment status
      let attempts = 0;
      const maxAttempts = 30;
      
      while (attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 5000));
        
        if (!contractId) break;
        
        const statusResponse = await client.getContract({ id: contractId });
        const status = (statusResponse.data as Record<string, unknown>)?.status as string | undefined;
        
        if (status === 'COMPLETE') {
          const address = (statusResponse.data as Record<string, unknown>)?.contractAddress as string | undefined;
          const txHash = String((statusResponse.data as Record<string, unknown>)?.transactionHash || 'N/A');
          
          if (address) {
            console.log(`   ✓ Deployed at: ${address}`);
            
            deployments[chainId][contractName] = {
              address,
              txHash,
              deployedAt: new Date().toISOString(),
            };
            saveDeployments(deployments);
            break;
          }
        } else if (status === 'FAILED') {
          throw new Error(`Deployment failed for ${contractName}`);
        }
        
        attempts++;
        console.log(`   Status: ${status} (${attempts}/${maxAttempts})`);
      }
    } catch (error) {
      console.error(`❌ Failed to deploy ${contractName}:`, error);
    }
  }

  console.log('\n═══════════════════════════════════════════════════════════════════');
  console.log('DEPLOYMENT SUMMARY');
  console.log('═══════════════════════════════════════════════════════════════════\n');

  for (const [name, info] of Object.entries(deployments[chainId])) {
    console.log(`${name}: ${info.address}`);
  }

  console.log(`\nDeployments saved to: ${DEPLOYMENTS_FILE}`);
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
