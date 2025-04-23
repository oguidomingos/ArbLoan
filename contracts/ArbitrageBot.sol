// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./interfaces/IUniswapV2Router.sol";

contract ArbitrageBot is Ownable, ReentrancyGuard {
    struct ArbitrageParams {
        address tokenIn;
        address tokenOut;
        uint256 amount;
        uint8 buyDexIndex;
        uint8 sellDexIndex;
    }
    struct DexInfo {
        IUniswapV2Router router;
        string name;
        bool enabled;
    }

    mapping(uint8 => DexInfo) public dexes;
    uint8 public dexCount;
    
    event ArbitrageExecuted(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        string buyDex,
        string sellDex
    );

    event DexAdded(uint8 indexed index, address router, string name);
    event DexUpdated(uint8 indexed index, address router, string name, bool enabled);

    constructor() {
        _transferOwnership(msg.sender);
    }

    function addDex(address _router, string memory _name) external onlyOwner {
        require(dexCount < 255, "Max DEX count reached");
        require(_router != address(0), "Invalid router address");
        
        dexes[dexCount] = DexInfo({
            router: IUniswapV2Router(_router),
            name: _name,
            enabled: true
        });

        emit DexAdded(dexCount, _router, _name);
        dexCount++;
    }

    function updateDex(uint8 _index, address _router, string memory _name, bool _enabled) external onlyOwner {
        require(_index < dexCount, "Invalid DEX index");
        require(_router != address(0), "Invalid router address");

        dexes[_index] = DexInfo({
            router: IUniswapV2Router(_router),
            name: _name,
            enabled: _enabled
        });

        emit DexUpdated(_index, _router, _name, _enabled);
    }

    function executeArbitrage(ArbitrageParams memory params) external onlyOwner nonReentrant {
        require(params.buyDexIndex < dexCount && params.sellDexIndex < dexCount, "Invalid DEX index");
        require(dexes[params.buyDexIndex].enabled && dexes[params.sellDexIndex].enabled, "DEX not enabled");
        
        DexInfo storage buyDex = dexes[params.buyDexIndex];
        DexInfo storage sellDex = dexes[params.sellDexIndex];

        IERC20(params.tokenIn).approve(address(buyDex.router), params.amount);
        
        address[] memory path = new address[](2);
        path[0] = params.tokenIn;
        path[1] = params.tokenOut;

        // Execute buy on first DEX
        uint256[] memory amounts = buyDex.router.swapExactTokensForTokens(
            params.amount,
            0, // Accept any amount
            path,
            address(this),
            block.timestamp
        );

        // Execute sell on second DEX
        IERC20(params.tokenOut).approve(address(sellDex.router), amounts[1]);
        
        address[] memory reversePath = new address[](2);
        reversePath[0] = params.tokenOut;
        reversePath[1] = params.tokenIn;

        uint256[] memory finalAmounts = sellDex.router.swapExactTokensForTokens(
            amounts[1],
            0, // Accept any amount
            reversePath,
            address(this),
            block.timestamp
        );

        require(finalAmounts[1] > params.amount, "No profit made");

        emit ArbitrageExecuted(
            params.tokenIn,
            params.tokenOut,
            params.amount,
            finalAmounts[1],
            buyDex.name,
            sellDex.name
        );
    }

    function withdrawToken(address _token, uint256 _amount) external onlyOwner {
        IERC20(_token).transfer(owner(), _amount);
    }
}