from typing_extensions import TypedDict

from cheshire.generic.command import *

LightStateDict = TypedDict(
    'LightStateDict', 
    {
        'SwitchCommand': SwitchCommand,
        'BrightnessCommand': BrightnessCommand,
        'ColorTemperatureCommand': ColorTemperatureCommand,
        'RGBCommand': RGBCommand,
        'WhiteCommand': WhiteCommand,
        'EffectCommand': EffectCommand,
        'SpeedCommand': SpeedCommand
    },
    total=False
)

class LightState:
    """Represents the desired state of a light by collecting the latest of each 
    type of command."""
    def __init__(
        self,
        *,
        switch: bool | None = None,
        brightness: int | None = None,
        color_temp: tuple[int, int] | None = None,
        rgb: tuple[int, int, int] | None = None,
        white: int | None = None,
        effect: Effect | None = None,
        speed: int | None = None
    ) -> None:
        self._state: LightStateDict = {}

        if switch is not None:
            self.update(SwitchCommand(switch))
        if brightness is not None:
            self.update(BrightnessCommand(brightness))
        if color_temp is not None:
            self.update(ColorTemperatureCommand(color_temp[0], color_temp[1]))
        if rgb is not None:
            self.update(RGBCommand(rgb[0], rgb[1], rgb[2]))
        if white is not None:
            self.update(WhiteCommand(white))
        if effect is not None:
            self.update(EffectCommand(effect))
        if speed is not None:
            self.update(SpeedCommand(speed))

    def update(self, c: Command):
        self._state[c.get_type()] = c

    @property
    def state(self):
        return self._state
