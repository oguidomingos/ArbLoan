const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("ArbitrageBot", function () {
  async function deployArbitrageBotFixture() {
    const [owner, otherAccount] = await ethers.getSigners();

    // Deploy mock tokens
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const tokenA = await MockERC20.deploy("Token A", "TKNA");
    const tokenB = await MockERC20.deploy("Token B", "TKNB");

    // Deploy mock routers
    const MockRouter = await ethers.getContractFactory("MockUniswapV2Router");
    const router1 = await MockRouter.deploy();
    const router2 = await MockRouter.deploy();

    // Deploy ArbitrageBot
    const ArbitrageBot = await ethers.getContractFactory("ArbitrageBot");
    const arbitrageBot = await ArbitrageBot.deploy();

    // Setup initial token balances
    const amount = ethers.utils.parseEther("1000");
    await tokenA.mint(owner.address, amount);
    await tokenB.mint(owner.address, amount);
    await tokenA.mint(router1.address, amount);
    await tokenB.mint(router1.address, amount);
    await tokenA.mint(router2.address, amount);
    await tokenB.mint(router2.address, amount);

    // Add DEXes to ArbitrageBot
    await arbitrageBot.addDex(router1.address, "DEX1");
    await arbitrageBot.addDex(router2.address, "DEX2");

    return { 
      arbitrageBot, 
      tokenA, 
      tokenB, 
      router1, 
      router2, 
      owner, 
      otherAccount,
      amount
    };
  }

  describe("Deployment", function () {
    it("Deve definir o owner correto", async function () {
      const { arbitrageBot, owner } = await loadFixture(deployArbitrageBotFixture);
      expect(await arbitrageBot.owner()).to.equal(owner.address);
    });

    it("Deve definir os endereços dos routers corretamente", async function () {
      const { arbitrageBot, router1, router2 } = await loadFixture(deployArbitrageBotFixture);
      const dex1 = await arbitrageBot.dexes(0);
      const dex2 = await arbitrageBot.dexes(1);
      expect(dex1.router).to.equal(router1.address);
      expect(dex2.router).to.equal(router2.address);
    });
  });

  describe("Arbitragem", function () {
    it("Deve permitir apenas o owner iniciar arbitragem", async function () {
      const { arbitrageBot, tokenA, tokenB, otherAccount } = await loadFixture(deployArbitrageBotFixture);
      
      const arbitrageParams = {
        tokenIn: tokenA.address,
        tokenOut: tokenB.address,
        amount: ethers.utils.parseEther("1"),
        buyDexIndex: 0,
        sellDexIndex: 1
      };

      await expect(
        arbitrageBot.connect(otherAccount).executeArbitrage(arbitrageParams)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Deve executar arbitragem com sucesso", async function () {
      const { arbitrageBot, tokenA, tokenB, owner, router1, router2 } = await loadFixture(deployArbitrageBotFixture);
      
      const amount = ethers.utils.parseEther("1");
      await tokenA.approve(arbitrageBot.address, amount);
      await tokenA.transfer(arbitrageBot.address, amount);

      // Configure mock routers to create a profitable trade
      await router1.setSlippageFactor(95); // 5% slippage
      await router2.setSlippageFactor(110); // 10% profit

      const arbitrageParams = {
        tokenIn: tokenA.address,
        tokenOut: tokenB.address,
        amount: amount,
        buyDexIndex: 0,
        sellDexIndex: 1
      };

      await expect(
        arbitrageBot.executeArbitrage(arbitrageParams)
      ).to.emit(arbitrageBot, "ArbitrageExecuted");
    });

    it("Deve falhar em caso de slippage alto", async function () {
      const { arbitrageBot, tokenA, tokenB, router1, router2 } = await loadFixture(deployArbitrageBotFixture);
      
      // Configurar preços para gerar slippage alto
      await router1.setSlippageFactor(80); // 20% slippage
      await router2.setSlippageFactor(70); // 30% slippage

      const amount = ethers.utils.parseEther("1");
      await tokenA.approve(arbitrageBot.address, amount);
      await tokenA.transfer(arbitrageBot.address, amount);

      const arbitrageParams = {
        tokenIn: tokenA.address,
        tokenOut: tokenB.address,
        amount: amount,
        buyDexIndex: 0,
        sellDexIndex: 1
      };

      await expect(
        arbitrageBot.executeArbitrage(arbitrageParams)
      ).to.be.revertedWith("No profit made");
    });

    it("Deve proteger contra ataques de reentrância", async function () {
      const [owner] = await ethers.getSigners();
      const { arbitrageBot, tokenA, tokenB } = await loadFixture(deployArbitrageBotFixture);
      
      // Configure os tokens
      const amount = ethers.utils.parseEther("1000");
      
      // Mint tokens para owner
      await tokenA.mint(owner.address, amount.mul(4));
      await tokenB.mint(owner.address, amount.mul(4));

      // Deploy o router malicioso
      const MockRouter = await ethers.getContractFactory("MockUniswapV2Router");
      const maliciousRouter = await MockRouter.deploy();
      
      // Configura o alvo do ataque
      await maliciousRouter.setTargetBot(arbitrageBot.address);

      // Transferir tokens para o router malicioso
      await tokenA.transfer(maliciousRouter.address, amount);
      await tokenB.transfer(maliciousRouter.address, amount);

      // Adicione o DEX malicioso como primeiro DEX
      await arbitrageBot.addDex(maliciousRouter.address, "MaliciousDEX");

      // Aprove e transfira tokens para o ArbitrageBot
      await tokenA.approve(arbitrageBot.address, amount);
      await tokenA.transfer(arbitrageBot.address, amount);

      // Aprova o router malicioso para gastar os tokens do ArbitrageBot
      await arbitrageBot.addDex(maliciousRouter.address, "MaliciousDEX2");

      const arbitrageParams = {
        tokenIn: tokenA.address,
        tokenOut: tokenB.address,
        amount: ethers.utils.parseEther("100"),
        buyDexIndex: 0,
        sellDexIndex: 1
      };

      // O ataque deve falhar devido ao ReentrancyGuard
      await expect(
        arbitrageBot.executeArbitrage(arbitrageParams)
      ).to.be.revertedWith("ReentrancyGuard: reentrant call");
    });
  });

  describe("Withdrawal", function () {
    it("Deve permitir apenas owner retirar tokens", async function () {
      const { arbitrageBot, tokenA, otherAccount } = await loadFixture(deployArbitrageBotFixture);
      
      const amount = ethers.utils.parseEther("1");
      await expect(
        arbitrageBot.connect(otherAccount).withdrawToken(tokenA.address, amount)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Deve retirar tokens com sucesso", async function () {
      const { arbitrageBot, tokenA, owner } = await loadFixture(deployArbitrageBotFixture);
      
      const amount = ethers.utils.parseEther("1");
      await tokenA.transfer(arbitrageBot.address, amount);

      await expect(
        arbitrageBot.withdrawToken(tokenA.address, amount)
      ).to.changeTokenBalance(tokenA, owner, amount);
    });
  });
});