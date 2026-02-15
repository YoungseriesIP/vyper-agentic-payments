/**
 * setup-wallet.ts
 * 
 * Create and configure a Circle developer-controlled wallet for contract deployment.
 * This uses the Circle Developer-Controlled Wallets SDK.
 * 
 * Prerequisites:
 * - CIRCLE_API_KEY environment variable
 * - CIRCLE_ENTITY_SECRET environment variable
 * 
 * Usage:
 *   npx ts-node scripts/setup-wallet.ts
 */

import 'dotenv/config';
import { 
  initiateDeveloperControlledWalletsClient, 
  Blockchain 
} from '@circle-fin/developer-controlled-wallets';

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const CIRCLE_API_KEY = process.env.CIRCLE_API_KEY;
const CIRCLE_ENTITY_SECRET = process.env.CIRCLE_ENTITY_SECRET;

if (!CIRCLE_API_KEY) {
  console.error('❌ CIRCLE_API_KEY is required. Set it in your .env file.');
  process.exit(1);
}

if (!CIRCLE_ENTITY_SECRET) {
  console.error('❌ CIRCLE_ENTITY_SECRET is required. Set it in your .env file.');
  process.exit(1);
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function main(): Promise<void> {
  console.log('╔════════════════════════════════════════════════════════════════╗');
  console.log('║           Circle Developer Wallet Setup                        ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  // Initialize the Circle SDK client
  const client = initiateDeveloperControlledWalletsClient({
    apiKey: CIRCLE_API_KEY as string,
    entitySecret: CIRCLE_ENTITY_SECRET as string,
  });

  // Step 1: Create a wallet set
  console.log('📁 Creating wallet set...');
  const walletSetResponse = await client.createWalletSet({
    name: `vyper-agentic-payments-${Date.now()}`,
  });

  if (!walletSetResponse.data?.walletSet) {
    console.error('❌ Failed to create wallet set');
    process.exit(1);
  }

  const walletSetId = walletSetResponse.data.walletSet.id;
  console.log(`   ✓ Wallet set created: ${walletSetId}\n`);

  // Step 2: Create a wallet for testnet
  // Note: Circle SDK uses blockchain identifiers - using ETH-SEPOLIA for testnet
  console.log('🔐 Creating wallet for deployment...');
  
  const walletsResponse = await client.createWallets({
    walletSetId,
    blockchains: [Blockchain.EthSepolia],
    count: 1,
    metadata: [
      {
        name: 'Vyper Agentic Payments Deployer',
        refId: 'deployer-wallet',
      },
    ],
  });

  if (!walletsResponse.data?.wallets?.length) {
    console.error('❌ Failed to create wallet');
    process.exit(1);
  }

  const wallet = walletsResponse.data.wallets[0];
  console.log(`   ✓ Wallet created!`);
  console.log(`   Address: ${wallet.address}`);
  console.log(`   Blockchain: ${wallet.blockchain}`);
  console.log(`   Wallet ID: ${wallet.id}\n`);

  // Step 3: Display summary
  console.log('═══════════════════════════════════════════════════════════════════');
  console.log('WALLET SETUP COMPLETE');
  console.log('═══════════════════════════════════════════════════════════════════\n');
  
  console.log('Add these to your .env file:\n');
  console.log(`CIRCLE_WALLET_SET_ID=${walletSetId}`);
  console.log(`CIRCLE_WALLET_ID=${wallet.id}`);
  console.log(`DEPLOYER_ADDRESS=${wallet.address}\n`);
  
  console.log('Next steps:');
  console.log('1. Fund the wallet with testnet ETH for gas');
  console.log('2. Run: npx ts-node scripts/deploy-viem.ts');
  console.log('');
  console.log('For Arc Testnet:');
  console.log('- Get testnet USDC from Circle faucet');
  console.log('- RPC: https://rpc.testnet.arc.circle.com');
  console.log('- Chain ID: 5042002');
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
