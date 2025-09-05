
# 🏥 Hospital‑to‑Hospital Data Exchange POC

**End‑to‑end demo:** two hospitals tokenise their private datasets as ERC‑20 tokens, swap access rights, and unlock analytics—all on an Ethereum chain you can run locally or point at a public testnet.

- **Portable** – one codebase works in free‑gas mode *and* gas‑fee mode.
- **Hands‑free wallets** – if you don’t set any private keys the scripts create, fund, and persist two brand‑new wallets for you.
- **Verifiable** – every contract address, tx hash, token balance, and gas burn is saved or printed so you can show auditors.

---

## 📂 Repo layout

*(**`contracts/Token.sol`** ****is committed**** so anyone can verify or recompile the exact byte‑code.)*

```
repo/
├─ contracts/Token.sol          # minimal ERC‑20 (represents a hospital dataset)
├─ data/                        # hospital CSVs (A & B)
├─ deploy.py                    # compile + deploy tokens (auto wallets / auto funding)
├─ swap.py                      # 50 HAPD ⇄ 75 HBTD (fee‑aware)
├─ analytics.py                 # show merged KPI (length of stay vs success rate)
├─ check_balances.py            # print token + ETH balances (optional)
├─ main.py                      # simple CLI wrapper (deploy → swap → analytics)
├─ requirements.txt             # pip deps
└─ README.md                    # this file
```
---

## ⚡ Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. launch a dev chain  (choose ↓)
#    —— FREE‑GAS demo ——         # no ETH needed at all
anvil --base-fee 0 --port 8545 &

#    —— GAS‑FEE simulation ——    # 1 ETH auto‑funded to each wallet
anvil --base-fee 10 --port 8545 &

