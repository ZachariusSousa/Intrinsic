import math


class WeatherSystem:
    """Simple day/night cycle and seasonal weather manager."""

    def __init__(self, day_length=12000, season_length=48000):
        # Number of environment steps that make up one day and one season
        self.day_length = day_length
        self.season_length = season_length
        self.tick = 0
        self.seasons = ["spring", "summer", "autumn", "winter"]
        self._season_index = 0

    @property
    def time_of_day(self) -> int:
        """Return the current time within the day [0, day_length)."""
        return self.tick % self.day_length

    @property
    def current_season(self) -> str:
        return self.seasons[self._season_index]

    def is_daytime(self) -> bool:
        """Return True if it's currently daytime."""
        return self.time_of_day < self.day_length / 2

    def step(self) -> None:
        """Advance the weather system by one tick."""
        self.tick += 1
        if self.tick % self.season_length == 0:
            self._season_index = (self._season_index + 1) % len(self.seasons)

    def get_light_intensity(self) -> float:
        """Return a lighting factor between 0 (dark) and 1 (full daylight)."""
        phase = self.time_of_day / self.day_length
        # Sinusoidal cycle: 0.3 at midnight, 1 at midday
        return 0.3 + 0.7 * math.sin(math.pi * phase)

    def get_sky_color(self) -> tuple:
        """Return the current sky color based on season and time of day."""
        base_colors = {
            "spring": (135, 206, 235),
            "summer": (100, 150, 255),
            "autumn": (135, 160, 220),
            "winter": (180, 220, 255),
        }
        base = base_colors[self.current_season]
        light = self.get_light_intensity()
        return tuple(int(c * light) for c in base)
