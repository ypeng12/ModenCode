from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from utils.cfg import *


class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        try:
            raw = checkout.extract_first()
            data = json.loads(raw)
            item['tmp'] = data

            offers = data.get('offers', [])
            if isinstance(offers, list) and offers:
                availability = offers[0].get('availability', '').lower()
            else:
                availability = offers.get('availability', '').lower() if isinstance(offers, dict) else ''

            return 'instock' not in availability
        except Exception:
            return True  # assume OOS if parsing fails

    def _sku(self, res, item, **kwargs):
        try:
            offers = item['tmp'].get('offers', [])
            if isinstance(offers, list) and offers:
                item['sku'] = offers[0].get('SKU', 'UNKNOWN')
            else:
                item['sku'] = 'UNKNOWN'

            item['name'] = item['tmp'].get('name', '').upper()
            brand = item['tmp'].get('brand', {})
            item['designer'] = brand.get('name', '').upper() if isinstance(brand, dict) else ''
            item['description'] = item['tmp'].get('description', '')
        except Exception:
            item['sku'] = 'UNKNOWN'

    def _images(self, res, item, **kwargs):
        images = item['tmp'].get('image', [])
        if isinstance(images, str):
            images = [images]
        item['images'] = images
        item['cover'] = images[0] if images else ''

    def _prices(self, res, item, **kwargs):
        offers = item['tmp'].get('offers', [])
        price = None
        if isinstance(offers, list) and offers:
            price = offers[0].get('price')
        elif isinstance(offers, dict):
            price = offers.get('price')

        item['originlistprice'] = price
        item['originsaleprice'] = price

    def _sizes(self, res, item, **kwargs):
        sizes = res.extract()
        clean = [s.strip() for s in sizes if s.strip() and 'size' not in s.lower()]
        item['originsizes'] = list(set(clean)) if clean else ['IT']

    def _parse_images(self, response, **kwargs):
        try:
            data = json.loads(response.xpath('//script[@type="application/ld+json" and contains(text(), "Product")]/text()').extract_first())
            imgs = data.get('image', [])
            return [imgs] if isinstance(imgs, str) else imgs
        except:
            return []

    def _parse_checknum(self, response, **kwargs):
        try:
            obj = json.loads(response.body)
            return obj.get('meta', {}).get('totalCount', 0)
        except:
            return 0

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            txt = info.strip()
            if any(k in txt.lower() for k in ['cm', 'heel', 'length', 'diameter', 'height', 'weight']):
                fits.append(txt)
        return '\n'.join(fits)


_parser = Parser()


class Config(MerchantConfig):
    name = 'macys'
    merchant = 'Macys'

    path = dict(
        plist=dict(),
        product=OrderedDict([
            ('checkout', ('//script[@type="application/ld+json" and contains(text(), "Product")]/text()', _parser._checkout)),
            ('sku', ('//html', _parser._sku)),
            ('images', ('//html', _parser._images)),
            ('prices', ('//html', _parser._prices)),
            ('sizes', ('//div[contains(@class,"size")]//text()', _parser._sizes)),
        ]),
        image=dict(
            method=_parser._parse_images,
        ),
        size_info=dict(
            method=_parser._parse_size_info,
            size_info_path='//div[contains(@class,"productDetails")]//text()',
        ),
        checknum=dict(
            method=_parser._parse_checknum,
        ),
    )

    list_urls = dict(
        f=dict(
            a=["https://www.macys.com/shop/womens-clothing?id=118"],
            b=["https://www.macys.com/shop/handbags-accessories?id=26846"],
            c=["https://www.macys.com/shop/clothing?id=1"],
            s=["https://www.macys.com/shop/shoes?id=13247"],
            e=["https://www.macys.com/shop/beauty?id=30077"],
        ),
        m=dict(
            e=["https://www.macys.com/shop/mens-grooming?id=1"],
            c=["https://www.macys.com/shop/mens-clothing?id=1"],
        ),
        params=dict(page=1),
    )

    countries = dict(
        US=dict(language='EN', currency='USD')
    )
