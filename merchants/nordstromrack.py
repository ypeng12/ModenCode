from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from utils.cfg import *
import re

def extract_selected_sku(html):
    m = re.search(r'"selectedSku"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1)
    return 'UNKNOWN'

def extract_colors_from_html(html):
    colors = set()
    # 只匹配 color 字段块
    color_blocks = re.findall(r'"color"\s*:\s*({.*?})\s*,\s*"', html, re.S)
    for block in color_blocks:
        try:
            if not block.strip().endswith('}'):
                block += '}'
            color_json = json.loads(block)
            for k, v in color_json.items():
                if k.startswith('anchor') and k.endswith('TextArea') and v:
                    colors.add(v)
        except Exception as e:
            anchor_matches = re.findall(r'"anchor\w+TextArea"\s*:\s*"([^"]+)"', block)
            for val in anchor_matches:
                if val:
                    colors.add(val)
    return sorted(colors)

def extract_sizes_from_html(html):
    sizes = set()
    # 1. 只匹配 size 字段
    size_blocks = re.findall(r'"size"\s*:\s*({.*?})\s*,\s*"', html, re.S)
    for block in size_blocks:
        try:
            # 尝试 JSON 解析（防止截断，加 }）
            if not block.strip().endswith('}'):
                block += '}'
            size_json = json.loads(block)
            for k, v in size_json.items():
                if k.startswith('anchor') and k.endswith('TextArea') and v:
                    sizes.add(v)
        except Exception as e:
            # fallback: 直接在这块用正则
            anchor_matches = re.findall(r'"anchor\w+TextArea"\s*:\s*"([^"]+)"', block)
            for val in anchor_matches:
                if val:
                    sizes.add(val)
    return sorted(sizes)


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
        item['designer'] = brand.get('name', '') if isinstance(brand, dict) else (brand if isinstance(brand, str) else '')

    def _description(self, res, item, **kwargs):
        desc = item['tmp'].get('description', '')
        # Remove HTML tags if any
        item['description'] = re.sub('<[^<]+?>', '', desc).strip() if desc else ''


    def _sku(self, res, item, **kwargs):
        html = res.get() if hasattr(res, 'get') else ''
        item['sku'] = extract_selected_sku(html)



    def _images(self, res, item, **kwargs):
        imgs = item['tmp'].get('image', [])
        if isinstance(imgs, str): imgs = [imgs]
        item['images'] = imgs
        item['cover'] = imgs[0] if imgs else ''


    def _color(self, res, item, **kwargs):
        html = res.get() if hasattr(res, 'get') else ''
        colors = extract_colors_from_html(html)
        item['color'] = ', '.join(colors)

    
    def _sizes(self, res, item, **kwargs):
    # 只要解析 anchorXXXTextArea，不要其他字段
        html = res.get() if hasattr(res, 'get') else ''
        item['sizes'] = extract_sizes_from_html(html)


    def _prices(self, res, item, **kwargs):
        offer = item['tmp'].get('offers', {})
        if isinstance(offer, dict):
            price = offer.get('price')
            if isinstance(price, str) and '-' in price:
                low, high = price.split('-')
                item['saleprice'] = float(low)
                item['listprice'] = float(high)
            else:
                item['saleprice'] = float(offer.get('lowPrice', 0.0))
                item['listprice'] = float(offer.get('highPrice', offer.get('lowPrice', 0.0)))
        else:
            item['saleprice'] = 0.0
            item['listprice'] = 0.0

    def _variants(self, res, item, **kwargs):
        # Parse window.__PRELOADED_STATE__ for all skus/sizes/colors
        script = None
        try:
            # Try all scripts, find the one with __PRELOADED_STATE__
            scripts = res.xpath('//script[contains(text(), "__PRELOADED_STATE__")]/text()').getall()
            for s in scripts:
                if 'window.__PRELOADED_STATE__' in s:
                    script = s
                    break
            if not script:
                return
            # 修正这里，不要带 </script>
            m = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?});', script, re.S)
            if not m:
                return
            state = json.loads(m.group(1))
            byid = state.get('skus', {}).get('byId', {})
            skus = []
            sizes_set = set()
            color_set = set()
            for sku_id, skuinfo in byid.items():
                skus.append(sku_id)
                size = skuinfo.get('sizeDisplayValue')
                color = skuinfo.get('colorDisplayValue')
                if size: sizes_set.add(size)
                if color: color_set.add(color)
            item['skus_list'] = skus
            item['sizes_set'] = sizes_set
            item['color_set'] = color_set
        except Exception as e:
            print('variants parse error:', e)
            
    def _related_products(self, res, item, **kwargs):
        return

_parser = Parser()

class Config(MerchantConfig):
    name = 'nordstromrack'
    merchant = 'Nordstrom Rack'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('tmp', ('//html', _parser._tmp)),
            ('variants', ('//html', _parser._variants)),
            ('sku', ('//html', _parser._sku)),
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
