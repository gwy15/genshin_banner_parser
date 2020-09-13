import json
from dataclasses import dataclass
from enum import Enum
import itertools
from typing import List
from pathlib import Path


class GachaType(Enum):
    Character = 1
    Weapon = 2


@dataclass
class GachaItem:
    type: GachaType
    name: str
    star: int

    prob_percentage: float
    is_up: bool

    def from_data(data: dict) -> 'GachaItem':
        if data['item_type'] == '角色':
            type = GachaType.Character
        elif data['item_type'] == '武器':
            type = GachaType.Weapon
        else:
            raise RuntimeError(f'Unknown type: {data}')

        p = float(data['prob'].rstrip('%'))

        return GachaItem(
            type=type,
            name=data['item_name'].strip(' '),
            prob_percentage=p,
            star=int(data['rank']),
            is_up=bool(int(data['is_up']))
        )


@dataclass
class Banner:
    title: str
    _5_gachas: List[GachaItem]
    _4_gachas: List[GachaItem]
    _3_gachas: List[GachaItem]

    def check(self):
        total_p = self._5_star + self._4_star + self._3_star
        print(f'checking: {total_p = }')
        assert abs(100 - total_p) < 0.01

        # 分类为 up x 类型，要求概率相同
        from collections import defaultdict
        for gachas in (self._3_gachas, self._4_gachas, self._5_gachas):
            for is_up in (True, False):
                for type in (GachaType.Character, GachaType.Weapon):
                    l = [
                        item for item in gachas
                        if item.is_up == is_up and item.type == type
                    ]
                    if len(l) >= 1:
                        assert all(
                            abs(l[0].prob_percentage -
                                item.prob_percentage) < 0.01
                            for item in l
                        )
                        print(
                            f'checking:star={l[0].star} {is_up=}, {type=} passed')

    @staticmethod
    def from_data(data: dict) -> 'Banner':
        title = data['title']
        _5_gachas = [GachaItem.from_data(item)
                     for item in data['r5_prob_list']]
        _4_gachas = [GachaItem.from_data(item)
                     for item in data['r4_prob_list']]
        _3_gachas = [GachaItem.from_data(item)
                     for item in data['r3_prob_list']]
        banner = Banner(
            title,
            _5_gachas=_5_gachas,
            _4_gachas=_4_gachas,
            _3_gachas=_3_gachas
        )
        banner.check()
        return banner

    def save(self, path: Path):
        def f(star, is_up, type):
            gachas = {
                3: self._3_gachas,
                4: self._4_gachas,
                5: self._5_gachas
            }[star]
            return [
                i.name for i in gachas if i.type == type and i.is_up == is_up
            ]

        def p(a, b):
            if b == 0:
                return 0.0
            return 100 * (a / b)

        data = {
            'prob': {
                '_5_star': self._5_star,
                '_4_star': self._4_star,

                '_5_star_up': p(self._5_star_up, self._5_star),
                '_4_star_up': p(self._4_star_up, self._4_star),

                '_5_up_char': p(self._5_up_char, self._5_star_up),
                '_5_non_up_char': p(self._5_non_up_char, self._5_star - self._5_star_up),
                '_4_up_char': p(self._4_up_char, self._4_star_up),
                '_4_non_up_char': p(self._4_non_up_char, self._4_star - self._4_star_up),
            },
            'guarantee': {
                '_5_star': 90,
                '_4_star': 10,
                '_5_star_up': 2,
                '_4_star_up': 2
            },
            'pool': {
                '_5_star': {
                    'up': {
                        'char': f(5, True, GachaType.Character),
                        'equip': f(5, True, GachaType.Weapon),
                    },
                    'non_up': {
                        'char': f(5, False, GachaType.Character),
                        'equip': f(5, False, GachaType.Weapon),
                    }
                },
                '_4_star': {
                    'up': {
                        'char': f(4, True, GachaType.Character),
                        'equip': f(4, True, GachaType.Weapon),
                    },
                    'non_up': {
                        'char': f(4, False, GachaType.Character),
                        'equip': f(4, False, GachaType.Weapon),
                    }
                },
                '_3_star': [i.name for i in self._3_gachas]
            }
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 星级概率
    @ property
    def _5_star(self):
        """五星总概率"""
        return sum(item.prob_percentage for item in self._5_gachas)

    @ property
    def _4_star(self):
        """四星总概率"""
        return sum(item.prob_percentage for item in self._4_gachas)

    @ property
    def _3_star(self):
        """三星总概率"""
        return sum(item.prob_percentage for item in self._3_gachas)

    @ property
    def _5_star_up(self):
        """五星 Up 概率"""
        return sum(
            item.prob_percentage
            for item in self._5_gachas
            if item.is_up
        )

    @ property
    def _4_star_up(self):
        """四星 up 概率 """
        return sum(
            item.prob_percentage
            for item in self._4_gachas
            if item.is_up
        )

    # 人物概率
    @ property
    def _5_up_char(self):
        """5星 up 人物概率"""
        return sum(
            item.prob_percentage
            for item in self._5_gachas
            if item.is_up and item.type == GachaType.Character
        )

    @ property
    def _5_non_up_char(self):
        """5星 非up 人物概率"""
        return sum(
            item.prob_percentage
            for item in self._5_gachas
            if not item.is_up and item.type == GachaType.Character
        )

    @ property
    def _4_up_char(self):
        """4星 up 人物概率"""
        return sum(
            item.prob_percentage
            for item in self._4_gachas
            if item.is_up and item.type == GachaType.Character
        )

    @ property
    def _4_non_up_char(self):
        """4星 非up 人物概率"""
        return sum(
            item.prob_percentage
            for item in self._4_gachas
            if not item.is_up and item.type == GachaType.Character
        )
