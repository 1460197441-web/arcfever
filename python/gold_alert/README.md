# Gold Price Alert

This is a standalone Python tool that:

- polls a gold price API
- evaluates one or more alert strategies
- sends email notifications through SMTP

## Files

- `monitor.py`: main program
- `config.example.json`: example configuration
- `requirements.txt`: Python dependency list
- `state.json`: created automatically after the first run

## Supported data providers

The current example is configured to scrape a webpage directly, without any API key.

### 1. `html_regex`

Use this when the website HTML contains a stable price string you can match with a regular expression.

- `url`
- `price_regex`
- `headers` (optional)
- `params` (optional)
- `user_agent` (optional)
- `symbol`
- `currency`
- `source_name` (optional)
- `value_multiplier` (optional)

Example:

```json
{
  "provider": "html_regex",
  "url": "https://www.investing.com/currencies/xau-usd-converter",
  "price_regex": "1\\s*XAU\\s*=\\s*([0-9,.]+)\\s*USD",
  "source_name": "Investing.com XAU/USD converter",
  "symbol": "XAU",
  "currency": "USD",
  "timeout_seconds": 10
}
```

### 2. `generic_json`

Use this if you later switch to a JSON endpoint:

- `url`
- `headers` (optional)
- `params` (optional)
- `json_path` such as `data.price`
- `symbol`
- `currency`
- `source_name` (optional)
- `value_multiplier` (optional)

### 3. `goldapi`

This is still supported if you later want a paid/official API:

- `base_url`
- `api_key`
- `symbol`
- `currency`
- `timeout_seconds`

## Install

Make sure Python 3.10+ is installed, then run:

```bash
pip install -r requirements.txt
```

## Configure

1. Create your local config:

```bash
copy config.example.json config.json
```

2. Update `config.json` with your real values:

- `market_data.url`
- `market_data.price_regex`
- `strategies`
- `email.smtp_host`
- `email.smtp_port`
- `email.username`
- `email.password`
- `email.to`

## Strategy types

### Price above threshold

```json
{
  "name": "Above 2400 USD",
  "type": "price_above",
  "threshold": 2400
}
```

### Price below threshold

```json
{
  "name": "Below 2300 USD",
  "type": "price_below",
  "threshold": 2300
}
```

### Percent change from previous poll

```json
{
  "name": "Up more than 1%",
  "type": "change_percent",
  "direction": "up",
  "threshold": 1.0
}
```

Available `direction` values:

- `up`
- `down`
- `either`

## Run

Run one cycle:

```bash
python monitor.py --config config.json --once
```

Send a test email:

```bash
python monitor.py --config config.json --test-email
```

Run continuously:

```bash
python monitor.py --config config.json
```

## Cooldown

The tool writes `state.json` and uses `alert.cooldown_minutes` to avoid sending the same alert too often.

## Notes on website scraping

Website scraping is convenient, but it is less stable than using an API.

- the page structure can change without notice
- some sites may block bots or rate-limit requests
- you may need to update `price_regex` if the page content changes

For the default example, the target webpage is [Investing.com XAU/USD converter](https://www.investing.com/currencies/xau-usd-converter).

## Windows scheduling

For better stability on Windows, use Task Scheduler to run this command every minute:

```bash
python monitor.py --config C:\path\to\config.json --once
```
