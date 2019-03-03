import asyncio
from nonocaptcha.solver import Solver

pageurl = "https://www.google.com/recaptcha/api2/demo"
sitekey = "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"

options = {
    "ignoreHTTPSErrors": True,
    "args": ["--timeout 5", "--no-sandbox"],
    "executablePath":"/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"}
client = Solver(pageurl, sitekey, options=options)

solution = asyncio.get_event_loop().run_until_complete(client.start())
if solution:
    print(solution)
