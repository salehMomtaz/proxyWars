
### [中文](README.md) | [Русский](https://github.com/XTLS/Xray-core/discussions/4113#discussioncomment-11468947)

# XHTTP: Beyond REALITY

Development summary: In mid-2024, @mmmray, @ll11l1lIllIl1lll and others developed SplitHTTP based on the principle and implementation details of “packetized uplink, streaming downlink” described by @RPRX. **For the first time, it penetrated most HTTP-capable middleboxes without sacrificing downlink efficiency, and for the first time enabled large-scale QUIC H3 through CDN, opening a brand-new era.** Browser forwarding (Browser Dialer) support, header padding to reduce fingerprints, XMUX for multiplexing control, and unlocking REALITY were added subsequently. Later @RPRX took over development, **realised true uplink/downlink separation and renamed it to XHTTP. For example, uplink can be IPv6 CDN H3 and downlink IPv4 REALITY H2 (source IPs can even be different), ~~and now a new era has begun again~~**. Next, the stream-up mode that does not sacrifice uplink efficiency was developed, the extra scheme for sharing all detail configuration, and default gRPC header camouflage for stream-up, **achieving H2 streaming uplink through CDN and replacing the traditional gRPC transport – if we had known this was possible, we might never have created that transport.** Finally, the HTTP transport layer was merged into XHTTP as stream-one mode, which also gained features like header padding, XMUX and gRPC header camouflage. **Now we have the complete XHTTP: all kinds of middlebox penetration, uplink/downlink separation, smooth XMUX – XHTTP’s era of handling any scenario officially arrives.**

Originally this was a cut-down document, but it accidentally became an article. This article is designed to help you thoroughly understand the principles and design of XHTTP so you can use it more effectively.

## If you want to donate to the Xray project or collect NFTs, related information is at the end of the article. Thank you for your support!

## Quick Start Guide

Don’t be put off by the number of XHTTP parameters – they all have sensible default values. If you just want to use XHTTP, follow these six steps:

1. Whether using TLS or REALITY, **generally you only need to set `path` in the XHTTP configuration; leave everything else empty.**
2. If the server supports QUIC H3, **set the client `alpn` to "h3" to use QUIC.**
3. When using CDN preferred IPs, set the client `address` to the IP, and `serverName` (SNI) to the domain name.
4. If you cannot connect through Cloudflare, **enable gRPC support in the CF dashboard.**
5. If you cannot penetrate Nginx, **change Nginx’s `proxy_pass` to `grpc_pass`.**
6. If you cannot penetrate other CDNs or reverse proxy software, it is recommended to set `mode` to "packet-up" – the most compatible option.

**XHTTP has multiplexing by default. Latency is lower than Vision, but multi-threaded speed tests may not perform as well unless you set `"maxConcurrency": 1` before testing (see the XMUX section).**

Cloudflare will terminate an HTTP connection that has no real data for 100 seconds in the downlink direction. Long-lived proxy connections need application-level keep-alive – for example, SSH requires setting `ClientAliveInterval` in sshd.

This article can be used as an enhanced manual. It covers essentially everything you want to know about XHTTP, with an explanation for every parameter. **At the end there is a configuration example covering all parameters, with each parameter’s usage scenario labelled. If you are unsure about any parameter, search for its name in the text to find a detailed explanation.**

## Two Core Principles

Just as [REALITY](https://github.com/XTLS/REALITY) can disguise itself as someone else’s website, **the fundamental logic of anti-censorship is to increase the “collateral damage” when the censor executes a block, so that the censor dares not block rashly.** I believed in TLS and obfuscating the timing and length characteristics of traffic over TLS for the same reason. Years of experience tell us that the GFW will not permanently block an entire IP of a large CDN because that would affect too many regular websites. **Therefore, for XHTTP, our initial goal was to hide it behind various CDNs.** However, to protect origin servers from attacks, CDNs usually buffer an entire HTTP request before forwarding it to the origin – except for specially supported transports like WS and gRPC. Many HTTP middleboxes also behave this way by default. Based on this, Tor’s Meek protocol wraps round-trip traffic into individual HTTP requests to penetrate these middleboxes, but the speed is painfully slow because it does not use XHTTP’s “streaming downlink”. **What is “streaming downlink”? Imagine you are downloading a large file from a website. The CDN misses the cache and fetches it from the origin. Obviously, it won’t buffer the entire file at the CDN before sending it to you, like it would for an uplink. Instead, whatever data the origin sends is forwarded to you in real time. This is the basis of XHTTP’s streaming downlink, which ensures that the most important downlink speed can be maxed out.** As for the uplink, for compatibility reasons XHTTP first implemented “packetized uplink”, i.e., packaging uplink traffic into individual POST requests. Its efficiency is obviously reduced, but for typical proxy usage uplink traffic is minimal. **Later I added “streaming uplink”, and we discovered that with gRPC header camouflage it can even do H2 streaming uplink through Cloudflare. After several rounds of optimisation, packetized uplink speed is now almost on par with streaming uplink.**

By the way, let’s touch on the recurring question of whether using CDN for proxying constitutes “abuse”: obviously a CDN that does not support streaming uplink is not intended for proxy services. However, to fight the GFW, it is reasonable and necessary to continually explore, develop and exploit as many new paths as possible – we have no choice, and increasing the censor’s “collateral damage” requires us to blend into “normal” services, which is unavoidable. **Take the simplest example: if one day an IP whitelist appears and CDN IPs are on it, will you use them or not? Some rules of the real world do not apply to anti-censorship. This is such a simple truth, yet some people always fail to grasp it.** If you still don’t get it, then transports like WebSocket now exist only for the purpose of putting traffic behind a CDN. As a developer you could delete it; as a user you could suggest its deletion. Take real action yourself to prove that “CDN abuse” is not just another excuse for the daily boring behaviour of attacking Xray out of some unhealthy psychology – ~~meanwhile your body is honest~~, and it’s not hard to see that the hypocritical nature of some people is already fully exposed.

## PACKET-UP

**This section has a lot of technical details. Non-developers may read only the bold parts.**

**For XHTTP’s most compatible “packetized uplink, streaming downlink”, i.e., packet-up mode, we designed it as follows:**

1. **The client `POST`s to `/yourpath/sameUUID/seq` to send uplink data:**
   - UUID is randomly generated. The same UUID will be used when starting the downlink later, so that the server can correlate them. If the server fails to correlate within 30 seconds, it will terminate the session.
   - `seq` starts at 0. The next POST body must be sent only after the previous one has been sent (but there is no need to wait for the response).
   - Multiple POSTs may arrive out of order at the server with low probability. The server reassembles them in `seq` order, caching at most 30 by default; if the limit is exceeded, the connection is dropped.
   - Note that UUID and `seq` are designed to be in the path, not in the query string, to avoid strange problems.

2. **The client starts the downlink with `GET /yourpath/sameUUID`. The server response headers include:**
   - `X-Accel-Buffering: no` to instruct middleboxes to disable buffering.
   - `Cache-Control: no-store` to tell middleboxes not to cache.
   - `Content-Type: text/event-stream` to masquerade as server-sent events (better compatibility; you can set `noSSEHeader` to turn this off).
   - For HTTP/1.1, `Transfer-Encoding: chunked` is also required; H2/H3 do not need it.

3. To avoid cross-origin restrictions when using Browser Dialer ([Browser Dialer](https://xtls.github.io/config/features/browser_dialer.html)), the server includes in all responses to GET and POST:
   - `Access-Control-Allow-Origin: *`
   - `Access-Control-Allow-Methods: GET, POST`

4. **To address the fixed-length fingerprint of HTTP request and response headers:**
   - Client request headers include `Referer: ...?x_padding=XXX...` by default (put in Referer to avoid unnecessary OPTIONS requests by Browser Dialer). The default length is 100–1000 bytes, randomised per request. The server checks that the padding length is within the allowed range by default.
   - Server response headers include `X-Padding: XXX...` by default, with length 100–1000, randomised per response.
   - **This is the header padding I have mentioned multiple times; the corresponding setting is `xPaddingBytes`.**
   - The idea of moving request header padding into `Referer` was proposed by @rPDmYQ, as was using `XXX`. `X` in Huffman encoding is 8 bits.

**Packetized uplink and `Referer: ...?x_padding=XXX...` produce relatively many and long log entries. You can configure your reverse proxy not to log them.**

Additionally, like other Xray transports, the server accepts the `X-Forwarded-For` header to obtain the client’s real IP, and it can check the `host` header sent by the client against the server’s configured `host` (my personal advice: don’t set it unless necessary, since we are already hiding behind a path).

**The above is the minimal, necessary flow of packet-up mode. However, there is one more small question: how to implement and limit the POST requests? There are three dedicated parameters:**

- `scMaxEachPostBytes`: maximum data per client POST, default 1000000 (1MB). This value should be smaller than the limit allowed by CDN and other HTTP middleboxes. The server will reject POSTs larger than this.
- `scMinPostsIntervalMs`: client only, per proxy request, minimum interval between client POST requests, default 30 ms.
- `scMaxBufferedPosts`: server only, per proxy request, maximum number of POST requests the server will buffer, default 30. Connection is dropped if exceeded.

**“Per proxy request” means each proxy request counts independently and does not affect others**, even if they are on the same H2/H3 connection. This is the meaning of “sc” – sub-connection. **To reduce fingerprints, the first two values can be given as ranges**, for example strings `"500000-1000000"` and `"10-50"`, randomised each time. All these parameters can be distributed to the client via `extra` (explained at the end of the article). **It is also worth noting that the latest Xray version has optimised packet-up, with speed almost catching up with stream-up, mainly benefiting QUIC H3 through CDN.**

## H1 / H2 / H3

Now that we have packet-up mode, which can penetrate almost all HTTP middleboxes, let’s discuss something interesting: **QUIC H3 through CDN – the brand-new era that SplitHTTP brought. Understanding this section is especially important for using XHTTP flexibly.**

A characteristic of many HTTP middleboxes is HTTP version conversion. For example, CDN and Nginx will convert incoming H3 traffic to H1 or H2 when forwarding to the origin. **This means our XHTTP server can listen only on H1 and H2, without needing to listen on H3, but the XHTTP client can still use H3.**

**This is also the default behaviour of the XHTTP server: it only listens on a TCP port and handles H1 and H2 traffic.** When TLS is enabled and you set only `"h3"` in `alpn`, the server will use quic-go to listen on a UDP port and handle H3 traffic, but this is not recommended at the moment. **Instead, you should hide XHTTP behind a real Nginx or Caddy to reduce fingerprint characteristics – this is also one of XHTTP’s important advantages over other QUIC-based proxies, ~~and of course the other advantage is being able to go through CDN~~.** Additionally, H3 congestion control is implemented at the application layer. In theory you could modify the QUIC congestion control algorithm of those reverse-proxy software and recompile, ~~to achieve the “aggressive sending” some people want~~.

**For the XHTTP client:**
1. **When TLS/REALITY is enabled, H2 is used by default**; otherwise HTTP/1.1.
2. When TLS is enabled, if `alpn` contains only `"http/1.1"`, HTTP/1.1 is used (but Xray will not allow changing the uTLS browser fingerprint camouflage in that case).
3. **When TLS is enabled, if `alpn` contains only `"h3"`, quic-go H3 is used.**
4. However, when using Browser Dialer, the specific HTTP version is determined by the browser (the entire `tlsSettings` is ignored).

**If you want to confirm the actual HTTP version and host used by the Xray client, as well as XHTTP mode, uplink/downlink separation, etc., set the log level to `"info"`.**

**Proxy QUIC H3 through CDN – at least XHTTP is the first to achieve this at scale, opening a new path.** After all, in some regions and with some ISPs, H3 is not heavily censored, ~~though in others it gets Q-ed to death~~. Even though we later developed stream-up mode and found that adding gRPC header camouflage can penetrate Cloudflare, that only applies to H2. ~~It seems the significance of this new era keeps growing.~~

## XMUX

**Now that we’ve mentioned H2 and H3, we must talk about their multiplexing: both are 0-RTT.** The difference is that H3 does not have H2’s TCP head-of-line blocking problem and supports connection migration – the client won’t disconnect when changing networks. ~~So friends who regularly read RFCs will ask~~: how do we specifically control their multiplexing? **We designed a concise yet powerful interface, XMUX:**

- `maxConcurrency`: maximum number of simultaneous proxy requests per TCP/QUIC connection. **When the number of proxy requests in a connection reaches this value, the core will establish a new connection** to accommodate more proxy requests. **When all XMUX values are 0, this defaults to `"16-32"`, randomised each time.**

- `maxConnections`: maximum number of simultaneous connections. **Before the number of connections reaches this value, each new proxy request will open a new connection.** After that, the core will start reusing existing connections. This conflicts with `maxConcurrency` – you can only use one of them. Default 0 (unlimited), supports range strings, randomised each time.

- `cMaxReuseTimes`: maximum number of times a connection is reused. **After being reused this many times, the connection will no longer be assigned new proxy requests** and will disconnect after the last internal proxy request closes. Default 0 (unlimited), supports range strings, randomised each time.

- `hMaxRequestTimes`: @xqzr discovered that Nginx by default allows up to 1000 HTTP requests per TCP/QUIC connection. **When all XMUX values are 0, this defaults to `"600-900"`, randomised**; otherwise default 0 (unlimited). **This item counts HTTP requests.** Generally stream-one produces one HTTP request, stream-up two, and packet-up N. The counting is not rigorous, and Golang’s GET requests have automatic retries, so it is not recommended to set this to the absolute maximum – you need to test with your CDN. **For packet-up, when the ongoing uplink POSTs exceed this limit, it will automatically switch to another TCP/QUIC connection, consuming one `reuseTimes` but not `concurrency`.** In fact, with the three default XMUX values, stream-* won’t hit the limit; only packet-up will, and it is the default mode for H3, **so adding this item again mainly benefits H3.**

- `hMaxReusableSecs`: @xqzr discovered that Nginx by default allows a TCP/QUIC connection to be reused for one hour. **When all XMUX values are 0, this defaults to `"1800-3000"`, randomised**; otherwise default 0 (unlimited). **After a TCP/QUIC connection lasts this long, it will no longer be assigned new HTTP requests** and will disconnect after the last internal HTTP request closes. For packet-up, if the ongoing uplink POSTs exceed this time, it automatically switches to another TCP/QUIC connection, consuming one `reuseTimes` but not `concurrency`.

- `hKeepAlivePeriod`: how often the client sends keep-alive packets on an idle H2/H3 connection, in seconds. Default 0, which means Chrome’s H2 default of 45 seconds, or quic-go H3’s 10 seconds. This is the only XMUX item that does not allow a range (randomness would be a fingerprint) and allows negative values (e.g., -1 to disable idle keep-alive). It is recommended to leave it at 0.

These XMUX parameters can be combined in various ways. For example, before multi-threaded speed tests you need to set `"maxConcurrency": 1`, while “unlimited” reuse can be achieved with `"maxConnections": 1`. Even if you don’t bother studying them, **when all these values are 0, the three default values written above will be applied, which means the H2/H3 main connection gets replaced periodically – quite smooth.** There won’t be the “stream stalling” experience caused by gRPC and HTTP transports always reusing the same connection. Likewise, these parameters can be distributed to the client via `extra`.

Note: Leaving everything empty is equivalent to all zeros, which will also pick up the three default values. **But if you set any one item, the other items will not have default values – you’ll need to fill them all in yourself.** Except for the first two, all items can be set simultaneously.

**Additionally, do not enable mux.cool when using XHTTP. Newer Xray server versions already have a check and only accept pure XUDP.**

Some excerpts about XMUX defaults:

> - I deliberately chose two options that are not easily discernible outside TLS: `maxConcurrency` plus `cMaxReuseTimes` (instead of `maxConnections` plus `cMaxLifetimeMs`). And the default values for both are randomised ranges, maximally eliminating potential fingerprints.
> - I chose `maxConcurrency` instead of `maxConnections` precisely to prevent the number of connections from becoming a fixed pattern. Of course, if you prefer the latter you can set it manually.

> - XMUX and Nginx count different objects. `maxConcurrency` and `cMaxReuseTimes` are both based on “proxied connections”. Only stream-one produces one HTTP request; stream-up produces two (one uplink, one downlink); packet-up produces N.
> - However, I’m not sure if stream-one might automatically produce an extra HTTP request in some cases. **Also, I think pursuing indefinite reuse of a single connection is not very meaningful, because if you were the ISP you would also limit the speed and clean up old connections – otherwise resources would gradually be eaten up by old connections. That is why XMUX’s default parameters limit reuse and rotate connections periodically.**

Some Nginx parameters are also discussed further down in the article.

## STREAM-UP/ONE

Finally, the other important mode of XHTTP: **“Streaming uplink, streaming downlink” – stream-up.** As the name implies, this mode’s uplink is also streaming, so uplink efficiency is not sacrificed. It was originally developed for REALITY, until we discovered that adding gRPC header camouflage enables H2 penetration through Cloudflare (**requires enabling gRPC support in the dashboard**), and reverse proxy software like Nginx also works well (**Nginx recommends `grpc_pass` – simple and easy**). So the default behaviour of `mode` as `"auto"` is:

- Client: **TLS H2 → stream-up; REALITY → stream-one** (stream-up if `downloadSettings` exists); **otherwise packet-up.**
- Server: accepts all three modes by default. **If set to a specific mode, it only accepts that mode.** An exception: `"stream-up"` also accepts stream-one.

> stream-up has slightly better compatibility than stream-one. Some community members reported that with CFT, enabling streaming uplink allows stream-up, but you need an additional option to make stream-one work (possibly due to the SSE camouflage?). Also, one CDN (forgot the name) severely throttles stream-one but not stream-up.

**Their implementations (non-developers may skip):**

- For stream-up, change packet-up’s packetized uplink to a streaming `POST /yourpath/sameUUID`, also with `Referer: ...?x_padding=XXX...`.
- For stream-one, just `POST /yourpath/` – the response is the downlink. Both directions are streaming, with header padding on both request and response headers.
- Note: for stream-one, if you set `/yourpath`, the actual request goes to `/yourpath/`. If there’s no trailing slash, one is automatically appended.
- **The uplink defaults to `Content-Type: application/grpc` to masquerade as gRPC (you can set `noGRPCHeader` to disable it).**
- The server’s downlink response headers are exactly the same as packet-up’s step 2. In stream-one you may observe the oddity of responding to gRPC with SSE headers; if you encounter issues, try `noSSEHeader`.

> https://github.com/XTLS/Xray-core/discussions/4113#discussioncomment-11682833 related tests found that Cloudflare will terminate an HTTP connection with no real data for 100 seconds on the downlink, causing stream-up’s uplink direction to be cut off. **So [this PR](https://github.com/XTLS/Xray-core/pull/4306) added `scStreamUpServerSecs` for servers, default `"20-80"` (randomised). The server will send `xPaddingBytes` bytes at this interval for keep-alive.**
> 
> You can set `"scStreamUpServerSecs": -1` to disable this mechanism; the server will then not even send the response header in a timely manner, matching the behaviour of older versions.

**So friends who frequently use gRPC will ask: what advantages does stream-up have over the gRPC transport?**

- The former does not need any gRPC library – **better performance**.
- The downlink of the former is a separate GET request, **not subject to CDN’s traffic limits for gRPC.**
- The former also has header padding, **XMUX**, uplink/downlink separation, and already incorporates the extra mechanism so all parameters can be shared – **more mature.**

Of course, the advantages of XHTTP over WebSocket and HTTPUpgrade, aside from **“no distinct fingerprint of ALPN http/1.1”**, I’m sure you already know after reading this far. I won’t list them all, ~~mainly because there are too many to list~~.

## Uplink/Downlink Separation

**The grand finale is, of course, yet another new era: uplink/downlink separation.** We roughly know that currently the GFW detects traffic characteristics like TLS-in-TLS based on a single connection. **If we split the uplink and downlink into different censorship systems – for example, uplink over IPv4 TCP, downlink over IPv6 UDP – the GFW will not react immediately.** And because the XHTTP server associates uplink and downlink solely by the randomly generated UUID in the path, **packet-up and stream-up inherently have true uplink/downlink separation capability.** Since XHTTP can penetrate various CDNs and can be combined with REALITY and more, the possibilities are infinite. For the client, you need to set `downloadSettings`:

```jsonc
"xhttpSettings": {
    "host": "example.com",
    "path": "/yourpath", // must be the same
    "mode": "auto",
    "extra": {
        "headers": {
            // "key": "value"
        },
        "xPaddingBytes": "100-1000",
        "noGRPCHeader": false, // stream-up/one, client only
        "noSSEHeader": false, // server only
        "scMaxEachPostBytes": 1000000, // packet-up only
        "scMinPostsIntervalMs": 30, // packet-up, client only
        "scMaxBufferedPosts": 30, // packet-up, server only
        "scStreamUpServerSecs": "20-80", // stream-up, server only
        "xmux": { // h2/h3 mainly, client only
            "maxConcurrency": "16-32",
            "maxConnections": 0,
            "cMaxReuseTimes": 0,
            "hMaxRequestTimes": "600-900",
            "hMaxReusableSecs": "1800-3000",
            "hKeepAlivePeriod": 0
        },
        "downloadSettings": { // client only
            "address": "", // another domain/IP
            "port": 443,
            "network": "xhttp",
            "security": "tls",
            "tlsSettings": {
                ...
            },
            "xhttpSettings": {
                "path": "/yourpath", // must be the same
                ...
            },
            "sockopt": {} // will be replaced by upload's "sockopt" if the latter's "penetrate" is true
        }
    }
}
```

**As you can see, `downloadSettings` is essentially a new `streamSettings`**, but with an extra `address` and `port` like in a VLESS outbound, to point to another entry. Obviously the `network` must be `"xhttp"` (cannot be omitted), and `security` can be `"tls"` or `"reality"`. **The `sockopt` item can be shared, but the receiver can set `penetrate` to true in the uplink `sockopt` to override the downlink – suitable for marking situations. Apart from this exception, when using uplink/downlink separation, the downlink configuration is completely independent and does not inherit any configuration from the uplink.** Moreover, for example, even if both uplink and downlink leave XMUX empty and thus use the default values, the specific values rolled from the ranges are independent and unrelated. **Over time, the multiplexing of uplink and downlink is completely asymmetric, and the timing of main connection rotations differs, which provides better anti-analysis effect.** Because if the GFW were to act against uplink/downlink separation, “identical main connection initiation time” would definitely be the most important entry point. Therefore, in the future, XHTTP will also allow initiating uplink and downlink connections at different times from the start.

In fact, if you are behind a CDN, you don’t even need to modify the server configuration to play with uplink/downlink separation. **For example, you can preferred-route an IPv4 address for TLS H2, and another IPv6 address for QUIC H3.** Also, CDNs generally support same-domain fronting. For instance, you can set the uplink `serverName` to `"a.example.com"`, the downlink `serverName` to `"b.example.com"`, and both `host` headers to `"c.example.com"`, **making the external SNIs appear different as well.** Of course, it’s even better if you have two domains. If you don’t have any domain at all, you can still deploy two VPS with two REALITY configurations for uplink/downlink separation: **whether CDN + reverse proxy, or REALITY + fallback, as long as both ultimately arrive at the same XHTTP inbound on the same VPS via the same path.** In short, because XHTTP works everywhere, the combinations you can freely assemble are endless – the only limit is your imagination.

**For example, after uplink/downlink separation was introduced, many people actually use it by assigning the uplink to a route with good forward path and the downlink to a route with good return path – this is quite practical.**

You could also set `"maxConnections": 1` for uplink and `"maxConcurrency": 1` for downlink, **so that the small amount of uplink data travels over a single underlying connection, while the large amount of downlink data is spread across different underlying connections, achieving anti-censorship, low latency and high speed simultaneously.** It’s a bit like Switch; combined with Vision Seed the effect is even better.

Above I pasted a configuration example that covers all parameters. **It’s mainly to let you know where each item should be written** and to explain some parameters not elaborated earlier:

- **`extra` is the raw JSON sharing scheme for all parameters other than `host`, `path`, `mode`. When `extra` exists, only those four items take effect. The share link only contains those four items, and GUIs generally only show those four, because parameters in `extra` are relatively low-frequency and should be distributed directly by the service publisher to clients – clients should not be allowed to modify them arbitrarily.**
Additional note: “distribute” means “people distribute” – the service publisher writes the complete `extra` and puts it into the share link; the client can use it directly as their own `extra`.

- `host` behaves the same as in Xray’s other HTTP-based transports. **The client’s host sending priority is `host` > `serverName` > `address`.** If the server sets `host`, it will check whether the client-sent value matches; otherwise no check is performed. It is recommended not to set it unless necessary. `host` must not be placed inside `headers`.

> **If you want to confirm the actual HTTP version and host used by the Xray client, as well as XHTTP mode, uplink/downlink separation, etc., set the log level to `"info"`.**

## Beyond REALITY

**Early last year I returned and wrote REALITY, which ~~destroys everything~~ solved multiple pain points in one go.** ~~Then I went clubbing every day and left things alone,~~ even the article has been delayed until now and is still unfinished. ~~XUDP UoT Migration is even more regrettable – last year the article was almost done but never published.~~ **Unknowingly, REALITY has quietly grown into the mainstream direct-connection solution.** I often see comments under posts about something being blocked recommending switching to REALITY – its reputation is evident. ~~Even because it’s so stable, the community isn’t as lively as before.~~ Although Xray has also made significant optimisations and improvements to other transports, **XHTTP is the first native Xray transport, ~~and the first one was a big one.~~** Having read this article, you also know that XHTTP can be used together with REALITY:

**“Beyond REALITY” does not mean replacing REALITY, but surpassing REALITY in popularity. It is no exaggeration to say that, in the consistent style of Xray, the emergence of XHTTP renders all other HTTP-based transports pale. This is the era where XHTTP handles all scenarios. It will be more popular than the previous successful protocol REALITY, because XHTTP’s features already determine that its coverage will be broader.**

Finally, I hope the appearance of XHTTP can bring you a little shock, just as Xray has done many times in history: **Innovation and renewal are always the faith of Xray.**

### If this article helps you, support a [REALITY NFT](https://opensea.io/assets/ethereum/0x5ee362866001613093361eb8569d59c4141b76d1/2):

- Total supply 1,000; the first 100 are priced at 0.01 ETH. The price will increase afterwards. **Snagging the first batch is pure profit.**
- ~~An article introducing REALITY will be published in the coming days.~~ It turned into an introduction to XHTTP.
- **Holding a REALITY NFT gives you early internal testing access to a new Xray client, as well as an airdrop of the next NFT – just like.**
- On 2025.1.1, holders of Project X NFT will receive two REALITY NFTs for free.

Thanks to everyone’s support, Project X NFT has already multiplied 5–6 times in value. For friends who hesitated during the initial offering of Project X NFT, this is a great opportunity to make up for that regret.

### Of course, if you can, supporting a [Project X NFT](https://github.com/XTLS/Xray-core/discussions/3633) is even more appreciated:

- ETH/USDT/USDC: `0xDc3Fe44F0f25D13CACb1C4896CD0D321df3146Ee`
- Project X NFT: [Announcement of NFTs by Project X #3633](https://github.com/XTLS/Xray-core/discussions/3633)
- REALITY NFT: https://opensea.io/assets/ethereum/0x5ee362866001613093361eb8569d59c4141b76d1/2
- Sometimes ETH gas fees are ridiculously high. You can click “favourite” first and buy when the gas fee is relatively normal.

If anything is still unclear, please leave a comment below and I will update the article. ~~It is recommended not to produce translated versions too early.~~
