// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IUniswapV2Router.sol";
import "../interfaces/IMockAttacker.sol";
import "../interfaces/IArbitrageBot.sol";

contract MockUniswapV2Router is IUniswapV2Router {
    uint256 public slippageFactor = 100; // 100 = no slippage, 90 = 10% slippage
    uint256 private constant PROFIT_FACTOR = 150; // 50% profit para garantir que o primeiro swap seja lucrativo
    bool public isAttacking;
    address public targetBot;

    constructor() {
        isAttacking = false;
    }

    function setTargetBot(address _target) external {
        targetBot = _target;
    }

    function setSlippageFactor(uint256 _slippageFactor) external {
        slippageFactor = _slippageFactor;
    }

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "EXPIRED");
        require(path.length >= 2, "INVALID_PATH");

        // Transfer tokens from sender to this contract (ArbitrageBot)
        IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        
        amounts = new uint256[](path.length);
        amounts[0] = amountIn;
        amounts[1] = (amountIn * PROFIT_FACTOR) / 100;

        // Se o chamador é o bot alvo e não estamos no meio de um ataque, tenta reentrar
        if (!isAttacking && msg.sender == targetBot) {
            isAttacking = true;

            // Tenta executar outra arbitragem durante o swap
            bytes memory data = abi.encodeWithSignature(
                "executeArbitrage((address,address,uint256,uint8,uint8))",
                IArbitrageBot.ArbitrageParams({
                    tokenIn: path[0],
                    tokenOut: path[1],
                    amount: amountIn,
                    buyDexIndex: 0,
                    sellDexIndex: 1
                })
            );
            
            (bool success,) = targetBot.call(data);
            require(!success, "Reentrancy attack should have failed");

            isAttacking = false;
        }

        // Transfere os tokens
        IERC20(path[path.length-1]).transfer(to, amounts[1]);
        
        return amounts;
    }

    // Implementações simplificadas das outras funções requeridas
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
}