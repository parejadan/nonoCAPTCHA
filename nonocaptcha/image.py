#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" ***IN TESTING*** """

import os
import shutil
import asyncio
from PIL import Image

from nonocaptcha.utils.iomanage import create_path, clean_path, save_file
from nonocaptcha.utils.imgparse import split_image
from nonocaptcha.utils.navigate import get_page
from nonocaptcha.utils.server import get_file_server
from nonocaptcha.base import Base, settings
from nonocaptcha import package_dir


class SolveImage(Base):
    search_url = 'https://www.google.com/searchbyimage?site=search&sa=X&image_url='

    def __init__(self, browser, image_frame, proxy, proxy_auth, proc_id, cleanup=True):
        self.browser = browser
        self.image_frame = image_frame
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.proc_id = proc_id
        self.cur_image_path = None
        self.title = None
        self.pieces = None
        self.cleanup = cleanup
        self.image_save_path = os.path.join(self.outpath, 'pictures')
        self.file_server = get_file_server(settings['image']['host'])
        self.create_root_if_needed()
        self.create_cache()

    async def get_images(self):
        table = await self.image_frame.querySelector('table')
        rows = await table.querySelectorAll('tr')
        for row in rows:
            cells = await row.querySelectorAll('td')
            for cell in cells:
                yield cell

    async def is_solvable(self):
        el = await self.get_description_element()
        desc = await self.image_frame.evaluate('el => el.innerText', el)
        return 'images' in desc

    async def pictures_of(self):
        el = await self.get_description_element()
        of = await self.image_frame.evaluate(
            'el => el.firstElementChild.innerText', el
        )
        return of.lstrip('a ')

    async def get_description_element(self):
        name1 = await self.image_frame.querySelector('.rc-imageselect-desc')
        name2 = await self.image_frame.querySelector(
            '.rc-imageselect-desc-no-canonical'
        )
        return name1 if name1 else name2

    async def cycle_to_solvable(self):
        while not await self.is_solvable() or await self.image_no() != 9:
            await self.click_reload_button()

    async def solve_by_image(self):
        # cycle through the captcha options until we find something solvable
        await self.cycle_to_solvable()
        title = await self.pictures_of()
        pieces = 9  # TODO: crop other sizes
        # we've found something to work with, now download and split the image
        image = await self.download_image()
        self.title = title
        print(f'Image of {title}')
        self.pieces = pieces
        self.cur_image_path = os.path.join(self.image_save_path, f'{hash(image)}')
        create_path(self.cur_image_path)
        file_path = os.path.join(self.cur_image_path, f'{title}.jpg')
        await save_file(file_path, image, binary=True)
        image_obj = Image.open(file_path)
        split_image(image_obj, pieces, self.cur_image_path)
        # identify each prominant object in split segments
        self.file_server.start(self.cur_image_path)
        queries = [self.reverse_image_search(i) for i in range(pieces)]
        results = await asyncio.gather(*queries, return_exceptions=True)
        for r in results:
            if isinstance(r, tuple) and r[1] is True:
                pass
                # TODO: return a list of numbers corresponding to image index

        return {'status': '?'}

    async def get_image_url(self):
        image_url = (
            'document.getElementsByClassName("rc-image-tile-wrapper")[0].'
            'getElementsByTagName("img")[0].src'
        )
        return await self.image_frame.evaluate(image_url)

    async def image_no(self):
        return len([i async for i in self.get_images()])

    async def download_image(self):
        image_url = await self.get_image_url()
        return await get_page(
            image_url, self.proxy, self.proxy_auth, binary=True
        )

    def create_cache(self):
        if self.cleanup:
            clean_path(self.image_save_path)
        create_path(self.image_save_path)

    async def reverse_image_search(self, image_no):
        image_path = self.file_server.get_url(f'{image_no}.jpg')
        page = await self.browser.newPage()
        await page.goto(self.search_url + image_path)
        card = await page.querySelector('div.card-section')
        if card:
            best_guess = await page.evaluate('el => el.children[1].innerText',
                                             card)
            print(image_no, best_guess)
        else:
            best_guess = ''
        await asyncio.sleep(100)
        await page.close()
        return self.title in best_guess
