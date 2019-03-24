import asyncio
import json

from pyppeteer.util import merge_dict
from user_agent import generate_navigator_js


from nonocaptcha.utils.iomanage import load_file
from nonocaptcha.browsers.launcher import Launcher
from nonocaptcha.base import Base
from nonocaptcha.exceptions import PageError


class RawDriver(Base):
    launcher = None
    browser = None

    def __init__(self, options, proxy=None, proxy_auth=None, loop=None, **kwargs):
        super().__init__()
        self.options = merge_dict(options, kwargs)
        self.proxy = f'http://{proxy}' if proxy else proxy
        self.proxy_auth = proxy_auth
        self.page = None
        self.loop = loop or asyncio.get_event_loop()

    async def get_new_browser(self):
        """
        Get a new browser, set proxy and arguments
        """
        args = [
            '--cryptauth-http-host ""',
            '--disable-accelerated-2d-canvas',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-browser-side-navigation',
            '--disable-client-side-phishing-detection',
            '--disable-default-apps',
            '--disable-dev-shm-usage',
            '--disable-device-discovery-notifications',
            '--disable-extensions',
            '--disable-features=site-per-process',
            '--disable-hang-monitor',
            '--disable-java',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-setuid-sandbox',
            '--disable-sync',
            '--disable-translate',
            '--disable-web-security',
            '--disable-webgl',
            '--metrics-recording-only',
            '--no-first-run',
            '--safebrowsing-disable-auto-update',
            '--no-sandbox',
            # Automation arguments
            '--enable-automation',
            '--password-store=basic',
            '--use-mock-keychain']
        if self.proxy:
            args.append(f'--proxy-server={self.proxy}')
        if 'args1' in self.options:
            args.extend(self.options.pop('args'))
        if 'headless' in self.options:
            self.headless = self.options['headless']
        if 'executablePath' not in self.options:
            self.options['executablePath'] = self.executable_path
        if self.slow_down:
            self.options['slowMo'] = self.slow_down
        if self.window:
            args.append(
                f'--window-size={self.window["width"]},{self.window["height"]}')
        self.options.update({
            'userDataDir': self.browser_data,
            'headless': self.headless,
            'args': args,
            #  Silence Pyppeteer logs
            'logLevel': 'CRITICAL'})
        self.launcher = Launcher(self.options)
        self.browser = await self.launcher.launch()
        self.page = await self.browser.newPage()
        if self.window:
            await self.page.setViewport(self.window)

        return self.browser

    async def cloak_navigator(self):
        """
        Emulate another browser's navigator properties
        and set webdriver false, inject jQuery.
        """
        jquery_js = await load_file(self.jquery_data)
        override_js = await load_file(self.override_data)
        navigator_config = generate_navigator_js(
            os=('linux', 'mac', 'win'), navigator=('chrome'))
        navigator_config['mediaDevices'] = False
        navigator_config['webkitGetUserMedia'] = False
        navigator_config['mozGetUserMedia'] = False
        navigator_config['getUserMedia'] = False
        navigator_config['webkitRTCPeerConnection'] = False
        navigator_config['webdriver'] = False
        dump = json.dumps(navigator_config)
        _navigator = f'const _navigator = {dump};'
        await self.page.evaluateOnNewDocument(
            '() => {\n%s\n%s\n%s}' % (_navigator, jquery_js, override_js))
        return navigator_config['userAgent']

    async def cleanup(self):
        if self.launcher:
            await self.launcher.killChrome()
            self.log('Browser closed')

    async def goto(self, url):
        """
        Navigate to address
        """
        user_agent = await self.cloak_navigator()
        await self.page.setUserAgent(user_agent)
        try:
            await self.loop.create_task(
                self.page.goto(
                    url,
                    timeout=self.page_load_timeout,
                    waitUntil='domcontentloaded',))
        except asyncio.TimeoutError:
            raise PageError('Page loading timed-out')
        except Exception as exc:
            raise PageError(f'Page raised an error: `{exc}`')