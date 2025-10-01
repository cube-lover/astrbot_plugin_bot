from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain, Video 
import aiohttp
import base64

@register("beauty_video", "美女视频", "获取美女视频的插件", "1.0")
class BeautyVideoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.encrypted_api = "aHR0cHM6Ly9hcGkuczAxcy5jbi9BUEkvbXZzcC8="
        self.session = aiohttp.ClientSession()
    async def terminate(self):
        await self.session.close()
    def _decrypt_api(self):
        return base64.b64decode(self.encrypted_api).decode()
    @filter.regex(r"^[/]?(美女视频|看视频|看美女)$")
    async def get_beauty_video(self, event: AstrMessageEvent):
        try:
            real_api_url = self._decrypt_api()
            
            async with self.session.get(real_api_url) as response:
                if response.status == 200:
                    video_component = Video.fromURL(real_api_url)
                    yield event.chain_result([video_component])
                else:
                    yield event.plain_result("获取视频失败 请稍后重试")

        except Exception:
            yield event.plain_result("视频异常 请稍后重试")
