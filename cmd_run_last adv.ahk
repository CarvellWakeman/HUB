F4::
SetKeyDelay, 5, 5

ControlSend, ,chmod +x runall, ahk_class KiTTY
ControlSend, ,{enter}, ahk_class KiTTY
sleep, 100

return


F5::
SetKeyDelay, 5, 5

ControlSend, ,^c, ahk_class KiTTY
ControlSend, ,{enter}, ahk_class KiTTY

ControlSend, ,mvn install ahk_class KiTTY
ControlSend, ,{enter}, ahk_class KiTTY

ControlSend, ,cd src/ ahk_class KiTTY
ControlSend, ,{enter}, ahk_class KiTTY
ControlSend, ,java com.hub.carvellwakeman.HubServer 5000 ahk_class KiTTY
ControlSend, ,{enter}, ahk_class KiTTY
sleep, 100

return


F6::
SetKeyDelay, 5, 5


ControlSend, ,^c, ahk_class KiTTY
ControlSend, ,{enter}, ahk_class KiTTY

;ControlSend, ,sudo cp /home/cooper/hub/WEB/* /var/www/html/, ahk_class KiTTY
;ControlSend, ,{enter}, ahk_class KiTTY
;sleep, 500

ControlSend, ,sudo /etc/init.d/apache2 reload, ahk_class KiTTY
ControlSend, ,{enter}, ahk_class KiTTY
