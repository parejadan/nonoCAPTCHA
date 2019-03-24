#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Base module. """

import asyncio
import logging
import os
import random

from nonocaptcha.utils.js import JS_LIBS
from nonocaptcha.utils.iomanage import create_path
from nonocaptcha import package_dir
from nonocaptcha.exceptions import SafePassage, TryAgain

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)

try:
    import yaml
    with open('nonocaptcha.yaml') as f:
        settings = yaml.load(f)
except FileNotFoundError:
    print(
        'Solver can\'t run without a configuration file!\n'
        'An example (nonocaptcha.example.yaml) has been copied to your folder.'
    )

    import sys
    from shutil import copyfile

    copyfile(
        f'{package_dir}/nonocaptcha.example.yaml', 'nonocaptcha.example.yaml')
    sys.exit(0)


class Clicker:
    @staticmethod
    async def click_button(button):
        click_delay = random.uniform(30, 170)
        await button.click(delay=click_delay)


class Base(Clicker):
    proc_id = 0
    headless = settings['headless']
    should_block_images = settings['block_images']
    page_load_timeout = settings['timeout']['page_load'] * 1000
    iframe_timeout = settings['timeout']['iframe'] * 1000
    animation_timeout = settings['timeout']['animation'] * 1000
    deface_data = os.path.join(package_dir, 'data', 'deface.html')
    jquery_data = os.path.join(package_dir, 'data', 'jquery.js')
    override_data = os.path.join(package_dir, 'data', 'override.js')
    js_libs = {}
    executable_path = settings.get('paths', {}).get('executable', None)
    outpath = os.path.join(os.getcwd(), 'data')
    browser_data = os.path.join(outpath, 'browserData')
    slow_down = settings.get('slow_down', None)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if settings['debug']:
            self.logger.setLevel('DEBUG')

        self.create_working_folders()

    def create_working_folders(self):
        configured = settings.get('paths')
        if configured:
            self.browser_data = configured.get('browser_profile', self.browser_data)
            self.outpath = configured.get('cache', self.outpath)

        create_path(self.outpath)
        create_path(self.browser_data)

    async def get_frames(self):
        self.checkbox_frame = next(
            frame for frame in self.page.frames if 'api2/anchor' in frame.url
        )
        self.image_frame = next(
            frame for frame in self.page.frames if 'api2/bframe' in frame.url
        )

    async def click_reload_button(self):
        reload_button = await self.image_frame.J('#recaptcha-reload-button')
        await self.click_button(reload_button)

    async def check_detection(self, timeout):
        """Checks if "Try again later", "please solve more" modal appears
        or success"""

        try:
            await self.page.waitForFunction(JS_LIBS.check_detection, timeout=timeout)
        except asyncio.TimeoutError:
            raise SafePassage()
        else:
            if await self.page.evaluate('parent.window.wasdetected === true;'):
                status = 'detected'
            elif await self.page.evaluate('parent.window.success === true'):
                status = 'success'
            elif await self.page.evaluate('parent.window.tryagain === true'):
                await self.page.evaluate('parent.window.tryagain = false;')
                raise TryAgain()

            return {'status': status}

    def log(self, message):
        self.logger.debug(f"{self.proc_id} {message}")
