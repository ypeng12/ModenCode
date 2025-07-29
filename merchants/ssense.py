from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import re
from parsel import Selector  

class Parser(MerchantParser):
    def _tmp(self, res, item, **kwargs):
        # 只做数据中转，不做最终输出
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

    def _sku(self, res, item, **kwargs):
        item['sku'] = item['tmp'].get('sku', 'UNKNOWN')

    def _name(self, res, item, **kwargs):
        item['name'] = item['tmp'].get('name', '').upper()

    def _designer(self, res, item, **kwargs):
        brand = item['tmp'].get('brand', {})
        item['designer'] = brand.get('name', '').upper() if isinstance(brand, dict) else (brand.upper() if brand else '')

    def _description(self, res, item, **kwargs):
        desc = item['tmp'].get('description', '')
        # Normalize whitespace and remove line breaks
        desc = desc.replace('\r', ' ').replace('\n', ' ').replace('\xa0', ' ')
        desc = re.sub(r'\s+', ' ', desc).strip()
        item['description'] = desc

    def _images(self, res, item, **kwargs):
        img = item['tmp'].get('image')
        # 支持 str 或 list
        images = [img] if isinstance(img, str) else (img if isinstance(img, list) else [])
        images = list(OrderedDict.fromkeys(images))
        # item['images'] = images
        # item['cover'] = images[0] if images else ''

    def _color(self, res, item, **kwargs):
        # 从 description 提取 Supplier color，或留空
        desc = item['tmp'].get('description', '')
        color = ''
        m = re.search(r'Supplier color:\s*([^\n]+)', desc)
        if m:
            color = m.group(1).strip()
        item['color'] = color
    def _sizes(self, res, item, **kwargs):
        html = res.get()
        sel = Selector(text=html)
        seen = set()
        sizes = []
        options = sel.xpath('//select[@id="pdpSizeDropdown"]/option[not(@disabled)]/text()').getall()
        for opt in options:
            opt = opt.strip()
            if '-' in opt:
                size = opt.split('-')[0].strip()
                if size not in seen:
                    sizes.append(size)
                    seen.add(size)
        item['sizes'] = sizes

    def _prices(self, res, item, **kwargs):
        offer = item['tmp'].get('offers', {})
        try:
            price = offer.get('price', 0.0)
            item['saleprice'] = float(price)
            item['listprice'] = float(price)
        except Exception:
            item['saleprice'] = 0.0
            item['listprice'] = 0.0

    def _related_products(self, res, item, **kwargs):
        return

_parser = Parser()

class Config(MerchantConfig):
    name = 'ssense'
    merchant = 'SSENSE'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('tmp', ('//html', _parser._tmp)),
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

def clean_output(item):
    # 只保留你要的主字段，不包括 images、cover、tmp
    main_keys = [
        'gender', 'merchant', 'crawler_name', 'category', 'country', 'area', 'language', 'currency', 'opflag',
        'sku', 'name', 'designer', 'color', 'description', 'sizes', 'saleprice', 'listprice'
    ]
    return {k: v for k, v in item.items() if k in main_keys}

