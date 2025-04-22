// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@aave/core-v3/contracts/interfaces/IPool.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockPool is IPool {
    mapping(address => bool) public flashLoanInitiated;

    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external override {
        // Não implementado neste mock
        revert("Not implemented");
    }

    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external override {
        require(assets.length == amounts.length, "INCONSISTENT_PARAMS");
        require(assets.length == modes.length, "INCONSISTENT_PARAMS");

        // Marca flash loan como iniciado
        flashLoanInitiated[receiverAddress] = true;

        // Transfere tokens para o receiver
        for (uint i = 0; i < assets.length; i++) {
            IERC20(assets[i]).transfer(receiverAddress, amounts[i]);
        }

        // Chama executeOperation no receiver
        IFlashLoanReceiver receiver = IFlashLoanReceiver(receiverAddress);
        require(
            receiver.executeOperation(
                assets,
                amounts,
                new uint256[](assets.length), // premiums
                onBehalfOf,
                params
            ),
            "FLASH_LOAN_FAILED"
        );

        // Recebe tokens de volta
        for (uint i = 0; i < assets.length; i++) {
            IERC20(assets[i]).transferFrom(
                receiverAddress,
                address(this),
                amounts[i] // Na implementação real seria amounts[i] + premium
            );
        }

        // Reseta estado
        flashLoanInitiated[receiverAddress] = false;
    }

    // Funções dummy necessárias para interface IPool
    
    function supply(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external override {}
    
    function supplyWithPermit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode, uint256 deadline, uint8 permitV, bytes32 permitR, bytes32 permitS) external override {}
    
    function withdraw(address asset, uint256 amount, address to) external override returns (uint256) {return 0;}
    
    function borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf) external override {}
    
    function repay(address asset, uint256 amount, uint256 interestRateMode, address onBehalfOf) external override returns (uint256) {return 0;}
    
    function repayWithPermit(address asset, uint256 amount, uint256 interestRateMode, address onBehalfOf, uint256 deadline, uint8 permitV, bytes32 permitR, bytes32 permitS) external override returns (uint256) {return 0;}
    
    function repayWithATokens(address asset, uint256 amount, uint256 interestRateMode) external override returns (uint256) {return 0;}
    
    function swapBorrowRateMode(address asset, uint256 interestRateMode) external override {}
    
    function rebalanceStableBorrowRate(address asset, address user) external override {}
    
    function setUserUseReserveAsCollateral(address asset, bool useAsCollateral) external override {}
    
    function liquidationCall(address collateralAsset, address debtAsset, address user, uint256 debtToCover, bool receiveAToken) external override {}
    
    function getUserAccountData(address user) external view override returns (uint256 totalCollateralETH, uint256 totalDebtETH, uint256 availableBorrowsETH, uint256 currentLiquidationThreshold, uint256 ltv, uint256 healthFactor) {
        return (0,0,0,0,0,0);
    }
    
    function initReserve(address asset, address aTokenAddress, address stableDebtAddress, address variableDebtAddress, address interestRateStrategyAddress) external override {}
    
    function dropReserve(address asset) external override {}
    
    function setReserveInterestRateStrategyAddress(address asset, address rateStrategyAddress) external override {}
    
    function setConfiguration(address asset, ReserveConfigurationMap calldata configuration) external override {}
    
    function getConfiguration(address asset) external view override returns (ReserveConfigurationMap memory) {
        return ReserveConfigurationMap(0);
    }
    
    function getUserConfiguration(address user) external view override returns (UserConfigurationMap memory) {
        return UserConfigurationMap(0);
    }
    
    function getReserveNormalizedIncome(address asset) external view override returns (uint256) {return 0;}
    
    function getReserveNormalizedVariableDebt(address asset) external view override returns (uint256) {return 0;}
    
    function getReserveData(address asset) external view override returns (ReserveData memory) {
        return ReserveData(
            ReserveConfigurationMap(0),
            uint128(0),
            uint128(0),
            uint128(0),
            uint128(0),
            uint128(0),
            uint40(0),
            uint16(0),
            address(0),
            address(0),
            address(0),
            address(0),
            uint128(0),
            uint128(0),
            uint128(0)
        );
    }
    
    function finalizeTransfer(address asset, address from, address to, uint256 amount, uint256 balanceFromBefore, uint256 balanceToBefore) external override {}
    
    function getReservesList() external view override returns (address[] memory) {
        return new address[](0);
    }
    
    function ADDRESSES_PROVIDER() external view override returns (IPoolAddressesProvider) {
        return IPoolAddressesProvider(address(0));
    }
    
    function updateBridgeProtocolFee(uint256 protocolFee) external override {}
    
    function updateFlashloanPremiums(uint128 flashLoanPremiumTotal, uint128 flashLoanPremiumToProtocol) external override {}
    
    function configureEModeCategory(uint8 id, DataTypes.EModeCategory memory category) external override {}
    
    function getEModeCategoryData(uint8 id) external view override returns (DataTypes.EModeCategory memory) {
        return DataTypes.EModeCategory(0,0,address(0),"");
    }
    
    function setUserEMode(uint8 categoryId) external override {}
    
    function getUserEMode(address user) external view override returns (uint256) {return 0;}
    
    function resetIsolationModeTotalDebt(address asset) external override {}
    
    function MAX_STABLE_RATE_BORROW_SIZE_PERCENT() external view override returns (uint256) {return 0;}
    
    function FLASHLOAN_PREMIUM_TOTAL() external view override returns (uint128) {return 0;}
    
    function BRIDGE_PROTOCOL_FEE() external view override returns (uint256) {return 0;}
    
    function FLASHLOAN_PREMIUM_TO_PROTOCOL() external view override returns (uint128) {return 0;}
    
    function MAX_NUMBER_RESERVES() external view override returns (uint16) {return 0;}
}