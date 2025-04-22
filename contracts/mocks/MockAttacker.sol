// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../ArbitrageBot.sol";
import "../interfaces/IMockAttacker.sol";

contract MockAttacker is IMockAttacker {
    ArbitrageBot public target;
    bool public hasAttacked;
    bool public isReentering;

    constructor(address _target) {
        target = ArbitrageBot(_target);
    }

    function attack(address tokenIn, address tokenOut, uint256 amount) external {
        require(!hasAttacked, "Already attacked");
        hasAttacked = true;

        // Approve tokens
        IERC20(tokenIn).approve(address(target), amount);

        // Create params for arbitrage
        ArbitrageBot.ArbitrageParams memory params = ArbitrageBot.ArbitrageParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            amount: amount,
            buyDexIndex: 0,
            sellDexIndex: 1
        });

        // Try to execute arbitrage
        target.executeArbitrage(params);
    }

    function onERC20Transfer(address token, uint256 amount) external override {
        // Not used in this version
    }

    // This function will be called when receiving ETH, attempting reentrancy
    receive() external payable {
        if (hasAttacked && !isReentering) {
            isReentering = true;

            // Get token addresses from stored state
            address tokenIn = address(0); // Will be set in test
            address tokenOut = address(0); // Will be set in test

            ArbitrageBot.ArbitrageParams memory params = ArbitrageBot.ArbitrageParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                amount: 1 ether,
                buyDexIndex: 0,
                sellDexIndex: 1
            });

            // Try to reenter
            target.executeArbitrage(params);

            isReentering = false;
        }
    }
}