# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    action.py                                          :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ioriiod0 <ioriiod0@gmail.com>              +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2019/01/08 13:52:22 by ioriiod0          #+#    #+#              #
#    Updated: 2019/01/17 14:03:53 by ioriiod0         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

from .types import Request, Response
from typing import Mapping, Type, Optional, Callable, Sequence
import random


from jinja2 import Template


ACTION_RESTART = "action_restart"
ACTION_LISTEN = "action_listen"


class ActionNotFound(Exception):
    pass


class Action(object):
    def __init__(self):
        super(Action, self).__init__()
        self.name = None

    def __call__(self, bot: Type['Bot'], tracker: Type['Tracker'], msg: Type[Request]) -> Optional[Response]:
        for f in bot._before_action:
            f(self, tracker, msg)

        ret = self.run(bot, tracker, msg)

        if isinstance(ret, str):
            ret = Response(ret)
        elif isinstance(ret, dict):
            ret = Response(**ret)

        for f in bot._after_action:
            f(self, tracker, msg)
        return ret

    def run(self, bot: Type['Bot'], tracker: Type['Tracker'], msg: Type[Request]) -> Optional[Response]:
        raise NotImplementedError("not implemented")

    def __str__(self):
        return "<action: %s>" % self.name


class ActionUtterTemplate(Action):
    def __init__(self, tpls: Sequence[str]):
        super(ActionUtterTemplate, self).__init__()
        self.templates = [Template(tpl) for tpl in tpls]

    def run(self, bot: Type['Bot'], tracker: Type['Tracker'], msg: Type[Request]) -> Response:
        template = random.choice(self.templates)
        text = template.render(tracker._as_dict())
        return Response(body=text)


class ActionFunctor(Action):
    def __init__(self, func: Callable[[Type['Bot'], Type['Tracker']], Optional[Mapping]]):
        super(ActionFunctor, self).__init__()
        self.func = func

    def run(self, bot: Type['Bot'], tracker: Type['Tracker'], msg: Type[Request]) -> Optional[Response]:
        return self.func(bot, tracker, msg)


class ActionRestart(Action):
    DEFAULT_UTTER_ACTION = 'utter_restart'

    def __init__(self):
        super(ActionRestart, self).__init__()

    def run(self, bot: Type['Bot'], tracker: Type['Tracker'], msg: Type[Request]) -> Optional[Response]:
        bot.reset()
        try:
            return bot.execute_action(self.DEFAULT_UTTER_ACTION, tracker, msg)
        except ActionNotFound as e:
            return None


class ActionListen(Action):
    def __init__(self):
        super(ActionListen, self).__init__()

    def run(self, bot: Type['Bot'], tracker: Type['Tracker'], msg: Type[Request]) -> None:
        return None


class ActionHubMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'ActionHub':
            return type.__new__(cls, name, bases, attrs)

        # add default action
        assert ACTION_RESTART not in attrs
        assert ACTION_LISTEN not in attrs

        attrs[ACTION_RESTART] = ActionRestart()
        attrs[ACTION_LISTEN] = ActionListen()

        actions = {}
        for k, v in attrs.items():
            if isinstance(v, Action):
                actions[k] = v
            elif isinstance(v, str):
                actions[k] = ActionUtterTemplate([v])
            elif callable(v):
                actions[k] = ActionFunctor(v)
            elif isinstance(v, (list, tuple)):
                actions[k] = ActionUtterTemplate(v)
            else:
                raise Exception('unkown action type')
            actions[k].name = k

        for k in actions.keys():
            attrs.pop(k)

        attrs['__domain__'] = name  # 假设表名和类名一致
        attrs['__actions__'] = actions  # 保存属性和列的映射关系
        return type.__new__(cls, name, bases, attrs)


class ActionHub(object, metaclass=ActionHubMetaclass):
    def __init__(self):
        super(ActionHub, self).__init__()

    def __getitem__(self, k: str) -> Type[Action]:
        act = self.__actions__.get(k)
        if act is None:
            raise ActionNotFound('action %s not found' % k)
        return act

    def __str__(self):
        return str(self.__actions__)
