// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IUniswapV2Router.sol";
import "../interfaces/IMockAttacker.sol";

contract MockUniswapV2Router is IUniswapV2Router {
    uint256 public slippageFactor = 100; // 100 = no slippage, 90 = 10% slippage
    uint256 private constant PROFIT_FACTOR = 150; // 50% profit para garantir que o primeiro swap seja lucrativo

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
        
        // Transfer tokens from sender to this contract
        IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        
        amounts = new uint256[](path.length);
        amounts[0] = amountIn;
        
        // Para o primeiro swap (do atacante), use PROFIT_FACTOR para garantir lucro
        try IMockAttacker(msg.sender).hasAttacked() returns (bool attacked) {
            if (attacked) {
                amounts[1] = (amountIn * PROFIT_FACTOR) / 100;
                // Tenta reentrar antes de transferir os tokens
                IMockAttacker(msg.sender).onERC20Transfer(path[0], amounts[1]);
            } else {
                amounts[1] = (amountIn * slippageFactor) / 100;
            }
        } catch {
            amounts[1] = (amountIn * slippageFactor) / 100;
        }
        
        // Transfer output tokens to recipient
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