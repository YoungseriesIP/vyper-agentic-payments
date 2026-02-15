/**
 * deploy-viem.ts
 * 
 * Deploy Vyper contracts using viem directly to Arc Testnet.
 * This is the recommended way to deploy contracts.
 * 
 * Prerequisites:
 * - Run scripts/compile-vyper.ts first
 * - PRIVATE_KEY environment variable (with 0x prefix)
 * - Funded wallet with testnet ETH for gas
 * 
 * Usage:
 *   npx ts-node scripts/deploy-viem.ts [contract-name]
 * 
 * Examples:
 *   npx ts-node scripts/deploy-viem.ts                    # Deploy all contracts
 *   npx ts-node scripts/deploy-viem.ts AgentIdentity      # Deploy specific contract
 */

import 'dotenv/config';
import { readFileSync, existsSync, writeFileSync } from 'fs';
import { join } from 'path';
import { 
  createWalletClient, 
  createPublicClient, 
  http, 
  defineChain,
  encodeFunctionData,
  encodeDeployData,
} from 'viem';
import type { Hex, Abi } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const ARTIFACTS_DIR = join(process.cwd(), 'artifacts');
const DEPLOYMENTS_FILE = join(process.cwd(), 'deployments.json');

// Arc Testnet chain definition
const arcTestnet = defineChain({
  id: 5042002,
  name: 'Arc Testnet',
  nativeCurrency: {
    name: 'Ether',
    symbol: 'ETH',
    decimals: 18,
  },
  rpcUrls: {
    default: {
      http: ['https://rpc.testnet.arc.circle.com'],
    },
  },
  blockExplorers: {
    default: {
      name: 'Arc Explorer',
      url: 'https://explorer.testnet.arc.circle.com',
    },
  },
  testnet: true,
});

// Contract deployment order (respecting dependencies)
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
    throw new Error(
      `Artifact not found: ${contractName}.json\n` +
      `Run 'npx ts-node scripts/compile-vyper.ts' first.`
    );
  }
  
  const raw = JSON.parse(readFileSync(artifactPath, 'utf-8'));
  return {
    contractName: raw.contractName,
    abi: raw.abi as Abi,
    bytecode: raw.bytecode as Hex,
  };
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
  console.log('║       Deploy Vyper Contracts (viem + Arc Testnet)              ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const PRIVATE_KEY = process.env.PRIVATE_KEY;

  if (!PRIVATE_KEY) {
    console.error('❌ PRIVATE_KEY is required. Set it in your .env file.');
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

  console.log(`Deployer: ${account.address}`);
  
  const balance = await publicClient.getBalance({ address: account.address });
  console.log(`Balance: ${Number(balance) / 1e18} ETH\n`);

  if (balance === BigInt(0)) {
    console.error('❌ Wallet has no ETH for gas. Fund it first.');
    process.exit(1);
  }

  const targetContract = process.argv[2];
  const contractsToDeploy = targetContract ? [targetContract] : DEPLOY_ORDER;

  const deployments = loadDeployments();
  const chainId = String(arcTestnet.id);

  if (!deployments[chainId]) {
    deployments[chainId] = {};
  }

  console.log(`Deploying to ${arcTestnet.name} (Chain ID: ${chainId})`);
  console.log(`Contracts: ${contractsToDeploy.join(', ')}\n`);

  for (const contractName of contractsToDeploy) {
    try {
      console.log(`\n📦 Deploying ${contractName}...`);
      
      const artifact = loadArtifact(contractName);
      const constructorArgs: unknown[] = [];
      
      if (['AgentReputation', 'AgentValidation', 'AgentEscrow'].includes(contractName)) {
        const identityAddr = deployments[chainId]['AgentIdentity']?.address;
        if (!identityAddr) {
          console.error(`❌ ${contractName} requires AgentIdentity to be deployed first`);
          continue;
        }
        constructorArgs.push(identityAddr);
      }

      if (contractName === 'AgentEscrow') {
        const usdcAddress = process.env.USDC_ADDRESS || '0x3600000000000000000000000000000000000000';
        constructorArgs.push(usdcAddress);
      }

      // Encode deploy data
      const deployData = encodeDeployData({
        abi: artifact.abi,
        bytecode: artifact.bytecode,
        args: constructorArgs,
      });

      // Send deployment transaction
      const txHash = await walletClient.sendTransaction({
        data: deployData,
        chain: arcTestnet,
        account,
      });

      console.log(`   Transaction: ${txHash}`);
      console.log(`   Waiting for confirmation...`);

      const receipt = await publicClient.waitForTransactionReceipt({ hash: txHash });
      
      if (!receipt.contractAddress) {
        throw new Error('No contract address in receipt');
      }

      console.log(`   ✓ Deployed at: ${receipt.contractAddress}`);
      console.log(`   Gas used: ${receipt.gasUsed}`);

      deployments[chainId][contractName] = {
        address: receipt.contractAddress,
        txHash,
        deployedAt: new Date().toISOString(),
      };

      saveDeployments(deployments);
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
