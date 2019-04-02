import asyncio
import json

from pyppeteer.util import merge_dict
from user_agent import generate_navigator_js


from nonocaptcha.utils.iomanage import load_file
from nonocaptcha.utils.js import JS_LIBS
from nonocaptcha.browsers.launcher import Launcher
from nonocaptcha.base import Base
from nonocaptcha.exceptions import PageError


class RawDriver(Base):
    launcher = None
    browser = None
    page_manager = None

    def __init__(self, options, proxy=None, proxy_auth=None, loop=None, **kwargs):
        super().__init__()
        self.options = merge_dict(options, kwargs)
        self.proxy = f'http://{proxy}' if proxy else proxy
        self.proxy_auth = proxy_auth
        self.loop = loop or asyncio.get_event_loop()

    @property
    def page(self):
        return self.page_manager.page

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
            '--use-mock-keychain',
            # allow user agent override
            '--enable-features=NetworkService']
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
        self.page_manager = PageManager(
            loop=self.loop,
            browser=self.browser,
            viewport=self.window,
            navigator_defaults=self.navigator,
            timeout=self.page_load_timeout)
        await self.set_newpage()

        return self.browser

    async def set_newpage(self):
        await self.page_manager.set_newpage()

    async def cleanup(self):
        if self.launcher:
            await self.launcher.killChrome()
            self.log('Browser closed')

    async def goto(self, url):
        """
        Navigate to address
        """
        await self.page_manager.goto(url)


class PageManager:
    def __init__(self, loop, browser, viewport, navigator_defaults, timeout):
        self.loop = loop
        self.browser = browser
        self.queue = []
        self.page = None
        self.viewport = viewport
        self.navigator_defaults = {
            'mediaDevices': False,
            'webkitGetUserMedia': False,
            'mozGetUserMedia': False,
            'getUserMedia': False,
            'webkitRTCPeerConnection': False,
            'webdriver': False}
        self.navigator_defaults.update(navigator_defaults)
        self.navigator_config = {}
        self.timeout = timeout
        self.os=navigator_defaults.pop('os', ('win', 'mac', 'linux'))

    @property
    def user_agent(self):
        return self.navigator_config.get(
            'userAgent',
            self.navigator_defaults.get('userAgent'))

    async def goto(self, url, regenerate_navigator=False):
        if not self.navigator_config or regenerate_navigator:
            await self.cloak_navigator()
        await self.page.setUserAgent(self.user_agent)
        try:
            await self.loop.create_task(
                self.page.goto(
                    url,
                    timeout=self.timeout,
                    waitUntil='domcontentloaded',))
        except asyncio.TimeoutError:
            raise PageError(f'Timeout loading {url}')
        except Exception as ex:
            raise PageError(f'While loading [{url}] encountered error{ex}')

    async def cloak_navigator(self):
        """
        Emulate another browser's navigator properties
        and set webdriver false, inject jQuery.
        """
        self.navigator_config = generate_navigator_js(
            os=self.os,
            navigator=('chrome'))
        self.navigator_config.update(self.navigator_defaults)
        await self.resync_navigator()

    async def resync_navigator(self, hard=False):
        dump = json.dumps(self.navigator_config)
        _ = f'const _navigator = {dump};'
        await self.page.evaluateOnNewDocument(
            '() => {\n%s\n%s\n%s}' % (_, JS_LIBS.jquery, JS_LIBS.override))

        if hard:
            await self.page.setUserAgent(self.user_agent)
            await self.sync_request_agent()

    async def sync_request_agent(self):
        user_agent = self.user_agent
        if user_agent:
            await self.page.setExtraHTTPHeaders(
                headers={'User-Agent': user_agent})

    async def evaluate_user_agent(self):
        running_agent = await self.page.evaluate('navigator.userAgent')
        return running_agent

    def workon_tab_number(self, num):
        self.page = self.page_queue[num]

    def workon_first(self):
        self.workon_tab_number(0)

    async def set_newpage(self):
        """
        Creates a new tab and sets it as the "context" page (self.page)
        """
        self.page = await self.browser.newPage()
        if self.viewport:
            await self.page.setViewport(self.viewport)
        await self.sync_request_agent()
