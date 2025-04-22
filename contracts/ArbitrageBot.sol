// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@aave/core-v3/contracts/interfaces/IPool.sol";
import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import "@aave/core-v3/contracts/flashloan/base/FlashLoanReceiverBase.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./interfaces/IUniswapV2Router.sol";


contract ArbitrageBot is FlashLoanReceiverBase {
    IPool public LENDING_POOL;
    address public owner;
    address public constant QUICKSWAP_ROUTER = 0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff;
    address public constant SUSHISWAP_ROUTER = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;

    event ArbitrageResult(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 profit,
        uint256 gasUsed,
        bool success,
        string message
    );

    constructor(address _lendingPoolAddressesProvider) FlashLoanReceiverBase(IPoolAddressesProvider(_lendingPoolAddressesProvider)) {
        owner = msg.sender;
        LENDING_POOL = IPool(IPoolAddressesProvider(_lendingPoolAddressesProvider).getPool());
    }

    function initiateArbitrage(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        address buyDex,
        address sellDex
    ) external {
        require(msg.sender == owner, "Only owner");
        
        address[] memory assets = new address[](1);
        assets[0] = tokenIn;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0; // No debt

        LENDING_POOL.flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            abi.encode(tokenIn, tokenOut, buyDex, sellDex),
            0
        );
    }

    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(LENDING_POOL), "Invalid caller");
        
        (address tokenIn, address tokenOut, address buyDex, address sellDex) = 
            abi.decode(params, (address, address, address, address));

        uint256 initialBalance = IERC20(tokenIn).balanceOf(address(this));
        bool success = true;
        string memory message = "Arbitragem completada com sucesso";

        try this._executeArbitrage(tokenIn, tokenOut, amounts[0], buyDex, sellDex) {
            uint256 finalBalance = IERC20(tokenIn).balanceOf(address(this));
            uint256 profit = finalBalance > initialBalance ? 
                finalBalance - initialBalance - premiums[0] : 0;

            // Repagar flash loan
            uint256 amountOwing = amounts[0] + premiums[0];
            IERC20(tokenIn).approve(address(LENDING_POOL), amountOwing);

            // Registrar resultado
            emit ArbitrageResult(
                tokenIn,
                tokenOut,
                profit,
                gasleft(),
                success,
                message
            );

        } catch {
            success = false;
            message = "Falha na execucao da arbitragem";
            
            emit ArbitrageResult(
                tokenIn,
                tokenOut,
                0,
                gasleft(),
                success,
                message
            );
        }

        return true;
    }

    function _executeArbitrage(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        address buyDex,
        address sellDex
    ) external {
        require(msg.sender == address(this), "Somente chamada interna");

        // Aprovar buyDex para gastar tokenIn
        IERC20(tokenIn).approve(buyDex, amount);

        // Comprar tokenOut na buyDex
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        IUniswapV2Router(buyDex).swapExactTokensForTokens(
            amount,
            0, // Aceitar qualquer quantidade (será verificado depois)
            path,
            address(this),
            block.timestamp
        );

        // Aprovar sellDex para gastar tokenOut
        uint256 tokenOutBalance = IERC20(tokenOut).balanceOf(address(this));
        IERC20(tokenOut).approve(sellDex, tokenOutBalance);

        // Vender tokenOut na sellDex
        path[0] = tokenOut;
        path[1] = tokenIn;

        IUniswapV2Router(sellDex).swapExactTokensForTokens(
            tokenOutBalance,
            0, // Aceitar qualquer quantidade (verificação de lucro feita depois)
            path,
            address(this),
            block.timestamp
        );
    }

    function withdraw(address token) external {
        require(msg.sender == owner, "Only owner");
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner, balance);
    }
}