"""obox 内置组件表：21 个既有标签 + chart + collapse。"""

from __future__ import annotations

from .alert import AlertComponent
from .button import ButtonComponent
from .card import CardComponent
from .chart import ChartComponent
from .checkbox import CheckboxComponent
from .choice import ChoiceComponent
from .collapse import CollapseComponent
from .container import DivComponent, TextComponent
from .flex import FlexComponent
from .image import ImageComponent
from .input import InputComponent, TextAreaComponent
from .modal import ModalComponent
from .navitem import NavItemComponent
from .notification import NotificationComponent
from .radio import RadioComponent
from .select import SelectComponent
from .slider import SliderComponent
from .switch import SwitchComponent
from .table import TableComponent
from .tabs import TabsComponent
from .tag import TagComponent

COMPONENT_TYPES = {
    component.tag: component
    for component in (
        DivComponent,
        TextComponent,
        ButtonComponent,
        InputComponent,
        TextAreaComponent,
        CheckboxComponent,
        RadioComponent,
        SwitchComponent,
        SelectComponent,
        SliderComponent,
        TagComponent,
        TableComponent,
        TabsComponent,
        ModalComponent,
        NotificationComponent,
        FlexComponent,
        CardComponent,
        AlertComponent,
        ImageComponent,
        NavItemComponent,
        ChoiceComponent,
        CollapseComponent,
        ChartComponent,
    )
}

__all__ = ["COMPONENT_TYPES"]