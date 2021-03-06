import celery
import pendulum

from api import tasks, utils
from api.models import Log
from api.v1 import tasks as v1_tasks


def create_log(content, log_type, owner, expires, privacy, guild, **kwargs) -> Log:
    """
    Create a log using specified data.
    :param content: Raw content of log.
    :type content: str
    :param log_type: Type of log, can be none if :param content is a list.
    :type log_type: Union[str, None]
    :param owner: Log owner.
    :param expires: Expiration time of log.
    :type expires: Union[str, None]
    :param privacy: Log privacy setting.
    :type privacy: str
    :param guild: Linked guild of log. Must be set if privacy setting is either guild or mods.
    :type guild: int
    :param kwargs: Extraneous data.
    """
    data = {'type': log_type, 'content': content, 'owner': owner, 'privacy': privacy, 'guild': guild}
    uuid = data['uuid'] = Log.generate_uuid(content)
    if Log.objects.filter(uuid=uuid).exists():
        return Log.objects.get(uuid=uuid)

    data['expires'] = pendulum.parse(expires) if expires else None

    result = celery.chain(
        v1_tasks.parse_text.s(log_type, content), tasks.parse_json.s() | tasks.create_pages.s(uuid)
    )()

    data['data'] = {'tasks': list(reversed(result.as_list())), **kwargs}

    return Log.objects.create(**data)
