// SPDX‑License‑Identifier: MIT
pragma solidity ^0.8.20;

/// @title Minimal ERC‑20 token (no dependencies)
/// @notice Used to represent hospital datasets as fungible assets.
contract Token {
    // ERC‑20 basics
    string  public name;
    string  public symbol;
    uint8   public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(
        string memory name_,
        string memory symbol_,
        uint256 initialSupply_,
        address owner_
    ) {
        name        = name_;
        symbol      = symbol_;
        totalSupply = initialSupply_;
        balanceOf[owner_] = initialSupply_;
        emit Transfer(address(0), owner_, initialSupply_);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "ERC20: balance too low");
        _move(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= value, "ERC20: allowance too low");
        allowance[from][msg.sender] = allowed - value;
        _move(from, to, value);
        return true;
    }

    // ---- internal ----
    function _move(address from, address to, uint256 value) internal {
        balanceOf[from] -= value;
        balanceOf[to]   += value;
        emit Transfer(from, to, value);
    }
}
