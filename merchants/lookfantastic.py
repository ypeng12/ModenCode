from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
from copy import deepcopy
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "add to cart" in checkout.extract_first().strip().lower():
            return False
        else:
            return True

    def _parse_multi_items(self, response, item, **kwargs):
        jsonText = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        if json:
            obj = json.loads(jsonText)
            if len(obj["offers"]) == 1:
                yield item
                return
            for color in obj["offers"]:
                if "out" in color["availability"].lower():
                    continue

                item_color = deepcopy(item)
                url = color["url"].split("?")[0]+"?shippingcountry="+item["country"]+"&switchcurrency="+item["currency"]+"&variation="+color["url"].split("&variation=")[-1]
                result = getwebcontent(url)
                html = etree.HTML(result)
                item_color["sku"] = color["sku"]
                imgs = html.xpath('//div[@class="productImageCarousel_imageWrapper"]/span[@data-size="600"]/@data-path')
                images = []
                for img in imgs:
                    img = "http:"+img

                    if img not in images:
                        images.append(img)
                item_color["images"] = images
                item_color['cover'] = item_color['images'][0]

                self.prices(html, item_color, **kwargs)
                item_color["url"] = url
                yield item_color

        else:
            yield item

    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = sku_data.extract_first().strip()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            if img not in images:
                images.append(img)
            if not cover and "_main" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc or desc in desc_li:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes1, item, **kwargs):
        sizes = ""
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        if item["designer"] == "":
            script = sizes1.xpath(".//script/text()").extract_first()
            for s in script:
                if "productbrand:" in s:
                    item["designer"] = s.split("productbrand:")[-1].split(",")[0].replace('"','').strip()
        item["designer"] = item["designer"].upper()

    def _prices(self, res, item, **kwargs):
        # print(prices.xpath('.//p[@class="productPrice_price"]/text()').extract()[0].strip())
        try:
            item['originlistprice'] = res.xpath('.//span[@class="productPrice_rrpPriceInfo"]/p/text()').extract_first().strip().split(':')[1]
            item['originsaleprice'] = res.xpath('.//p[@class="productPrice_price "]/text()').extract_first().strip()
        except:
            try:
                item['originlistprice'] = prices.xpath('.//p[@class="productPrice_price"]/text()').extract()[0].strip()
                item['originsaleprice'] = prices.xpath('.//p[@class="productPrice_price"]/text()').extract()[0].strip()
            except:
                try:
                    item['originlistprice'] = prices.xpath('.//p[@class="productPrice_rrp"]/text()')[0].strip().split(":")[-1]
                    item['originsaleprice'] = prices.xpath('.//p[@class="productPrice_price"]/text()')[0].strip().replace('\u20bd',"")
                except:
                    item['originlistprice'] = ""
                    item['originsaleprice'] = ""

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="athenaProductImageCarousel_imageWrapper"]/span[@data-size="600"]/@data-path').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images
        
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="responsiveProductListHeader_resultsCount"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number




_parser = Parser()



