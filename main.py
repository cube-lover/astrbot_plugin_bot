from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import urllib.parse

@register(
    "astrbot_plugin_gemini",
    "cube",
    "通过 MissQiu Gemini API 图生图生成手办化图片",
    "1.3.0",
    "https://github.com/yourrepo/astrbot_plugin_gemini"
)
class GeminiPlugin(Star):
    """Gemini 手办化插件"""

    def __init__(self, context: Context):
        # 不再访问 context.config
        self.context = context

        # ---------------------- 从面板配置读取 ----------------------
        # context.get("配置项", 默认值)
        self.apikey = context.get("apikey", "")
        self.width = context.get("width", "1024")
        self.height = context.get("height", "1024")

        # 固定 text 提示词
        self.text = (
            "Please accurately transform the main subject in this photo into a realistic, masterpiece-like 1/7 scale PVC statue. "
            "...(省略，和之前一样)..."
        )

        # 初始化 aiohttp 会话
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10))

    async def terminate(self):
        try:
            await self.session.close()
        except Exception as e:
            logger.exception("关闭 aiohttp 会话时出错: %s", e)

    # 使用 regex 代替 keyword，兼容新版 API
    @filter.regex(r"手办化")
    async def gen_image_by_keyword(self, event: AstrMessageEvent):
        await self._generate_image(event)

    async def _generate_image(self, event: AstrMessageEvent):
        try:
            img_list = event.get_images()
            if not img_list:
                yield event.plain_result("请发送一张图片，并在文字里加上 '手办化'")
                return

            img_url = img_list[0]

            params = {
                "text": self.text,
                "width": self.width,
                "height": self.height,
                "type": "tu",
                "url": img_url,
                "tc": "no",
                "enhance": "false",
                "apikey": self.apikey
            }
            url = "https://missqiu.icu/API/Gemini.php?" + urllib.parse.urlencode(params)

            async with self.session.get(url) as resp:
                if resp.status != 200:
                    logger.warning("Gemini API 返回非 200 响应: %s", resp.status)
                    yield event.plain_result(f"手办化失败，状态码: {resp.status}")
                    return
                img_bytes = await resp.read()

            yield event.image_result(img_bytes)

        except Exception:
            logger.exception("处理手办化图生图时发生异常")
            yield event.plain_result("手办化失败，请稍后重试。")



