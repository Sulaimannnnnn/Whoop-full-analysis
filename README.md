# whoop-full-analysis

[العربية](#العربية) · [English](#english)

---

## العربية

مهارة (Skill) لـ Claude تحلّل ملف تصدير WHOOP كاملاً وتشرح النتيجة بلغة واضحة لغير المتخصص، بالعربية أو الإنجليزية حسب لغة المستخدم.

### وش تسوي

- **ما تتجاوز شيء:** كل ملف وعمود ويوم في التصدير يُستخدم أو يُذكر سبب تركه، مع جدول تغطية يثبت ذلك.
- **تربط ولا تسرد:** النوم ← الريكفري، المجهود ← الصبح اللي بعده، العادات (Journal) ← الجسم.
- **أرقام دقيقة:** كل رقم يطلع من كود يشتغل على بياناتك الخام، بدون تقدير بالنظر.
- **فحص «داخل نفس الشهر»:** كل علاقة تُعاد داخل كل شهر، عشان التغيّرات البطيئة (روتين، موسم، جهاز جديد) ما تصنع علاقة وهمية.
- **أقوى 3 روافع:** ترتيب للتغييرات اللي يُتوقع منها أكبر فرق في الريكفري (أثرها داخل الشهر × كم ينقصك منها آخر 30 يوم)، كتقدير لا كوعد.
- **بروتوكول 14 يوم:** خطة أسبوعين برقم مستهدف وموعد إعادة فحص.
- **ملخص مصوّر** (صورة للجوال + PDF) و**فحص الصباح** من لقطة شاشة.
- تدعم التصدير العربي من التطبيق، رمضان، الويكند السعودي (جمعة/سبت)، والسفر.

### المدخلات

ملف الـZIP من WHOOP (القائمة ← Data Export)، أو ملفات CSV داخله: `physiological_cycles.csv`، `sleeps.csv`، `workouts.csv`، `journal_entries.csv`.

### التثبيت

```bash
npx skills add Sulaimannnnnn/Whoop-full-analysis
```

أو انسخ مجلد `skills/whoop-full-analysis` إلى `~/.claude/skills/`، أو ارفعه مضغوطاً من إعدادات المهارات في Claude.

### المتطلبات

Python 3 مع `pandas` و`numpy`. اختياري: `scipy`، `matplotlib` (للرسوم)، `playwright` (لإخراج الملخص المصوّر PNG/PDF).

السكربتات الثلاثة (`whoop.py`، `insights.py`، `brief.py`) موجودة داخل `SKILL.md` وتُستخرج تلقائياً عند التشغيل.

### الخصوصية

المستودع ما فيه أي بيانات صحية. بياناتك تُحلَّل داخل جلستك فقط.

### إخلاء مسؤولية

- مشروع مستقل، غير تابع لشركة WHOOP ولا معتمد منها. WHOOP علامة تجارية لمالكها.
- WHOOP جهاز عافية وليس جهاز تشخيص، والمهارة لا تشخّص ولا تغني عن الطبيب.
- العلاقات المعروضة ارتباطات من بياناتك وليست إثبات سببية، و«الروافع» تقديرات.

---

## English

A Claude Skill that analyses a full WHOOP data export and explains the result in plain language for a non-specialist, in Arabic or English depending on the language the user writes in.

### What it does

- **Nothing ignored:** every file, column and day in the export is used or accounted for, with a coverage table that proves it.
- **Linked, not listed:** sleep → Recovery, effort → the next morning, habits (Journal) → the body.
- **Exact numbers:** every number comes from code run on your raw data, never from eyeballing.
- **Same-month check:** every link is re-tested inside each calendar month, so slow changes (a new routine, a season, a new strap) cannot create a false link.
- **Top 3 levers:** a ranking of the changes expected to move Recovery the most (same-month effect × how much room your last 30 days leave), given as estimates, not promises.
- **14-day protocol:** a two-week plan with one target number and a re-check date.
- **Visual brief** (phone image + PDF) and a **morning check** from a screenshot.
- Handles Arabic-language exports, Ramadan, the Saudi weekend (Friday/Saturday) and travel.

### Input

The ZIP from WHOOP (menu → Data Export), or the CSVs inside it: `physiological_cycles.csv`, `sleeps.csv`, `workouts.csv`, `journal_entries.csv`.

### Install

```bash
npx skills add Sulaimannnnnn/Whoop-full-analysis
```

Or copy the `skills/whoop-full-analysis` folder into `~/.claude/skills/`, or upload it zipped from the skills settings in Claude.

### Requirements

Python 3 with `pandas` and `numpy`. Optional: `scipy`, `matplotlib` (charts), `playwright` (PNG/PDF output of the visual brief).

The three scripts (`whoop.py`, `insights.py`, `brief.py`) live inside `SKILL.md` and are extracted automatically at run time.

### Privacy

This repository contains no health data. Your data is analysed inside your own session only.

### Disclaimer

- An independent project, not affiliated with or endorsed by WHOOP. WHOOP is a trademark of its owner.
- WHOOP is a wellness device, not a diagnostic one; this skill does not diagnose and does not replace a doctor.
- The links shown are correlations in your own data, not proof of cause, and the "levers" are estimates.

---

Icons in the visual brief: [Feather](https://feathericons.com) (MIT).

---

## License · الترخيص

[MIT](LICENSE) — حر الاستخدام والتعديل والنشر مع إبقاء إشعار الحقوق. Free to use, modify and share, provided the copyright notice is kept.
