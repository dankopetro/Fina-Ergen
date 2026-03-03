import json

new_phrases = {
    "about": {
        "en": ["who created you", "who made you", "what version are you", "about fina", "system info"],
        "fr": ["qui t'a créé", "quelle est ta version", "à propos de fina", "info système"],
        "de": ["wer hat dich gemacht", "wer hat dich erschaffen", "welche version bist du", "über fina"],
        "ja": ["誰があなたを作りましたか", "あなたのバージョンは何ですか", "finaについて", "システム情報"],
        "zh": ["谁创造了你", "你是什么版本", "关于fina", "系统信息"]
    },
    "ac_control": {
        "en": ["turn off the ac", "turn on the ac", "set ac to 24 degrees", "turn off the air conditioning"],
        "fr": ["allume la clim", "éteins la clim", "mets la clim à 24"],
        "de": ["schalte die klimaanlage ein", "schalte die klimaanlage aus", "stelle die klimaanlage auf 24"],
        "ja": ["エアコンをつけて", "エアコンを消して", "エアコンを24度にして"],
        "zh": ["打开空调", "关闭空调", "把空调设为24度"]
    },
    "hangup_doorbell": {
        "en": ["hang up the doorbell", "end call", "hang up", "close the door"],
        "fr": ["raccroche", "termine l'appel", "ferme la porte"],
        "de": ["leg auf", "beende den anruf", "schließe die tür"],
        "ja": ["切って", "電話を切る", "ドアを閉める"],
        "zh": ["挂断", "结束通话", "关门"]
    },
    "exit": {
        "en": ["bye", "goodbye", "go to sleep", "stop listening"],
        "fr": ["au revoir", "salut", "dors", "arrête d'écouter"],
        "de": ["tschüss", "auf wiedersehen", "geh schlafen", "hör auf zuzuhören"],
        "ja": ["さようなら", "バイバイ", "寝て", "聞くのをやめて"],
        "zh": ["再见", "拜拜", "去睡觉", "停止聆听"]
    },
    "play_music": {
        "en": ["play some music", "start music", "play a song"],
        "fr": ["mets de la musique", "joue une chanson"],
        "de": ["spiel musik", "spiel ein lied"],
        "ja": ["音楽をかけて", "歌を再生して"],
        "zh": ["播放音乐", "放首歌"]
    },
    "stop_music": {
        "en": ["stop the music", "pause the song", "music off"],
        "fr": ["arrête la musique", "mets en pause"],
        "de": ["stoppe die musik", "musik aus"],
        "ja": ["音楽を止めて", "音楽を消して"],
        "zh": ["停止音乐", "关掉音乐"]
    },
    "pause_music": {
        "en": ["pause the music", "pause it"],
        "fr": ["pause la musique", "pause"],
        "de": ["pausiere die musik", "pause"],
        "ja": ["音楽を一時停止して", "一時停止"],
        "zh": ["暂停音乐", "暂停"]
    },
    "next_track": {
        "en": ["next song", "next track", "skip this song"],
        "fr": ["chanson suivante", "piste suivante"],
        "de": ["nächstes lied", "nächster titel"],
        "ja": ["次の曲", "スキップして"],
        "zh": ["下一首歌", "跳过这首歌"]
    },
    "shutdown": {
        "en": ["shutdown the computer", "turn off the pc"],
        "fr": ["éteins l'ordinateur", "éteins le pc"],
        "de": ["schalte den computer aus", "pc herunterfahren"],
        "ja": ["パソコンをシャットダウンして", "pcの電源を切って"],
        "zh": ["关闭电脑", "关机"]
    },
    "restart_pc": {
        "en": ["restart the computer", "reboot the pc"],
        "fr": ["redémarre l'ordinateur", "redémarre le pc"],
        "de": ["starte den computer neu", "pc neustarten"],
        "ja": ["パソコンを再起動して", "再起動して"],
        "zh": ["重启电脑", "重启"]
    },
    "suspend": {
        "en": ["suspend the computer", "put pc to sleep"],
        "fr": ["mets l'ordinateur en veille", "suspendre"],
        "de": ["computer in energiesparmodus", "suspendieren"],
        "ja": ["パソコンをスリープにして", "スリープ"],
        "zh": ["让电脑睡眠", "睡眠"]
    },
    "wake_up": {
        "en": ["fina", "wake up fina", "are you there", "listen to me"],
        "fr": ["fina", "réveille-toi fina", "tu es là"],
        "de": ["fina", "wach auf", "bist du da"],
        "ja": ["fina", "起きて", "聞いてる？"],
        "zh": ["fina", "醒醒", "你在吗"]
    },
    "web_search": {
        "en": ["search the web", "google this", "find this online"],
        "fr": ["cherche sur le web", "google ça", "trouve ça en ligne"],
        "de": ["suche im internet", "google das", "finde das online"],
        "ja": ["ウェブで検索して", "ググって", "ネットで調べて"],
        "zh": ["在网上搜一下", "谷歌一下", "搜索"]
    },
    "get_weather": {
        "en": ["how is the weather", "what's the weather like", "weather forecast"],
        "fr": ["quel temps fait-il", "météo"],
        "de": ["wie ist das wetter", "wettervorhersage"],
        "ja": ["天気はどうですか", "天気予報"],
        "zh": ["天气怎么样", "天气预报"]
    },
    "take_screenshot": {
        "en": ["take a screenshot", "capture the screen"],
        "fr": ["fais une capture d'écran", "capture l'écran"],
        "de": ["mache einen screenshot", "bildschirmfoto"],
        "ja": ["スクリーンショットを撮って", "スクショ"],
        "zh": ["截图", "截屏"]
    },
    "tv_on": {
        "en": ["turn on the tv", "power on television", "start the tv"],
        "fr": ["allume la télévision", "allume la télé"],
        "de": ["schalte den fernseher ein", "fernseher an"],
        "ja": ["テレビをつけて"],
        "zh": ["打开电视"]
    },
    "tv_off": {
        "en": ["turn off the tv", "power off television"],
        "fr": ["éteins la télé", "ferme la télévision"],
        "de": ["schalte den fernseher aus", "fernseher aus"],
        "ja": ["テレビを消して"],
        "zh": ["关掉电视"]
    }
}

try:
    with open('intents.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for intent, langs in new_phrases.items():
        if intent not in data:
            data[intent] = []
        for lang, phrases in langs.items():
            for phrase in phrases:
                if phrase not in data[intent]:
                    data[intent].append(phrase)

    with open('intents.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Intents translated successfully")
except Exception as e:
    print("Error:", str(e))
