# admin.puttclub.ir — پنل مدیریت پات‌کلاب

**یک پوستهٔ مدیریتی، دو بخش:** «مدیریت سایت» و «مدیریت فروشگاه». این هاست پوستهٔ عمومی puttclub.ir را نمایش نمی‌دهد.

- `https://admin.puttclub.ir/admin/` → پنل اصلی با همان دو بخش
- `https://admin.puttclub.ir/` → ارجاع به پنل اصلی (`/?shop=1` قدیمی به بخش فروشگاه می‌رود)
- `https://admin.puttclub.ir/login.html` → ورود مدیران با حساب Supabase Auth
- سند `admin/site/index.html` فقط داخل پنل، در قاب «مدیریت سایت» باز می‌شود تا مسیر واقعی Next.js (`/admin/site/`) حفظ شود؛ مراجعهٔ مستقیم به آن دوباره به پوستهٔ اصلی برمی‌گردد.
- مسیرهای قدیمی `/site/`, `/shop/` و `/admin/login/` تنها ارجاع سازگاری‌اند؛ صفحهٔ دوم یا پوستهٔ عمومی سایت کپی نمی‌شود.
- `robots.txt` → `Disallow: /` (این هاست ایندکس نمی‌شود).

## ورود

همان حساب Supabase Auth که قبلاً استفاده می‌کردی (`app_metadata.web_admin = true`، یا `web_shop_staff`
برای حساب‌های فقط-فروشگاه). جلسه در `localStorage` با کلید `puttclub_web_auth_v1` نگه داشته می‌شود و
پنل از همان‌جا می‌خواند؛ `login.html` همان `PC_SITE_CLOUD.signInAdmin(...)` را صدا می‌زند.

## داده

از همان ابر مشترک (Supabase) می‌آید؛ همهٔ فراخوانی‌های `/api/*` در مرورگر به Supabase ترجمه
می‌شوند، پس مستقل از دامنه کار می‌کنند. CORS پروژه روی `https://admin.puttclub.ir` تست شده است.

## انتشار

گردش‌کار «Publish the ops panel on this host» فایل‌های هش‌دار را از `golf-academy-pro` تازه می‌کند، اما
پوستهٔ این هاست را بازنویسی نمی‌کند:

1. `admin/index.html` = پوستهٔ مدیریتیِ موبایل‌پسند با دو تب؛ بخش فروشگاه، `SHOP_OPS.mount()` فعلی را بارگذاری می‌کند؛
2. `admin/site/index.html` = خروجیِ واقعی مدیریت سایت، با همان مسیر `/admin/site/` که بستهٔ Next.js انتظار دارد؛
3. `index.html` فقط ورودی را به `/admin/` می‌فرستد؛ `login.html` دو مقصدِ همین پوسته را ارائه می‌کند؛
4. `_next/`, `images/`, `data/`, `favicon.ico`, `enter-academy.js`, `site-cloud.*.js`, `shop-ops.*.js`
   و `public-cloud-manifest.json` تازه می‌شوند؛ نام bootstrap و chunkها در هر سه سند پنل/ورود بازنویسی می‌شود؛
5. `tools/cine.py` پس‌زمینه را فقط به پوسته و صفحهٔ ورود تزریق می‌کند؛ گردش‌کار ارجاع شکسته، مسیر گم‌شده، یا پنل ناقص را رد می‌کند.

صفحه‌های عمومی سایت (`shop/`, `checkout/`, `product/`, `academy/`, `login/`, `panel/`) عمداً اینجا
کپی نمی‌شوند — آن‌ها فقط روی `puttclub.ir` هستند.

- DNS: رکورد CNAME با نام `admin` و مقصد `babakmvmv-lab.github.io` (مدیریت در deSEC).
- زمان‌بندی: کرون `23 3 * * *` + `workflow_dispatch`.
