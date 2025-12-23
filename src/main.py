from math import ceil

import pandas as pd
import plotly.express as px

CW = 0.21
CR = 120.96
RO = 1.204
AREA = 2.28
FR = 0.006
ETA = 0.93
CAPACITY = 85


def kmh_to_ms(v: float) -> float:
  return v / 3.6


def get_consumption(v_ms: float, p_additional: float = 1300) -> float:
  """[kwh/km]."""
  p_roll = CR * v_ms
  f_air = (RO / 2) * v_ms * v_ms * CW * AREA
  p_air = f_air * v_ms
  hours = ((1 / v_ms) * 1000 * 100) / 3600
  driving_energy = ((p_roll + p_air) * hours) * (1 / ETA)  # Wh
  total_energy = driving_energy + (p_additional * hours)  # Wh
  return total_energy / 1000  # kWh / 100km


def get_optimal_speed_kmh(
  soc_start: float,
  distance_km: float,
  charging_power_kw: float,
  charging_penalty_time_h: float = 0.2,  # 6 mins overhead
) -> float:
  def total_time_objective(v_kmh: float) -> float:
    driving_time_h = distance_km / v_kmh
    energy_needed_kwh = (get_consumption(kmh_to_ms(v_kmh)) * distance_km) / 100
    energy_start_kwh = soc_start * CAPACITY
    energy_to_charge = max(0, energy_needed_kwh - energy_start_kwh)
    num_times_charging = ceil(energy_to_charge / CAPACITY)

    penalty = charging_penalty_time_h * num_times_charging if energy_to_charge > 0 else 0
    charging_time_h = (energy_to_charge / charging_power_kw) + penalty

    return driving_time_h + charging_time_h

  speeds = []
  times = []
  consumptions = []
  for speed in range(45, 211):
    speeds.append(speed)
    times.append(total_time_objective(speed))  # hours
    consumptions.append(get_consumption(kmh_to_ms(speed)))

  df = pd.DataFrame({"speed": speeds, "time": times, "consumption": consumptions})
  fig = px.scatter(df, x="speed", y="time", color="consumption")
  fig.update_layout(legend_title="Legend", showlegend=True)
  fig.show()


if __name__ == "__main__":
  get_optimal_speed_kmh(
    soc_start=1,
    distance_km=640,
    charging_power_kw=230,
  )