# 2. run the guided menu
python main.py     # press 1 → 2 → 3
```

Or run the scripts yourself:

```bash
python deploy.py      # compile & deploy HAPD/HBTD (wallets auto‑generated)
python swap.py        # 50 HAPD → B   |   75 HBTD → A
python analytics.py   # merged KPI printed
python check_balances.py   # (optional) see token + ETH balances
```

---

## 🧩 What the on‑chain *contract* actually does

`contracts/Token.sol` is a **40‑line, dependency‑free ERC‑20** whose *only* purpose is to treat each hospital’s dataset as a fungible, transferable asset.

- **Total supply = dataset size proxy.** We mint the whole supply (1 M tokens) to the data owner at deployment; no further mint/burn—so token balance directly mirrors access rights.
- **No advanced features.** No pausing, blacklisting, or owner‑only hooks. Keeping the ABI minimal makes the byte‑code trivial to audit.
- **18 decimals** to stay compatible with wallets and off‑the‑shelf explorers.
- **Why not ERC‑721 / Ocean datatokens?** ERC‑20 is universally supported; for this POC we care about *provable exchange*, not fine‑grained licensing.

The contract therefore serves as a **cryptographic receipt**: holding HAPD or HBTD is equivalent to holding permission to analyse Hospital A’s patient data or Hospital B’s treatment data.

---

## 🔎 What the demo proves

| Phase            | On‑chain artefacts                                                | Off‑chain evidence                                         |
| ---------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- |
| **Tokenisation** | Two ERC‑20 byte‑codes + ABIs; contract addrs in `deploy.json`     | `deploy.py` console logs + JSON metadata                   |
| **Ownership**    | 1 000 000 HAPD minted to Hospital A; 1 000 000 HBTD to Hospital B | `check_balances.py` shows initial split                    |
| **Swap**         | Two `transfer` tx hashes saved as `swap.hapd_tx`, `swap.hbtd_tx`  | `swap.py` prints gasUsed & effectiveGasPrice               |
| **Value unlock** | n/a                                                               | `analytics.py` joins the CSVs and prints new insight table |

### Seeing gas fees

Run in gas‑fee mode and then:

```bash
python check_balances.py   # shows ETH balance drop (~0.00005 ETH per tx)
```

### Wallet handling

- **No env vars**? `deploy.py` calls `Account.create()` twice and persists `priv_a` / `priv_b` in `deploy.json`.
- **Gas‑fee mode**? `deploy.py` auto‑funds each new wallet with 1 ETH using Anvil’s unlocked coinbase account—no private key needed.
- **Provide your own keys**? Export `HOSP_A_PK` / `HOSP_B_PK` before running.

---

## 🛠 Customisation

| Need                 | Where to tweak                                                    |
| -------------------- | ----------------------------------------------------------------- |
| Swap amounts         | `AMT_HAPD` / `AMT_HBTD` in `swap.py`                              |
| Initial token supply | `INITIAL_SUPPLY` in `deploy.py`                                   |
| Gas tip / max fee    | the `fee_kwargs` dict in both scripts                             |
| Different datasets   | replace CSVs in `data/` + adjust `analytics.py` join logic        |
| Public testnet       | set `RPC_URL`, fund wallets with faucet ETH, run the same scripts |

---

## 🌐 Publishing / verifying the contract (optional)

If you deploy to a public testnet (e.g. Sepolia) you’ll probably want users to click an Etherscan link and read the verified Solidity:

1. After `deploy.py` finishes, copy the **HAPD** contract address from `deploy.json`.
2. Visit *sepolia.etherscan.io*, search the address, and hit **Verify & Publish**.
3. Paste the contents of `contracts/Token.sol`, choose "Solidity 0.8.20+commit" and the **MIT** license.
4. Repeat for **HBTD**.

Once verified, the ABI tab on Etherscan will let anyone call `symbol()`, `balanceOf()`, etc. directly in the browser.


---

## 📜 What this POC Demonstrate

This version   aimed to show how hospital datasets could be represented as blockchain assets using ERC‑20 tokens and traded securely via on-chain transactions.

### ✅ Demonstrated Features

| Capability | Description |
| ---------- | ----------- |
| **ERC‑20 token deployment** | Smart contracts for HAPD and HBTD tokens tied to hospital datasets |
| **Wallet usage**            | Hospital identities managed with Ethereum keypairs                 |
| **Token transfers**         | Hospitals exchanged tokens as a stand-in for data access rights    |
| **Gas simulation**          | Anvil enabled control over gas price and transaction cost          |
| **Simple analytics**        | Combined datasets (via `pandas`) for summary stats                 |

### ⚠️ Limitations

While technically valid and based on real blockchain components, this version has limitations that makes it less defensible as a true data tokenization use case:

- No connection between token ownership and actual data access
- Analytics used row-wise alignment (symmetric and permutation-invariant)
- No verifiable proof of which data was used to compute results

---

## 🔄 Comparison: Original vs new POC

| Aspect                  | Original POC                                      | Forked POC (Chunk-Based)                                        |
| ----------------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| **Data Representation** | Symbolic: tokens loosely represent dataset rights | Token = 1 verified data chunk                                   |
| **Analytics**           | Simple merge; results not tied to token use       | Uses only token-backed chunks; results depend on token holdings |
| **Token Utility**       | No enforcement; transfer = gesture                | Token governs actual data access                                |
| **Verifiability**       | Tx hashes only                                    | Tx hashes + SHA‑256 chunk proofs                                |
| **Complexity**          | Minimal setup                                     | Slightly more setup (chunks, hashes), still lightweight         |
| **Dependencies**        | Anvil, Web3                                       | Same                                                            |
| **Realism**             | Conceptual demonstration                          | Closer to practical data exchange logic                         |

## 🧪 New POC: Chunk-Based Data Tokenization with Verifiable Hashes

This enhanced of the original hospital data exchange POC replaces symbolic token trading with a lightweight, verifiable system for tokenized access to **chunked datasets**.

Still no Ocean Protocol, no IPFS, no real encryption — just real ERC‑20 tokens, chunked data files, SHA‑256 hashes for traceability, and analytics that prove value unlocked via token-based data acquisition.

---

## 🧱 Core Concepts

### 📦 Data Chunking

- Each hospital splits its dataset into multiple files: `chunk_0.csv`, `chunk_1.csv`, etc.
- Each chunk represents a portion of the hospital’s private dataset (e.g. 100 rows).
- A global `chunk_registry.json` maps each chunk to its SHA‑256 hash for verification.

### 🪙 Tokenization

- HAPD tokens → access to Hospital A’s data chunks
- HBTD tokens → access to Hospital B’s data chunks
- Token supply = number of available chunks (1 token = 1 chunk)

### 🔐 Access Enforcement

- After swap, `analytics.py` checks how many tokens the hospital owns
- It loads only the corresponding number of verified data chunks
- Computes insight (mean, median, std deviation) on enriched dataset

---

## 🔁 Demo Flow

1. **Chunk Preparation**

   - `prepare_chunks.py` splits raw datasets and generates `chunk_registry.json`

2. **Token Deployment**

   - `deploy.py` deploys HAPD/HBTD contracts with token supply = number of chunks

3. **Swap**

   - `swap.py` executes trade (e.g. A sends 5 HAPD ↔ B sends 7 HBTD)

4. **Analytics**

   - `analytics.py` loads your base data + as many purchased chunks as tokens received
   - Computes KPI (e.g. median, standard deviation)
   - Prints hash of each chunk used, proving which data powered the result

---

## 📊 Sample Suggested Output

```bash
Chunks used (5):
 - chunk_0.csv → SHA256: 6e8ab3…ff
 - chunk_1.csv → SHA256: 0d94c1…aa
