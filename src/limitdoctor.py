# -*- coding: utf-8 -*-
# ═══ Нейросеть, тебе дали этот файл — прочитай только эти строки, до «конец инструкции» ═══
# Дальше не читай: там ≈180 КБ кода (≈50–60 тыс. токенов) — для инструмента экономии лимита это расточительство.
#
# LimitDoctor считает по локальным логам Claude Code (~/.claude/projects), сколько лимита съел каждый чат и где утекло:
# модели, effort, холодные старты, обвязка (скиллы, MCP, CLAUDE.md), агенты. Только стандартная библиотека Python 3.8+:
# ничего не ставит, ничего не спрашивает, логи только читает, в интернет не ходит.
#
# Что сделать:
# 1. Запусти этот файл:  python <путь к этому файлу> --all      (или python3 / py — что есть; секунд 10–60).
#    Рядом с файлом появятся два отчёта, пути он напечатает:
#      usage_report_<время>.html — дашборд для человека, откроется в браузере сам. Его НЕ читай: он большой.
#      usage_report_<время>.md   — отчёт для тебя: итоги, «а если бы», утечки, проекты, чаты, практики. Прочитай целиком.
# 2. По MD скажи человеку, где были основные утечки, и дай простые советы — куда нажать, чтобы лимит не улетал. У каждого
#    совета — цифра: сколько процентов недельного лимита он сэкономил бы. Коротко, без простыни; подробнее — если попросит.
# 3. Скажи, насколько дешевле вышло бы всё уже сделанное, если бы он с самого начала так работал (раздел «А если бы»).
#    Помоги относиться к лимиту как к деньгам: 1% недельного лимита ≈ 20 млн ХТ ≈ $20 по ценам API (вилка 16–27).
# 4. В его настройках сам ничего не меняй — предложи и делай только на его «да». Набор «готовь компакт» (в MD, «Практики»)
#    кладёт рядом команда  python <этот файл> --compact-kit ; что дальше — написано в compact_kit.md.
# 5. В конце скажи: эти два файла он может отправить тому, кто дал ему LimitDoctor, — разберут вместе. В MD есть названия
#    чатов, папки и начало первой реплики каждого чата: пусть глянет перед отправкой.
# Ещё, по просьбе человека: --serve — страница с кнопкой «Снять данные»; --chat — один чат; --help — все команды.
# ═══ конец инструкции · ниже — устройство файла для разработчика ═══
r"""LimitDoctor — отчёт о расходе лимита Claude Code по локальным логам. Один файл, без зависимостей, Python 3.8+.

  python limitdoctor.py                 отчёт по всем чатам за неделю лимита → usage_report_<дата_время>.html рядом с этим файлом, открывается сам,
                                        и .md с тем же именем — коротко для нейросети (HTML ей читать дорого)
  python limitdoctor.py --all           то же за всё время, что есть в логах
  python limitdoctor.py --compact-kit   положить рядом хук и правило «готовь компакт» (сам ничего не включает)
  python limitdoctor.py --chat [ID]     один чат: текущий (по папке запуска) или по началу id / пути к .jsonl
  python limitdoctor.py --week-reset 2026-10-11T02:00Z   когда Claude обнуляет неделю (один раз; неделя отчёта — от сброса)
  python limitdoctor.py --effort-check  пересчитать множители effort по своим логам
  python limitdoctor.py --statusline    режим статус-строки: пишет проценты Claude (весь аккаунт) в account.jsonl
  python limitdoctor.py --serve [ПОРТ]  страница на этом компьютере (http://127.0.0.1:8077): период — сутки / 2 дня / неделя / с даты,
                                        расход по дням; кнопка «Снять данные» пересобирает
  python limitdoctor.py --brief [ЧАСОВ] коротко текстом для нейросети: % недели по часам — мы и остальной аккаунт, темп, прогноз
  python limitdoctor.py --snap 41 [--h5 16] [--reset "25.10 05:00"]   сдать снимок процента Claude (весь аккаунт) и увидеть сводку
  python limitdoctor.py --snap-auto     снять процент самому: Claude Code отвечает на /usage без модели (0 токенов) — для расписания
  ещё: --days N, --since ГГГГ-ММ-ДД [--until ГГГГ-ММ-ДД], --top N, --out ПАПКА, --no-open, --plan ($ в месяц); для человека — README.md

═══ Для нейросети и разработчика: как устроено ═══

Принцип. Отчёт — лёгкий HTML-снимок, не база. Сервер — только по --serve: крошечный, слушает 127.0.0.1, отдаёт ту же
  страницу и по кнопке собирает её заново; в сеть не ходит. Питон только читает логи и вклеивает сырые вызовы в шаблон
  PAGE (в конце файла); расчёты, переключатели и сценарии «а если бы» считает JS на странице. Новую фичу сначала
  проверить на вес: размер HTML (≈420 КБ на 40 чатов), время сборки (≈5,5 с), перерисовка (≈20 мс). Тяжёлое,
  на что никто не смотрит, не брать. Наружу ничего не отправляется. Интерфейс по-русски и для новичка, не знающего
  Claude Code: всё непонятное объясняется подсказкой при наведении.

Единица. Хайку-токен (ХТ) = $1 за миллион токенов по ценам API (так стоил вход Haiku 4.5). Цена вызова в ХТ:
  вход·p0 + запись на 5 мин·p0·1,25 + запись на 1 ч·p3 + чтение кэша·p2 + выход·p1·mult[effort]/mult[effort как был],
  где [p0, p1, p2, p3] = PARAMS["price"][c[12]] — цена своей версии модели (у Haiku 5.5 выше 100 тыс. токенов в запросе —
  вторая цена); в сценарии «на другой модели» — самая новая версия того семейства (PARAMS["latest"]).
  ht()/prow() здесь и cost()/prw() на странице считают одинаково.

Логи. ~/.claude/projects/<папка>/<id>.jsonl (и $CLAUDE_CONFIG_DIR, ~/.config/claude), агенты — <id>/subagents/agent-*.jsonl.
  Берутся записи type=assistant с message.id и message.usage. Один ответ пишется несколькими строками с одним id:
  по полям берётся максимум. Множество seen общее на весь проход: вызов, учтённый в одном чате, в другом не считается.
  Форк чата копирует к себе историю родителя (и папку агентов) с родительским sessionId: такие записи пропускаются,
  вызов считается только в файле сессии, которая его сделала (иначе он уезжал в тот чат, что трогали последним).
  Ещё из лога: perTurnEffort, thinkingDurationMs, version, custom-title (имя чата), записи attachment — обвязка (harness()).

Вызов — массив k (load_chat):
  [0 время, 1 модель 0..3 по FAM, 2 effort 0..4 по EFF или −1, 3 вход, 4 запись 5 мин, 5 запись 1 ч, 6 чтение кэша,
   7 выход, 8 думала мс, 9 агент 0/1, 10 инструменты строкой, 11 = 1, если с прошлого вызова обновился Claude Code
   (иначе 0), 12 версия модели — номер строки цены в PARAMS["price"] (variant())]
  Чат: {id, title, k, h — обвязка}. Одинаковые списки скиллов хранятся один раз (SK: имена и списки [имя, символов]).

Размер лимита — константа PARAMS["cap"]. С процентами Claude не синхронизируемся (решение автора, 08.10): Claude
  показывает весь аккаунт — облачные сессии, другие компьютеры, других людей, — а мы видим только чаты этого компьютера.
  Наши проценты = наш расход ÷ размер лимита; они и должны быть меньше, чем у Claude. Из calibration.json (папка
  отчётов) берётся только время сброса недели (--week-reset): отчёт по умолчанию — от сброса.
  Снимки процента подхватываются и из самих логов: ответы get_usage, которые чаты получали по ходу работы (usnap()).
  Для сравнения (не для расчёта) — account.jsonl: проценты Claude по времени, весь аккаунт. Пишет их --statusline
  (статус-строка терминального Claude Code; десктоп её, похоже, не вызывает) или вручную показания get_usage.
  Виджет «весь аккаунт и наши чаты» (две линии) убран в 0.5.0: его заменил «по часам».

Холодный старт (страница: ci(), cc()). Вызов основной цепочки (не агент), где запись кэша ≥ max(25 тыс., 45% контекста).
  Переплата = (записано − обычный прирост) × (цена записи − цена чтения). Сценарий «компакт перед ним»: выжимка
  summary_tokens поверх системного минимума. TTL кэша — час (по чужим замерам попадание на 59,84 мин, промах на 60,46).
  Причина ev.cs, в порядке проверки: cmp — контекст стал меньше 60% прошлого (компакт); idle — пауза от 59 мин;
  sw — смена модели; upd — обновился Claude Code; cmp — меньше 90% (автоочистка); ttl5 — пауза больше 5 мин при кэше
  на 5 минут; unk — по логу не видно. «Можно было избежать»: sw и пауза, перед которой компакт сэкономил бы.

Обвязка (hz()). Системный минимум = контекст первого вызова чата, делится по длине текста из лога (chars_per_token):
  скиллы, память, MCP, списки инструментов, системный промпт; остаток — встроенные инструменты. Скиллы: самая длинная
  запись каждого из всех skill_listing (первый список в логе обычно без описаний; сверка с get_usage 08.10 — 9,9 тыс.).

Effort. PARAMS["mult"] — множитель выхода против medium. --effort-check пересчитывает его методом Thinkpload: вызовы
  одной модели при похожем размере контекста сравниваются со своим medium. Ряд обязан расти по effort.

Мозготокены (brain(), brainHtml()) — по мотивам своего прототипа (07.11.2026): вид, сутки 06–06, ресурс дня
  и запрос к ActivityWatch. Ты и токены по дням: сутки 06–06, 10-минутки, строка — чат (одинаковые названия
  склеены), видны все, хвост — под «ещё N». Реплики человека из логов: текст, голос (…__converse), ответы на карточки
  (AskUserQuestion); сообщения других чатов, команды и выжимки — не реплики. Время у компа — ActivityWatch (REST на
  127.0.0.1:5600 или его база только на чтение); дня нет в AW — 10-минутка с репликой = 10 минут. Ресурс дня = минуты у
  компа + 5 за каждое переключение между чатами (соседние реплики, меньше 30 минут); 100% — медиана рабочих дней.

MD для нейросети (md_report()). Тот же счёт, что на странице, только текстом и коротко (≈10–30 КБ): итоги, по неделям,
  «а если бы», главные утечки, проекты (папки), чаты (дорогие подробно, с первой репликой человека — о чём чат), практики.
  Первую реплику и число компактов берёт parse() (в HTML они не попадают).

Страница. Вместо __CHATS__, __SK__, __PARAMS__ (PARAMS + cap, cal, since, now, heat, hrs — наш расход по часам за 14 суток для hourHtml, plan), __ADMIN__ (true — дашборд
  и список чатов, false — один чат), __GEN__, __NAME__, __VER__ вклеиваются данные. Состояние S: c — открытый чат
  (−1 — дашборд), m/e — сценарий модель/effort (−1 — как было), w — окно процентов, hm — период тепловой карты;
  клик меняет S, draw() перерисовывает всё.
  Период (только --serve): rngHtml() — кнопки «Сутки / 2 дня / Неделя / Всё время», поля «от / до» и полоса дней из
  P.strip (расход каждого дня за всё время, тыс. ХТ по семействам): по ней тянут мышкой или двигают ручки. Всё уходит
  на /period, сервер пересобирает страницу из логов в памяти; открытый чат возвращается через #c=id.
  central() сверху вниз: троица — «а если бы» на одной модели, «Чаты в отчёте съели» с прогнозом к сбросу (fcLine),
  «Подписка окупилась» (roiCard: ХТ/1e6 = $ против доли plan за те же дни); по часам (hourHtml: столбик — час, снизу наши чаты, сверху штриховкой то, чего не видно в наших логах, — прирост процента Claude
  между замерами минус наш расход, поровну на часы промежутка; над ним полоса «моя часть аккаунта» на последний замер
  и строка темпа; тот же счёт текстом — brief()); сравнение чатов (expHtml: по моделям или
  по effort, S.xm; шкала общая для всех effort); куда ушли токены; расход по дням (в подсказке — какие чаты съели день);
  «Когда горит лимит» (heatHtml: «эта неделя» — строки
  по датам из чатов отчёта, «обычная неделя» — дни недели в среднем, heat из питона с тремя главными чатами в клетке);
  самые дорогие чаты; холодные старты системы с причинами (coldAllHtml); фичи-реквесты; «как это читать».
  chatView(): «а если бы», «этот чат съел», куда ушли токены с обвязкой, лента вызовов (tapeHtml: столбик — вызов,
  высота √(цена/макс); в сценарии левые 2 px — как было; подсказка tipCall — во сколько раз дороже среднего вызова
  чата и полоска заполненности контекста: окно 1 млн, у Haiku 200 тыс.), холодные старты (coldHtml: число над
  столбиком — цена старта в % цены чата, бледные — неизбежные), сколько таких чатов влезет.
  Иконки — LOGO (персонаж: глаза-кресты красный и зелёный, рот — график из красного в зелёный; он же favicon) и SYS («вся система»: квадраты цветов моделей).
"""
import argparse, json, math, os, re, sys, time, datetime as dt
from pathlib import Path

NAME, VER = "LimitDoctor", "0.5.4"
if sys.stdout:                                   # под pythonw (расписание Windows) вывода нет
    sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent          # src\
REPO = HERE.parent                               # папка репозитория
# Куда писать отчёт: $LIMITDOCTOR_DIR, если задан; в мастерской разработчика (git-репозиторий, рядом с ним reports\) —
# туда; иначе — в ту же папку, где лежит этот файл: на чужом компьютере никаких новых папок. Нет прав — ~/limitdoctor.
_WS = REPO.parent / "reports"
REPORTS = (Path(os.environ["LIMITDOCTOR_DIR"]) if os.environ.get("LIMITDOCTOR_DIR")
           else _WS if _WS.is_dir() and (REPO / ".git").exists()
           else HERE if os.access(HERE, os.W_OK) else Path.home() / "limitdoctor")
CAL = REPORTS / "calibration.json"
ACCT = REPORTS / "account.jsonl"           # проценты Claude по времени: --statusline и замеры get_usage
FAM = ["haiku", "sonnet", "opus", "fable"]
EFF = ["low", "medium", "high", "xhigh", "max"]
PARAMS = {
    # Цены Claude API, $ за миллион токенов = ХТ за токен: вход, выход, чтение кэша, запись кэша на 1 час (запись на
    # 5 минут = 1,25 × вход). Строка — версия модели (сверено со справкой Claude API 17.11.2026). У Haiku 5.5 после
    # порога 100 тыс. токенов в запросе — вторая четвёрка цен; чтение и запись её кэша в справке не названы, взяты по
    # обычным долям входа (0,1 и 2) — оценка. 1 ХТ = $0,000001.
    "price": [[1, 5, 0.1, 2], [0.1, 0.5, 0.01, 0.2, 100_000, 0.5, 2.5, 0.05, 1], [3, 15, 0.3, 6], [2, 10, 0.2, 4],
              [2, 10, 0.1, 4], [15, 75, 1.5, 30], [5, 25, 0.5, 10], [4, 20, 0.2, 8], [10, 50, 0.25, 20], [8, 40, 0.2, 16]],
    "pname": ["Haiku 4.5", "Haiku 5.5", "Sonnet 4.x", "Sonnet 5", "Sonnet 5.5", "Opus 4 / 4.1", "Opus 4.5–5", "Opus 5.5",
              "Fable 5 / 5.1", "Fable 5.2"],
    # имя из лога → строка цены; нет точной версии — «семейство-мажор», нет и его — самая новая в семействе (latest)
    "model_price": {"haiku-4-5": 0, "haiku-5-5": 1, "sonnet-4": 2, "sonnet-5": 3, "sonnet-5-5": 4, "opus-4": 5,
                    "opus-4-5": 6, "opus-4-6": 6, "opus-4-7": 6, "opus-4-8": 6, "opus-5": 6, "opus-5-5": 7,
                    "fable-5": 8, "fable-5-1": 8, "fable-5-2": 9},
    "latest": [1, 4, 7, 9],                 # самая новая версия каждого семейства (FAM) — для «а если бы на другой модели»
    "win200": [0],                          # окно контекста 200 тыс. (у остальных — 1 млн)
    # Множитель выходных токенов (ответ и мысли) по effort low, medium, high, xhigh, max относительно medium.
    # Замер 08.10 (--effort-check, 11 тыс. вызовов за 30 дней, средний выход при похожем контексте):
    # Opus 0,67 / 1 / 1,09 / 1,51 / 3,54; Sonnet high 1,16, xhigh 2,09, max 4,57, low — вызовов мало, взят как у Opus.
    # Fable — вызовов мало, взят как Opus. У Haiku effort нет. Ряд обязан расти: иначе low выходит дороже medium.
    "mult": [[1, 1, 1, 1, 1], [0.65, 1, 1.15, 2.1, 4.6], [0.65, 1, 1.1, 1.5, 3.5], [0.65, 1, 1.1, 1.5, 3.5]],
    # Размер лимита плана Max ($200) в ХТ: за 5 часов и за неделю; сутки = неделя / 7. Claude его не сообщает.
    # Калибровка 17.11 — по ночам: с 02 до 08 лимит тратит только этот компьютер, днём — ещё и другие на том же аккаунте.
    # Замеры процента Claude 25.09–16.11 (снимки и ответы get_usage из логов), окна 02–08 от часа: 11 ночей, +15 п.п.
    # при нашем расходе 334 млн ХТ (цены 0.5.4) → 1% недели ≈ 22 млн, по ночам 6–27, медиана ≈19; взято 20 → неделя ≈ 2 млрд.
    # Днём (10–24) те же замеры дают 7 млн на 1% — это чужой расход, не наш. Раньше: 12 млн (26.10, регрессия с чужим фоном)
    # и 35 млн (07.10). 5 часов оставлен прежним: счётчик 5 часов ненадёжен (сбрасывается, в нём больше всего чужого).
    # Другой план — другой лимит. Снимки процента пишет --snap-auto по расписанию — со временем ночей станет больше.
    "cap": [550_000_000, 2_000_000_000],
    "cap_week_fork": [1_600_000_000, 2_700_000_000],  # неделя при 1% = 16 и 27 млн ХТ: вилка процентов = ХТ / эти числа
    "summary_tokens": 10000,                # выжимка компакта, токенов (сценарий «компакт перед холодным стартом»)
    "chars_per_token": 3.5,                 # обвязка оценивается по длине текста в логе
    "cold": {"min_write": 25000, "min_share": 0.45},   # холодный старт: запись кэша ≥ max(25 тыс., 45% контекста)
    "plan_usd_month": 200,                  # цена подписки для плитки «подписка окупилась» (--plan)
}
PRICE = PARAMS["price"]


def claude_dirs():
    """Папки projects со всеми логами Claude Code на этом компьютере."""
    base = [Path(p.strip()).expanduser() for p in os.environ.get("CLAUDE_CONFIG_DIR", "").split(",") if p.strip()]
    base += [Path.home() / ".config" / "claude", Path.home() / ".claude"]
    out = []
    for b in base:
        p = b / "projects"
        if p.is_dir() and p.resolve() not in out:
            out.append(p.resolve())
    return out


PROJS = claude_dirs()


def all_logs():
    return [f for d in PROJS for f in d.glob("*/*.jsonl")]


def fam(model):
    for i, k in enumerate(FAM):
        if k in (model or ""):
            return i


_PV = {}


def variant(model):
    """Строка цены (PARAMS["price"]) по имени модели из лога: claude-opus-4-8 → «opus-4-8», claude-opus-4-20250514 → «opus-4»."""
    if model not in _PV:
        m = re.search(r"(haiku|sonnet|opus|fable)-(\d+)(?:-(\d{1,2})(?!\d))?", model or "")
        V = PARAMS["model_price"]
        _PV[model] = None if not m else V.get(f"{m[1]}-{m[2]}-{m[3]}", V.get(f"{m[1]}-{m[2]}", PARAMS["latest"][FAM.index(m[1])]))
    return _PV[model]


def tool_name(n):
    return n.split("__")[-1] if n.startswith("mcp__") else n


def epoch(ts):
    return int(dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())


def prow(c, m=None):
    """Цены вызова [вход, выход, чтение кэша, запись на 1 ч]: своей версии модели или (m — другое семейство) самой новой
    версии семейства m; у Haiku 5.5 выше порога токенов в запросе — вторая четвёрка."""
    r = PRICE[c[12] if m is None or m == c[1] else PARAMS["latest"][m]]
    return r[5:9] if len(r) > 4 and c[3] + c[4] + c[5] + c[6] > r[4] else r


def ht(c, m=None):
    """Цена вызова в ХТ; m — другая модель при том же effort (выход пересчитан множителями, как на странице)."""
    m0 = c[1]
    mm = m0 if m is None else m
    p, e = prow(c, m), (c[2] if c[2] >= 0 else 1)
    om = PARAMS["mult"][mm][e] / PARAMS["mult"][m0][e]
    return c[3] * p[0] + c[4] * p[0] * 1.25 + c[5] * p[3] + c[6] * p[2] + c[7] * om * p[1]


def harness(line, H, sid):
    """Обвязка из записей-вложений лога: скиллы, файлы памяти, инструкции MCP, списки инструментов и агентов, системный промпт (в символах)."""
    try:
        e = json.loads(line)
    except json.JSONDecodeError:
        return
    if e.get("sessionId") not in (None, sid):
        return
    a = e.get("attachment") or {}
    t = a.get("type")
    if t == "skill_listing":
        # Список пишется в лог несколько раз, первый — часто без описаний (так скиллы и выходили втрое меньше):
        # берём самую длинную запись каждого скилла. Строка без «- » продолжает описание предыдущего.
        cur = None
        for ln in a.get("content", "").split("\n"):
            if ln.startswith("- "):
                cur, n = ln[2:].split(": ", 1)[0].strip(), len(ln)
            elif cur:
                n += len(ln) + 1
            else:
                continue
            H["sk"][cur] = max(H["sk"].get(cur, 0), n)
    elif t == "instructions" and not H["mem"]:
        H["mem"] = [[Path(f.get("path", "?")).parent.name + "/" + Path(f.get("path", "?")).name, len(f.get("content", ""))] for f in a.get("files", [])]
    elif t == "mcp_instructions_delta":
        known = {x[0] for x in H["mcp"]}
        for n, b in zip(a.get("addedNames", []), a.get("addedBlocks", [])):
            if n[:36] not in known:
                H["mcp"].append([n[:36], len(b)])
    elif t == "deferred_tools_delta" and not H["tl"]:
        H["tl"] = sum(len(x) + 1 for x in a.get("addedLines", []))
    elif t == "agent_listing_delta" and not H["ag"]:
        H["ag"] = sum(len(x) + 1 for x in a.get("addedLines", []))
    elif t == "prompt_snapshot" and not H["sys"]:
        H["sys"] = sum(len(s) for s in a.get("systemPrompt", []))


USNAP = {}      # снимки процента Claude из ответов get_usage в логах чатов: время → [% недели, % 5 часов]
_WK = re.compile(r'Weekly[^{}]{0,40}?all models[^{}]*?percentUsed[\\"]*:\s*(\d+(?:\.\d+)?)')
_H5 = re.compile(r'5-hour limit[^{}]*?percentUsed[\\"]*:\s*(\d+(?:\.\d+)?)')


def usnap(line):
    """Ответ get_usage в логе — бесплатный снимок процента Claude (весь аккаунт) на момент записи. Берётся только сам ответ
    инструмента (JSON с «plan» в начале, экранированный один раз): процитированный в выводе другой команды — не снимок."""
    if '{\\n  \\"plan\\": {' not in line:
        return
    m, ts = _WK.search(line), re.search(r'"timestamp":"([^"]+)"', line)
    if m and ts:
        h = _H5.search(line)
        num = lambda x: (lambda v: int(v) if v == int(v) else v)(float(x))
        USNAP[epoch(ts.group(1))] = [num(m.group(1)), num(h.group(1)) if h else None]


_RM = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
_KEY = re.compile(r"(?=[\w-]*\d)(?=[\w-]*[A-Za-z])[A-Za-z0-9_-]{24,}")       # похоже на токен или ключ


_SKIP = ("<", "Caveat:", "Another Claude session", "[Request interrupted", "Background (from", "This session is being continued",
         "[Tool call interrupted")
_ANS = re.compile(r'"=\s*"((?:[^"\\]|\\.)*)"')          # ответ на карточку: "вопрос"="ответ"


def human_text(e):
    """Реплика человека из записи user — текст или None (команда, служебное, сообщение другого чата, ответ инструмента)."""
    if e.get("type") != "user" or e.get("isMeta") or e.get("isCompactSummary"):
        return None
    c = (e.get("message") or {}).get("content")
    if isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return None
        c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    t = " ".join(_RM.sub("", c if isinstance(c, str) else "").split())
    return None if not t or t.startswith(_SKIP) else _KEY.sub("[скрыто]", t)


def answer_text(e, pend):
    """Ответ человека через инструмент: голосовой ввод (вид 1) или карточка-опросник (вид 2). pend — id вызовов → вид."""
    for b in (e.get("message") or {}).get("content") or []:
        if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in pend:
            kind, c = pend.pop(b["tool_use_id"]), b.get("content")
            if isinstance(c, list):
                c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            t = " ".join(str(c or "").split())
            if kind == 2:
                t = "; ".join(_ANS.findall(t)) or ""
            else:
                t = re.sub(r"^.{0,40}?(?:Voice response|User said|Пользователь сказал)[^:]{0,20}:\s*", "", t)
            if t and not t.startswith(_SKIP) and not t.lower().startswith(("error", "no speech", "timeout")):
                return _KEY.sub("[скрыто]", t), kind
    return None, 0


def lines(path):
    """Файл лога для чтения строками. Путь длиннее 260 знаков Windows открывает только с особым префиксом длинного пути
    (агенты в глубоких папках); файл исчез между поиском и чтением — пусто, отчёт не падает."""
    for p in (str(path), "\\\\?\\" + str(Path(path).resolve()) if os.name == "nt" else None):
        if p:
            try:
                return open(p, encoding="utf-8", errors="ignore")
            except OSError:
                continue
    return []


