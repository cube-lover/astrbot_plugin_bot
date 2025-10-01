from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import urllib.parse

@register("astrbot_plugin_gemini", "知鱼", "通过 MissQiu Gemini API 生成图片", "1.0.0", "https://github.com/yourrepo/astrbot_plugin_gemini")
class GeminiPlugin(Star):
    """Gemini 图片生成插件

    触发方式：/gen_image 描述词
    """

    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化 aiohttp 会话，增加连接限制，防止占用过多连接
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10))
        # TODO: 替换为你的 API Key
        self.apikey = "你的APIKEY"

    async def terminate(self):
        """插件停用或卸载时关闭 aiohttp 会话"""
        try:
            await self.session.close()
        except Exception as e:
            logger.exception("关闭 aiohttp 会话时出错: %s", e)

    @filter.command("gen_image")
    async def gen_image(self, event: AstrMessageEvent):
        """生成图片指令"""
        try:
            # 获取用户输入文本
            text = event.get_message_content().strip()
            if not text:
                yield event.plain_result("请在指令后输入描述词，例如：/gen_image 画个猫")
                return

            # 请求参数
            params = {
                "text": text,
                "width": "1024",
                "height": "1024",
                "type": "wen",   # 文生图
                "tc": "no",      # 直接返回图片
                "enhance": "false",
                "apikey": self.apikey
            }
            url = "https://missqiu.icu/API/Gemini.php?" + urllib.parse.urlencode(params)

            # 异步请求图片
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    logger.warning("Gemini API 返回非 200 响应: %s", resp.status)
                    yield event.plain_result(f"图片生成失败，状态码: {resp.status}")
                    return
                img_bytes = await resp.read()  # 获取图片二进制

            # 返回图片消息
            yield event.image_result(img_bytes)

        except Exception:
            logger.exception("处理生成图片指令时发生异常")
            yield event.plain_result("图片生成异常，请稍后重试。")

