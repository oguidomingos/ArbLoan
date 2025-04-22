// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IMockAttacker {
    function hasAttacked() external view returns (bool);
    function onERC20Transfer(address token, uint256 amount) external;
}