// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../../contracts/ArbitrageBot.sol";

contract MockAttacker {
    ArbitrageBot public target;
    bool public hasAttacked;

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

    // This function will be called during the token transfer
    function onERC20Transfer(address token, uint256 amount) external {
        if (hasAttacked) {
            ArbitrageBot.ArbitrageParams memory params = ArbitrageBot.ArbitrageParams({
                tokenIn: token,
                tokenOut: token,
                amount: amount,
                buyDexIndex: 0,
                sellDexIndex: 1
            });

            // Try to reenter
            target.executeArbitrage(params);
        }
    }
}