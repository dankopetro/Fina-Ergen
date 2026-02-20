
import re

file_path = './src/App.vue'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscamos el bloque SUPPORTED_MESSAGING_APPS
start_marker = "const SUPPORTED_MESSAGING_APPS = {"

start_idx = content.find(start_marker)
if start_idx == -1:
    print("Error: No se encontró SUPPORTED_MESSAGING_APPS")
    exit(1)

# Encontrar el final balanceando llaves
brace_count = 0
i = start_idx + len(start_marker)
found_start = False
end_idx = -1

brace_count = 1 

while i < len(content):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end_idx = i + 1
            break
    i += 1

if end_idx == -1:
    print("Error: No se pudo determinar el final del objeto")
    exit(1)

# Nuevo contenido (Completo Global)
new_apps_definition = """const SUPPORTED_MESSAGING_APPS = {
    'sms': { 
        id: 'sms',
        name: 'SMS', 
        package: 'com.android.mms', 
        icon: 'fa-solid fa-comment-sms', 
        color: 'text-blue-500',
        isDefault: true
    },
    'whatsapp': { 
        id: 'whatsapp',
        name: 'WhatsApp', 
        package: 'com.whatsapp', 
        icon: 'fa-brands fa-whatsapp', 
        color: 'text-green-500',
        uri: 'https://api.whatsapp.com/send?phone={phone}&text={text}'
    },
    'telegram': { 
        id: 'telegram',
        name: 'Telegram', 
        package: 'org.telegram.messenger', 
        icon: 'fa-brands fa-telegram', 
        color: 'text-cyan-400',
        uri: 'tg://msg?text={text}&to={phone}'
    },
    'signal': {
        id: 'signal',
        name: 'Signal',
        package: 'org.thoughtcrime.securesms',
        icon: 'fa-solid fa-shield-halved',
        color: 'text-indigo-400',
        uri: 'smsto:{phone}:{text}'
    },
    'wechat': { 
        id: 'wechat',
        name: 'WeChat', 
        package: 'com.tencent.mm', 
        icon: 'fa-brands fa-weixin',
        color: 'text-green-600',
        uri: 'weixin://'
    },
    'qq': {
        id: 'qq',
        name: 'QQ',
        package: 'com.tencent.mobileqq',
        icon: 'fa-brands fa-qq', 
        color: 'text-blue-500',
        uri: 'mqqwpa://im/chat?chat_type=wpa&uin={phone}&version=1&src_type=web'
    },
    'line': {
        id: 'line',
        name: 'LINE',
        package: 'jp.naver.line.android',
        icon: 'fa-brands fa-line',
        color: 'text-green-500',
        uri: 'https://line.me/R/msg/text/?{text}'
    },
    'viber': {
        id: 'viber',
        name: 'Viber',
        package: 'com.viber.voip',
        icon: 'fa-brands fa-viber',
        color: 'text-purple-600',
        uri: 'viber://chat?number={phone}'
    },
    'kakaotalk': {
        id: 'kakaotalk',
        name: 'KakaoTalk',
        package: 'com.kakao.talk',
        icon: 'fa-solid fa-comment', 
        color: 'text-yellow-400',
        uri: 'kakaotalk://'
    }
};"""

final_content = content[:start_idx] + new_apps_definition + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("✅ Lista de Apps de Mensajería Global actualizada.")
