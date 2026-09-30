# admin.puttclub.ir — پنل عملیاتی سایت و فروشگاه

**تنها مسیر ورود به پنل مدیریت.** این هاست فقط پنل اُپس را سرو می‌کند؛ دیگر آینهٔ سایت عمومی نیست.

- `https://admin.puttclub.ir/` → خودِ پنل (بدون پسوند `/admin/site/`)
- `https://admin.puttclub.ir/login.html` → ورود مدیران (اگر جلسه‌ات تمام شده باشد)
- `admin/…` و `404.html` → فقط صفحه‌های یک‌خطیِ «جابه‌جا شد» برای بوک‌مارک‌های قدیمی
- `robots.txt` → `Disallow: /` (این هاست ایندکس نمی‌شود)

## ورود

همان حساب Supabase Auth که قبلاً استفاده می‌کردی (`app_metadata.web_admin = true`، یا `web_shop_staff`
برای حساب‌های فقط-فروشگاه). جلسه در `localStorage` کلید `puttclub_web_auth_v1` نگه داشته می‌شود و
پنل از همان‌جا می‌خواند؛ به همین دلیل `login.html` چیز جدیدی نمی‌سازد، فقط همان
`PC_SITE_CLOUD.signInAdmin(...)` را صدا می‌زند.

## داده

از همان ابر مشترک (Supabase) می‌آید؛ همهٔ فراخوانی‌های `/api/*` در خود مرورگر به Supabase ترجمه
می‌شوند، پس مستقل از دامنه کار می‌کنند. CORS پروژه روی `https://admin.puttclub.ir` تست شده است.

## publishes = فایل‌های این ریپو + گردش‌کار

`source/build_public_cloud.py` در ریپوی `golf-academy-pro` فایل‌های هش‌دار را می‌سازد؛ گردش‌کار
«Publish the ops panel on this host» آن‌ها را این‌جا می‌گذارد:

1. `index.html` (پوستهٔ پنل) از `admin/site/` ریپوی اصلی — اگر روزی از آن ریپو حذف شد، همین فایلِ
   ترک‌شدهٔ این ریپو استفاده می‌شود؛
2. `_next/`, `images/`, `data/`, `favicon.ico`, `enter-academy.js`, `site-cloud.*.js`, `shop-ops.*.js`
   و `public-cloud-manifest.json`؛
3. نام فایل‌های هش‌دار (bootstrap و چانک‌های `pc-*`) داخل `index.html` و `login.html` بازنویسی
   می‌شود، پس تغییر نام در ریپوی اصلی این هاست را نمی‌شکند؛
4. اگر ارجاع شکسته‌ای وجود داشته باشد یا bootstrap/shop-ops پیدا نشود، **ران فیلد می‌شود** و
   نسخهٔ قبلی سر جایش می‌ماند (به‌جای انتشار یک پنل نصفه‌نیمه).

صفحه‌های عمومی سایت (`shop/`, `checkout/`, `product/`, `academy/`, `login/`, `panel/`) عمداً اینجا
کپی **نمی‌شوند** — آن‌ها فقط روی `puttclub.ir` هستند.

- DNS: رکورد CNAME با نام `admin` و مقصد `babakmvmv-lab.github.io` (مدیریت در deSEC).
- زمان‌بندی: کرون `23 3 * * *` + `workflow_dispatch`.
