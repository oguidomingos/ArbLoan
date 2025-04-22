require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      viaIR: true,
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    polygon: {
      url: "https://polygon-rpc.com",
      chainId: 137,
      accounts: ["a900d27668eeb4428bdbc275456f6e27588480a3b64687177a08858606f60d5f"]
    },
    mumbai: {
      url: "https://rpc-mumbai.maticvigil.com",
      chainId: 80001,
      accounts: ["a900d27668eeb4428bdbc275456f6e27588480a3b64687177a08858606f60d5f"]
    }
  }
};