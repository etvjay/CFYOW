# Bradbury CI Wallet

CFYOW EXP-003 requires an appeal-capable GenLayer network. Studionet does not configure the appeal contracts, so EXP-003 runs on `testnet_bradbury`.

## Security model

Use a dedicated Bradbury-only burner wallet.

- Do not use a mainnet wallet.
- Do not reuse a wallet that holds valuable assets.
- Never commit the private key.
- Store the private key only as the GitHub Actions repository secret `BRADBURY_PRIVATE_KEY`.
- The public address may be shown in Actions logs so it can be funded and audited.

## GitHub configuration

In the `etvjay/CFYOW` repository:

1. Open **Settings**.
2. Open **Secrets and variables** → **Actions**.
3. Under **Repository secrets**, choose **New repository secret**.
4. Name it exactly `BRADBURY_PRIVATE_KEY`.
5. Paste the dedicated Bradbury wallet private key and save it.

The workflow injects this secret into the job as `BRADBURY_PRIVATE_KEY`. `gltest.config.yaml` references it as `${BRADBURY_PRIVATE_KEY}` for `testnet_bradbury`.

## Funding

Fund only the public address using the official GenLayer testnet faucet:

https://testnet-faucet.genlayer.foundation

Bradbury uses:

- GenLayer RPC: `https://rpc-bradbury.genlayer.com`
- Chain ID: `4221`
- Native currency: `GEN`

The EXP-003 workflow performs a preflight before testing. It derives and prints only the public address, checks the GEN balance, and exits before any experiment if the signer is missing or unfunded.

## Running EXP-003

Open **Actions** → **EXP-003 Bradbury Evidence** → **Run workflow**.

Use branch `research/experiment-ledger-v1`, keep `require_appeal` as `1`, and leave `appeal_value` blank so the test resolves the network minimum appeal bond automatically.

Do not enter the private key into workflow inputs, issues, commits, PR comments, or chat.
