from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import re
from utils.cfg import *

class Parser(MerchantParser):
    def _tmp(self, res, item, **kwargs):
        item['tmp'] = {}
        try:
            scripts = res.xpath('//script[@type="application/ld+json"]/text()').getall()
            for script in scripts:
                try:
                    data = json.loads(script.strip())
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        item['tmp'] = data
                        return
                except Exception:
                    continue
        except Exception:
            item['tmp'] = {}

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp'].get('name', '').strip()

    def _designer(self, res, item, **kwargs):
        brand = item['tmp'].get('brand', {})
        item['designer'] = brand.get('name', '') if isinstance(brand, dict) else brand if isinstance(brand, str) else ''

    def _description(self, res, item, **kwargs):
        desc = item['tmp'].get('description', '')
        if isinstance(desc, str):
            parts = desc.split('. ')
            seen = set()
            dedup_parts = []
            for part in parts:
                if part not in seen:
                    seen.add(part)
                    dedup_parts.append(part)
            item['description'] = '. '.join(dedup_parts).strip()
        else:
            item['description'] = ''

    def _images(self, res, item, **kwargs):
        imgs = item['tmp'].get('image') or []
        if isinstance(imgs, str):
            imgs = [imgs]
        elif isinstance(imgs, dict) and 'url' in imgs:
            imgs = [imgs['url']]
        elif isinstance(imgs, dict):
            imgs = [imgs.get('image')] if 'image' in imgs else []
        item['images'] = [img['url'] if isinstance(img, dict) and 'url' in img else img for img in imgs if isinstance(img, (str, dict))]
        item['images'] = list(OrderedDict.fromkeys(item['images']))
        item['cover'] = item['images'][0] if item['images'] else ''

    def _variants(self, res, item, **kwargs):
        
        script = res.xpath('//script[contains(text(),"ShopifyAnalytics") or contains(text(),"productVariants")]/text()').get()
        sizes, color_set, sku_set, variants_data = [], set(), set(), []
        if script:
            try:
                json_match = re.search(r'productVariants":(\[.*?\])', script, re.S)
                if json_match:
                    raw = json_match.group(1)
                    raw = raw.replace('\n', '').replace('\t', '').replace('"', '"')
                    variants = json.loads(raw)
                    for v in variants:
                        title = v.get("title", "")
                        sku = v.get("sku", "")
                        price = v.get("price", {}).get("amount")
                        available = v.get("available", True)
                        size = ""
                        color = ""
                        # print(sku)
                        sku_set.add(sku)
                        if "/" in title:
                            size, color = [x.strip() for x in title.split('/', 1)]
                            sizes.append(size)
                            color_set.add(color)
                        # Always append, even if no '/' in title
                        variants_data.append({
                            "size": size,
                            "color": color,
                            "sku": sku,
                            "price": float(price) if price else 0.0,
                            "in_stock": available
                        })
                    # print("ASASASSASA")
                    # print(variants_data)
                    # print("")
                    
                    item["sizes"] = [v["size"]     for v in variants_data]
                    item["prices"]= [v["price"]    for v in variants_data]
                    item["sku"] = [v["sku"]     for v in variants_data]
                    # item["in_stock_list"] = [v["in_stock"] for v in variants_data]
                    item["variants_data"] = variants_data
            except Exception:
                pass

        try:
            analytics_script = res.xpath('//script[@id="web-pixels-manager-setup"]/text()').get()
            if analytics_script:
                json_match = re.search(r'productVariants":\s*(\[.*?\])', analytics_script, re.S)
                if json_match:
                    variants = json.loads(json_match.group(1))
                    for v in variants:
                        title = v.get("title", "")
                        sku = v.get("sku", "")
                        price = v.get("price", {}).get("amount")
                        available = v.get("available", True)
                        size = ""
                        color = ""
                        # print (sku)
                        if "/" in title:
                            size, color = [x.strip() for x in title.split('/', 1)]
                            sizes.append(size)
                            color_set.add(color)
                            
                        variants_data.append({
                            "size": size,
                            "color": color,
                            "sku": sku,
                            "price": float(price) if price else 0.0,
                            "in_stock": available
                        })
                    # print(variants_data)

                    item["variants_data"] = variants_data

                    
                    
                product_match = re.search(r'var meta\s*=\s*({.*?});', analytics_script, re.S)
                if product_match:
                    meta_json = json.loads(product_match.group(1))
                    product_info = meta_json.get('product', {})
                    item.setdefault('product_id', product_info.get('id', ''))
                    item.setdefault('vendor', product_info.get('vendor', ''))
                    item.setdefault('product_type', product_info.get('type', ''))
        except Exception:
            pass

        item["sizes"] = list(OrderedDict.fromkeys(sizes))
        item["color"] = ', '.join(sorted(color_set))
        item["sku"] = ', '.join(sorted(sku_set))

        return 
    
    

    # def _sku(self, res, item, **kwargs):
    #     # 直接 print 验证
    #     print("DEBUG: _sku sees variants_data =", item.get("variants_data"))
    #     if 'variants_data' in item and item['variants_data']:
    #         skus = [v.get('sku') for v in item['variants_data'] if v.get('sku')]
    #         if skus:
    #             item['sku'] = ','.join(skus)
    #             return
    #     item['sku'] = item.get('product_id', '') or item['tmp'].get('sku', '') or 'UNKNOWN'

    def _prices(self, res, item, **kwargs):
        if 'variants_data' in item and item['variants_data']:
            prices = [v['price'] for v in item['variants_data'] if v.get('price')]
            if prices:
                item['saleprice'] = item['listprice'] = float(max(prices))
                return

        price = res.xpath('//span[contains(@class, "product__price--sale") or contains(@class, "product__price")]/text()').re_first(r'\$([\d\.]+)')
        if not price:
            script = res.xpath('//script[contains(text(), "variants")]/text()').get()
            if script:
                match = re.search(r'"price"\s*:\s*"(\d+\.\d{2})"', script)
                if match:
                    price = match.group(1)
        item['saleprice'] = item['listprice'] = float(price) if price else 0.0

    def _related_products(self, res, item, **kwargs):
        return

_parser = Parser()

class Config(MerchantConfig):
    name = 'shopsimon'
    merchant = 'ShopSimon'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('tmp', ('//html', _parser._tmp)),
            ('variants', ('//html', _parser._variants)),
            ('sku', ('//html', _parser._sku)),
            # ('sku', ('//html', _parser._variants)),
            ('name', ('//html', _parser._name)),
            ('designer', ('//html', _parser._designer)),
            ('description', ('//html', _parser._description)),
            ('images', ('//html', _parser._images)),
            ('color', ('//html', _parser._color)),
            ('sizes', ('//html', _parser._sizes)),
            ('prices', ('//html', _parser._prices)),

            
        ])
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )
