# Proxy Wars
Endless battles between GFW and freedom brigade


---
**Step 0-1 Change DNS to cloudflare and google**

```
sudo apt install resolvconf

sudo systemctl start resolvconf.service

sudo systemctl enable resolvconf.service

sudo systemctl status resolvconf.service
```
```
vi /etc/resolvconf/resolv.conf.d/head

nameserver 1.1.1.1
nameserver 8.8.8.8
```
```
sudo resolvconf --enable-updates

sudo resolvconf -u

sudo systemctl restart resolvconf.service

sudo systemctl restart systemd-resolved.service

resolvectl status
```
**Step 0-2 Change DNS to cloudflare and google**

```
mkdir /etc/systemd/resolved.conf.d/

vi /etc/systemd/resolved.conf.d/dns_servers.conf
```
```
[Resolve]
DNS=1.1.1.1 8.8.8.8
```
```
systemctl restart systemd-resolved

resolvectl status

systemd-resolve --status
```

---

**Step 1 Optimizing**
```
sh -c 'apt-get update; apt-get upgrade -y; apt-get dist-upgrade -y; apt-get autoremove -y; apt-get autoclean -y'
```
```
apt-get install -y software-properties-common ufw wget curl git socat cron busybox bash-completion locales nano apt-utils
```

---

**Step 2 BBR TCP Congestion Control**
```
vi /etc/sysctl.conf
```
Add lines below to the end of the file.

```
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
```
```
sysctl -p
```
output:
```
sysctl net.ipv4.tcp_congestion_control
```
---

**Step 3 Change SSH Port**
```
vi /etc/ssh/sshd_config
```
```
#Port 22
```
```
systemctl reload sshd
systemctl restart sshd
```
Since ubuntu 24.04:
https://ubuntuhandbook.org/index.php/2024/04/install-ssh-ubuntu-2404/
edit sshd_config but for changes to take effect:
```
sudo systemctl daemon-reload
```
```
sudo systemctl restart ssh.socket
```
To revert:
```
systemctl disable --now ssh.socket
rm -f /etc/systemd/system/ssh.service.d/00-socket.conf
rm -f /etc/systemd/system/ssh.socket.d/addresses.conf
systemctl daemon-reload
systemctl enable --now ssh.service
```
twinsen: Long story short - for all those who do not like this change:
```
systemctl disable --now ssh.socket
systemctl enable --now ssh.service
```
---

**Step 4 x-ui**
```
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```
---

**Step 5 Warp Interface**
```
wget -N https://gitlab.com/fscarmen/warp/-/raw/main/menu.sh && bash menu.sh
```
warp i
ipv4 
de nl

 warp h (help)
 
 warp n (Get the WARP IP)
 
 warp o (Turn off WARP temporarily)
 
 warp u (Turn off and uninstall WARP interface and Socks5 Linux Client)
 
 warp b (Upgrade kernel, turn on BBR, change Linux system)
 
 warp a (Change account to Free, WARP+ or Teams)
 
 warp p (Getting WARP+ quota by scripts)
 
 warp v (Sync the latest version)
 
 warp r (Connect/Disconnect WARP Linux Client)
 
 warp 4/6 (Add WARP IPv4/IPv6 interface)
 
 warp d (Add WARP dualstack interface IPv4 + IPv6)
 
 warp c (Install WARP Linux Client and set to proxy mode)
 
 warp l (Install WARP Linux Client and set to WARP mode)
 
 warp i (Change the WARP IP to support Netflix)
 
 warp e (Install Iptables + dnsmasq + ipset solution)
 
 warp w (Install WireProxy solution)
 
 warp y (Connect/Disconnect WireProxy socks5)
 
 warp k (Switch between kernel and wireguard-go-reserved)
 
 warp g (Switch between warp global and non-global)
 
 warp s 4/6/d (Set stack proiority: IPv4 / IPv6 / VPS default)

 **Warp Interface**
```
{
      "tag": "warp",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIPv4"
      },
      "streamSettings": {
        "sockopt": {
          "interface": "warp",
          "tcpFastOpen": true,
          "tcpNoDelay": true,
          "tcpKeepAliveIdle": 100
        }
      }
    }
```
list interfaces
```
ip link show
```
or
```
ifconfig -a
```
warp interface
normal warp
```
# first run
wget -N https://gitlab.com/fscarmen/warp/-/raw/main/menu.sh && bash menu.sh
# menu
warp
```
on ubuntu 24 warp can not get ip so we use warp-go and choose ```WARP Non-global dualstack ipv4 priority``` option
```
# first run
wget -N https://gitlab.com/fscarmen/warp/-/raw/main/warp-go.sh && bash warp-go.sh
# menu
warp-go
```
in panel go to advanced add this in outbounds section
```
    {
      "tag": "warp",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIPv4"
      },
      "streamSettings": {
        "sockopt": {
          "interface": "WARP",
          "tcpFastOpen": true
        }
      }
    }
```
and add routing rule network tcp,udp outbound warp or source port 0-65535 outbound warp

---

**Step 6 Clear History**
```
history -c
```
```
history -w
```
delete a specific line:
```
history -d <line-number>
```
delete multiple lines:
```
history -d <first-line-number>-<last-line-number>
```
edit history file:
```
vi ~/.bash_history
```
delete long wrong terminal prompt:
```
ctrl+w
```
---

**Step 10 Telegram MTProto proxy**
```
https://telegra.ph/How-Run-MTProto-Proxy-Telegram-with-iSegaro-05-18
```

Certificate with certbot
-
```
sudo apt install software-properties-common
```
```
sudo add-apt-repository ppa:certbot/certbot
```
```
sudo apt-get install certbot -y
```
```
sudo certbot certonly --standalone --preferred-challenges http --agree-tos --email saleh.mumtaz@proton.me -d 
```
```
certbot certonly --force-renew -d 
```
https://docs.digitalocean.com/support/how-can-i-renew-lets-encrypt-certificates/

---

UFW
-
see all currently used ports
```
sudo lsof -i -P -n | grep LISTEN | grep "*"
```
**Default Modes**
```
ufw default deny incoming
```
```
ufw default allow outgoing
```
```
ufw allow 1605,8443,443,80,2053,2083,2087,2096/tcp
```
```
ufw allow 1605,8443,443,80,2053,2083,2087,2096/udp
```
```
ufw show added
```
```
ufw enable
```
```
ufw status
```
```
sudo ufw --force disable
```
```
sudo ufw --force reset
```
