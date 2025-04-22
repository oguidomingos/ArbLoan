// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IMockRouter {
    function setRate(address tokenIn, address tokenOut, string memory rate) external;
    function getRate(address tokenIn, address tokenOut) external view returns (uint256);
    
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);
}