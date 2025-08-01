# 🕷️ ModeSens Merchant Crawler

This project implements a modular, scalable crawler framework for extracting and normalizing e-commerce product data from various merchant websites. It is designed to support ModeSens' backend data pipeline and is compatible with both live data ingestion and local parser testing.

## 🔍 Overview

Modern e-commerce platforms aggregate products from multiple retailers, each with unique page structures, product formats, and variant logic. This crawler system addresses those challenges with:

- Merchant-specific parsers using a shared inheritance-based architecture
- Hybrid parsing using both JSON-LD and XPath
- Variant normalization (e.g., size, color, availability)
- Dynamic image and SKU resolution
- Integration-ready output

## 🧠 Features

- ✅ Extracts structured data: name, brand, SKU, price, color, sizes, images
- ✅ Handles multi-variant products and color-specific SKUs
- ✅ Captcha-aware scraping logic for robust operation
- ✅ Easily extendable by adding new merchant parser modules
- ✅ Testing support using local HTML snapshots

## 🛍 Supported Merchants (Sample)

- Macy’s
- Goop
- KicksCrew
- (More can be added under `merchants/`)

## 🧱 Tech Stack

- Python 3.x
- `lxml`, `json`, `requests`, `OrderedDict`
- Custom merchant parser framework
- Deepcopy logic for variant expansion

## 📁 Project Structure

crawl_product/
├── merchants/ # Merchant-specific parser modules (e.g., goop.py)
├── tests/ # Test HTML files and main entry for validation
├── utils/ # Shared utilities and config
├── lambdas/ # AWS Lambda-compatible modules (if used)
├── requirements.txt # Python dependencies
├── pyproject.toml # Build configuration
├── template.yaml # AWS SAM template
└── README.md

pgsql
复制
编辑

## 📦 Sample Output (JSON)

```json
{
  "sku": "FV5029-100",
  "name": "AIR JORDAN 4 RETRO 'WHITE CEMENT'",
  "designer": "AIR JORDAN",
  "color": "SUMMIT WHITE/FIRE RED/TECH GREY/BLACK",
  "originlistprice": 210.00,
  "originsaleprice": 210.00,
  "images": ["https://.../img1.jpg"],
  "cover": "https://.../img1.jpg",
  "sizes": ["7", "8", "9.5"]
}
