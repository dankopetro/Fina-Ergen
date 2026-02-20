import subprocess
import sys

def test_transaction(code, params):
    cmd = f"adb -s 192.168.0.6:5555 shell service call isms {code} {params}"
    print(f"Testing {code} with {params}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Stdout: {res.stdout}")
    print(f"Stderr: {res.stderr}")

# Probar transacciones comunes de envío de texto
# Transacción 6: sendText (Old style)
# Transacción 7: sendMultipartText
# Transacción 18: sendTextForSubscriber (New style)
# Transacción 19: sendMultipartTextForSubscriber

# Parámetros para Transaction 6 (Aprox 7-8)
test_transaction(6, 'i32 0 s16 "com.android.shell" s16 "null" s16 "2213999606" s16 "null" s16 "ENGINEER_6" s16 "null" s16 "null"')

# Parámetros para Transaction 18 (Aprox 12-14)
test_transaction(18, 'i32 0 s16 "com.android.shell" s16 "null" s16 "2213999606" s16 "null" s16 "ENGINEER_18" s16 "null" s16 "null" i32 1 i32 -1 i32 0 i32 -1')
