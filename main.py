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
    """Gemini 手办化插件

    触发方式：
    发送一张图片并附带关键词 "手办化"
    """

    # ---------------------- 修正 __init__ 接收 config ----------------------
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}

        # ---------------------- 从配置读取 ----------------------
        self.apikey = self.config.get("apikey", "")
        self.width = self.config.get("width", "1024")
        self.height = self.config.get("height", "1024")

        # 固定 text 提示词
        self.text = (
            "Please accurately transform the main subject in this photo into a realistic, masterpiece-like 1/7 scale PVC statue. "
            "A box should be placed behind the side of the statue: the front of the box has a large, clear transparent front window printed with the main artwork, product name, brand logo, barcode, and a small specification or authenticity verification panel. "
            "A small price tag sticker must also be attached to the corner of the box. "
            "Meanwhile, a computer monitor is placed at the back, and the monitor screen needs to display the ZBrush modeling process of this statue. "
            "In front of the packaging box, this statue should be placed on a round plastic base. "
            "The statue must have 3D dimensionality and a sense of realism, and the texture of the PVC material needs to be clearly represented. "
            "The statue should occupy a moderate portion of the scene, not too large, so that the surrounding packaging, tabletop, and background elements are clearly visible and well balanced in the composition. "
            "The tabletop and surrounding scene should have additional details, such as scattered drawing tools, reference sheets, notebooks, small stationery, coffee cups, or small decorative items, to make the environment richer but not cluttered. "
            "Ensure that these extra elements do not obscure the statue and maintain proper perspective. "
            "If the background can be set as an indoor scene, the effect will be even better. "
            "Below are detailed guidelines to note: "
            "When repairing any missing parts, there must be no poorly executed elements. "
            "When repairing human figures (if applicable), the body parts must be natural, movements must be coordinated, and the proportions of all parts must be reasonable. "
            "If the original photo is not a full-body shot, try to supplement the statue to make it a full-body version. "
            "The human figure's expression and movements must be exactly consistent with those in the photo. "
            "The figure's head should not appear too large, its legs should not appear too short, and the figure should not look stunted—this guideline may be ignored if the statue is a chibi-style design. "
            "For animal statues, the realism and level of detail of the fur should be reduced to make it more like a statue rather than the real original creature. "
            "No outer outline lines should be present, and the statue must not be flat. "
            "Please pay attention to the perspective relationship of near objects appearing larger and far objects smaller."
        )

        # 初始化 aiohttp 会话
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10))

    async def terminate(self):
        try:
            await self.session.close()
        except Exception as e:
            logger.exception("关闭 aiohttp 会话时出错: %s", e)

    # 使用 regex 替代 keyword，避免新版本 AttributeError
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
            text = self.text

            params = {
                "text": text,
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

