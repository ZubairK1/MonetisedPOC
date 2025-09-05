"""Compile & deploy HAPD and HBTD ERC‑20 tokens to a local Anvil chain.

• Launch Anvil once (choose either free‑gas or fee mode):
    # Zero‑gas demo (no ETH needed)
    anvil --base-fee 0 --port 8545 &

    # OR simulate real gas fees (baseFee = 1 gwei)
    anvil --port 8545 &

• Then run:
    python deploy.py

If `HOSP_A_PK` / `HOSP_B_PK` are **unset**, the script:
1. Generates two brand‑new wallets.
2. If the chain’s base‑fee > 0, auto‑funds each wallet with 1 ETH from Anvil’s
   unlocked coinbase account (no private key needed).
3. Saves private keys and contract addresses in `deploy.json`.
"""
import json, os
from pathlib import Path
from solcx import compile_standard, install_solc
from web3 import Web3
from eth_account import Account

# ── Chain / compiler config ───────────────────────────────────────────────────
RPC_URL        = os.getenv("RPC_URL", "http://127.0.0.1:8545")
CHAIN_ID       = 31337
SOLC_VERSION   = "0.8.20"
INITIAL_SUPPLY = 1_000 * 10**18  # 1 M tokens (18 decimals)

# ── Resolve / create hospital wallets ────────────────────────────────────────
PK_A = os.getenv("HOSP_A_PK")
PK_B = os.getenv("HOSP_B_PK")
if not PK_A or not PK_B:
    print("[*] Generating fresh hospital wallets …")
    acct_a = Account.create(); PK_A = acct_a.key.hex()
    acct_b = Account.create(); PK_B = acct_b.key.hex()
else:
    acct_a = Account.from_key(PK_A)
    acct_b = Account.from_key(PK_B)

# ── Resolve / create requestor wallet ────────────────────────────────────────
PK_REQ = os.getenv("REQUESTOR_PK")
if not PK_REQ:
    print("[*] Generating fresh requestor wallet …")
    acct_req = Account.create(); PK_REQ = acct_req.key.hex()
else:
    acct_req = Account.from_key(PK_REQ)

# ── Connect to Anvil ─────────────────────────────────────────────────────────
w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), f"Web3 not connected to {RPC_URL}"

#base_fee_zero = w3.eth.gas_price == 0
base_fee_zero = w3.eth.get_block("latest")["baseFeePerGas"] == 0


if base_fee_zero:
    fee_kwargs = {"gasPrice": 0}
else:
    fee_kwargs = {
        "maxFeePerGas":        w3.to_wei(2, "gwei"),
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
    }

# ── Auto‑fund wallets only if the chain charges gas ──────────────────────────
if not base_fee_zero:
    coinbase = w3.eth.accounts[0]  # unlocked by Anvil
    for addr in (acct_a.address, acct_b.address, acct_req.address):
        if w3.eth.get_balance(addr) == 0:
            tx_hash = w3.eth.send_transaction({
                "from":  coinbase,
                "to":    addr,
                "value":  w3.to_wei(1, "ether"),
            })
            w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"    Funded {addr[:10]}… with 1 ETH")

# ── Compile Token.sol ─────────────────────────────────────────────────────────
print("[*] Compiling Solidity …")
install_solc(SOLC_VERSION)
source = Path("contracts/Token.sol").read_text()
compiled = compile_standard({
    "language": "Solidity",
    "sources": {"Token.sol": {"content": source}},
    "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}},
}, solc_version=SOLC_VERSION)
artifact = compiled["contracts"]["Token.sol"]["Token"]
abi = artifact["abi"]
bytecode = artifact["evm"]["bytecode"]["object"]
Token = w3.eth.contract(abi=abi, bytecode=bytecode)

# ── Helper to deploy each token ──────────────────────────────────────────────
def deploy_token(name, symbol, owner_pk):
    owner = Account.from_key(owner_pk).address
    tx = Token.constructor(name, symbol, INITIAL_SUPPLY, owner).build_transaction({
        "from": owner,
        "nonce": w3.eth.get_transaction_count(owner),
        "chainId": CHAIN_ID,
        "gas": 3_000_000,
        **fee_kwargs,
    })
    signed = w3.eth.account.sign_transaction(tx, owner_pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"    ✓ Deployed {symbol} at {receipt.contractAddress}")
    return receipt.contractAddress, tx_hash.hex()

# ── Deploy tokens ────────────────────────────────────────────────────────────
print("[*] Deploying hospital tokens …")
hapd_addr, hapd_tx = deploy_token("Hospital A Patient Data", "HAPD", PK_A)
hbtd_addr, hbtd_tx = deploy_token("Hospital B Treatment Data", "HBTD", PK_B)

# ── Transfer initial HAPD tokens to requestor ───────────────────────────────
print("[*] Funding requestor with HAPD tokens …")
hapd = w3.eth.contract(address=hapd_addr, abi=abi)
owner = Account.from_key(PK_A).address
init_amt = 1000 * 10**18  # 1000 HAPD
tx = hapd.functions.transfer(acct_req.address, init_amt).build_transaction({
    "from": owner,
    "nonce": w3.eth.get_transaction_count(owner),
    "chainId": CHAIN_ID,
    "gas": 200_000,
    **fee_kwargs,
})
signed = w3.eth.account.sign_transaction(tx, PK_A)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"    ✓ Sent {init_amt // 10**18} HAPD to requestor {acct_req.address[:8]}…")

# ── Transfer initial HBTD tokens to requestor ───────────────────────────
print("[*] Funding requestor with HBTD tokens …")
hbtd = w3.eth.contract(address=hbtd_addr, abi=abi)
owner = Account.from_key(PK_B).address
init_amt = 1000 * 10**18  # 1000 HBTD
tx = hbtd.functions.transfer(acct_req.address, init_amt).build_transaction({
    "from": owner,
    "nonce": w3.eth.get_transaction_count(owner),
    "chainId": CHAIN_ID,
    "gas": 200_000,
    **fee_kwargs,
})
signed = w3.eth.account.sign_transaction(tx, PK_B)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"    ✓ Sent {init_amt // 10**18} HBTD to requestor {acct_req.address[:8]}…")
# ── Persist metadata for downstream scripts ──────────────────────────────────

meta = {
    "HAPD":   {"address": hapd_addr, "deploy_tx": hapd_tx},
    "HBTD":   {"address": hbtd_addr, "deploy_tx": hbtd_tx},
    "acct_a": acct_a.address,
    "acct_b": acct_b.address,
    "acct_req": acct_req.address,
    "priv_a": PK_A,
    "priv_b": PK_B,
    "priv_req": PK_REQ,
}
Path("deploy.json").write_text(json.dumps(meta, indent=2))
Path("abi.json").write_text(json.dumps(abi, indent=2))

print("[✔] Deployment complete – details saved to deploy.json")