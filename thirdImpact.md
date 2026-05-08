# first start
check dns at the beginning
```
resolvectl status
ls /etc/netplan/
vi /etc/netplan/xx-config.yaml
netplan apply
```
---
update and upgrade and install
```
sh -c 'apt-get update; apt-get upgrade -y; apt-get dist-upgrade -y; apt-get autoremove -y; apt-get autoclean -y'
apt-get install -y software-properties-common ufw wget curl git socat cron busybox bash-completion locales nano apt-utils
```
---
Disable IPv6
```
sudo vi /etc/default/grub

# Change this line:
GRUB_CMDLINE_LINUX_DEFAULT=""
# To:
GRUB_CMDLINE_LINUX_DEFAULT="ipv6.disable=1"

# Save and update GRUB
sudo update-grub

sudo reboot

# Check IPv6 addresses
ip addr show ens160 | grep inet6
# Should show nothing if disabled

# Or check sysfs
test -f /proc/net/if_inet6 && echo "IPv6 enabled" || echo "IPv6 disabled"

```
---
Timezone
```
sudo localectl set-locale LC_TIME=C.UTF-8
```
or
```
env | egrep '^(LANG|LC_)'
```
```
vi /etc/default/locale
```
```
LANG=C.UTF-8
LC_ALL=C.UTF-8
LC_TIME=C.UTF-8
```
```
timedatectl list-timezones | grep Tehran
sudo timedatectl set-timezone Asia/Tehran
sudo timedatectl set-timezone UTC
```
then reboot

---
NGINX
```
sudo apt update
sudo apt install curl gnupg2 ca-certificates lsb-release ubuntu-keyring
curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor | sudo tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null
```
```
echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
http://nginx.org/packages/ubuntu `lsb_release -cs` nginx" \
| sudo tee /etc/apt/sources.list.d/nginx.list
```
```
echo -e "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" \
| sudo tee /etc/apt/preferences.d/99nginx
```
```
sudo apt update
sudo apt install nginx
```
---
bbr
```
vi /etc/sysctl.conf
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
sysctl -p
```
---
SSH
```
vi /etc/ssh/sshd_config
sudo systemctl daemon-reload && sudo systemctl restart ssh.socket
```
ssh tunnel to proxify terminal of the restricted vps
```
ssh-keygen -t ed25519 -C "sso"
ssh-copy-id -p $sshport root@x.x.x.x
```
Test run check
```
ssh -p $sshport root@x.x.x.x "whoami"
ssh -p $sshport -D 1080 -N -f root@x.x.x.x
ss -tulpn | grep :1080
```
proxify terminal
```
apt install -y proxychains4
cp /etc/proxychains4.conf /etc/proxychains4.conf.backup
vi /etc/proxychains4.conf
```
change `socks4 127.0.0.1 9050` to `socks5 127.0.0.1 1080` <br/>
then run the script you want
```
proxychains4 bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```
for reverse ssh tunnel
```
ssh-keygen -t ed25519 -f ~/.ssh/iran_key -C "foreign_to_iran"
ssh-copy-id -i ~/.ssh/iran_key.pub root@x.x.x.x
```
test run check
```
ssh -i ~/.ssh/iran_key root@x.x.x.x "whoami"
ssh -i ~/.ssh/iran_key -R 1080 -N -f root@x.x.x.x
```
on iran
```
ss -tulpn | grep :1080
```
---
x-ui-pro
```
sudo su -c "$(command -v apt||echo dnf) -y install wget;bash <(wget -qO- raw.githubusercontent.com/GFW4Fun/x-ui-pro/master/x-ui-pro.sh) -panel 1 -xuiver last -cdn off -secure no -country xx"
sudo sh -c "$(wget -qO- https://github.com/v2rayA/v2rayA-installer/raw/main/uninstaller.sh)"
rm -r /usr/local/etc/v2raya && systemctl stop warp-plus && systemctl disable warp-plus && rm -rf /etc/warp-plus/ && systemctl stop tor && systemctl disable tor && apt remove -y tor
crontab -e
30 10 * * * sudo apt update && sudo apt upgrade -y
0 11 * * * /sbin/shutdown -r +5
```
change the credentials with x-ui command menu then set other things in panel itself. port path certs session duration
in xray config disable protection shield and delete routings. correct statistics and log
reality's dest is the socket nginx is listening on put ```/etc/xray.socket``` in corresponding field</br></br>
if you enabled ip limit, use the following command to clear the log time to time
```
echo "" > /usr/local/x-ui/access.log
```
---
changing the html site
```
wget https://github.com/pathumd/2021_personal_site/archive/refs/heads/main.zip && unzip main.zip && rm -r /var/www/html/* && cp -r /root/2021_personal_site-main/. /var/www/html/ && rm main.zip && rm -r 2021_personal_site-main
```
---
Nginx configuration
```
vim /lib/systemd/system/nginx.service
ExecStartPre=/bin/rm -f /etc/xray.socket
vim /etc/nginx/sites-available/
unix:/etc/xray.socket
ln -fs "/etc/nginx/sites-available/" "/etc/nginx/sites-enabled/"
sudo nginx -t
systemctl daemon-reload && sudo systemctl reload nginx && systemctl restart nginx && systemctl status nginx
```
if entered linking command wrongly
```
rm /etc/nginx/sites-enabled/
```
if got any problem with ports check the process listening on them
t and u are tcp and udp, can use -tlpn and -ulpn to check only tcp or udp ports
```
sudo ss -tulpn | grep ":80 "
```
then kill the process with
socket file should be created and deleted by process, remove it manually if it didn't, it shouldn't be present before process begins that's why we added a pre start command to nginx service file earlier
```
sudo fuser -k 80/tcp
sudo fuser -k /etc/xray.socket
sudo rm -f /etc/xray.socket
#or
sudo lsof | grep /etc/xray.socket
sudo kill -9 <PID>
```
---
