"""Quickstart demo for hvacpy v0.2."""
from hvacpy import Q_, AirState, AirProcess, PsychChart

# Standard office air
office = AirState(dry_bulb=Q_(25, 'degC'), rh=0.60)
print(f'Dry bulb:   {office.dry_bulb:.1f}')
print(f'Wet bulb:   {office.wet_bulb:.2f}')
print(f'Dew point:  {office.dew_point:.2f}')
print(f'Humidity:   {office.humidity_ratio:.5f}')
h_kj = office.enthalpy.to("kJ/kg")
print(f'Enthalpy:   {h_kj:.2f}')
print(f'Density:    {office.density:.4f}')

# Cooling process
supply = AirState(dry_bulb=Q_(13, 'degC'), rh=0.95)
process = AirProcess(office, supply, Q_(1.5, 'kg/s'))
print(f'Process:    {process.process_type}')
total_kw = process.total_heat.to("kW")
print(f'Total heat: {total_kw:.2f}')
print(f'SHR:        {process.sensible_ratio:.3f}')

# Chart
chart = PsychChart()
chart.add_point('Office', office, color='blue')
chart.add_point('Supply', supply, color='green')
chart.add_process(process, label='Cooling coil')
chart.save('psychro_demo.png')
print('Chart saved to psychro_demo.png')
