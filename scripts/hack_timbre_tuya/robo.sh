#!/system/bin/sh
echo "Iniciando Robo..."
cd /data/user/0/com.tuya.smart
tar cvf /sdcard/tuya_backup.tar .
echo "Robo completado. Archivo en /sdcard/tuya_backup.tar"
chmod 777 /sdcard/tuya_backup.tar
