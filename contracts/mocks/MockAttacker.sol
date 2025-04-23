// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../ArbitrageBot.sol";
import "../interfaces/IMockAttacker.sol";
import "../interfaces/IUniswapV2Router.sol";

contract MockAttacker is IMockAttacker, IUniswapV2Router {
    ArbitrageBot public target;
    bool public hasAttacked;
    bool public isReentering;
    address public storedTokenIn;
    address public storedTokenOut;
    uint256 public storedAmount;

    constructor(address _target) {
        target = ArbitrageBot(_target);
    }

    function attack(address tokenIn, address tokenOut, uint256 amount) external {
        require(!hasAttacked, "Already attacked");
        hasAttacked = true;

        // Store token addresses for reentrant attack
        storedTokenIn = tokenIn;
        storedTokenOut = tokenOut;
        storedAmount = amount;

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

    // Implementação das funções da interface IUniswapV2Router
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory) {
        require(deadline >= block.timestamp, "EXPIRED");
        
        IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        
        uint256[] memory amounts = new uint256[](2);
        amounts[0] = amountIn;
        amounts[1] = amountIn * 150 / 100; // 50% de lucro
        
        // Tenta reentrar antes de transferir os tokens
        if (hasAttacked && !isReentering) {
            this.onERC20Transfer(path[0], amounts[1]);
        }
        
        IERC20(path[1]).transfer(to, amounts[1]);
        return amounts;
    }

    function factory() external pure returns (address) { return address(0); }
    function WETH() external pure returns (address) { return address(0); }
    function addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256) external pure returns (uint256,uint256,uint256) { return (0,0,0); }
    function addLiquidityETH(address,uint256,uint256,uint256,address,uint256) external payable returns (uint256,uint256,uint256) { return (0,0,0); }
    function removeLiquidity(address,address,uint256,uint256,uint256,address,uint256) external pure returns (uint256,uint256) { return (0,0); }
    function removeLiquidityETH(address,uint256,uint256,uint256,address,uint256) external pure returns (uint256,uint256) { return (0,0); }
    function swapTokensForExactTokens(uint256,uint256,address[] calldata,address,uint256) external pure returns (uint256[] memory) { return new uint256[](0); }
    function swapExactETHForTokens(uint256,address[] calldata,address,uint256) external payable returns (uint256[] memory) { return new uint256[](0); }
    function swapTokensForExactETH(uint256,uint256,address[] calldata,address,uint256) external pure returns (uint256[] memory) { return new uint256[](0); }
    function swapExactTokensForETH(uint256,uint256,address[] calldata,address,uint256) external pure returns (uint256[] memory) { return new uint256[](0); }
    function swapETHForExactTokens(uint256,address[] calldata,address,uint256) external payable returns (uint256[] memory) { return new uint256[](0); }
    function quote(uint256,uint256,uint256) external pure returns (uint256) { return 0; }
    function getAmountOut(uint256,uint256,uint256) external pure returns (uint256) { return 0; }
    function getAmountIn(uint256,uint256,uint256) external pure returns (uint256) { return 0; }
    function getAmountsOut(uint256,address[] calldata) external pure returns (uint256[] memory) { return new uint256[](0); }
    function getAmountsIn(uint256,address[] calldata) external pure returns (uint256[] memory) { return new uint256[](0); }

    function onERC20Transfer(address token, uint256 amount) external override {
        if (hasAttacked && !isReentering) {
            isReentering = true;

            ArbitrageBot.ArbitrageParams memory params = ArbitrageBot.ArbitrageParams({
                tokenIn: storedTokenIn,
                tokenOut: storedTokenOut,
                amount: storedAmount,
                buyDexIndex: 0,
                sellDexIndex: 1
            });

            // Try to reenter
            target.executeArbitrage(params);

            isReentering = false;
        }
    }

    receive() external payable {
        // Not used in this version since we're using ERC20 callbacks
    }
}