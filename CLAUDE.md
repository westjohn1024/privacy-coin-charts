# privacy-coin-charts

Collects price and market data for privacy coins (currently Monero, Zcash, Dash, Minotari)
from the CoinMarketCap API four times a day and appends it to a CSV in S3.
Everything runs on AWS and is defined with AWS CDK (Python).

## Layout
- `lambda_function.py` - the Lambda that runs in AWS: calls CoinMarketCap, appends rows to the CSV in S3.
- `fetch.py` - local-only script that does the same fetch and writes a local CSV. Not deployed.
- `requirements.txt` - packages for `fetch.py` only.
- `infra/` - the CDK app. `infra/infra/infra_stack.py` defines the bucket, Lambda,
  EventBridge schedule, CloudWatch alarm and SNS alerts. `infra/tests/` holds the pytest tests.
- `.github/workflows/checks.yml` - runs ruff and pytest on every pull request.
- `.github/workflows/deploy.yml` - runs `cdk deploy` when changes to the Lambda, `infra/` or itself merge to main.

## Commands
- Lint (from the repo root): `ruff check` (pinned to ruff 0.17.4 in CI)
- Test (from `infra/`): `pip install -r requirements.txt -r requirements-dev.txt`, then `python -m pytest`
- Preview infrastructure changes (from `infra/`): `cdk synth -c alert_email=test@example.com`

## Rules
- Never commit secrets: no API keys, `.env` files, email addresses or CSV data.
- The CoinMarketCap API key lives in AWS Parameter Store at `/privacy-coins/cmc-api-key`.
  The alert email comes from the `ALERT_EMAIL` GitHub secret. Don't hard-code either.
- AWS region is us-east-2. Don't add resources in any other region.
- AWS is currently set up with the free tier, try to avoid building anything that will increase costs.  If costs must increase, get approval first.
- Every change goes through a pull request; ruff and pytest must pass. Never push to main.
- Never run `cdk deploy` yourself. Deploys happen only from GitHub Actions after a human merges.
- Keep `lambda_function.py` dependency-free (standard library plus boto3, which Lambda provides).
- Coins are chosen by CoinMarketCap slug (the `SLUGS` env var / default in `lambda_function.py`).
  Minotari's slug is `tari`.
- Keep changes small and focused on the request; explain anything you weren't sure about in the PR description.
