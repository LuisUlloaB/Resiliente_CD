# Controlador Digital - Proyecto Resiliente
_El repositorio Resiliente-CD almacenará los avances en el desarrollo de scripts para el Controlador Digital, con el fin de facilitar el desarrollo cooperativo entre todos las personas involucradas en el proyecto._

## Descripción de scripts
_Scripts principales:_

| Script | Descripción |
| :----: | :---------- |
| **resiliente.py** | Script encargado de iniciar la comunicación con los módulos del sistema a traves del protocolo ModBus, así como de solicitar parámetros de monitoreo y verificar *flags* de activación en los módulos receptores de alerta. Escribe en las tablas de monitoreo de la base de datos: *resiliente.db*. |
| **activador.py** | Si *resiliente.py* detecta un *flag* de activación en algún módulo receptor, este llama a la función *activar()* de *activador.py* para solicitar al módulo donde detecto el flag sus parámetros de activación, estos serán almacenados en la tabla *activacion* de la base de datos *resiliente.db* y procesados para extraer los parámetros que determinan el tipo de audio a usar, estos parámetros se almacenan en un archivo de formato JSON, *audio_param.json*. | 
| **disparador.py** | Script encargado de verificar si los parámetros de monitoreo ya almacenandos en la base de datos coinciden con el valor (o rango de valores) esperado, en caso no coincidan se estructura un archivo en formato JSON indicando el módulo, parámetro y el valor erroneo, luego este archivo se envía al servidor Web mediante un canal SFTP. También es función de este script enviar un flag de encendido al *sub - módulo de Potencia* cuando la fecha actual coincida con el rango de fecha de inicio y final del último registro en la tabla *activacion* de la base de datos. Finalmente, este script debe estar preparado para recibir solicitudes de monitoreo desde el servidor web, procesarlas y enviar una respuesta con los parámetros solicitados. |
| **sftp.py** | Script utilizado para establecer una conexión SFTP y enviar archivos al servidor web. |
| **stream_audio.py** | Script encargado de procesar el archivo *audio_param.json* y seleccionar de entre la carpeta *./audios/* los audios adecuados para la activación de alerta. Leerá de la tabla de *activacion* de la base de datos los parámetros de fecha *inicio* y *final* de la activación y cuando la fecha actual se encuentre en el rango de los parámetros reproducirá el conjunto de audios seleccionados. |
| **apagado_seguro.py** | Script para detectar la señal de apagado seguro del *Sub - Módulo Controlador central (Raspberry Pi)* cuando el *Sub - Módulo de sensores* pone en 'HIGH' el pin GPIO 17 del controlador central.|

_Scripts usados para pruebas_

| Script | Descripción |
| :----: | :---------- |
| **apagar_buzzer.py** | Pone en 'LOW' el flag hacia el *Sub - módulo de potencia*. |
| **./clock/clock.sh** | Muestra la fecha del Raspberry Pi y del RTC de respaldo. |
| **./clock/test_timesync.sh** | Verifica si la fecha del Raspberry Pi y RTC están sincronizadas. |

## Librerías requeridas
  * PyModBus: [Documentación](https://buildmedia.readthedocs.org/media/pdf/pymodbus/latest/pymodbus.pdf)
    ```
    $ pip install pymodbus
    ```
  * vlc:
    ```
    $ pip install python-vlc
    ```
  * sftp: [Documentación](https://buildmedia.readthedocs.org/media/pdf/pysftp/release_0.2.9/pysftp.pdf)
    ```
    $ pip3 install pysftp
    ```
    
## ¿Cómo empezar?
  Para inciar el controlador digital se deben ejecutar 3 scripts:
  ```
  $ python3 resiliente.py
  ```
  ```
  $ python3 disparador.py
  ```
  ```
  $ python stream_audio.py
  ```
 Se recomienda ejecutar cada script en un terminal diferente, ya que cada uno de ellos al estar ejecutándose irá mostrando su proceso en pantalla.
 
## Tareas pendientes
- [x] Monitoreo de módulos del sistema
- [x] Activación de alerta por módulos receptores (RDS, TDT y Manual)
- [x] Activación de alerta por Servidor Web
- [x] Fichero de configuración de parámetros del sistema
- [ ] Desarrollo del modo Test
- [ ] Automatizar ejecución de scripts usando demonios y servicios
- [ ] Desarrollo de Sub - Módulo de sensores (STM32)