class Config(MerchantConfig):
    name = 'lookfantastic'
    merchant = 'Lookfantastic'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a[contains(@class,"responsivePaginationButton--last")]/text()',
            items = '//div[@data-component="productBlock"]',
            designer = './div/span/@data-product-brand',
            link = './div/a[@class="productBlock_link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="athenaProductPage_actions"]/div/span/span/button/text()', _parser.checkout)),
            ('images',('//div[@class="athenaProductImageCarousel_imageWrapper"]/span[@data-size="600"]/@data-path',_parser.images)), 
            ('sku',('//div/@data-master-id',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//h1[@class="productName_title"]/text()'),
            ('designer','//div[@data-information-component="brand"]/div/text()'),
            ('description', ('//div[@class="productDescription_synopsisContent"]/div/p//text()',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
            ('prices', ('//span[@class="productPrice_priceInfo"]', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(


            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
         
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            e = [
                "https://www.lookfantastic.com/health-beauty/men/view-all-men-s.list?pageNumber="
            ]

        ),
        f = dict(

            e = [
                "https://www.lookfantastic.com/health-beauty/body/supplements.list?pageNumber=",
                "https://www.lookfantastic.com/health-beauty/body/hand-gel.list?pageNumber=",
                "https://www.lookfantastic.com/health-beauty/body/self-tanning.list?pageNumber=",
                "https://www.lookfantastic.com/health-beauty/face/view-all-skincare.list?pageNumber=",
                "https://www.lookfantastic.com/health-beauty/make-up/view-all-make-up.list?pageNumber=",
                "https://www.lookfantastic.com/health-beauty/hair/view-all-haircare.list?pageNumber=",
                "https://www.lookfantastic.com/brands/mac/view-all.list?pageNumber="
                "https://www.lookfantastic.com/health-beauty/body/moisturisers/lotions.list?pageNumber=",
                "https://www.lookfantastic.com/brands/beauty-works/view-all.list?pageNumber=",
                "https://www.lookfantastic.com/brands/herbivore/tools.list?pageNumber=",
                "https://www.lookfantastic.com/brands/hollywood-browzer/view-all.list?pageNumber=",
                "https://www.lookfantastic.com/brands/nuface/view-all.list?pageNumber=",
                "https://www.lookfantastic.com/brands/iluminage/all.list?pageNumber=",
                "https://www.lookfantastic.com/brands/tripollar/tripollar-view-all.list?pageNumber=",
                "https://www.lookfantastic.com/health-beauty/fragrance/view-all-fragrance.list?pageNumber=",

            ],




        params = dict(
            # TODO:

            ),
        ),

        # country_url_base = '/en-us/',
    )

    parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {
                'en_shippingCountry_V6':'US',
                'en_currency_V6':'USD',
            },
        ),
        CN = dict(
            currency_sign = '\xa5',
            currency = 'CNY',
            cookies = {
                'en_shippingCountry_V6':'CN',
                'en_currency_V6':'CNY',
            },
        ),
        JP = dict(
            currency_sign = '\xa3',
            currency = 'JPY',
            discurrency = "GBP",
            cookies = {
                'en_shippingCountry_V6':'JP',
                'en_currency_V6':'GBP',
            },
        ),
        KR = dict(
            currency_sign = "\u20A9",
            currency = 'KRW',
            # currency = "GBP",
            cookies = {
                'en_shippingCountry_V6':'KR',
                'en_currency_V6':'KRW',
            },
        ),
        HK = dict(
            currency_sign = 'HK$',
            currency = 'HKD',
            cookies = {
                'en_shippingCountry_V6':'HK',
                'en_currency_V6':'HKD',
            },
        ),
        SG = dict(
            currency_sign = 'S$',
            currency = 'SGD',
            cookies = {
                'en_shippingCountry_V6':'SG',
                'en_currency_V6':'SGD',
            },
        ),
        AU = dict(
            
            currency = 'AUD',
            currency_sign = 'A$',
            cookies = {
                'en_shippingCountry_V6':'AU',
                'en_currency_V6':'AUD',
            },
        ),
        GB = dict(
            
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = {
                'en_shippingCountry_V6':'GB',
                'en_currency_V6':'GBP',
            },
        ),
        DE = dict(
            currency_sign = '\u20ac',
            currency = 'EUR',
            cookies = {
                'en_shippingCountry_V6':'DE',
                'en_currency_V6':'EUR',
            },
        ),
        CA = dict(
            currency_sign = 'CA$',
            currency = 'CAD',
            cookies = {
                'en_shippingCountry_V6':'CA',
                'en_currency_V6':'CAD',
            },
        ),
        NO = dict(
            area = 'AP',
            currency_sign = 'kr',
            currency = 'NOK',
            cookies = {
                'en_shippingCountry_V6':'NO',
                'en_currency_V6':'NOK',
            },
        ),
        # Currency Sign Issue
        # RU = dict(
        #     currency_sign = u'\xd1',
        #     currency = 'RUB',
        #     discurrency = "GBP",
        #     thousand_sign = u'\xa0',
        #     cookies = {
        #         'en_shippingCountry_V6':'RU',
        #         'en_currency_V6':'RUB',
        #     },
        # )
        )

        


