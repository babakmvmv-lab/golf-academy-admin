#!/usr/bin/env python3
"""Refresh public assets for the original PuttClub admin export on admin.puttclub.ir.

The three Next.js route exports under admin/ are intentionally owned by this repository.  The
public-site repository removed them after the admin host was created, so this job refreshes only
shared, compiled assets and never copies the public site's pages or redesigns the admin UI.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP_AT_ROOT = {
    ".git", ".github", "CNAME", "README.md", "index.html", "login.html", "404.html",
    "robots.txt", "admin", "tools",
}

# This small adapter only changes links that were root-relative when the same pages lived on
# puttclub.ir.  Internal /admin and /admin/site routes stay on the new admin host.
NAV_ADAPTER = r'''<!-- admin-host-navigation:begin -->
<script id="admin-host-navigation">
(function(){
  document.addEventListener('click',function(event){
    var el=event.target;
    if(el&&el.nodeType!==1)el=el.parentElement;
    if(!el||!el.closest)return;
    var a=el.closest('a[href]');if(!a)return;
    var href=a.getAttribute('href')||'';
    var path=href.split(/[?#]/,1)[0];
    var publicPath=path==='/'||path==='/shop'||path==='/shop/'||
      path==='/academy'||path==='/academy/'||path==='/checkout'||path==='/checkout/'||
      path.indexOf('/product/')===0;
    if(!publicPath)return;
    event.preventDefault();event.stopImmediatePropagation();
    window.location.assign('https://puttclub.ir'+href);
  },true);
})();
</script>
<!-- admin-host-navigation:end -->'''

# Small, host-local polish for Persian admin headers.  The public website and all page content stay
# unchanged; this fixes the Latin display font being applied to Persian brand text and normalizes
# the existing vector icons without replacing the original interface.
HEADER_POLISH = r'''<!-- admin-header-polish:begin -->
<style id="admin-header-polish">
/* Persian header type: use the panel's bundled Vazirmatn face, with correct RTL shaping. */
#shop-ops .sh-brand b,
#shop-ops .sh-top h1,
#shop-ops .sh-top-meta,
#shop-ops .sh-nav button,
#shop-ops .sh-side-bottom,
body aside .text-sm.font-black,
body aside nav button,
body main .text-xl.font-black {
  font-family: var(--font-vazirmatn, "Vazirmatn", Tahoma, sans-serif) !important;
  font-feature-settings: "kern" 1, "liga" 1;
  letter-spacing: 0 !important;
}
#shop-ops .sh-brand b {
  direction: rtl !important;
  text-align: right;
  font-size: 17px !important;
  font-weight: 750 !important;
  line-height: 1.55 !important;
}
#shop-ops .sh-brand small { letter-spacing: 0 !important; font-size: 11px !important; }
#shop-ops .sh-top h1 {
  font-size: clamp(18px, 3.4vw, 22px) !important;
  line-height: 1.55 !important;
  font-weight: 750 !important;
}
#shop-ops .sh-top .sh-eyebrow { font-family: var(--font-vazirmatn, "Vazirmatn", Tahoma, sans-serif) !important; letter-spacing: .35px !important; }
#shop-ops .sh-hamburger {
  width: 42px !important; height: 42px !important;
  border-radius: 12px !important;
  border-color: #ddc07c55 !important;
  background: #ddc07c12 !important;
  color: #e6d39e !important;
  box-shadow: 0 2px 8px #0002;
}
#shop-ops .sh-hamburger .sh-icon { width: 22px; height: 22px; background: transparent; color: inherit; }
#shop-ops .sh-hamburger .sh-icon svg { width: 20px; height: 20px; stroke-width: 1.85 !important; }
#shop-ops .sh-icon svg,
body aside nav button svg,
body aside a svg,
body aside button svg,
body main svg.lucide {
  flex: 0 0 auto;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.8 !important;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}
body aside nav button svg,
body aside a svg,
body aside button svg { width: 18px; height: 18px; }
body main svg.lucide { display: block; }
@media (max-width: 760px) {
  #shop-ops .sh-top { align-items: center !important; }
  #shop-ops .sh-top .sh-eyebrow { font-size: 9px !important; }
  #shop-ops .sh-top-meta { line-height: 1.7; }
}
</style>
<!-- admin-header-polish:end -->'''

# The private routes get their own local scenic backgrounds; no public page is changed.
BACKGROUND_CSS = {
    "admin/index.html": r'''<!-- admin-background:begin -->
<style id="admin-background">
#shop-ops {
  background-image: linear-gradient(180deg, rgba(3,10,7,.62), rgba(3,10,7,.72)), url("/admin/assets/admin-cinematic-bg.jpg") !important;
  background-position: center center;
  background-repeat: no-repeat;
  background-size: cover !important;
  background-attachment: fixed;
}
#shop-ops .sh-side {
  background: linear-gradient(180deg, rgba(16,37,27,.91), rgba(10,25,18,.95)) !important;
  -webkit-backdrop-filter: blur(10px) saturate(108%);
  backdrop-filter: blur(10px) saturate(108%);
}
@media (max-width:760px) {
  #shop-ops { background-attachment: scroll; background-position: 58% center; }
}
</style>
<!-- admin-background:end -->''',
    "admin/site/index.html": r'''<!-- admin-background:begin -->
<style id="admin-background">
body {
  background-image: linear-gradient(140deg, rgba(3,10,7,.60), rgba(3,10,7,.73)), url("/admin/assets/admin-cinematic-bg.jpg") !important;
  background-position: center center;
  background-repeat: no-repeat;
  background-size: cover !important;
  background-attachment: fixed;
}
body aside {
  -webkit-backdrop-filter: blur(12px) saturate(108%);
  backdrop-filter: blur(12px) saturate(108%);
}
@media (max-width:760px) {
  body { background-attachment: scroll; background-position: 58% center; }
}
</style>
<!-- admin-background:end -->''',
    "admin/login/index.html": r'''<!-- admin-background:begin -->
<style id="admin-background">
body {
  background-image: linear-gradient(135deg, rgba(3,10,8,.72), rgba(3,10,8,.53) 55%, rgba(3,10,8,.70)), url("/admin/assets/admin-login-cinematic-bg.jpg") !important;
  background-position: center 54%;
  background-repeat: no-repeat;
  background-size: cover !important;
  background-attachment: fixed;
}
@media (max-width:760px) {
  body { background-attachment: scroll; background-position: 54% center; }
}
</style>
<!-- admin-background:end -->''',
}

# Keep the same login UI, but do not hide the Auth service's actual failure behind
# "check email and password".  No credentials or raw server responses are exposed.
AUTH_ERROR_OLD = (
    "catch(e){if(e.code==='WEB_ADMIN_REQUIRED')throw e;const out=error('ورود ابری انجام نشد؛ ایمیل و رمز مدیر سایت را بررسی کنید.',"
    "e.status||401,'WEB_AUTH_REQUIRED');out.errorCode=e.errorCode||'';out.serverMessage=e.serverMessage||'';throw out;}"
)
AUTH_ERROR_NEW = r'''catch(e){
      if(e.code==='WEB_ADMIN_REQUIRED')throw e;
      const code=String(e.errorCode||e.code||''),status=Number(e.status)||401;
      let message;
      if(/rate|over_request|too many/i.test(code+' '+String(e.serverMessage||''))||status===429)
        message='ورود موقتاً به‌دلیل تلاش‌های زیاد محدود شده؛ چند دقیقه بعد دوباره امتحان کنید.';
      else if(code==='email_not_confirmed')
        message='ایمیل این حساب در سرویس ابری تأیید نشده است.';
      else if(code==='invalid_credentials'||code==='invalid_grant'||status===400||status===401)
        message='ورود رد شد: نام کاربری یا رمز حساب ابری درست نیست. نام Admin به admin@puttclub.ir نگاشت می‌شود.';
      else if(code==='NETWORK'||code==='TIMEOUT'||status===0||/ارتباط با ابر|مهلت/.test(String(e.message||'')))
        message='اتصال مرورگر به سرویس ورود ابری برقرار نشد؛ اتصال اینترنت را بررسی کنید و دوباره تلاش کنید.';
      else
        message='ورود ابری انجام نشد (HTTP '+status+(code?'، کد '+code:'')+'). همین پیام را بفرستید؛ رمز را نفرستید.';
      const out=error(message,status,'WEB_AUTH_REQUIRED');
      out.errorCode=code;out.serverMessage=String(e.serverMessage||e.message||'').slice(0,200);throw out;
    }'''


def fail(message: str) -> None:
    raise SystemExit(message)


def copy_item(src: Path, dest: Path) -> None:
    if not src.exists():
        fail(f"required upstream asset is missing: {src}")
    if dest.is_dir():
        shutil.rmtree(dest)
    elif dest.exists():
        dest.unlink()
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def clean_root() -> None:
    for item in ROOT.iterdir():
        if item.name in KEEP_AT_ROOT:
            continue
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()
    (ROOT / ".nojekyll").touch()


def patch_bootstrap(manifest: dict) -> str:
    boot = str(manifest.get("bootstrap") or "")
    if not re.fullmatch(r"site-cloud\.[0-9a-f]{12}\.js", boot):
        fail(f"invalid current bootstrap in manifest: {boot!r}")
    path = ROOT / boot
    if not path.is_file():
        fail(f"manifest bootstrap was not copied: {boot}")
    source = path.read_text(encoding="utf-8")
    if source.count(AUTH_ERROR_OLD) != 1:
        fail("signInAdmin error-message anchor changed; refusing to publish an unhelpful login error")
    source = source.replace(AUTH_ERROR_OLD, AUTH_ERROR_NEW, 1)
    new_boot = "site-cloud." + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12] + ".js"
    (ROOT / new_boot).write_text(source, encoding="utf-8")
    if new_boot != boot:
        path.unlink()
    manifest["bootstrap"] = new_boot
    return new_boot


def refresh_route_refs(boot: str, chunks: dict[str, str]) -> None:
    for path in sorted((ROOT / "admin").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".html", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"site-cloud\.[0-9a-f]{12}\.js", boot, text)
        for original, current in sorted(chunks.items(), key=lambda item: len(item[0]), reverse=True):
            text = re.sub(r"pc-[0-9a-f]{12}-" + re.escape(original), current, text)
            text = re.sub(r"(?<![-\w])" + re.escape(original), current, text)
        if re.search(r"pc-[0-9a-f]{12}-pc-[0-9a-f]{12}-", text):
            fail(f"corrupted Next chunk reference in {path.relative_to(ROOT)}")
        path.write_text(text, encoding="utf-8")


def inject_navigation_adapter(boot: str) -> None:
    for rel in ("admin/index.html", "admin/site/index.html", "admin/login/index.html"):
        path = ROOT / rel
        if not path.is_file():
            fail(f"missing original admin route export: {rel}")
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"<!-- admin-host-navigation:begin -->[\s\S]*?<!-- admin-host-navigation:end -->",
            "", text,
        )
        text = re.sub(
            r"<!-- admin-header-polish:begin -->[\s\S]*?<!-- admin-header-polish:end -->",
            "", text,
        )
        text = re.sub(
            r"<!-- admin-background:begin -->[\s\S]*?<!-- admin-background:end -->",
            "", text,
        )
        tag = f'<script src="/{boot}"></script>'
        if text.count(tag) != 1:
            fail(f"expected exactly one {tag} in {rel}")
        text = text.replace(tag, tag + NAV_ADAPTER, 1)
        if text.lower().count("</head>") != 1:
            fail(f"expected exactly one closing head tag in {rel}")
        background = BACKGROUND_CSS.get(rel)
        if not background:
            fail(f"no background style is configured for {rel}")
        text = re.sub(r"</head>", HEADER_POLISH + background + "</head>", text, count=1, flags=re.I)
        path.write_text(text, encoding="utf-8")


def write_entry_pages() -> None:
    (ROOT / "index.html").write_text('''<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="refresh" content="0;url=/admin/">
<title>داشبورد مدیر | پات‌کلاب</title></head>
<body><p>در حال باز کردن داشبورد مدیر… <a href="/admin/">ادامه</a></p>
<script>location.replace('/admin/');</script></body></html>
''', encoding="utf-8")
    (ROOT / "login.html").write_text('''<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="refresh" content="0;url=/admin/login/">
<title>ورود مدیران | پات‌کلاب</title></head>
<body><p>در حال باز کردن ورود مدیران… <a href="/admin/login/">ادامه</a></p>
<script>location.replace('/admin/login/');</script></body></html>
''', encoding="utf-8")
    (ROOT / "404.html").write_text('''<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="refresh" content="0;url=https://puttclub.ir/">
<title>صفحه پیدا نشد | پات‌کلاب</title></head>
<body><p>صفحه پیدا نشد. <a href="https://puttclub.ir/">بازگشت به سایت پات‌کلاب</a></p>
<script>location.replace('https://puttclub.ir/');</script></body></html>
''', encoding="utf-8")
    (ROOT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")


def verify(manifest: dict, boot: str) -> None:
    expected = {
        "admin/index.html": "داشبورد مدیر | پات‌کلاب",
        "admin/site/index.html": "مدیریت سایت | پات‌کلاب",
        "admin/login/index.html": "pc-28304687a7b7-12lzqn_~_d9qf.js",
    }
    for rel, marker in expected.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        if marker not in text:
            fail(f"wrong or missing original route at {rel}: expected {marker!r}")
        if "admin-shell-css" in text or "ga-cinematic" in text or "puttclub-admin-frame-height" in text:
            fail(f"custom shell/skin was injected into the original route {rel}")
        if text.count(boot) != 1:
            fail(f"{rel} does not load exactly one current cloud bootstrap")
        if "admin-host-navigation" not in text:
            fail(f"{rel} is missing the cross-host site-link adapter")
        if text.count("<!-- admin-header-polish:begin -->") != 1:
            fail(f"{rel} is missing the host-local header typography/icon polish")
        if "Vazirmatn" not in text or "stroke-width: 1.8" not in text:
            fail(f"{rel} is missing the intended Persian font or consistent icon styling")
        if text.count("<!-- admin-background:begin -->") != 1:
            fail(f"{rel} is missing its cinematic background")
        if rel == "admin/login/index.html":
            image = "admin-login-cinematic-bg.jpg"
        else:
            image = "admin-cinematic-bg.jpg"
        if f"/admin/assets/{image}" not in text or not (ROOT / "admin/assets" / image).is_file():
            fail(f"{rel} references a missing cinematic image: {image}")
    site = (ROOT / "admin/site/index.html").read_text(encoding="utf-8")
    if "<iframe" in site or "admin-login-guard" in site:
        fail("the site editor must stay on its own native Next route, not an iframe/redirect shell")
    login_chunk = (ROOT / "_next/static/chunks/pc-28304687a7b7-12lzqn_~_d9qf.js")
    if not login_chunk.is_file():
        fail("the original administrator login route chunk is missing")
    login_js = login_chunk.read_text(encoding="utf-8")
    for marker in ("پنل فروشگاه", "پنل سایت", "signInAdmin", "بازگشت به فروشگاه"):
        if marker not in login_js:
            fail(f"original login page is missing its expected control: {marker}")
    boot_path = ROOT / boot
    boot_source = boot_path.read_text(encoding="utf-8")
    for marker in ("PC_SITE_CLOUD", "loadShopOps", "signInAdmin", "admin@puttclub.ir"):
        if marker not in boot_source:
            fail(f"cloud bootstrap is missing expected admin API: {marker}")
    shop = str(manifest.get("shopOpsAsset") or "")
    if not shop or not (ROOT / shop).is_file():
        fail("the current shop-ops asset is missing")
    if "backupView2" not in (ROOT / shop).read_text(encoding="utf-8"):
        print("::warning::current shop-ops asset does not contain backupView2")
    missing = []
    for path in (ROOT / "admin").rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        refs = set(re.findall(r'(?:src|href)=["\'](/[^"\'?#]+)["\']', text))
        for ref in refs:
            if ref.startswith(("/_next/", "/images/", "/data/")):
                target = ROOT / ref.lstrip("/")
                if not target.is_file():
                    missing.append(f"{path.relative_to(ROOT)} → {ref}")
    if missing:
        fail("dangling admin export references:\n  " + "\n  ".join(sorted(missing)))


def preflight(main: Path) -> dict:
    """Fail before clean_root() if the source export is incomplete or no longer compatible."""
    manifest_path = main / "source/public-cloud-manifest.json"
    if not manifest_path.is_file():
        fail(f"upstream export is incomplete: {main}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"upstream manifest is unreadable: {exc}")
    boot = str(manifest.get("bootstrap") or "")
    shop = str(manifest.get("shopOpsAsset") or "")
    if not re.fullmatch(r"site-cloud\.[0-9a-f]{12}\.js", boot):
        fail(f"invalid current bootstrap in upstream manifest: {boot!r}")
    if not re.fullmatch(r"shop-ops\.[0-9a-f]{12}\.js", shop):
        fail(f"invalid shop-ops asset in upstream manifest: {shop!r}")
    required = ("_next", "images", "data", "favicon.ico", "enter-academy.js", boot, shop)
    missing = [name for name in required if not (main / name).exists()]
    if missing:
        fail("upstream export is missing required assets: " + ", ".join(missing))
    for pattern, expected in (("site-cloud.*.js", boot), ("shop-ops.*.js", shop)):
        hits = sorted(main.glob(pattern))
        if len(hits) != 1 or hits[0].name != expected:
            fail(f"expected exactly the manifest asset {expected!r} for {pattern}, found {[p.name for p in hits]}")
    upstream_boot = (main / boot).read_text(encoding="utf-8")
    if upstream_boot.count(AUTH_ERROR_OLD) != 1:
        fail("signInAdmin error-message anchor changed; refusing to replace the local host output")
    for rel in ("admin/index.html", "admin/site/index.html", "admin/login/index.html"):
        if not (ROOT / rel).is_file():
            fail(f"the original admin route export is missing from this repository: {rel}")
    for rel in ("admin/assets/admin-cinematic-bg.jpg", "admin/assets/admin-login-cinematic-bg.jpg"):
        if not (ROOT / rel).is_file():
            fail(f"required private admin background is missing: {rel}")
    return manifest


def sync(main: Path) -> None:
    # Preflight before removing any generated files: an upstream build or manifest change must
    # never leave a local checkout half-cleaned when someone runs this tool by hand.
    manifest = preflight(main)
    clean_root()
    for name in ("_next", "images", "data", "favicon.ico", "enter-academy.js"):
        copy_item(main / name, ROOT / name)
    for pattern in ("site-cloud.*.js", "shop-ops.*.js"):
        hits = sorted(main.glob(pattern))
        if len(hits) != 1:
            fail(f"expected one current upstream {pattern}, found {len(hits)}")
        shutil.copy2(hits[0], ROOT / hits[0].name)
    shutil.copy2(main / "source/public-cloud-manifest.json", ROOT / "public-cloud-manifest.json")
    manifest_path = ROOT / "public-cloud-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    boot = patch_bootstrap(manifest)
    refresh_route_refs(boot, manifest.get("chunks") or {})
    inject_navigation_adapter(boot)
    write_entry_pages()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify(manifest, boot)
    print(f"Original admin routes retained; refreshed {boot} and {manifest.get('shopOpsAsset')}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("usage: python3 tools/sync_admin_host.py /path/to/current/golf-academy-pro-export")
    sync(Path(sys.argv[1]).resolve())
