import os
import sys

# Add the directory to sys.path
sys.path.append('.')

try:
    from utils import (
        read_recent_unread_emails, clean_text_for_speech, trim_response, clean_input, speak, sleep_now, change_wallpaper,
        listen, get_mistral_response, get_weather, get_weather_tomorrow, when_will_rain, web_search, load_contacts, send_email, count_recent_unread_emails,
        play_music, stop_music, pause_music, next_track, music_volume_down, shutdown, update, add_reminder, list_reminders, run_schedule_loop, get_top_news,
        get_battery_status, wiki_summary, get_ip, get_system_stats, start_timer, tell_joke, create_note,
        get_current_datetime, play_youtube, find_file, get_clipboard, convert_currency, generate_image, self_destruct,
        read_pdf, get_weather_forecast, update_assistant_code, get_time_based_greeting, get_uptime, scan_ports, get_public_ip,
        scan_wifi, save_voice_note, get_daily_affirmation, toggle_battery_saver, play_ambient_sound, take_webcam_photo,
        backup_files, download_instagram_reel, convert_md_to_html, generate_password, check_linux_updates, handle_unknown_request,
        decrease_volume, decrease_brightness, increase_volume, increase_brightness, take_screenshot, toggle_night_mode, translate_text, close_app, open_app, turn_on_tv, turn_off_tv, music_volume_up,
        tv_volume_up_cmd, tv_volume_down_cmd, tv_channel_up_cmd, tv_channel_down_cmd, tv_open_app_cmd, tv_exit_app_cmd, tv_set_channel_cmd, tv_mute_cmd, is_tv_on, ensure_tv_is_on, tv_set_input_cmd, get_doorbell_status_cmd, show_doorbell_image, show_doorbell_stream
    )
    print("IMPORTS_OK")
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
except Exception as e:
    print(f"OTHER_ERROR: {e}")
