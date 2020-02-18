from service import Service, Message
from service.error import UnknownMessageType
from vk_utils.registrate import VkSettings
from vk_utils.requests_service import RequestService
from vk_utils.settings import VkSettingsData


class DoVkMethod(Message):
    def __init__(self, method: str, **params):
        super().__init__()
        self.method = method
        self.params = params


class VkMethod(Service):
    def __init__(self, message: Message):
        super().__init__(message)
        self.settings: VkSettingsData
        self.additional_params: dict

    async def warm_up(self):
        self.settings = await VkSettings.settings()
        self.additional_params = {
            'access_token': self.settings.token,
            'lang': 'ru',
            'v': "5.103"
        }

    async def process(self, message: Message):
        if isinstance(message, DoVkMethod):
            return await RequestService.get_request(
                f"{self.settings.api_host}{message.method}",
                {**message.params, **self.additional_params}
            )
        raise UnknownMessageType(self, message)

