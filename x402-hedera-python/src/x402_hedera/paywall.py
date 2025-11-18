"""
Paywall utilities for x402 Hedera payments.
"""

import json
from typing import Dict, Any, List, Optional

from x402_hedera.types import PaymentRequirements
from x402_hedera.common import x402_VERSION

# Simple paywall HTML template
PAYWALL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Required</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 500px;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 1rem;
        }
        p {
            color: #666;
            margin-bottom: 2rem;
        }
        .error {
            color: #e74c3c;
            background: #fee;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
        }
        .amount {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Payment Required</h1>
        <p>This resource requires payment to access.</p>
        <div id="error-container"></div>
        <div id="amount-container"></div>
        <p>Please use a compatible wallet to complete the payment.</p>
    </div>
    <script>
        // Payment configuration will be injected here
        if (window.x402) {
            const config = window.x402;
            const errorContainer = document.getElementById('error-container');
            const amountContainer = document.getElementById('amount-container');
            
            if (config.error) {
                errorContainer.innerHTML = '<div class="error">' + config.error + '</div>';
            }
            
            if (config.amount) {
                amountContainer.innerHTML = '<div class="amount">$' + config.amount.toFixed(6) + '</div>';
            }
        }
    </script>
</body>
</html>"""


def is_browser_request(headers: Dict[str, Any]) -> bool:
    """
    Determine if request is from a browser vs API client.

    Args:
        headers: Dictionary of request headers (case-insensitive keys)

    Returns:
        True if request appears to be from a browser, False otherwise
    """
    headers_lower = {k.lower(): v for k, v in headers.items()}
    accept_header = headers_lower.get("accept", "")
    user_agent = headers_lower.get("user-agent", "")

    if "text/html" in accept_header and "Mozilla" in user_agent:
        return True

    return False


def create_x402_config(
    error: str,
    payment_requirements: List[PaymentRequirements],
) -> Dict[str, Any]:
    """Create x402 configuration object from payment requirements."""

    requirements = payment_requirements[0] if payment_requirements else None
    display_amount = 0
    current_url = ""
    testnet = True

    if requirements:
        # Convert atomic amount back to display amount
        try:
            amount = int(requirements.max_amount_required)
            # Determine decimals based on asset
            if requirements.asset == "0.0.0" or (requirements.asset and requirements.asset.lower() == "hbar"):
                decimals = 8  # HBAR decimals
            else:
                decimals = 6  # USDC decimals (default for tokens)
            display_amount = float(amount) / (10**decimals)
        except (ValueError, TypeError):
            display_amount = 0

        current_url = requirements.resource or ""
        testnet = requirements.network == "hedera-testnet"

    # Create the window.x402 configuration object
    return {
        "amount": display_amount,
        "paymentRequirements": [
            req.model_dump(by_alias=True) for req in payment_requirements
        ],
        "testnet": testnet,
        "currentUrl": current_url,
        "error": error,
        "x402_version": x402_VERSION,
    }


def inject_payment_data(
    html_content: str,
    error: str,
    payment_requirements: List[PaymentRequirements],
) -> str:
    """Inject payment requirements into HTML as JavaScript variables."""

    # Create x402 configuration object
    x402_config = create_x402_config(error, payment_requirements)

    # Create the configuration script
    log_on_testnet = (
        "console.log('Payment requirements initialized:', window.x402);"
        if x402_config["testnet"]
        else ""
    )

    config_script = f"""
  <script>
    window.x402 = {json.dumps(x402_config)};
    {log_on_testnet}
  </script>"""

    # Inject the configuration script into the head
    return html_content.replace("</head>", f"{config_script}\n</head>")


def get_paywall_html(
    error: str,
    payment_requirements: List[PaymentRequirements],
) -> str:
    """
    Load paywall HTML and inject payment data.

    Args:
        error: Error message to display
        payment_requirements: List of payment requirements

    Returns:
        Complete HTML with injected payment data
    """
    return inject_payment_data(PAYWALL_TEMPLATE, error, payment_requirements)