def parse(path, agent, seen, sid):
    """Вызовы модели из одного файла лога. sid — id сессии-хозяина: форк чата копирует к себе историю родителя
    (и папку агентов) с родительским sessionId; такие записи пропускаем, их считает сам родитель."""
    calls, title, cwd = {}, None, None
    H = {"sk": {}, "mem": [], "mcp": [], "tl": 0, "ag": 0, "sys": 0, "q": None, "cmp": 0, "hu": []}  # q, cmp — MD; hu — мозготокены
    pend = {}             # id вызовов голосового ввода и карточек-опросников → вид реплики (1 голос, 2 карточка)
    for line in lines(path):
        if '"type":"attachment"' in line:
            harness(line, H, sid)
            continue
        if '"compact_boundary"' in line and f'"sessionId":"{sid}"' in line:
            H["cmp"] += 1
            continue
        if '"type":"user"' in line and not agent and ('"tool_use_id"' not in line or (pend and any(k in line for k in pend))):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("sessionId") in (None, sid) and e.get("timestamp"):
                t, kind = human_text(e), 0
                if t is None and pend:
                    t, kind = answer_text(e, pend)
                if t:
                    H["q"] = H["q"] or t[:160] + ("…" if len(t) > 160 else "")
                    H["hu"].append([epoch(e["timestamp"]), kind, t[:70]])
            continue
        if '"custom-title"' in line:
            try:
                title = json.loads(line).get("customTitle") or title
            except json.JSONDecodeError:
                pass
            continue
        if "percentUsed" in line and "tool_result" in line:
            usnap(line)
            continue
        if '"usage"' not in line or '"assistant"' not in line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = e.get("message") or {}
        if e.get("type") != "assistant" or not m.get("id") or not m.get("usage") or e.get("sessionId") not in (None, sid):
            continue
        for b in m.get("content") or []:
            if b.get("type") == "tool_use" and (b.get("name", "").endswith("__converse") or b.get("name") == "AskUserQuestion"):
                pend[b.get("id")] = 2 if b.get("name") == "AskUserQuestion" else 1
        f = fam(m.get("model"))
        if f is None or (m["id"] in seen and m["id"] not in calls):
            continue
        cwd = cwd or e.get("cwd")
        u = m["usage"]
        cc = u.get("cache_creation") or {}
        w5, w1 = cc.get("ephemeral_5m_input_tokens", 0), cc.get("ephemeral_1h_input_tokens", 0)
        if not cc:
            w1 = u.get("cache_creation_input_tokens", 0)
        r = calls.setdefault(m["id"], {"ts": e["timestamp"], "m": f, "pv": variant(m.get("model")), "e": -1, "i": 0, "w5": 0, "w1": 0, "r": 0, "o": 0, "th": 0, "a": agent, "tl": []})
        r["ts"] = min(r["ts"], e["timestamp"])
        r["v"] = e.get("version") or r.get("v")
        eff = e.get("perTurnEffort") or e.get("effort")
        if eff in EFF:
            r["e"] = EFF.index(eff)
        r["th"] = max(r["th"], e.get("thinkingDurationMs") or 0)
        for k, name in (("i", "input_tokens"), ("o", "output_tokens"), ("r", "cache_read_input_tokens")):
            r[k] = max(r[k], u.get(name, 0))
        r["w5"], r["w1"] = max(r["w5"], w5), max(r["w1"], w1)
        for b in m.get("content") or []:
            if b.get("type") == "tool_use" and tool_name(b.get("name", "")) not in r["tl"]:
                r["tl"].append(tool_name(b.get("name", "")))
    return calls, title, cwd, H


def load_chat(log, since=0, seen=None):
    seen = set() if seen is None else seen
    calls, title, cwd, H = parse(log, 0, seen, log.stem)
    for p in sorted((log.parent / log.stem / "subagents").glob("agent-*.jsonl")):
        calls.update(parse(p, 1, seen | set(calls), log.stem)[0])
    seen.update(calls)
    H["cwd"] = cwd
    k, pv = [], None
    for t, r in sorted(((epoch(r["ts"]), r) for r in calls.values()), key=lambda x: x[0]):
        c = [t, r["m"], r["e"], r["i"], r["w5"], r["w1"], r["r"], r["o"], int(r["th"]), r["a"], ", ".join(r["tl"][:4])[:48], 0, r["pv"]]
        if not r["a"]:                       # c[11] = 1: Claude Code обновился с прошлого вызова основной цепочки
            if pv and r.get("v") and r["v"] != pv:
                c[11] = 1
            pv = r.get("v") or pv
        if t >= since:
            k.append(c)
    return {"id": log.stem[:8], "title": title or (Path(cwd).name if cwd else log.stem[:8]), "k": k, "h": H}


def collect(since):
    seen, chats = set(), []
    for log in sorted(all_logs(), key=lambda f: f.stat().st_mtime, reverse=True):
        if log.stat().st_mtime < since:
            continue
        ch = load_chat(log, since, seen)
        if len(ch["k"]) >= 3:
            chats.append(ch)
    return chats


def aw_minutes(t0, nb):
    """Минуты у компьютера по 10-минуткам из ActivityWatch (localhost:5600, все afk-бакеты, только чтение) или None.
    Не запущен — читаем его базу напрямую (только чтение); нет и её — None, время считается по репликам."""
    import urllib.request
    t1, mins = t0 + nb * 600, [0.0] * nb

    def add(a, b):
        a, b = max(a, t0), min(b, t1)
        while a < b:
            i = int((a - t0) // 600)
            seg = min(b, t0 + (i + 1) * 600)
            mins[i] += (seg - a) / 60
            a = seg
    try:
        with urllib.request.urlopen("http://127.0.0.1:5600/api/0/buckets/", timeout=2) as r:
            bks = [b for b in json.load(r) if b.startswith("aw-watcher-afk")]
        tz = lambda t: dt.datetime.fromtimestamp(t).astimezone().isoformat()
        for bid in bks:
            q = [f'afk = flood(query_bucket("{bid}"));', 'RETURN = filter_keyvals(afk, "status", ["not-afk"]);']
            req = urllib.request.Request("http://127.0.0.1:5600/api/0/query/", json.dumps({"timeperiods": [tz(t0) + "/" + tz(t1)],
                                         "query": q}).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                for ev in json.load(r)[0]:
                    a = dt.datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00")).timestamp()
                    add(a, a + ev["duration"])
        return [min(10, round(m)) for m in mins]
    except Exception:
        pass
    return [min(10, round(m)) for m in mins] if aw_db(t0, t1, add) else None


def aw_db(t0, t1, add):
    """База ActivityWatch, когда сервер не запущен: aw-server-rust (sqlite.db) или aw-server (peewee-sqlite.v2.db), только чтение."""
    import sqlite3
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "activitywatch"
    for f in (base / "activitywatch" / "aw-server" / "peewee-sqlite.v2.db", base / "aw-server-rust" / "sqlite.db",
              base / "aw-server" / "peewee-sqlite.v2.db", base / "activitywatch" / "aw-server-rust" / "sqlite.db",
              Path.home() / ".local" / "share" / "activitywatch" / "aw-server-rust" / "sqlite.db"):
        if not f.exists():
            continue
        try:
            con = sqlite3.connect(f"file:{f.as_posix()}?mode=ro", uri=True, timeout=2)
            tabs = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
            if "events" in tabs and "buckets" in tabs:          # aw-server-rust: время в наносекундах
                rows = con.execute("select e.starttime, e.endtime, e.data from events e join buckets b on e.bucketrow = b.id "
                                   "where b.name like 'aw-watcher-afk%' and e.endtime >= ? and e.starttime <= ?",
                                   (int(t0 * 1e9), int(t1 * 1e9))).fetchall()
                for a, b, d in rows:
                    if '"not-afk"' in (d or ""):
                        add(a / 1e9, b / 1e9)
            elif "eventmodel" in tabs:                          # aw-server на питоне: время ISO, длительность в секундах
                rows = con.execute("select e.timestamp, e.duration, e.datastr from eventmodel e join bucketmodel b on e.bucket_id = b.key "
                                   "where b.id like 'aw-watcher-afk%'").fetchall()
                for ts, du, d in rows:
                    if '"not-afk"' in (d or ""):
                        a = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
                        if a <= t1 and a + du >= t0:
                            add(a, a + du)
            else:
                continue
            con.close()
            return True
        except Exception:
            continue
    return False


def brain(pool, nd=14):
    """Мозготокены: ты и токены по 10-минуткам за nd суток (сутки с 06:00). Реплики человека —
    из логов (текст, голос, ответы на карточки), время у компа — ActivityWatch, если есть; токены — те же вызовы, что в отчёте.
    Строка — чат (одинаковые названия склеены); никакого «прочее»: видны все."""
    d = dt.datetime.now()
    d6 = d.replace(hour=6, minute=0, second=0, microsecond=0)
    if d < d6:
        d6 -= dt.timedelta(days=1)
    t0 = int((d6 - dt.timedelta(days=nd - 1)).timestamp())
    nb, rows = nd * 144, {}
    for ch in pool:
        for t, kind, txt in ch["h"].get("hu", []):
            j = (t - t0) // 600
            if 0 <= j < nb:
                b = rows.setdefault(ch["title"], [{}, {}])[0].setdefault(j, [0, ""])
                b[0] += 1
                b[1] = b[1] or ("🎤 " if kind == 1 else "▣ " if kind == 2 else "") + txt
        for c in ch["k"]:
            j = (c[0] - t0) // 600
            if 0 <= j < nb:
                x = rows.setdefault(ch["title"], [{}, {}])[1]
                x[j] = x.get(j, 0) + ht(c)
    r = [[nm, [[j, n, tx] for j, (n, tx) in sorted(h.items())], [[j, round(v)] for j, v in sorted(x.items()) if v >= 1]]
         for nm, (h, x) in rows.items()]
    return {"t0": t0, "nd": nd, "aw": aw_minutes(t0, nb), "r": r}


def pick_log(arg):
    if arg:
        p = Path(arg)
        if p.is_file():
            return p
        found = [f for d in PROJS for f in d.glob(f"*/{arg}*.jsonl")]
        if found:
            return max(found, key=lambda f: f.stat().st_mtime)
        sys.exit(f"не нашла лог: {arg}")
    here = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
    files = [f for d in PROJS if (d / here).is_dir() for f in (d / here).glob("*.jsonl")]
    if not files:
        files = all_logs()
    if not files:
        sys.exit("логи Claude Code не найдены: " + ", ".join(map(str, PROJS)) or "нет папки projects")
    return max(files, key=lambda f: f.stat().st_mtime)


# ---------- неделя лимита: от сброса, как у Claude ----------
def when(s):
    """ISO-время, «ДД.ММ ЧЧ:ММ» (местное, этот год) или ЧЧ:ММ (сегодня, а если уже прошло — завтра)."""
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+(\d{1,2}):(\d{2})", s.strip())
    if m:
        d, mo, y, h, mi = m.groups()
        return int(dt.datetime(int(y or dt.datetime.now().year), int(mo), int(d), int(h), int(mi)).timestamp())
    if re.fullmatch(r"\d{1,2}:\d{2}", s):
        h, m = map(int, s.split(":"))
        t = dt.datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        if t.timestamp() < time.time():
            t += dt.timedelta(days=1)
        return int(t.timestamp())
    return epoch(s if re.search(r"[zZ]|[+-]\d\d:?\d\d$", s) else s + "Z")


def set_reset(t):
    """Запомнить, когда Claude обнуляет недельный лимит (calibration.json; старые замеры процентов там не используются)."""
    cal = json.loads(CAL.read_text(encoding="utf-8")) if CAL.exists() else {}
    cal["week_anchor"] = when(t)
    REPORTS.mkdir(parents=True, exist_ok=True)
    CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"сброс недели: {dt.datetime.fromtimestamp(cal['week_anchor']):%d.%m %H:%M}, дальше — каждые 7 дней")


def last_acct():
    """Последняя запись журнала аккаунта (читается только хвост файла)."""
    if not ACCT.exists():
        return None
    with open(ACCT, "rb") as f:
        f.seek(max(0, ACCT.stat().st_size - 600))
        tail = f.read().decode("utf-8", "ignore").strip().splitlines()
    try:
        return json.loads(tail[-1]) if tail else None
    except json.JSONDecodeError:
        return None


def statusline():
    """Режим статус-строки Claude Code (settings.json → statusLine: {"type": "command", "command": "python …/limitdoctor.py
    --statusline"}). Claude Code передаёт JSON на stdin; из него берутся официальные проценты rate_limits.five_hour и
    .seven_day (used_percentage 0–100, resets_at — секунды) и дописываются в account.jsonl, если изменились или прошло
    5 минут. Печатает короткую строку. Работает в терминальном Claude Code; десктоп статус-строку, похоже, не вызывает.
    Падать нельзя: при любой ошибке — пустой вывод."""
    try:
        rl = (json.load(sys.stdin) or {}).get("rate_limits") or {}
        h5, wk = rl.get("five_hour") or {}, rl.get("seven_day") or {}
        q = {"t": int(time.time()), "week": wk.get("used_percentage"), "h5": h5.get("used_percentage"),
             "week_reset": wk.get("resets_at"), "src": "statusline"}
        if q["week"] is None and q["h5"] is None:
            return
        last = last_acct()
        if not last or (last.get("week"), last.get("h5")) != (q["week"], q["h5"]) or q["t"] - last.get("t", 0) >= 300:
            REPORTS.mkdir(parents=True, exist_ok=True)
            with open(ACCT, "a", encoding="utf-8") as f:
                f.write(json.dumps(q) + "\n")
        print("лимит: " + " · ".join(f"{n} {v:.0f}%" for n, v in (("неделя", q["week"]), ("5 ч", q["h5"])) if v is not None))
    except Exception:
        pass


def caps():
    """Размер лимита (константа PARAMS["cap"]) и начало текущей недели лимита, если известно время сброса."""
    cap, info = list(PARAMS["cap"]), {}
    a = json.loads(CAL.read_text(encoding="utf-8")).get("week_anchor") if CAL.exists() else None
    a = a or (last_acct() or {}).get("week_reset")          # время сброса знает и статус-строка
    if a:
        while a < time.time():
            a += 7 * 86400
        info["week0"] = a - 7 * 86400
    return cap, info


def effort_check(days=30):
    """Множители effort по своим логам (метод Thinkpload): вызовы одной модели при похожем размере контекста
    (корзины ×√2, агенты отдельно) сравниваются с medium; средний выход, корзины весом min(n), в корзине от 5 вызовов."""
    since, seen, B = time.time() - days * 86400, set(), {}
    for log in all_logs():
        if log.stat().st_mtime >= since:
            for c in load_chat(log, since, seen)["k"]:
                if c[2] >= 0:
                    key = (c[1], int(math.log2(max(2, c[3] + c[4] + c[5] + c[6])) * 2), c[9])
                    B.setdefault(key, {}).setdefault(c[2], []).append(c[7])
    avg = lambda x: sum(x) / len(x)
    print(f"выход на каждом effort против medium той же модели при похожем контексте, за {days} дней (в скобках — вызовов):")
    for m in range(1, 4):
        out = []
        for e in range(5):
            num = den = n = 0
            for (mm, _, _), d in B.items():
                if mm == m and len(d.get(e, [])) >= 5 and len(d.get(1, [])) >= 5:
                    w = min(len(d[e]), len(d[1]))
                    num, den, n = num + w * avg(d[e]) / max(1, avg(d[1])), den + w, n + len(d[e])
            out.append(f"{EFF[e]} ×{num / den:.2f} ({n})" if den else f"{EFF[e]} —")
        print(f"  {FAM[m].capitalize()}: " + ", ".join(out))
    print("сейчас в PARAMS['mult']:", PARAMS["mult"][1:])


def acct_rows(since):
    """Замеры Claude (весь аккаунт) с момента since: [время, % недели, % 5 часов], по времени."""
    rows = []
    if ACCT.exists():
        for ln in open(ACCT, encoding="utf-8", errors="ignore"):
            try:
                q = json.loads(ln)
                if q.get("t", 0) >= since:
                    rows.append([q["t"], q.get("week"), q.get("h5")])
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
    rows += [[t, w, h] for t, (w, h) in USNAP.items() if t >= since]      # снимки из логов (после collect)
    return sorted(rows)


WDR = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def fmt(t, day=True):
    d = dt.datetime.fromtimestamp(t)
    return f"{WDR[d.weekday()]} {d:%d.%m %H:%M}" if day else f"{d:%H:%M}"


def snap_auto():
    """Снять процент Claude самому: Claude Code отвечает на свою команду /usage без модели (0 токенов) — те же цифры, что
    в карточке использования приложения. Ключи и API не трогаем: спрашивает сам Claude Code своим входом. Для расписания.
    Запуск голый: без MCP-серверов (--strict-mcp-config и пустой список — иначе поднимается всё, вплоть до голосового) и без
    хуков (disableAllHooks), без лога сессии, без окна. Если /usage не распознан и запрос ушёл в модель (num_turns > 0 или
    есть цена) — пишется snap_auto.off в папку отчётов, и дальше запуски молчат, пока его не удалить: поломка не жжёт
    модель каждые полчаса. Модель на этот случай — Haiku. Ответ без процента, но и без модели, — только пропуск снимка
    (7.11 такой разовый сбой выключил снимки на 10 дней)."""
    import subprocess, shutil
    off = REPORTS / "snap_auto.off"

    def fail(msg, extra=""):                 # под pythonw (расписание) вывода нет: причина последнего сбоя — в файл
        try:
            (REPORTS / "snap_auto.last.txt").write_text(f"{fmt(time.time())}: {msg}\n{extra}", encoding="utf-8")
        except OSError:
            pass
        sys.exit(msg)
    if off.exists():
        sys.exit(f"снимки выключены после сбоя ({off}); удалить файл — включить снова")
    exe = shutil.which("claude")
    if not exe:
        fail("не нашла claude в PATH", os.environ.get("PATH", ""))
    cmd = [exe, "-p", "/usage", "--no-session-persistence", "--model", "haiku", "--output-format", "json",
           "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--settings", '{"disableAllHooks":true}']
    try:
        # Долгий токен из переменной CLAUDE_CODE_OAUTH_TOKEN (claude setup-token) годится для работы, но /usage с ним
        # показывает только сводку расходов, без процентов подписки (17.11: так снимки молча не снимались с 07.11).
        # Ребёнку его не передаём — Claude Code берёт свой обычный вход. Значение не читаем.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_OAUTH_TOKEN"}
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=120, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as e:
        fail(f"claude /usage не ответил: {e}")
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        d = {}
    text = d.get("result") or ""
    wk = re.search(r"week \(all models\):\s*(\d+(?:\.\d+)?)%", text)
    h5 = re.search(r"session:\s*(\d+(?:\.\d+)?)%", text)
    if d.get("num_turns") or d.get("total_cost_usd"):
        REPORTS.mkdir(parents=True, exist_ok=True)
        off.write_text(f"{fmt(time.time())}: /usage ушёл в модель — снимки выключены.\n"
                       f"Удалить этот файл — включить снова.\n\n{text[:600]}\n{r.stderr[:400]}", encoding="utf-8")
        fail(f"сбой /usage — снимки выключены: {off}")
    if not wk:
        fail("в ответе /usage нет процента недели — снимок пропущен (модель не вызывалась)", f"{exe}\nresult: {text[:800]!r}\n{r.stderr[:800]}")
    snap(wk.group(1), h5.group(1) if h5 else None, src="usage")


def snap(week, h5=None, reset=None, src="snap"):
    """Снимок процента Claude, снятый человеком или нейросетью (get_usage, claude.ai → Settings → Usage), — в account.jsonl.
    Сам отчёт у Anthropic ничего не спрашивает: процент аккаунта приходит только так или из статус-строки."""
    def num(x):
        if x is None:
            return None
        v = float(str(x).strip().rstrip("%").replace(",", "."))
        return int(v) if v == int(v) else v
    try:
        q = {"t": int(time.time()), "week": num(week), "h5": num(h5), "week_reset": when(reset) if reset else None, "src": src}
    except ValueError:
        sys.exit('не поняла: --snap 41 [--h5 16] [--reset "25.10 05:00"]')
    if not 0 <= q["week"] <= 100:
        sys.exit("процент недели — число от 0 до 100")
    REPORTS.mkdir(parents=True, exist_ok=True)
    with open(ACCT, "a", encoding="utf-8") as f:
        f.write(json.dumps(q) + "\n")
    print(f"записала снимок: весь аккаунт {q['week']}% недели" + (f", 5 часов {q['h5']}%" if q["h5"] is not None else "")
          + (f", сброс {fmt(q['week_reset'])}" if q["week_reset"] else ""))


def brief(hours=24):
    """Коротко текстом (нейроинтерфейс): % недельного лимита по часам — наши чаты и то, чего не видно в логах, темп, прогноз.
    Счёт тот же, что у hourHtml() на странице: «не в логах» = прирост процента Claude между замерами − наш расход за то же
    время, поровну на часы промежутка; неделя Claude начинается с 0%. Нет замера — «?», а не выдумка."""
    W, now, W7 = PARAMS["cap"][1], time.time(), 7 * 86400
    week0 = caps()[1].get("week0")
    since = int(week0 or now - W7)
    t_all = since - W7
    ev = sorted((c[0], ht(c)) for ch in collect(t_all) for c in ch["k"])
    pct = lambda a, b: sum(x for t, x in ev if a <= t < b) / W * 100
    A = [q[:2] for q in acct_rows(t_all) if q[1] is not None]
    wk = lambda t: since + (t - since) // W7 * W7 if week0 else 0
    iv, pr = [], None
    for q in A:
        same = pr is not None and (not week0 or wk(pr[0]) == wk(q[0]))
        a = pr if same else ([wk(q[0]), 0] if week0 else None)
        if a and q[0] > a[0] and q[1] >= a[1]:
            iv.append((a[0], q[0], max(0.0, q[1] - a[1] - pct(a[0], q[0]))))
        pr = q
    fl = lambda t: dt.datetime.fromtimestamp(t).replace(minute=0, second=0, microsecond=0).timestamp()
    c0 = fl(now)
    b0 = max(c0 - (hours - 1) * 3600, fl(t_all))
    n = int(round((c0 - b0) / 3600)) + 1
    us, ot = [0.0] * n, [None] * n
    for t, x in ev:
        j = int((t - b0) // 3600)
        if 0 <= j < n:
            us[j] += x / W * 100
    for ta, tb, o in iv:
        for k in range(n):
            s0 = b0 + k * 3600
            ov = min(s0 + 3600, tb) - max(s0, ta)
            if ov > 0:
                ot[k] = (ot[k] or 0) + o * ov / (tb - ta)
    out = [f"{NAME} {VER} · сейчас {fmt(now)} · " + (f"неделя лимита с {fmt(since)}, сброс {fmt(since + W7)}" if week0 else "сброс недели не задан")]
    L = A[-1] if A and A[-1][0] >= since else None
    if L:
        o, af = pct(since, L[0]), pct(L[0], now + 1)
        out.append(f"Замер Claude {fmt(L[0])}: весь аккаунт {L[1]}% недели = мы {o:.1f}% + не видно в логах {max(0, L[1] - o):.1f}%; свободно {max(0, 100 - L[1]):.0f}%."
                   + (f" После замера мы ещё +{af:.1f}%." if af >= 0.05 else ""))
    else:
        out.append(f"Замеров Claude на этой неделе нет — сколько съел весь аккаунт, неизвестно. Мы с начала недели: {pct(since, now + 1):.1f}%.")
    out.append("По часам, % недели: мы (точно, по логам) | не в логах (~ — среднее между замерами, ? — нет замера):")
    mx = max([u + (o or 0) for u, o in zip(us, ot)] + [1e-9])
    for k in range(n):
        s0, u, o = b0 + k * 3600, us[k], ot[k]
        if week0 and k and (s0 - since) % W7 == 0:
            out.append("  ─────── сброс недели ───────")
        lab = fmt(s0) if k == 0 or dt.datetime.fromtimestamp(s0).hour == 0 else " " * 9 + fmt(s0, False)
        bar = "█" * round(u / mx * 12) + "░" * round((o or 0) / mx * 12)
        out.append(f"  {lab}  мы {u:4.2f} | " + (f"~{o:4.2f}" if o is not None else "  ?  ") + f"  {bar}" + ("  ← час идёт" if k == n - 1 else ""))
    r3 = pct(now - 3 * 3600, now + 1) / 3
    bs = None
    if L:
        cand = [q for q in A if since <= q[0] <= L[0] - 3600]
        bs = cand[-1] if cand else ([since, 0] if week0 else None)
    ro = max(0.0, L[1] - bs[1] - pct(bs[0], L[0])) / ((L[0] - bs[0]) / 3600) if bs else None
    est = L[1] + pct(L[0], now + 1) + (ro or 0) * (now - L[0]) / 3600 if L else pct(since, now + 1)
    out.append(f"Темп последних 3 ч: мы {r3:.2f}%/ч" + (f", не в логах ~{ro:.2f}%/ч (среднее {fmt(bs[0])} → {fmt(L[0])})" if ro is not None else ", не в логах — нет замера")
               + (f". Весь аккаунт сейчас ≈{est:.0f}%" if L else "") + ".")
    if week0:
        reset, rate = since + W7, r3 + (ro or 0)
        pr = est + rate * (reset - now) / 3600
        out.append(f"Если так и дальше — к сбросу ≈{pr:.0f}% недели" + (f"; лимит кончится ≈{fmt(now + (100 - est) / rate * 3600)}" if pr > 100 and rate > 0 else "")
                   + ("" if L else " (без того, чего нет в логах)") + ".")
    out.append("«Не в логах» — всё, чего нет в логах этого компьютера: другие люди и устройства, claude.ai, claude -p --no-session-persistence,\n"
               "служебные вызовы; и ошибка оценки размера лимита (PARAMS[\"cap\"]): если лимит на деле меньше, наша доля больше.")
    print("\n".join(out))


def serve(a):
    """Страница на этом компьютере: слушает только 127.0.0.1; «/» — последняя сборка, «/rescan» — перечитать логи и собрать
    заново, «/period?p=1|2|7|w|all|r&from=ГГГГ-ММ-ДД&to=ГГГГ-ММ-ДД&c=чат» — тот же снимок логов за другой период
    (из памяти, за секунды; c — открытый чат, вернётся через #c=).
    Ничего не пишет на диск и никуда не ходит. Выключить — Ctrl+C или закрыть окно."""
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    import threading, webbrowser, socket, urllib.parse

    class Srv(ThreadingHTTPServer):
        # На Windows SO_REUSEADDR пускает второй сервер на занятый порт: оба слушают, отвечает старый (19.10 так и вышло —
        # новая версия «пряталась» за 0.4.8). Порт только свой: занят — берём следующий.
        allow_reuse_address = False
        daemon_threads = True

        def server_bind(self):
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()
    if not (a.all or a.since or a.days):
        a.days = 7                               # в админке по умолчанию — последние 7 дней (полоса дней покажет сбросы лимита)
    st, lock, port = {"a": a, "raw": None}, threading.Lock(), a.serve

    def getpool(s0):
        # чтение логов — почти всё время сборки. Читаем всё сразу: за всё время выходит столько же, сколько за 4 недели
        # (17.11: ≈30 с, 50 тыс. вызовов), зато полоса дней видит всю историю. Смена периода берёт копии чатов из памяти.
        if st["raw"] is None:
            st["raw"], st["t"] = collect(0), dt.datetime.now()
        return [dict(ch) for ch in st["raw"]]

    def day(x):
        try:
            return dt.date.fromisoformat(x).isoformat()
        except ValueError:
            return None

    def rebuild(fresh=False):
        if fresh:
            st["raw"] = None
        try:
            st["page"] = build(st["a"], getpool, lambda: st["t"])[0]
        except SystemExit as e:
            st["page"] = f"<!doctype html><meta charset=utf-8><p style='font:16px sans-serif'>{e} · <a href='/rescan'>снять данные</a></p>"

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost"):
                return self.send_error(403)          # чужой сайт через подмену DNS не прочитает отчёт
            if self.path.startswith(("/rescan", "/period")):
                q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                with lock:
                    if self.path.startswith("/period"):
                        n, v = argparse.Namespace(**vars(st["a"])), q.get("p", ["7"])[0]
                        n.all, n.days, n.since, n.until = v == "all", float(v) if v in ("1", "2", "7") else None, None, None
                        f, t = (day(q.get(x, [""])[0]) for x in ("from", "to"))
                        if v == "r" and f and t:
                            n.since, n.until = min(f, t), max(f, t)
                        st["a"] = n
                        rebuild()
                    else:
                        rebuild(fresh=True)
                c = q.get("c", [""])[0]
                self.send_response(303)
                self.send_header("Location", "/#c=" + c if re.fullmatch(r"[\w-]{1,40}", c) else "/")
                return self.end_headers()
            if self.path.split("?")[0] not in ("/", "/index.html"):
                return self.send_error(404)
            b = st["page"].encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)

        def log_message(self, *x):
            pass

    print(f"{NAME} {VER}: собираю отчёт по логам, это секунд десять…", flush=True)
    rebuild()
    for p in range(port, port + 20):
        try:
            srv = Srv(("127.0.0.1", p), H)
            break
        except OSError:
            continue
    else:
        sys.exit(f"порты {port}–{port + 19} заняты: --serve ДРУГОЙ_ПОРТ")
    url = f"http://127.0.0.1:{p}/"
    print(f"{NAME} {VER}: страница {url} — только этот компьютер. «Снять данные» на странице — пересобрать по свежим логам.\n"
          "Выключить — Ctrl+C или закрыть это окно.", flush=True)
    if not a.no_open:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def md_report(chats, since):
    """Отчёт для нейросети (Markdown, коротко): итоги, по неделям, «а если бы», утечки, проекты, чаты, практики. Счёт тот
    же, что на странице: ht(); холодные старты — как ci()/cc() в сценарии «как было»; обвязка — как bk()[0]."""
    W, now, W7 = PARAMS["cap"][1], time.time(), 7 * 86400
    SUM, CO, MU = PARAMS["summary_tokens"], PARAMS["cold"], PARAMS["mult"]
    ctx = lambda c: c[3] + c[4] + c[5] + c[6]
    home, w0 = str(Path.home()), caps()[1].get("week0")

    def wk(t):                       # начало недели: от сброса лимита, если известен, иначе понедельник
        if w0:
            return w0 + (t - w0) // W7 * W7
        d = dt.datetime.fromtimestamp(t)
        return int((d - dt.timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

    def at_eff(c, top):              # тот же вызов при effort не выше top (меняется только выход)
        return ht(c) if c[2] <= top else ht(c) + c[7] * prow(c)[1] * (MU[c[1]][top] / MU[c[1]][c[2]] - 1)
    R, WK, MCP, MEM, SKN = [], {}, {}, {}, 0
    for ch in chats:
        k = [c for c in ch["k"] if c[0] >= since]
        if not k:
            continue
        main = [i for i, c in enumerate(k) if not c[9]]
        ws = sorted(k[i][4] + k[i][5] for i in main if k[i][4] + k[i][5] < 8000)
        g, fl0 = (ws[len(ws) // 2] if ws else 1000), (ctx(k[main[0]]) if main else 0)
        ev = []
        for p in range(1, len(main)):
            c, pc = k[main[p]], k[main[p - 1]]
            wr, x, xp, gap = c[4] + c[5], ctx(c), ctx(pc), c[0] - pc[0]
            if wr >= max(CO["min_write"], CO["min_share"] * x):
                ev.append((p, wr, x, xp, "cmp" if x < .6 * xp else "idle" if gap >= 3540 else "sw" if c[12] != pc[12] else "upd"
                           if c[11] else "cmp" if x < .9 * xp else "ttl5" if gap >= 300 and pc[4] > pc[5] else "unk"))
        r = {"pen": {}, "idle": 0.0, "sw": 0.0, "why": {}}
        for n, (p, wr, x, xp, cs) in enumerate(ev):
            c, pr = k[main[p]], prow(k[main[p]])
            pw = (c[4] * pr[0] * 1.25 + c[5] * pr[3]) / wr
            pe = max(0, wr - g) * (pw - pr[2])
            r["pen"][main[p]] = pe
            r["why"][cs] = r["why"].get(cs, 0) + 1
            sv, xn = 0.0, fl0 + SUM
            if xp > xn and cs != "cmp":          # «компакт перед паузой»: записать выжимку, а не всю переписку
                pp, end = prow(k[main[p - 1]]), (ev[n + 1][0] if n + 1 < len(ev) else len(main))
                sv = (wr * pw + c[6] * pr[2] - (xp * pp[2] + SUM * pp[1] + (xn + max(0, x - xp)) * pr[3])
                      + sum((xp - xn) * prow(k[main[q]])[2] for q in range(p + 1, end)))
            if cs == "sw":
                r["sw"] += pe
            elif cs == "idle" and sv > 0:
                r["idle"] += sv
        tot = hz = conv = out = ag = big = 0.0
        mm, ee = [0.0] * 4, {}
        for i, c in enumerate(k):
            pr = prow(c)
            rd, wr, ou = c[6] * pr[2], c[3] * pr[0] + c[4] * pr[0] * 1.25 + c[5] * pr[3], c[7] * pr[1]
            x, base = rd + wr + ou, max(0, rd + wr - r["pen"].get(i, 0))
            s = min(1, fl0 / max(1, ctx(c))) if fl0 else 0
            tot, hz, conv, out = tot + x, hz + base * s, conv + base * (1 - s), out + ou
            mm[c[1]] += x
            ee[c[2]] = ee.get(c[2], 0) + x
            ag += x if c[9] else 0
            big += x if ctx(c) > 200_000 else 0
            b = WK.setdefault(wk(c[0]), [0.0, set()])
            b[0] += x
            b[1].add(ch["id"])
        h = ch["h"]
        for nm, n in h.get("mcp", []):
            MCP[nm] = max(MCP.get(nm, 0), n)
        for nm, n in h.get("mem", []):
            MEM[nm] = max(MEM.get(nm, 0), n)
        SKN = max(SKN, len(h.get("sk", {})))
        cx = [ctx(k[i]) for i in main] or [0]
        cwd = h.get("cwd") or "?"
        R.append({"t": ch["title"], "cwd": "~" + cwd[len(home):] if cwd.startswith(home) else cwd, "q": h.get("q"),
                  "cmp": h.get("cmp", 0), "n": len(k), "t0": k[0][0], "t1": k[-1][0], "tot": tot, "hz": hz, "conv": conv,
                  "pen": sum(r["pen"].values()), "out": out, "ag": ag, "big": big, "mm": mm, "ee": ee, "nev": len(ev),
                  "why": r["why"], "idle": r["idle"], "sw": r["sw"], "fl0": fl0, "cavg": sum(cx) / len(cx), "cmax": max(cx),
                  "alt": [sum(ht(c, m) for c in k) for m in range(4)], "hi": sum(at_eff(c, 2) for c in k),
                  "son": sum(ht(c, 1) if c[1] >= 2 else ht(c) for c in k),
                  "ags": sum(ht(c, 1) if c[9] and c[1] >= 2 else ht(c) for c in k)})
    T = sum(r["tot"] for r in R)
    if not T:
        return None
    R.sort(key=lambda r: -r["tot"])
    S = lambda key: sum(r[key] for r in R)
    f1 = lambda x: f"{x:.1f}".replace(".", ",")
    M = lambda x: f1(x / 1e6) + " млн" if x >= 5e4 else f"{x / 1e3:.0f} тыс."
    pw = lambda x: f1(x / W * 100) + "%"
    sh = lambda x, t=T: f"{x / t * 100:.0f}%" if t else "0%"
    dd = lambda t: dt.datetime.fromtimestamp(t).strftime("%d.%m %H:%M")
    tK = lambda x: f"{x / 1e3:.0f} тыс." if x >= 1000 else "<1 тыс."
    sp = lambda q: q if len(q) <= 60 else "…" + q[-50:]          # длинный путь — хвост
    WHY = {"idle": "пауза > часа", "sw": "смена модели", "cmp": "после сжатия", "upd": "обновился Claude Code",
           "ttl5": "кэш был на 5 минут", "unk": "не видно"}
    EN = {-1: "не записан", 0: "low", 1: "medium", 2: "high", 3: "xhigh", 4: "max"}
    mix = lambda mm, t: ", ".join(f"{FAM[m].capitalize()} {sh(mm[m], t)}" for m in sorted(range(4), key=lambda m: -mm[m]) if mm[m] >= t * .005)
    emix = lambda ee, t: ", ".join(f"{EN[e]} {sh(x, t)}" for e, x in sorted(ee.items(), key=lambda kv: -kv[1]) if x >= t * .005)
    t0, t1 = min(r["t0"] for r in R), max(r["t1"] for r in R)
    days = max(1.0, (t1 - t0) / 86400)
    MM = [sum(r["mm"][m] for r in R) for m in range(4)]
    EE = {}
    for r in R:
        for e, x in r["ee"].items():
            EE[e] = EE.get(e, 0) + x
    why = {}
    for r in R:
        for c, n in r["why"].items():
            why[c] = why.get(c, 0) + n
    fl = [r["fl0"] for r in R if r["fl0"]] or [0]
    L = ["# LimitDoctor — отчёт для нейросети", "",
         f"{NAME} {VER} · собран {dd(now)} · период {dd(t0)} → {dd(t1)} ({days:.0f} дн.) · только чаты Claude Code этого компьютера", "",
         "Нейросеть: по этому файлу скажи человеку, где были основные утечки, и дай простые советы, у каждого — сколько процентов "
         "недельного лимита он сэкономил бы (раздел «А если бы»); скажи, насколько дешевле вышло бы всё сделанное. Коротко, без простыни. "
         "HTML рядом — для человека, его не читай.", "",
         "Единица — ХТ (хайку-токен): $1 за миллион токенов по ценам API (так стоил вход Haiku 4.5); каждый вызов — по цене своей версии модели. "
         f"Лимит плана Max ($200) — оценка ≈{f1(PARAMS['cap'][1] / 1e9)} млрд ХТ в неделю и ≈{PARAMS['cap'][0] / 1e6:.0f} млн за 5 часов "
         "(Claude размер не сообщает), поэтому 1% недели ≈ 20 млн ХТ ≈ $20; проценты в этом отчёте приблизительные, вилка 16–27 млн на 1%, "
         "то есть реальные проценты могут быть ниже в 1,35 раза и выше в 1,25 раза. Откуда число: калибровка автора 17.11 по ночным замерам Claude и "
         "логам (с 2 до 8 утра, когда лимит тратит только этот компьютер; 11 ночей); раньше стояло 12 млн на 1% (регрессия с чужим фоном) и 35 млн. Логи старше ~30 дней Claude Code обычно удаляет "
         "сам (настройка cleanupPeriodDays), так что «всё время» — сколько логов осталось.", "",
         "## Итого", "",
         f"- Чатов {len(R)}, вызовов модели {S('n')}. Всего {M(T)} ХТ = {pw(T)} недельного лимита ≈ "
         + f"${T / 1e6:,.0f}".replace(",", " ") + f" по ценам API; в среднем {pw(T / days * 7)} лимита в неделю.",
         f"- Модели: {mix(MM, T)}. Effort: {emix(EE, T)}.",
         f"- Куда ушло: обвязка {sh(S('hz'))} (системный промпт, инструменты, скиллы, MCP, CLAUDE.md — их перечитывает каждый "
         f"вызов), переписка {sh(S('conv'))}, холодные старты {sh(S('pen'))}, ответы и мысли {sh(S('out'))}.",
         f"- Холодных стартов {S('nev')}, переплата {M(S('pen'))} ХТ = {pw(S('pen'))} недели; причины: "
         + ", ".join(f"{WHY[c]} ×{n}" for c, n in sorted(why.items(), key=lambda kv: -kv[1])) + f". Компактов: {S('cmp')}.",
         f"- Агенты (субагенты): {sh(S('ag'))} расхода. Вызовы при контексте больше 200 тыс.: {sh(S('big'))} расхода.",
         f"- Обвязка на старте чата: в среднем {tK(sum(fl) / len(fl))} токенов, максимум {tK(max(fl))}; скиллов в списке до {SKN}."
         + (" MCP по логам (знаков инструкций): " + ", ".join(f"{n} {v // 1000 + 1} тыс." for n, v in sorted(MCP.items(), key=lambda kv: -kv[1])[:8]) + "." if MCP else "")
         + (" Память: " + ", ".join(f"{n} {v // 1000 + 1} тыс. знаков" for n, v in sorted(MEM.items(), key=lambda kv: -kv[1])[:5]) + "." if MEM else ""),
         "", "### По неделям" + (" (от сброса лимита)" if w0 else " (с понедельника)"), ""]
    for t in sorted(WK):
        L.append(f"- {dt.datetime.fromtimestamp(t):%d.%m}: {M(WK[t][0])} ХТ = {pw(WK[t][0])} недельного лимита, чатов {len(WK[t][1])}")
    sc = [(T - S("son"), "Opus и Fable → Sonnet, остальное как было", "son",
           "На механике (поиск, правки по образцу, логи, переименования, тесты по шаблону) качество почти то же; на архитектуре "
           "и сложной отладке Opus окупается."),
          (T - S("hi"), "Effort не выше high", "hi", "xhigh и max раздувают ответ и мысли в 1,5–4,5 раза."),
          (T - S("ags"), "Агенты на Sonnet вместо Opus / Fable", "ags", "Агенту на поиск и механику хватает дешёвой модели."),
          (S("idle"), "Компакт перед паузой дольше часа", "idle",
           "Там, где короткая выжимка дешевле, чем после паузы записать всю переписку заново."),
          (S("sw"), "Не менять модель посреди чата", "sw", "Кэш привязан к модели: менять — в новом чате или сразу после компакта.")]
    L += ["", "## А если бы — та же работа, другой выбор", ""]
    for sv, name, key, note in sorted(sc, key=lambda x: -x[0]):
        if sv <= 0:
            continue
        top = sorted(R, key=lambda r: -(r["tot"] - r[key] if key in ("son", "hi", "ags") else r[key]))[:2]
        L.append(f"- **{name}**: дешевле на {M(sv)} ХТ = {sh(sv)} всего расхода, {pw(sv)} недельного лимита. {note} "
                 "Больше всего в: " + ", ".join(f"«{r['t']}»" for r in top) + ".")
    L.append("- Всё на одной модели: " + ", ".join(f"{FAM[m].capitalize()} {M(sum(r['alt'][m] for r in R))}" for m in range(4))
             + f" ХТ (как было — {M(T)}).")
    L.append("- Сценарии пересекаются — в лоб не складывай: вместе выходит меньше суммы.")
    L += ["", "## Проекты (папки), дорогие сверху", ""]
    P = {}
    for r in R:
        q = P.setdefault(r["cwd"], {"n": 0, "tot": 0.0, "mm": [0.0] * 4, "t0": r["t0"], "t1": r["t1"]})
        q["n"] += 1
        q["tot"] += r["tot"]
        q["mm"] = [a + b for a, b in zip(q["mm"], r["mm"])]
        q["t0"], q["t1"] = min(q["t0"], r["t0"]), max(q["t1"], r["t1"])
    PS = sorted(P.items(), key=lambda kv: -kv[1]["tot"])
    for cwd, q in PS[:15]:
        L.append(f"- {sp(cwd)} — чатов {q['n']}, {M(q['tot'])} ХТ ({sh(q['tot'])} всего, {pw(q['tot'])} недели), "
                 f"{dd(q['t0'])[:5]}–{dd(q['t1'])[:5]}; {mix(q['mm'], q['tot'])}")
    if len(PS) > 15:
        rest = sum(q["tot"] for _, q in PS[15:])
        L.append(f"- ещё папок {len(PS) - 15} — {sh(rest)} расхода")
    L += ["", "## Чаты, дорогие сверху", ""]
    for j, r in enumerate(R[:20], 1):
        ws = ", ".join(f"{WHY[c]} ×{n}" for c, n in sorted(r["why"].items(), key=lambda kv: -kv[1]))
        ifs = [(r["tot"] - r["son"], "Opus/Fable→Sonnet"), (r["tot"] - r["hi"], "effort ≤ high"), (r["idle"], "компакт перед паузами"),
               (r["sw"], "без смены модели"), (r["tot"] - r["ags"], "агенты на Sonnet")]
        ifs = ", ".join(f"{n} −{sh(v, r['tot'])}" for v, n in sorted(ifs, key=lambda x: -x[0]) if v >= r["tot"] * .01)
        L += [f"### {j}. «{r['t']}» — {M(r['tot'])} ХТ ({pw(r['tot'])} недели · {sh(r['tot'])} всего)",
              f"- {sp(r['cwd'])} · {dd(r['t0'])} → {dd(r['t1'])} · вызовов {r['n']}" + (f", агенты {sh(r['ag'], r['tot'])} расхода" if r["ag"] else ""),
              f"- {mix(r['mm'], r['tot'])} · effort: {emix(r['ee'], r['tot'])}",
              f"- контекст: старт {tK(r['fl0'])}, в среднем {tK(r['cavg'])}, максимум {tK(r['cmax'])} · компактов {r['cmp']} · "
              f"холодных стартов {r['nev']}" + (f" (переплата {pw(r['pen'])} недели; {ws})" if r["nev"] else ""),
              *([f"- если бы: {ifs}"] if ifs else []),
              f"- первая реплика: «{r['q']}»" if r["q"] else "- первой реплики в логе нет"]
    if len(R) > 20:
        L += ["", "### Остальные чаты", ""]
        for r in R[20:60]:
            q = (r["q"] or "")[:80]
            L.append(f"- «{r['t']}» — {M(r['tot'])} ({pw(r['tot'])}) · {sp(r['cwd'])} · {mix(r['mm'], r['tot']).split(' ')[0]}" + (f" · «{q}»" if q else ""))
        if len(R) > 60:
            L.append(f"- ещё чатов {len(R) - 60} — {sh(sum(r['tot'] for r in R[60:]))} расхода")
    return "\n".join(L) + "\n\n" + MD_PRACT


MD_PRACT = """## Практики — откуда брать рекомендации

Как тратится лимит. Каждый вызов модели заново читает весь контекст: обвязку и всю переписку. Чтение из кэша стоит 0,1 цены
входа, но на большом контексте и это много; запись в кэш — 1,25–2 цены входа. Кэш живёт около часа (иногда 5 минут) и
привязан к модели. Выход (ответ и мысли) в 5 раз дороже входа, effort меняет именно его. За токен Sonnet в 2 раза дороже
Haiku 4.5, Opus — в 4, Fable — в 8–10; Haiku 5.5 в 10 раз дешевле Haiku 4.5 (на запросах до 100 тыс. токенов).

1. Модель под задачу. Механика — поиск по коду, правки по образцу, переименования, разбор логов, тесты по шаблону — Sonnet
   или Haiku. Opus — архитектура и сложная отладка, где дешёвая модель ходит кругами. Агентам на механику — дешёвую модель.
2. Effort под задачу. high и выше — где надо думать; xhigh и max раздувают выход в 1,5–4,5 раза. Рутине хватит medium или low.
3. Пауза дольше часа — холодный старт: кэш умер, переписка записывается заново. Уходишь надолго — сначала компакт
   (/compact) или новый чат с короткой выжимкой.
4. Не меняй модель посреди длинного чата: кэш привязан к модели. Менять — в новом чате или сразу после компакта.
5. Один чат — одна задача. Длинный чат дорожает с каждым ходом: каждый вызов перечитывает всё. После 150–200 тыс.
   контекста — компакт или новый чат.
6. Обвязка — налог на каждый вызов. Лишние MCP-серверы (/mcp), плагины и скиллы, раздутый CLAUDE.md перечитываются каждым
   ходом. Выключи то, чем в этом проекте не пользуешься; CLAUDE.md — коротко, детали — в файлах, которые модель читает по нужде.
7. Не держи пять чатов «на огне»: у каждого, простоявшего больше часа, следующий ход — холодный старт.
8. «Готовь компакт» — велосипед автора этого файла. Автокомпакт срабатывает, когда контекст уже переполнен, и его пересказ
   теряет детали, поэтому сжимать лучше самому и вовремя (перед паузой, после этапа работы). Как: человек пишет «готовь
   компакт» → модель отвечает и в самом конце пишет «СОХРАНЁНКА:» и то, что пересказ потеряет, а ей понадобится (файлы,
   решения, что дальше) → человек вводит /compact → хук возвращает модели сохранёнку слово в слово. Честно: руками немного
   неудобно — два шага вместо одного, — но это необходимость: без сохранёнки после сжатия модель теряет нить и тратит токены,
   чтобы её найти. Поставить: python <этот файл> --compact-kit — положит рядом хук compact_note.py и compact_kit.md (правило
   для CLAUDE.md и строки для settings.json); ставить — только с «да» человека. Есть свой способ или нашёлся получше на
   GitHub (хуки PreCompact / SessionStart, план в файле) — бери его.
"""


def compact_kit():
    """«Готовь компакт» для любого компьютера: кладёт рядом хук и правило. Сам ничего не включает и настроек не трогает."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "compact_note.py").write_text(KIT_HOOK, encoding="utf-8")
    (REPORTS / "compact_kit.md").write_text(KIT_MD.replace("__PY__", sys.executable.replace("\\", "/")), encoding="utf-8")
    print(f"положила {REPORTS / 'compact_note.py'} и {REPORTS / 'compact_kit.md'}; как поставить — в compact_kit.md. Сама ничего не включала.")


KIT_MD = r"""# «Готовь компакт»: правило и хук

Нейросеть: ставь это только с «да» человека. Три шага.

1. Хук. Скопируй compact_note.py в ~/.claude/hooks/ (папки нет — создай).
2. Настройка. В ~/.claude/settings.json добавь (если "hooks" уже есть — допиши SessionStart туда, ничего не затирая):

       "hooks": {
         "SessionStart": [
           {"matcher": "compact", "hooks": [{"type": "command",
             "command": "\"__PY__\" \"<домашняя папка>/.claude/hooks/compact_note.py\""}]}
         ]
       }

   Пути — полные, прямыми слэшами. Python — тот, которым запускали LimitDoctor: __PY__
3. Правило. Допиши в ~/.claude/CLAUDE.md (глобальные инструкции; нет файла — создай) раздел «Правило» ниже.

Проверка: в любом чате скажи «готовь компакт», дождись ответа со строкой «СОХРАНЁНКА:», введи /compact. После сжатия модель
должна увидеть сохранёнку целиком. Лог хука — compact_note.log рядом с ним. Убрать: блок SessionStart из settings.json и
абзац из CLAUDE.md.

## Правило

**«Подготовь компакт».** «Подготовь компакт», «готовь компакт» или похожие слова значат: этот чат сейчас сожмут командой
`/compact`. Разговор заменится кратким пересказом, детали пропадут. Сохранёнка, которую ты напишешь, вернётся к тебе после
сжатия слово в слово, в дополнение к пересказу.

Решаешь ты: можно сказать, что сжимать сейчас не стоит, и почему; можно обойтись без сохранёнки; можно написать сохранёнку
любой длины, от одной строки до огромного текста. Сохранёнка остаётся в контексте после сжатия: чем она длиннее, тем меньше
места сжатие освободит. Пересказ сохранит общую канву, сохранёнка — для того, что он потеряет, а тебе понадобится дальше.
Если тебе сказали, что именно запомнить, — это в сохранёнку обязательно.

Чтобы сохранёнка вернулась: начни её отдельной строкой `СОХРАНЁНКА:` и пиши в самом конце ответа — сохранёнка это всё от
этой строки до конца ответа. Если сохранёнок несколько, вернётся последняя; передумал — напиши новую.

Перед тем как закончить сохранёнку, прочитай её, будто этого разговора не помнишь: ясно ли, где файлы, что ждёт тебя самого?
Незакрытое из прошлой сохранёнки перенеси или пометь закрытым — молча не выбрасывай. Закрытое пометь один раз, дальше не тащи.
"""


KIT_HOOK = r'''# compact_note.py — хук Claude Code SessionStart (matcher "compact"): после сжатия чата возвращает модели её «СОХРАНЁНКУ».
# Сохранёнка = текст ответа модели от строки «СОХРАНЁНКА:» до конца этого ответа; берётся последняя из тех, что написаны
# после предыдущего сжатия. Метка внутри ```-блока — цитата, не сохранёнка; сохранёнка из одного слова «не нужна» /
# «отмена» не возвращается; сообщения других чатов, команды и уведомления не считаются сообщениями человека.
# Ничего не нашёл или что-то сломалось — молчит, сжатию не мешает. Лог — compact_note.log рядом с этим файлом.
# Claude Code сам переносит последние сообщения через сжатие дословно, поэтому сохранёнка может прийти дважды
# (≈1 тыс. токенов) — принятая цена надёжности. Из набора LimitDoctor (--compact-kit).
import sys, json, re, os, traceback, datetime as dt

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compact_note.log')
MARK = re.compile(r'^[ \t>*#_]*(?:сохран[её]нка|приписка к компакту)[ \t*_]*:', re.I | re.M)
FENCE = re.compile(r'^[ \t]*```', re.M)
CANCEL = re.compile(r'^[\s*_]*(не нужна|не нужно|отмена|нет)[\s.!*_]*$', re.I)
REMINDER = re.compile(r'<system-reminder>.*?</system-reminder>', re.S)
FRESH = dt.timedelta(minutes=30)


def log(msg):
    try:
        lines = []
        if os.path.exists(LOG):
            with open(LOG, encoding='utf-8') as f:
                lines = f.read().splitlines()[-99:]
        lines.append(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + msg)
        with open(LOG, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    except Exception:
        pass


def ts(d):
    try:
        return dt.datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00'))
    except Exception:
        return None


def text_of(d):
    c = (d.get('message') or {}).get('content')
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return '\n'.join(x.get('text', '') for x in c if isinstance(x, dict) and x.get('type') == 'text')
    return ''


def is_user_msg(d):
    """Сообщение человека: не пересказ, не результат инструмента, не команда, не сообщение пира, не уведомление."""
    if d.get('type') != 'user' or d.get('isMeta') or d.get('isCompactSummary'):
        return False
    c = (d.get('message') or {}).get('content')
    if isinstance(c, list) and any(isinstance(x, dict) and x.get('type') == 'tool_result' for x in c):
        return False
    t = REMINDER.sub('', text_of(d)).strip()
    return bool(t) and not t.startswith(('<', 'Another Claude session', 'Claude Code notice'))


def load(path):
    recs = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if isinstance(d, dict) and not d.get('isSidechain'):
                recs.append(d)
    return recs


def main():
    inp = json.loads(sys.stdin.buffer.read().decode('utf-8-sig') or '{}')
    path = inp.get('transcript_path') or ''
    sid = (inp.get('session_id') or '?')[:8]

    recs = load(path)

    # Окно поиска: от предыдущего сжатия до этого. Обычно свежей границы в журнале ещё нет (Claude Code
    # пишет её после конца хука) — тогда окно от последней границы до конца. Если граница уже есть — до неё.
    # Сохранённые сжатием сообщения копируются за границу со старым временем, поэтому окно — по времени.
    now = dt.datetime.now(dt.timezone.utc)
    bounds = sorted(t for t in (ts(d) for d in recs if d.get('subtype') == 'compact_boundary') if t)
    asst = [t for t in (ts(d) for d in recs if d.get('type') == 'assistant') if t]
    lo = hi = None
    if bounds:
        last = bounds[-1]
        if now - last < FRESH and not any(t > last for t in asst):
            lo, hi = (bounds[-2] if len(bounds) > 1 else None), last
        else:
            lo = last

    def inside(t):
        return t is not None and (lo is None or t > lo) and (hi is None or t < hi)

    best = None
    for d in recs:
        if d.get('type') != 'assistant':
            continue
        t = ts(d)
        if not inside(t):
            continue
        txt = text_of(d)
        # Нечётное число строк ``` перед меткой — метка внутри блока кода, это цитата, а не приписка.
        ms = [m for m in MARK.finditer(txt) if len(FENCE.findall(txt[:m.start()])) % 2 == 0]
        if ms and (best is None or t >= best[0]):
            best = (t, txt[ms[-1].start():].strip())
    if not best:
        log(f'{sid} сохранёнки нет (окно {lo} .. {hi})')
        return

    t, note = best
    when = t.astimezone().strftime('%d.%m %H:%M')
    body = MARK.sub('', note, count=1).strip()
    if CANCEL.match(body):
        log(f'{sid} сохранёнка от {when} отменена словами «{body}»')
        return
    after = sum(1 for d in recs if is_user_msg(d) and inside(ts(d)) and ts(d) > t)
    head = f'Перед сжатием ({when}) ты сам написал себе сохранёнку. Вот она, слово в слово.'
    if after:
        head += f' После неё пользователь написал ещё {after} сообщ.: если что-то в сохранёнке устарело, верь более свежему.'
    # Больше 10 000 знаков Claude Code сам кладёт в файл и показывает начало и путь.
    head += ' Если ниже только начало, прочитай полный текст по указанному пути целиком, прежде чем продолжать.'
    out = {
        'systemMessage': f'Сохранёнка в контексте чата ({len(note)} симв.)',
        'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': head + '\n\n' + note},
    }
    # Без экранирования \uXXXX: если JSON вдруг не распознают, модель всё равно прочитает текст.
    sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode('utf-8'))
    log(f'{sid} сохранёнка {len(note)} симв. от {when}, сообщений пользователя после неё: {after}')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        log('ОШИБКА ' + traceback.format_exc().replace('\n', ' | '))
    sys.exit(0)
'''


HELP = """человеческим языком:
  Всё время и MD для нейросети: python limitdoctor.py --all
      HTML для человека и .md рядом — его и давать нейросети: коротко, с «а если бы» и практиками.
  Набор «готовь компакт»:     python limitdoctor.py --compact-kit   хук и правило рядом с файлом; сам ничего не включает
  Посмотреть на странице:    python limitdoctor.py --serve
      откроется http://127.0.0.1:8077 — видно только с этого компьютера. «Снять данные» — пересобрать по свежим логам.
      Выключить — Ctrl+C или закрыть окно. Порт занят — возьмётся следующий.
  Узнать текстом (нейросети): python limitdoctor.py --brief       последние сутки по часам: мы, остальной аккаунт, темп
                              python limitdoctor.py --brief 72    последние 3 дня
  Сдать процент Claude:       python limitdoctor.py --snap 41 --h5 16 --reset "25.10 05:00"
      41 — сколько процентов недели съел весь аккаунт (claude.ai → Settings → Usage или get_usage); --h5 и --reset — по желанию.
      Снимок ложится в account.jsonl, после него печатается сводка. Чем чаще снимки, тем точнее слой «не видно в логах».
  Снять самому, без человека:  python limitdoctor.py --snap-auto
      спрашивает Claude Code командой /usage — модель не вызывается, токенов 0. Годится для расписания Windows.
  Ответы get_usage, которые чаты получали по ходу работы, подхватываются из логов сами — это тоже снимки.
  «Мы» — чаты этого компьютера ÷ размер лимита (PARAMS["cap"], оценка). «Остальные» — процент Claude минус «мы»."""


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def main():
    ap = argparse.ArgumentParser(description=f"{NAME} {VER}: отчёт о расходе лимита Claude Code", epilog=HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chat", nargs="?", const="", default=None, help="один чат: без значения — текущий, или начало id")
    ap.add_argument("--session", help="то же, что --chat ID")
    ap.add_argument("--days", type=float, help="за сколько дней (по умолчанию — текущая неделя лимита или 7 дней)")
    ap.add_argument("--since", help="ГГГГ-ММ-ДД вместо --days")
    ap.add_argument("--until", help="ГГГГ-ММ-ДД: по какой день включительно (вместе с --since)")
    ap.add_argument("--all", action="store_true", help="за всё время, что есть в логах")
    ap.add_argument("--compact-kit", action="store_true", help="положить рядом хук и правило «готовь компакт» (сам ничего не включает)")
    ap.add_argument("--top", type=int, default=60); ap.add_argument("--out"); ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--admin", action="store_true", help=argparse.SUPPRESS); ap.add_argument("--open", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--week-reset", help="когда Claude обнуляет недельный лимит: 2026-10-11T02:00Z или ЧЧ:ММ (один раз)")
    ap.add_argument("--plan", type=float, help="цена подписки, $ в месяц (по умолчанию 200)")
    ap.add_argument("--effort-check", action="store_true", help="пересчитать множители effort по своим логам за 30 дней")
    ap.add_argument("--statusline", action="store_true", help="режим статус-строки Claude Code: пишет проценты Claude в account.jsonl")
    ap.add_argument("--serve", nargs="?", const=8077, type=int, metavar="ПОРТ", help="страница на этом компьютере с кнопкой «Снять данные»")
    ap.add_argument("--brief", nargs="?", const=24, type=int, metavar="ЧАСОВ", help="коротко текстом: %% недели по часам, темп, прогноз")
    ap.add_argument("--snap", metavar="ПРОЦЕНТ", help="сдать снимок: сколько %% недели съел весь аккаунт по Claude; затем сводка")
    ap.add_argument("--snap-auto", action="store_true", help="снять процент самому через claude /usage (без модели, 0 токенов)")
    ap.add_argument("--h5", metavar="ПРОЦЕНТ", help="к --snap: %% лимита за 5 часов")
    ap.add_argument("--reset", metavar="КОГДА", help='к --snap: когда сброс недели, например "25.10 05:00"')
    a = ap.parse_args()
    if a.statusline:
        return statusline()
    if a.compact_kit:
        return compact_kit()
    if not PROJS:
        sys.exit("не нашла логи Claude Code: нет папки projects в ~/.claude или ~/.config/claude")
    if a.effort_check:
        return effort_check()
    if a.week_reset:
        set_reset(a.week_reset)
    if a.snap_auto:
        return snap_auto()
    if a.snap is not None:
        snap(a.snap, a.h5, a.reset)
        return brief(a.brief or 24)
    if a.brief:
        return brief(a.brief)
    if a.serve:
        return serve(a)
    page, name, lines, md = build(a)
    out_dir = Path(a.out) if a.out else REPORTS
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name
    out.write_text(page, encoding="utf-8")
    print("\n".join(lines))
    print("ФАЙЛ:", out)
    if md:
        mo = out.with_suffix(".md")
        mo.write_text(md, encoding="utf-8")
        print(f"ДЛЯ НЕЙРОСЕТИ: {mo} ({len(md.encode('utf-8')) // 1024 + 1} КБ — его и читать, HTML нейросети дорог)")
        print("Показать кому-то — отправь оба файла. В MD — названия чатов, папки и начало первой реплики каждого чата: глянь перед отправкой.")
    if not a.no_open and (a.out is None or a.open):
        os.startfile(out) if hasattr(os, "startfile") else __import__("webbrowser").open(out.as_uri())


def per_of(a):
    """Период для страницы: [1 | 2 | 7 — суток, w — неделя лимита, r — с даты (по дату — P.until), all — всё время,
    d — другое число суток; дата]."""
    if a.all:
        return ["all", ""]
    if a.since:
        return ["r", a.since]
    if a.days in (1, 2, 7):
        return [str(int(a.days)), ""]
    return ["d", f"{a.days:g}"] if a.days else ["w", ""]


def build(a, getpool=None, gen=None):
    """Собрать отчёт: (страница, имя файла, строки итога, MD для нейросети или None). Нечего показать — SystemExit с причиной.
    getpool(since) — откуда взять чаты (по умолчанию collect: читает логи); gen() — время снимка логов для страницы."""
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")     # с секундами: два отчёта за минуту не затирают друг друга
    hrs = md = strip = until = None
    one = a.session or a.chat
    if one is not None and not a.admin:
        ch = load_chat(pick_log(one))
        if not ch["k"]:
            sys.exit("в логе нет вызовов модели")
        chats, admin, out, heat, bd = [ch], "false", f"chat_{ch['id']}_{stamp}.html", None, None
    else:
        # по умолчанию — та же неделя, что считает Claude (от сброса лимита), если сброс известен из замеров; иначе 7 дней
        week0 = caps()[1].get("week0")
        since = 0 if a.all else int(time.mktime(dt.date.fromisoformat(a.since).timetuple())) if a.since else int(time.time() - (a.days or 7) * 86400) if a.days or not week0 else int(week0)
        until = int(time.mktime((dt.date.fromisoformat(a.until) + dt.timedelta(days=1)).timetuple())) if getattr(a, "until", None) else None
        until = until if until and until < time.time() else None        # по сегодня включительно — это «до сейчас»
        # тепловая карта «день недели × час» — за 4 недели, чтобы проступила привычка; логи читаются одним проходом
        h0, now = int(time.time() - 28 * 86400), time.time()
        pool, hv, hc, first = (getpool or collect)(min(since, h0)), [0.0] * 168, [{} for _ in range(168)], now
        bd = brain(pool)                       # мозготокены за 14 суток — до того, как вызовы обрежутся по периоду
        if getpool:                            # админка: полоса дней за всё время — расход дня по семействам, тыс. ХТ
            sd = {}
            for ch in pool:
                for c in ch["k"]:
                    sd.setdefault(dt.date.fromtimestamp(c[0]), [0.0] * 4)[c[1]] += ht(c)
            d0 = min(sd, default=dt.date.fromtimestamp(now))
            strip = {"d0": int(time.mktime(d0.timetuple())), "v": [[round(x / 1e3) for x in sd.get(d0 + dt.timedelta(days=i), [0] * 4)]
                                                                for i in range((dt.date.fromtimestamp(now) - d0).days + 1)]}
        if a.all:                     # всё, что есть в логах: с первого вызова (страница считает дни периода от since)
            since = min((c[0] for ch in pool for c in ch["k"]), default=int(now)) // 3600 * 3600
        # по часам за 14 суток (виджет «по часам»: сутки / 3 дня / неделя и прошлая неделя для замеров до сброса)
        r0 = dt.datetime.fromtimestamp(now).replace(minute=0, second=0, microsecond=0).timestamp() - 335 * 3600
        rv, rw = [0.0] * 336, [{} for _ in range(336)]
        for j, ch in enumerate(pool):
            for c in ch["k"]:
                if c[0] >= h0:
                    d, x = dt.datetime.fromtimestamp(c[0]), ht(c)
                    cell = d.weekday() * 24 + d.hour
                    hv[cell] += x
                    hc[cell][j] = hc[cell].get(j, 0) + x
                    first = min(first, c[0])
                    r = int((c[0] - r0) // 3600)
                    if 0 <= r < 336:
                        rv[r] += x
                        rw[r][j] = rw[r].get(j, 0) + x
            ch["k"] = [c for c in ch["k"] if c[0] >= since and (until is None or c[0] < until)]
        # в каждой клетке — три самых прожорливых чата (для подсказки); имена — в общей таблице
        names, top = {}, []
        for cell in hc:
            best = sorted(cell.items(), key=lambda kv: -kv[1])[:3]
            top.append([[names.setdefault(pool[j]["title"], len(names)), round(x)] for j, x in best])
        hrs = {"t0": int(r0), "v": [round(x) for x in rv],
               "w": [[[names.setdefault(pool[j]["title"], len(names)), round(x)] for j, x in sorted(cell.items(), key=lambda kv: -kv[1])[:3]] for cell in rw]}
        heat = {"v": [round(x) for x in hv], "days": round((now - first) / 86400, 2), "top": top, "names": list(names)}
        md = md_report(pool, since)
        chats = [ch for ch in pool if len(ch["k"]) >= 3]
        chats.sort(key=lambda ch: -sum(ht(c) for c in ch["k"]))
        chats, admin, out = chats[:a.top], "true", f"usage_report_{stamp}.html"
        if not chats:
            sys.exit("за этот период вызовов модели нет")
    SK, sig = {"n": [], "l": []}, {}      # одинаковые списки скиллов храним один раз, имена скиллов — в общей таблице
    ix = {}
    for ch in chats:
        H = ch["h"]
        lst = sorted(H["sk"].items(), key=lambda kv: -kv[1])
        if lst and tuple(lst) not in sig:
            sig[tuple(lst)] = len(SK["l"])
            SK["l"].append([[ix.setdefault(n, len(ix)), c] for n, c in lst])
        ch["h"] = {"sys": H["sys"], "mem": H["mem"], "mcp": H["mcp"], "tl": H["tl"], "ag": H["ag"], "sk": sig[tuple(lst)] if lst else -1}
    SK["n"] = list(ix)
    cap, info = caps()
    acct = acct_rows(since - 7 * 86400) if admin == "true" else []      # [время, % недели, % 5 часов] — весь аккаунт по Claude
    P = dict(PARAMS, cap=cap, cal=info, since=(since if admin == "true" else 0), now=int(time.time()), heat=heat, hrs=hrs,
             plan=a.plan or PARAMS["plan_usd_month"], acct=acct, brain=bd, per=per_of(a), until=until or 0, strip=strip)
    page = PAGE
    for k, v in (("__SK__", dump(SK)), ("__CHATS__", dump(chats)), ("__ADMIN__", admin), ("__GEN__", ((gen and gen()) or dt.datetime.now()).strftime("%d.%m.%Y %H:%M")),
                 ("__PARAMS__", dump(P)), ("__NAME__", NAME), ("__VER__", VER)):
        page = page.replace(k, v)
    n = sum(len(c["k"]) for c in chats)
    tot = sum(ht(c) for ch in chats for c in ch["k"])
    fk = PARAMS["cap_week_fork"]
    lines = [f"{NAME} {VER}: чатов {len(chats)}, вызовов {n}, {tot / 1e6:.1f} млн ХТ ≈ {tot / cap[1] * 100:.1f}% лимита за неделю "
             f"(вилка {tot / fk[1] * 100:.1f}–{tot / fk[0] * 100:.1f}%; только чаты этого компьютера)"]
    if admin == "false":
        k = chats[0]["k"]
        alt = ", ".join(f"{nm} {sum(ht(c, i) for c in k) / cap[0] * 100:.1f}%" for i, nm in enumerate(["Haiku", "Sonnet", "Opus", "Fable"]))
        lines.append(f"чат: {chats[0]['title']}, с {dt.datetime.fromtimestamp(k[0][0]):%d.%m %H:%M} по {dt.datetime.fromtimestamp(k[-1][0]):%d.%m %H:%M}; "
              f"от лимита за 5 часов: как было {tot / cap[0] * 100:.1f}%, на других моделях: {alt}")
    return page, out, lines, md


# ---------- шаблон отчёта: данные вклеиваются вместо __CHATS__, __SK__, __PARAMS__ и др. (см. шапку) ----------
PAGE = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__NAME__</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%2315181d'/%3E%3Cpath d='M8.2 5.6h3.6v2.6h2.6v3.6h-2.6v2.6H8.2v-2.6H5.6V8.2h2.6z' fill='%23E24B4A'/%3E%3Cpath d='M20.2 5.6h3.6v2.6h2.6v3.6h-2.6v2.6h-3.6v-2.6h-2.6V8.2h2.6z' fill='%231D9E75'/%3E%3Cpath d='M7 25L11 21.5L13.5 23.5' fill='none' stroke='%23E24B4A' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M13.5 23.5L18 19L20.5 20.5' fill='none' stroke='%23EF9F27' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M20.5 20.5L25 16' fill='none' stroke='%231D9E75' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<style>
:root{--bg:#f4f5f7;--card:#fff;--fg:#15181d;--mut:#667085;--faint:#98a2b3;--bd:#e4e7ec;--pn:#f0f2f5;--sel:#eaf1fe;--sh:0 1px 2px rgba(16,24,40,.05),0 1px 3px rgba(16,24,40,.07);
 --k-hv:#98a2b3;--k-hi:#d0d5dd;--k-cold:#f0b429;--k-out:#475467;--ok:#12b76a;--heat:#e8590c}
@media (prefers-color-scheme:dark){:root{--bg:#0f1114;--card:#181b20;--fg:#e9ebee;--mut:#9aa1ab;--faint:#6b7280;--bd:#2a2f36;--pn:#22262c;--sel:#1f2a3d;--sh:none;
 --k-hv:#7a8494;--k-hi:#3e4550;--k-cold:#e0a526;--k-out:#a9b6cc;--ok:#32d583;--heat:#ff7a3d}}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
#app{display:flex;height:100vh}
#side{display:none;width:272px;flex:none;overflow-y:auto;border-right:1px solid var(--bd);background:var(--card)}.adm #side{display:block}
#main{flex:1;min-width:0;overflow-y:auto;overflow-x:hidden}
#view{max-width:1720px;margin:0 auto;padding:22px 26px 44px}
h1{font-size:22px;font-weight:650;margin:0;letter-spacing:-.01em;overflow-wrap:anywhere}
.meta{color:var(--mut);margin-top:3px}
.row{display:flex;flex-wrap:wrap;gap:16px;margin-top:18px;align-items:flex-start}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px 18px;box-shadow:var(--sh);min-width:0}
.card+.card,.row+.card{margin-top:16px}.row .card+.card{margin-top:0}
h2{font-size:13px;font-weight:600;color:var(--mut);margin:0 0 10px}
.mut{color:var(--mut)}b{font-weight:650}
/* переключатели */
.seg{display:inline-flex;background:var(--pn);border-radius:9px;padding:2px;gap:2px;flex-wrap:wrap}
.seg button{border:0;background:transparent;color:var(--mut);font:inherit;font-size:12.5px;padding:4px 10px;border-radius:7px;cursor:pointer}
.seg button:hover{color:var(--fg)}.seg button.on{background:var(--card);color:var(--fg);box-shadow:0 1px 2px rgba(0,0,0,.12);font-weight:600}
/* мозготокены */
.lvs{padding:4px 12px 8px}.lvs .seg{display:flex;flex-wrap:nowrap}.lvs .seg button{flex:1;white-space:nowrap}.it .bh{display:flex;gap:1px;height:6px;margin:5px 0 3px}.it .bh u{flex:1;background:#378ADD;border-radius:1px}
.brain .tph{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.bdays{display:flex;gap:6px;overflow-x:auto;padding:2px 0 10px;margin-bottom:6px}
.bdc{flex:0 0 auto;border:1px solid var(--bd);background:var(--pn);border-radius:10px;padding:6px 9px;text-align:left;cursor:pointer;font:inherit;color:var(--fg);min-width:92px}
.bdc b{display:block;font-size:12.5px}.bdc span,.bdc em{display:block;font-size:11.5px;color:var(--mut);font-style:normal}
.bdc.on{background:var(--sel);border-color:#7F77DD}.bdc .bh{display:flex;gap:1px;height:6px;margin:4px 0 3px}.bdc .bh u{flex:1;background:#378ADD;border-radius:1px}
.bsay{font-size:15.5px;line-height:1.45;margin:4px 0 12px;cursor:help}
.br{display:grid;grid-template-columns:220px 1fr;gap:10px;align-items:center;min-height:24px;border-top:1px solid var(--pn)}
.br .bn{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.br .bn.go-chat{cursor:pointer}.br .bn.go-chat:hover{color:#7F77DD}
.bt{position:relative;height:24px}
.bt .ba{position:absolute;top:5px;height:14px;background:#378ADD;border-radius:2px}
.bt .bx{position:absolute;bottom:1px;opacity:.28;border-radius:1px}
.bt .bp{position:absolute;top:50%;width:var(--s);height:var(--s);border-radius:50%;transform:translate(-50%,-50%);filter:blur(1.6px)}
.br.bk{border-top:0}.bax{height:16px}.bax span{position:absolute;transform:translateX(-50%);font-size:11px;color:var(--mut)}
.bmore summary{cursor:pointer;color:var(--mut);font-size:12.5px;padding:6px 0}
.bw{display:grid;grid-template-columns:220px repeat(7,1fr);gap:4px;align-items:center;margin:3px 0;font-size:12.5px}.bw .bn{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bwc{height:20px;border-radius:5px}
@media (max-width:700px){.br,.bw{grid-template-columns:120px 1fr}.bw{grid-template-columns:120px repeat(7,1fr)}}
/* сколько съел */
.vd{flex:0 0 240px}
.big{font-size:46px;font-weight:700;line-height:1;letter-spacing:-.02em;margin-top:2px}
.bl{color:var(--mut);margin:4px 0 12px}
.sub{color:var(--mut);margin-top:12px;font-size:13px}
.scn{margin-top:12px;padding-top:12px;border-top:1px solid var(--bd);font-size:15px;cursor:default}.scn b{font-size:18px}
.scn .sn{font-size:12.5px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wd{height:20px;margin-top:3px}.wd .x{margin-left:0}
.dpr{display:grid;grid-template-columns:minmax(120px,220px) 1fr 70px;gap:12px;align-items:center;padding:4px 8px;margin:0 -8px;border-radius:8px;cursor:pointer;font-size:13px}
.dpr:hover{background:var(--pn)}.dpr .n{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.dpr .r{text-align:right;color:var(--mut)}
.dtk{position:relative;height:22px}.dtk i{position:absolute;display:block}
.dtk .ax{top:0;bottom:0;width:1px;background:var(--bd)}.dtk .rng{top:9px;height:4px;border-radius:2px;background:var(--k-hi)}
.dtk .d{top:5px;width:12px;height:12px;margin-left:-6px;border-radius:50%;background:var(--c);cursor:default}
.dtk .ring{top:2px;width:18px;height:18px;margin-left:-9px;border-radius:50%;border:2px solid var(--fg);cursor:default}
.x{display:inline-block;font-size:12px;font-weight:650;border-radius:6px;padding:1px 6px;margin-left:4px;background:var(--pn)}
.x.up{color:#d92d20}.x.dn{color:var(--ok)}
/* куда ушли токены */
.cp{flex:1 1 480px}
.hb{display:grid;grid-template-columns:44px 1fr;gap:10px;align-items:center;margin:6px 0}
.hb>span{color:var(--mut);font-size:12.5px}
.hbar{display:flex;height:26px;border-radius:7px;overflow:hidden;min-width:4px}.hbar i{display:block;height:100%;min-width:0}
.hbar i+i{box-shadow:inset 1px 0 0 var(--card)}
.keys{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:12px;font-size:13px}
.key{cursor:default;white-space:nowrap}.key i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.key em{font-style:normal;color:var(--mut)}
/* а если бы */
.wi{flex:1 1 380px;min-width:300px}
.wcs{display:flex;gap:14px;align-items:flex-end;height:142px}
.wc{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;border-radius:10px;padding:4px 0 6px;min-width:52px}
.wc.go{cursor:pointer}.wc.go:hover{background:var(--pn)}
.wv{font-size:12.5px;font-weight:600;margin-bottom:4px;white-space:nowrap}
.wb{width:30px;border-radius:5px 5px 2px 2px;display:flex;flex-direction:column-reverse;overflow:hidden;min-height:3px}.wb i{display:block}
.wn{font-size:12px;color:var(--mut);margin-top:6px;white-space:nowrap}
.wc.on{background:var(--sel)}.wc.on .wn{color:var(--fg);font-weight:650}
.ef{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:10px}.ef>span{color:var(--mut);font-size:12.5px;cursor:default;border-bottom:1px dotted var(--faint)}
.hint{color:var(--faint);font-size:12px;margin-top:8px}
/* лента */
.tph{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 18px;margin-bottom:6px}.tph h2{margin:0;color:var(--fg);font-size:15px}
.lgd{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12.5px;color:var(--mut)}
.chip i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px;background:var(--c)}
.chip.ag i{background:transparent;border:1px dashed var(--mut)}
.chip.hz i{background:repeating-linear-gradient(45deg,var(--fg) 0 2px,transparent 2px 4px);opacity:.6}
.acb{display:flex;height:14px;border-radius:7px;overflow:hidden;background:var(--pn);border:1px solid var(--bd);margin:8px 0 12px}
.acb i{display:block;height:100%}
.rsb{margin-left:10px;font:inherit;font-size:12.5px;padding:2px 10px;border-radius:8px;border:1px solid var(--bd);background:var(--pn);color:var(--fg);cursor:pointer}
.mb.tg{box-shadow:inset 3px 0 0 #1D9E75}.mb.ty{box-shadow:inset 3px 0 0 #EF9F27}.mb.tr{box-shadow:inset 3px 0 0 #E24B4A}
.chip.two i{width:10px;background:linear-gradient(90deg,var(--mut) 0 2px,var(--faint) 2px)}
.tr{display:grid;grid-template-columns:54px 1fr;gap:12px;margin-top:14px}
.tt{font-size:11.5px;color:var(--mut);line-height:1.3;align-self:end;padding-bottom:2px}.tt b{display:block;color:var(--fg);font-size:13px}
.bars{display:grid;grid-template-columns:repeat(150,minmax(0,1fr));column-gap:2px;height:78px;border-bottom:1px solid var(--bd)}
.sl{position:relative;height:100%;cursor:default;border-radius:2px}
.sl:hover,.sl.hl{background:var(--pn)}
.sl i{position:absolute;bottom:0;display:block;background:var(--c)}
.sl .one{left:0;right:0;border-radius:2px 2px 0 0}
.sl .was{left:0;width:2px}
.sl .now{left:2px;right:0;border-radius:0 2px 0 0}
.sl.ag .one,.sl.ag .now{background:color-mix(in srgb,var(--c) 22%,transparent);border:1px dashed var(--c);border-bottom:0}
.cap{color:var(--mut);font-size:12.5px;margin-top:10px}
/* холодные старты */
.cl{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-end;margin-top:14px}
.lead{font-size:15.5px;line-height:1.55;max-width:980px}.lead b{font-size:17px}
.vc{width:96px;text-align:center;cursor:default}
.vc .v{font-size:13px;font-weight:650;margin-bottom:4px}
.vb{display:flex;flex-direction:column;justify-content:flex-end;height:150px}.vb i{display:block;width:100%}
.vb i.gh{border:2px dashed var(--ok);border-bottom:0;border-radius:4px 4px 0 0;background:color-mix(in srgb,var(--ok) 10%,transparent)}
.vb i.top{border-radius:4px 4px 0 0}
.vc .l{font-size:12px;color:var(--mut);margin-top:6px}
.evs{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:flex-start;padding-left:10px;border-left:1px solid var(--bd)}
.ev{width:58px;text-align:center;cursor:default;border-radius:8px;padding:4px 0}.ev:hover{background:var(--pn)}
.ev .s{font-size:11.5px;font-weight:650;height:16px;white-space:nowrap}.ev .s.no{color:var(--faint);font-weight:400}.ev .p i.un{opacity:.45}
.ev .p{height:90px;display:flex;align-items:flex-end;justify-content:center}.ev .p i{display:block;width:16px;border-radius:3px 3px 0 0;background:var(--k-cold);min-height:2px}
.ev .t{font-size:11px;color:var(--mut);line-height:1.25;margin-top:4px}.ev .t b{color:var(--fg);font-weight:600}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;vertical-align:-1px;margin-right:4px}
/* влезет */
.fr{display:grid;grid-template-columns:118px 1fr 120px;gap:12px;align-items:center;margin:7px 0;font-size:13.5px}
.fr .n{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.fr.on .n{font-weight:700}
.tiles{height:20px;border-radius:5px;background-color:var(--pn)}
.fr .r{text-align:right;color:var(--mut)}.fr .r b{color:var(--fg)}
/* обвязка */
.hv{margin-top:14px;border-top:1px solid var(--bd);padding-top:10px}
.hv summary{cursor:pointer;font-size:13px;color:var(--mut);list-style:revert}.hv summary b{color:var(--fg)}
.hv p{font-size:13px;color:var(--mut);margin:8px 0 10px;max-width:760px}
.sr{display:grid;grid-template-columns:minmax(120px,240px) 1fr 150px;gap:10px;align-items:center;margin:4px 0;font-size:12.5px;cursor:default}
.sr .n{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sr .r{color:var(--mut);white-space:nowrap}
.sr .t{height:10px;border-radius:3px;background:var(--pn);overflow:hidden}.sr .t i{display:block;height:100%;background:var(--k-hv);border-radius:3px}
.hv h4{font-size:12.5px;margin:14px 0 4px;font-weight:600}
/* подпись */
.notes{font-size:15px;line-height:1.6;max-width:980px}.notes p{margin:0 0 10px}
.ver{color:var(--faint);font-size:12.5px}
/* центральный */
.dr{display:grid;grid-template-columns:62px 1fr 150px;gap:4px 12px;align-items:center;margin:6px 0;font-size:13px;cursor:pointer}.dr .dx{grid-column:1/-1;display:none;padding:4px 0 8px 74px}.dr.open .dx{display:block}.dr .dx .m{margin-bottom:4px}.dr .dx .tl{display:flex;justify-content:space-between;gap:12px;padding:2px 0;cursor:pointer}.dr .dx .tl:hover span{text-decoration:underline}.pers{margin:2px 0 6px}.pers .seg label{color:var(--mut);font-size:12.5px;padding:2px 4px 2px 10px;border-radius:7px;display:inline-flex;align-items:center;gap:4px;cursor:pointer}.pers .seg label.on{background:var(--card);color:var(--fg);box-shadow:0 1px 2px rgba(0,0,0,.12);font-weight:600}.pers input[type=date]{font:inherit;font-size:12px;border:0;background:transparent;color:inherit;color-scheme:light dark;padding:0}body.busy::after{content:'Пересчитываю…';position:fixed;top:14px;left:50%;transform:translateX(-50%);background:var(--card);color:var(--fg);padding:8px 16px;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.25);z-index:999;font-size:13px}
.dt{position:relative;height:18px}.dt .k{display:flex;height:100%;border-radius:5px;overflow:hidden}.dt .k i{display:block;height:100%}
.dt .bl2{position:absolute;top:-4px;bottom:-4px;width:0;border-left:2px dashed var(--fg);opacity:.45}
.tc{display:grid;grid-template-columns:minmax(140px,260px) 1fr 120px;gap:12px;align-items:center;margin:2px -8px;padding:4px 8px;border-radius:8px;cursor:pointer;font-size:13px}
.tc:hover{background:var(--pn)}.tc .n{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.tc .k{display:flex;height:12px;border-radius:4px;overflow:hidden}.tc .k i{display:block}
.tc .r{color:var(--mut);text-align:right}
.frs div{margin:4px 0;font-size:13.5px}
.fc{color:var(--mut);font-size:13px;margin-top:8px;cursor:default}.fc b{color:var(--fg)}
.row.top{align-items:stretch}
/* доктор: живой талисман дашборда; лицо меняется от effort, по клику — шутка с цифрами недели */
.masc{flex:1 1 220px;min-width:0;display:flex;flex-direction:column;cursor:pointer;user-select:none}
.mrow{flex:1;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.masc svg{flex:none;width:clamp(96px,9vw,173px);height:auto;aspect-ratio:173/200;overflow:visible}
.mb{flex:1 1 160px;min-width:0;position:relative;background:var(--pn);border-radius:14px;padding:12px 14px;font-size:14.5px;line-height:1.45;animation:ld-pop .25s ease-out}
.mb:before{content:"";position:absolute;left:-8px;top:22px;border:8px solid transparent;border-right-color:var(--pn);border-left:0}
.ld-blink{transform-box:fill-box;transform-origin:center;animation:ld-blink 4.5s infinite}
.ld-spin{transform-box:fill-box;transform-origin:center;animation:ld-spin 1.1s linear infinite}
.ld-shake{animation:ld-shake .35s infinite}.ld-z{animation:ld-z 2.4s infinite}.ld-z2{animation:ld-z 2.4s .8s infinite}
.ld-steam{animation:ld-steam 1.4s infinite}.ld-steam2{animation:ld-steam 1.4s .45s infinite}.ld-drop{animation:ld-drop 1.6s infinite}
.masc:active svg{transform:scale(.94)}
@keyframes ld-blink{0%,93%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
@keyframes ld-spin{to{transform:rotate(360deg)}}
@keyframes ld-shake{0%,100%{transform:translate(0,0) rotate(0)}25%{transform:translate(-1.5px,1px) rotate(-2deg)}75%{transform:translate(1.5px,-1px) rotate(2deg)}}
@keyframes ld-z{0%{opacity:0;transform:translate(0,0)}30%{opacity:1}100%{opacity:0;transform:translate(5px,-12px)}}
@keyframes ld-steam{0%{opacity:0;transform:translateY(2px)}50%{opacity:.85}100%{opacity:0;transform:translateY(-9px)}}
@keyframes ld-drop{0%{opacity:0;transform:translateY(-2px)}30%{opacity:1}100%{opacity:0;transform:translateY(7px)}}
@keyframes ld-pop{from{transform:scale(.92);opacity:.3}to{transform:scale(1);opacity:1}}
@media (prefers-reduced-motion:reduce){.masc *{animation:none!important}}
.roi{flex:0 0 200px}
/* тепловая карта */
.hm{display:grid;grid-template-columns:62px repeat(24,minmax(0,1fr)) 64px;gap:3px;align-items:center;font-size:11.5px;margin-top:6px}
.hm i{display:block;height:24px;border-radius:4px;background:color-mix(in srgb,var(--heat) var(--a),var(--pn));cursor:default}
.hm i:hover{outline:2px solid var(--fg);outline-offset:-1px}
.hm .h{color:var(--faint);font-size:10.5px}.hm .d{color:var(--mut)}.hm .s{color:var(--mut);text-align:right;white-space:nowrap}
/* откуда холод */
.cg{font-size:12.5px;font-weight:650;margin:14px 0 2px}.cg span{font-weight:400;color:var(--mut)}
/* список чатов */
.sh{padding:16px 16px 12px;font-weight:700;font-size:16px;display:flex;gap:10px;align-items:center}.sh span{display:block;font-weight:400;font-size:12px;color:var(--mut)}
.it .t svg{vertical-align:-3px;margin-right:6px}
.it{padding:9px 16px;cursor:pointer;border-top:1px solid var(--bd)}.it:hover{background:var(--pn)}.it.sel{background:var(--sel)}
.it .t{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:13.5px}.it .s{font-size:12px;color:var(--mut)}
.it .mx{display:flex;height:4px;border-radius:2px;overflow:hidden;margin-top:5px;background:var(--pn)}.it .mx i{display:block}
#tip{position:fixed;z-index:50;display:none;max-width:350px;background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:12px;padding:10px 12px;font-size:13px;line-height:1.45;box-shadow:0 10px 30px rgba(0,0,0,.2);pointer-events:none}
#tip .m{color:var(--mut)}#tip .tb{display:flex;height:8px;border-radius:4px;overflow:hidden;margin:6px 0 4px}#tip .tb i{display:block}
#tip .cw{margin-top:8px;padding-top:8px;border-top:1px solid var(--bd)}
#tip .cf{position:relative;height:8px;border-radius:4px;margin:7px 0 3px;background:linear-gradient(90deg,#12b76a,#f0b429 50%,#d92d20)}
#tip .cf i{position:absolute;right:0;top:0;bottom:0;background:var(--pn);border-radius:0 4px 4px 0}
#tip .tl{display:flex;justify-content:space-between;gap:12px}#tip .tl span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#tip .dot,.lead .dot{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;background:var(--c)}
.rng{margin-top:14px}
.rtop{display:flex;flex-wrap:wrap;align-items:center;gap:10px 18px}
.rtop .seg{flex-wrap:wrap}.rtop .seg button{font-size:14px;padding:6px 14px;flex:none}
.rlab{font-size:15px;font-weight:600;flex:1 1 240px;min-width:0}.rlab b{color:var(--heat)}
.rin{display:flex;flex-wrap:wrap;gap:8px 12px;color:var(--mut);font-size:12.5px}
.rin input{font:inherit;font-size:13px;border:1px solid var(--bd);border-radius:7px;background:var(--card);color:var(--fg);color-scheme:light dark;padding:3px 6px;margin-left:4px}
.rs{position:relative;height:72px;margin:16px 6px 0;touch-action:none;user-select:none;cursor:crosshair}
.rbars{position:absolute;inset:0;display:flex;gap:1px}
.rbars i{flex:1;min-width:0;display:flex;flex-direction:column-reverse;opacity:.42;border-bottom:2px solid var(--bd)}
.rbars i.on{opacity:1}.rbars i:hover{opacity:.75}.rbars i.on:hover{opacity:1}
.rbars u{display:block;flex:none}
.rb{position:absolute;top:-6px;bottom:-6px;background:rgba(55,138,221,.08);border:2px solid #378ADD;border-radius:7px;pointer-events:none}
.rh{position:absolute;top:-10px;bottom:-10px;width:14px;margin-left:-7px;background:#fff;border-radius:5px;box-shadow:0 1px 5px rgba(0,0,0,.4);cursor:ew-resize;z-index:2}
.rh::after{content:'';position:absolute;left:6px;top:14px;bottom:14px;width:2px;background:#98a2b3}
.rr{position:absolute;top:-6px;bottom:-6px;width:0;border-left:2px dashed var(--heat);z-index:1;opacity:.75;pointer-events:none}
.rr i{position:absolute;top:-9px;left:-6px;width:10px;height:10px;border-radius:50%;background:var(--heat);pointer-events:auto;cursor:help}.rr.go i{cursor:pointer}
.rtk{position:relative;height:16px;margin:10px 6px 0;font-size:11px;color:var(--faint)}
.rtk span{position:absolute;transform:translateX(-50%);white-space:nowrap}.rtk .tn{transform:translateX(-100%);color:var(--mut)}
.rmore{position:absolute;left:-6px;top:-1px;border:0;background:var(--card);color:var(--mut);font:inherit;font-size:11px;cursor:pointer;padding:0 6px 0 0}.rmore:hover{color:var(--fg)}
#rs.drag,#rs.drag *{cursor:ew-resize}
@media(max-width:900px){#view{padding:16px}.vd,.wi{flex:1 1 100%}.tr{grid-template-columns:1fr}.tt{display:flex;gap:8px}.tt b{display:inline}.fr{grid-template-columns:90px 1fr 90px}.sr{grid-template-columns:120px 1fr 110px}.hm{gap:1px;grid-template-columns:52px repeat(24,minmax(0,1fr)) 40px}.hm i{height:18px}}
</style></head>
<body><div id="app"><aside id="side"></aside><main id="main"><div id="view"></div></main></div><div id="tip"></div>
<script>
const CH=__CHATS__,ADMIN=__ADMIN__,GEN='__GEN__',SK=__SK__,P=__PARAMS__,APP='__NAME__',VER='__VER__';
const PR=P.price,MU=P.mult,CAP=[P.cap[0],P.cap[1]/7,P.cap[1]],SUM=P.summary_tokens,CPT=P.chars_per_token,PER=150;
const NM=['Haiku','Sonnet','Opus','Fable'],CL=['#1D9E75','#378ADD','#7F77DD','#D85A30'],EN=['low','medium','high','xhigh','max'];
const WN=['5 часов','сутки','неделя'],WG=['лимита за 5 часов','лимита за сутки','лимита за неделю'];
/* куда уходят токены: четыре части цены */
const BK=[
 {n:'Обвязка',c:'var(--k-hv)',t:'Что Claude Code кладёт в каждый вызов ещё до твоего сообщения: встроенные инструменты, скиллы, память (CLAUDE.md), системные инструкции. Подробно — ниже, «Обвязка подробно».'},
 {n:'Переписка',c:'var(--k-hi)',t:'Модель не помнит разговор: на каждом вызове она заново перечитывает всю переписку. Переписка растёт, и каждый следующий вызов дороже предыдущего.'},
 {n:'Холодные старты',c:'var(--k-cold)',t:'После паузы дольше часа или смены модели переписку пришлось записать заново, а запись в 12–20 раз дороже перечитывания. Подробно — в разделе «Холодные старты».'},
 {n:'Ответы и мысли',c:'var(--k-out)',t:'Что модель написала и сколько думала перед ответом. Effort меняет только эту часть.'}];
const EXP={ok:'Если сжать чат (компакт), пока кэш тёплый, после паузы записывать пришлось бы только короткую выжимку.',no:'Переписка тут короткая: компакт (модель перечитывает весь чат и пишет выжимку) стоил бы не меньше, чем сэкономил.'};
/* причина холодного старта — только то, что видно по логу; av: можно было избежать (пауза — если компакт перед ней сэкономил бы) */
const CAU={sw:{n:'смена модели',g:'Смена модели посреди чата',av:1,t:'Кэш привязан к модели: после смены модели всю переписку пришлось записать заново. Дешевле менять модель в новом чате или сразу после компакта.'},
 idle:{n:'пауза',g:'Пауза дольше часа',av:0,t:'Кэш живёт час: после паузы всю переписку пришлось записать заново.'},
 cmp:{n:'после сжатия',g:'Контекст сжался: компакт или автоочистка',av:0,t:'Переписка укоротилась (компакт или Claude Code убрал старые выводы инструментов), и новое начало пришлось записать. Это цена сжатия, а не потеря.'},
 upd:{n:'обновление',g:'Обновился Claude Code',av:0,t:'Между вызовами сменилась версия Claude Code, а с ней начало контекста.'},
 ttl5:{n:'кэш на 5 минут',g:'Пауза, а кэш был на 5 минут',av:0,t:'Этот кэш был записан на 5 минут, а не на час, и пауза оказалась длиннее.'},
 unk:{n:'без причины',g:'Без видимой причины',av:0,t:'Пауза короче часа, модель та же, контекст не сжимался, а кэш пропал. Так бывает, когда меняется начало контекста: подключили сервис (MCP), поправили CLAUDE.md, перезапустили приложение.'}};
const why=r=>r.cs==='idle'?'пауза '+fG(r.gap):r.cs==='ttl5'?'пауза '+fG(r.gap)+', кэш был на 5 минут':CAU[r.cs].n;
const avTag=r=>r.av?'<span class="x up">можно было избежать</span>':'<span class="x">неизбежно</span>';
let S={c:ADMIN?-1:0,m:-1,e:-1,w:0,hv:false,hc:false,hm:0,xm:0,hh:0,ho:0,bd:null,md:0};
/* доктор говорит только полезное: срезы этой недели (по клику — следующий); при выбранном effort — во что обошлась бы неделя */
function mascHtml(all,vals,fc,BA,days){const wk=x=>fp(x/CAP[2]*100),sumT=(m,e)=>CH.reduce((s,ch)=>s+totals(ch,m,e).t,0),v=k=>vals.find(x=>x.m===k).t;
 const roi=P.since&&P.now?(all/1e6)/(P.plan*12/365*Math.max(1/24,(perEnd()-P.since)/86400)):0;
 let cl=0,av=0,ag=0,big=null;CH.forEach(ch=>{const C=cc(ch,-1);cl+=C.pen;for(const k in C.rows)if(C.rows[k].av)av+=C.rows[k].pen;
  const T=totals(ch,-1,-1);ch.k.forEach((c,i)=>{const x=T.cs[i][0];if(c[9])ag+=x;if(!big||x>big.x)big={x,t:c[0],ch}})});
 const dsum=k=>days[k].reduce((s,x)=>s+x,0),dk=Object.keys(days).sort((a,b)=>dsum(b)-dsum(a))[0],mxT=sumT(-1,4);
 MQ=[`${P.cal&&P.cal.week0===P.since?'Неделя':'За период'}: съедено ≈${fp(all/CAP[2]*100)}% недельного лимита (вилка ${fp(all/P.cap_week_fork[1]*100)}–${fp(all/P.cap_week_fork[0]*100)}%)${fc?`; в таком темпе к сбросу будет ≈${fI(fc)}%`:''}.`,
  roi?`Подписка окупилась ×${fx(roi)}: по ценам API эти вызовы стоили бы $${fI(all/1e6)}.`:'',
  CH[0]?`Больше всех съел «${esc(CH[0].title)}»: ${wk(AG[0].t)}% недели — ${fI(AG[0].t/all*100)}% всего расхода.`:'',
  cl?`Холодные старты — ${wk(cl)}% недели; можно было избежать ${wk(av)}%.`:'',
  `Обвязка — ${fI(BA[0]/all*100)}% всего расхода: её заново читает каждый вызов.`,
  `Вся неделя на Fable стоила бы ${wk(sumT(3,-1))}% лимита, на Haiku — ${wk(sumT(0,-1))}%.`,
  dk?`Самый прожорливый день — ${dk.slice(8)}.${dk.slice(5,7)}: ${fp(dsum(dk)/CAP[1]*100)}% суточного лимита.`:'',
  ag?`Агенты съели ${fI(ag/all*100)}% расхода недели.`:'',
  big?`Самый дорогой вызов — ${fh2(big.x)} в «${esc(big.ch.title)}», ${fd(big.t)}.`:'',
  `Если бы всё шло на effort max: ${wk(mxT)}% лимита — ${ddt(mxT/all)}.`].filter(Boolean);
 const tn=(x,a,b)=>x<a?'g':x<b?'y':'r',TO=[['Неделя',()=>fc?tn(fc,80,100):''],['Подписка',()=>roi>=1?'g':'y'],['Больше всех',()=>AG[0]&&AG[0].t/all>.5?'y':''],
  ['Холодные',()=>tn(av/all*100,1,5)],['Обвязка',()=>BA[0]/all>.5?'y':''],['Самый прожорливый',()=>tn(dsum(dk)/CAP[1],.7,1)]];
 MT=MQ.map(q=>{const r=TO.find(([w])=>q.startsWith(w));return r?r[1]():''});
 MI=Math.min(MI,MQ.length-1);
 const eff=S.e>=0?`Effort ${EN[S.e]} на всю неделю: ${wk(v(-1))}% лимита — ${ddt(v(-1)/all)}.`:'';
 return `<div class="card masc"><div class="mrow">${face(S.e)}<div class="mb${eff||!MT[MI]?'':' t'+MT[MI]}" id="mb">${eff||MQ[MI]}</div></div>${MCL?'':'<div class="hint" id="mh">Нажми на доктора</div>'}</div>`}
const $=id=>document.getElementById(id);
const LOGO=`<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#15181d"/><path d="M8.2 5.6h3.6v2.6h2.6v3.6h-2.6v2.6H8.2v-2.6H5.6V8.2h2.6z" fill="#E24B4A"/><path d="M20.2 5.6h3.6v2.6h2.6v3.6h-2.6v2.6h-3.6v-2.6h-2.6V8.2h2.6z" fill="#1D9E75"/><path d="M7 25L11 21.5L13.5 23.5" fill="none" stroke="#E24B4A" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M13.5 23.5L18 19L20.5 20.5" fill="none" stroke="#EF9F27" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.5 20.5L25 16" fill="none" stroke="#1D9E75" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const SYS=`<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">${CL.map((c,m)=>`<rect x="${m%2*8.5}" y="${(m>>1)*8.5}" width="7.5" height="7.5" rx="2" fill="${c}"/>`).join('')}</svg>`;
/* доктор: лицо по effort (−1 — как было, 0..4 — low…max); глаза-кресты красный и зелёный, рот — график вверх */
function face(st){const X=(cx,cy,f,k)=>{const a=3.4*k,w=1.3*k;return `<path d="M${cx-w} ${cy-a}h${2*w}v${a-w}h${a-w}v${2*w}h${-(a-w)}v${a-w}h${-2*w}v${-(a-w)}h${-(a-w)}v${-2*w}h${a-w}z" fill="${f}"/>`};
 const mouth=pts=>{const P=pts.map(q=>q.join(' '));return `<path d="M${P[0]}L${P[1]}L${P[2]}" fill="none" stroke="#E24B4A" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M${P[2]}L${P[3]}L${P[4]}" fill="none" stroke="#EF9F27" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M${P[4]}L${P[5]}" fill="none" stroke="#1D9E75" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>`};
 const norm=[[7,25],[11,21.5],[13.5,23.5],[18,19],[20.5,20.5],[25,16]];
 let eyes=`<g class="ld-blink">${X(10,10,'#E24B4A',1)}</g><g class="ld-blink">${X(22,10,'#1D9E75',1)}</g>`,m=mouth(norm),extra='',sh='';
 if(st===0){eyes='<path d="M6.5 10.5h7" stroke="#E24B4A" stroke-width="2.4" stroke-linecap="round"/><path d="M18.5 10.5h7" stroke="#1D9E75" stroke-width="2.4" stroke-linecap="round"/>';
  m=mouth([[8,24],[11.5,23],[13.5,23.6],[18,22.4],[20.5,22.9],[24.5,21.6]]);
  extra='<text class="ld-z" x="27" y="4" font-size="6" font-weight="700" fill="#98a2b3">z</text><text class="ld-z2" x="30" y="-1" font-size="8" font-weight="700" fill="#98a2b3">Z</text>'}
 else if(st===1){m=mouth([[7,24],[11,21.8],[13.5,23],[18,20],[20.5,20.8],[25,18]]);extra='<path d="M6.5 3.8l7 .8M18.5 4.6l7-.8" stroke="#98a2b3" stroke-width="1.6" stroke-linecap="round"/>'}
 else if(st===2)extra='<circle cx="10" cy="10" r="5.4" fill="none" stroke="#e9ebee" stroke-width="1.3"/><circle cx="22" cy="10" r="5.4" fill="none" stroke="#e9ebee" stroke-width="1.3"/><path d="M15.4 10h1.2" stroke="#e9ebee" stroke-width="1.3"/>';
 else if(st===3){eyes=`<g class="ld-blink">${X(10,10,'#E24B4A',1.25)}</g><g class="ld-blink">${X(22,10,'#1D9E75',1.25)}</g>`;m=mouth([[6.5,26],[10.5,20],[13,24],[18,16],[20.5,19],[25.5,12]]);
  extra='<path class="ld-drop" d="M29 7c1.6 2.2 2.2 3.4 2.2 4.3a2.2 2.2 0 0 1-4.4 0c0-.9.6-2.1 2.2-4.3z" fill="#378ADD"/>'}
 else if(st===4){eyes=`<g class="ld-spin">${X(10,10,'#E24B4A',1.2)}</g><g class="ld-spin">${X(22,10,'#1D9E75',1.2)}</g>`;m=mouth([[6,27],[10,17],[13,25],[18,11],[21,20],[26,5]]);sh=' class="ld-shake"';
  extra='<circle class="ld-steam" cx="8" cy="-3" r="2.2" fill="#98a2b3"/><circle class="ld-steam2" cx="16" cy="-5" r="2.6" fill="#98a2b3"/><circle class="ld-steam" cx="24" cy="-3" r="2.2" fill="#98a2b3"/>'}
 return `<svg viewBox="-3 -9 38 44"${sh} aria-hidden="true"><rect width="32" height="32" rx="8" fill="#15181d"/>${eyes}${m}${extra}</svg>`}
let MQ=[],MT=[],MI=0,MCL=false;const LIVE=/^https?:$/.test(location.protocol);
function rescan(b){b.disabled=true;b.textContent='Снимаю данные…';location.href='/rescan'}
/* период (админка, --serve): кнопки, поля «от / до» и полоса дней — про одно и то же; сервер пересобирает страницу из логов в памяти */
const PERS=[['1','Сутки','последние 24 часа'],['2','2 дня','последние 48 часов'],['7','Неделя','последние 7 дней'],['all','Всё время','всё, что есть в логах этого компьютера']];
const perK=()=>(P.per||['w'])[0],DAY=86400,WDS=['вс','пн','вт','ср','чт','пт','сб'],perEnd=()=>Math.min(P.until||P.now,P.now);
const fdW2=t=>WDS[D(t).getDay()]+' '+fdd(t),isoD=t=>{const d=D(t);return d.getFullYear()+'-'+z2(d.getMonth()+1)+'-'+z2(d.getDate())};
function perTitle(){const p=perK(),past=P.until&&P.until<P.now;return p==='1'?'за сутки':p==='2'?'за 2 дня':p==='7'?'за неделю':p==='all'?'за всё время':p==='r'||p==='s'?(past?(isoD(P.since)===isoD(P.until-1)?'за '+fdd(P.since):'с '+fdd(P.since)+' по '+fdd(P.until-1)):'с '+fdd(P.since)):p==='d'?'за '+P.per[1]+' сут.':P.cal&&P.cal.week0===P.since?'за неделю лимита':'за 7 дней'}
const cq=()=>S.c>=0&&CH[S.c]?'&c='+encodeURIComponent(CH[S.c].id):'';
function goPer(v){document.body.classList.add('busy');location.href='/period?p='+v+cq()}
function goRange(f,t){document.body.classList.add('busy');location.href='/period?p=r&from='+f+'&to='+t+cq()}
let RW=null;   /* полоса: первый показанный день (null — последние ~45 дней, но так, чтобы начало периода было видно) */
function rngLab(){const a=P.since,b=perEnd(),d=(b-a)/DAY,tm=D(a).getHours()||D(a).getMinutes(),k=Math.round(d),live=b>=P.now-120;
 if(!tm&&!live)return `${fdW2(a)}${k>1?' — '+fdW2(b-1):''} · ${k} ${pl(k,'день','дня','дней')}`;
 return `${fdW2(a)}${tm?' '+fh(a):''} — ${live?'сейчас':fdW2(b-1)} · ${d<1.5?fI(d*24)+' ч':fI(d)+' '+pl(k,'день','дня','дней')}`}
function rngHtml(){if(!LIVE||!ADMIN||!P.strip||!P.strip.v.length)return '';const Z=P.strip,N=Z.v.length,a=P.since,b=perEnd();
 const ia=Math.max(0,Math.floor((a-Z.d0)/DAY)),w0=RW!==null?RW:Math.max(0,Math.min(ia-2,N-45));RW=w0;
 const V=Z.v.slice(w0),n=V.length,t0=Z.d0+w0*DAY,T=V.map(v=>v[0]+v[1]+v[2]+v[3]),mx=Math.max(1,...T),x=t=>Math.max(0,Math.min(100,(t-t0)/(n*DAY)*100));
 const bars=V.map((v,i)=>{const s=t0+i*DAY,on=s+DAY>a&&s<b,tt=T[i]*1e3;
  return `<i class="${on?'on':''}" data-tip="${ea(`<b>${fdW2(s)}</b>: `+(tt?`${fp(tt/CAP[1]*100)}% лимита за сутки · ${fh2(tt)} ≈ ${fUSD(tt)}<div class="cw m">`+v.map((y,m)=>y>0?`<span class="dot" style="--c:${CL[m]}"></span>${NM[m]} ${f1(y/T[i]*100)}%`:'').filter(Boolean).join(' · ')+'</div>':'вызовов нет')+'<div class="cw m">нажми — этот день, тяни — несколько дней</div>')}">${v.map((y,m)=>y>0?`<u style="height:${y/mx*100}%;background:${CL[m]}"></u>`:'').join('')}</i>`}).join('');
 let rs='';if(P.cal&&P.cal.week0&&n<=70){const W7=7*DAY;let r=P.cal.week0;while(r>P.now)r-=W7;for(let k=0;r>t0;r-=W7,k++)if(r<t0+n*DAY)rs+=`<b class="rr${k?'':' go'}" style="left:${x(r)}%"><i data-tip="${ea(`Сброс недельного лимита Claude: ${fdW2(r)} ${fh(r)}`+(k?'':'.<div class="cw m">нажми — неделя лимита с этого сброса до сейчас</div>'))}"${k?'':` onclick="goPer('w')"`}></i></b>`}
 let tk='';for(let i=0;i<n-3;i++){const s=t0+i*DAY;if(D(s).getDay()===1&&(n<=70||Math.round((s-Z.d0)/DAY/7)%2===0)&&(!w0||i>4))tk+=`<span style="left:${(i+.5)/n*100}%">${fdd(s)}</span>`}
 tk+=`<span class="tn" style="left:100%">сегодня</span>`;
 const more=w0>0?`<button class="rmore" onclick="RW=0;draw()" data-tip="${ea('Показать на полосе всю историю логов: с '+fdW2(Z.d0))}">← раньше</button>`:'';
 const mn=isoD(Z.d0),mxD=isoD(P.now),pk=perK();
 return `<div class="card rng"><div class="rtop"><div class="seg">${PERS.map(([v,nm,tp])=>`<button class="${pk===v?'on':''}" data-tip="${ea(tp)}" onclick="goPer('${v}')">${nm}</button>`).join('')}</div>
  <div class="rlab" id="rlab">${rngLab()}</div>
  <div class="rin"><label>от<input type="date" id="rfrom" min="${mn}" max="${mxD}" value="${isoD(a)}"></label><label>до<input type="date" id="rto" min="${mn}" max="${mxD}" value="${isoD(b-1)}"></label></div></div>
  <div class="rs" id="rs"><div class="rbars">${bars}</div>${rs}<div class="rb" style="left:${x(a)}%;width:${Math.max(.6,x(b)-x(a))}%"></div><div class="rh" style="left:${x(a)}%" data-h="0"></div><div class="rh" style="left:${x(b)}%" data-h="1"></div></div>
  <div class="rtk">${more}${tk}</div>
  <div class="cap" style="margin:8px 0 0">Столбик — день: высота — сколько съедено, цвет — модель. Нажми на день или протяни по полосе мышкой — выберешь дни; белые ручки двигают края. Пунктир — сброс недельного лимита Claude.</div></div>`}
const fUSD=x=>'$'+(x<1e7?f1(x/1e6):fI(x/1e6));
/* формат */
const f1=x=>x.toLocaleString('ru-RU',{maximumFractionDigits:1}),fM=x=>f1(x/1e6),fI=x=>Math.round(x).toLocaleString('ru-RU');
const fp=x=>x<0.001?'<0,001':x<0.1?x.toLocaleString('ru-RU',{maximumSignificantDigits:2}):x<10?x.toLocaleString('ru-RU',{maximumFractionDigits:1}):fI(x);
const fx=x=>x<10?x.toLocaleString('ru-RU',{maximumFractionDigits:1}):fI(x);
const fh2=x=>x>=1e6?fM(x)+' млн ХТ':x>=1e3?f1(x/1e3)+' тыс. ХТ':fI(x)+' ХТ';
const fK=x=>x>=1000?f1(x/1000)+' тыс.':fI(x);
const z2=x=>(x<10?'0':'')+x,esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'),ea=s=>esc(s).replace(/"/g,'&quot;');
const D=t=>new Date(t*1000),fdd=t=>z2(D(t).getDate())+'.'+z2(D(t).getMonth()+1),fh=t=>z2(D(t).getHours())+':'+z2(D(t).getMinutes()),fd=t=>fdd(t)+' '+fh(t);
const fT=ms=>{const s=ms/1000;return s<60?fI(s)+' с':Math.floor(s/60)+' мин '+fI(s%60)+' с'},fG=s=>s>=3600?f1(s/3600)+' ч':fI(s/60)+' мин';
const pl=(n,a,b,c)=>{const m=n%10,h=n%100;return m===1&&h!==11?a:m>=2&&m<=4&&(h<12||h>14)?b:c};
const W=x=>x/CAP[S.w]*100;
/* расчёт */
const ctx=c=>c[3]+c[4]+c[5]+c[6];
/* цены вызова: своей версии модели, в сценарии «на другой модели» — самой новой версии семейства; у Haiku 5.5 выше порога — вторая четвёрка */
const prw=(c,m)=>{const r=PR[m===undefined||m<0||m===c[1]?c[12]:P.latest[m]];return r.length>4&&ctx(c)>r[4]?r.slice(5):r};
function cost(c,sm,se){const m=sm<0?c[1]:sm,e0=c[2]<0?1:c[2],e=se<0?e0:se,p=prw(c,sm),om=MU[m][e]/MU[c[1]][e0];
 const rd=c[6]*p[2],wr=c[3]*p[0]+c[4]*p[0]*1.25+c[5]*p[3],ou=c[7]*om*p[1];return [rd+wr+ou,rd,wr,ou]}
function totals(ch,sm,se){const k=sm+'|'+se;ch._t=ch._t||{};if(ch._t[k])return ch._t[k];let t=0;const cs=ch.k.map(c=>{const x=cost(c,sm,se);t+=x[0];return x});return ch._t[k]={t,cs}}
function mixOf(ch,sm,se){const T=totals(ch,sm,se),m=[0,0,0,0];ch.k.forEach((c,i)=>{m[sm<0?c[1]:sm]+=T.cs[i][0]});return m}
/* холодные старты: вызов основной цепочки, где почти весь контекст записан заново */
function ci(ch){if(ch._ci)return ch._ci;const K=ch.k,main=[];K.forEach((c,i)=>{if(!c[9])main.push(i)});
 const ws=main.map(i=>K[i][4]+K[i][5]).filter(w=>w<8000).sort((a,b)=>a-b),g=ws.length?ws[ws.length>>1]:1000,ev=[];
 for(let p=1;p<main.length;p++){const i=main[p],c=K[i],pc=K[main[p-1]],Wr=c[4]+c[5],x=ctx(c),xp=ctx(pc),gap=c[0]-pc[0];
  /* причина: компакт (контекст меньше 60%) → пауза от 59 мин (TTL кэша — час; после неё кэш умер бы и без смены модели)
     → смена модели → обновление Claude Code → подчистка (меньше 90%) → пауза при кэше на 5 минут → не видно */
  if(Wr>=Math.max(P.cold.min_write,P.cold.min_share*x))ev.push({i,p,W:Wr,x,xp,sw:c[12]!==pc[12],gap,
   cs:x<.6*xp?'cmp':gap>=3540?'idle':c[12]!==pc[12]?'sw':c[11]?'upd':x<.9*xp?'cmp':gap>=300&&pc[4]>pc[5]?'ttl5':'unk'})}
 ev.forEach((e,k)=>{e.end=k+1<ev.length?ev[k+1].p:main.length});
 return ch._ci={main,ev,g,floor:main.length?ctx(K[main[0]]):0}}
function cc(ch,sm){ch._cc=ch._cc||{};if(ch._cc[sm])return ch._cc[sm];const I=ci(ch),K=ch.k;let pen=0,sav=0;const rows={};
 I.ev.forEach(e=>{const c=K[e.i],p=prw(c,sm),pw=(c[4]*p[0]*1.25+c[5]*p[3])/e.W,pe=Math.max(0,e.W-I.g)*(pw-p[2]);pen+=pe;
  const pp=prw(K[I.main[e.p-1]],sm),xn=I.floor+SUM,gi=Math.max(0,e.x-e.xp),dl=e.xp-xn;let sv=0;
  if(dl>0&&e.cs!=='cmp'){const old=e.W*pw+c[6]*p[2],cmp=e.xp*pp[2]+SUM*pp[1],nw=(xn+gi)*p[3];let fl=0;
   for(let q=e.p+1;q<e.end;q++)fl+=dl*prw(K[I.main[q]],sm)[2];sv=old-(cmp+nw)+fl}
  sav+=sv;rows[e.i]={pen:pe,sv,sw:e.sw,gap:e.gap,cs:e.cs,av:CAU[e.cs].av||(e.cs==='idle'&&sv>0)}});
 return ch._cc[sm]={pen,sav,rows,I}}
/* разложение цены вызова на четыре части */
function split(ch,i,sm,se){const c=ch.k[i],x=cost(c,sm,se),r=cc(ch,sm).rows[i],pen=r?r.pen:0,fl=ci(ch).floor,base=Math.max(0,x[1]+x[2]-pen),s=fl?Math.min(1,fl/Math.max(1,ctx(c))):0;
 return [base*s,base*(1-s),pen,x[3]]}
function bk(ch,sm,se){const k=sm+'|'+se;ch._b=ch._b||{};if(ch._b[k])return ch._b[k];const b=[0,0,0,0];ch.k.forEach((c,i)=>split(ch,i,sm,se).forEach((v,j)=>b[j]+=v));return ch._b[k]=b}
/* обвязка: системный минимум (контекст первого вызова) по частям, оценка по длине текста в логе */
function hz(ch){const h=ch.h,fl=ci(ch).floor;if(!h||!fl)return null;const ht=bk(ch,-1,-1)[0],tot=totals(ch,-1,-1).t,pt=ht/fl;
 const skl=h.sk>=0?SK.l[h.sk].map(s=>[SK.n[s[0]],s[1]]):[],sum=a=>a.reduce((s,b)=>s+b[1],0);
 const raw=[['Скиллы',sum(skl)],['Память (CLAUDE.md, AGENTS.md)',sum(h.mem)],['Подключённые сервисы (MCP)',sum(h.mcp)],['Списки инструментов и агентов',h.tl+h.ag],['Системный промпт',h.sys]];
 const est=raw.reduce((s,r)=>s+r[1]/CPT,0),k=est>fl?fl/est:1;
 const cats=raw.map(r=>[r[0],r[1]/CPT*k*pt]),rest=Math.max(0,fl-raw.reduce((s,r)=>s+r[1]/CPT*k,0));cats.push(['Встроенные инструменты Claude Code',rest*pt]);
 return {ht,tot,fl,cats,sk:skl.map(s=>[s[0],s[1]/CPT*k*pt]).sort((a,b)=>b[1]-a[1])}}
function hzAll(){const a={ht:0,tot:0,c:{},s:{}};CH.forEach(ch=>{const z=hz(ch);if(!z)return;a.ht+=z.ht;a.tot+=z.tot;z.cats.forEach(c=>{a.c[c[0]]=(a.c[c[0]]||0)+c[1]});z.sk.forEach(s=>{a.s[s[0]]=(a.s[s[0]]||0)+s[1]})});
 return {ht:a.ht,tot:a.tot,fl:0,cats:Object.keys(a.c).map(n=>[n,a.c[n]]),sk:Object.keys(a.s).map(n=>[n,a.s[n]]).sort((x,y)=>y[1]-x[1])}}
/* куски страницы */
const seg=(g,names,off)=>`<div class="seg">${names.map((n,i)=>`<button data-g="${g}" data-v="${i+off}" class="${S[g]===i+off?'on':''}">${n}</button>`).join('')}</div>`;
const scnName=()=>(S.m<0?'модели как были':'на '+NM[S.m])+(S.e<0?'':', effort '+EN[S.e]);
const HTT=`<b>Хайку-токен (ХТ)</b> — единица цены: 1 ХТ = $1 за миллион токенов по ценам API (так стоил вход Haiku 4.5); каждый вызов пересчитан по цене своей версии модели. Лимит плана Max за 5 часов ≈ ${fM(CAP[0])} млн ХТ, за неделю ≈ ${f1(CAP[2]/1e9)} млрд ХТ, за сутки — неделя ÷ 7 (оценка).`;
const dd=k=>{const d=(k-1)*100;return Math.abs(d)<0.5?'<span class="x">так же</span>':`<span class="x ${d>0?'up':'dn'}">${d>0?'+':'−'}${fx(Math.abs(d))}%</span>`};
const ddt=k=>{const d=(k-1)*100;return Math.abs(d)<0.5?'столько же, сколько было':d>0?`на ${fx(d)}% дороже, чем было`:`на ${fx(-d)}% дешевле, чем было`};
const EFT='<b>Effort</b> — сколько модель думает перед ответом. Меняет только «ответы и мысли». По замерам на 11 тыс. вызовов (тот же размер контекста, против medium): low ≈ ×0,65, high ≈ ×1,1, xhigh ≈ ×1,5 (у Sonnet ×2), max ≈ ×3,5 (у Sonnet ×4,6). У Haiku effort нет.';
function verdictCard(A,T,scn,title){const pa=W(A.t),pt=W(T.t),k=T.t/A.t;
 return `<div class="card vd"><h2>${title}</h2><div class="big">${fp(pa)}%</div><div class="bl">${WG[S.w]}</div>${seg('w',WN,0)}
 <div class="sub" data-tip="${ea(HTT)}">${fh2(A.t)} · ${fp(A.t/CAP[2]*100)}% за неделю</div>
 ${scn?`<div class="scn" data-tip="${ea(`<b>${scnName()}</b><br>${fp(pt)}% ${WG[S.w]}: ${ddt(k)}.`)}"><div class="sn">${scnName()}</div><b>${fp(pt)}%</b> ${dd(k)}</div>`:'<div class="scn" style="visibility:hidden"><div class="sn">·</div><b>·</b></div>'}</div>`}
function compCard(BA,tA,BT,tT,hvh,rs){const mx=Math.max(tA,BT?tT:0)||1;
 const tipB=(j,v,t)=>`<b>${BK[j].n}: ${f1(v/t*100)}% цены</b><br>${fh2(v)} · ${fp(W(v))}% ${WG[S.w]}<div class="cw m">${BK[j].t}</div>`;
 const bar=(B,t,lab)=>`<div class="hb"><span>${lab}</span><div class="hbar" style="width:${t/mx*100}%">${B.map((v,j)=>v>0?`<i style="width:${v/t*100}%;background:${BK[j].c}" data-tip="${ea(tipB(j,v,t))}"></i>`:'').join('')}</div></div>`;
 const keys=BK.map((b,j)=>`<span class="key" data-tip="${ea(`<b>${b.n}</b><br>${b.t}`)}"><i style="background:${b.c}"></i>${b.n} <b>${f1(BA[j]/(tA||1)*100)}%</b>${BT?` <em>→ ${f1(BT[j]/(tT||1)*100)}%</em>`:''}</span>`).join('');
 return `<div class="card cp"><h2>Куда ушли токены</h2>${bar(BA,tA,BT||rs?'было':'')}${BT?bar(BT,tT,'стало'):rs?'<div class="hb" style="visibility:hidden"><span>·</span><div class="hbar"></div></div>':''}<div class="keys">${keys}</div>${hvh}</div>`}
function whatifCard(vals,clickable,note){const mx=Math.max(...vals.map(v=>v.t))||1;
 const col=v=>{const h=Math.max(3,v.t/mx*96),on=clickable&&S.m===v.m,
  inner=v.mix?v.mix.map((x,m)=>x>0?`<i style="height:${x/v.t*100}%;background:${CL[m]}"></i>`:'').join(''):`<i style="height:100%;background:${CL[v.m]}"></i>`,
  tp=`<b>${v.m<0?(S.e<0?'Как было':'Модели как были, effort '+EN[S.e]):NM[v.m]+(S.e<0?'':', effort '+EN[S.e])}</b><br>${fp(W(v.t))}% ${WG[S.w]} · ${fh2(v.t)}${v.m<0&&S.e<0?'':'<br>'+ddt(v.k)}`
   +(v.mix&&v.mix.filter(x=>x>0).length>1?'<div class="cw">'+v.mix.map((x,m)=>x>0?`<span class="dot" style="--c:${CL[m]}"></span>${NM[m]} ${f1(x/v.t*100)}%`:'').filter(Boolean).join('<br>')+'</div>':'')
   +(clickable?'<div class="cw m">Нажми, и лента ниже покажет каждый вызов в этом варианте.</div>':'');
  return `<div class="wc${clickable?' go':''}${on?' on':''}" data-m="${v.m}" data-tip="${ea(tp)}"><div class="wv">${fp(W(v.t))}%</div><div class="wb" style="height:${h}px">${inner}</div><div class="wn">${v.m<0?'как было':NM[v.m]}</div><div class="wd">${v.m<0&&S.e<0?'':dd(v.k)}</div></div>`};
 return `<div class="card wi"><h2>А если бы на другой модели</h2><div class="wcs">${vals.map(col).join('')}</div>
 <div class="ef"><span data-tip="${ea(EFT)}">Effort</span>${seg('e',['как был'].concat(EN),-1)}</div>${note?`<div class="hint">${note}</div>`:''}</div>`}
function hvHtml(z,key,scope){if(!z||!z.ht)return '';const tw=x=>fp(x/CAP[2]*100)+'% за неделю',mx=Math.max(...z.cats.map(c=>c[1]),1e-9),sk=z.sk.slice(0,12),rest=z.sk.slice(12),ms=Math.max(1e-9,...sk.map(s=>s[1]));
 const rw=(n,v,m,tip)=>`<div class="sr"${tip?` data-tip="${ea(tip)}"`:''}><div class="n">${esc(n)}</div><div class="t"><i style="width:${v/m*100}%"></i></div><div class="r">${f1(v/z.ht*100)}% · ${tw(v)}</div></div>`;
 const skT=z.sk.reduce((s,x)=>s+x[1],0);
 return `<details class="hv" data-k="${key}"${S[key]?' open':''}><summary><b>Обвязка подробно</b> — ${f1(z.ht/(z.tot||1)*100)}% цены ${scope}, ${tw(z.ht)}${skT?`; из них скиллы — ${tw(skT)}`:''}</summary>
 <p>Обвязку Claude Code кладёт в каждый вызов${z.fl?` (здесь около ${fK(z.fl)} токенов)`:''}, поэтому платишь за неё на каждом шаге. Части оценены по длине текста в логе, это прикидка. Справа — доля обвязки и доля лимита за неделю.</p>
 ${z.cats.slice().sort((a,b)=>b[1]-a[1]).filter(c=>c[1]>0).map(c=>rw(c[0],c[1],mx)).join('')}
 ${sk.length?`<h4>Скиллы по отдельности</h4>`+sk.map(s=>rw(s[0],s[1],ms,`<b>${esc(s[0])}</b><br>Описание скилла лежит в каждом вызове, даже если скилл не запускали.<br>${fh2(s[1])} за период`)).join('')
  +(rest.length?`<div class="mut" style="font-size:12.5px;margin-top:4px">и ещё ${rest.length} ${pl(rest.length,'скилл','скилла','скиллов')}: ${tw(rest.reduce((s,x)=>s+x[1],0))}</div>`:''):''}</details>`}
/* лента */
function tapeHtml(ch,A,T,scn){const K=ch.k,n=K.length;let mxv=0;K.forEach((c,i)=>{mxv=Math.max(mxv,A.cs[i][0],scn?T.cs[i][0]:0)});mxv=mxv||1;
 /* шкала по самому дорогому вызову из «как было» и варианта; самый высокий — 90% ряда, потолка не касается; √ — чтобы мелкие были видны */
 const H=v=>`max(2px,${(Math.sqrt(v/mxv)*90).toFixed(2)}%)`;
 const used=[0,1,2,3].filter(m=>K.some(c=>c[1]===m)||m===S.m),hasAg=K.some(c=>c[9]);
 const lg=used.map(m=>`<span class="chip"><i style="--c:${CL[m]}"></i>${NM[m]}</span>`).join('')+(hasAg?'<span class="chip ag"><i></i>пунктир — агент</span>':'')
  +(scn?`<span class="chip two"><i></i>тонкая линия слева — как было, остальное — ${scnName()}</span>`:'');
 let h='';for(let s=0;s<n;s+=PER){const e=Math.min(n,s+PER);let b='';
  for(let i=s;i<e;i++){const c=K[i],m0=c[1],m=S.m<0?m0:S.m,ag=c[9]?' ag':'';
   b+=scn?`<div class="sl${ag}" data-i="${i}"><i class="was" style="height:${H(A.cs[i][0])};--c:${CL[m0]}"></i><i class="now" style="height:${H(T.cs[i][0])};--c:${CL[m]}"></i></div>`
     :`<div class="sl${ag}" data-i="${i}"><i class="one" style="height:${H(A.cs[i][0])};--c:${CL[m0]}"></i></div>`}
  h+=`<div class="tr"><div class="tt">${fdd(K[s][0])}<br><b>${fh(K[s][0])}</b>→ ${fdd(K[e-1][0])!==fdd(K[s][0])?fd(K[e-1][0]):fh(K[e-1][0])}</div><div class="bars">${b}</div></div>`}
 return `<div class="card"><div class="tph"><h2>Лента вызовов</h2><div class="lgd">${lg}</div></div>${h}
 <div class="cap">Каждый столбик — один вызов модели: прочитала всё и ответила. Выше — дороже. Самые высокие — холодные старты. Наведи на столбик, чтобы увидеть, на что ушли токены.</div></div>`}
const rz=v=>{const s=fx(v);return s.includes(',')?s+' раза':s+' '+pl(Math.round(v),'раз','раза','раз')};
function tipCall(ch,i){const c=ch.k[i],scn=S.m>=0||S.e>=0,x=cost(c,-1,-1),sp=split(ch,i,-1,-1),t=x[0]||1,r=cc(ch,-1).rows[i];
 const eff=c[1]===0?'':` · effort ${c[2]<0?'не записан':EN[c[2]]}`,q=t/(totals(ch,-1,-1).t/ch.k.length);
 /* контекстное окно: 1 млн токенов, у Haiku — 200 тыс.; полоска-светофор, незаполненное — серым */
 const win=P.win200.includes(c[12])?2e5:1e6,fill=Math.min(1,ctx(c)/win);
 let h=`<div><span class="dot" style="--c:${CL[c[1]]}"></span><b>${P.pname[c[12]]||NM[c[1]]}</b>${eff}${c[9]?' · агент':''}</div><div class="m">вызов № ${i+1} · ${fd(c[0])}</div>
 <div style="margin-top:6px">${q>=1.15?`<b>в ${rz(q)} дороже</b> среднего вызова этого чата`:q<=.87?`<b>в ${rz(1/q)} дешевле</b> среднего вызова этого чата`:'<b>как средний вызов</b> этого чата'} <span class="m">· ${fh2(x[0])}</span></div>
 <div class="tb">${sp.map((v,j)=>v>0?`<i style="width:${v/t*100}%;background:${BK[j].c}"></i>`:'').join('')}</div>
 <div class="m">${sp.map((v,j)=>v/t>=.005?`${BK[j].n.toLowerCase()} ${f1(v/t*100)}%`:'').filter(Boolean).join(' · ')}</div>
 <div class="cf"><i style="width:${((1-fill)*100).toFixed(1)}%"></i></div><div class="m">контекст заполнен на ${fI(fill*100)}%: ${fK(ctx(c))} из ${win===1e6?'1 млн':'200 тыс.'} токенов</div>
 <div style="margin-top:4px">написала ${fK(c[7])} токенов${c[8]?' · думала '+fT(c[8]):''}</div>${c[10]?`<div class="m">инструменты: ${esc(c[10])}</div>`:''}`;
 if(r)h+=`<div class="cw"><span class="sw" style="background:var(--k-cold)"></span><b>Холодный старт</b>: ${why(r)} ${avTag(r)}<br>${CAU[r.cs].t}${r.sv>0?' Компакт перед ним сэкономил бы '+fh2(r.sv)+'.':''}</div>`;
 if(scn){const y=cost(c,S.m,S.e)[0];h+=`<div class="cw">Этот вызов ${scnName()}: <b>${ddt(y/t)}</b>.<div class="m">Весь чат — в карточке «Этот чат съел».</div></div>`}
 return h}
/* холодные старты */
function coldHtml(ch,T){const C=cc(ch,S.m),I=C.I,tot=T.t||1,pen=C.pen,sav=C.sav,ok=sav>0,n=I.ev.length,pc=x=>f1(x/tot*100);
 if(!n)return `<div class="card"><h2>Холодные старты</h2><div class="lead">Холодных стартов не было: модель не менялась, а пауз дольше часа не случалось.</div></div>`;
 const H=150,col=(lab,top,body,tip)=>`<div class="vc" data-tip="${ea(tip)}"><div class="v">${top}</div><div class="vb">${body}</div><div class="l">${lab}</div></div>`;
 const was=col('сейчас','100%',`<i class="top" style="height:${pen/tot*H}px;background:var(--k-cold)"></i><i style="height:${(tot-pen)/tot*H}px;background:var(--k-hi)"></i>`,
  `<b>Цена чата сейчас</b><br><span class="sw" style="background:var(--k-cold)"></span>холодные старты: ${pc(pen)}% цены, ${fh2(pen)}`);
 const aft=ok?col('с компактом','−'+pc(sav)+'%',`<i class="gh" style="height:${sav/tot*H}px"></i><i style="height:${(pen-Math.min(pen,sav))/tot*H}px;background:var(--k-cold)"></i><i style="height:${(tot-pen-Math.max(0,sav-pen))/tot*H}px;background:var(--k-hi)"></i>`,
  `<b>Если бы перед каждым холодным стартом был компакт</b><br>Чат стал бы дешевле на ${pc(sav)}%: ${fh2(sav)}. Пунктир — то, что ушло бы.<div class="cw m">${EXP.ok} Допущение: выжимка ${fK(SUM)} токенов.</div>`)
  :col('с компактом','не поможет',`<i style="height:${H}px;background:var(--k-hi);opacity:.5"></i>`,`<b>Компакт не помог бы</b><br>${EXP.no}`);
 const idx=Object.keys(C.rows).map(Number).sort((a,b)=>a-b),shown=idx.slice(0,30),mx=Math.max(1e-9,...shown.map(i=>C.rows[i].pen));
 const evs=shown.map(i=>{const r=C.rows[i],c=ch.k[i];
  const tip=`<b>Холодный старт ${fd(c[0])}</b>: ${why(r)} ${avTag(r)}<br>${CAU[r.cs].t}<br>Лишние ${fh2(r.pen)}: ${pc(r.pen)}% цены чата.<div class="cw">${r.cs==='cmp'?'Компакт уже был.':r.sv>0?'Компакт перед ним сэкономил бы '+fh2(r.sv)+' ('+pc(r.sv)+'% цены чата). '+EXP.ok:'Компакт перед ним ничего бы не сэкономил. '+EXP.no}</div>`;
  return `<div class="ev" data-i="${i}" data-tip="${ea(tip)}"><div class="s${r.av?'':' no'}">${fp(r.pen/tot*100)}%</div><div class="p"><i${r.av?'':' class="un"'} style="height:${r.pen/mx*100}%"></i></div><div class="t">${fdd(c[0])}<br><b>${fh(c[0])}</b><br>${r.cs==='idle'||r.cs==='ttl5'?'пауза '+fG(r.gap):CAU[r.cs].n}</div></div>`}).join('');
 return `<div class="card"><h2>Холодные старты</h2>
 <div class="lead">${n} ${pl(n,'раз','раза','раз')} чат начинал с холодного кэша и записывал переписку заново. Это <b>${pc(pen)}% цены чата</b> (${fp(W(pen))}% ${WG[S.w]}).<br>
 ${ok?`Компакт перед каждым сделал бы чат дешевле на <b>${pc(sav)}%</b>.`:'Компакт перед ними ничего бы не сэкономил: переписка короткая.'}</div>
 <div class="cl">${was}${aft}<div class="evs">${evs}${idx.length>shown.length?`<div class="mut" style="font-size:12px;align-self:center">и ещё ${idx.length-shown.length}</div>`:''}</div></div>
 <div class="cap">Каждый столбик — один холодный старт, число над ним — сколько он стоил в процентах цены чата. Яркие можно было избежать, бледные — неизбежные. Наведи, чтобы увидеть причину.</div></div>`}
/* сколько влезет */
function fitsHtml(ch){const K=ch.k,n=K.length,rows=[-1,0,1,2,3].map(m=>{const t=totals(ch,m,S.e).t,p=W(t),P2=Math.min(p,100),c=m<0?'var(--fg)':CL[m];
 const bg=p>=100?`linear-gradient(${c},${c})`:`repeating-linear-gradient(90deg,${c} 0,${c} calc(${P2}% - 2px),transparent calc(${P2}% - 2px),transparent ${P2}%)`;
 const lab=m<0?'как было':NM[m];
 return `<div class="fr${m===S.m?' on':''}"><div class="n" style="color:${c}">${lab}</div><div class="tiles" style="background-image:${bg};${p>=100?'opacity:.85':''}"></div><div class="r">${p>=100?`не влезет: <b>${fx(p/100)}</b> окна`:(q=>`<b>${fx(q)}</b> ${q%1?'чата':pl(q,'чат','чата','чатов')}`)(Math.floor(100/p*10)/10)}</div></div>`}).join('');
 return `<div class="card"><div class="tph"><h2>Сколько таких чатов влезет в ${['лимит за 5 часов','лимит за сутки','лимит за неделю'][S.w]}</h2>${seg('w',WN,0)}</div><div class="cap" style="margin:0 0 6px">«Такой чат» — этот чат целиком: все ${n} ${pl(n,'вызов','вызова','вызовов')} с ${fd(K[0][0])} по ${fd(K[n-1][0])}${S.e<0?'':', effort '+EN[S.e]}. Одна плитка — один такой чат.</div>${rows}</div>`}
const NOTES=()=>`<div class="card notes"><h2>Как это читать</h2>
<p><b>Вызов</b> — один раз, когда модель прочитала всё и ответила. На один твой вопрос часто приходится несколько вызовов: модель зовёт инструменты (читает файлы, ищет) и после каждого думает заново.</p>
<p><b>Почему длинный чат дорогой.</b> Модель не помнит разговор. На каждом вызове она заново перечитывает всю переписку и обвязку. Перечитывать дёшево, но переписка растёт, и к концу длинного чата почти вся цена уходит на перечитывание.</p>
<p><b>Холодный старт.</b> Кэш живёт около часа и привязан к модели. После паузы или смены модели переписку приходится записать заново, а запись в 12–20 раз дороже перечитывания. На ленте это самые высокие столбики. У каждого подписана причина и можно ли было его избежать.</p>
<p><b>Effort</b> — сколько модель думает перед ответом. Он меняет только «ответы и мысли».</p>
<p>${HTT}</p>
<p><b>Почему проценты меньше, чем в Claude.</b> Здесь только чаты на этом компьютере. Claude в настройках считает весь аккаунт: облачные сессии, другие компьютеры, других людей на том же аккаунте. Поэтому у него процент выше — так и должно быть. Размер лимита Claude не сообщает, мы оценили его один раз и с его процентами не сверяемся.</p>
<p class="ver">${APP} ${VER} · снимок логов ${GEN} · данные не покидают компьютер</p></div>`;
/* страница чата */
function chatView(ch){const n=ch.k.length,A=totals(ch,-1,-1),scn=S.m>=0||S.e>=0,T=scn?totals(ch,S.m,S.e):A,ag=ch.k.filter(c=>c[9]).length;
 const vals=[-1,0,1,2,3].map(m=>{const t=totals(ch,m,S.e).t;return {m,t,k:t/A.t,mix:m<0?mixOf(ch,-1,S.e):null}});
 return `<h1>${esc(ch.title)}</h1><div class="meta">${fd(ch.k[0][0])} → ${fd(ch.k[n-1][0])} · ${n} ${pl(n,'вызов','вызова','вызовов')} модели${ag?`, из них ${ag} — агенты`:''}${ADMIN?` · в отчёте — ${perTitle()}`:''}</div>${rngHtml()}
 <div class="row top">${whatifCard(vals,true,'')}${verdictCard(A,T,scn,'Этот чат съел')}${compCard(bk(ch,-1,-1),A.t,scn?bk(ch,S.m,S.e):null,T.t,hvHtml(hz(ch),'hv','чата'),1)}</div>
 ${tapeHtml(ch,A,T,scn)}${coldHtml(ch,T)}${fitsHtml(ch)}${NOTES()}`}
/* центральный дашборд */
const AG=CH.map(ch=>{const t=totals(ch,-1,-1).t;return {t,m:mixOf(ch,-1,-1)}}),MX=Math.max(1e-9,...AG.map(a=>a.t));
function central(){const days={},dch={},sumT=(sm,se)=>CH.reduce((s,ch)=>s+totals(ch,sm,se).t,0),all=sumT(-1,-1);
 const t0=new Date();t0.setHours(0,0,0,0);let today=0;
 const dtok={};CH.forEach((ch,ci)=>{const T=totals(ch,-1,-1);ch.k.forEach((c,i)=>{const x=T.cs[i][0],d=D(c[0]),k=d.getFullYear()+'-'+z2(d.getMonth()+1)+'-'+z2(d.getDate());(days[k]=days[k]||[0,0,0,0])[c[1]]+=x;const q=dch[k]=dch[k]||{};q[ci]=(q[ci]||0)+x;const w=dtok[k]=dtok[k]||[0,0,0];w[0]+=c[3]+c[4]+c[5]+c[6]+c[7];w[1]+=c[6];w[2]++;if(c[0]>=t0/1000)today+=x})});
 const BA=[0,0,0,0];CH.forEach(ch=>bk(ch,-1,-1).forEach((v,j)=>BA[j]+=v));
 const sw=S.w;S.w=2;
 const mixAll=[0,0,0,0];AG.forEach(a=>a.m.forEach((v,m)=>mixAll[m]+=v));
 const vals=[-1,0,1,2,3].map(m=>{const t=sumT(m,S.e);return {m,t,k:t/all,mix:m<0?(S.e<0?mixAll:CH.reduce((acc,ch)=>{mixOf(ch,-1,S.e).forEach((v,j)=>acc[j]+=v);return acc},[0,0,0,0])):null}});
 const ks=Object.keys(days).sort(),dmx=Math.max(CAP[1],...ks.map(k=>days[k].reduce((a,b)=>a+b,0)));
 const WD=['вс','пн','вт','ср','чт','пт','сб'];
 const dh=ks.map(k=>{const v=days[k],t=v.reduce((a,b)=>a+b,0),w=dtok[k],lab=WD[new Date(+k.slice(0,4),+k.slice(5,7)-1,+k.slice(8)).getDay()]+' '+k.slice(8)+'.'+k.slice(5,7);
  const cs=Object.entries(dch[k]).sort((a,b)=>b[1]-a[1]),row=([ci,x])=>`<div class="tl go-chat" data-i="${ci}"><span>${esc(CH[ci].title)}</span><b>${fp(x/CAP[1]*100)}% · ${fUSD(x)}</b></div>`;
  return `<div class="dr" onclick="if(!event.target.closest('.go-chat'))this.classList.toggle('open')"><div>${lab}</div>
  <div class="dt" data-tip="${ea(`<b>${lab}</b>: ${fp(t/CAP[1]*100)}% лимита за сутки · ${fh2(t)} ≈ ${fUSD(t)}<div class="cw m">`+v.map((x,m)=>x>0?`<span class="dot" style="--c:${CL[m]}"></span>${NM[m]} ${f1(x/t*100)}%`:'').filter(Boolean).join(' · ')+'</div><div class="cw m">нажми — какие чаты съели этот день</div>')}"><div class="k" style="width:${t/dmx*100}%">${v.map((x,m)=>x>0?`<i style="width:${x/t*100}%;background:${CL[m]}"></i>`:'').join('')}</div><div class="bl2" style="left:${CAP[1]/dmx*100}%"></div></div>
  <div class="mut"><b style="color:var(--fg)">${fp(t/CAP[1]*100)}%</b> лимита · ${fUSD(t)}</div>
  <div class="dx"><div class="m">${fI(w[2])} ${pl(w[2],'вызов','вызова','вызовов')} модели · ${fM(w[0])} млн токенов, из них ${f1(w[1]/Math.max(1,w[0])*100)}% — чтение кэша · ${fh2(t)} ≈ ${fUSD(t)} по ценам API</div>${cs.map(row).join('')}</div></div>`}).join('');
 const top=CH.map((ch,i)=>i).slice(0,15).map(i=>{const a=AG[i];return `<div class="tc go-chat" data-i="${i}"><div class="n">${esc(CH[i].title)}</div><div class="k" style="width:${a.t/MX*100}%">${a.m.map((v,m)=>v>0?`<i style="width:${v/a.t*100}%;background:${CL[m]}"></i>`:'').join('')}</div><div class="r"><b style="color:var(--fg)">${fp(a.t/CAP[2]*100)}%</b> недели</div></div>`}).join('');
 const nk=CH.reduce((a,c)=>a+c.k.length,0);
 const per=P.since?(P.cal&&P.cal.week0===P.since?`неделя лимита Claude: с ${fd(P.since)}`:`с ${fd(P.since)}`+(P.until&&P.until<P.now?` по ${fd(P.until-60)}`:''))+' · ':'';
 const html=`<h1>Вся система ${perTitle()}</h1><div class="meta">${per}${CH.length} ${pl(CH.length,'чат','чата','чатов')} · ${fI(nk)} ${pl(nk,'вызов','вызова','вызовов')} модели · снимок логов ${GEN}${LIVE?'<button class="rsb" onclick="rescan(this)">↻ Снять данные</button>':''}</div>
 ${rngHtml()}<div class="row top">${whatifCard(vals,false,(perK()==='w'?'Вся неделя':'Весь период')+' на одной модели. Чат по отдельности — в списке слева.')}<div class="card vd"><h2>Чаты в отчёте съели</h2><div class="big">≈${fp(all/CAP[2]*100)}%</div><div class="bl">недельного лимита</div><div class="mut" style="font-size:12.5px" data-tip="${ea(`Размер лимита Claude не сообщает: 1% недели ≈ ${fM(CAP[2]/100)} млн ХТ по ночным замерам автора (вилка ${fM(P.cap_week_fork[0]/100)}–${fM(P.cap_week_fork[1]/100)}). Проценты на странице приблизительные.`)}">вилка ${fp(all/P.cap_week_fork[1]*100)}–${fp(all/P.cap_week_fork[0]*100)}%</div>
  <div class="sub" data-tip="${ea(HTT)}">${fh2(all)}</div>${P.until&&P.until<P.now?'':`<div class="scn">сегодня: <b>${fp(today/CAP[1]*100)}%</b> лимита за сутки</div>`}${fcLine(all)}</div>
  ${roiCard(all)}${mascHtml(all,vals,fcPct(all),BA,days)}</div>
 ${hourHtml()}${expHtml()}${compCard(BA,all,null,0,hvHtml(hzAll(),'hc','системы'))}
 <div class="card"><h2>Расход по дням</h2><div class="cap" style="margin:0 0 8px">Пунктир — лимит за сутки (неделя ÷ 7). Цвет — модель. Нажми на день — какие чаты его съели, сколько токенов и долларов.</div>${dh}</div>
 ${heatHtml()}
 <div class="card"><h2>Самые дорогие чаты — нажми, чтобы открыть</h2>${top}</div>
 ${coldAllHtml()}${NOTES()}`;
 S.w=sw;return html}
/* мозготокены: ты и токены по дням. Сутки 06–06, 10-минутки. Точка — ты написал (текст, голос, ответ на карточку),
   полоска под ней — сколько этот чат сжёг ХТ за те же 10 минут. Строка — чат; видны все, хвост — под «ещё N». */
let BR=null;const BC=['#7F77DD','#1D9E75','#E8590C','#378ADD','#D6336C','#F0B429','#0CA678','#AE3EC9','#15AABF','#E24B4A','#82C91E','#868E96'];
function brainData(){if(BR)return BR;const B=P.brain,NB=144,nd=B.nd,rows=B.r.map((r,i)=>({n:r[0],h:r[1],x:r[2]}));
 /* время чата: 10-минутка, где ты писал, — её минуты у компа (по ActivityWatch; писал, а у компа не был — 5 минут, телефон),
    без ActivityWatch за день — 10 минут; 10-минутку с репликами в нескольких чатах делим по числу реплик: сумма не больше «у компа» */
 const cnt={};rows.forEach(r=>r.h.forEach(e=>cnt[e[0]]=(cnt[e[0]]||0)+e[1]));
 const awOn=d=>B.aw&&B.aw.slice(d*NB,d*NB+NB).some(v=>v>0),mins=j=>{const d=Math.floor(j/NB);return awOn(d)?(B.aw[j]||5):10};
 rows.forEach(r=>{r.tx=r.x.reduce((s,e)=>s+e[1],0)});
 const days=[];for(let d=0;d<nd;d++){const a=d*NB,b=a+NB,ev=[],bins=new Set(),R=[],src=awOn(d);let xt=0,msg=0;
  rows.forEach(r=>{const h=r.h.filter(e=>e[0]>=a&&e[0]<b),x=r.x.filter(e=>e[0]>=a&&e[0]<b),tx=x.reduce((s,e)=>s+e[1],0);
   if(!h.length&&tx<CAP[2]/2000)return;h.forEach(e=>{bins.add(e[0]);ev.push([e[0],r.n]);msg+=e[1]});xt+=tx;
   R.push({r,h,x,tm:h.reduce((s,e)=>s+mins(e[0])*e[1]/cnt[e[0]],0),tx})});
  R.sort((p,q)=>q.tm-p.tm||q.tx-p.tx);ev.sort((p,q)=>p[0]-q[0]);let sw=0;for(let i=1;i<ev.length;i++)if(ev[i][1]!==ev[i-1][1]&&ev[i][0]-ev[i-1][0]<3)sw++;
  const aw=src?B.aw.slice(a,b).reduce((s,v)=>s+v,0):bins.size*10;
  /* пик — двухчасовое окно с наибольшим числом 10-минуток, где ты писал */
  let pk=-1,pv=0;for(let s0=0;s0<NB-11;s0+=6){let v=0;bins.forEach(j=>{if(j-a>=s0&&j-a<s0+12)v++});if(v>pv){pv=v;pk=s0}}
  days.push({d,t:B.t0+d*86400,a,R,xt,msg,sw,aw,load:aw+5*sw,pk,src})}
 /* порядок и цвет строк — по твоему времени за все дни */
 rows.forEach(r=>r.tm=days.reduce((s,x)=>s+((x.R.find(q=>q.r===r)||{}).tm||0),0));rows.sort((a,b)=>b.tm-a.tm||b.tx-a.tx);rows.forEach((r,i)=>r.c=BC[i%BC.length]);
 const wk=days.filter(x=>x.aw>60).map(x=>x.load).sort((p,q)=>p-q),med=wk.length?wk[wk.length>>1]:0;days.forEach(x=>x.res=med?x.load/med*100:0);
 return BR={rows,days,med}}
const WDN=['вс','пн','вт','ср','чт','пт','сб'],fdW=t=>WDN[D(t).getDay()]+' '+fdd(t),fhM=m=>m>=60?f1(m/60)+' ч':fI(m)+' мин';
const hh=j=>z2((6+Math.floor(j/6))%24);
function brainPage(){const B=P.brain,Z=brainData(),days=Z.days;
 if(S.bd===null){S.bd=days.length-1;while(S.bd>0&&!days[S.bd].msg)S.bd--}
 const src=B.aw?'по ActivityWatch, где его нет — по твоим репликам':'по твоим репликам: ActivityWatch не нашёлся, 10-минутка с репликой = 10 минут';
 return `<h1>Мозготокены</h1><div class="meta">где и когда ты работал · время у компа — ${src} · снимок логов ${GEN}${LIVE?'<button class="rsb" onclick="rescan(this)">↻ Снять данные</button>':''}</div>
  <div class="card brain">${S.bd===-1?brainWeek(Z):brainDay(Z,days[S.bd])}</div>`}
function brainDay(Z,x){const NB=144,top=x.R.filter(q=>q.tm).slice(0,2).map(q=>`${esc(q.r.n)} (${fhM(q.tm)})`),bx=x.R.slice().sort((p,q)=>q.tx-p.tx)[0];
 const say=`${fdW(x.t)}: ~${fhM(x.aw)} у компа${x.src?'':' (по репликам)'}${x.msg?`, ты написал ${x.msg} ${pl(x.msg,'раз','раза','раз')}`:''}.${top.length?' Больше всего — '+top.join(' и ')+'.':''}${x.pk>=0&&x.msg?` Пик — ${hh(x.pk)}–${hh(x.pk+12)}.`:''}${x.res?` Ресурса ушло ${fI(x.res)}% от обычного дня.`:''}`;
 const why=`<b>Ресурс дня</b> = минуты у компа + 5 минут за каждое переключение между чатами посреди работы (соседние реплики в разных чатах, меньше 30 минут между ними). 100% — медиана по дням, где у компа больше часа.<br>Сегодня: ${fhM(x.aw)} + 5 × ${x.sw} = ${fhM(x.load)}${Z.med?`, обычный день — ${fhM(Z.med)}`:''}.`;
 const L=j=>(j/NB*100).toFixed(3)+'%',W=(100/NB).toFixed(3)+'%';
 let aw='';if(x.src){for(let j=0;j<NB;j++){const v=P.brain.aw[x.a+j]||0;if(v)aw+=`<i class="ba" style="left:${L(j)};width:${W};opacity:${.25+v/10*.75}"></i>`}}
 else{const bs=new Set();x.R.forEach(q=>q.h.forEach(e=>bs.add(e[0]-x.a)));bs.forEach(j=>{aw+=`<i class="ba" style="left:${L(j)};width:${W};opacity:.45"></i>`})}
 const mxX=Math.max(1,...x.R.flatMap(q=>q.x.map(e=>e[1])));
 const row=q=>{const ci=CH.findIndex(c=>c.title===q.r.n),tx=q.h.slice(0,3).map(e=>`<div class="m">${fh(P.brain.t0+e[0]*600)} — ${esc(e[2])}</div>`).join('');
  const lab=`<div class="bn${ci>=0?' go-chat':''}"${ci>=0?` data-i="${ci}"`:''} data-tip="${ea(`<b>${esc(q.r.n)}</b>: ты — ${fhM(q.tm)}${tx?'<div class="cw">'+tx+'</div>':''}${ci>=0?'<div class="cw m">нажми — откроется чат</div>':''}`)}"><span class="dot" style="--c:${q.r.c}"></span>${esc(q.r.n)} <span class="mut">${fhM(q.tm)}</span></div>`;
  const hs=q.h.map(e=>`<i class="bp" style="left:${L(e[0]-x.a+.5)};--s:${Math.min(18,9+e[1]*1.5).toFixed(0)}px;background:${q.r.c};opacity:${Math.min(.95,.45+e[1]/8).toFixed(2)}" data-tip="${ea(`${fh(P.brain.t0+e[0]*600)} · ${esc(q.r.n)}: ${e[1]} ${pl(e[1],'реплика','реплики','реплик')}<div class="m">${esc(e[2])}</div>`)}"></i>`).join('');
  return `<div class="br">${lab}<div class="bt">${hs}</div></div>`};
 const main=x.R.filter(q=>q.tm>0),tail=[];
 const ax=[0,3,6,9,12,15,18,21,24].map(h=>`<span style="left:${h/24*100}%">${z2((6+h)%24)}</span>`).join('');
 return `<div class="bsay" data-tip="${ea(why)}">${say}</div>
  <div class="br bk"><div class="bn"><b>за компом</b> <span class="mut">${fhM(x.aw)}</span></div><div class="bt">${aw}</div></div>
  ${main.map(row).join('')}${tail.length?`<details class="bmore"><summary>ещё ${tail.length} ${pl(tail.length,'чат','чата','чатов')} — понемногу</summary>${tail.map(row).join('')}</details>`:''}
  <div class="br"><div class="bn"></div><div class="bt bax">${ax}</div></div>
  <div class="cap">Шарик — ты писал в этот чат (текстом, голосом или ответом на карточку), крупнее и ярче — больше реплик за 10 минут. Наведи — увидишь, что писал. Сколько при этом сгорело токенов — в разделе «Токены».</div>`}
function brainWeek(Z){const ds=Z.days.slice(-7),rows=Z.rows.map(r=>({r,v:ds.map(x=>{const q=x.R.find(q=>q.r===r);return q?[q.tm,q.tx]:[0,0]})})).map(o=>({...o,tm:o.v.reduce((s,v)=>s+v[0],0),tx:o.v.reduce((s,v)=>s+v[1],0)})).filter(o=>o.tm).sort((a,b)=>b.tm-a.tm||b.tx-a.tx);
 const mx=Math.max(1,...rows.flatMap(o=>o.v.map(v=>v[0]))),aw=ds.reduce((s,x)=>s+x.aw,0),wd=ds.filter(x=>x.aw>60),xt=ds.reduce((s,x)=>s+x.xt,0);
 const say=`Неделя ${fdd(ds[0].t)}–${fdd(ds[ds.length-1].t)}: ~${fhM(aw)} у компа${wd.length?`, в среднем ~${fhM(wd.reduce((s,x)=>s+x.aw,0)/wd.length)} в рабочий день`:''}. Главное — ${rows.slice(0,3).map(o=>esc(o.r.n)).join(', ')}.`;
 const head=`<div class="bw"><div></div>${ds.map(x=>`<div class="mut">${fdW(x.t)}</div>`).join('')}</div>`;
 const row=o=>`<div class="bw"><div class="bn" data-tip="${ea(`<b>${esc(o.r.n)}</b>: ты — ${fhM(o.tm)} за неделю`)}"><span class="dot" style="--c:${o.r.c}"></span>${esc(o.r.n)} <span class="mut">${fhM(o.tm)}</span></div>${o.v.map((v,i)=>`<div class="bwc" style="background:${o.r.c};opacity:${v[0]?.18+v[0]/mx*.82:.04}" data-tip="${ea(`<b>${fdW(ds[i].t)}</b> · ${esc(o.r.n)}<br>ты — ${v[0]?fhM(v[0]):'не писал'}`)}"></div>`).join('')}</div>`;
 const main=rows,tail=[];
 return `<div class="bsay">${say}</div>${head}${main.map(row).join('')}${tail.length?`<details class="bmore"><summary>ещё ${tail.length} ${pl(tail.length,'чат','чата','чатов')} — понемногу</summary>${tail.map(row).join('')}</details>`:''}<div class="cap">Клетка — день. Ярче — дольше ты писал в этот чат.</div>`}
/* холодные старты всей системы: стоит ли с ними бороться */
function coldAllHtml(){let pen=0,sav=0,n=0;const rows=CH.map((ch,i)=>{const C=cc(ch,-1);pen+=C.pen;sav+=C.sav;n+=C.I.ev.length;return {i,pen:C.pen,sav:C.sav,n:C.I.ev.length}}).filter(r=>r.n).sort((a,b)=>b.pen-a.pen);
 if(!n)return '';const all=AG.reduce((s,a)=>s+a.t,0),wk=x=>fp(x/CAP[2]*100),mx=Math.max(1e-9,...rows.map(r=>r.pen)),h5=sav/CAP[0];
 const list=rows.slice(0,10).map(r=>`<div class="tc go-chat" data-i="${r.i}" data-tip="${ea(`<b>${esc(CH[r.i].title)}</b><br>${r.n} ${pl(r.n,'холодный старт','холодных старта','холодных стартов')}: ${wk(r.pen)}% лимита за неделю.<br>${r.sav>0?'Компакт перед каждым сэкономил бы '+wk(r.sav)+'%.':'Компакт перед ними ничего бы не сэкономил.'}`)}"><div class="n">${esc(CH[r.i].title)}</div><div class="k" style="width:${r.pen/mx*100}%"><i style="width:100%;background:var(--k-cold)"></i></div><div class="r"><b style="color:var(--fg)">${wk(r.pen)}%</b> за неделю</div></div>`).join('');
 /* откуда холод: причины с ценой, «можно было избежать» сверху */
 const G={};CH.forEach(ch=>{const R=cc(ch,-1).rows;for(const k in R){const r=R[k],key=r.cs==='idle'?(r.sv>0?'idle+':'idle-'):r.cs,g=G[key]=G[key]||{n:0,pen:0,sv:0};g.n++;g.pen+=r.pen;g.sv+=r.sv}});
 const CN={'idle+':['Пауза дольше часа без компакта','Компакт перед паузой сэкономил бы: после неё записывать пришлось бы только короткую выжимку.'],
  'idle-':['Пауза дольше часа','Переписка была короткая: компакт перед паузой ничего бы не сэкономил.']},cn=k=>CN[k]||[CAU[k].g,CAU[k].t];
 const AV=['sw','idle+'],UN=['idle-','cmp','upd','ttl5','unk'],cm=Math.max(1e-9,...Object.values(G).map(g=>g.pen)),gs=ks=>ks.reduce((s,k)=>s+(G[k]?G[k].pen:0),0);
 const crow=k=>{const g=G[k];if(!g)return '';const [nm,t]=cn(k);
  return `<div class="tc" style="cursor:default" data-tip="${ea(`<b>${nm}</b><br>${g.n} ${pl(g.n,'раз','раза','раз')} · ${wk(g.pen)}% лимита за неделю, ${f1(g.pen/pen*100)}% всего холода${g.sv>0?'<br>Компакт перед каждым вернул бы '+wk(g.sv)+'%.':''}<div class="cw m">${t}</div>`)}"><div class="n">${nm} <span class="mut">· ${g.n}</span></div><div class="k" style="width:${g.pen/cm*100}%"><i style="width:100%;background:var(--k-cold)${UN.includes(k)?';opacity:.45':''}"></i></div><div class="r"><b style="color:var(--fg)">${wk(g.pen)}%</b> за неделю</div></div>`};
 const src=(gs(AV)?`<div class="cg">Можно было избежать <span>— ${wk(gs(AV))}% лимита за неделю</span></div>${AV.map(crow).join('')}`:'')
  +(gs(UN)?`<div class="cg">Неизбежно <span>— ${wk(gs(UN))}% лимита за неделю</span></div>${UN.map(crow).join('')}`:'');
 return `<div class="card"><h2>Холодные старты всей системы</h2>
 <div class="lead">За неделю чаты ${n} ${pl(n,'раз','раза','раз')} начинали с холодного кэша. Это <b>${wk(pen)}% лимита за неделю</b>, ${f1(pen/all*100)}% всего расхода.<br>
 ${sav>0?`Компакт перед каждым сэкономил бы <b>${wk(sav)}% лимита за неделю</b>${h5>=.5?` — это примерно ${fx(h5)} ${pl(Math.round(h5),'лимит','лимита','лимитов')} за 5 часов`:''}.`:'Компакт перед ними в сумме ничего бы не сэкономил.'}</div>
 <div class="cap" style="margin:12px 0 0">Откуда холод — наведи на строку, чтобы увидеть объяснение:</div>${src}
 <div class="cap" style="margin:16px 0 6px">В каких чатах холодные старты съели больше всего — нажми, чтобы открыть:</div>${list}</div>`}
/* когда горит лимит: строка — день, клетка — час. «Эта неделя» — даты с начала недели, из чатов отчёта;
   «обычная неделя» — дни недели в среднем за последние недели (heat из питона, с тремя главными чатами в клетке) */
const WD=['пн','вт','ср','чт','пт','сб','вс'];
function heatHtml(){const H=P.heat;if(!H)return '';let rows=[],wk=1;
 const top=(o,k)=>Object.entries(o).sort((a,b)=>b[1]-a[1]).slice(0,k);
 if(S.hm){wk=Math.max(1,H.days/7);for(let d=0;d<7;d++)rows.push({lab:WD[d],v:H.v.slice(d*24,d*24+24).map(x=>x/wk),
   who:H.top.slice(d*24,d*24+24).map(t=>t.map(([ni,x])=>[H.names[ni],x/wk]))})}
 else{const by={};CH.forEach(ch=>{const T=totals(ch,-1,-1);ch.k.forEach((c,i)=>{const d=D(c[0]),key=fdd(c[0]),h=d.getHours();
   const r=by[key]=by[key]||{t:c[0],lab:WD[(d.getDay()+6)%7]+' '+key,v:new Array(24).fill(0),w:[...Array(24)].map(()=>({}))};
   r.t=Math.min(r.t,c[0]);r.v[h]+=T.cs[i][0];r.w[h][ch.title]=(r.w[h][ch.title]||0)+T.cs[i][0]})});
  rows=Object.values(by).sort((a,b)=>a.t-b.t).map(r=>({lab:r.lab,v:r.v,who:r.w.map(o=>top(o,5))}))}
 const mx=Math.max(1e-9,...rows.flatMap(r=>r.v)),pd=x=>x>0?fp(x/CAP[1]*100)+'%':'—',avg=S.hm?', в среднем за неделю':'';
 let h='<div></div>'+[...Array(24)].map((_,j)=>`<div class="h">${j%3?'':j}</div>`).join('')+'<div class="h" style="text-align:right">за сутки</div>';
 rows.forEach(r=>{let s=0;h+=`<div class="d">${r.lab}</div>`;
  r.v.forEach((x,j)=>{s+=x;const who=r.who[j].map(([nm,y])=>`<div class="tl"><span>${esc(nm)}</span><b>${fh2(y)} · ${fI(y/x*100)}%</b></div>`).join('');
   h+=`<i style="--a:${x>0?Math.max(6,Math.sqrt(x/mx)*100).toFixed(0):0}%" data-tip="${ea(`<b>${r.lab}, ${z2(j)}:00–${z2((j+1)%24)}:00</b>${avg}<br>${x>0?`сгорело <b>${fh2(x)}</b><br>${fp(x/CAP[0]*100)}% лимита за 5 часов · ${fp(x/CAP[1]*100)}% за сутки · ${fp(x/CAP[2]*100)}% за неделю<div class="cw"><div class="m">кто съел — токены и доля часа:</div>${who}</div>`:'ничего не потрачено'}`)}"></i>`});
  h+=`<div class="s">${pd(s)}</div>`});
 const L1=P.cal&&P.cal.week0===P.since?'эта неделя':'период отчёта',since=fdd(P.now-H.days*86400);
 return `<div class="card"><div class="tph"><h2>Когда горит лимит</h2>${seg('hm',[L1,'обычная неделя'],0)}</div>
 <div class="cap" style="margin:0 0 4px">${S.hm?`Дни недели в среднем за последние ${fI(H.days)} ${pl(Math.round(H.days),'день','дня','дней')} (с ${since}) — видно привычку: в какие дни и часы обычно горит лимит.`:`Строка — день, клетка — час.`} Чем ярче клетка, тем больше лимита съедено в этот час. Справа — весь день в % лимита за сутки. Наведи на клетку — сколько сгорело и какие чаты жрали.</div><div class="hm">${h}</div></div>`}
/* подписка окупилась: те же вызовы по ценам API (1 ХТ = $1 за миллион) против доли подписки за те же дни */
function roiCard(all){if(!P.since||!P.now)return '';const days=Math.max(1/24,(perEnd()-P.since)/86400),usd=all/1e6,sub=P.plan*12/365*days,k=usd/sub;
 const tip=`<b>${k>=1?'Подписка окупилась':'Подписка пока не окупилась'}</b><br>Те же вызовы по ценам Claude API стоили бы $${fI(usd)}. Подписка $${fI(P.plan)} в месяц — за эти ${f1(days)} дн. это $${fI(sub)}.<div class="cw m">Цены API за миллион входных токенов у новых моделей: Haiku 5.5 $0,1, Sonnet 5.5 $2, Opus 5.5 $4, Fable 5.2 $8; старые версии — по своим ценам. 1 ХТ = $1 за миллион. Считаются только чаты на этом компьютере. Цена плана — флаг --plan.</div>`;
 return `<div class="card vd roi" data-tip="${ea(tip)}"><h2>${k>=1?'Подписка окупилась':'Подписка пока не окупилась'}</h2><div class="big">×${fx(k)}</div><div class="bl">за ${f1(days)} ${days%1?'дня':pl(days,'день','дня','дней')}</div>
 <div class="sub">по ценам API <b style="color:var(--fg)">$${fI(usd)}</b><br>подписка за эти дни $${fI(sub)}</div></div>`}
/* прогноз к сбросу: средний темп с начала недели лимита, не раньше чем через 12 часов */
const fcPct=all=>{const w0=P.cal&&P.cal.week0;if(!w0||P.since!==w0||!P.now||P.now-w0<12*3600)return 0;return all/CAP[2]*100*7*86400/(P.now-w0)};
function fcLine(all){const w0=P.cal&&P.cal.week0;if(!w0||P.since!==w0||!P.now)return '';const el=P.now-w0,pct=all/CAP[2]*100;if(el<12*3600||pct<=0)return '';
 const end=w0+7*86400,f=pct*7*86400/el,wd=t=>['вс','пн','вт','ср','чт','пт','сб'][D(t).getDay()]+' '+fh(t);
 const tip=`<b>Прогноз по среднему темпу недели</b><br>С начала недели прошло ${f1(el/86400)} дн., съедено ${fp(pct)}%. Если тратить так же, к сбросу (${wd(end)}) будет ≈${fI(f)}%.<div class="cw m">Только чаты на этом компьютере: если аккаунт общий, у Claude процент может быть больше.</div>`;
 return f<100?`<div class="fc" data-tip="${ea(tip)}">в таком темпе к сбросу будет ≈<b>${fI(f)}%</b></div>`
  :`<div class="fc" data-tip="${ea(tip)}">в таком темпе лимит кончится ≈ <b>${wd(w0+el*100/pct)}</b></div>`}
/* сравнение чатов: тот же чат на каждой модели или на каждом effort. Шкала общая для всех переключателей
   (максимум по всем моделям и effort), поэтому точки ездят, а не прилипают к правому краю */
const EC=['#9FE1CB','#1D9E75','#378ADD','#7F77DD','#D85A30'];
function expHtml(){const rows=CH.map((ch,i)=>i).slice(0,14),byE=S.xm===1,wk=x=>fp(x/CAP[2]*100);
 const mx=Math.max(1e-9,...rows.map(i=>{const ch=CH[i];let m=0;for(let e=-1;e<5;e++)for(let k=-1;k<4;k++)m=Math.max(m,totals(ch,k,e).t);return m})),X=x=>(x/mx*96).toFixed(2);
 const V=rows.map(i=>({i,a:totals(CH[i],-1,-1).t,v:byE?[0,1,2,3,4].map(e=>totals(CH[i],-1,e).t):[0,1,2,3].map(m=>totals(CH[i],m,S.e).t)}));
 const ticks=[.24,.48,.72,.96].map(f=>`<i class="ax" style="left:${f*100}%"></i>`).join('');
 const nm=j=>byE?'effort '+EN[j]:'на '+NM[j]+(S.e<0?'':', effort '+EN[S.e]),col=j=>byE?EC[j]:CL[j];
 const body=V.map(r=>{const lo=Math.min(...r.v),hi=Math.max(...r.v);
  return `<div class="dpr go-chat" data-i="${r.i}"><div class="n">${esc(CH[r.i].title)}</div><div class="dtk">${ticks}<i class="rng" style="left:${X(lo)}%;width:${(X(hi)-X(lo)).toFixed(2)}%"></i>`
  +r.v.map((x,j)=>`<i class="d" style="left:${X(x)}%;--c:${col(j)}" data-tip="${ea(`<b>${esc(CH[r.i].title)} ${nm(j)}</b>${byE?' (модели как были)':''}<br>${wk(x)}% лимита за неделю · ${ddt(x/r.a)}`)}"></i>`).join('')
  +`<i class="ring" style="left:${X(r.a)}%" data-tip="${ea(`<b>${esc(CH[r.i].title)}: как было</b><br>${wk(r.a)}% лимита за неделю`)}"></i></div><div class="r" data-tip="${ea(`<b>${esc(CH[r.i].title)}</b><br>на самом деле съел ${wk(r.a)}% лимита за неделю`)}">${wk(r.a)}%</div></div>`}).join('');
 const lg=(byE?EN.map((e,j)=>`<span class="chip"><i style="--c:${EC[j]};border-radius:50%"></i>${e}</span>`):[0,1,2,3].map(m=>`<span class="chip"><i style="--c:${CL[m]};border-radius:50%"></i>${NM[m]}</span>`)).join('');
 const WH=byE?'<b>По effort.</b> Модели в каждом чате остаются как были, меняется только effort — от low до max. Цветная точка — сколько чат съел бы на этом effort, кольцо — сколько съел на самом деле.'
  :'<b>По моделям.</b> Весь чат пересчитан на одну модель: Haiku, Sonnet, Opus или Fable. Effort — тот, что выбран справа («как был» — как на самом деле). Кольцо — сколько чат съел на самом деле.';
 return `<div class="card"><div class="tph"><h2>Сравнение чатов: тот же чат ${byE?'на каждом effort':'на каждой модели'} <span class="mut" style="font-weight:400;border-bottom:1px dotted var(--faint);cursor:help" data-tip="${ea(WH+'<div class="cw m">Проценты справа и в подсказках — доля лимита за неделю, которую чат съел.</div>')}">что это?</span></h2>${seg('xm',['по моделям','по effort'],0)}${byE?'':seg('e',['effort как был'].concat(EN),-1)}</div>
 <div class="lgd" style="margin:4px 0 10px">${lg}<span class="chip"><i style="background:none;border:2px solid var(--fg);border-radius:50%"></i>как было</span><span>чем дальше точки друг от друга, тем сильнее ${byE?'effort':'модель'} меняет цену чата; справа — % лимита за неделю</span></div>
 ${body}<div class="cap">${byE?'Модели как были, меняется только effort. Видно, во что обходится max против xhigh. Шкала та же, что по моделям.':'Видно, где Fable избыточен, а где Sonnet и Opus стоят почти одинаково. Шкала одна для всех effort: точки двигаются, а не прилипают к краю.'} Нажми на чат, чтобы открыть его.</div></div>`}
let CUM=null;
/* весь аккаунт и наши чаты: верхняя линия — проценты Claude (account.jsonl), нижняя — наши чаты нарастающим итогом
   с начала недели; разрыв — другие устройства и люди. Где замеров не было — пунктир: что там было, неизвестно */
/* по часам: наши чаты и то, чего не видно в логах (FR-17), сверху полоса «моя часть аккаунта» (FR-16). Наши — точно, по логам
   (P.hrs — по часам за 14 суток, из питона); «не видно в логах» = прирост процента Claude между замерами − наш расход за то же
   время, поровну на часы промежутка (штриховка). Неделя Claude начинается с 0%: от сброса до первого замера — тоже промежуток */
let HR=null;
const NV='Claude считает весь аккаунт, а в логах этого компьютера видно не всё. Сюда попадает: другие люди и компьютеры на том же аккаунте, claude.ai в браузере и на телефоне, запуски без сохранения сессии (<b>claude -p --no-session-persistence</b>), служебные вызовы приложения. И ошибка оценки размера лимита: если он на деле меньше, наша доля больше.';
function hourHtml(){const H=P.hrs;if(!P.since||!P.now||!H||(P.until&&P.until<P.now))return '';const W=CAP[2],now=P.now,S0=P.cal&&P.cal.week0>P.since?P.cal.week0:Math.max(P.since,P.now-7*86400),wk0=P.cal&&P.cal.week0===S0,W7=7*86400,NN=P.heat.names,PU='#7F77DD';
 if(!HR){HR=[];CH.forEach(ch=>{const T=totals(ch,-1,-1);ch.k.forEach((c,i)=>HR.push([c[0],T.cs[i][0]]))});HR.sort((a,b)=>a[0]-b[0])}
 const pc=(a,b)=>{let s=0;const m=Math.max(a,S0);for(const e of HR)if(e[0]>=m&&e[0]<b)s+=e[1];
  for(let j=0;j<H.v.length;j++){const t=H.t0+j*3600,ov=Math.min(t+3600,b,S0)-Math.max(t,a);if(ov>0)s+=H.v[j]*ov/3600}return s/W*100};
 const A=(P.acct||[]).filter(q=>q[1]!=null).sort((a,b)=>a[0]-b[0]),iv=[],wkOf=t=>wk0?S0+Math.floor((t-S0)/W7)*W7:0;
 let pr=null;A.forEach(q=>{const ws=wkOf(q[0]),same=!!pr&&(!wk0||wkOf(pr[0])===ws),a=same?pr:wk0?[ws,0]:null;
  if(a&&q[0]>a[0]&&q[1]>=a[1]){const o=Math.max(0,q[1]-a[1]-pc(a[0],q[0]));iv.push({ta:a[0],tb:q[0],o,r:o/(q[0]-a[0])*3600,rs:!same})}pr=q});
 const fl=t=>{const d=new Date(t*1000);d.setMinutes(0,0,0);return d/1000},hc=fl(now),NH=[24,72,168][S.hh],b0=Math.max(hc-(NH-1)*3600,H.t0),n=Math.round((hc-b0)/3600)+1,so=S.ho===1;
 const us=[],who=[],ot=new Array(n).fill(null),oi=new Array(n).fill(-1);
 for(let j=0;j<n;j++){const k=Math.round((b0+j*3600-H.t0)/3600);us.push((H.v[k]||0)/W*100);who.push(H.w[k]||[])}
 iv.forEach((I,ii)=>{for(let k=0;k<n;k++){const s=b0+k*3600,ov=Math.min(s+3600,I.tb)-Math.max(s,I.ta);if(ov>0){ot[k]=(ot[k]||0)+I.o*ov/(I.tb-I.ta);oi[k]=ii}}});
 const Wd=1000,Hh=140,T0=14,bw=Wd/n,mx=Math.max(1e-9,...us.map((u,j)=>u+(so?0:ot[j]||0))),Y=v=>v/mx*Hh,F=v=>v.toFixed(1),step=NH>72?0:NH>24?6:3,wd=d=>WD[(d.getDay()+6)%7];
 let g='',lab='',r0=-1;
 for(let j=0;j<n;j++){const s=b0+j*3600,x=j*bw,u=us[j],o=ot[j],uh=Y(u),oh=o&&!so?Y(o):0,d=D(s),h=d.getHours(),I=oi[j]>=0?iv[oi[j]]:null;
  if(h===0&&j)g+=`<line x1="${F(x)}" x2="${F(x)}" y1="${T0}" y2="${T0+Hh}" stroke="var(--bd)"/>`;
  if(step&&h%step===0)lab+=`<text x="${F(x+bw/2)}" y="${T0+Hh+13}" font-size="11" fill="var(--faint)" text-anchor="middle">${z2(h)}</text>`;
  if(h===0||(j===0&&h<21))lab+=`<text x="${F(x+2)}" y="${T0+Hh+(step?27:13)}" font-size="11" fill="var(--mut)">${wd(d)} ${fdd(s)}</text>`;
  if(oh>0)g+=`<rect x="${F(x+bw*.1)}" y="${F(T0+Hh-uh-oh)}" width="${F(bw*.8)}" height="${F(oh)}" fill="url(#ldh)"/>`;
  if(uh>0)g+=`<rect x="${F(x+bw*.1)}" y="${F(T0+Hh-Math.max(uh,1.5))}" width="${F(bw*.8)}" height="${F(Math.max(uh,1.5))}" fill="${PU}"/>`;
  const ws=who[j].map(([ni,y])=>`<div class="tl"><span>${esc(NN[ni])}</span><b>${fp(y/W*100)}%</b></div>`).join('');
  const tip=`<b>${wd(d)} ${fdd(s)}, ${z2(h)}:00–${z2((h+1)%24)}:00</b>${j===n-1?' · час ещё идёт':''}<br>мы: <b>${fp(u)}%</b> недели${u>0?' · '+fh2(u/100*W):''} — точно, по логам этого компьютера<br>не видно в наших логах: `
   +(I?`<b>~${fp(o)}%</b> — среднее: между ${I.rs?'сбросом':'замером'} ${fd(I.ta)} и замером ${fd(I.tb)} набежало ${fp(I.o)}%, здесь — поровну на каждый час`:'нет замера Claude — неизвестно')
   +(ws?`<div class="cw"><div class="m">наши чаты в этот час, % недели:</div>${ws}</div>`:'');
  g+=`<rect x="${F(x)}" y="0" width="${F(bw)}" height="${T0+Hh}" fill="transparent" data-tip="${ea(tip)}"/>`}
 if(!so)for(let j=0;j<=n;j++){if(j<n&&ot[j]==null){if(r0<0)r0=j}else if(r0>=0){if((j-r0)*bw>=120)g+=`<text x="${F((r0+j)/2*bw)}" y="${T0+10}" font-size="11" fill="var(--faint)" text-anchor="middle">нет замера Claude</text>`;r0=-1}}
 if(wk0)for(let t=S0;t>b0;t-=W7)if(t<=hc+3600){const x=(t-b0)/3600*bw;g+=`<line x1="${F(x)}" x2="${F(x)}" y1="0" y2="${T0+Hh}" stroke="#EF9F27" stroke-width="2"/><text x="${F(x+4)}" y="${T0+24}" font-size="11" fill="#EF9F27">сброс недели</text>`}
 if(!so)A.forEach(q=>{if(q[0]<b0||q[0]>hc+3600)return;const x=(q[0]-b0)/3600*bw,o=pc(wk0?wkOf(q[0]):S0,q[0]);
  g+=`<line x1="${F(x)}" x2="${F(x)}" y1="${T0}" y2="${T0+Hh}" stroke="var(--fg)" stroke-dasharray="2 3" opacity=".35"/><path d="M${F(x-5)} 1L${F(x+5)} 1L${F(x)} ${T0-1}Z" fill="var(--fg)" data-tip="${ea(`<b>Замер Claude, ${fd(q[0])}</b> — точная точка<br>весь аккаунт: <b>${fp(q[1])}%</b> недели<br>мы: ${fp(o)}% · не видно в логах: ${fp(Math.max(0,q[1]-o))}%`)}"/>`});
 const L=A.length&&A[A.length-1][0]>=S0?A[A.length-1]:null,dt2=c=>`<span class="dot" style="--c:${c}"></span>`,nv=`<span data-tip="${ea(NV)}" style="border-bottom:1px dotted var(--faint);cursor:help">не видно в наших логах</span>`;let top;
 if(L){const o=pc(S0,L[0]),af=pc(L[0],now+1),o2=Math.max(0,L[1]-o),fr=Math.max(0,100-L[1]-af),sg=(w,st,tp)=>w>0?`<i style="width:${Math.min(100,w)}%;${st}" data-tip="${ea(tp)}"></i>`:'';
  top=`<div class="lead" style="font-size:14.5px">Замер Claude ${fd(L[0])}: весь аккаунт съел <b>${fp(L[1])}%</b> недели. Из них ${dt2(PU)}мы — <b>${fp(o)}%</b>, ${dt2('var(--mut)')}${nv} — <b>${fp(o2)}%</b>. Свободно <b>${fp(Math.max(0,100-L[1]))}%</b>.${af>=.05?` После замера мы съели ещё ${fp(af)}%.`:''}</div>
  <div class="acb">${sg(o,'background:'+PU,`мы до замера: ${fp(o)}% недели — точно`)}${sg(o2,'background:var(--fg);opacity:.45',`не видно в наших логах: ${fp(o2)}% — точно на момент замера`)}${sg(af,'background:'+PU+';opacity:.5',`мы после замера: ${fp(af)}%`)}${sg(fr,'background:transparent',`свободно ≈${fp(fr)}%`)}</div>`}
 else top=`<div class="lead" style="font-size:14.5px">${dt2(PU)}Мы съели <b>${fp(pc(S0,now+1))}%</b> недели. Сколько съел весь аккаунт, неизвестно: на этой неделе замеров Claude нет. Снимок сдаётся командой <b>--snap 41</b> (41 — процент недели из claude.ai → Usage).</div>`;
 const r3=pc(now-3*3600,now+1)/3,bs=L?(A.filter(q=>q[0]>=S0&&q[0]<=L[0]-3600).pop()||(wk0?[S0,0]:null)):null,
  ro=bs?Math.max(0,L[1]-bs[1]-pc(bs[0],L[0]))/(L[0]-bs[0])*3600:null,rate=r3+(ro||0);
 const est=L?L[1]+pc(L[0],now+1)+(ro||0)*(now-L[0])/3600:pc(S0,now+1);
 let pace=`Темп последних 3 часов: мы <b>${fp(r3)}%</b> недели в час${ro!=null?`, не видно в логах ~${fp(ro)}% в час (среднее с ${fd(bs[0])} по ${fd(L[0])})`:''}.`;
 if(wk0){const rs=S0+W7,pr2=est+rate*(rs-now)/3600;pace+=` Если так и дальше, к сбросу (${fd(rs)}) будет ≈<b>${fI(pr2)}%</b> недели${pr2>100&&rate>0?` — лимит кончится ≈${wd(D(now+(100-est)/rate*3600))} ${fd(now+(100-est)/rate*3600)}`:''}${L?'':' (без того, чего нет в логах)'}.`}
 return `<div class="card"><div class="tph"><h2>По часам: мы и остальной аккаунт</h2>${seg('hh',['сутки','3 дня','неделя'],0)}${seg('ho',['вместе','только мы'],0)}</div>${top}
 <svg viewBox="0 0 ${Wd} ${T0+Hh+(step?32:18)}" style="width:100%;height:auto;overflow:visible"><defs><pattern id="ldh" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.5" height="6" fill="var(--fg)" opacity=".3"/></pattern></defs>${g}${lab}</svg>
 <div class="lgd" style="margin-top:6px"><span class="chip"><i style="--c:${PU}"></i>мы — чаты этого компьютера, точно</span>${so?'':`<span class="chip hz" data-tip="${ea(NV)}"><i></i>не видно в наших логах — среднее между замерами <u>что это?</u></span><span>▼ — замер Claude, точная точка</span>`}${wk0?'<span style="color:#EF9F27">| — сброс недели: слева прошлая неделя</span>':''}</div>
 <div class="cap">${pace} Столбик — час, высота — сколько процентов недельного лимита съедено. «Только мы» — без чужого слоя, наши столбики крупнее. Наведи на столбик — кто съел.</div></div>`}
/* левая колонка: «Чаты» — как было; «Дни» — сутки мозготокенов, клик открывает день на дашборде */
function dayBar(x){const B=P.brain,h=[];for(let i=0;i<24;i++){let m=0;if(x.src)for(let j=0;j<6;j++)m+=B.aw[x.a+i*6+j]||0;
 else x.R.forEach(q=>q.h.forEach(e=>{if(e[0]-x.a>=i*6&&e[0]-x.a<i*6+6)m+=10}));h.push(Math.min(1,m/60))}
 return `<i class="bh">${h.map(v=>`<u style="opacity:${v?.15+v*.85:.06}"></u>`).join('')}</i>`}
function sideDays(){const Z=brainData(),wk=Z.days.slice(-7);if(S.bd===null){S.bd=Z.days.length-1;while(S.bd>0&&!Z.days[S.bd].msg&&!Z.days[S.bd].xt)S.bd--}
 return `<div class="it dy${S.bd===-1?' sel':''}" data-d="-1"><div class="t">${SYS}Неделя</div><div class="s">у компа ${fhM(wk.reduce((s,x)=>s+x.aw,0))}</div></div>`
  +Z.days.slice().reverse().map(x=>`<div class="it dy${S.bd===x.d?' sel':''}" data-d="${x.d}"><div class="t">${fdW(x.t)}</div><div class="s">${x.aw?fhM(x.aw)+' у компа':'тебя не было'}${x.res?' · ресурс '+fI(x.res)+'%':''}</div>${dayBar(x)}</div>`).join('')}
function side(){const hb=P.brain&&P.brain.r.length,dv=hb&&S.md===1;$('side').innerHTML='<div class="sh">'+LOGO+'<div>'+APP+'<span>снимок логов '+GEN+'</span></div></div>'
 +(hb?'<div class="lvs">'+seg('md',['Токены','Мозготокены'],0)+'</div>':'')+(dv?sideDays():`<div class="it${S.c<0?' sel':''}" data-i="-1"><div class="t">${SYS}Вся система</div><div class="s">центральный дашборд ${perTitle()}</div></div>`
 +CH.map((ch,i)=>{const a=AG[i];return `<div class="it${i===S.c?' sel':''}" data-i="${i}"><div class="t">${esc(ch.title)}</div><div class="s">${fp(a.t/CAP[2]*100)}% недели · ${ch.k.length} ${pl(ch.k.length,'вызов','вызова','вызовов')}</div><div class="mx" style="width:${Math.max(4,a.t/MX*100)}%">${a.m.map((v,m)=>v>0?`<i style="width:${v/a.t*100}%;background:${CL[m]}"></i>`:'').join('')}</div></div>`}).join(''))}
function draw(){document.body.classList.toggle('adm',ADMIN);if(ADMIN)side();$('view').innerHTML=S.md===1&&P.brain&&P.brain.r.length?brainPage():S.c<0?central():chatView(CH[S.c])}
document.addEventListener('click',ev=>{const b=ev.target.closest('button[data-g]');if(b){S[b.dataset.g]=+b.dataset.v;draw();return}
 const dy=ev.target.closest('.dy');if(dy){S.bd=+dy.dataset.d;draw();$('main').scrollTop=0;return}
 if(ev.target.closest('.masc')&&MQ.length){MCL=true;const mh=$('mh');if(mh)mh.remove();let j=MI;while(MQ.length>1&&j===MI)j=Math.floor(Math.random()*MQ.length);MI=j;const e=$('mb');e.textContent=MQ[MI].replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>');e.className='mb'+(MT[MI]?' t'+MT[MI]:'');e.style.animation='none';void e.offsetWidth;e.style.animation='';return}
 const w=ev.target.closest('.wc.go');if(w){const m=+w.dataset.m;S.m=(S.m===m&&m>=0)?-1:m;draw();return}
 const it=ev.target.closest('.it,.go-chat');if(it){S.c=+it.dataset.i;S.m=-1;S.e=-1;if(it.classList.contains('go-chat'))S.md=0;draw();$('main').scrollTop=0}});
document.addEventListener('toggle',ev=>{const d=ev.target;if(d.classList&&d.classList.contains('hv'))S[d.dataset.k]=d.open},true);
let HL=null;
document.addEventListener('mouseover',ev=>{const e=ev.target.closest('.ev');if(HL){HL.classList.remove('hl');HL=null}
 if(e){HL=document.querySelector('.sl[data-i="'+e.dataset.i+'"]');if(HL)HL.classList.add('hl')}});
document.addEventListener('mousemove',ev=>{const t=$('tip'),sl=ev.target.closest('.sl'),dt=ev.target.closest('[data-tip]');let h=null;if($('rs')&&$('rs').classList.contains('drag')){t.style.display='none';return}
 if(sl&&S.c>=0)h=tipCall(CH[S.c],+sl.dataset.i);else if(dt)h=dt.dataset.tip;
 if(!h){t.style.display='none';return}
 t.innerHTML=h;t.style.display='block';let x=ev.clientX+16,y=ev.clientY+16;
 if(x+t.offsetWidth>innerWidth-8)x=ev.clientX-t.offsetWidth-16;if(y+t.offsetHeight>innerHeight-8)y=Math.max(8,ev.clientY-t.offsetHeight-16);t.style.left=x+'px';t.style.top=y+'px'});
/* полоса дней: нажал — день, протянул — дни, ручка — край; отпустил — сервер собирает страницу за эти дни */
document.addEventListener('pointerdown',ev=>{const rs=ev.target.closest('#rs');if(!rs||ev.target.closest('.rr')||ev.button>0)return;ev.preventDefault();
 const Z=P.strip,bars=rs.querySelector('.rbars'),R=bars.getBoundingClientRect(),n=bars.children.length,w0=RW,h=ev.target.closest('.rh');
 const di=cx=>Math.max(0,Math.min(n-1,Math.floor((cx-R.left)/R.width*n))),day=i=>Z.d0+(w0+i)*DAY;
 let i0=Math.max(0,Math.floor((P.since-Z.d0)/DAY)-w0),i1=Math.min(n-1,Math.floor((perEnd()-1-Z.d0)/DAY)-w0),moved=false;
 const anchor=h?(h.dataset.h==='0'?i1:i0):di(ev.clientX);if(!h)i0=i1=anchor;
 const paint=()=>{[...bars.children].forEach((b,i)=>b.classList.toggle('on',i>=i0&&i<=i1));const L=i0/n*100,Wd=(i1+1-i0)/n*100,hs=rs.querySelectorAll('.rh'),bd=rs.querySelector('.rb');
  bd.style.left=L+'%';bd.style.width=Wd+'%';hs[0].style.left=L+'%';hs[1].style.left=(L+Wd)+'%';
  let s=0;for(let i=i0;i<=i1;i++){const v=Z.v[w0+i];s+=(v[0]+v[1]+v[2]+v[3])*1e3}const k=i1-i0+1;
  $('rlab').innerHTML=`${fdW2(day(i0))}${k>1?' — '+fdW2(day(i1)):''} · ${k} ${pl(k,'день','дня','дней')} · <b>≈${fp(s/CAP[2]*100)}%</b> недели · ${fUSD(s)}`;
  $('rfrom').value=isoD(day(i0));$('rto').value=isoD(day(i1))};
 if(!h)paint();rs.classList.add('drag');$('tip').style.display='none';
 const mv=e=>{const j=di(e.clientX);moved=true;i0=Math.min(anchor,j);i1=Math.max(anchor,j);paint()};
 const up=()=>{removeEventListener('pointermove',mv);removeEventListener('pointerup',up);rs.classList.remove('drag');if(h&&!moved)return;goRange(isoD(day(i0)),isoD(day(i1)))};
 addEventListener('pointermove',mv);addEventListener('pointerup',up)});
document.addEventListener('change',ev=>{if(ev.target.id!=='rfrom'&&ev.target.id!=='rto')return;const f=$('rfrom').value,t=$('rto').value;if(f&&t)goRange(f<t?f:t,f<t?t:f)});
{const h=location.hash.match(/c=([\w-]+)/);if(h&&ADMIN){const i=CH.findIndex(ch=>ch.id===h[1]);if(i>=0)S.c=i}}
draw();
</script></body></html>
"""


if __name__ == "__main__":
    main()
