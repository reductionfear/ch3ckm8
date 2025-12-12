# CHECKMATE v0.2

A powerful multi-gateway card checker with built-in sites and custom site support.

```
░▄▀▀░█▄█▒██▀░▄▀▀░█▄▀░█▄▒▄█▒▄▀▄░▀█▀▒██▀
░▀▄▄▒█▒█░█▄▄░▀▄▄░█▒█░█▒▀▒█░█▀█░▒█▒░█▄▄
         @isnotsin
```

---

## FEATURES

### Multi-Gateway Support
- **Stripe Auth** - Card authorization without charge
- **Stripe Charge** - Full checkout flow with actual charge
- **PPCP** - PayPal Commerce Platform integration
- **B3 Auth** - Braintree card authorization
- **B3 Charge** - Braintree full checkout with charge

### Dual Site Mode
- **Built-in Sites** - Use `SIN-STRIPE`, `SIN-PPCP`, `SIN-B3` for automatic server-side rotation
- **Custom Sites** - Manage your own site lists with independent files per gateway

### Performance
- Multi-threaded checking (5 threads default)
- Real-time progress tracking
- Live statistics display: S (Success) | L (Live) | D (Dead) | I (Invalid)
- Automatic card extraction from any format

### Privacy & Security
- Site URLs hidden in logs (displays as SITE 1, SITE 2, etc.)
- Secure API key management with expiry validation
- Full proxy support for anonymity
- Telegram forwarder for instant notifications

### Smart Results
- Color-coded terminal output
- Auto-save results by category (approved/charged/live/ccn)
- Detailed summary statistics
- Timestamped result files

### Easy Configuration
- Simple menu-driven interface
- API key validation and expiry checking
- Custom server support
- Per-gateway site management
- Proxy enable/disable toggle

---

## PRICING

### API Key Plans

| Plan | Duration | Price |
|------|----------|-------|
| Standard Key | 7 days | $10 |
| Private API | 30 days | $15 |

### Standard Key (7 days - $10)
- Full access to all 5 gateways
- Stripe Auth & Charge
- PPCP (PayPal Commerce Platform)
- Braintree Auth & Charge
- BIN checker included
- Proxy parameter support
- Built-in site rotation
- 100 requests per minute

### Private API (30 days - $15)
- Dedicated API instance
- All standard features included
- Higher rate limits (200 requests/minute)
- Priority support
- Not listed on public status page
- Custom integrations available
- Perfect for building your own tools

---

## AVAILABLE GATEWAYS

### Stripe
- `/stripe` - Card authorization (no charge)
- `/stripe_charge` - Full checkout with charge attempt

### PayPal Commerce Platform
- `/ppcp` - PPCP card payment processing

### Braintree
- `/b3` - Card authorization (no charge)
- `/b3charge` - Full checkout with charge attempt

### Additional Tools
- `/bin` - BIN information lookup (no authentication required)

---

## INSTALLATION

```bash
git clone https://github.com/isnotsin/checkmate.git
cd checkmate
python3 checker.py
```

The script will automatically install required dependencies (requests).

No manual pip install needed - dependencies are handled on first run.

---

## QUICK START

### 1. Configure API Key
```
Main Menu > [2] CONFIGURE API KEY
Enter your API key when prompted
```

The tool will validate your key and show expiry information.

### 2. Add Custom Sites (Optional)
```
Main Menu > [4] CONFIGURE SITES
Select gateway (Stripe Auth/Charge, PPCP, B3 Auth/Charge)
Choose: Add manually or import from TXT file
```

Each gateway has its own independent site list:
- `sites/stripe.txt` - For Stripe Auth
- `sites/stripe_charge.txt` - For Stripe Charge
- `sites/ppcp.txt` - For PPCP
- `sites/b3.txt` - For B3 Auth
- `sites/b3charge.txt` - For B3 Charge

### 3. Configure Proxy (Optional)
```
Main Menu > [5] CONFIGURE PROXY
Set proxy URL: http://user:pass@host:port
Enable/disable as needed
```

### 4. Configure Telegram Forwarder (Optional)
```
Main Menu > [6] CONFIGURE FORWARDER
Set bot token and chat ID
Receive instant notifications for successful checks
```

### 5. Start Checking
```
Main Menu > [1] START CHECKER
Choose gateway (1-5)
Select site mode (Built-in or Custom)
Enter card file paths (comma separated)
```

---

## FILE STRUCTURE