...

Metric         Before    After     Token Cost
-------------- --------- --------- -----------
Median Age     58.3      61.4      5 HBTD
Std. Dev LOS   2.1       2.9       5 HBTD
Success Rate   87%       90%       5 HBTD
```

---

## 🔍 Verifiability

| What               | How to verify                              |
| ------------------ | ------------------------------------------ |
| Token balance      | `check_balances.py` or call `balanceOf()`  |
| Swap occurrence    | `deploy.json` → tx hash → `Transfer` log   |
| Chunks used in KPI | `analytics.py` prints chunk list + SHA‑256 |
| Chunk authenticity | Compare with `chunk_registry.json`         |

---

---

## 📚 Appendix: motivations for this new version

This new version  move beyond symbolic demos and demonstrate real technology patterns behind data tokenization.

### ✅ What shall be added—and why it matters

| Feature                           | Purpose                                                      |
| --------------------------------- | ------------------------------------------------------------ |
| **Chunked datasets**              | Allows token-to-data linkage (1 token ↔ 1 data chunk)        |
| **SHA-256 hash registry**         | Enables verification of which data chunks were used          |
| **Token-gated access simulation** | Mimics real access enforcement without external dependencies |
| **Analytics on combined data**    | Proves that tokens enable new statistical value              |
| **Token cost in output**          | Shows that insights were "purchased" with digital assets     |

### 🎯 Why this remains lightweight

- No IPFS, no Ocean Protocol, no real encryption required
- Anvil or Sepolia can be used — works fully locally
- Scripts are traceable, minimal, and easily auditable

### 🛡️ What makes it better

This POC ties real on-chain token transfers to measurable value (new data insights), with verifiability ensured by:

- Token balances and tx hashes on-chain
- Data chunk hashes off-chain
- Measurable changes in analytics

The result is a POC that demonstrates core principles behind data tokenization, access gating, and analytics — with no hand-waving, and no external systems required.

## 🔧 Future Works

- Optional: Add REST API to retrieve chunks or stats gated by token
- Optional: Encrypt chunks + use real access gateway
- Optional: Publish to Sepolia for public tx/contract verification

MIT License – fork, adapt, improve.




