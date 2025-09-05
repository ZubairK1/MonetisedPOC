#!/usr/bin/env python3
"""
swap.py — Swap 50 HAPD for 75 HBTD between Hospital A and Hospital B.

• Run after deploy.py creates deploy.json and abi.json.
• Works on both zero‑gas Anvil (--base-fee 0) and fee‑charging chains.
"""

import json
import os
from web3 import Web3
from eth_account import Account

# ── Connect to chain ─────────────────────────────────────────────────────────
RPC_URL  = os.getenv("RPC_URL", "http://127.0.0.1:8545")
CHAIN_ID = 31337
w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), f"Web3 not connected to {RPC_URL}"

# ── Fee settings auto‑adapt to chain ─────────────────────────────────────────
base_fee_zero = w3.eth.get_block("latest")["baseFeePerGas"] == 0
fee_kwargs = (
    {"gasPrice": 0}
    if base_fee_zero
    else {
        "maxFeePerGas":        w3.to_wei(2, "gwei"),
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
    }
)

# ── Swap amounts ─────────────────────────────────────────────────────────────
AMT_HAPD = 50 * 10**18
AMT_HBTD = 75 * 10**18

# ── Load metadata & ABI ──────────────────────────────────────────────────────
meta = json.load(open("deploy.json"))
abi  = json.load(open("abi.json"))

hapd = w3.eth.contract(address=meta["HAPD"]["address"], abi=abi)
hbtd = w3.eth.contract(address=meta["HBTD"]["address"], abi=abi)

PK_A = meta["priv_a"]            # Hospital A private key
PK_B = meta["priv_b"]            # Hospital B private key
acct_a = Account.from_key(PK_A)
acct_b = Account.from_key(PK_B)

print("[+] Swapping tokens …")

# ── Helper to send a transfer ────────────────────────────────────────────────
def send(contract, sender_pk, to_addr, amount):
    sender = Account.from_key(sender_pk).address
    tx = contract.functions.transfer(to_addr, amount).build_transaction({
        "from":   sender,
        "nonce":  w3.eth.get_transaction_count(sender),
        "chainId": CHAIN_ID,
        "gas":    200_000,
        **fee_kwargs,
    })
    signed = w3.eth.account.sign_transaction(tx, sender_pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    sym = contract.functions.symbol().call()
    print(
        f"    ✓ {amount // 10**18} {sym}  "
        f"{sender[:8]}… → {to_addr[:8]}…  "
        f"gasUsed={receipt.gasUsed:,}"
        f"  effectiveGasPrice={receipt.effectiveGasPrice / 1e9:.2f} gwei"
    )
    return tx_hash.hex()

# ── Execute the two legs of the swap ─────────────────────────────────────────
tx_hapd = send(hapd, PK_A, acct_b.address, AMT_HAPD)  # A → B
tx_hbtd = send(hbtd, PK_B, acct_a.address, AMT_HBTD)  # B → A

# ── Persist tx hashes back into deploy.json ──────────────────────────────────
meta["swap"] = {"hapd_tx": tx_hapd, "hbtd_tx": tx_hbtd}
json.dump(meta, open("deploy.json", "w"), indent=2)

print("[✔] Swap complete – tx hashes stored in deploy.json")