```
checkmate/
├── checker.py              # Main script
├── checker_config.json     # Auto-generated configuration
├── sites/                  # Custom site lists (auto-created)
│   ├── stripe.txt
│   ├── stripe_charge.txt
│   ├── ppcp.txt
│   ├── b3.txt
│   └── b3charge.txt
└── results/                # Auto-saved results (auto-created)
    ├── approved_YYYYMMDD_HHMMSS.txt
    ├── charged_YYYYMMDD_HHMMSS.txt
    ├── live_YYYYMMDD_HHMMSS.txt
    └── ccn_YYYYMMDD_HHMMSS.txt
```

---

## CARD FILE FORMAT

The tool automatically extracts cards from various formats:

```
4532015112830366|12|2025|123
4532015112830366 12 2025 123
4532015112830366/12/2025/123
4532015112830366 12/25 123
Card: 4532015112830366, Exp: 12/2025, CVV: 123
```

Any format works - the tool intelligently parses card data.

---

## OUTPUT EXAMPLE

```
09:12:22 : [S] 4602xxxxxxxx1681|04|30|458 | CHARGED - PAYMENT SUCCESS | 203.0.113.45 | STRIPE_CHARGE | SIN-STRIPE
09:12:23 : [L] 5234xxxxxxxx9012|12|28|123 | INSUFFICIENT_FUNDS - INSUFFICIENT FUNDS | 203.0.113.46 | PPCP | SITE 1
09:12:24 : [L] 4111xxxxxxxx1111|01|25|999 | INCORRECT_CVC - SECURITY CODE INVALID | 203.0.113.47 | B3CHARGE | SITE 2
09:12:25 : [D] 4000xxxxxxxx0002|06|26|456 | DECLINED - CARD DECLINED | 203.0.113.48 | B3 | SIN-B3

PROGRESS: 226/226 | S: 18 | L: 47 | D: 157 | I: 4

==================================================
CHECK SUMMARY
==================================================
TOTAL CHECKED: 226
APPROVED: 12
CHARGED: 6
CCN MATCHED: 28
LIVE: 19
DEAD: 157
INVALID/ERROR: 4
==================================================

[+] SAVED TO results/approved_20250115_091225.txt
[+] SAVED TO results/charged_20250115_091225.txt
[+] SAVED TO results/ccn_20250115_091225.txt
[+] SAVED TO results/live_20250115_091225.txt
```

---

## STATUS CODES

### Card Status
| Status | Symbol | Description |
|--------|--------|-------------|
| APPROVED | S | Card authorized successfully (auth gateways) |
| CHARGED | S | Payment completed (charge gateways) |
| CCN MATCHED | L | Card valid but declined (CVV error, insufficient funds) |
| LIVE | L | Card active but declined by processor |
| DEAD | D | Card declined or invalid |
| ERROR | I | Technical error or invalid format |

### Common Response Codes
- `charged` - Payment successful
- `succeeded` - Authorization successful
- `insufficient_funds` - Card has no funds
- `incorrect_cvc` - Wrong CVV code
- `card_declined` - Generic decline
- `expired_card` - Card expired
- `invalid_number` - Invalid card number

---

## CONFIGURATION

### API Key Setup
```json
{
  "api_key": "ABC123",
  "api_base": "https://api.isnotsin.com",
  "bot_token": "",
  "chat_id": "",
  "proxy": "",
  "proxy_enabled": false
}
```

Configuration is stored in `checker_config.json` and persists between sessions.

### Custom Server
If you have a private API instance:
```
Main Menu > [3] CONFIGURE SERVER
Enter your custom API base URL
Example: https://your-private-api.com
```

---

## PROXY CONFIGURATION

### Supported Formats
```
http://host:port
http://user:pass@host:port
https://host:port
https://user:pass@host:port
```

### Usage
1. Configure proxy via menu option [5]
2. Enable/disable without removing proxy URL
3. Proxy IP will be shown in check results
4. Used for all gateway requests

---

## TELEGRAM FORWARDER

### Setup
1. Create a Telegram bot via @BotFather
2. Get your bot token
3. Get your chat ID (use @userinfobot)
4. Configure in menu option [6]

### Features
- Instant notifications for successful checks
- Shows card details, status, and message
- Only sends for: APPROVED, CHARGED, CCN MATCHED, LIVE
- Does not spam for dead cards or errors

---

## SITE MANAGEMENT

### Built-in Sites
Use the following codes for automatic server-side rotation:
- `SIN-STRIPE` - Stripe gateways
- `SIN-PPCP` - PPCP gateway
- `SIN-B3` - Braintree gateways

Built-in sites are maintained server-side and regularly updated.

### Custom Sites
Each gateway maintains its own independent site list:

**Adding Sites Manually:**
```
Main Menu > [4] CONFIGURE SITES
Select gateway
Choose [1] ADD SITE MANUALLY
Enter domain: shop.example.com
```

