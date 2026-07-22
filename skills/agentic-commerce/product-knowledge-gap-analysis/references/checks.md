# Product knowledge check commands

Replace `$PDP` with a representative product page URL. Repeat for each important product type and variant family.

## Raw product-page evidence

```bash
curl -sS -L --max-time 20 "$PDP" | grep -oE '<h1[^>]*>[^<]+|[[:alnum:]][^<]{0,80}(SKU|GTIN|size|ingredient|material|compatib|allergen|warranty)[^<]{0,120}' | head -80
curl -sS -L --max-time 20 "$PDP" | grep -oiE '(add to cart|out of stock|in stock|sold out|select (a )?(size|color|variant))' | sort -u
```

Record attributes visible in raw HTML. If core facts appear only after client-side interaction, mark them unavailable to basic crawlers.

## Rendered product evidence

Use a browser or operator-provided rendered capture when the page exposes product facts only after JavaScript or variant selection. Record the selected product and variant identifiers, displayed price and currency, availability, sale timing, fulfillment-relevant state, visible update markers, capture timestamp, and the interactions used. Keep this evidence labeled `public`.

## Structured product fields and variants

```bash
curl -sS -L --max-time 20 "$PDP" | grep -oE '<script type="application/ld\+json">[^<]*' | sed 's/^<script[^>]*>//' | python3 -m json.tool
curl -sS -L --max-time 20 "$PDP" | grep -oiE 'hasVariant|offers|priceCurrency|availability|sku|gtin' | sort -u
```

Check Product markup for stable identifiers and variant relationships. [SRC-SCHEMA-PRODUCT] Check Offer markup for price, currency, availability, price validity, and shipping or fulfillment details. [SRC-SCHEMA-OFFER] Treat fields not supported by visible evidence as unknown; never infer ingredients, compatibility, or safety claims.

## Catalog-feed comparison when supplied

```bash
curl -sS -L --max-time 20 -o /dev/null -w '%{http_code} %{content_type}\n' "$FEED_URL"
curl -sS -L --max-time 20 "$FEED_URL" | head -c 1000
```

Set `$FEED_URL` only to a public operator-supplied feed. Compare its identifiers and attributes with the product page; mismatches are source-of-truth gaps.

Record a feed retrieval timestamp and any observable generation time, version, ETag, or last-modified indicator. Compare the representative facts from the feed with raw HTML, rendered content, and JSON-LD. Do not treat the feed as checkout evidence.

## Optional checkout comparison

Use checkout evidence only when an operator supplies verified evidence or supervises a check that cannot purchase, authorize payment, submit checkout, or reserve inventory. Record the evidence method and timestamp. If adding an item can reserve stock or create operational state, do not perform the check.

Keep checkout observations separate from public observations. Report checkout consistency as verified only when the checkout evidence meets the requirement above; otherwise report it as `not verified`.

## Mismatch record

For each differing fact, record every surface and observed value, the evidence timestamp, the buyer or agent failure mode, the proposed source of truth, the remediation owner, and whether the mismatch blocks reliable recommendation or action. Variant, price, currency, availability, sale-timing, or fulfillment mismatches that can change the selected item, amount, purchasability, or delivery promise are blocking.
