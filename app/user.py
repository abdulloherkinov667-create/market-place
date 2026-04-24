import os
import django
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from asgiref.sync import sync_to_async

# ================= DJANGO SETUP =================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from app.models import (
    Users, UzumProduct,
    Like, ShopingModel,
    Order, OrderItem,
)

# ================= CONFIG =================
# Asosiy botdan FARQLI token ishlatish kerak!
TOKEN = "8664343682:AAHAK6ctV8b-XUcY_T3MDFrNAbxfEjzX8JU"   # <-- o'z tokeningizni qo'ying

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STATES =================
class LoginState(StatesGroup):
    username = State()
    password = State()

# ================= SESSION (xotira) =================
# { telegram_id: django_user_id }
logged_in_users: dict[int, int] = {}

# ================= KEYBOARDS =================
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❤️ Like'larim")],
            [KeyboardButton(text="🛒 Savatim")],
            [KeyboardButton(text="📦 Buyurtmalarim")],
            [KeyboardButton(text="🌟 Istaklarim")],
            [KeyboardButton(text="📊 Statistikam")],
            [KeyboardButton(text="🚪 Chiqish")],
        ],
        resize_keyboard=True
    )

# ================= HELPERS =================
async def get_logged_user(tg_id: int):
    """Kirgan foydalanuvchini qaytaradi, aks holda None"""
    user_id = logged_in_users.get(tg_id)
    if not user_id:
        return None
    try:
        return await sync_to_async(Users.objects.get)(id=user_id)
    except Users.DoesNotExist:
        logged_in_users.pop(tg_id, None)
        return None


async def require_login(msg: types.Message) -> bool:
    """Login tekshiradi. Kirmagansa xabar beradi va False qaytaradi."""
    user = await get_logged_user(msg.from_user.id)
    if not user:
        await msg.answer(
            "🔐 Avval tizimga kiring.\n/login buyrug'ini yuboring."
        )
        return False
    return True

# ╔══════════════════════════════════════════╗
# ║              START                      ║
# ╚══════════════════════════════════════════╝

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    user = await get_logged_user(msg.from_user.id)
    if user:
        await msg.answer(
            f"👋 Salom, *{user.username}*! Siz allaqachon kirgansiz.",
            reply_markup=main_kb(),
            parse_mode="Markdown"
        )
    else:
        await msg.answer(
            "👋 Xush kelibsiz!\n\n"
            "Bu bot faqat *ro'yxatdan o'tgan foydalanuvchilar* uchun.\n"
            "Tizimga kirish uchun: /login",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )

# ╔══════════════════════════════════════════╗
# ║              LOGIN                      ║
# ╚══════════════════════════════════════════╝

@dp.message(Command("login"))
async def cmd_login(msg: types.Message, state: FSMContext):
    user = await get_logged_user(msg.from_user.id)
    if user:
        await msg.answer(
            f"✅ Siz allaqachon *{user.username}* sifatida kirgansiz.",
            reply_markup=main_kb(),
            parse_mode="Markdown"
        )
        return
    await msg.answer(
        "👤 *Tizimga kirish*\n\nFoydalanuvchi nomingizni kiriting:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
            resize_keyboard=True
        )
    )
    await state.set_state(LoginState.username)


@dp.message(F.text == "❌ Bekor qilish")
async def cancel_login(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())


@dp.message(LoginState.username)
async def login_get_username(msg: types.Message, state: FSMContext):
    username = msg.text.strip()

    # Bazada foydalanuvchi bormi?
    exists = await sync_to_async(Users.objects.filter(username=username).exists)()
    if not exists:
        await msg.answer(
            "❌ Bunday foydalanuvchi topilmadi.\n"
            "Qaytadan kiriting yoki '❌ Bekor qilish' bosing:"
        )
        return

    await state.update_data(username=username)
    await msg.answer(
        "🔑 Parolingizni kiriting:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
            resize_keyboard=True
        )
    )
    await state.set_state(LoginState.password)


@dp.message(LoginState.password)
async def login_get_password(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    username = data['username']
    password = msg.text

    # Django authenticate (sync_to_async orqali)
    from django.contrib.auth import authenticate as django_auth
    user = await sync_to_async(django_auth)(username=username, password=password)

    if user is None:
        await msg.answer(
            "❌ Parol noto'g'ri!\nQaytadan kiriting yoki '❌ Bekor qilish' bosing:"
        )
        return

    # Login muvaffaqiyatli
    logged_in_users[msg.from_user.id] = user.id
    await state.clear()

    await msg.answer(
        f"✅ Xush kelibsiz, *{user.username}*! 🎉\n\n"
        f"Quyidagi bo'limlarni ko'rishingiz mumkin:",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

# ╔══════════════════════════════════════════╗
# ║           CHIQISH                       ║
# ╚══════════════════════════════════════════╝

@dp.message(F.text == "🚪 Chiqish")
async def logout(msg: types.Message):
    if msg.from_user.id in logged_in_users:
        logged_in_users.pop(msg.from_user.id)
        await msg.answer(
            "👋 Tizimdan chiqdingiz.\nQayta kirish uchun: /login",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await msg.answer("Siz tizimda emassiz.", reply_markup=ReplyKeyboardRemove())

# ╔══════════════════════════════════════════╗
# ║           ❤️ LIKE'LAR                   ║
# ╚══════════════════════════════════════════╝

@dp.message(F.text == "❤️ Like'larim")
async def my_likes(msg: types.Message):
    if not await require_login(msg):
        return

    user = await get_logged_user(msg.from_user.id)
    likes = await sync_to_async(list)(
        Like.objects.filter(user=user)
        .select_related('product', 'product__category')
        .order_by('-created_at')
    )

    if not likes:
        await msg.answer("💔 Hali hech qanday mahsulotni like qilmagansiz.")
        return

    text = f"❤️ *Like'langan mahsulotlar* ({len(likes)} ta):\n\n"
    for i, like in enumerate(likes, 1):
        p = like.product
        active = "✅" if p.is_active else "❌ (o'chirilgan)"
        text += (
            f"{i}. *{p.name}* {active}\n"
            f"   💰 {p.price:,} so'm\n"
            f"   📂 {p.category.name}\n"
            f"   📅 {like.created_at.strftime('%d.%m.%Y')}\n\n"
        )

    await msg.answer(text, parse_mode="Markdown")

# ╔══════════════════════════════════════════╗
# ║           🛒 SAVAT                      ║
# ╚══════════════════════════════════════════╝

@dp.message(F.text == "🛒 Savatim")
async def my_cart(msg: types.Message):
    if not await require_login(msg):
        return

    user = await get_logged_user(msg.from_user.id)
    cart_items = await sync_to_async(list)(
        ShopingModel.objects.filter(user=user)
        .select_related('product', 'product__category')
        .order_by('-created_at')
    )

    if not cart_items:
        await msg.answer("🛒 Savatingiz bo'sh.")
        return

    text = f"🛒 *Savatingiz* ({len(cart_items)} ta mahsulot):\n\n"
    total = 0
    for i, item in enumerate(cart_items, 1):
        p = item.product
        text += (
            f"{i}. *{p.name}*\n"
            f"   💰 {p.price:,} so'm\n"
            f"   📂 {p.category.name}\n\n"
        )
        total += p.price

    text += f"💳 *Jami: {total:,} so'm*"
    await msg.answer(text, parse_mode="Markdown")

# ╔══════════════════════════════════════════╗
# ║           📦 BUYURTMALAR                ║
# ╚══════════════════════════════════════════╝

@dp.message(F.text == "📦 Buyurtmalarim")
async def my_orders(msg: types.Message):
    if not await require_login(msg):
        return

    user = await get_logged_user(msg.from_user.id)
    orders = await sync_to_async(list)(
        Order.objects.filter(user=user).order_by('-created_at')[:15]
    )

    if not orders:
        await msg.answer("📭 Hali buyurtma bermагансиз.")
        return

    STATUS_EMOJI = {
        'Kutilmoqda': '⏳', 'Tasdiqlandi': '✅',
        'Tayyorlanmoqda': '📦', "Yo'lga chiqdi": '🚚',
        'Yetkazildi': '🏠', 'Bekor qilindi': '❌', 'Qaytarildi': '↩️',
    }

    buttons = []
    text = f"📦 *Buyurtmalarim* (oxirgi {len(orders)} ta):\n\n"

    for o in orders:
        emoji = STATUS_EMOJI.get(o.is_status, '📋')
        total = await sync_to_async(lambda order=o: order.total_order_price)()
        text += (
            f"{emoji} *#{o.id}* — {o.is_status}\n"
            f"   💰 {total:,} so'm | 📅 {o.created_at.strftime('%d.%m.%Y')}\n\n"
        )
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} #{o.id} — {o.is_status}",
            callback_data=f"uorder_{o.id}"
        )])

    await msg.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("uorder_"))
async def order_detail(call: types.CallbackQuery):
    # Login tekshirish
    user = await get_logged_user(call.from_user.id)
    if not user:
        await call.answer("🔐 Tizimga kiring", show_alert=True)
        return

    oid = int(call.data.split("_")[1])
    try:
        order = await sync_to_async(Order.objects.get)(id=oid, user=user)
    except Order.DoesNotExist:
        await call.answer("❌ Buyurtma topilmadi", show_alert=True)
        return

    items = await sync_to_async(list)(
        OrderItem.objects.filter(order=order).select_related('product')
    )
    total = await sync_to_async(lambda: order.total_order_price)()

    STATUS_EMOJI = {
        'Kutilmoqda': '⏳', 'Tasdiqlandi': '✅',
        'Tayyorlanmoqda': '📦', "Yo'lga chiqdi": '🚚',
        'Yetkazildi': '🏠', 'Bekor qilindi': '❌', 'Qaytarildi': '↩️',
    }
    emoji = STATUS_EMOJI.get(order.is_status, '📋')

    text = (
        f"📋 *Buyurtma #{order.id}*\n\n"
        f"{emoji} Holat: *{order.is_status}*\n"
        f"💳 To'lov: {order.payment_method}\n"
        f"📍 Manzil: {order.address or '—'}\n"
        f"📅 Sana: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"*Mahsulotlar:*\n"
    )
    for item in items:
        name = item.product.name if item.product else "O'chirilgan"
        text += f"  • {name} × {item.count} = {item.item_total_price:,} so'm\n"

    text += f"\n💰 *Jami: {total:,} so'm*"

    await call.message.answer(text, parse_mode="Markdown")
    await call.answer()

# ╔══════════════════════════════════════════╗
# ║           🌟 ISTAKLARIM (LIKES = WISH)  ║
# ╚══════════════════════════════════════════╝
# Modelingizda alohida "Wishlist" yo'q,
# shuning uchun Like = istaklar sifatida ko'rsatiladi
# (agar keyinchalik alohida model qo'shsangiz shu yerga qo'shasiz)

@dp.message(F.text == "🌟 Istaklarim")
async def my_wishlist(msg: types.Message):
    if not await require_login(msg):
        return

    user = await get_logged_user(msg.from_user.id)
    likes = await sync_to_async(list)(
        Like.objects.filter(user=user)
        .select_related('product')
        .order_by('-created_at')
    )

    if not likes:
        await msg.answer("🌟 Istaklaringiz bo'sh.\nWeb saytda mahsulotlarni like qiling!")
        return

    text = f"🌟 *Istaklarim* ({len(likes)} ta):\n\n"
    available = []
    unavailable = []

    for like in likes:
        p = like.product
        if p.is_active and p.count > 0:
            available.append(p)
        else:
            unavailable.append(p)

    if available:
        text += "✅ *Mavjud mahsulotlar:*\n"
        for p in available:
            discount_text = ""
            if p.aksi_narx > 0:
                discounted = int(p.price * (1 - p.aksi_narx / 100))
                discount_text = f" → *{discounted:,} so'm* 🔖{p.aksi_narx}%"
            text += f"  • {p.name} — {p.price:,} so'm{discount_text}\n"

    if unavailable:
        text += "\n❌ *Mavjud emas:*\n"
        for p in unavailable:
            reason = "Tugagan" if not p.count else "O'chirilgan"
            text += f"  • {p.name} ({reason})\n"

    await msg.answer(text, parse_mode="Markdown")

# ╔══════════════════════════════════════════╗
# ║           📊 STATISTIKA                 ║
# ╚══════════════════════════════════════════╝

@dp.message(F.text == "📊 Statistikam")
async def my_stats(msg: types.Message):
    if not await require_login(msg):
        return

    user = await get_logged_user(msg.from_user.id)

    # Buyurtmalar
    orders = await sync_to_async(list)(Order.objects.filter(user=user))
    total_orders = len(orders)

    # Sotib olingan mahsulotlar (Yetkazildi)
    delivered = [o for o in orders if o.is_status == 'Yetkazildi']
    total_spent = 0
    total_items_bought = 0

    for o in delivered:
        t = await sync_to_async(lambda order=o: order.total_order_price)()
        total_spent += t
        items = await sync_to_async(list)(OrderItem.objects.filter(order=o))
        for item in items:
            total_items_bought += item.count

    # Holat bo'yicha
    STATUS_EMOJI = {
        'Kutilmoqda': '⏳', 'Tasdiqlandi': '✅',
        'Tayyorlanmoqda': '📦', "Yo'lga chiqdi": '🚚',
        'Yetkazildi': '🏠', 'Bekor qilindi': '❌', 'Qaytarildi': '↩️',
    }
    status_counts = {}
    for o in orders:
        status_counts[o.is_status] = status_counts.get(o.is_status, 0) + 1

    # Savat
    cart_count = await sync_to_async(ShopingModel.objects.filter(user=user).count)()

    # Like'lar
    likes_count = await sync_to_async(Like.objects.filter(user=user).count)()

    # Eng ko'p sotib olingan mahsulot
    all_items = await sync_to_async(list)(
        OrderItem.objects.filter(order__user=user, order__is_status='Yetkazildi')
        .select_related('product')
    )
    product_counts: dict[str, int] = {}
    for item in all_items:
        if item.product:
            name = item.product.name
            product_counts[name] = product_counts.get(name, 0) + item.count

    top_product = max(product_counts, key=product_counts.get) if product_counts else None

    text = (
        f"📊 *{user.username} — Statistika*\n\n"
        f"🛒 Jami buyurtmalar: *{total_orders}* ta\n"
        f"📦 Sotib olingan mahsulotlar: *{total_items_bought}* dona\n"
        f"💰 Jami sarflangan: *{total_spent:,}* so'm\n"
        f"🛒 Hozir savatda: *{cart_count}* ta\n"
        f"❤️ Like'langan: *{likes_count}* ta\n"
    )

    if top_product:
        text += f"🏆 Eng ko'p sotib olingan: *{top_product}* ({product_counts[top_product]} dona)\n"

    if status_counts:
        text += "\n*Buyurtmalar holati:*\n"
        for status, count in status_counts.items():
            emoji = STATUS_EMOJI.get(status, '📋')
            text += f"  {emoji} {status}: {count} ta\n"

    await msg.answer(text, parse_mode="Markdown")


# ================= RUN =================
async def main():
    logging.info("✅ User bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())