Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & "java -jar 'C:/Users/Zach/Desktop/hub_client\HubDevice.jar' 192.168.1.70 5000 5001 hubdevice picard" & Chr(34), 0
Set WinScriptHost = Nothing