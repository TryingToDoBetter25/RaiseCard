# raisecard.py

# encoding:utf-8
import requests
import os
import plugins
from io import BytesIO
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *
from PIL import Image  # 添加Pillow库导入

@plugins.register(
    name="RaiseCard",
    desire_priority=100,
    hidden=False,
    desc="A simple plugin that raises a card with a given message",
    version="0.1",
    author="金永勋 微信：xun900207",
)
class RaiseCardPlugin(Plugin):
    def __init__(self):
        super().__init__()
        try:
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[RaiseCardPlugin] inited.")
        except Exception as e:
            logger.warn("[RaiseCardPlugin] init failed, ignore.")
            raise e

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return

        content = e_context["context"].content.strip()
        
        if content.startswith("举牌"):
            message = content.replace("举牌", "").strip()
            image_url = self.get_card_image_url(message)
            if image_url:
                image_data = self.download_image(image_url)
                if image_data:
                    reply = Reply(ReplyType.IMAGE, image_data)
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                else:
                    reply = Reply(ReplyType.TEXT, "无法保存卡片图片，请稍后再试。")
                    e_context["reply"] = reply
            else:
                reply = Reply(ReplyType.TEXT, "无法生成卡片图片，请稍后再试。")
                e_context["reply"] = reply

    def get_help_text(self, **kwargs):
        help_text = "输入【举牌 [消息]】 来生成带有指定消息的卡片图片。"
        return help_text

    def get_card_image_url(self, message):
        api_url = "https://api.suyanw.cn/api/zt.php"
        try:
            response = requests.get(api_url, params={"msg": message})
            response.raise_for_status()
            
            # 检查响应内容类型是否为图片
            content_type = response.headers.get('Content-Type')
            if 'image' in content_type:
                logger.debug("Image content detected")
                return response.url  # 直接使用请求的URL
            
            data = response.json()
            return data.get("image")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except ValueError:
            logger.error("Failed to parse JSON response")
            return None

    def download_image(self, image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            # 将响应内容转换为PIL图像
            image = Image.open(BytesIO(response.content))
            
            # 转换图像模式为RGBA（如果不是的话）
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # 创建新的白色背景图像
            background = Image.new('RGBA', image.size, (255, 255, 255, 255))
            
            # 将原图像合并到白色背景上
            # composite_image = Image.alpha_composite(background, image)
            
            # 使用白色背景混合
            composite_image = background.copy()
            composite_image.paste(image, (0, 0), image)
            
            # 转换回BytesIO对象
            output = BytesIO()
            composite_image.save(output, format='PNG')
            output.seek(0)
            
            logger.info("Image processed and background changed to white")
            return output
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return None

# 示例调用
if __name__ == "__main__":
    plugin = RaiseCardPlugin()
    print(plugin.get_card_image_url("上班996别墅靠大海"))
