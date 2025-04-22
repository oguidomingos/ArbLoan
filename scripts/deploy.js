const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);
  
  // Verificar saldo
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance), "MATIC");

  // Endereço do Aave Pool Addresses Provider na Polygon
  const AAVE_ADDRESSES_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";

  const ArbitrageBot = await hre.ethers.getContractFactory("ArbitrageBot");
  try {
    console.log("Deploying ArbitrageBot...");
    const arbitrageBot = await ArbitrageBot.deploy(AAVE_ADDRESSES_PROVIDER, {
      gasLimit: 2000000,
      gasPrice: hre.ethers.parseUnits("50", "gwei")
    });

    // Aguardar deploy
    const deploymentReceipt = await arbitrageBot.waitForDeployment();
    const deployedAddress = await arbitrageBot.getAddress();
    console.log("ArbitrageBot deployed to:", deployedAddress);
  } catch (error) {
    console.error("Error during deployment:", error);
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });