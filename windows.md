Legacy right-click menu<br/><br/>
Open cmd and enter
```
reg.exe add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve
```
to revert back to new one
```
reg.exe delete "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}" /f
```
after using any of them restart explorer Win+R
```
taskkill /f /im explorer.exe & start explorer.exe
```

---
"Admin CMD" option in right click menu<br/><br/>
open regedit with run and go to
```
HKEY_CLASSES_ROOT\DesktopBackground\Shell\
```
Right-click Shell → New → Key, name it "AdminCMD".<br/><br/>
Inside the new key, create another key named "command".<br/><br/>
Set the (Default) value inside "command" to:
```
cmd.exe /k "cd /d %V"
```
Now, right-click Desktop → "Admin CMD" opens CMD as Admin.<br/><br/>
to set Icon for it<br/><br/>
Right-click on the Admin CMD key → New → String Value.<br/><br/>
Name it Icon (case-sensitive).<br/><br/>
Double-click Icon and set its value to:
```
%SystemRoot%\System32\cmd.exe,0
```
or copy paste following code in notepad and save as AdminCMD.reg then right click and choose merge</br></br>
```
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\Directory\Background\shell\AdminCMD]
"Icon"="cmd.exe,0"

[HKEY_CLASSES_ROOT\Directory\Background\shell\AdminCMD\command]
@="powershell -windowstyle hidden -Command \"Start-Process cmd.exe -ArgumentList '/k cd /d %V' -Verb RunAs\""
```
Restart File Explorer (Apply Changes)<br/><br/>
Open Task Manager (Ctrl + Shift + Esc).<br/><br/>
Find Windows Explorer → Restart.<br/><br/>
or use run Win+R
```
taskkill /f /im explorer.exe & start explorer.exe
```

---
to solve blurry properties window in windows 10/11, with 14 inch displays.<br/><br/>
cause is recommended scaling by windows, manual High DPI scaling override takes too much time.<br/><br/>
open cmd as administrator and enter:
```
setx __COMPAT_LAYER HighDpiAware /M
```
to revert
```
setx __COMPAT_LAYER "" /M
```
or
```
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v __COMPAT_LAYER /f
```

---

Get MD5 hash of files inside a folder</br></br>
Open terminal in that folder and run:</br></br>
```
Get-ChildItem -Path "C:\downloads" -Recurse -File | Get-FileHash -Algorithm MD5 | Select-Object Hash | Format-Table -HideTableHeaders | Out-File -Append X:\PATH\md5_checksums.txt
```
Do not set the txt output path inside the folder itself.

---

If wifi keeps disconnecting automatically, Win + (shift+x) > (shift+m) > adapters > disable "Alow the computer to turn off this device to save power"

---

Use --silent-debugger-extension-api to hide started debugging this browser banner.</br>
Exit any running-instance of Chrome (e.g., navigate to chrome://quit).<br/>
Find shortuts and copen properties. Then in target field add --silent-debugger-extension-api after what was already there.<br/>
```"C:\Program Files\Google\Chrome\Application\chrome.exe" --silent-debugger-extension-api```
Usually, one shortcut on desktop, the other is pinned in taskbar, present in ```C:\ProgramData\Microsoft\Windows\Start Menu\Programs```


---
Recover Flash Drive
```
attrib  -H -S F:\\*.* /S /D /L
```
---
fix cottuption
```
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /ScanHealth
DISM /Online /Cleanup-Image /RestoreHealth
sfc /scannow
```
---
بروزرسانی تمام نسخه‌های سیستم‌عامل‌ ویندوز

آموزش تنظیم پراکسی برای دریافت آپدیت‌های ویندوز
1. در ابتدا ابزار Powershell را با دسترسی Administrator در سیستم خود اجرا کنید و متغییر proxy را با استفاده از دستور زیر تنظیم کنید:

```Powershell
$proxy = "win.devneeds.ir:8445"
```
سپس دستورات زیر را خط به خط کپی کرده و در Powershell جایگذاری کنید (می‌توانید با استفاده کلیک راست، جایگذاری را انجام دهید)


```Powershell
netsh winhttp set proxy $proxy

Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyEnable -Value 1
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyServer -Value $proxy
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyOverride -Value ""

Write-Host "Proxy ENABLED"
```
2. روند بروزرسانی را می‌توانید با استفاده از رابط گرافیکی از مسیر settings --> Update & Security شروع کنید
یا با وارد کردن دستور زیر در محیط Powershell، فرآیند بروزرسانی را شروع کنید:


```Powershell
Start-Service wuauserv
usoclient StartScan; usoclient StartDownload; usoclient StartInstall
```
3. غیرفعال سازی پراکسی با تنظیم مقادیر پایین در Powershell انجام می‌شود:
نکته: حتمأ دقت داشته باشید که Powershell را با دسترسی Administrator و خط به خط اجرا کنید:


```Powershell
netsh winhttp reset proxy

Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyEnable -Value 0

Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyServer -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyOverride -ErrorAction SilentlyContinue

Write-Host "Proxy DISABLED (rollback done)"
```
---
**About drivers**</br>
If you want to update drivers too, Windows Update may include some drivers automatically, but command-line control is not very transparent with usoclient.

A better method is PowerShell module PSWindowsUpdate.

**Install module**
```powershell
Install-Module PSWindowsUpdate -Force
```
If prompted about repository trust, answer:

Y
or
A
Import it
```powershell
Import-Module PSWindowsUpdate
```
See available updates
```powershell
Get-WindowsUpdate -MicrosoftUpdate
```
Install all updates, including Microsoft Update items
```powershell
Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -AutoReboot
```
This is the closest thing to “update everything” for:

Windows updates
some Microsoft products
some drivers offered via Microsoft Update
About winget
If by “everything” you also mean apps, then after Windows Update you can run:

```powershell
winget upgrade --all
```
This updates installed applications such as:

browsers
editors
tools
media apps
But not core Windows system updates.

So:

DISM/SFC → repair Windows
Windows Update / PSWindowsUpdate → update Windows + some drivers
winget → update apps
