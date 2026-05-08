<td class="d-block color-fg-default comment-body markdown-body js-comment-body">
  <h3 dir="auto">فارسی | <a href="https://github.com/XTLS/Xray-core/discussions/4113#discussioncomment-11468947" data-hovercard-type="discussion" data-hovercard-url="/XTLS/Xray-core/discussions/4113/hovercard?comment_id=11468947" aria-keyshortcuts="Alt+ArrowUp">Русский</a></h3>
  <h1 dir="auto">XHTTP: فراتر از REALITY</h1>

  <p dir="auto"><strong>خلاصه توسعه:</strong> در میانه ۲۰۲۴، <a href="https://github.com/mmmray">@mmmray</a> و <a href="https://github.com/ll11l1lIllIl1lll">@ll11l1lIllIl1lll</a> به همراه دیگران، بر اساس اصل «ارسال بسته‌ای در جهت آپلود و استریم در جهت دانلود» و جزئیات پیاده‌سازی ارائه‌شده توسط <a href="https://github.com/RPRX">@RPRX</a>، SplitHTTP را توسعه دادند. برای نخستین بار توانستند بدون کاهش کارایی دانلود، از اکثر باکس‌های میانی سازگار با HTTP عبور کنند و نخستین پیاده‌سازی گسترده QUIC H3 از طریق CDN را انجام دهند تا دعوت به دوران جدید شود.</p>

  <p dir="auto"><strong>سریع شروع کنید</strong></p>
  <ol dir="auto">
    <li>چه TLS باشد چه REALITY، <strong>معمولاً فقط تعیین <code>path</code> برای پیکربندی XHTTP کافی است؛ سایر فیلدها را خالی بگذارید</strong>.</li>
    <li>اگر سرور QUIC H3 پشتیبانی می‌کند، <strong>در سمت کلاینت <code>alpn</code> را روی «h3» بگذارید تا QUIC فعال شود</strong>.</li>
    <li>برای انتخاب IP بهینه‌ی CDN، در کلاینت <code>address</code> را IP و <code>serverName</code> (SNI) را دامنه قرار دهید.</li>
    <li>اگر به Cloudflare وصل نمی‌شود، <strong>در پنل CF گزینهٔ پشتیبانی gRPC را فعال کنید</strong>.</li>
    <li>اگر از Nginx عبور نمی‌کند، <strong>در کانفیگ Nginx <code>proxy_pass</code> را به <code>grpc_pass</code> تغییر دهید</strong>.</li>
    <li>اگر از CDN یا پروکسی معکوس دیگری عبور نمی‌کند، توصیه می‌شود <code>mode</code> را روی «packet-up» بگذارید تا بالاترین سازگاری را داشته باشید.</li>
  </ol>

  <p dir="auto"><strong>XHTTP به‌صورت پیش‌فرض مالتی‌پلکس دارد و تأخیرش از Vision کمتر است، ولی در تست چند رشته‌ای ضعیف‌تر است مگر اینکه <code>"maxConcurrency": 1</code> تنظیم کنید.</strong></p>

  <h2 dir="auto">دو منطق زیرساخت</h2>
  <p dir="auto">همان‌طور که REALITY می‌تواند خود را جای وب‌سایت دیگری جا بزند، <strong>منطق پایهٔ مقابله با سانسور، افزایش «آسیب جانبی» برای سانسورچی است تا او را از مسدودسازی بی‌محابا بازدارد</strong>. تجربهٔ چندین‌ساله نشان می‌دهد GFW هیچ‌گاه آدرس IP یک CDN بزرگ را برای همیشه مسدود نمی‌کند، چون وب‌سایت‌های عادی زیادی را درگیر می‌کند. <strong>بنابراین هدف اولیهٔ ما این بود که XHTTP را پشت انبوهی از CDNهای مختلف پنهان کنیم</strong>.</p>

  <h2 dir="auto">PACKET-UP</h2>
  <p dir="auto"><strong>برای بالاترین سازگاری XHTTP (حالت «بسته‌ای آپلود، استریم دانلود») این طراحی را به کار بردیم:</strong></p>
  <ol dir="auto">
    <li><strong>کلاینت با <code>POST /yourpath/sameUUID/seq</code> داده می‌فرستد:</strong>
      <ul dir="auto">
        <li>UUID تصادفی است؛ اگر ظرف ۳۰ ثانیه سرور نتواند درخواست‌ها را مرتبط کند، جلسه بسته می‌شود.</li>
        <li>seq از ۰ شروع می‌شود؛ POST بعدی تنها پس از ارسال کامل بادی POST قبلی مجاز است.</li>
        <li>سرور تا ۳۰ POST را نگه می‌دارد؛ از حد گذشتن باعث قطع می‌شود.</li>
      </ul>
    </li>
    <li><strong>کلاینت با <code>GET /yourpath/sameUUID</code> دانلود را آغاز می‌کند؛ هدرهای پاسخ سرور:</strong>
      <ul dir="auto">
        <li><code>X-Accel-Buffering: no</code></li>
        <li><code>Cache-Control: no-store</code></li>
        <li><code>Content-Type: text/event-stream</code></li>
      </ul>
    </li>
    <li><strong>برای پر کردن طول ثابت هدرها:</strong>
      <ul dir="auto">
        <li>درخواست‌ها: <code>Referer: ...?x_padding=XXX...</code> (۱۰۰–۱۰۰۰ بایت تصادفی)</li>
        <li>پاسخ‌ها: <code>X-Padding: XXX...</code> (۱۰۰–۱۰۰۰ بایت تصادفی)</li>
      </ul>
    </li>
  </ol>

  <h2 dir="auto">H1 / H2 / H3</h2>
  <p dir="auto"><strong>CDN و Nginx معمولاً نسخهٔ HTTP را تغییر می‌دهند؛ بنابراین سرور XHTTP می‌تواند فقط H1/H2 را گوش دهد ولی کلاینت با H3 متصل شود.</strong></p>
  <ul dir="auto">
    <li>اگر در <code>alpn</code> فقط «h3» باشد، کلاینت از quic-go H3 استفاده می‌کند.</li>
    <li>اگر <code>alpn</code> خالی یا «http/1.1» باشد، به ترتیب H2 یا HTTP/1.1 برمی‌گردد.</li>
  </ul>

  <h2 dir="auto">XMUX</h2>
  <ul dir="auto">
    <li><code>maxConcurrency</code>: حداکثر تعداد استریم‌های هم‌زمان در هر TCP/QUIC. پیش‌فرض تصادفی ۱۶–۳۲.</li>
    <li><code>maxConnections</code>: حداکثر تعداد کانکشن‌های مجزا. ۰ یعنی نامحدود.</li>
    <li><code>cMaxReuseTimes</code>: تعداد دفعات باز-استفاده از یک کانکشن. ۰ یعنی بی‌نهایت.</li>
    <li><code>hMaxRequestTimes</code>: حداکثر HTTP request در هر کانکشن (Nginx پیش‌فرض ۱۰۰۰). پیش‌فرض تصادفی ۶۰۰–۹۰۰.</li>
    <li><code>hMaxReusableSecs</code>: حداکثر زمان باز-استفاده از یک کانکشن. پیش‌فرض تصادفی ۱۸۰۰–۳۰۰۰ ثانیه.</li>
    <li><code>hKeepAlivePeriod</code>: بازهٔ keep-alive در ثانیه. ۰ یعنی رفتار پیش‌فرض مرورگر.</li>
  </ul>

  <h2 dir="auto">STREAM-UP / ONE</h2>
  <p dir="auto"><strong>در حالت «استریم آپلود، استریم دانلود» (stream-up) بازده آپلود نیز حفظ می‌شود.</strong></p>
  <ul dir="auto">
    <li>کلاینت برای TLS H2 به‌صورت خودکار stream-up و برای REALITY stream-one انتخاب می‌کند.</li>
    <li>سرور به‌طور پیش‌فرض هر سه حالت را می‌پذیرد.</li>
    <li>برای Nginx: <code>grpc_pass</code> توصیه می‌شود.</li>
    <li>سرور هر ۲۰–۸۰ ثانیه یک بایت padding می‌فرستد تا CF دانلود ۱۰۰ ثانیه‌ای بی‌داده را قطع نکند.</li>
  </ul>

  <h2 dir="auto">جداسازی آپلود / دانلود</h2>
  <p dir="auto"><strong>با جداسازی مسیر آپلود و دانلود (مثلاً IPv4 TCP vs IPv6 QUIC) GFW نمی‌تواند یک‌باره هر دو را شناسایی کند.</strong></p>
  <ul dir="auto">
    <li>در کلاینت <code>downloadSettings</code> تعریف کنید؛ در آن <code>address</code> و <code>port</code> جداگانه قابل تنظیم است.</li>
    <li>مقادیر XMUX و تنظیمات دیگر در آپلود و دانلود کاملاً مستقل خواهند بود.</li>
  </ul>

  <h2 dir="auto">Beyond REALITY</h2>
  <p dir="auto"><strong>Beyond REALITY به معنی کنار گذاشتن REALITY نیست؛ بلکه به معنی فراگیری بیشتر است.</strong> XHTTP به‌خاطر قابلیت‌هایش قطعاً پوشش گسترده‌تری نسبت به REALITY خواهد داشت.</p>

  <h3 dir="auto">اگر این مقاله برایتان مفید بود، از <a href="https://opensea.io/assets/ethereum/0x5ee362866001613093361eb8569d59c4141b76d1/2">REALITY NFT</a> حمایت کنید:</h3>
  <ul dir="auto">
    <li>تنها ۱۰۰۰ عدد؛ ۱۰۰ عدد اول ۰.۰۱ ETH، بعدی‌ها گران‌تر می‌شوند.</li>
    <li>دارندگان REALITY NFT به بتا ورژن جدید کلاینت Xray و ایردراپ بعدی دسترسی زودهنگام خواهند داشت.</li>
  </ul>

  <h3 dir="auto">آدرس حمایت با ETH/USDT/USDC:</h3>
  <p dir="auto"><code>0xDc3Fe44F0f25D13CACb1C4896CD0D321df3146Ee</code></p>
</td>
