# SSLH-EV
SSLH-EV Xray Nginx


<img width="847" alt="sslhev" src="https://github.com/user-attachments/assets/12b3d870-c980-463e-b7e8-2c9bce330d84">
<br />



**هدف:**<br /> 
میخواهیم در سرور فقط پورت ۴۴۳ و ۸۰ باز باشند. میخواهیم روی پورت ۴۴۳ سایت واقعی، پنل، اینباند ریلیتی و سی دی ان و پروکسی تلگرام و پروکسی socks5 و ssh داشته باشیم یا حداقل همیشه امکان اجراشون روی ۴۴۳ رو داشته باشیم به طوری که بقیه سرویس ها به مشکل نخورند.

به شخصه فکر میکنم ssh روی پورت ۴۴۳ نیازی نیست.بعید میدونم روزی برسه که ssh به خارج رو ببندند.<br />


پورت ۴۴۳ توسط SSLH اشغال میشه و بقیه برنامه ها باید از اون ترافیک خودشون رو تحویل بگیرن، که یعنی ایپی درخواست دهنده به دست سرویس نمیرسه مگر اینکه ویکی SSLH رو بخوانید و روش Transparent proxy رو اجرا کنید.


اینباند ریلیتی روی ۴۴۴۳ خواهد بود، انجینکس روی سوکت دامنه، پروکسی تلگرام روی ۵۴۴۳ و ssh روی ۶۴۴۳.


مثل دفعه قبل دامنه ریلیتی باید تیک خاموش باشه. باید براش با اسکریپت gfw4fun هم انجینکس رو تنظیم کنیم هم گواهی امنیتی بگیریم.



این دفعه از سوکت دامنه استفاده خواهیم کرد، احتمال داره به خطا بر بخورید که بخاطر یا دسترسی نادرست دادن هست یا به ترتیب نادرست اجرا کردنش. نحوه کارکرد sslh به صورت زیر هست:<br />
اتصال ریلیتی معتبر<br />
[ client <--> sslh:443 <--> xray:4443 | check if it is authentic REALITY request ]<br />

