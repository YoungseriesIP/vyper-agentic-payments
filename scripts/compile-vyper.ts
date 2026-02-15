/**
 * Vyper Contract Compiler
 *
 * Compiles .vy files to ABI + bytecode artifacts.
 *
 * Usage:
 *   npx tsx scripts/compile-vyper.ts --all              # Compile all contracts
 *   npx tsx scripts/compile-vyper.ts contracts/X.vy    # Compile single contract
 */

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const CONTRACTS_DIR = path.join(process.cwd(), 'contracts');
const ARTIFACTS_DIR = path.join(process.cwd(), 'artifacts');

interface Artifact {
  contractName: string;
  abi: unknown[];
  bytecode: string;
  sourceFile: string;
  compiledAt: string;
}

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function getContractName(filePath: string): string {
  return path.basename(filePath, '.vy');
}

function compileContract(vyperFile: string): Artifact {
  const contractName = getContractName(vyperFile);
  const absolutePath = path.isAbsolute(vyperFile)
    ? vyperFile
    : path.join(process.cwd(), vyperFile);

  if (!fs.existsSync(absolutePath)) {
    throw new Error(`File not found: ${absolutePath}`);
  }

  console.log(`Compiling ${contractName}...`);

  // Get ABI
  let abiJson: string;
  try {
    abiJson = execSync(`vyper -f abi "${absolutePath}"`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch (error: unknown) {
    const err = error as { stderr?: string; message?: string };
    throw new Error(`Failed to compile ABI for ${contractName}: ${err.stderr || err.message}`);
  }

  // Get bytecode
  let bytecode: string;
  try {
    bytecode = execSync(`vyper -f bytecode "${absolutePath}"`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch (error: unknown) {
    const err = error as { stderr?: string; message?: string };
    throw new Error(`Failed to compile bytecode for ${contractName}: ${err.stderr || err.message}`);
  }

  // Parse ABI
  let abi: unknown[];
  try {
    abi = JSON.parse(abiJson);
  } catch {
    throw new Error(`Invalid ABI JSON for ${contractName}: ${abiJson.substring(0, 100)}...`);
  }

  // Ensure bytecode has 0x prefix
  if (!bytecode.startsWith('0x')) {
    bytecode = '0x' + bytecode;
  }

  return {
    contractName,
    abi,
    bytecode,
    sourceFile: vyperFile,
    compiledAt: new Date().toISOString(),
  };
}

function saveArtifact(artifact: Artifact): string {
  ensureDir(ARTIFACTS_DIR);
  const outputPath = path.join(ARTIFACTS_DIR, `${artifact.contractName}.json`);
  fs.writeFileSync(outputPath, JSON.stringify(artifact, null, 2));
  return outputPath;
}

function getAllContracts(): string[] {
  if (!fs.existsSync(CONTRACTS_DIR)) {
    throw new Error(`Contracts directory not found: ${CONTRACTS_DIR}`);
  }

  return fs
    .readdirSync(CONTRACTS_DIR)
    .filter((f) => f.endsWith('.vy') && !f.startsWith('I')) // Skip interface files
    .map((f) => path.join(CONTRACTS_DIR, f));
}

function main(): void {
  const args = process.argv.slice(2);

  let contractFiles: string[];

  if (args.includes('--all') || args.length === 0) {
    contractFiles = getAllContracts();
    console.log(`Found ${contractFiles.length} contracts to compile\n`);
  } else {
    // Compile specific file(s)
    contractFiles = args.filter((arg) => arg.endsWith('.vy'));
    if (contractFiles.length === 0) {
      console.error('Usage:');
      console.error('  npx tsx scripts/compile-vyper.ts --all');
      console.error('  npx tsx scripts/compile-vyper.ts contracts/AgentIdentity.vy');
      process.exit(1);
    }
  }

  const results: { name: string; success: boolean; error?: string }[] = [];

  for (const file of contractFiles) {
    try {
      const artifact = compileContract(file);
      const outputPath = saveArtifact(artifact);
      console.log(`  ✅ ${artifact.contractName}`);
      console.log(`     ABI: ${artifact.abi.length} entries`);
      console.log(`     Bytecode: ${artifact.bytecode.length} chars`);
      console.log(`     Saved: ${outputPath}\n`);
      results.push({ name: artifact.contractName, success: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`  ❌ ${getContractName(file)}: ${message}\n`);
      results.push({ name: getContractName(file), success: false, error: message });
    }
  }

  // Summary
  console.log('========================================');
  console.log('COMPILATION SUMMARY');
  console.log('========================================');
  const passed = results.filter((r) => r.success).length;
  const failed = results.filter((r) => !r.success).length;
  console.log(`✅ ${passed} succeeded`);
  if (failed > 0) {
    console.log(`❌ ${failed} failed`);
    process.exit(1);
  }
}

main();