**Importing from File:**
```
Main Menu > [4] CONFIGURE SITES
Select gateway
Choose [2] ADD SITES FROM TXT FILE
Enter file path: /path/to/sites.txt
```

**Site Format:**
```
shop.example.com
store.website.com
https://another-shop.com
www.example-store.net
```

URLs are automatically cleaned (http/https and www removed).

---

## BEST PRACTICES

### For Best Results
1. Use proxies to avoid IP blocks
2. Keep thread count at 5 (default) for stability
3. Use built-in sites for convenience
4. Add custom sites for specific targets
5. Enable Telegram forwarder for real-time monitoring

### Site Management Tips
- Test sites before adding to your list
- Remove dead/offline sites regularly
- Use different sites for different gateways
- Built-in sites are pre-tested and working

### Card File Tips
- One card per line
- Any format is accepted (tool auto-extracts)
- Remove duplicates before checking
- Use comma-separated files for bulk checking

---

## TROUBLESHOOTING

### API Key Issues
```
[!] API KEY EXPIRED OR INVALID
```
**Solution:** Configure new API key via menu option [2]

### No Cards Loaded
```
[-] NO CARDS LOADED
```
**Solution:** Check file path and format. Ensure cards are in format: CC|MM|YY|CVV

### Connection Errors
```
ERROR - CONNECTION ERROR
```
**Solution:** Check internet connection, try with proxy, or use different site

### Site Unreachable
```
ERROR - SITE_UNREACHABLE
```
**Solution:** Site may be down. Use built-in sites or try different custom site

### Timeout Errors
```
ERROR - TIMEOUT
```
**Solution:** Site is slow or overloaded. Enable proxy or use different site

---

## CONTACT & SUPPORT

**Developer:** @isnotsin

**Telegram:** [@isnotsin](https://t.me/isnotsin)

**Website:** https://isnotsin.com

**API Status:** https://status.isnotsin.com

**API Docs:** https://api.isnotsin.com

### Purchase API Keys
Contact via Telegram for:
- Standard Keys (7 days - $10)
- Private API (30 days - $15)

### Payment Methods
- Cryptocurrency (USDT, BTC, ETH)
- PayPal
- Other methods available on request

### Support Response Time
- API key purchases: Within 24 hours
- Technical support: Within 48 hours
- General inquiries: Within 72 hours

---

## FREQUENTLY ASKED QUESTIONS

**Q: What's the difference between AUTH and CHARGE gateways?**

A: AUTH gateways only authorize cards without charging. CHARGE gateways attempt actual payment transactions.

**Q: Can I use multiple proxies?**

A: Currently one proxy at a time. You can change it anytime via the configuration menu.

**Q: How accurate are the results?**

A: Results depend on site quality and card validity. Built-in sites are tested regularly for accuracy.

**Q: What does CCN MATCHED mean?**

A: Card is valid and active, but declined for other reasons (wrong CVV, insufficient funds, etc.)

**Q: Can I check multiple card files at once?**

A: Yes, enter file paths separated by commas: `cards1.txt, cards2.txt, cards3.txt`

**Q: Are my checked cards logged?**

A: No. Cards are only saved locally in your results folder. Nothing is sent to our servers except API requests.

**Q: Can I get a refund?**

A: No refunds for API keys. Test with built-in sites before purchasing.

**Q: How do I add more threads?**

A: Currently fixed at 5 threads for stability. Higher thread counts may be added in future versions.

---

## CHANGELOG

### Version 0.2 (Current)
- Added Stripe Charge gateway
- Added B3 Charge gateway
- Separated site files per gateway (5 independent lists)
- Improved gateway selection menu
- Updated pricing information
- Enhanced site management
- Better error handling
- Updated documentation

### Version 0.1
- Initial release
- 3 gateways (Stripe, PPCP, B3)
- Built-in site support
- Custom site management
- Multi-threading
- Telegram forwarder
- Proxy support

---

## LEGAL DISCLAIMER

This tool is provided for educational and testing purposes only. Users are responsible for:

1. Obtaining proper authorization before testing any cards
2. Compliance with all applicable laws and regulations
3. Ensuring legitimate use of the software
4. Understanding that unauthorized card testing is illegal

The developer is not responsible for any misuse of this software. Use at your own risk.

By using this tool, you agree to:
- Use it only for legitimate testing purposes
- Comply with all local and international laws
- Accept full responsibility for your actions
- Not hold the developer liable for any consequences

---

## LICENSE

Copyright 2025 @isnotsin - All Rights Reserved

This software is proprietary. Unauthorized copying, modification, distribution, or use of this software is strictly prohibited without explicit written permission from the developer.

---

**Made by sinno$ | @isnotsin**

**For professional card testing and gateway integration**