انجینکس ترافیکی که از نظر هسته ریلیتی معتبر نیست رو میگیره و بر اساس url مسیریابی خودش رو روی اون انجام میده، یا سایت رو میاره یا پنل رو یا اینباند سی دی ان تشخیص میده رمزنگاری رو برمیداره برش میگردونه دست هسته.<br />
[ client <--> sslh:443 <--> xray:4443 <--> nginx:uds <--> xray:inbound's_local_port ]<br />

اتصال به پنل توسط انجینکس<br />
[ client <--> sslh:443 <--> xray:4443 <--> nginx:uds <--> x-ui:panel_port ]<br />

و در مورد MTProxy قبل فرستادن درخواست‌ها به هسته ایکس‌ری قرار میگیره.<br />
[ client <--> sslh:443 | check if sni == zula.ir <--> mtproxy:5443 ]<br />


تاکیدات قبلی، اسپایدرایکس رو خالی نگذارید، شورت ایدی رو خالی نگذارید هر کدوم رو اگر میتونید چندتا تعریف کنید و با , از هم جداشون کنید و به هرکاربر ترکیب متفاوتی بدید.<br />
در قسمت اسپایدر هر رشته ای از اعداد و حروف که میخواهید قرار بدید، راجب اسپایدرایکس توضیحاتی داده نشده اما وقتی در ویکی گفته به هر کلاینت متفاوت بدید خب ما همون رو اجرا میکنیم، تا جایی گه ممکن باشه. <br />


ادرس اسکریپت https://github.com/GFW4Fun/x-ui-pro<br />


نصب کننده پنل تنظیم انجینکس و گرفتن گواهی برای سی دی ان. <br />


پنل رو پورتش رو یادداشت کنید یا با دستور x-ui و وارد کردن ۱۰ مشخصات رو بگیرید، لینکی که داده رو https هست تبدیل به http کنید و جلوی دامنه پورت پنل رو بگذارید، قبلش دیوار اتش رو باید خاموش کرده باشید.<br />




**حتما در هنگام ساخت پروتوکل اینباند ریلیتی رو که روی ویلس گذاشتید با پورت ۴۴۳ برید پایین امنیت بذارید روی ریلیتی بعد روی clients کلیک کنید و flow  رو روی xtls-rprx-vision تنظیم کنید.**<br />


عکس زیر دو کانفیگ پوشانده شده ریلیتی سلف استیل هستند و بقیه روی سی دی ان.



![Screenshot 2024-11-03 083003](https://github.com/user-attachments/assets/820e9639-91df-4626-b780-7cddc20d658e)


از هر سی دی انی که وبسوکت پشتیبانی کنه یا split رو قبول بکنه میتونید استفاده کنید.<br />
مشکل این روش محدود شدن شما به یک اینباند ریلیتی هست.<br />


![Screenshot 2024-11-03 084400](https://github.com/user-attachments/assets/4b8cde2e-7276-4778-bca4-c6ada979c2eb)


# راه اندازی

0: خاموش کردن دیوار اتش
```
ufw disable
```

نصب پنل 
```
sudo su -c "$(command -v apt||echo dnf) -y install wget;bash <(wget -qO- raw.githubusercontent.com/GFW4Fun/x-ui-pro/master/x-ui-pro.sh) -panel 1 -cdn off"
```


نصب سایت فیک **به هیچ عنوان رد نشود**
```
bash <(wget -qO- raw.githubusercontent.com/GFW4Fun/x-ui-pro/master/x-ui-pro.sh) -RandomTemplate yes
```


تنظیم کانفیگ انجینکس
```
sudo nano /etc/nginx/sites-available/yourdomain.com
```
<br />

برای هر دامنه مجزا باید اسکریپت اجرا بشه.برای دامنه های سی دی ان، ابتدا تیک خاموش باشه، بعد که اسکریپت گواهی دامنه رو گرفت و تنظیم کرد و تغییرات قبلی رو روی فایل اون دامنه اجرا کردید تیکش رو روشن کنید.<br />
در این جا فقط و فقط پورت 443 رو به ```unix:/etc/xray.socket``` تغییر بدید. چپ چین راست چینش شاید بهم بریزد عکس رو توجه کنید. دقت کنید دو خط دارای ۴۴۳ هستن، اونی که بین دو خط ۸۰ هست رو پاک کنید و فقط اخرین خط ۴۴۳ رو تغییر بدید.


![Screenshot 2024-11-03 091246](https://github.com/user-attachments/assets/292dc711-22a8-470f-8012-6aa05c1c55a9)


To this:


![image](https://github.com/user-attachments/assets/d052a7a4-37ab-4bcf-abe9-29a22056941e)



تست انجینکس
```
ln -fs "/etc/nginx/sites-available/yourdomain.com" "/etc/nginx/sites-enabled/"
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart nginx
```


ارور برخورد کردید این دستورات زیر رو اجرا کنید سپس دستورات قبلی رو اجرا کنید. شاید بعدها به ارور address already in use بخورید که راه حلش به صورت بلوک بعدی هست.<br />

```
sudo fuser -k 80/tcp
sudo fuser -k 443/tcp
sudo fuser -k 8443/tcp
sudo fuser -k /etc/xray.socket
sudo rm -f /etc/xray.socket
sudo systemctl start nginx
```

دستور استاپ زیر رو که زدید ۱۵ ۲۰ ثانیه صبر کنید.~اگر حال و حوصله این صبر کردن ها رو نداشتید برید سرویس فایل انجینکس و KillMode=control-group رو به انتهای بلوک اجرا اضافه کنید. البته استاندارد نیست این کار.~<br />

```
sudo systemctl stop nginx
sudo lsof | grep /etc/xray.socket
sudo kill -9 <PID>
sudo rm -f /etc/xray.socket
sudo systemctl start nginx
```

برای رفع این مشکل، در فایل سرویس انجینکس دستور حذف فایل سوکت رو قبل از اجرای خود انجینکس قرار میدیم.

```
vim /lib/systemd/system/nginx.service
```
بعد خط PIDFile ، یک خط خالی درست کنید و این خط زیر رو اونجا قرار بدید
```
ExecStartPre=/bin/rm -f /etc/xray.socket
```
بعد دستورات زیر رو به ترتیب بزنید
```
systemctl daemon-reload
sudo systemctl reload nginx
systemctl restart nginx
```


# X-UI

ساخت اینباند ریلیتی
**تاکیدات قبلی، اسپایدرایکس رو خالی نگذارید، شورت ایدی رو خالی نگذارید هر کدوم رو اگر میتونید چندتا تعریف کنید(شورت ایدی رو خود پنل ثنایی میده و هر کلاینت هم فکر کنم رندوم یکی رو میذاره براش) و با , از هم جداشون کنید و به هرکاربر ترکیب متفاوتی از شورت ایدی و اسپایدرایکس بدید.<br />
در قسمت اسپایدر هر رشته ای از اعداد و حروف که میخواهید قرار بدید، من ed=2560? هم قرار دادم به مشکلی نخورد فکر نمیکنم بدرد این جا بخوره چون کاربرد اسپایدرایکس گفتن چیز دیگری غیر از path در ترنسپورت های دیگه هست.یعنی کاراکترهای این حالتی هم میتونید داخل هر اسپایدرایکس بگذارید.<br />**
**حتما در هنگام ساخت پروتوکل اینباند ریلیتی رو که روی ویلس گذاشتید با پورت ۴۴۴۳ برید پایین امنیت بذارید روی ریلیتی، بعد روی clients کلیک کنید و flow  رو روی xtls-rprx-vision تنظیم کنید. برای کلاینت های جدید پنجره ساختشون خودش فیلدش رو داره اونی که اخرش udp443 هست را انتخاب نکنید!**<br />
اکسترنال پروکسی رو تنظیم کنید دامنه ریلیتی‌تون لاکن پورت 443 باشه.


![image](https://github.com/user-attachments/assets/ae17859a-b43f-4507-a309-f06107c58fb1)
![image](https://github.com/user-attachments/assets/d56fe5b4-e872-4a85-b149-3cc0cdccab4e)
![image](https://github.com/user-attachments/assets/5e726e58-3d70-4f8f-affe-b19ddeda0fa2)



ساخت اینباند سی دی ان<br />


از gfw4fun میباشد:<br />


![image](https://github.com/user-attachments/assets/4db3a6c3-62a1-4abe-bda6-171cf0ad2bc7)
![image](https://github.com/user-attachments/assets/e9ab2e33-71b1-45f0-9b77-0469cd69d81f)
![image](https://github.com/user-attachments/assets/7f914763-564d-464f-a10d-c7bdde12e5cb)



# SSLH-EV

قسمت سخت ماجرا، ممکن هست به یک سری ارور بربخورید چون قرار هست کامپایل انجام بشه.دستورات زیر رو به ترتیب اجرا کنید، wget unzip هم باید نصب باشن.<br />

```
sudo apt update
sudo apt install build-essential libconfig-dev libwrap0-dev libsystemd-dev libcap-dev libbsd-dev libpcre2-dev libev-dev libio-socket-inet6-perl
```

```
wget https://github.com/yrutschle/sslh/archive/refs/heads/master.zip
unzip master.zip
cd sslh-master
./configure
nano Makefile
```

در این فایل باید خط ۱۰ تا ۱۶ رو مقابل = بدون هیچ فاصله ای عدد 1 رو قرار بدین. خط ۹ سنیتایزر و ۱۷ تست، دستشون نزنید در اینجا به کار ما نمیان. این تصویر زیر فایل اصلاح شده من هست، برای شما مقابل بعضی هاش عدد 1 نخواهد بود. به بقیه فایل کاری نداریم و ذخیره کنید و خارج بشید.

![image](https://github.com/user-attachments/assets/8fd194db-f26a-4f3a-9915-6ef3537a2845)

پس از تغییر makefile:
```
make
sudo make install
sudo rm /usr/sbin/sslh
sudo cp sslh-ev /usr/sbin/sslh
```
حالا باید کانفیگش رو بسازیم:

```
nano /etc/sslh.cfg
```


بلوک زیر رو با توجه به دامنه خودتون و پورت های خودتون میتونید ویرایش کنید:
```
timeout: 2;
pidfile: "/run/sslh/sslh.pid";
# Listen on public port 443 for incoming connections
listen:
(
    { host: "0.0.0.0"; port: "443"; }
);

# Protocol definitions
protocols:
(

    # Forward SSH traffic to the local SSH server on port 22
    { name: "ssh"; host: "127.0.0.1"; port: "22"; keepalive: true; fork: true; tfo_ok: true },

    #MTProto Proxy
    { name: "tls"; host: "127.0.0.1"; port: "5443"; sni_hostnames: [ "mtprotoproxyfaketlsdomain.com" ]; keepalive: true; tfo_ok: true },

    # Forward HTTPS (TLS) traffic to Xray on localhost:4443
    { name: "tls"; host: "127.0.0.1"; port: "4443"; keepalive: true; tfo_ok: true },

    # Forward anything else to 4443 xray
    { name: "anyprot"; host: "127.0.0.1"; port: "4443"; keepalive: true; tfo_ok: true }
);
```
در این کانفیگ، اول هرچی اس اس اچ بیاد میفرسته دست برنامه sshd بعد هرچی اتصال تی ال اس بیاد که اس ان ای با اون دامنه‌ای که شما برای پروکسی فیک تی ال اس تلگرام انتخاب کرده باشی، برابر باشه میفرستش دست پروکسی تلگرام روی سرور.<br />
بقیه تی ال اس ها بدون چک شدن میرن دست هسته ایکس‌ری. بعد اینها خودشون شامل نخست درخواست های معتبر ریلیتی، دوم درخواست های غیرریلیتی مثل باز کردن دامنه یا پنل یا اینباندهای سی دی ان میشن.<br />
در نهایت هرچی تی ال اس نبود رو و پروتوکل دیگه ای باشه باز میفرسته دست انجینکس، حالا شما میتونید https://github.com/yrutschle/sslh/blob/9243a6e36964ba7443f62be05abd19303109e95d/test.cfg رو یک نگاه کنید یا خود مخزن رو بررسی کنید و به دلخواه همون پرتوکل هایی که در عکس گذاشتم رو شخصی سازی کنید، مثلا خود من چون mtproxy روی تلگرام نمیتونه به تماس شخصی و گروه وصل بشه روی ۴۴۳ یک socks5 هم میخوام بالا بیارم، که جایگاهش بعد تعریف ssh در بخش protocols هست.<br />


حالا ساخت یوزر sslh و دایرکتوری کاری و دادن دسترسی به یوزرش:
```
sudo useradd -r -s /bin/false sslh
sudo mkdir -p /run/sslh
sudo chown sslh:sslh /run/sslh

```

Edit the service file

```
sudo nano /usr/lib/systemd/system/sslh.service
```
بلوک زیر رو کپی کنید بذارید داخل فایل ذخیره کنید بیاید بیرون.
```
[Unit]
Description=SSL/SSH multiplexer
After=network.target
Documentation=man:sslh(8)

[Service]
User=sslh
RuntimeDirectory=sslh
ExecStart=/usr/sbin/sslh --foreground -n --config /etc/sslh.cfg
PIDFile=/run/sslh/sslh.pid
KillMode=control-group
#Hardening
PrivateTmp=true
CapabilityBoundingSet=CAP_SETGID CAP_SETUID CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
SecureBits=noroot-locked
ProtectSystem=strict
ProtectHome=true
ProtectKernelModules=true
ProtectKernelTunables=true
ProtectControlGroups=true
MountFlags=private
NoNewPrivileges=true
PrivateDevices=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
MemoryDenyWriteExecute=true
DynamicUser=true

[Install]
WantedBy=multi-user.target

```

توضیح سوییچ ها: foreground برای اجرا لازم هست چرا که اگر نباشه برنامه از systemd جدا میشه و ران نمیشه. -n برای این هست که ایپی رو به دامنه تبدیل نکنه چرا که باعث کاهش سرعت و افزایش تاخیر میشه. حالا راه انداختن سرویسش به صورت زیر هست:
```
sudo systemctl daemon-reload
sudo systemctl start sslh
sudo systemctl status sslh
```
وضعیت که بگیرید اگر خطا وجود داشت باید ببینید کجا اشتباه کانفیگ کردید یا در کامپایل جایی اشتباه شده. شاید هم دسترسی مورد نیاز یک دایرکتوری خاصی داده نشده. این راهنما رو من بعد از خطاهای بسیار دارم مینویسم تا حد امکان همشون برطرف شده. در پایان اگر مشکلی نبود فعالش کنید که با ریبوت بالا بیاد.
```
sudo systemctl enable sslh
```

با دستور زیر میتونید لاگ سرویس رو وارد یک فایل تکست کنید بریزید روی سیستم و بازش کنید ببینید درخواست ها از کدام ایپی ها بودن و جایی برنامه خطا داده یا نه، کانکشن تایم اوت ها خطا نیستند. و با دستور زیرش میتونید لاگ برای چندساعت قبل رو بگیرید. x رو برداید ساعتی که میخواهید بگذارید
```
journalctl -u sslh.service > sslh-mm-dd-yy.txt
journalctl -u sslh --since "x hour ago" > sslh-mm-dd-yy.txt
```
# پروکسی تلگرام MTProxy
اول نرم افزارهای مورد نیاز
```
apt install git curl build-essential libssl-dev zlib1g-dev
```

بعد دانلود مخزن:
```
git clone https://github.com/TelegramMessenger/MTProxy
cd MTProxy
```
با اجرای configure فایل Makefile رو میسازیم
```
./configure
```
باید makefile رو ویرایش کنیم:
```
vim Makefile
```
خط ۱۵ و ۱۶ ، هر دو رو کامل پاک کنید، و بلوک زیر عکس رو جایگذاری کنید:



![Screenshot 2024-11-14 191004](https://github.com/user-attachments/assets/dc29d70e-9bab-4e67-be13-7536ecc55f1c)



```
CFLAGS = $(ARCH) -O3 -std=gnu11 -Wall -mpclmul -march=core2 -mfpmath=sse -mssse3 -fno-strict-aliasing -fno-strict-overflow -fwrapv -fcommon -DAES=1 -DCOMMIT=\"${COMMIT}\" -D_GNU_SOURCE=1 -D_FILE_OFFSET_BITS=64
LDFLAGS = $(ARCH) -ggdb -rdynamic -lm -lrt -lcrypto -lz -lpthread -lcrypto -fcommon
```



بعد فایل زیر رو باید ویرایش کنیم:


```
vim /root/MTProxy/common/pid.c
```
برید خط ۴۲، برای من فایل ویرایش شده، از گیتهابش تصویر نمونه دست نخورده رو میگذارم:


![Screenshot 2024-11-14 192344](https://github.com/user-attachments/assets/43fe9135-f041-45b2-89fa-e0187259ccf2)




دو خط ۴۲ و ۴۳ رو پاک کنید، جاشون خط زیر رو قرار بدید:
```
PID.pid = (unsigned short)p;
```
به شکل زیر باید بشه:


![image](https://github.com/user-attachments/assets/fd379181-2be5-4b06-87e1-9a51e5a6528a)



حالا باید برنامه رو کامپایل کرده و بسازیم، دقت کنید از دایرکتوری MTProxy خارج نشده باشید
```
make
```
اگر خطا داد، کپیش کنید و دستور زیر رو بزنید و بگردید دنبال حل خطاش، اگر خطا نداد این دستور رو نادیده بگیرید.
```
make clean
```
در ادامه برید به این دایرکتوری
```
cd objs/bin
```
سکرت اتصال به سرور خود تلگرام رو از تلگرام میگیرید :
```
curl -s https://core.telegram.org/getProxySecret -o proxy-secret
```
بعد کانفیگ سرور از تلگرام رو میگیریم:
```
curl -s https://core.telegram.org/getProxyConfig -o proxy-multi.conf
```
حالا یک سکرت برای پروکسیمون، ذخیرش کنید
```
head -c 16 /dev/urandom | xxd -ps
```


حالا یا از دامنه خودتون که برای ریلیتی استفاده کردید استفاده کنید(برای من کار کرد اما یک خطا داد گفت فلان اپشن فعال نیست اتصال کامل شبیه سازی نمیشه) یا اس ان ای اسکنر هاشمی SNI Scanner Hawshemi رو اجرا کنید، ایپی سرور خودتون رو بزنید، میاد سایت هایی که روی سابنت شما هستن رو بهتون میده، بررسی کنید کدومش براتون کار میکنه. به این صورت تست کنید:


```
./mtproto-proxy -u root -p 8888 -H 5443 -S secretyougenerated --aes-pwd proxy-secret proxy-multi.conf -D domain.com --http-stats
```
بعد که دامنه پیدا کردید، دستی اجرا کردید بهش وصل شدید و تلگرام وصل شد و کار کرد، فایل سرویس میسازید:
```
nano /etc/systemd/system/MTProxy.service
```
بلوک زیر رو کپی و جایگذاری کنید، پارامترهای سکرت و دامنه رو قبلش در نوتپد با مال خودتون عوض کنید
```
[Unit]
Description=MTProxy
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/MTProxy/objs/bin
ExecStart=/root/MTProxy/objs/bin/mtproto-proxy -u root -p 8888 -H 5443 -S secretyougenerated --aes-pwd proxy-secret proxy-multi.conf -D domain.com --http-stats
Restart=on-failure
KillMode=control-group

[Install]
WantedBy=multi-user.target
```
سپس
```
systemctl daemon-reload
systemctl restart MTProxy.service
systemctl status MTProxy.service
```
خطا دیدید باید حلش کنید، و اگر خطایی در وضعیت نبود سرویس رو فعال کنید.
```
systemctl enable MTProxy.service
```

باید از فیک تی ال اس استفاده بکنیم. اون دامنه ای که یافتید یا دامنه خودتون بود، برید به این سایت https://www.rapidtables.com/convert/number/ascii-to-hex.html ، دامنه رو وارد کنید و کانورت کنید و کپیش کنید.<br /> حالا اون کد هگزادسیمال رو نگه دارید، برید توی تلگرام، توی hostname دامنه ریلیتی رو بزنید، بعد پورت ۴۴۳ بعد در سکرت همون سکرت خودتون رو بگذارید، اما! اولش ee اضافه کنید، اخرش هم برید کد هگزادسیمال رو بگذارید، مراقب باشید اشتباهی نکنید یک حرفی پاک بشه. کار پروکسی تلگرام تمام هست. اما بدونید ۲ تا ۱۵ درصد از سی پی یو رو گاهی مصرف میکنه علتش این هست یک پروکسی ساده مثل این اماده هست اتصال تعداد بسیار زیادی کاربر رو تامین کنه.<br />


مثلا google.com به صورت هگزادسیمال میشود 676F6F676C652E636F6D و سکرت شما 77f827f80a2ed3db50ac892007be0bfd هست، در سکرت داخل برنامه تلگرام باید اینطور قرار بدید:<br />


ee77f827f80a2ed3db50ac892007be0bfd676F6F676C652E636F6D

<img width="750" alt="mtproxy" src="https://github.com/user-attachments/assets/2c65f726-7808-45e9-a32a-25e6248593a5">







# دیوار اتش
۲۷۸۹ پورت اس اس اچ من هست، شما با پورت خودتون عوض کنید. پورت اس اس اچ رو تا زمانی که میشه باز بگذارید تا پایداری این راه اندازی کامل سنجیده بشه.
```
ufw status
ufw reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 80,443,2789/tcp
ufw allow 80,443,2789/udp
```
تغییر پورت اس اس اچ:
```
vi /etc/ssh/sshd_config
```
```
#Port 22
```
```
systemctl reload sshd
```
**از زمان اوبونتو ۲۴**


https://ubuntuhandbook.org/index.php/2024/04/install-ssh-ubuntu-2404/
edit sshd_config but for changes to take effect:
```
sudo systemctl daemon-reload
```
```
sudo systemctl restart ssh.socket
```
To revert to previous mode:


twinsen said: Long story short - for all those who do not like this change:
```
systemctl disable --now ssh.socket
systemctl enable --now ssh.service
```


UFW at last
```
ufw enable
```



