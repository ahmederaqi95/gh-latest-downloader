# gh-latest-downloader

أداة تحمّل **آخر إصدار (Release) من كل المشاريع** الموجودة في رابط GitHub (مستخدم أو منظمة أو مشروع واحد)، وتختار تلقائياً الملف المناسب لـ **نظام التشغيل والمعالج** عندك.

- بدون أي مكتبات خارجية، تحتاج Python 3.9 أو أحدث فقط
- تعمل على Windows وLinux وmacOS
- آمنة: تتحقق من الـ checksum وتدعم المعاينة بـ `--dry-run`
- لا تعيد تحميل الملفات الموجودة بالفعل

## التشغيل على ويندوز

1. ثبّت Python من https://www.python.org/downloads/ وفعّل خيار Add python.exe to PATH.
2. نزّل المشروع وفك الضغط.
3. افتح الملف `run.bat` بالنوت باد وعدّل الرابط في هذا السطر:

```bat
set "URL=https://github.com/storytold"
```

4. اضغط دبل كليك على `run.bat`، والملفات هتنزل في فولدر `downloads`.

ممكن كمان تكتب الرابط مباشرة:

```bat
run.bat https://github.com/some-user
```

## التشغيل من سطر الأوامر

```bash
python get_latest.py https://github.com/storytold
python get_latest.py https://github.com/storytold --dry-run
```

## أهم الخيارات

| الخيار | الوظيفة |
| --- | --- |
| `--dry-run` | يعرض ما سيتم تحميله بدون تحميل |
| `--dir` | فولدر الحفظ |
| `--no-forks` | تجاهل المشاريع المنسوخة |
| `--include` / `--exclude` | فلترة المشاريع بالاسم (regex) |
| `--prefer zip,exe` | تحديد نوع الملف المفضل |
| `--source-fallback` | تحميل السورس لو مفيش ملف مناسب |

القائمة الكاملة في [README.md](README.md).

## حد GitHub للطلبات

بدون Token الحد هو 60 طلب في الساعة. لو ظهرت رسالة rate limit، أنشئ Token وعرّف المتغير `GITHUB_TOKEN`:

```bat
set GITHUB_TOKEN=ghp_xxxxxxxx
```

## تنبيه أمان

الأداة تحمّل ملفات تنفيذية من المشاريع التي تحددها، فاستخدمها مع مصادر تثق فيها وراجع نتيجة `--dry-run` أولاً.

## الرخصة

MIT
