
import s_tool
import sun_calendar
import valid_night_obs



sun_data = sun_calendar.sun_set_rise()

rise , sett = sun_data["lst_rise"], sun_data["lst_set"]

select_nightime = sun_calendar.get_nighttime()

night_observations = s_tool.nightobs()


