from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import re
from utils.cfg import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        try:
            for script in checkout.extract():
                data = json.loads(script)
                if data.get('@type') == 'Product':
                    item['tmp'] = data
                    return False  # assume in stock
            return True
        except Exception:
            return True

    def _sku(self, res, item, **kwargs):
        # First try from the main JSON
        tmp = item.get('tmp', {})
        item['sku'] = tmp.get('sku', '')

        # Fallback: try to extract sku_number from page text
        if not item['sku'] or item['sku'] == 'UNKNOWN':
            import re
            text = ''.join(res.extract())
            match = re.search(r'"sku_number"\s*:\s*"(\d+)"', text)
            if match:
                item['sku'] = match.group(1)

        if not item['sku']:
            item['sku'] = 'UNKNOWN'

        item['name'] = tmp.get('name', '').upper()
        brand = tmp.get('brand', {})
        item['designer'] = brand.get('name', '').upper() if isinstance(brand, dict) else brand.upper()
        item['description'] = tmp.get('description', '')

    def _images(self, res, item, **kwargs):
        images = item['tmp'].get('image', [])
        if isinstance(images, str):
            images = [images]
        item['images'] = images
        item['cover'] = images[0] if images else ''

    def _prices(self, res, item, **kwargs):
        try:
            text = ''.join(res.extract())
            sale = re.search(r'"list_price"\s*:\s*"([\d\.]+)"', text)
            msrp = re.search(r'"msrp"\s*:\s*"([\d\.]+)"', text)
            if sale:
                item['saleprice'] = float(sale.group(1))
            if msrp:
                item['listprice'] = float(msrp.group(1))
            if not item.get('listprice'):
                item['listprice'] = item.get('saleprice')
        except:
            item['listprice'] = item.get('saleprice')

    def _sizes(self, res, item, **kwargs):
        raw = res.extract()
        sizes = [s.strip() for s in raw if s.strip()]
        item['sizes'] = sizes

    def _color(self, res, item, **kwargs):
        colors = res.extract()
        clean = [c.strip() for c in colors if c.strip()]
        item['color'] = ', '.join(clean)


_parser = Parser()


class Config(MerchantConfig):
    name = 'ruelala'
    merchant = 'RueLaLa'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('checkout', ('//script[@type="application/ld+json"]/text()', _parser._checkout)),
            ('sku', ('//html', _parser._sku)),
            ('images', ('//html', _parser._images)),
            ('prices', ('//html', _parser._prices)),
            ('sizes', ('//button[contains(@class,"sku-size")]/text()', _parser._sizes)),
            ('color', ('//input[contains(@class,"sku-color")]/@data-display_value', _parser._color)),
        ])
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )
