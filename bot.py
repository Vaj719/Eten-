Enter"""
بوت تحويل الملفات بين القنوات - ملف واحد
Python + Telethon

التثبيت: pip install telethon
التشغيل: python bot.py

المميزات:
- تسجيل دخول بحساب تيليجرام (رقم + كود + 2FA)
- أزرار شفافة (inline)
- تحويل الملفات بدون اسم المصدر
- مراقبة القنوات المصدر
"""

import os
import sys
import json
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path

# ============================================================
# الإعدادات
# ============================================================
BOT_TOKEN = "8807828987:AAF3rNmZ72ETpmttoIIZmZ7MeMCIvk05mCM"
ADMIN_ID = 8757482062

# بيانات تطبيق عام - صغيرة ولا تحتاج تعديل
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "sessions"
DATA_FILE = BASE_DIR / "data.json"
LAST_MSG_FILE = BASE_DIR / "last_messages.json"
LOG_FILE = BASE_DIR / "bot.log"
SESSIONS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ============================================================
# إصلاح Telethon لو تم تعديله من قبل
# ============================================================
def fix_telethon():
    """إرجاع Telethon لحالته الأصلية لو تم تعديله"""
    try:
        import telethon
        init_path = os.path.join(os.path.dirname(telethon.__file__), 'tl', 'functions', '__init__.py')
        with open(init_path, 'r', encoding='utf-8') as f:
            src = f.read()
        if "struct.pack('<q', self.api_id)" in src:
            src = src.replace("struct.pack('<q', self.api_id)", "struct.pack('<i', self.api_id)")
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(src)
            print("✅ تم إصلاح Telethon")
        elif "struct.pack('<i', self.api_id)" in src:
            print("✅ Telethon سليم")
    except Exception as e:
        print(f"⚠️ {e}")

fix_telethon()

# ============================================================
# استيراد Telethon
# ============================================================
try:
    from telethon import TelegramClient, events, Button
    from telethon.errors import (
        PhoneCodeInvalidError, PhoneCodeExpiredError,
        PasswordHashInvalidError, SessionPasswordNeededError,
        PhoneNumberInvalidError, FloodWaitError
    )
except ImportError:
    print("❌ شغّل: pip install telethon")
    sys.exit(1)

# ============================================================
# JSON helpers
# ============================================================
def load_json(p):
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_json(p, d):
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

def load_data():
    d = load_json(DATA_FILE)
    if not d:
        d = {}
    # التأكد من وجود كل المفاتيح
    if "accounts" not in d:
        d["accounts"] = {}
    if "source_channels" not in d:
        d["source_channels"] = []
    if "target_channel" not in d:
        d["target_channel"] = None
    save_json(DATA_FILE, d)
    return d

def save_data(d):
    save_json(DATA_FILE, d)

def load_last():
    return load_json(LAST_MSG_FILE)

def save_last(d):
    save_json(LAST_MSG_FILE, d)

# ============================================================
# User states
# ============================================================
user_states = {}

def set_state(uid, st, **kw):
    user_states[uid] = {"state": st, **kw}

def get_state(uid):
    return user_states.get(uid)

def clear_state(uid):
    user_states.pop(uid, None)

# ============================================================
# Keyboards - أزرار شفافة (inline)
# ============================================================
def main_menu():
    """القائمة الرئيسية - أزرار inline شفافة"""
    return [
        [Button.inline("➕ إضافة حساب", b"add_account")],
        [Button.inline("📋 قائمة الحسابات", b"list_accounts")],
        [Button.inline("📢 تعين قناة وجهة", b"set_target")],
        [Button.inline("➕ إضافة قناة مصدر", b"add_source")],
        [Button.inline("📋 القنوات المصدر", b"list_sources")],
        [Button.inline("🎯 القناة الوجهة", b"show_target")],
        [Button.inline("▶️ تشغيل المراقبة", b"start_monitor")],
        [Button.inline("⏹️ إيقاف المراقبة", b"stop_monitor")],
    ]

def cancel_inline():
    """زر إلغاء شفاف"""
    return [Button.inline("❌ إلغاء", b"cancel")]

# ============================================================
# Account / login
# ============================================================
def session_path(name):
    return str(SESSIONS_DIR / name)

async def start_login(name, phone):
    client = TelegramClient(session_path(name), API_ID, API_HASH)
    await client.connect()
    try:
        result = await client.send_code_request(phone)
        return {"ok": True, "client": client, "hash": result.phone_code_hash}
    except PhoneNumberInvalidError:
        await client.disconnect()
        return {"ok": False, "err": "رقم الهاتف غير صحيح"}
    except FloodWaitError as e:
        await client.disconnect()
        return {"ok": False, "err": f"انتظر {e.seconds} ثانية"}
    except Exception as e:
        await client.disconnect()
        return {"ok": False, "err": str(e)}

async def complete_login(client, phone, code, phone_code_hash):
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        return {"ok": True}
    except SessionPasswordNeededError:
        return {"ok": False, "2fa": True}
    except PhoneCodeInvalidError:
        return {"ok": False, "err": "الكود غير صحيح"}
    except PhoneCodeExpiredError:
        return {"ok": False, "err": "انتهت صلاحية الكود"}
    except Exception as e:
        return {"ok": False, "err": str(e)}

async def complete_2fa(client, password):
    try:
        await client.sign_in(password=password)
        return {"ok": True}
    except PasswordHashInvalidError:
        return {"ok": False, "err": "كلمة المرور غير صحيحة"}
    except Exception as e:
        return {"ok": False, "err": str(e)}

def save_account(name, phone):
    d = load_data()
    d["accounts"][name] = {
        "session_name": name,
        "phone": phone,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_data(d)

def del_account(name):
    d = load_data()
    d["accounts"].pop(name, None)
    save_data(d)
    for ext in [".session", ".session-journal", ""]:
        p = SESSIONS_DIR / f"{name}{ext}"
        if p.exists():
            try:
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    import shutil
                    shutil.rmtree(p)
            except Exception:
                pass

def first_account():
    d = load_data()
    a = d.get("accounts", {})
    if not a:
        return None
    return list(a.values())[0]["session_name"]

def parse_channel(t):
    t = t.strip()
    m = re.search(r't\.me/([a-zA-Z0-9_]+)', t, re.I)
    if m:
        return "@" + m.group(1)
    if re.match(r'^@[a-zA-Z0-9_]{5,}$', t):
        return t
    if re.match(r'^[a-zA-Z0-9_]{5,}$', t):
        return "@" + t
    return None

# ============================================================
# Monitor
# ============================================================
monitor_running = False
monitor_task = None

async def forward_msg(client, from_channel, msg_id, target_channel):
    """تحويل ملف فقط بدون اسم المصدر + إضافة @x_Tongk تحت الملف"""
    try:
        msgs = await client.get_messages(from_channel, ids=msg_id)
        if not msgs:
            return False
        msg = msgs if isinstance(msgs, list) else [msgs]
        msg = msg[0]

        # تحويل الملفات فقط (تجاهل الرسائل النصية العادية)
        if not msg.media:
            return False

        # بناء الكابشن: اسم الملف الأصلي + @x_Tongk
        original_caption = msg.message or ""
        signature = "\n\n@x_Tongk"
        new_caption = original_caption + signature if original_caption else signature.strip()

        await client.send_file(
            target_channel,
            file=msg.media,
            caption=new_caption,
            formatting_entities=msg.entities
        )
        log.info(f"حوّل ملف {msg_id} من {from_channel}")
        return True
    except Exception as e:
        log.error(f"فشل التحويل {msg_id}: {e}")
        return False

async def monitor_loop():
    global monitor_running
    log.info("المراقبة بدأت")
    first_run = True

    while monitor_running:
        try:
            d = load_data()
            srcs = d.get("source_channels", [])
            tgt = d.get("target_channel")

            if not tgt or not srcs:
                await asyncio.sleep(30)
                continue

            sn = first_account()
            if not sn:
                await asyncio.sleep(30)
                continue

            uc = TelegramClient(session_path(sn), API_ID, API_HASH)
            await uc.connect()

            if not await uc.is_user_authorized():
                await uc.disconnect()
                await asyncio.sleep(30)
                continue

            lm = load_last()

            for ch in srcs:
                lid = lm.get(ch, 0)
                try:
                    msgs = await uc.get_messages(ch, limit=50)
                    if not msgs:
                        continue

                    msgs.reverse()

                    if first_run and lid == 0:
                        if msgs:
                            lm[ch] = msgs[0].id
                            save_last(lm)
                            log.info(f"أول تشغيل - {ch}: {msgs[0].id}")
                        continue

                    for msg in msgs:
                        if msg.id <= lid:
                            continue

                        # تحويل الملفات فقط (تجاهل الرسائل النصية)
                        if msg.media:
                            await forward_msg(uc, ch, msg.id, tgt)

                        lm[ch] = msg.id
                        save_last(lm)

                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    log.error(f"خطأ {ch}: {e}")

            await uc.disconnect()
            first_run = False

        except Exception as e:
            log.error(f"خطأ المراقبة: {e}")

        await asyncio.sleep(30)

    log.info("المراقبة توقفت")

# ============================================================
# Bot
# ============================================================
bot = TelegramClient("fwd_bot_session", API_ID, API_HASH)

# ============================================================
# /start - عرض القائمة الرئيسية
# ============================================================
@bot.on(events.NewMessage(pattern="/start"))
async def cmd_start(event):
    if event.sender_id != ADMIN_ID:
        return
    clear_state(event.sender_id)
    await event.reply(
        "🤖 <b>بوت تحويل الملفات بين القنوات</b>\n\n"
        "اختر من القائمة:",
        parse_mode="html",
        buttons=main_menu()
    )

# ============================================================
# معالجة callback queries (الأزرار الشفافة)
# ============================================================
@bot.on(events.CallbackQuery(func=lambda e: e.sender_id == ADMIN_ID))
async def handle_callback(event):
    data = event.data
    uid = event.sender_id

    # إلغاء
    if data == b"cancel":
        clear_state(uid)
        await event.edit("تم الإلغاء.", buttons=main_menu())
        return

    # إضافة حساب
    if data == b"add_account":
        set_state(uid, "waiting_phone")
        await event.edit(
            "📱 <b>تسجيل دخول حساب تيليجرام</b>\n\n"
            "أرسل رقم الهاتف مع رمز الدولة.\n"
            "مثال: <code>+9647701234567</code>",
            parse_mode="html",
            buttons=cancel_inline()
        )

    # قائمة الحسابات
    elif data == b"list_accounts":
        d = load_data()
        accs = d.get("accounts", {})
        if not accs:
            await event.edit("📋 لا توجد حسابات مضافة.", buttons=main_menu())
            return
        txt = "📋 <b>الحسابات:</b>\n\n"
        btns = []
        for sn, a in accs.items():
            txt += f"📱 <code>{a['phone']}</code>\n🗓️ {a['added_at']}\n\n"
            btns.append([Button.inline(f"🗑️ حذف {a['phone']}", f"delacc:{sn}".encode())])
        btns.append([Button.inline("🔙 رجوع", b"back")])
        await event.edit(txt, parse_mode="html", buttons=btns)

    # تعيين قناة وجهة
    elif data == b"set_target":
        if not load_data().get("accounts"):
            await event.edit("⚠️ أضف حساباً أولاً.", buttons=main_menu())
            return
        set_state(uid, "waiting_target")
        await event.edit(
            "📢 أرسل معرف القناة الوجهة.\nمثال: <code>@my_channel</code>",
            parse_mode="html",
            buttons=cancel_inline()
        )

    # إضافة قناة مصدر
    elif data == b"add_source":
        if not load_data().get("accounts"):
            await event.edit("⚠️ أضف حساباً أولاً.", buttons=main_menu())
            return
        set_state(uid, "waiting_source")
        await event.edit(
            "➕ أرسل معرف القناة المصدر.\nمثال: <code>@source_channel</code>",
            parse_mode="html",
            buttons=cancel_inline()
        )

    # قائمة القنوات المصدر
    elif data == b"list_sources":
        d = load_data()
        chs = d.get("source_channels", [])
        if not chs:
            await event.edit("📋 لا توجد قنوات مصدر.", buttons=main_menu())
            return
        txt = "📋 <b>القنوات المصدر:</b>\n\n"
        btns = []
        for i, ch in enumerate(chs):
            txt += f"{i+1}. <code>{ch}</code>\n"
            btns.append([Button.inline(f"🗑️ حذف {ch}", f"delsrc:{i}".encode())])
        btns.append([Button.inline("🔙 رجوع", b"back")])
        await event.edit(txt, parse_mode="html", buttons=btns)

    # عرض القناة الوجهة
    elif data == b"show_target":
        tgt = load_data().get("target_channel")
        if tgt:
            await event.edit(f"🎯 القناة الوجهة: <code>{tgt}</code>", parse_mode="html", buttons=main_menu())
        else:
            await event.edit("🎯 لم تُعين بعد.", buttons=main_menu())

    # تشغيل المراقبة
    elif data == b"start_monitor":
        global monitor_running, monitor_task
        d = load_data()
        if not d.get("accounts"):
            await event.edit("⚠️ لا توجد حسابات.", buttons=main_menu())
            return
        if not d.get("target_channel"):
            await event.edit("⚠️ لم تُعين قناة وجهة.", buttons=main_menu())
            return
        if not d.get("source_channels"):
            await event.edit("⚠️ لا قنوات مصدر.", buttons=main_menu())
            return
        if monitor_running:
            await event.edit("▶️ تعمل بالفعل.", buttons=main_menu())
            return
        monitor_running = True
        monitor_task = asyncio.create_task(monitor_loop())
        await event.edit(
            f"▶️ <b>المراقبة تعمل!</b>\n\n"
            f"مصادر: {len(d['source_channels'])}\n"
            f"وجهة: <code>{d['target_channel']}</code>",
            parse_mode="html",
            buttons=main_menu()
        )

    # إيقاف المراقبة
    elif data == b"stop_monitor":
        if not monitor_running:
            await event.edit("⏹️ متوقفة.", buttons=main_menu())
            return
        monitor_running = False
        if monitor_task:
            monitor_task.cancel()
        await event.edit("⏹️ تم الإيقاف.", buttons=main_menu())

    # حذف حساب
    elif data.startswith(b"delacc:"):
        sn = data.split(b":", 1)[1].decode()
        del_account(sn)
        await event.edit(f"✅ حُذف: <code>{sn}</code>", parse_mode="html", buttons=main_menu())

    # حذف قناة مصدر
    elif data.startswith(b"delsrc:"):
        idx = int(data.split(b":")[1])
        d = load_data()
        chs = d.get("source_channels", [])
        if idx < len(chs):
            deleted = chs.pop(idx)
            d["source_channels"] = chs
            save_data(d)
            await event.edit(f"✅ حُذف: <code>{deleted}</code>", parse_mode="html", buttons=main_menu())

    # رجوع
    elif data == b"back":
        await event.edit("🤖 القائمة الرئيسية:", buttons=main_menu())

# ============================================================
# معالجة الرسائل النصية (حسب الحالة)
# ============================================================
@bot.on(events.NewMessage(func=lambda e: e.sender_id == ADMIN_ID and e.text))
async def handle_text(event):
    uid = event.sender_id
    st = get_state(uid)

    if not st:
        # لو ما في حالة، نعرض القائمة
        if event.text.startswith("/"):
            return  # أوامر تُعالج في handlers أخرى
        await event.reply("اختر من القائمة:", buttons=main_menu())
        return

    state = st["state"]

    # === إضافة حساب ===
    if state == "waiting_phone":
        ph = re.sub(r'\s+', '', event.text.strip())
        if not re.match(r'^\+\d{6,15}$', ph):
            await event.reply("❌ رقم غير صحيح. مثال: +9647701234567", buttons=cancel_inline())
            return

        sn = "user_" + re.sub(r'[^0-9]', '', ph)
        r = await start_login(sn, ph)

        if r["ok"]:
            set_state(uid, "waiting_code", sn=sn, phone=ph, client=r["client"], hash=r["hash"])
            await event.reply("✅ تم إرسال الكود إلى تيليجرام.\n\nأرسل الكود الآن:", buttons=cancel_inline())
        else:
            await event.reply(f"❌ {r['err']}", buttons=cancel_inline())

    elif state == "waiting_code":
        st = get_state(uid)
        if not st or not st.get("client"):
            clear_state(uid)
            await event.reply("❌ خطأ. ابدأ من جديد.", buttons=main_menu())
            return

        code = re.sub(r'\s+', '', event.text.strip())
        r = await complete_login(st["client"], st["phone"], code, st["hash"])

        if r["ok"]:
            await st["client"].disconnect()
            save_account(st["sn"], st["phone"])
            clear_state(uid)
            await event.reply("✅ تم تسجيل الدخول! تم حفظ الحساب.", buttons=main_menu())
        elif r.get("2fa"):
            set_state(uid, "waiting_2fa", sn=st["sn"], phone=st["phone"], client=st["client"])
            await event.reply("🔒 2FA مفعّل. أرسل كلمة المرور:", buttons=cancel_inline())
        else:
            await event.reply(f"❌ {r.get('err', 'خطأ')}\nأعد الكود:", buttons=cancel_inline())

    elif state == "waiting_2fa":
        st = get_state(uid)
        if not st or not st.get("client"):
            clear_state(uid)
            await event.reply("❌ خطأ.", buttons=main_menu())
            return

        r = await complete_2fa(st["client"], event.text.strip())

        if r["ok"]:
            await st["client"].disconnect()
            save_account(st["sn"], st["phone"])
            clear_state(uid)
            await event.reply("✅ تم تسجيل الدخول مع 2FA!", buttons=main_menu())
        else:
            await event.reply(f"❌ {r.get('err', 'خطأ')}\nأعد كلمة المرور:", buttons=cancel_inline())

    # === تعيين قناة وجهة ===
    elif state == "waiting_target":
        ch = parse_channel(event.text)
        if not ch:
            await event.reply("❌ معرّف غير صحيح.", buttons=cancel_inline())
            return
        d = load_data()
        d["target_channel"] = ch
        save_data(d)
        clear_state(uid)
        await event.reply(f"✅ القناة الوجهة: <code>{ch}</code>", parse_mode="html", buttons=main_menu())

    # === إضافة قناة مصدر ===
    elif state == "waiting_source":
        ch = parse_channel(event.text)
        if not ch:
            await event.reply("❌ معرّف غير صحيح.", buttons=cancel_inline())
            return
        d = load_data()
        if ch not in d["source_channels"]:
            d["source_channels"].append(ch)
            save_data(d)
        clear_state(uid)
        await event.reply(f"✅ أُضيفت: <code>{ch}</code>", parse_mode="html", buttons=main_menu())

# ============================================================
# تشغيل البوت
# ============================================================
async def main():
    log.info("=" * 50)
    log.info("  بوت تحويل الملفات - Python + Telethon")
    log.info("=" * 50)
    await bot.start(bot_token=BOT_TOKEN)
    log.info("البوت يعمل الآن...")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
