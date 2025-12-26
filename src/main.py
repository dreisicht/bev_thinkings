from dataclasses import dataclass
from math import ceil

import pandas as pd
import plotly.express as px
import plotly.io as pio

RO = 1.204  # Air density
G = 9.81  # Gravitational acceleration


@dataclass
class Car:
  """Car properties.

  Args:
    weight: Empty weight of the car including one driver [kg]
    area: Frontal area [m²]
    eta: Powertrain efficiency []
    capacity: Battery capacity [kWh]
    p_additional: Auxiliary power consuption [W]
    cw: Air resistance coefficient []
    cr: Rolling resistance coefficient []
    charging_power: Average charging power of the car [kw]
  """

  weight: int
  area: float
  eta: float
  capacity: float
  p_additional: int
  cw: float
  cr: float
  charging_power: int


def kmh_to_ms(v: float) -> float:
  return v / 3.6


def get_consumption(car: Car, v_ms: float) -> float:
  """Returns the constant speed consumption [kwh/100km]."""
  p_roll = car.cr * G * car.weight * v_ms
  f_air = (RO / 2) * v_ms * v_ms * car.cw * car.area
  p_air = f_air * v_ms
  duration_100km_h = ((1 / v_ms) * 1000 * 100) / 3600
  driving_energy_wh = ((p_roll + p_air) * duration_100km_h) * (1 / car.eta)
  total_energy_wh = driving_energy_wh + (car.p_additional * duration_100km_h)
  return total_energy_wh / 1000  # kWh / 100km


def _get_trip_duration(
  car: Car,
  soc_start: float,
  distance_km: float,
  charging_penalty_time_h: float,
  v_kmh: float,
) -> float:
  driving_time_h = distance_km / v_kmh
  energy_needed_kwh = (get_consumption(car, kmh_to_ms(v_kmh)) * distance_km) / 100
  energy_start_kwh = soc_start * car.capacity
  energy_to_charge_kwh = max(0, energy_needed_kwh - energy_start_kwh)
  num_times_charging = ceil(energy_to_charge_kwh / car.capacity)

  penalty = charging_penalty_time_h * num_times_charging if energy_to_charge_kwh > 0 else 0
  charging_time_h = (energy_to_charge_kwh / car.charging_power) + penalty

  return driving_time_h + charging_time_h


def plot_speed_vs_duration(
  car: Car,
  soc_start: float,
  distance_km: float,
  charging_penalty_time_h: float,
) -> float:
  """Plots the speed over the duration.

  Args:
    car: Instance of a Car dataclass.
    soc_start: Stat of charge []
    distance_km: The distance to cover [km]
    charging_penalty_time_h: Average time loss per charging
  """
  speeds_kmh = []
  times_h = []
  consumptions_kwh_100km = []
  for v_kmh in range(45, 211):
    speeds_kmh.append(v_kmh)
    times_h.append(
      _get_trip_duration(car, soc_start, distance_km, charging_penalty_time_h, v_kmh),
    )  # hours
    consumptions_kwh_100km.append(get_consumption(car, kmh_to_ms(v_kmh)))

  df = pd.DataFrame({"speed": speeds_kmh, "time": times_h, "consumption": consumptions_kwh_100km})
  fig = px.scatter(
    df,
    x="speed",
    y="time",
    color="consumption",
    labels={
      "speed": "Travel speed [km/h]",
      "time": "Total trip time [h]",
      "consumption": "Energy consumption [kWh/100km]",
    },
    hover_data={"speed": ":.1f", "time": ":.2f", "consumption": ":.2f"},
    title="Total travel time over speed",
  )
  fig.update_layout(legend_title="Legend", showlegend=True, title="Constant speed")
  fig.write_html("plot.html")


if __name__ == "__main__":
  cla250 = Car(
    weight=2055,
    area=2.28,
    eta=0.93,
    capacity=85,
    p_additional=1300,
    cw=0.21,
    cr=0.006,
    charging_power=220,
  )
  plot_speed_vs_duration(cla250, soc_start=1, distance_km=1000, charging_penalty_time_h=0.2)
