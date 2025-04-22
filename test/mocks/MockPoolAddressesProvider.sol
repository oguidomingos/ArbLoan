// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";

contract MockPoolAddressesProvider is IPoolAddressesProvider {
    address private _pool;
    address private _priceOracle;
    
    function setPool(address pool) external {
        _pool = pool;
    }

    function getPool() external view override returns (address) {
        return _pool;
    }

    // Implementações mínimas necessárias da interface
    
    function getMarketId() external view override returns (string memory) {
        return "Mock Aave Market";
    }
    
    function setMarketId(string calldata marketId) external override {}
    
    function getAddress(bytes32 id) external view override returns (address) {
        return address(0);
    }
    
    function setAddressAsProxy(bytes32 id, address implementationAddress) external override {}
    
    function setAddress(bytes32 id, address newAddress) external override {}
    
    function getACLManager() external view override returns (address) {
        return address(0);
    }
    
    function setACLManager(address newAclManager) external override {}
    
    function getACLAdmin() external view override returns (address) {
        return address(0);
    }
    
    function setACLAdmin(address newAclAdmin) external override {}
    
    function getPriceOracle() external view override returns (address) {
        return _priceOracle;
    }
    
    function setPriceOracle(address newPriceOracle) external override {
        _priceOracle = newPriceOracle;
    }
    
    function getPriceOracleSentinel() external view override returns (address) {
        return address(0);
    }
    
    function setPriceOracleSentinel(address newPriceOracleSentinel) external override {}
    
    function getPoolConfigurator() external view override returns (address) {
        return address(0);
    }
    
    function getPoolDataProvider() external view override returns (address) {
        return address(0);
    }
}